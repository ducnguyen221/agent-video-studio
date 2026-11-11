import os
from pathlib import Path

import pytest

from video_studio.contract import ContractError
from video_studio.effect_library import search
from video_studio.effect_library.distilled_sources import parse_ffmpeg, parse_hypit


ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.skipif(os.name != "nt", reason="secure distilled reader is Windows-only")
@pytest.mark.parametrize(("query", "identifier"), [
    ("cropdetect", "VE-ref-ffmpeg-cropdetect"),
    ("speedramp", "VE-ref-ffmpeg-speedramp"),
    ("multicam", "VE-ref-ffmpeg-multicam"),
    ("stabilize", "VE-ref-ffmpeg-stabilize"),
    ("continuity", "VE-ref-hypit-t7"),
    ("safe area", "VE-ref-hypit-t8"),
])
def test_distilled_specific_techniques_are_searchable(query, identifier):
    rows = search(query, distilled_root=ROOT, limit=100)
    item = next(row for row in rows if row["id"] == identifier)
    assert item["kind"] == "reference" and item["maturity"] == "reference_only"
    assert item["rights"] == "unknown" and item["checks"]["render"] == "not_run"
    assert item["source"] and item["upstream_source"].startswith("https://")
    assert "not installed" in item["runtime"]


def test_ffmpeg_tool_ids_are_stable_when_rows_are_reordered():
    doc = (ROOT / "skills/video-edit/references/ffmpeg-tool-index.md").read_text(encoding="utf-8")
    rows = parse_ffmpeg(doc)
    lines = doc.splitlines()
    indexes = [i for i, line in enumerate(lines) if line.startswith("| ") and "`" in line and line.count("|") == 4]
    reordered = list(lines)
    reordered[indexes[0]], reordered[indexes[-1]] = reordered[indexes[-1]], reordered[indexes[0]]
    assert {item["id"] for item in rows} == {item["id"] for item in parse_ffmpeg("\n".join(reordered))}
    assert len(rows) == 42


def test_hypit_extracts_nine_cards_without_recipes_or_commands():
    doc = (ROOT / "skills/video-routing/references/production-techniques.md").read_text(encoding="utf-8")
    rows = parse_hypit(doc)
    assert len(rows) == 9
    item = next(item for item in rows if item["id"] == "VE-ref-hypit-t7")
    assert "Continuity" in item["name"]
    assert "ffmpeg -" not in str(rows)


def test_hypit_rejects_provenance_only_in_code_fence():
    doc = (ROOT / "skills/video-routing/references/production-techniques.md").read_text(encoding="utf-8")
    lines = doc.splitlines()
    lines = [("```md\n" + line + "\n```") if "https://github.com/hypit-ai/hypit/blob/" in line else line for line in lines]
    with pytest.raises(ContractError, match="provenance"):
        parse_hypit("\n".join(lines))


@pytest.mark.parametrize("parser", [parse_ffmpeg, parse_hypit])
def test_distilled_parser_rejects_malformed_source(parser):
    with pytest.raises(ContractError):
        parser("## malformed source")


def test_cli_distilled_opt_out_is_explicit(capsys):
    from video_studio.effect_library.__main__ import main
    assert main(["--q", "cropdetect", "--no-distilled"]) == 1
    output = capsys.readouterr()
    assert "distilled" in output.err.lower()


def test_parsers_reject_duplicate_or_fenced_table_and_ignore_fenced_hypit_heading():
    ffmpeg = (ROOT / "skills/video-edit/references/ffmpeg-tool-index.md").read_text(encoding="utf-8")
    with pytest.raises(ContractError):
        parse_ffmpeg(ffmpeg.replace("`cropdetect`", "`probe`"))
    with pytest.raises(ContractError):
        parse_ffmpeg(ffmpeg.replace("| Đo và kiểm", "```\n| Đo và kiểm", 1))
    with pytest.raises(ContractError):
        parse_ffmpeg("```md\n" + ffmpeg + "\n```\n")
    with pytest.raises(ContractError):
        parse_ffmpeg(ffmpeg + "\n```\n42 tên sau là **tên trong tài liệu nguồn**\n```\n")
    with pytest.raises(ContractError):
        parse_ffmpeg(ffmpeg.replace("github.com/kajisho5/ffmpeg-skill", "github.com/unrelated/project"))
    with pytest.raises(ContractError):
        parse_ffmpeg(ffmpeg.replace("ffmpeg-skill, commit 6e42a79", "ffmpeg-skill, commit aaaaaaa"))
    hypit = (ROOT / "skills/video-routing/references/production-techniques.md").read_text(encoding="utf-8")
    assert len(parse_hypit(hypit + "\n```md\n## T1 — fake\n- **Dùng khi:** fake\n```\n")) == 9
    with pytest.raises(ContractError):
        parse_hypit(hypit + "\n## T10 — unexpected\n- **Dùng khi:** drift\n")
    with pytest.raises(ContractError):
        parse_hypit(hypit.replace("(#t1--qa-có-bằng-chứng)", "(#t7--continuity-nhân-vật-và-camera)"))
    with pytest.raises(ContractError):
        parse_hypit(hypit.replace("[T1 — QA có bằng chứng]", "[T1 — Other title]"))


@pytest.mark.skipif(os.name != "nt", reason="secure distilled reader is Windows-only")
def test_default_cli_search_includes_distilled(capsys):
    from video_studio.effect_library.__main__ import main
    assert main(["--q", "cropdetect"]) == 0
    assert "VE-ref-ffmpeg-cropdetect" in capsys.readouterr().out


def test_distilled_reader_fails_closed_on_unsupported_platform(monkeypatch):
    from video_studio.effect_library import distilled_sources
    monkeypatch.setattr(distilled_sources.os, "name", "unsupported")
    with pytest.raises(ContractError, match="not verified"):
        distilled_sources.load_distilled(ROOT)


def test_cli_preserves_other_sources_on_unsupported_platform(monkeypatch, capsys):
    from types import SimpleNamespace
    from video_studio.effect_library import __main__ as cli
    monkeypatch.setattr(cli, "os", SimpleNamespace(name="posix"))
    assert cli.main(["--q", "react bits"]) == 0
    output = capsys.readouterr()
    assert "VE-react-bits" in output.out
    assert "incomplete" in output.err and "FFmpeg and Hypit" in output.err
