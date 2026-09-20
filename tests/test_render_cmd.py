"""Cổng KỶ LUẬT GỌI TIẾN TRÌNH CON của bước render.

Không có Node, không có HyperFrames, không có mạng: `subprocess.run` bị thay bằng hàm giả ghi
lại đúng những gì được truyền. Cái được khẳng định ở đây là những thứ chỉ hỏng trên máy khác
(mac, CI) hoặc hỏng âm thầm (bản trôi, shell nuốt tham số), nên phải bắt bằng test chứ không
bằng mắt:

* tham số 1 là **argv list**, không phải chuỗi lệnh;
* **không** có `shell` bật — truyền list qua shell trên POSIX chỉ chạy phần tử đầu;
* bản HyperFrames lấy từ biến môi trường / `station.json`, và phải là bản CỤ THỂ;
* thử lại đúng số lần, và stderr của HyperFrames luôn được in ra log.
"""
import json
import os
import subprocess

import pytest

from conftest import last_json
from video_studio import _env, contract, render
from video_studio.contract import ContractError, EngineError, StationMissing

FAKE_NPX = "/fake/bin/npx"


class Rec:
    """Thay cho subprocess.run: ghi lại lời gọi, trả kết quả theo kịch bản."""

    def __init__(self, outcomes=(0,)):
        self.calls = []
        self.outcomes = list(outcomes)

    def __call__(self, argv, **kw):
        self.calls.append((argv, kw))
        code = self.outcomes[min(len(self.calls) - 1, len(self.outcomes) - 1)]
        if code == "timeout":
            raise subprocess.TimeoutExpired(argv, kw.get("timeout") or 1)
        if code:
            raise subprocess.CalledProcessError(code, argv, output=b"",
                                                stderr=b"HyperFrames: worker died\nline2\n")
        return subprocess.CompletedProcess(argv, 0, b"", b"")


@pytest.fixture
def npx(monkeypatch):
    monkeypatch.setattr(_env, "npx_exe", lambda: FAKE_NPX)
    monkeypatch.setattr(_env, "node_exe", lambda: "/fake/bin/node")
    monkeypatch.setattr(_env, "ffmpeg_exe", lambda: "/other/bin/ffmpeg")


@pytest.fixture
def run(monkeypatch):
    rec = Rec()
    monkeypatch.setattr(render.subprocess, "run", rec)
    return rec


# ── argv + shell ────────────────────────────────────────────────────────────────────────

def test_argv_is_a_list_with_pinned_version(npx, monkeypatch):
    monkeypatch.setenv("HYPERFRAMES_VERSION", "0.8.51")
    argv = render.hyperframes_argv("render", "-o", "out.mp4")
    assert isinstance(argv, list)
    assert argv == [FAKE_NPX, "--yes", "hyperframes@0.8.51", "render", "-o", "out.mp4"]


@pytest.mark.parametrize("bad", ["latest", "^0.8.0", "~0.8.1", "0.8", "next", "0.8.x"])
def test_floating_version_is_a_contract_error(npx, monkeypatch, bad):
    monkeypatch.setenv("HYPERFRAMES_VERSION", bad)
    with pytest.raises(ContractError) as e:
        render.hyperframes_argv("render")
    assert e.value.code == contract.CONTRACT_ERROR


def test_render_passes_a_list_and_never_uses_a_shell(npx, run, tmp_path, monkeypatch):
    monkeypatch.setenv("HYPERFRAMES_VERSION", "0.7.94")
    render.render_project(str(tmp_path), "silent.mp4", timeout=42)
    argv, kw = run.calls[0]
    assert isinstance(argv, list) and argv[0] == FAKE_NPX
    assert kw.get("shell") in (None, False), "argv list KHÔNG được đi qua shell"
    assert kw["cwd"] == str(tmp_path)
    assert kw["timeout"] == 42 and kw["check"] is True


def test_render_puts_node_and_ffmpeg_first_on_path(npx, run, tmp_path):
    render.render_project(str(tmp_path), "s.mp4")
    env = run.calls[0][1]["env"]
    head = env["PATH"].split(os.pathsep)[:2]
    assert head == [os.path.dirname("/fake/bin/node"), os.path.dirname("/other/bin/ffmpeg")]
    assert env["HF_HUB_OFFLINE"] == "1" and env["TRANSFORMERS_OFFLINE"] == "1"


def test_missing_npx_is_station_missing(monkeypatch):
    monkeypatch.setattr(_env, "npx_exe", lambda: None)
    with pytest.raises(StationMissing) as e:
        render.hyperframes_argv("render")
    assert e.value.code == contract.STATION_MISSING
    assert "npx" in str(e.value).lower()


# ── thử lại ─────────────────────────────────────────────────────────────────────────────

def test_retries_then_succeeds(npx, monkeypatch, tmp_path):
    rec = Rec([1, 1, 0])
    monkeypatch.setattr(render.subprocess, "run", rec)
    slept = []
    render.render_project(str(tmp_path), "s.mp4", sleep=slept.append)
    assert len(rec.calls) == 3 and slept == [render.RETRY_SLEEP] * 2


