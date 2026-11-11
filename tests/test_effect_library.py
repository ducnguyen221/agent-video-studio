import hashlib
import json
import os
from pathlib import Path

import pytest

from video_studio.contract import ContractError
from video_studio.effect_library import capture, search


def entry(data=b"effect"):
    return {"id": "VE-test", "name": "Nắng xiên", "kind": "component", "maturity": "candidate",
            "rights": "owned", "source": "original synthetic", "runtime": "browser", "tags": ["sun"],
            "roles": ["ambient"], "techniques": ["rays"], "ratios": ["16:9"],
            "asset": {"path": "effect.js", "sha256": hashlib.sha256(data).hexdigest()},
            "checks": {k: "not_run" for k in ("static_check", "preview", "render", "audio", "ratio_test", "reuse_evidence")}}


@pytest.mark.skipif(os.name == "nt", reason="Windows capture is supported with explicit existing station")
def test_capture_is_fail_closed(tmp_path):
    p, s = tmp_path / "project", tmp_path / "station"
    p.mkdir(); s.mkdir(); (p / "effect.js").write_bytes(b"effect")
    with pytest.raises(ContractError, match="not verified"):
        capture(p, s, entry())
    assert not (s / "effect-library").exists()


def test_reference_unknown_is_searchable(tmp_path):
    e = entry(); e.update(kind="reference", rights="unknown", asset=None, source="https://example.org")
    f = tmp_path / "entries.json"; f.write_text(json.dumps([e]), encoding="utf-8")
    assert search("nang", {"rights": "unknown"}, repo_entries=f)[0]["kind"] == "reference"


def test_repo_bundle_fails_closed_without_windows_verifier(tmp_path, monkeypatch):
    import importlib
    from types import SimpleNamespace
    module = importlib.import_module("video_studio.effect_library.search")
    record = entry()
    record.pop("asset")
    record["assets"] = [{"path": name, "sha256": "0" * 64, "rights": "owned"}
                        for name in ("a.js", "b.css")]
    catalog = tmp_path / "entries.json"
    catalog.write_text(json.dumps([record]), encoding="utf-8")
    monkeypatch.setattr(module, "os", SimpleNamespace(name="posix"))
    with pytest.raises(ContractError, match="unavailable"):
        search(repo_entries=catalog)


def test_search_requires_all_words_without_matching_inside_other_words(tmp_path):
    records = []
    for identifier, name in (("VE-rays", "Nắng xiên"), ("VE-weight", "Cân nặng"),
                             ("VE-substring", "Nangluong")):
        record = entry()
        record.update(id=identifier, name=name, kind="reference", rights="unknown", asset=None,
                      source="https://example.org/" + identifier)
        records.append(record)
    catalog = tmp_path / "entries.json"
    catalog.write_text(json.dumps(records), encoding="utf-8")
    assert [row["id"] for row in search("nang xien", repo_entries=catalog)] == ["VE-rays"]
    assert {row["id"] for row in search("nắng", repo_entries=catalog)} == {"VE-rays", "VE-weight"}
    assert search("nang khongco", repo_entries=catalog) == []
    assert search("!!!", repo_entries=catalog) == []
    assert len(search("", repo_entries=catalog)) == 3


def test_search_indexes_runtime_and_roles():
    root = Path(__file__).resolve().parents[1]
    catalog = root / "skills/video-theme-library/assets/effect-library/entries.json"
    assert any(row["id"] == "VE-react-bits" for row in search("GSAP", repo_entries=catalog))
    assert any(row["id"] == "VE-sun-rays" for row in search("ambient", repo_entries=catalog))


def test_search_ranks_consecutive_whole_words_above_substrings(tmp_path):
    records = []
    for identifier, name, tags in (("VE-a", "Bobcat dog", ["cat"]), ("VE-z", "Cat dog", [])):
        record = entry()
        record.update(id=identifier, name=name, tags=tags, kind="reference", rights="unknown", asset=None,
                      source="https://example.org/" + identifier)
        records.append(record)
    catalog = tmp_path / "entries.json"
    catalog.write_text(json.dumps(records), encoding="utf-8")
    assert [row["id"] for row in search("cat dog", repo_entries=catalog)] == ["VE-z", "VE-a"]


