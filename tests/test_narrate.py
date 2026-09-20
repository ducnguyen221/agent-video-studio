"""`video-studio narrate` — lồng giọng vào video câm, và với --project thì render trước.

Không có engine giọng thật ở đây: `voice_studio` là bản giả (conftest), HyperFrames là một
hàm giả. Cái được kiểm là HỢP ĐỒNG: tham số đi đúng chỗ, bản câm trung gian không nằm lại
trong thư mục giao hàng, thiếu repo giọng ra mã 3 kèm lệnh cài, và mọi lỗi thành mã thoát.
"""
import json
import os

import pytest

from conftest import fake_voice_studio, last_json
from video_studio import narrate as nar
from video_studio import projects, voice
from video_studio.contract import ContractError, StationMissing


@pytest.fixture
def station(tmp_path, monkeypatch):
    st = tmp_path / "st"
    (st / "projects" / "demo").mkdir(parents=True)
    (st / "scratch").mkdir()
    monkeypatch.setenv("VIDEO_STATION", str(st))
    return st


def _silent(tmp_path, name="in.mp4"):
    p = tmp_path / name
    p.write_text("silent", encoding="utf-8")
    return str(p)


# ── đường cơ bản: video có sẵn ──────────────────────────────────────────────────────────

def test_narrate_passes_every_option_through_to_the_voice_repo(tmp_path, monkeypatch):
    pkg = fake_voice_studio(monkeypatch)
    out = str(tmp_path / "final.mp4")
    rc = nar.main(["--video", _silent(tmp_path), "--text", "Xin chào", "--out", out,
                   "--profile", "demo", "--mode", "shortest", "--speed", "1.1",
                   "--seed", "7", "--bgm", "lofi", "--bgm-volume", "0.2", "--normalize"])
    assert rc == 0
    kind, args = pkg.calls[-1]
    assert kind == "narrate"
    assert args["profile"] == "demo" and args["mode"] == "shortest"
    assert args["speed"] == 1.1 and args["seed"] == 7
    assert args["bgm"] == "lofi" and args["bgm_volume"] == 0.2
    assert args["normalize"] is True and args["text"] == "Xin chào"
    assert os.path.isfile(out)


def test_narrate_reads_the_text_file_path_through(tmp_path, monkeypatch):
    pkg = fake_voice_studio(monkeypatch)
    script = tmp_path / "loi.txt"
    script.write_text("lời dẫn dài", encoding="utf-8")
    assert nar.main(["--video", _silent(tmp_path), "--file", str(script),
                     "--out", str(tmp_path / "o.mp4")]) == 0
    args = pkg.calls[-1][1]
    assert args["file"] == str(script) and args["text"] is None


def test_json_result_is_one_line_with_engine_versions(tmp_path, monkeypatch, capsys):
    fake_voice_studio(monkeypatch, version="1.2.3")
    monkeypatch.setenv("HYPERFRAMES_VERSION", "0.7.94")
    assert nar.main(["--video", _silent(tmp_path), "--text", "a",
                     "--out", str(tmp_path / "o.mp4"), "--json"]) == 0
    data = last_json(capsys.readouterr().out)
    assert data["ok"] is True
    assert data["engine"]["voice_studio"] == "1.2.3"
    assert data["engine"]["hyperframes"] == "0.7.94"
    assert data["outputs"][0]["duration"] == 12.5
    assert "total" in data["timings"]


def test_missing_video_is_contract_error(tmp_path, monkeypatch):
    fake_voice_studio(monkeypatch)
    assert nar.main(["--video", str(tmp_path / "khong-co.mp4"), "--text", "a",
                     "--out", str(tmp_path / "o.mp4")]) == 2


