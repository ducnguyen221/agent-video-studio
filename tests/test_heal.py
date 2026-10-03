"""Cổng P1-25: `video-studio probe --heal` — gói chẩn đoán + thang tự chữa trước khi bắt khởi động lại.

Mac mini 02/10/2026: render kẹt, khởi động lại là hết, và sau đó không còn chứng cứ nào để tìm
nguyên nhân. Bốn thứ phải đúng:

* kẹt ⇒ chụp gói chẩn đoán TRƯỚC khi chữa (chữa xong là mất hiện trường), không lọt secret;
* thang: giết bộ dựng MỒ CÔI (không đụng lượt dựng còn cha) → xoá profile tạm cũ → chờ → thử lại;
* qua ở lần nào thì mã 0 và nói rõ đã tự chữa; hết thang mới `RENDER_STUCK` + đường gói;
* hỏng kiểu khác `RENDER_STUCK` thì KHÔNG chạy thang (thang chữa máy kẹt, không chữa cài đặt).

Không Node, không tiến trình thật: probe, `ps`, kill và sleep đều là hàm giả.
"""
import json
import os
import time

import pytest

from conftest import last_json
from video_studio import contract, heal, probe
from video_studio.contract import EngineError, StationMissing

STUCK_ERR = f"{probe.STUCK}: môi trường render kẹt — khởi động lại máy rồi chạy lại\nđuôi log"
OK = {"seconds": 2.8, "hyperframes": "0.8.54"}


class Probe:
    """Chuỗi kết quả lần lượt: "ok" | "stuck" | "fail"."""

    def __init__(self, *seq):
        self.seq, self.calls = list(seq), 0

    def __call__(self, timeout):
        r = self.seq[min(self.calls, len(self.seq) - 1)]
        self.calls += 1
        if r == "stuck":
            e = EngineError(STUCK_ERR)
            e.output = "page.goto: Navigation timeout of 60000 ms exceeded"
            raise e
        if r == "fail":
            raise StationMissing("thiếu npx")
        return dict(OK)


PROCS = [
    {"pid": 1, "ppid": 0, "name": "launchd", "cmd": "/sbin/launchd"},
    # mồ côi: Chrome của HyperFrames bị bỏ lại khi cha chết, kèm một helper con của nó
    {"pid": 500, "ppid": 1, "name": "chrome-headless-shell",
     "cmd": "/x/chrome-headless-shell --user-data-dir=/tmp/puppeteer_dev_chrome_profile-a"},
    {"pid": 501, "ppid": 500, "name": "chrome-headless-shell",
     "cmd": "/x/chrome-headless-shell --type=renderer"},
    # còn cha: một lượt dựng khác đang chạy thật — KHÔNG được đụng
    {"pid": 600, "ppid": 77, "name": "node", "cmd": "node /n/hyperframes render -o out.mp4"},
    {"pid": 77, "ppid": 1, "name": "pwsh", "cmd": "pwsh -File run.ps1 --api-key=SECRET123456789"},
    # mồ côi nhưng không phải bộ dựng
    {"pid": 700, "ppid": 1, "name": "ollama", "cmd": "ollama serve"},
]


@pytest.fixture
def quiet(monkeypatch, tmp_path):
    """Không `ps` thật, không kill thật, không sleep thật, thư mục tạm riêng."""
    monkeypatch.setattr(heal, "list_processes", lambda run=None: [dict(p) for p in PROCS])
    monkeypatch.setattr(heal, "_NT", False)          # PROCS mang hình POSIX (ppid 1 = mồ côi)
    killed, slept, logs = [], [], []
    tmp = tmp_path / "tmp"
    tmp.mkdir()

    def run(argv, **kw):
        class R:
            returncode = 0
            stdout = b"TOKEN=abc123 1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZ012345\n"
            stderr = b""
        return R()

    kw = dict(diag_dir=str(tmp_path / "render-stuck"), sleep=slept.append, run=run,
              kill=killed.append, tmpdir=str(tmp), log=logs.append)
    return kw, killed, slept, logs, tmp


# ── thang ──────────────────────────────────────────────────────────────────────────────

def test_healthy_probe_takes_no_snapshot_and_no_action(quiet, tmp_path):
    kw, killed, slept, logs, _ = quiet
    res = heal.ladder(Probe("ok"), 30, **kw)
    assert res["heal"] is None and res["seconds"] == 2.8
    assert killed == [] and slept == []
    assert not (tmp_path / "render-stuck").exists(), "máy khoẻ thì không chụp gì"


