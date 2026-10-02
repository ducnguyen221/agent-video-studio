"""Cổng P1-24: `video-studio probe` + gợi ý khởi động lại khi render chết ở `Navigation timeout`.

Mac mini 02/10/2026: Hot AI hỏng sau 42 phút vì môi trường render kẹt (HyperFrames không mở
được trang ở frame 0, mọi project, mọi bản) — khởi động lại máy là hết. Hai thứ phải đúng:

* `probe` phân biệt **kẹt** (quá giờ / Navigation timeout → `RENDER_STUCK:` + "khởi động lại
  máy") với hỏng kiểu khác (đuôi log + `doctor --hf`), và giết CẢ CÂY tiến trình khi quá giờ;
* `render_project` hỏng ở MỌI lần thử vì Navigation timeout thì lỗi nói thẳng "khởi động lại
  máy" — còn hỏng lẫn lộn thì giữ lời khuyên cũ (`doctor --hf`).

Không Node, không mạng: `Popen`/`subprocess.run` là hàm giả. Phép render thật nằm ở bước nghiệm
thu trên máy (`video-studio probe`), không ở bộ test lõi.
"""
import os
import subprocess

import pytest

from conftest import last_json
from video_studio import _env, contract, probe, render
from video_studio.contract import EngineError, StationMissing

FAKE_NPX = "/fake/bin/npx"


@pytest.fixture
def npx(monkeypatch):
    monkeypatch.setattr(_env, "npx_exe", lambda: FAKE_NPX)
    monkeypatch.setattr(_env, "node_exe", lambda: "/fake/bin/node")
    monkeypatch.setattr(_env, "ffmpeg_exe", lambda: "/fake/bin/ffmpeg")
    monkeypatch.setenv("HYPERFRAMES_VERSION", "0.8.54")


class FakePopen:
    """Thay Popen: `mode` = "ok" | "timeout" | "nav" | "fail"."""
    made = []

    def __init__(self, argv, cwd=None, mode="ok", **kw):
        self.argv, self.cwd, self.kw, self.mode = argv, cwd, kw, mode
        self.pid, self.returncode, self.killed = 4242, None, False
        FakePopen.made.append(self)

    def communicate(self, timeout=None):
        if self.mode == "timeout":
            raise subprocess.TimeoutExpired(self.argv, timeout)
        if self.mode == "nav":
            self.returncode = 1
            return b"Error: page.goto: Navigation timeout of 60000 ms exceeded\n", None
        if self.mode == "fail":
            self.returncode = 1
            return b"chrome-headless-shell not found\n", None
        with open(os.path.join(self.cwd, probe.OUT), "wb") as f:
            f.write(b"\0" * 64)
        self.returncode = 0
        return b"Render complete\n", None

    def wait(self, timeout=None):
        return self.returncode


def _popen(mode):
    return lambda argv, **kw: FakePopen(argv, mode=mode, **kw)


def test_probe_ok_renders_a_tiny_project_with_draft_quality(npx, tmp_path):
    res = probe.run_probe(timeout=30, workdir=str(tmp_path), popen=_popen("ok"))
    p = FakePopen.made[-1]
    assert p.argv == [FAKE_NPX, "--yes", "hyperframes@0.8.54", "render", "-o", probe.OUT,
                      "-q", "draft"]
    assert p.kw.get("shell") in (None, False)
    assert res["hyperframes"] == "0.8.54"
    html = (tmp_path / "index.html").read_text(encoding="utf-8")
    # Không tài nguyên ngoài: mạng chậm không được giả làm "render kẹt".
    assert "http://" not in html and "https://" not in html
    assert "window.__timelines" in html, "thiếu timeline thì engine chờ 45 s — phép thử hết rẻ"
    for name in ("hyperframes.json", "meta.json", "package.json"):
        assert (tmp_path / name).is_file()


def test_probe_timeout_is_STUCK_kills_the_tree_and_says_restart(npx, tmp_path, monkeypatch):
    killed = []
    monkeypatch.setattr(probe, "_kill_tree", lambda p: killed.append(p.pid))
    with pytest.raises(EngineError) as e:
        probe.run_probe(timeout=5, workdir=str(tmp_path), popen=_popen("timeout"))
    assert e.value.code == contract.ENGINE_ERROR
    msg = str(e.value)
    assert msg.startswith(probe.STUCK + ":") and "khởi động lại máy" in msg
    assert killed == [4242], "quá giờ phải giết cả cây tiến trình (Chrome mồ côi làm máy kẹt thêm)"