@pytest.mark.skipif(os.name != "nt", reason="station reader is fail-closed outside Windows")
def test_station_hash_is_checked(tmp_path):
    directory = tmp_path / "effect-library/entries/VE-test"
    directory.mkdir(parents=True)
    (directory / "effect.js").write_bytes(b"wrong")
    (directory / "entry.json").write_text(json.dumps(entry()), encoding="utf-8")
    with pytest.raises(ContractError, match="hash"): search(station=tmp_path)


@pytest.mark.parametrize("with_other_source", [False, True])
def test_explicit_station_without_entries_is_an_error(tmp_path, with_other_source):
    station = tmp_path / "station"
    station.mkdir()
    pm = tmp_path / "pm.json"
    pm.write_text(json.dumps({"entries": [{"id": "PM-example", "name": "Example"}]}), encoding="utf-8")
    with pytest.raises(ContractError, match="[Ss]tation.*entries"):
        search(station=station, pm_index=pm if with_other_source else None)


@pytest.mark.skipif(os.name != "nt", reason="station reader is fail-closed outside Windows")
def test_empty_existing_station_entries_is_searchable(tmp_path):
    (tmp_path / "effect-library" / "entries").mkdir(parents=True)
    assert search(station=tmp_path) == []


@pytest.mark.skipif(os.name != "nt", reason="station reader is fail-closed outside Windows")
def test_station_reader_failure_is_not_silently_ignored(tmp_path, monkeypatch):
    from video_studio.effect_library import _native_windows

    (tmp_path / "effect-library" / "entries").mkdir(parents=True)
    def fail_reader(_directory):
        raise OSError("failed to open or close native handle")
    monkeypatch.setattr(_native_windows, "search_experiment", fail_reader)
    with pytest.raises(ContractError, match="failed to open or close native handle"):
        search(station=tmp_path)


def test_prompt_motion_and_filters():
    index = Path(__file__).resolve().parents[1] / "skills/video-theme-library/assets/prompt-motion/index.json"
    results = search("", {"kind": "reference", "rights": "unknown"}, pm_index=index, limit=500)
    assert len(results) == 240
    assert all(x["maturity"] == "reference_only" for x in results)
    for check in ("static_check", "preview", "render", "audio", "ratio_test", "reuse_evidence"):
        assert len(search(filters={"check." + check: "not_run"}, pm_index=index, limit=500)) == 240
        assert search(filters={"check." + check: "pass"}, pm_index=index, limit=500) == []


def test_search_evidence_filters_distinguish_pass_fail_and_unrun(tmp_path):
    records = []
    for state in ("pass", "fail", "not_run"):
        record = entry()
        record.update(id="VE-" + state.replace("_", "-"), name="Example " + state,
                      kind="reference", rights="unknown", asset=None,
                      source="https://example.org/" + state)
        record["checks"]["render"] = state
        if state == "pass":
            record["evidence"] = {"render": "synthetic proof"}
        records.append(record)
    catalog = tmp_path / "entries.json"
    catalog.write_text(json.dumps(records), encoding="utf-8")
    pm = tmp_path / "pm.json"
    pm.write_text(json.dumps({"entries": [{"id": "PM-example", "name": "Example reference"}]}), encoding="utf-8")
    for state in ("pass", "fail"):
        rows = search(filters={"check.render": state}, repo_entries=catalog, pm_index=pm)
        assert [row["id"] for row in rows] == ["VE-" + state]
    rows = search(filters={"check.render": "not_run"}, repo_entries=catalog, pm_index=pm)
    assert {row["id"] for row in rows} == {"VE-not-run", "PM-example"}
    assert next(row for row in rows if row["id"] == "PM-example")["checks"]["render"] == "not_run"
    assert {row["id"] for row in search(filters={"check.render": "pass", "check.preview": "not_run"}, repo_entries=catalog)} == {"VE-pass"}