def test_without_the_voice_repo_it_is_code_3_with_the_install_command(tmp_path, monkeypatch,
                                                                     capsys):
    monkeypatch.setitem(__import__("sys").modules, "voice_studio", None)
    monkeypatch.setattr(voice, "available", lambda: False)
    rc = nar.main(["--video", _silent(tmp_path), "--text", "a", "--out", str(tmp_path / "o.mp4"),
                   "--json"])
    assert rc == 3
    err = capsys.readouterr()
    assert "pip install -e" in err.err
    assert json.loads(err.out.strip().splitlines()[-1])["code"] == 3


def test_text_and_file_are_mutually_exclusive(tmp_path):
    assert nar.main(["--video", _silent(tmp_path), "--text", "a", "--file", "b",
                     "--out", "o.mp4"]) == 2


def test_video_and_project_are_mutually_exclusive(tmp_path):
    assert nar.main(["--video", _silent(tmp_path), "--project", "demo", "--text", "a",
                     "--out", "o.mp4"]) == 2


# ── --project: render rồi lồng tiếng trong một lệnh ─────────────────────────────────────

def test_project_renders_first_then_narrates_and_removes_the_silent_file(
        tmp_path, station, monkeypatch):
    pkg = fake_voice_studio(monkeypatch)
    seen = {}

    def fake_render(proj_dir, out_file, **kw):
        seen["proj"] = proj_dir
        seen["out"] = out_file
        with open(out_file, "w", encoding="utf-8") as f:
            f.write("silent")
        return out_file

    monkeypatch.setattr(nar.render, "render_project", fake_render)
    out = str(tmp_path / "final.mp4")
    assert nar.main(["--project", "demo", "--text", "a", "--out", out]) == 0
    assert seen["proj"] == str(station / "projects" / "demo")
    # bản câm nằm trong scratch của TRẠM, không nằm cạnh sản phẩm, và đã bị dọn
    assert os.path.dirname(seen["out"]).startswith(str(station / "scratch"))
    assert not os.path.exists(seen["out"])
    assert [n for n in os.listdir(os.path.dirname(out)) if n.endswith(nar.SILENT_SUFFIX)] == []
    assert pkg.calls[-1][1]["video"] == seen["out"]


def test_keep_silent_keeps_the_intermediate(tmp_path, station, monkeypatch):
    fake_voice_studio(monkeypatch)
    seen = {}

    def fake_render(proj_dir, out_file, **kw):
        seen["out"] = out_file
        open(out_file, "w").close()
        return out_file

    monkeypatch.setattr(nar.render, "render_project", fake_render)
    assert nar.main(["--project", "demo", "--text", "a", "--out", str(tmp_path / "f.mp4"),
                     "--keep-silent"]) == 0
    assert os.path.isfile(seen["out"])


def test_silent_file_is_cleaned_even_when_narration_fails(tmp_path, station, monkeypatch):
    def boom(args):
        raise RuntimeError("engine giọng sập")

    fake_voice_studio(monkeypatch, narrate=boom)
    seen = {}

    def fake_render(proj_dir, out_file, **kw):
        seen["out"] = out_file
        open(out_file, "w").close()
        return out_file

    monkeypatch.setattr(nar.render, "render_project", fake_render)
    assert nar.main(["--project", "demo", "--text", "a", "--out", str(tmp_path / "f.mp4")]) == 1
    assert not os.path.exists(seen["out"])


def test_unknown_project_name_is_station_missing(station, tmp_path, monkeypatch):
    fake_voice_studio(monkeypatch)
    with pytest.raises(StationMissing) as e:
        nar.resolve_project("khong-co")
    assert "video-studio init" in str(e.value)


def test_project_accepts_a_plain_directory(tmp_path):
    d = tmp_path / "loose-project"
    d.mkdir()
    assert nar.resolve_project(str(d)) == str(d)


def test_empty_project_name_is_contract_error():
    with pytest.raises(ContractError):
        nar.resolve_project("  ")


def test_silent_path_lands_in_station_scratch(station):
    p = nar._silent_path(os.path.join("x", "final.mp4"))
    assert p.startswith(str(station / "scratch"))
    assert p.endswith("final.mp4" + nar.SILENT_SUFFIX)
    assert os.path.isdir(os.path.dirname(p))