def test_probe_navigation_timeout_is_STUCK(npx, tmp_path):
    with pytest.raises(EngineError) as e:
        probe.run_probe(timeout=30, workdir=str(tmp_path), popen=_popen("nav"))
    assert str(e.value).startswith(probe.STUCK + ":")
    assert "Navigation timeout" in str(e.value)


def test_probe_other_failure_is_NOT_called_stuck(npx, tmp_path):
    with pytest.raises(EngineError) as e:
        probe.run_probe(timeout=30, workdir=str(tmp_path), popen=_popen("fail"))
    msg = str(e.value)
    assert not msg.startswith(probe.STUCK), "lỗi cài đặt không được đổ cho 'máy kẹt'"
    assert "doctor --hf" in msg and "chrome-headless-shell" in msg


def test_probe_new_process_group_so_the_tree_can_be_killed(npx, tmp_path):
    probe.run_probe(timeout=30, workdir=str(tmp_path), popen=_popen("ok"))
    kw = FakePopen.made[-1].kw
    if os.name == "nt":
        assert kw.get("creationflags") == subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        assert kw.get("start_new_session") is True


def test_probe_own_tempdir_is_removed(npx, monkeypatch, tmp_path):
    d = tmp_path / "own"
    monkeypatch.setattr(probe.tempfile, "mkdtemp", lambda prefix="": str(d))
    probe.run_probe(timeout=30, popen=_popen("ok"))
    assert not d.exists()


def test_probe_missing_npx_is_station_missing(monkeypatch):
    monkeypatch.setattr(_env, "npx_exe", lambda: None)
    with pytest.raises(StationMissing):
        probe.run_probe(timeout=30, popen=_popen("ok"))


def test_probe_cli_json_contract(npx, monkeypatch, capsys):
    monkeypatch.setattr(probe, "run_probe", lambda t: {"seconds": 7.2, "hyperframes": "0.8.54"})
    assert probe.main(["--json"]) == 0
    out = last_json(capsys.readouterr().out)
    assert out == {"ok": True, "seconds": 7.2, "hyperframes": "0.8.54"}


def test_probe_cli_stuck_is_code_1_with_marker(npx, monkeypatch, capsys):
    def boom(t):
        raise EngineError(f"{probe.STUCK}: môi trường render kẹt — khởi động lại máy rồi chạy lại")
    monkeypatch.setattr(probe, "run_probe", boom)
    assert probe.main(["--json", "--timeout", "3"]) == contract.ENGINE_ERROR
    out = last_json(capsys.readouterr().out)
    assert out["ok"] is False and out["error"].startswith(probe.STUCK)


def test_probe_cli_rejects_zero_timeout(capsys):
    assert probe.main(["--timeout", "0", "--json"]) == contract.CONTRACT_ERROR


# ── render_project: Navigation timeout ở MỌI lần thử ⇒ gợi ý khởi động lại ──────────────

class NavRun:
    def __init__(self, errs):
        self.errs, self.calls = list(errs), 0

    def __call__(self, argv, **kw):
        err = self.errs[min(self.calls, len(self.errs) - 1)]
        self.calls += 1
        raise subprocess.CalledProcessError(1, argv, output=b"", stderr=err)


NAV = b"Error: page.goto: Navigation timeout of 60000 ms exceeded (frame 0)\n"


def test_render_all_attempts_navigation_timeout_says_restart(npx, monkeypatch, tmp_path):
    monkeypatch.setattr(render.subprocess, "run", NavRun([NAV]))
    with pytest.raises(EngineError) as e:
        render.render_project(str(tmp_path), "s.mp4", sleep=lambda _s: None)
    msg = str(e.value)
    assert render.STUCK_PREFIX in msg and "khởi động lại máy" in msg
    assert "video-studio probe" in msg
    assert e.value.code == contract.ENGINE_ERROR


def test_render_mixed_failures_keep_the_doctor_hint(npx, monkeypatch, tmp_path):
    monkeypatch.setattr(render.subprocess, "run", NavRun([NAV, b"worker died\n", NAV]))
    with pytest.raises(EngineError) as e:
        render.render_project(str(tmp_path), "s.mp4", sleep=lambda _s: None)
    assert render.STUCK_PREFIX not in str(e.value)
    assert "doctor --hf" in str(e.value)