@pytest.mark.parametrize("value", ["unknown", "PASS", "", None, [], True])
def test_search_rejects_invalid_evidence_filter(value):
    with pytest.raises(ContractError, match="evidence"):
        search(filters={"check.render": value})


def test_cli_filters_prompt_motion_evidence(capsys, tmp_path):
    from video_studio.effect_library.__main__ import main
    pm = tmp_path / "pm.json"
    pm.write_text(json.dumps({"entries": [{"id": "PM-example", "name": "Example"}]}), encoding="utf-8")
    catalog = tmp_path / "entries.json"
    catalog.write_text("[]", encoding="utf-8")
    assert main(["--pm-index", str(pm), "--repo-entries", str(catalog), "--check", "render=pass"]) == 1
    assert json.loads(capsys.readouterr().out) == []
    assert main(["--pm-index", str(pm), "--repo-entries", str(catalog), "--check", "render=not_run"]) == 0
    assert json.loads(capsys.readouterr().out)[0]["entry"]["id"] == "PM-example"
    assert main(["--pm-index", str(pm), "--repo-entries", str(catalog), "--check", "render=pass", "--check", "render=pass"]) == 2
    assert "duplicate" in capsys.readouterr().err
    for invalid in ("render=unknown", "missing=pass", "render", "render=pass=fail"):
        assert main(["--pm-index", str(pm), "--repo-entries", str(catalog), "--check", invalid]) == 2
        assert "evidence filter" in capsys.readouterr().err


def test_invalid_check_key_is_rejected_even_without_catalog():
    with pytest.raises(ContractError, match="Unknown filter"):
        search(filters={"check.no_such_check": "pass"})


def test_repo_missing_check_is_not_assumed_unrun(tmp_path):
    record = entry()
    record.update(kind="reference", maturity="reference_only", rights="unknown", asset=None, source="https://example.org")
    del record["checks"]["render"]
    catalog = tmp_path / "entries.json"
    catalog.write_text(json.dumps([record]), encoding="utf-8")
    with pytest.raises(ContractError, match="checks"):
        search(filters={"check.render": "not_run"}, repo_entries=catalog)


