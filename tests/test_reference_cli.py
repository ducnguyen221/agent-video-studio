"""`video-studio reference`: parser, dispatcher, mẫu tệp, doctor, package-data.

Không ffmpeg, không mạng: hàm `media.*` / `subs.*` được giả khi cần; cái được kiểm là cách lệnh
đổi lỗi thành mã thoát và những gì `init` / `audit` ghi hoặc báo.
"""
import json
import os
import re
from pathlib import Path

import pytest

from video_studio import _env, cli, doctor
from video_studio.contract import StationMissing
from video_studio.reference import gate, media

ROOT = Path(__file__).resolve().parent.parent


def run(argv, capsys):
    rc = cli.main(["reference", *argv])
    out = capsys.readouterr()
    last = [ln for ln in out.out.splitlines() if ln.strip()]
    return rc, (json.loads(last[-1]) if last and last[-1].startswith("{") else None), out.err


def init(tmp_path, capsys, *extra, name="demo"):
    return run(["init", "--name", name, "--dir", str(tmp_path / "ref"), "--json", *extra], capsys)


def test_reference_is_listed_in_help(capsys):
    assert "reference" in cli.COMMANDS
    assert cli.main(["--help"]) == 0
    assert "reference" in capsys.readouterr().out
    assert cli.main(["reference", "--help"]) == 0
    text = capsys.readouterr().out
    for action in ("init", "frames", "tiles", "transcribe", "fetch", "audit"):
        assert action in text


def test_init_creates_layout_and_pending_provenance(tmp_path, capsys):
    rc, payload, _ = init(tmp_path, capsys)
    assert rc == 0 and payload["ok"] is True
    project = tmp_path / "ref" / "demo"
    assert payload["project"] == str(project)
    assert payload["rights_status"] == "rights_pending"
    assert payload["next"]
    for d in ("source", "evidence/frames", "evidence/tiles", "transcripts", "assets"):
        assert (project / d).is_dir(), d
    for f in ("provenance.json", "reference-map.md", "brief.md", "treatment.md"):
        assert (project / f).is_file(), f
        assert f in payload["files"]
    prov = gate.load_provenance(str(project))
    assert prov["project"] == "demo" and prov["rights_status"] == "rights_pending"
    assert prov["reference"] == {"url": None, "local_file": None, "sha256": None, "title": None}
    for f in ("reference-map.md", "brief.md", "treatment.md"):
        text = (project / f).read_text(encoding="utf-8")
        assert "demo" in text and "{{" not in text


def test_init_without_station_is_code_3(capsys):
    rc, payload, _ = run(["init", "--name", "demo", "--json"], capsys)
    assert rc == 3 and payload["ok"] is False and payload["code"] == 3