def test_probe_and_render_share_one_marker():
    assert probe.STUCK == render.STUCK_PREFIX == "RENDER_STUCK"


def test_probe_cli_missing_npx_is_code_3_with_json(monkeypatch, capsys):
    monkeypatch.setattr(_env, "npx_exe", lambda: None)
    assert probe.main(["--json"]) == contract.STATION_MISSING
    assert last_json(capsys.readouterr().out)["code"] == contract.STATION_MISSING


def test_probe_cli_stuck_prints_no_traceback(npx, monkeypatch, capsys):
    """Kết quả đo không phải sự cố: đuôi log của runner (và tin Telegram) phải là câu đọc được."""
    def boom(t):
        raise EngineError(f"{probe.STUCK}: kẹt")
    monkeypatch.setattr(probe, "run_probe", boom)
    probe.main(["--timeout", "3"])
    assert "Traceback" not in capsys.readouterr().err


# ── làm ấm NGOÀI trần giờ (review 02/10: tải lần đầu không được tính là "kẹt") ──────────

@pytest.fixture(autouse=True)
def _khong_lam_am_that(monkeypatch, request):
    if "warm" not in request.node.name:
        monkeypatch.setattr(probe, "warm_up", lambda: None)


class WarmRun:
    def __init__(self, *codes):
        self.codes, self.calls = list(codes), []

    def __call__(self, argv, **kw):
        self.calls.append((argv, kw))
        c = self.codes[len(self.calls) - 1]
        if c == "timeout":
            raise subprocess.TimeoutExpired(argv, kw.get("timeout"))
        return subprocess.CompletedProcess(argv, c, b"", b"loi tai goi")


def test_warm_up_co_chromium_chi_goi_version(npx):
    run = WarmRun(0)
    probe.warm_up(run=run, chromium=True)
    assert [c[0][3:] for c in run.calls] == [["--version"]]
    assert run.calls[0][1]["timeout"] == probe.WARM_TIMEOUT


def test_warm_up_thieu_chromium_thi_browser_ensure(npx):
    run = WarmRun(0, 0)
    probe.warm_up(run=run, chromium=False)
    assert run.calls[1][0][3:] == ["browser", "ensure"]


def test_warm_up_qua_gio_la_ma_3_KHONG_phai_ket(npx):
    with pytest.raises(StationMissing) as e:
        probe.warm_up(run=WarmRun("timeout"), chromium=True)
    assert probe.STUCK not in str(e.value) and e.value.code == contract.STATION_MISSING


def test_warm_up_hong_la_ma_3(npx):
    with pytest.raises(StationMissing):
        probe.warm_up(run=WarmRun(0, 1), chromium=False)


def test_run_probe_lam_am_TRUOC_khi_bam_gio(npx, tmp_path):
    thu_tu = []
    probe.run_probe(timeout=30, workdir=str(tmp_path), popen=lambda a, **k: (
        thu_tu.append("render"), FakePopen(a, mode="ok", **k))[1],
        warm=lambda: thu_tu.append("warm"))
    assert thu_tu == ["warm", "render"]


def test_navigation_timeout_trong_log_nhung_render_DAT_thi_khong_ket(npx, tmp_path):
    class Qua(FakePopen):
        def communicate(self, timeout=None):
            out, _ = super().communicate(timeout)
            return b"retry: Navigation timeout of 60000 ms exceeded\n" + out, None
    res = probe.run_probe(timeout=30, workdir=str(tmp_path),
                          popen=lambda a, **k: Qua(a, mode="ok", **k))
    assert res["hyperframes"] == "0.8.54"


def test_warm_mac_dinh_qua_gio_thi_GIET_CA_CAY(npx, monkeypatch):
    """Review 02/10 vòng 2: `subprocess.run` treo trên Windows khi cháu giữ pipe."""
    giet = []

    class P:
        pid, returncode = 77, None

        def __init__(self, *a, **k):
            pass

        def communicate(self, timeout=None):
            raise subprocess.TimeoutExpired("npx", timeout)

    monkeypatch.setattr(probe.subprocess, "Popen", P)
    monkeypatch.setattr(probe, "_kill_tree", lambda p: giet.append(p.pid))
    with pytest.raises(StationMissing):
        probe.warm_up(chromium=True)
    assert giet == [77]