@pytest.mark.skipif(os.name != "nt", reason="station reader is fail-closed outside Windows")
def test_evidence_filter_applies_to_station_entries(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    (project / "effect.js").write_bytes(b"effect")
    station = tmp_path / "station"
    (station / "effect-library" / "entries").mkdir(parents=True)
    record = entry()
    record["checks"]["static_check"] = "pass"
    record["evidence"] = {"static_check": "synthetic check"}
    capture(project, station, record)
    assert [row["id"] for row in search(filters={"check.static_check": "pass"}, station=station)] == ["VE-test"]
    assert search(filters={"check.render": "pass"}, station=station) == []


@pytest.mark.skipif(os.name != "nt", reason="station reader is fail-closed outside Windows")
def test_station_missing_check_is_not_assumed_unrun(tmp_path):
    directory = tmp_path / "effect-library/entries/VE-test"
    directory.mkdir(parents=True)
    record = entry()
    record.update(kind="reference", maturity="reference_only", rights="unknown", asset=None, source="https://example.org")
    del record["checks"]["render"]
    (directory / "entry.json").write_text(json.dumps(record), encoding="utf-8")
    with pytest.raises(ContractError, match="checks"):
        search(filters={"check.render": "not_run"}, station=tmp_path)


def test_validation_rejects_unsafe_paths_and_unsupported_urls():
    from video_studio.effect_library import validate_entry
    for path in ("../x", "C:/x", "a/../x", "a\\b", "a:bad"):
        value = entry(); value["asset"]["path"] = path
        with pytest.raises(ContractError):
            validate_entry(value)
    for source in ("javascript://example", "javascript:alert(1)", "file:///tmp/x", "https://example.com bad", "https://example.com:bad"):
        value = entry(); value["source"] = source
        with pytest.raises(ContractError):
            validate_entry(value)
    value = entry(); value["checks"]["render"] = "pass"
    with pytest.raises(ContractError, match="evidence"):
        validate_entry(value)


def test_cli_search_utf8():
    import subprocess
    import sys
    result = subprocess.run([sys.executable, "-m", "video_studio.effect_library", "--q", "nang xien", "--limit", "2"], capture_output=True, timeout=30)
    assert result.returncode == 0, result.stderr
    assert "VE-sun-rays" in result.stdout.decode("utf-8")


@pytest.mark.skipif(os.name != "nt", reason="station reader is fail-closed outside Windows")
def test_missing_station_manifest_is_error(tmp_path):
    (tmp_path / "effect-library/entries/VE-missing").mkdir(parents=True)
    with pytest.raises(ContractError, match="missing station entry manifest"):
        search(station=tmp_path)


def test_licensed_entry_requires_license_evidence():
    from video_studio.effect_library import validate_entry
    record = entry(); record["rights"] = "licensed"
    with pytest.raises(ContractError, match="license"):
        validate_entry(record)
    record["license"] = {"id": "MIT", "source": "LICENSE", "terms": "Keep notice"}
    assert validate_entry(record) is record


def test_public_capture_and_materialize_fail_closed_on_unverified_platform(monkeypatch, tmp_path):
    from types import SimpleNamespace
    from video_studio.effect_library import catalog
    monkeypatch.setattr(catalog, "os", SimpleNamespace(name="posix"))
    with pytest.raises(ContractError, match="not verified"):
        catalog.capture(tmp_path, tmp_path, entry())
    with pytest.raises(ContractError, match="not verified"):
        catalog.materialize(tmp_path, "VE-test", tmp_path, "asset.js")


def test_cli_main_search_returns_json_and_filters(capsys):
    from video_studio.effect_library.__main__ import main
    assert main(["--q", "nang xien", "--kind", "component", "--ratio", "16:9", "--limit", "2"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result and result[0]["entry"]["id"] == "VE-sun-rays"
    assert all(row["entry"]["kind"] == "component" and "16:9" in row["entry"]["ratios"] for row in result)


def test_cli_main_no_results_and_invalid_catalog(capsys, tmp_path):
    from video_studio.effect_library.__main__ import main
    assert main(["--q", "this-does-not-exist-876543"]) == 1
    assert json.loads(capsys.readouterr().out) == []
    assert main(["--pm-index", str(tmp_path / "missing.json")]) == 2
    assert "Cannot read catalog" in capsys.readouterr().err


def test_cli_main_rejects_nonpositive_limit(capsys):
    from video_studio.effect_library.__main__ import main
    assert main(["--limit", "0"]) == 2
    assert "positive integer" in capsys.readouterr().err


@pytest.mark.parametrize(("query", "identifier", "repository", "license_hint"), [
    ("react bits", "VE-react-bits", "https://github.com/DavidHDev/react-bits", "Commons Clause"),
    ("magic ui", "VE-magic-ui", "https://github.com/magicuidesign/magicui", "MIT"),
    ("motion primitives", "VE-motion-primitives", "https://github.com/ibelick/motion-primitives", "MIT"),
])
def test_cli_online_references_include_repository_and_license(capsys, query, identifier, repository, license_hint):
    from video_studio.effect_library.__main__ import main
    assert main(["--q", query, "--kind", "reference", "--limit", "5"]) == 0
    rows = json.loads(capsys.readouterr().out)
    record = next(row["entry"] for row in rows if row["entry"]["id"] == identifier)
    assert record["repository"] == repository
    assert license_hint in record["license_note"]
    assert record["rights"] == "unknown"
    assert "effect-sources.md" in record["details"]


def test_react_bits_cli_warns_against_redistributing_ported_components(capsys):
    from video_studio.effect_library.__main__ import main
    assert main(["--q", "react bits", "--limit", "1"]) == 0
    record = json.loads(capsys.readouterr().out)[0]["entry"]
    assert all(term in record["license_note"] for term in ("redistribute", "standalone", "bundled", "ported"))
    assert record["license_url"] == "https://github.com/DavidHDev/react-bits/blob/main/LICENSE.md"


def test_resource_root_prefers_bundle_and_rejects_partial_bundle(monkeypatch, tmp_path):
    from video_studio.effect_library import resources

    package = tmp_path / "video_studio"
    fake_module = package / "effect_library" / "resources.py"
    fake_module.parent.mkdir(parents=True)
    fake_module.touch()
    monkeypatch.setattr(resources, "__file__", str(fake_module))

    def add_index(root, relative):
        index = root / relative
        index.parent.mkdir(parents=True, exist_ok=True)
        index.write_text("{}", encoding="utf-8")

    bundle = package / "_bundled"
    add_index(bundle, resources._CATALOG)
    with pytest.raises(ContractError, match="missing or incomplete"):
        resources.resource_root()
    add_index(bundle, resources._MOTION)
    assert resources.resource_root() == bundle
    add_index(tmp_path, resources._CATALOG)
    assert resources.resource_root() == bundle  # Never mix two incomplete trees.
    add_index(tmp_path, resources._MOTION)
    assert resources.resource_root() == bundle  # A sibling catalog cannot override the installed bundle.
    (bundle / resources._MOTION).unlink()
    with pytest.raises(ContractError, match="missing or incomplete"):
        resources.resource_root()  # Never fall back to sibling resources when bundle is partial.


def test_resource_root_uses_checkout_without_bundle(monkeypatch, tmp_path):
    from video_studio.effect_library import resources

    fake_module = tmp_path / "video_studio" / "effect_library" / "resources.py"
    fake_module.parent.mkdir(parents=True)
    fake_module.touch()
    monkeypatch.setattr(resources, "__file__", str(fake_module))
    for relative in (resources._CATALOG, resources._MOTION):
        index = tmp_path / relative
        index.parent.mkdir(parents=True, exist_ok=True)
        index.write_text("{}", encoding="utf-8")
    assert resources.resource_root() == tmp_path


@pytest.mark.skipif(os.name != "nt", reason="Windows junction semantics")
def test_resource_root_rejects_bundle_junction(monkeypatch, tmp_path):
    import subprocess
    from video_studio.effect_library import resources

    fake_module = tmp_path / "video_studio" / "effect_library" / "resources.py"
    fake_module.parent.mkdir(parents=True)
    fake_module.touch()
    outside = tmp_path / "outside"
    outside.mkdir()
    link = fake_module.parents[1] / "_bundled"
    env = dict(os.environ, EFFECT_TEST_LINK=str(link), EFFECT_TEST_TARGET=str(outside))
    result = subprocess.run(["powershell", "-NoProfile", "-Command", "New-Item -ItemType Junction -Path $env:EFFECT_TEST_LINK -Target $env:EFFECT_TEST_TARGET | Out-Null"], env=env, capture_output=True, timeout=20)
    if result.returncode:
        pytest.skip("Windows junction setup unavailable")
    monkeypatch.setattr(resources, "__file__", str(fake_module))
    try:
        with pytest.raises(ContractError, match="unsafe"):
            resources.resource_root()
    finally:
        os.rmdir(link)


@pytest.mark.skipif(os.name != "nt", reason="Windows junction semantics")
def test_resource_root_does_not_resolve_junction_in_package_path(monkeypatch, tmp_path):
    import subprocess
    from video_studio.effect_library import resources

    outside = tmp_path / "outside"
    module = outside / "video_studio/effect_library/resources.py"
    module.parent.mkdir(parents=True)
    module.touch()
    for relative in (resources._CATALOG, resources._MOTION):
        index = outside / relative
        index.parent.mkdir(parents=True, exist_ok=True)
        index.write_text("{}", encoding="utf-8")
    link = tmp_path / "linked"
    env = dict(os.environ, EFFECT_TEST_LINK=str(link), EFFECT_TEST_TARGET=str(outside))
    result = subprocess.run(["powershell", "-NoProfile", "-Command", "New-Item -ItemType Junction -Path $env:EFFECT_TEST_LINK -Target $env:EFFECT_TEST_TARGET | Out-Null"], env=env, capture_output=True, timeout=20)
    if result.returncode:
        pytest.skip("Windows junction setup unavailable")
    monkeypatch.setattr(resources, "__file__", str(link / "video_studio/effect_library/resources.py"))
    try:
        with pytest.raises(ContractError, match="unsafe"):
            resources.resource_root()
    finally:
        os.rmdir(link)

@pytest.mark.parametrize("value", [None, "", "   ", "!!!", 123, []])
def test_runtime_filter_rejects_invalid_values(value):
    with pytest.raises(ContractError, match="runtime"):
        search(filters={"runtime": value})


def test_runtime_filter_matches_whole_folded_tokens_and_combines_filters(tmp_path):
    records = []
    for identifier, name, runtime in [("VE-a", "first", "Canvas Kết xuất GSAP"),
                                      ("VE-b", "GSAP", "Canvas notgsap"),
                                      ("VE-c", "third", "Canvas GSAP")]:
        record = entry()
        record.update(id=identifier, name=name, kind="reference", rights="unknown", asset=None,
                      source="https://example.org", runtime=runtime)
        records.append(record)
    records[2]["checks"]["render"] = "pass"
    records[2]["evidence"] = {"render": "synthetic test evidence"}
    catalog = tmp_path / "entries.json"
    catalog.write_text(json.dumps(records), encoding="utf-8")
    found = search(filters={"runtime": "ket xuat gsap", "check.render": "not_run"}, repo_entries=catalog)
    assert [row["id"] for row in found] == ["VE-a"]
    assert {row["id"] for row in search(filters={"runtime": "gsap"}, repo_entries=catalog)} == {"VE-a", "VE-c"}


def test_ratio_unknown_is_explicit_opt_in_and_preserves_metadata():
    from video_studio.effect_library.resources import resource_root
    catalog = resource_root() / "skills/video-theme-library/assets/effect-library/entries.json"
    strict = search("react bits", {"ratio": "16:9"}, repo_entries=catalog, limit=500)
    assert not any(row["id"] == "VE-react-bits" for row in strict)
    expanded = search("react bits", {"ratio": "16:9"}, repo_entries=catalog,
                      limit=500, include_unknown_ratio=True)
    record = next(row for row in expanded if row["id"] == "VE-react-bits")
    assert record["ratios"] == []
    assert record["checks"]["ratio_test"] == "not_run"
    with pytest.raises(ContractError):
        search(include_unknown_ratio=True)
    with pytest.raises(ContractError):
        search(filters={"ratio": "16:9"}, include_unknown_ratio="yes")


def test_ratio_opt_in_excludes_known_mismatches(tmp_path):
    records = []
    for identifier, ratios in [("VE-unknown", []), ("VE-match", ["16:9"]), ("VE-other", ["9:16"])]:
        record = entry()
        record.update(id=identifier, kind="reference", maturity="reference_only", rights="unknown", asset=None,
                      source="https://example.org", ratios=ratios)
        records.append(record)
    catalog = tmp_path / "entries.json"
    catalog.write_text(json.dumps(records), encoding="utf-8")
    found = search(filters={"ratio": "16:9"}, repo_entries=catalog, include_unknown_ratio=True)
    assert {row["id"] for row in found} == {"VE-unknown", "VE-match"}


def test_cli_runtime_and_unknown_ratio(capsys):
    from video_studio.effect_library.__main__ import main
    assert main(["--q", "react bits", "--runtime", "gsap", "--ratio", "16:9", "--include-unknown-ratio"]) == 0
    rows = json.loads(capsys.readouterr().out)
    assert next(row["entry"] for row in rows if row["entry"]["id"] == "VE-react-bits")["ratios"] == []
    assert main(["--runtime", "!!!"]) == 2
    assert "runtime" in capsys.readouterr().err
    assert main(["--include-unknown-ratio"]) == 2


def test_prompt_motion_ratio_unknown_does_not_include_known_redesign(tmp_path):
    index = tmp_path / "pm.json"
    source = {"entries": [
        {"id": "PM-redesign", "name": "Redesign", "sol_analysis": {"ratio_fit": {
            "16:9": {"fit": "requires_redesign"}, "9:16": {"fit": "requires_redesign"}}}},
        {"id": "PM-unknown", "name": "Unknown"},
        {"id": "PM-match", "name": "Match", "sol_analysis": {"ratio_fit": {
            "16:9": {"fit": "preferred"}}}},
    ]}
    index.write_text(json.dumps(source), encoding="utf-8")
    rows = search(filters={"ratio": "16:9"}, pm_index=index, include_unknown_ratio=True)
    assert {row["id"] for row in rows} == {"PM-unknown", "PM-match"}
    all_rows = search(pm_index=index)
    redesign = next(row for row in all_rows if row["id"] == "PM-redesign")
    assert redesign["ratios"] == []
    assert redesign["ratio_fit"]["16:9"]["fit"] == "requires_redesign"
    portrait = search(filters={"ratio": "9:16"}, pm_index=index, include_unknown_ratio=True)
    assert {row["id"] for row in portrait} == {"PM-unknown", "PM-match"}
    assert next(row for row in portrait if row["id"] == "PM-match")["ratios"] == ["16:9"]


@pytest.mark.parametrize("value", [None, "", "   ", 123, True, []])
def test_ratio_filter_rejects_invalid_values(value):
    with pytest.raises(ContractError):
        search(filters={"ratio": value}, include_unknown_ratio=True)


def test_runtime_filter_preserves_dotted_version_tokens(tmp_path):
    record = entry()
    record.update(kind="reference", maturity="reference_only", rights="unknown", asset=None, source="https://example.org",
                  runtime="HyperFrames 0.8.54 Kết xuất")
    catalog = tmp_path / "entries.json"
    catalog.write_text(json.dumps([record]), encoding="utf-8")
    assert search(filters={"runtime": "hyperframes 0.8.54 ket xuat"}, repo_entries=catalog)
    assert not search(filters={"runtime": "hyperframes 0.54.8"}, repo_entries=catalog)
    assert not search(filters={"runtime": "hyperframes 0.8"}, repo_entries=catalog)

@pytest.mark.skipif(os.name != "nt", reason="capture requires Windows")
@pytest.mark.parametrize("identifier", ["VE-ref-ffmpeg-speedramp", "VE-ref-hypit-t1"])
def test_capture_rejects_distilled_reference_id_before_publish(tmp_path, identifier):
    project = tmp_path / "project"
    project.mkdir()
    station = tmp_path / "station"
    entries = station / "effect-library" / "entries"
    entries.mkdir(parents=True)
    record = entry()
    record.update(id=identifier, kind="reference", maturity="reference_only", rights="unknown", asset=None,
                  source="https://example.org/a-distinct-synthetic-reference")
    with pytest.raises(ValueError, match="[Ii][Dd].*distilled"):
        capture(project, station, record)
    assert list(entries.iterdir()) == []


@pytest.mark.skipif(os.name != "nt", reason="capture requires Windows")
def test_capture_fails_closed_when_distilled_catalog_unreadable(tmp_path, monkeypatch):
    from video_studio.effect_library import distilled_sources
    project = tmp_path / "project"
    project.mkdir()
    station = tmp_path / "station"
    entries = station / "effect-library" / "entries"
    entries.mkdir(parents=True)
    record = entry()
    record.update(kind="reference", maturity="reference_only", rights="unknown", asset=None,
                  source="https://example.org/a-distinct-synthetic-reference")
    def broken(_root):
        raise ContractError("Cannot safely read distilled references")
    monkeypatch.setattr(distilled_sources, "load_distilled", broken)
    with pytest.raises(ContractError, match="Cannot safely read"):
        capture(project, station, record)
    assert list(entries.iterdir()) == []