def test_init_defaults_to_station_reference_dir(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(_env, "station_dir", lambda: str(tmp_path / "st"))
    rc, payload, _ = run(["init", "--name", "demo", "--json"], capsys)
    assert rc == 0
    assert (tmp_path / "st" / "reference" / "demo" / "provenance.json").is_file()


@pytest.mark.parametrize("bad", ["../demo", "a/b", "..", ""])
def test_init_refuses_path_name(tmp_path, capsys, bad):
    rc, payload, _ = init(tmp_path, capsys, name=bad)
    assert rc == 2 and payload["code"] == 2
    assert not (tmp_path / "demo").exists()
    ref = tmp_path / "ref"
    assert not ref.exists() or not any(ref.iterdir())


def test_init_never_overwrites(tmp_path, capsys):
    assert init(tmp_path, capsys)[0] == 0
    brief = tmp_path / "ref" / "demo" / "brief.md"
    brief.write_text("sửa tay", encoding="utf-8")
    rc, payload, _ = init(tmp_path, capsys)
    assert rc == 2 and "đã có" in payload["error"]
    assert brief.read_text(encoding="utf-8") == "sửa tay"


def test_init_rejects_internal_url(tmp_path, capsys):
    rc, payload, _ = init(tmp_path, capsys, "--url", "http://127.0.0.1/x")
    assert rc == 2 and payload["code"] == 2
    assert not (tmp_path / "ref" / "demo").exists()


def test_init_records_normalized_reference_url(tmp_path, capsys):
    url = "HTTPS://Example.COM/watch?v=1"
    rc, _, _ = init(tmp_path, capsys, "--url", url)
    assert rc == 0
    prov = gate.load_provenance(str(tmp_path / "ref" / "demo"))
    assert prov["reference"]["url"] == gate.check_url(url)


def test_init_records_local_file_hash_without_copy(tmp_path, capsys):
    clip = tmp_path / "clip.mp4"
    clip.write_bytes(b"abc")
    rc, _, _ = init(tmp_path, capsys, "--file", str(clip))
    assert rc == 0
    project = tmp_path / "ref" / "demo"
    ref = gate.load_provenance(str(project))["reference"]
    assert ref["sha256"] == gate.sha256_file(str(clip))
    assert os.path.samefile(ref["local_file"], clip)
    assert not any(p.name == "clip.mp4" for p in project.rglob("*"))


def test_init_missing_file_is_2(tmp_path, capsys):
    rc, payload, _ = init(tmp_path, capsys, "--file", str(tmp_path / "nope.mp4"))
    assert rc == 2 and payload["code"] == 2
    assert not (tmp_path / "ref" / "demo").exists()


def test_transcribe_cli_bad_language_is_2(tmp_path, capsys):
    clip = tmp_path / "v.mp4"
    clip.write_bytes(b"x")
    rc, payload, _ = run(["transcribe", "--input", str(clip), "--project", str(tmp_path),
                          "--language", "../x", "--json"], capsys)
    assert rc == 2 and payload["code"] == 2


def test_transcribe_cli_passes_arguments(tmp_path, monkeypatch, capsys):
    seen = {}

    def fake(input_path, project_dir, subs=None, language="vi", force=False):
        seen.update(input=input_path, project=project_dir, subs=subs, language=language, force=force)
        return {"transcript": "t.json", "source": "subtitles:file", "granularity": "cue", "entries": 1}

    monkeypatch.setattr("video_studio.reference.subs.transcribe", fake)
    rc, payload, _ = run(["transcribe", "--input", "a.mp4", "--project", "p", "--subs", "s.srt",
                          "--language", "en", "--force", "--json"], capsys)
    assert rc == 0 and payload["transcript"] == "t.json"
    assert seen == {"input": "a.mp4", "project": "p", "subs": "s.srt", "language": "en", "force": True}


def test_audit_clean_exit_0(tmp_path, capsys):
    init(tmp_path, capsys)
    rc, payload, _ = run(["audit", "--project", str(tmp_path / "ref" / "demo"), "--json"], capsys)
    assert rc == 0 and payload["ok"] is True and payload["checked"] == 0


def test_audit_findings_exit_2_with_json_list(tmp_path, capsys):
    init(tmp_path, capsys)
    project = tmp_path / "ref" / "demo"
    (project / "assets" / "hero.png").write_bytes(b"png")
    rc, payload, err = run(["audit", "--project", str(project), "--json"], capsys)
    assert rc == 2
    assert payload["ok"] is False and payload["code"] == 2
    assert payload["error"] == "1 phát hiện"
    assert payload["findings"] == [{"path": "assets/hero.png", "problem": "chưa khai trong assets"}]
    assert "assets/hero.png" in err


def test_audit_assets_outside_project_is_2(tmp_path, capsys):
    init(tmp_path, capsys)
    rc, payload, _ = run(["audit", "--project", str(tmp_path / "ref" / "demo"),
                          "--assets", str(tmp_path), "--json"], capsys)
    assert rc == 2 and payload["code"] == 2


def test_frames_cli_parses_marks_and_returns_list(tmp_path, monkeypatch, capsys):
    seen = {}

    def fake(input_path, out_dir, at, force=False):
        seen.update(at=at, force=force, out=out_dir)
        return [{"requested": m, "file": "f.png"} for m in at]

    monkeypatch.setattr(media, "extract_frames", fake)
    rc, payload, _ = run(["frames", "--input", "v.mp4", "--at", "1,2.5", "--out", "o", "--json"], capsys)
    assert rc == 0 and seen["at"] == [1.0, 2.5] and seen["force"] is False
    assert len(payload["frames"]) == 2


def test_frames_cli_bad_mark_is_2(capsys):
    rc, payload, _ = run(["frames", "--input", "v.mp4", "--at", "1,abc", "--out", "o", "--json"], capsys)
    assert rc == 2 and payload["code"] == 2


def test_frames_cli_maps_station_missing_to_3(monkeypatch, capsys):
    def boom(*a, **k):
        raise StationMissing("thiếu ffmpeg")

    monkeypatch.setattr(media, "extract_frames", boom)
    rc, payload, _ = run(["frames", "--input", "v.mp4", "--at", "1", "--out", "o", "--json"], capsys)
    assert rc == 3 and payload["code"] == 3


def test_tiles_cli_passes_arguments(monkeypatch, capsys):
    seen = {}

    def fake(input_path, out_dir, every, cols=4, rows=4, width=320, label=False, force=False):
        seen.update(every=every, cols=cols, rows=rows, width=width, label=label, force=force)
        return {"every": every, "sheets": []}

    monkeypatch.setattr(media, "contact_sheets", fake)
    rc, payload, _ = run(["tiles", "--input", "v.mp4", "--every", "2", "--out", "o", "--cols", "3",
                          "--label", "--json"], capsys)
    assert rc == 0 and payload["every"] == 2.0 and payload["sheets"] == []
    assert seen == {"every": 2.0, "cols": 3, "rows": 4, "width": 320, "label": True, "force": False}


def test_unknown_action_is_2(capsys):
    rc, _, _ = run(["explode", "--json"], capsys)
    assert rc == 2


def test_missing_action_is_2(capsys):
    rc, _, _ = run([], capsys)
    assert rc == 2


def test_fetch_parser_accepts_contract_arguments():
    from video_studio.reference import build_parser

    args = build_parser().parse_args(
        ["fetch", "--url", "https://example.com/v", "--allow-url", "https://example.com/v",
         "--project", "p", "--go", "--max-mb", "100", "--sub-langs", "vi,en"])
    assert (args.go, args.max_mb, args.sub_langs) == (True, 100, "vi,en")


def test_reference_checks_only_warn(monkeypatch):
    monkeypatch.setattr(_env, "ytdlp_exe", lambda: None)
    monkeypatch.setattr("video_studio.edit.transcribe.available", lambda: False)
    checks = doctor.reference_checks()
    assert {c["name"] for c in checks} == {"yt-dlp", "faster-whisper"}
    assert all(c["level"] == "warn" and c["ok"] is False and c["hint"] for c in checks)


def test_reference_checks_warn_when_fetch_would_refuse_ytdlp(monkeypatch):
    monkeypatch.setattr(_env, "ytdlp_exe", lambda: "C:/x/yt-dlp.cmd")
    monkeypatch.setattr("video_studio.edit.transcribe.available", lambda: True)
    yt = next(c for c in doctor.reference_checks() if c["name"] == "yt-dlp")
    assert yt["ok"] is False and yt["level"] == "warn"
    assert "fetch sẽ từ chối" in yt["detail"] and yt["hint"] == doctor.HINT_YTDLP


def test_reference_checks_ok_when_present(monkeypatch):
    monkeypatch.setattr(_env, "ytdlp_exe", lambda: "C:/x/yt-dlp.exe")
    monkeypatch.setattr("video_studio.edit.transcribe.available", lambda: True)
    assert all(c["ok"] and c["level"] == "ok" for c in doctor.reference_checks())


def test_ytdlp_exe_uses_ytdlp_dir(tmp_path, monkeypatch):
    seen = {}
    monkeypatch.setattr(_env, "_tool", lambda name, var: seen.update(name=name, var=var) or "x")
    assert _env.ytdlp_exe() == "x" and seen == {"name": "yt-dlp", "var": "YTDLP_DIR"}


def test_templates_are_package_data():
    assert "reference/templates/*.md" in (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    for f in ("reference-map.md", "brief.md", "treatment.md"):
        text = (ROOT / "video_studio" / "reference" / "templates" / f).read_text(encoding="utf-8")
        assert "{{project}}" in text
    assert "{{date}}" in (ROOT / "video_studio" / "reference" / "templates"
                          / "reference-map.md").read_text(encoding="utf-8")


def test_env_example_and_conftest_know_ytdlp_dir():
    assert re.search(r"^YTDLP_DIR=", (ROOT / ".env.example").read_text(encoding="utf-8"), re.M)
    assert "YTDLP_DIR" in (ROOT / "tests" / "conftest.py").read_text(encoding="utf-8")


def test_page_counts_thirteen_commands():
    assert 'data-to="13">13</b> lệnh' in (ROOT / "docs" / "index.html").read_text(encoding="utf-8")


def test_frames_and_tiles_cli_pass_absolute_out(monkeypatch, tmp_path, capsys):
    monkeypatch.chdir(tmp_path)
    seen = []
    monkeypatch.setattr(media, "extract_frames", lambda i, out, at, force=False: seen.append(out) or [])
    monkeypatch.setattr(media, "contact_sheets", lambda i, out, every, **k: seen.append(out) or {})
    _, p1, _ = run(["frames", "--input", "v.mp4", "--at", "1", "--out=-x", "--json"], capsys)
    _, p2, _ = run(["tiles", "--input", "v.mp4", "--every", "2", "--out=-x", "--json"], capsys)
    assert all(os.path.isabs(o) for o in seen) and len(seen) == 2
    assert os.path.isabs(p1["out"]) and os.path.isabs(p2["out"])


def test_init_race_on_existing_project_is_2(tmp_path, monkeypatch, capsys):
    def racing(path, *a, **k):
        raise FileExistsError(path)

    monkeypatch.setattr(os, "mkdir", racing)
    rc, payload, _ = init(tmp_path, capsys)
    assert rc == 2 and payload["code"] == 2


def test_init_leaves_nothing_when_a_template_is_missing(tmp_path, monkeypatch, capsys):
    from video_studio import reference

    def broken(template, project, today):
        raise FileNotFoundError(template)

    monkeypatch.setattr(reference, "_render", broken)
    rc, _, _ = init(tmp_path, capsys)
    assert rc == 1
    assert not (tmp_path / "ref" / "demo").exists()


def test_init_cleans_up_when_writing_fails_midway(tmp_path, monkeypatch, capsys):
    def boom(project, prov):
        raise RuntimeError("lỗi ngoài hệ tệp")

    monkeypatch.setattr(gate, "save_provenance", boom)
    rc, _, _ = init(tmp_path, capsys)
    assert rc == 1
    assert not (tmp_path / "ref" / "demo").exists()


def test_audit_ctrl_c_is_code_2(tmp_path, monkeypatch, capsys):
    def interrupt(*a, **k):
        raise KeyboardInterrupt

    monkeypatch.setattr(gate, "audit_assets", interrupt)
    rc, payload, _ = run(["audit", "--project", str(tmp_path), "--json"], capsys)
    assert rc == 2 and payload["ok"] is False


def test_init_permission_error_on_mkdir_is_2(tmp_path, monkeypatch, capsys):
    def deny(path, *a, **k):
        raise PermissionError(13, "từ chối", path)

    monkeypatch.setattr(os, "mkdir", deny)
    rc, payload, _ = init(tmp_path, capsys)
    assert rc == 2 and payload["code"] == 2 and "demo" in payload["error"]


def test_init_permission_error_on_subdir_is_2_and_cleans_up(tmp_path, monkeypatch, capsys):
    real = os.makedirs

    def deny(path, *a, **k):
        if str(path).endswith("transcripts"):
            raise PermissionError(13, "từ chối", path)
        return real(path, *a, **k)

    monkeypatch.setattr(os, "makedirs", deny)
    rc, payload, _ = init(tmp_path, capsys)
    assert rc == 2 and payload["code"] == 2
    assert not (tmp_path / "ref" / "demo").exists()


def test_init_unreadable_file_is_2(tmp_path, monkeypatch, capsys):
    clip = tmp_path / "clip.mp4"
    clip.write_bytes(b"abc")

    def deny(path):
        raise PermissionError(13, "từ chối", path)

    monkeypatch.setattr(gate, "sha256_file", deny)
    rc, payload, _ = init(tmp_path, capsys, "--file", str(clip))
    assert rc == 2 and payload["code"] == 2 and "clip.mp4" in payload["error"]
    assert not (tmp_path / "ref" / "demo").exists()


def test_init_dir_that_is_a_file_is_2(tmp_path, capsys):
    f = tmp_path / "ref"
    f.write_text("x", encoding="utf-8")
    rc, payload, _ = init(tmp_path, capsys)
    assert rc == 2 and "--dir không phải thư mục" in payload["error"]