def test_stuck_then_recovers_after_first_wait(quiet):
    kw, killed, slept, logs, _ = quiet
    pr = Probe("stuck", "ok")
    res = heal.ladder(pr, 30, **kw)
    assert pr.calls == 2 and slept == [60]
    h = res["heal"]
    assert h["recovered"] is True and h["step"] == 2
    assert os.path.isdir(h["diag"]), "gói chẩn đoán phải chụp TRƯỚC khi chữa"
    assert killed == [500, 501], "giết mồ côi + cây con, không đụng lượt dựng còn cha"
    assert "RENDER_HEAL=recovered step=2" in logs
    assert any(l.startswith("RENDER_DIAG=") for l in logs)


def test_stuck_to_the_end_raises_with_diag_and_reboot_hint(quiet):
    kw, killed, slept, logs, _ = quiet
    pr = Probe("stuck")
    with pytest.raises(EngineError) as e:
        heal.ladder(pr, 30, **kw)
    assert pr.calls == 3 and slept == [60, 600], "thang mặc định: 60 s rồi 600 s"
    msg = str(e.value)
    assert msg.startswith(probe.STUCK + ":") and "khởi động lại máy" in msg
    assert e.value.diag in msg and os.path.isdir(e.value.diag)
    assert "RENDER_HEAL=failed steps=3" in logs


def test_other_failure_first_runs_no_ladder(quiet, tmp_path):
    kw, killed, slept, logs, _ = quiet
    with pytest.raises(StationMissing):
        heal.ladder(Probe("fail"), 30, **kw)
    assert killed == [] and slept == []
    assert not (tmp_path / "render-stuck").exists()


def test_other_failure_mid_ladder_is_raised_as_is(quiet):
    kw, *_ = quiet
    with pytest.raises(StationMissing):
        heal.ladder(Probe("stuck", "fail"), 30, **kw)


def test_custom_waits_are_used(quiet):
    kw, _, slept, *_ = quiet
    kw["waits"] = (1, 1)
    with pytest.raises(EngineError):
        heal.ladder(Probe("stuck"), 1, **kw)
    assert slept == [1, 1]


# ── mồ côi ─────────────────────────────────────────────────────────────────────────────

def test_find_orphans_posix_ppid_1_only_render_processes():
    ra = heal.find_orphans(PROCS, self_pid=99999, nt=False)
    assert [p["pid"] for p in ra] == [500, 501]


def test_find_orphans_windows_parent_gone():
    procs = [
        {"pid": 10, "ppid": 4, "name": "explorer.exe", "cmd": ""},
        {"pid": 20, "ppid": 3333, "name": "chrome-headless-shell.exe",
         "cmd": "chrome-headless-shell.exe --headless"},       # cha 3333 đã chết
        {"pid": 21, "ppid": 20, "name": "chrome-headless-shell.exe", "cmd": "--type=gpu"},
        {"pid": 30, "ppid": 10, "name": "node.exe", "cmd": "node hyperframes render"},  # còn cha
    ]
    assert [p["pid"] for p in heal.find_orphans(procs, self_pid=1, nt=True)] == [20, 21]


def test_find_orphans_never_returns_self():
    me = [{"pid": 4242, "ppid": 1, "name": "python", "cmd": "python -m hyperframes-probe"}]
    assert heal.find_orphans(me, self_pid=4242, nt=False) == []


# ── profile tạm ────────────────────────────────────────────────────────────────────────

def test_clean_profiles_removes_only_old_matching_dirs(tmp_path):
    now = time.time()
    for name, age in [("puppeteer_dev_chrome_profile-old", 7200), ("hyperframes-abc", 7200),
                      ("video-studio-probe-x", 7200), ("puppeteer_dev_chrome_profile-new", 60),
                      ("khac-old", 7200)]:
        d = tmp_path / name
        d.mkdir()
        os.utime(d, (now - age, now - age))
    (tmp_path / "hyperframes.log").write_text("x")             # file, không phải thư mục
    xoa = heal.clean_profiles(str(tmp_path), now=now)
    assert sorted(os.path.basename(p) for p in xoa) == [
        "hyperframes-abc", "puppeteer_dev_chrome_profile-old", "video-studio-probe-x"]
    assert (tmp_path / "puppeteer_dev_chrome_profile-new").is_dir(), "profile mới = lượt đang chạy"
    assert (tmp_path / "khac-old").is_dir() and (tmp_path / "hyperframes.log").is_file()


