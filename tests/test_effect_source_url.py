import os

import pytest

from video_studio.contract import ContractError
from video_studio.effect_library import capture
from video_studio.effect_library.catalog import CHECKS, _validate_metadata_entry, validate_entry


def reference(source="https://example.invalid/library"):
    return {
        "id": "VE-source-url", "name": "Source URL", "kind": "reference",
        "maturity": "reference_only", "rights": "unknown", "source": source,
        "runtime": "online", "tags": [], "roles": [], "techniques": [],
        "ratios": [], "checks": dict.fromkeys(CHECKS, "not_run"), "asset": None,
    }


@pytest.mark.parametrize("source", [
    r"https://example.invalid\library",
    r"https://example.invalid/library\item",
    r"https://example.invalid/library?redirect=\item",
])
def test_reference_source_rejects_backslash(source):
    with pytest.raises(ContractError, match="source URL"):
        validate_entry(reference(source))


def test_license_url_still_rejects_backslash():
    value = reference()
    value["license_url"] = r"https://example.invalid\license"
    with pytest.raises(ValueError, match="license_url"):
        _validate_metadata_entry(value)


@pytest.mark.parametrize("source", [
    "https://example.invalid/library/",
    "http://example.invalid/library?item=one",
    "https://example.invalid/a%5Cb",
])
def test_valid_reference_sources_remain_accepted(source):
    assert _validate_metadata_entry(reference(source))["source"] == source


@pytest.mark.skipif(os.name != "nt", reason="capture is Windows-only")
def test_bad_source_is_rejected_before_station_write(tmp_path):
    station = tmp_path / "station"
    entries = station / "effect-library" / "entries"
    entries.mkdir(parents=True)
    with pytest.raises(ContractError, match="source URL"):
        capture(tmp_path, station, reference(r"https://example.invalid\library"))
    assert list(entries.iterdir()) == []


@pytest.mark.parametrize("source", [
    " https://example.invalid/library",
    "\thttps://example.invalid/library",
    " https://example.invalid\\library",
    "\thttps://example.invalid\\library",
])
def test_reference_rejects_prefixed_whitespace(source):
    with pytest.raises((ContractError, ValueError)):
        _validate_metadata_entry(reference(source))


@pytest.mark.skipif(os.name != "nt", reason="capture is Windows-only")
@pytest.mark.parametrize("source", [" https://example.invalid\\library", "\thttps://example.invalid/library"])
def test_prefixed_source_rejected_before_station_write(tmp_path, source):
    station = tmp_path / "station"
    entries = station / "effect-library" / "entries"
    entries.mkdir(parents=True)
    with pytest.raises((ContractError, ValueError)):
        capture(tmp_path, station, reference(source))
    assert list(entries.iterdir()) == []
