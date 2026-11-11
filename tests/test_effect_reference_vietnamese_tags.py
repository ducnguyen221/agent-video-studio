from pathlib import Path

import pytest

from video_studio.effect_library import search


@pytest.mark.parametrize("query", ["chữ chuyển động", "chu chuyen dong"])
def test_animated_text_references_are_discoverable_in_vietnamese(query):
    root = Path(__file__).resolve().parents[1]
    catalog = root / "skills/video-theme-library/assets/effect-library/entries.json"
    rows = search(query, {"kind": "reference"}, repo_entries=catalog, limit=50)
    by_id = {row["id"]: row for row in rows}
    for identifier in ("VE-react-bits", "VE-magic-ui", "VE-motion-primitives"):
        assert identifier in by_id
        assert by_id[identifier]["rights"] == "unknown"
        assert by_id[identifier]["maturity"] == "reference_only"
        assert by_id[identifier]["checks"]["render"] == "not_run"

@pytest.mark.parametrize(
    ("query", "identifier"),
    [
        ("hiệu ứng hạt", "VE-react-bits"),
        ("hieu ung hat", "VE-react-bits"),
        ("hiệu ứng chữ sản phẩm", "VE-magic-ui"),
        ("hieu ung chu san pham", "VE-magic-ui"),
    ],
)
def test_effect_sources_match_vietnamese_descriptions_without_relaxing_filters(query, identifier):
    catalog = Path(__file__).resolve().parents[1] / "skills/video-theme-library/assets/effect-library/entries.json"
    def ids(filters=None, **kwargs):
        return {item["id"] for item in search(query, filters, repo_entries=catalog, limit=100, **kwargs)}

    assert identifier in ids({"kind": "reference", "rights": "unknown", "check.render": "not_run"})
    assert identifier not in ids({"kind": "component"})
    assert identifier not in ids({"rights": "owned"})
    assert identifier not in ids({"check.render": "pass"})
    assert identifier not in ids({"ratio": "16:9"})
    assert identifier in ids({"ratio": "16:9"}, include_unknown_ratio=True)
    assert identifier not in {row["id"] for row in search(query + " unicorn", repo_entries=catalog, limit=100)}