# ── gói chẩn đoán ──────────────────────────────────────────────────────────────────────

def test_diag_bundle_has_evidence_and_no_secret(quiet, tmp_path):
    kw, *_ = quiet
    d = heal.diag_bundle(str(tmp_path / "rs"), STUCK_ERR, "Navigation timeout", run=kw["run"],
                         tmpdir=kw["tmpdir"], procs=[dict(p) for p in PROCS])
    files = sorted(os.listdir(d))
    for f in ("probe-error.txt", "ps-top-cpu.txt", "render-procs.txt", "temp-profiles.txt",
              "summary.json"):
        assert f in files
    allt = "".join(open(os.path.join(d, f), encoding="utf-8").read() for f in files)
    assert "SECRET123456789" not in allt, "dòng lệnh tiến trình không được vào gói"
    assert "abc123" not in allt and "ABCDEFGHIJKLMNOPQRSTUVWXYZ012345" not in allt, "phải che token"
    rp = open(os.path.join(d, "render-procs.txt"), encoding="utf-8").read()
    assert "2 mồ côi" in rp and "pid=500" in rp and "MO_COI" in rp
    assert json.load(open(os.path.join(d, "summary.json"), encoding="utf-8"))["orphans"] == 2


def test_che_masks_common_secret_shapes():
    s = heal._che("api_key=XYZ password: hunter2 bot 1234567:AAAAAAAAAAAAAAAAAAAAAAAA ghp_abcdefghijklmnop1234")
    assert "XYZ" not in s and "hunter2" not in s and "AAAAAAAA" not in s and "ghp_abc" not in s


# ── CLI ────────────────────────────────────────────────────────────────────────────────

def _khong_cham_may_that(monkeypatch):
    """CLI đi đường thật: chặn `ps`/`pmset`/`log show` (macOS: tới 120 s) và thư mục tạm thật."""
    def goi(root, *a, **k):
        d = os.path.join(root, "gia")
        os.makedirs(d, exist_ok=True)
        return d
    monkeypatch.setattr(heal, "diag_bundle", goi)
    monkeypatch.setattr(heal, "clean_profiles", lambda *a, **k: [])

def test_cli_heal_recovered_json_carries_heal(monkeypatch, capsys, tmp_path):
    pr = Probe("stuck", "ok")
    monkeypatch.setattr(probe, "run_probe", pr)
    monkeypatch.setattr(heal, "list_processes", lambda run=None: [])
    monkeypatch.setattr(heal.time, "sleep", lambda s: None)
    _khong_cham_may_that(monkeypatch)
    code = probe.main(["--json", "--heal", "--diag-dir", str(tmp_path), "--heal-waits", "0,0"])
    assert code == 0
    out = last_json(capsys.readouterr().out)
    assert out["ok"] is True and out["heal"]["recovered"] is True and out["heal"]["step"] == 2


def test_cli_heal_exhausted_is_code_1_with_diag(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(probe, "run_probe", Probe("stuck"))
    monkeypatch.setattr(heal, "list_processes", lambda run=None: [])
    monkeypatch.setattr(heal.time, "sleep", lambda s: None)
    _khong_cham_may_that(monkeypatch)
    code = probe.main(["--json", "--heal", "--diag-dir", str(tmp_path), "--heal-waits", "0,0"])
    assert code == contract.ENGINE_ERROR
    out = last_json(capsys.readouterr().out)
    assert out["error"].startswith(probe.STUCK) and os.path.isdir(out["diag"])


def test_cli_without_heal_json_unchanged(monkeypatch, capsys):
    monkeypatch.setattr(probe, "run_probe", lambda t: dict(OK))
    assert probe.main(["--json"]) == 0
    assert last_json(capsys.readouterr().out) == {"ok": True, **OK}


@pytest.mark.parametrize("bad", ["", "a,b", "-1,5"])
def test_cli_bad_heal_waits_is_code_2(bad, capsys):
    assert probe.main(["--json", "--heal", "--heal-waits", bad]) == contract.CONTRACT_ERROR