def test_gives_up_with_engine_error_and_logs_stderr(npx, monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(render.subprocess, "run", Rec([1]))
    with pytest.raises(EngineError) as e:
        render.render_project(str(tmp_path), "s.mp4", sleep=lambda _s: None)
    assert e.value.code == contract.ENGINE_ERROR
    err = capsys.readouterr().err
    assert "worker died" in err, "stderr của HyperFrames phải vào log, không bị nuốt"


def test_timeout_is_not_retried(npx, monkeypatch, tmp_path):
    rec = Rec(["timeout"])
    monkeypatch.setattr(render.subprocess, "run", rec)
    with pytest.raises(EngineError):
        render.render_project(str(tmp_path), "s.mp4", sleep=lambda _s: None)
    assert len(rec.calls) == 1


# ── index.html + font ───────────────────────────────────────────────────────────────────

def test_write_index_substitutes_the_font_stack(tmp_path, monkeypatch):
    html = "<style>body{font-family:%s}</style>" % render.FONT_TOKEN
    p = render.write_index(str(tmp_path), html)
    assert render.FONT_TOKEN not in open(p, encoding="utf-8").read()
    assert "Inter" in open(p, encoding="utf-8").read()
    monkeypatch.setenv("VIDEO_FONT", "Be Vietnam Pro")
    render.write_index(str(tmp_path), html)
    assert "'Be Vietnam Pro', Inter" in open(p, encoding="utf-8").read()


def test_no_template_carries_a_hardcoded_font():
    """Template chỉ được mang chỗ trống — tên font cứng là bug trên máy không có font đó."""
    root = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "video_studio", "templates")
    for dp, _dn, fn in os.walk(root):
        for name in fn:
            if not name.endswith((".py", ".html")):
                continue
            text = open(os.path.join(dp, name), encoding="utf-8").read()
            assert "font-family:\"" not in text and "font-family:Inter" not in text, name


# ── hợp đồng CLI ────────────────────────────────────────────────────────────────────────

def test_bad_spec_exits_2_with_one_json_line(tmp_path, capsys):
    bad = tmp_path / "spec.json"
    bad.write_text(json.dumps({"schema_version": 1, "date": "2026-01-01"}), encoding="utf-8")
    rc = render.main(["--project", "topstory", "--input", str(bad),
                      "--out", str(tmp_path / "o"), "--json"])
    assert rc == contract.CONTRACT_ERROR
    payload = last_json(capsys.readouterr().out)
    assert payload["ok"] is False and payload["code"] == 2 and "brand" in payload["error"]


def test_brand_file_can_supply_a_spec_that_has_none(tmp_path, capsys, monkeypatch):
    """Một spec dùng lại cho nhiều kênh: brand đến từ `--brand`, và phải được trộn TRƯỚC khi kiểm."""
    spec_p = tmp_path / "spec.json"
    spec_p.write_text(json.dumps({"schema_version": 1, "date": "2026-01-02",
                                  "top_story": {"sections": [{"title": "x"}]}}), encoding="utf-8")
    brand_p = tmp_path / "brand.json"
    brand_p.write_text(json.dumps({"a": "Tin", "b": "Ngày", "site": "vi-du.example"}),
                       encoding="utf-8")
    seen = {}
    monkeypatch.setattr(render, "_template",
                        lambda p: lambda spec, out: seen.update(spec=spec, out=out) or [])
    rc = render.main(["--project", "topstory", "--input", str(spec_p), "--brand", str(brand_p),
                      "--out", str(tmp_path / "o"), "--json"])
    assert rc == contract.OK
    assert seen["spec"]["brand"]["site"] == "vi-du.example"
    assert seen["spec"]["_spec_path"] == str(spec_p), "đường tương đối phải neo vào file spec"
    assert last_json(capsys.readouterr().out)["ok"] is True


def test_missing_render_dependency_is_code_3_not_a_traceback(tmp_path, capsys, monkeypatch):
    """Thiếu numpy/voice_studio là 'cài tiếp' (3), không phải 'thử lại đi' (1)."""
    spec_p = tmp_path / "spec.json"
    spec_p.write_text(json.dumps({"schema_version": 1, "date": "2026-01-02",
                                  "brand": {"a": "A", "b": "B", "site": "s.example"},
                                  "top_story": {"sections": [{"title": "x"}]}}), encoding="utf-8")

    def boom(_spec, _out):
        raise ImportError(name="numpy")
    monkeypatch.setattr(render, "_template", lambda p: boom)
    rc = render.main(["--project", "topstory", "--input", str(spec_p),
                      "--out", str(tmp_path / "o"), "--json"])
    assert rc == contract.STATION_MISSING
    payload = last_json(capsys.readouterr().out)
    assert payload["code"] == 3 and "numpy" in payload["error"]
    assert "[voice]" in payload["error"], "phải nói ĐÚNG lệnh cần chạy"


def test_unknown_project_is_rejected_by_argparse(tmp_path, capsys):
    rc = render.main(["--project", "khong-co", "--input", "x.json", "--out", str(tmp_path),
                      "--json"])
    assert rc == contract.CONTRACT_ERROR
    assert last_json(capsys.readouterr().out)["ok"] is False


def test_engine_block_reports_the_pinned_version(npx, monkeypatch):
    monkeypatch.setenv("HYPERFRAMES_VERSION", "0.8.51")
    info = render.engine_versions()
    assert info["hyperframes"] == "0.8.51"
    assert info["video_studio"] and info["contract"]