# ── adapter sang repo giọng ─────────────────────────────────────────────────────────────

def test_adapter_builds_voice_argv_without_empty_flags(tmp_path, monkeypatch):
    pkg = fake_voice_studio(monkeypatch)
    voice.narrate(_silent(tmp_path), str(tmp_path / "o.mp4"), text="a")
    args = pkg.calls[-1][1]
    assert args["profile"] is None and args["bgm"] is None
    assert args["lang"] == "Vietnamese", "mặc định phải đến từ parser CỦA repo giọng"
    assert args["seed"] == 42


def test_adapter_works_without_build_parser(tmp_path, monkeypatch):
    """Bản repo giọng cũ không có `build_parser` vẫn gọi được (Namespace tối thiểu)."""
    pkg = fake_voice_studio(monkeypatch)
    monkeypatch.delattr(pkg.narrate, "build_parser")
    voice.narrate(_silent(tmp_path), str(tmp_path / "o.mp4"), text="a", mode="shortest")
    args = pkg.calls[-1][1]
    assert args["mode"] == "shortest" and args["text"] == "a"


def test_a_voice_repo_with_different_flags_is_code_2_WITH_a_json_line(tmp_path, monkeypatch,
                                                                      capsys):
    """`SystemExit` của argparse là `BaseException` ⇒ `contract.run` KHÔNG bắt được nó.

    Một bản `agent-voice-studio` lệch cờ làm `narrate --json` thoát 2 mà không in dòng JSON
    nào; bên gọi đọc dòng cuối stdout theo `CONTRACT.md` §2 thì vỡ chứ không đọc được lỗi.
    Nay `_args` đổi nó thành `ContractError` — vẫn mã 2, nhưng đi qua đường hợp đồng.
    """
    import argparse as ap_mod

    pkg = fake_voice_studio(monkeypatch)
    # Bản giọng "mới": bỏ --mode, thêm --style. Cờ của repo này không còn khớp.
    def picky_parser():
        ap = ap_mod.ArgumentParser(prog="voice-studio narrate")
        ap.add_argument("--video", required=True)
        ap.add_argument("--out", required=True)
        ap.add_argument("--text")
        ap.add_argument("--style")
        return ap

    monkeypatch.setattr(pkg.narrate, "build_parser", picky_parser)
    with pytest.raises(ContractError) as e:
        voice.narrate(_silent(tmp_path), str(tmp_path / "o.mp4"), text="a", mode="fit")
    assert e.value.code == 2
    assert "agent-voice-studio" in str(e.value)

    # Và qua CLI thật: đúng một dòng JSON cuối stdout, mã 2.
    rc = nar.main(["--video", _silent(tmp_path, "b.mp4"), "--out", str(tmp_path / "o2.mp4"),
                   "--text", "a", "--json"])
    assert rc == 2
    payload = last_json(capsys.readouterr().out)
    assert payload["ok"] is False and payload["code"] == 2


@pytest.mark.parametrize("style", [None, "", "none", "NONE", "off"])
def test_mix_bgm_does_nothing_without_a_style(style, monkeypatch, tmp_path):
    pkg = fake_voice_studio(monkeypatch)
    assert voice.mix_bgm(tmp_path / "a.mp4", style) is False
    assert pkg.calls == []


def test_mix_bgm_delegates_to_the_voice_repo(monkeypatch, tmp_path):
    pkg = fake_voice_studio(monkeypatch)
    assert voice.mix_bgm(tmp_path / "a.mp4", "lofi", 0.15) is True
    assert pkg.calls[-1][1]["bgm"] == "lofi" and pkg.calls[-1][1]["volume"] == 0.15


def test_version_and_available_never_raise(monkeypatch):
    monkeypatch.setitem(__import__("sys").modules, "voice_studio", None)
    assert voice.available() is False and voice.version() is None
