"""Sổ nguồn Hypit (`upstream.json`, `NOTICE`): ghim commit, quan hệ ý tưởng, đích local có thật."""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KEY = "hypit-techniques"


def _entry():
    data = json.loads((ROOT / "upstream.json").read_text(encoding="utf-8"))
    for section in data.values():
        if isinstance(section, dict) and KEY in section:
            return section[KEY]
    raise AssertionError(f"upstream.json không có khoá {KEY}")


def test_hypit_reference_is_pinned_and_honest():
    entry = _entry()
    assert re.fullmatch(r"[0-9a-f]{40}", entry["ref"])
    assert entry["relationship"] == "idea_reference"
    assert entry["code_copied"] is False
    assert entry["assets_copied"] is False
    local = entry["local_paths"]
    assert "skills/video-reference-analysis/SKILL.md" in local
    missing = [p for p in local if not (ROOT / p).exists()]
    assert not missing, f"local_paths không tồn tại: {missing}"
    notice = (ROOT / "NOTICE").read_text(encoding="utf-8")
    assert entry["ref"] in notice
    assert entry["ref"] in entry["license_url"]


def test_hypit_upstream_paths_sorted_unique_relative():
    paths = _entry()["upstream_paths"]
    assert len(paths) == len(set(paths))
    assert paths == sorted(paths)
    assert all(not p.startswith(("/", "\\")) and ".." not in p.split("/") for p in paths)
