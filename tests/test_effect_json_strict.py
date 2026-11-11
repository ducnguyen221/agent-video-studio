import json
import math
import os

import pytest

from video_studio.contract import ContractError
from video_studio.effect_library import capture, search


def _prompt():
    return {"id": "VE-strict-json", "name": "Synthetic prompt", "kind": "prompt", "maturity": "candidate", "rights": "owned", "source": "synthetic", "runtime": "browser", "tags": [], "roles": [], "techniques": [], "ratios": [], "checks": dict.fromkeys(("static_check", "preview", "render", "audio", "ratio_test", "reuse_evidence"), "not_run"), "prompt_text": "synthetic prompt", "extra": {"nested": [{"score": 1.0}]}}


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_capture_rejects_nested_nonfinite_without_publishing(tmp_path, value):
    project = tmp_path / "project"
    entries = tmp_path / "station" / "effect-library" / "entries"
    project.mkdir()
    entries.mkdir(parents=True)
    manifest = _prompt()
    manifest["extra"]["nested"][0]["score"] = value
    with pytest.raises(ContractError, match="JSON"):
        capture(project, tmp_path / "station", manifest)
    assert list(entries.iterdir()) == []


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_search_rejects_nonfinite_catalog_metadata(tmp_path, value):
    record = _prompt()
    record["extra"]["nested"][0]["score"] = value
    catalog = tmp_path / "entries.json"
    catalog.write_text(json.dumps([record]), encoding="utf-8")
    with pytest.raises(ContractError, match="JSON"):
        search(repo_entries=catalog)


def test_finite_metadata_search_is_preserved(tmp_path):
    record = _prompt()
    catalog = tmp_path / "entries.json"
    catalog.write_text(json.dumps([record], allow_nan=False), encoding="utf-8")
    assert search(repo_entries=catalog)[0]["extra"] == record["extra"]

@pytest.mark.skipif(os.name != "nt", reason="station capture is Windows only")
def test_finite_metadata_captures_and_searches_without_change(tmp_path):
    project = tmp_path / "project"
    station = tmp_path / "station"
    project.mkdir()
    (station / "effect-library" / "entries").mkdir(parents=True)
    record = _prompt()
    assert capture(project, station, record) == record["id"]
    assert search("synthetic prompt", station=station)[0]["extra"] == record["extra"]
