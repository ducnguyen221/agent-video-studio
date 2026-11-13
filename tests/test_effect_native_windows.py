import os

import pytest

pytestmark = pytest.mark.skipif(os.name != "nt", reason="Windows native experiment")


def test_public_bundle_capture_search_and_verified_read(tmp_path):
    import hashlib
    from video_studio.effect_library import capture, materialize, read_bundle, search

    source, station = tmp_path / "source", tmp_path / "station"
    source.mkdir(); (station / "effect-library" / "entries").mkdir(parents=True)
    files = {"index.html": b"<div>synthetic</div>", "scripts/effect.js": b"export const glow = 1;"}
    for path, data in files.items():
        dest = source / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
    checks = dict.fromkeys(("static_check", "preview", "render", "audio", "ratio_test", "reuse_evidence"), "not_run")
    manifest = {"id": "VE-multi-example", "name": "Multifile example", "kind": "component",
                "maturity": "candidate", "rights": "owned", "source": "synthetic", "runtime": "browser",
                "tags": ["multifile"], "roles": [], "techniques": [], "ratios": ["16:9"], "checks": checks,
                "assets": [{"path": path, "sha256": hashlib.sha256(data).hexdigest(), "rights": "owned"}
                           for path, data in files.items()]}
    assert capture(source, station, manifest) == manifest["id"]
    assert search("multifile", station=station)[0]["id"] == manifest["id"]
    assert read_bundle(station, manifest["id"]) == files
    with pytest.raises(ValueError, match="multi-file"):
        materialize(station, manifest["id"], source, "output")
    assert not (source / "output").exists()


def test_bundle_validation_rejects_unsafe_paths_and_unlicensed_files():
    import hashlib
    from video_studio.contract import ContractError
    from video_studio.effect_library import validate_entry

    digest = hashlib.sha256(b"synthetic").hexdigest()
    checks = dict.fromkeys(("static_check", "preview", "render", "audio", "ratio_test", "reuse_evidence"), "not_run")
    base = {"id": "VE-multi-paths", "name": "Multi paths", "kind": "component", "maturity": "candidate",
            "rights": "owned", "source": "synthetic", "runtime": "browser", "tags": [], "roles": [],
            "techniques": [], "ratios": [], "checks": checks}
    good = {"path": "Dir/effect.js", "sha256": digest, "rights": "owned"}
    for bad in ("../outside", "dir/EFFECT.js", "DIR", "Dir/effect.js/sub", "CON.txt", "bad?.js", "a//b.js", "other.js/",
                "a/b/c/d/e/f/g/h/i.js", "caf\u00e9.js"):
        other = {"path": bad, "sha256": digest, "rights": "owned"}
        first = {"path": "cafe\u0301.js", "sha256": digest, "rights": "owned"} if bad == "caf\u00e9.js" else good
        with pytest.raises(ContractError):
            validate_entry(dict(base, assets=[first, other]))
    for rights in ("unknown", "licensed"):
        with pytest.raises(ContractError):
            validate_entry(dict(base, assets=[good, {"path": "index.html", "sha256": digest, "rights": rights}]))


def test_repo_bundle_search_verifies_each_file(tmp_path, monkeypatch):
    import hashlib
    import json
    from video_studio.contract import ContractError
    from video_studio.effect_library import search
    import importlib

    search_module = importlib.import_module("video_studio.effect_library.search")
    monkeypatch.setattr(search_module, "resource_root", lambda: tmp_path)

    checks = dict.fromkeys(("static_check", "preview", "render", "audio", "ratio_test", "reuse_evidence"), "not_run")
    manifest = {"id": "VE-repo-multi", "name": "Repo multi", "kind": "component", "maturity": "candidate",
                "rights": "owned", "source": "synthetic", "runtime": "browser", "tags": [], "roles": [],
                "techniques": [], "ratios": [], "checks": checks,
                "assets": [{"path": name, "sha256": hashlib.sha256(content).hexdigest(), "rights": "owned"}
                           for name, content in (("nested/effect.js", b"synthetic"), ("other.css", b"css"))]}
    catalog = tmp_path / "entries.json"
    catalog.write_text(json.dumps([manifest]), encoding="utf-8")
    (tmp_path / "nested").mkdir()
    (tmp_path / "nested/effect.js").write_bytes(b"synthetic")
    (tmp_path / "other.css").write_bytes(b"css")
    assert search("repo multi", repo_entries=catalog)[0]["id"] == "VE-repo-multi"
    (tmp_path / "other.css").write_bytes(b"tampered")
    with pytest.raises(ContractError, match="hash"):
        search(repo_entries=catalog)
    (tmp_path / "other.css").unlink()
    with pytest.raises(ContractError, match="repo bundle"):
        search(repo_entries=catalog)


def test_repo_bundle_holds_all_file_handles_during_verification(tmp_path, monkeypatch):
    import hashlib
    import importlib
    import json
    from video_studio.effect_library import _native_windows as native, search

    a, b = tmp_path / "a.js", tmp_path / "b.css"
    a.write_bytes(b"asset-a"); b.write_bytes(b"asset-b")
    checks = dict.fromkeys(("static_check", "preview", "render", "audio", "ratio_test", "reuse_evidence"), "not_run")
    record = {"id": "VE-held", "name": "Held", "kind": "component", "maturity": "candidate",
              "rights": "owned", "source": "synthetic", "runtime": "browser", "tags": [], "roles": [],
              "techniques": [], "ratios": [], "checks": checks,
              "assets": [{"path": f.name, "sha256": hashlib.sha256(f.read_bytes()).hexdigest(), "rights": "owned"} for f in (a, b)]}
    catalog = tmp_path / "entries.json"
    catalog.write_text(json.dumps([record]), encoding="utf-8")
    monkeypatch.setattr(importlib.import_module("video_studio.effect_library.search"), "resource_root", lambda: tmp_path)
    original = native.read_all
    attempted = []

    def observe(handle, limit=64 * 1024 * 1024):
        payload = original(handle, limit)
        if payload == b"asset-a":
            with pytest.raises(PermissionError):
                b.write_bytes(b"changed during verification")
            attempted.append(True)
        return payload

    monkeypatch.setattr(native, "read_all", observe)
    assert search(repo_entries=catalog)[0]["id"] == "VE-held"
    assert attempted == [True] and b.read_bytes() == b"asset-b"


def test_repo_catalog_close_failure_closes_other_handles(tmp_path, monkeypatch):
    import importlib
    import json
    from video_studio.contract import ContractError
    from video_studio.effect_library import _native_windows as native, search

    catalog = tmp_path / "entries.json"
    catalog.write_text(json.dumps([]), encoding="utf-8")
    original_close = native.close
    calls = []

    def failing_close(handle):
        original_close(handle)
        calls.append(handle)
        if len(calls) == 1:
            raise OSError("injected close error")

    monkeypatch.setattr(native, "close", failing_close)
    monkeypatch.setattr(importlib.import_module("video_studio.effect_library.search"), "resource_root", lambda: tmp_path)
    with pytest.raises(ContractError, match="close repo verification"):
        search(repo_entries=catalog)
    assert len(calls) == 2


def test_capture_verifies_repo_bundle_and_rejects_duplicate_identity(tmp_path, monkeypatch):
    import hashlib
    import json
    from video_studio.effect_library import capture, resources
    from video_studio.effect_library import distilled_sources

    # This fixture focuses on the repo bundle and has no distilled documents.
    monkeypatch.setattr(distilled_sources, "load_distilled", lambda _root: [])

    repo, project, station = tmp_path / "repo", tmp_path / "project", tmp_path / "station"
    project.mkdir()
    (station / "effect-library" / "entries").mkdir(parents=True)
    index = repo / "skills/video-theme-library/assets/effect-library/entries.json"
    index.parent.mkdir(parents=True)
    checks = dict.fromkeys(("static_check", "preview", "render", "audio", "ratio_test", "reuse_evidence"), "not_run")
    files = {"a.js": b"synthetic A", "b.css": b"synthetic B"}
    assets = []
    for name, payload in files.items():
        (repo / name).write_bytes(payload)
        (project / name).write_bytes(payload)
        assets.append({"path": name, "sha256": hashlib.sha256(payload).hexdigest(), "rights": "owned"})
    base = {"id": "VE-repo", "name": "Repo bundle", "kind": "component", "maturity": "candidate",
            "rights": "owned", "source": "synthetic", "runtime": "browser", "tags": [], "roles": [],
            "techniques": [], "ratios": [], "checks": checks}
    index.write_text(json.dumps([dict(base, assets=assets)]), encoding="utf-8")
    monkeypatch.setattr(resources, "resource_root", lambda: repo)
    duplicate = dict(base, id="VE-copy", name="Different name", assets=list(reversed(assets)))
    with pytest.raises(ValueError, match="bundle already exists in repo"):
        capture(project, station, duplicate)
    distinct = dict(base, id="VE-distinct", name="Distinct", asset=assets[0])
    assert capture(project, station, distinct) == "VE-distinct"
    (repo / "b.css").write_bytes(b"tampered")
    with pytest.raises(ValueError, match="hash"):
        capture(project, station, dict(distinct, id="VE-another", name="Another"))
    assert sorted(p.name for p in (station / "effect-library" / "entries").iterdir()) == ["VE-distinct"]


def test_repo_bundle_search_rejects_junction(tmp_path, monkeypatch):
    import hashlib
    import importlib
    import json
    import subprocess
    from video_studio.contract import ContractError
    from video_studio.effect_library import search

    repo, outside = tmp_path / "repo", tmp_path / "outside"
    repo.mkdir(); outside.mkdir()
    (outside / "file.js").write_bytes(b"outside")
    (repo / "b.css").write_bytes(b"css")
    link = repo / "linked"
    env = dict(os.environ, EFFECT_TEST_LINK=str(link), EFFECT_TEST_TARGET=str(outside))
    result = subprocess.run(["powershell", "-NoProfile", "-Command", "New-Item -ItemType Junction -Path $env:EFFECT_TEST_LINK -Target $env:EFFECT_TEST_TARGET | Out-Null"], env=env, capture_output=True, timeout=20)
    if result.returncode:
        pytest.skip("Windows junction setup unavailable")
    checks = dict.fromkeys(("static_check", "preview", "render", "audio", "ratio_test", "reuse_evidence"), "not_run")
    record = {"id": "VE-linked", "name": "Linked", "kind": "component", "maturity": "candidate",
              "rights": "owned", "source": "synthetic", "runtime": "browser", "tags": [], "roles": [],
              "techniques": [], "ratios": [], "checks": checks,
              "assets": [{"path": "linked/file.js", "sha256": hashlib.sha256(b"outside").hexdigest(), "rights": "owned"},
                         {"path": "b.css", "sha256": hashlib.sha256(b"css").hexdigest(), "rights": "owned"}]}
    catalog = tmp_path / "entries.json"
    catalog.write_text(json.dumps([record]), encoding="utf-8")
    monkeypatch.setattr(importlib.import_module("video_studio.effect_library.search"), "resource_root", lambda: repo)
    try:
        with pytest.raises(ContractError, match="repo bundle"):
            search(repo_entries=catalog)
    finally:
        os.rmdir(link)


def _is_junction(path):
    """`Path.is_junction` exists only from Python 3.12."""
    check = getattr(os.path, "isjunction", None)
    if check is not None:
        return check(path)
    import stat
    try:
        return bool(os.lstat(path).st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT) and not os.path.islink(path)
    except (OSError, AttributeError):
        return False



def test_single_repo_asset_does_not_follow_junction_after_check(tmp_path, monkeypatch):
    import hashlib
    import importlib
    import json
    import subprocess
    from video_studio.contract import ContractError
    from video_studio.effect_library import search

    repo, outside = tmp_path / "repo", tmp_path / "outside"
    (repo / "inside").mkdir(parents=True); outside.mkdir()
    (repo / "inside/effect.js").write_bytes(b"inside")
    (outside / "effect.js").write_bytes(b"outside")
    checks = dict.fromkeys(("static_check", "preview", "render", "audio", "ratio_test", "reuse_evidence"), "not_run")
    record = {"id": "VE-single-race", "name": "Single race", "kind": "component", "maturity": "candidate",
              "rights": "owned", "source": "synthetic", "runtime": "browser", "tags": [], "roles": [],
              "techniques": [], "ratios": [], "checks": checks,
              "asset": {"path": "inside/effect.js", "sha256": hashlib.sha256(b"outside").hexdigest()}}
    catalog = tmp_path / "entries.json"
    catalog.write_text(json.dumps([record]), encoding="utf-8")
    module = importlib.import_module("video_studio.effect_library.search")
    monkeypatch.setattr(module, "resource_root", lambda: repo)
    original = module._safe_file
    link = repo / "inside"

    def swap_after_check(root, relative):
        path = original(root, relative)
        link.rename(repo / "saved")
        env = dict(os.environ, EFFECT_TEST_LINK=str(link), EFFECT_TEST_TARGET=str(outside))
        result = subprocess.run(["powershell", "-NoProfile", "-Command", "New-Item -ItemType Junction -Path $env:EFFECT_TEST_LINK -Target $env:EFFECT_TEST_TARGET | Out-Null"], env=env, capture_output=True, timeout=20)
        if result.returncode:
            pytest.skip("Windows junction setup unavailable")
        return path

    monkeypatch.setattr(module, "_safe_file", swap_after_check)
    try:
        with pytest.raises(ContractError, match="hash|repo"):
            search(repo_entries=catalog)
    finally:
        if _is_junction(link):
            os.rmdir(link)


def test_prompt_motion_index_rejects_junction(tmp_path):
    import json
    import subprocess
    from video_studio.contract import ContractError
    from video_studio.effect_library import search

    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "index.json").write_text(json.dumps({"entries": []}), encoding="utf-8")
    link = tmp_path / "linked"
    env = dict(os.environ, EFFECT_TEST_LINK=str(link), EFFECT_TEST_TARGET=str(outside))
    result = subprocess.run(["powershell", "-NoProfile", "-Command", "New-Item -ItemType Junction -Path $env:EFFECT_TEST_LINK -Target $env:EFFECT_TEST_TARGET | Out-Null"], env=env, capture_output=True, timeout=20)
    if result.returncode:
        pytest.skip("Windows junction setup unavailable")
    try:
        with pytest.raises(ContractError, match="catalog"):
            search(pm_index=link / "index.json")
    finally:
        os.rmdir(link)


def test_bundle_read_rejects_tampered_payload_and_rights(tmp_path):
    import base64
    import hashlib
    import json
    from video_studio.contract import ContractError
    from video_studio.effect_library import capture, read_bundle

    project, station = tmp_path / "source", tmp_path / "station"
    project.mkdir(); (station / "effect-library" / "entries").mkdir(parents=True)
    for name in ("a.js", "b.css"):
        (project / name).write_bytes(name.encode())
    checks = dict.fromkeys(("static_check", "preview", "render", "audio", "ratio_test", "reuse_evidence"), "not_run")
    manifest = {"id": "VE-bundle-tamper", "name": "Bundle tamper", "kind": "component", "maturity": "candidate",
                "rights": "owned", "source": "synthetic", "runtime": "browser", "tags": [], "roles": [],
                "techniques": [], "ratios": [], "checks": checks,
                "assets": [{"path": n, "sha256": hashlib.sha256(n.encode()).hexdigest(), "rights": "owned"} for n in ("a.js", "b.css")]}
    capture(project, station, manifest)
    path = station / "effect-library" / "entries" / manifest["id"] / "entry.json"
    original = json.loads(path.read_text(encoding="utf-8"))
    changed = json.loads(json.dumps(original)); changed["assets_base64"]["a.js"] = base64.b64encode(b"malicious").decode()
    path.write_text(json.dumps(changed), encoding="utf-8")
    with pytest.raises(ValueError, match="hash"):
        read_bundle(station, manifest["id"])
    changed = json.loads(json.dumps(original)); changed["entry"]["assets"][0]["rights"] = "unknown"
    path.write_text(json.dumps(changed), encoding="utf-8")
    with pytest.raises(ContractError, match="rights"):
        read_bundle(station, manifest["id"])
    from video_studio.effect_library import search
    for value in (3, ["data"], "%%%", "cà"):
        changed = json.loads(json.dumps(original)); changed["assets_base64"]["a.js"] = value
        path.write_text(json.dumps(changed), encoding="utf-8")
        with pytest.raises(ContractError, match="bundle"):
            search(station=station)


def test_legacy_v1_invalid_base64_is_reported_as_catalog_error(tmp_path):
    import hashlib
    import json
    from video_studio.contract import ContractError
    from video_studio.effect_library import capture, search

    project, station = tmp_path / "project", tmp_path / "station"
    project.mkdir(); (station / "effect-library" / "entries").mkdir(parents=True)
    (project / "effect.js").write_bytes(b"synthetic")
    checks = dict.fromkeys(("static_check", "preview", "render", "audio", "ratio_test", "reuse_evidence"), "not_run")
    manifest = {"id": "VE-v1-invalid", "name": "V1 invalid", "kind": "component", "maturity": "candidate",
                "rights": "owned", "source": "synthetic", "runtime": "js", "tags": [], "roles": [],
                "techniques": [], "ratios": [], "checks": checks,
                "asset": {"path": "effect.js", "sha256": hashlib.sha256(b"synthetic").hexdigest()}}
    capture(project, station, manifest)
    assert search("v1 invalid", station=station)[0]["id"] == manifest["id"]
    record_path = station / "effect-library" / "entries" / manifest["id"] / "entry.json"
    original = json.loads(record_path.read_text(encoding="utf-8"))
    for invalid in (3, ["data"], "%%%", "cà"):
        changed = dict(original, asset_base64=invalid)
        record_path.write_text(json.dumps(changed), encoding="utf-8")
        with pytest.raises(ContractError, match="encoding"):
            search(station=station)


def test_bundle_deduplicates_complete_bundle_but_allows_shared_dependency(tmp_path):
    import hashlib
    from video_studio.effect_library import capture

    project, station = tmp_path / "source", tmp_path / "station"
    project.mkdir(); (station / "effect-library" / "entries").mkdir(parents=True)
    files = {"shared.js": b"shared", "one.html": b"first", "two.html": b"second"}
    for name, content in files.items():
        (project / name).write_bytes(content)
    checks = dict.fromkeys(("static_check", "preview", "render", "audio", "ratio_test", "reuse_evidence"), "not_run")
    common = {"kind": "component", "maturity": "candidate", "rights": "owned", "source": "synthetic",
              "runtime": "browser", "tags": [], "roles": [], "techniques": [], "ratios": [], "checks": checks}
    def asset(name):
        return {"path": name, "sha256": hashlib.sha256(files[name]).hexdigest(), "rights": "owned"}
    capture(project, station, dict(common, id="VE-bundle-one", name="One bundle", assets=[asset("shared.js"), asset("one.html")]))
    capture(project, station, dict(common, id="VE-bundle-two", name="Two bundle", assets=[asset("shared.js"), asset("two.html")]))
    with pytest.raises(ValueError, match="bundle already exists"):
        capture(project, station, dict(common, id="VE-bundle-copy", name="Copy bundle", assets=[asset("one.html"), asset("shared.js")]))
    assert {p.name for p in (station / "effect-library" / "entries").iterdir()} == {"VE-bundle-one", "VE-bundle-two"}


def test_bundle_source_files_are_locked_before_first_read(tmp_path, monkeypatch):
    import hashlib
    from video_studio.effect_library import capture
    from video_studio.effect_library import _native_windows as native

    project, station = tmp_path / "source", tmp_path / "station"
    project.mkdir(); (station / "effect-library" / "entries").mkdir(parents=True)
    for name in ("a.js", "b.js"):
        (project / name).write_bytes(name.encode())
    checks = dict.fromkeys(("static_check", "preview", "render", "audio", "ratio_test", "reuse_evidence"), "not_run")
    manifest = {"id": "VE-bundle-lock", "name": "Bundle lock", "kind": "component", "maturity": "candidate",
                "rights": "owned", "source": "synthetic", "runtime": "browser", "tags": [], "roles": [],
                "techniques": [], "ratios": [], "checks": checks,
                "assets": [{"path": n, "sha256": hashlib.sha256(n.encode()).hexdigest(), "rights": "owned"} for n in ("a.js", "b.js")]}
    original = native.read_all
    attempts = []
    def checked_read(handle, *args, **kwargs):
        if not attempts:
            with pytest.raises(OSError):
                (project / "b.js").write_bytes(b"changed")
            attempts.append(True)
        return original(handle, *args, **kwargs)
    monkeypatch.setattr(native, "read_all", checked_read)
    capture(project, station, manifest)
    assert attempts == [True]
    assert (project / "b.js").read_bytes() == b"b.js"


def test_bundle_total_size_limit_is_checked_before_publish_and_on_read(tmp_path, monkeypatch):
    import hashlib
    from video_studio.effect_library import _native_windows as native
    from video_studio.effect_library import capture, read_bundle

    project, station = tmp_path / "source", tmp_path / "station"
    project.mkdir(); entries = station / "effect-library" / "entries"; entries.mkdir(parents=True)
    for name in ("a.js", "b.js"):
        (project / name).write_bytes(b"1234")
    checks = dict.fromkeys(("static_check", "preview", "render", "audio", "ratio_test", "reuse_evidence"), "not_run")
    manifest = {"id": "VE-bundle-size", "name": "Bundle size", "kind": "component", "maturity": "candidate",
                "rights": "owned", "source": "synthetic", "runtime": "browser", "tags": [], "roles": [],
                "techniques": [], "ratios": [], "checks": checks,
                "assets": [{"path": n, "sha256": hashlib.sha256(b"1234").hexdigest(), "rights": "owned"} for n in ("a.js", "b.js")]}
    monkeypatch.setattr(native, "MAX_BUNDLE_BYTES", 7)
    with pytest.raises(ValueError, match="size limit"):
        capture(project, station, manifest)
    assert list(entries.iterdir()) == []
    monkeypatch.setattr(native, "MAX_BUNDLE_BYTES", 8)
    capture(project, station, manifest)
    assert read_bundle(station, manifest["id"]) == {"a.js": b"1234", "b.js": b"1234"}
    monkeypatch.setattr(native, "MAX_BUNDLE_BYTES", 7)
    with pytest.raises(ValueError, match="size"):
        read_bundle(station, manifest["id"])


def test_bundle_write_failure_rolls_back_without_publish(tmp_path, monkeypatch):
    import hashlib
    from video_studio.effect_library import _native_windows as native

    project, entries = tmp_path / "project", tmp_path / "entries"
    project.mkdir(); entries.mkdir()
    names = ("a.js", "b.css")
    for name in names:
        (project / name).write_bytes(name.encode())
    checks = dict.fromkeys(("static_check", "preview", "render", "audio", "ratio_test", "reuse_evidence"), "not_run")
    manifest = {"id": "VE-bundle-rollback", "name": "Bundle rollback", "kind": "component", "maturity": "candidate",
                "rights": "owned", "source": "synthetic", "runtime": "browser", "tags": [], "roles": [],
                "techniques": [], "ratios": [], "checks": checks,
                "assets": [{"path": n, "sha256": hashlib.sha256(n.encode()).hexdigest(), "rights": "owned"} for n in names]}
    original = native.write_all
    def fail_payload(handle, payload):
        if b'"format":"ve-bundle-v2"' in payload:
            original(handle, payload[:20])
            raise OSError("synthetic interrupted write")
        return original(handle, payload)
    monkeypatch.setattr(native, "write_all", fail_payload)
    with pytest.raises(OSError, match="interrupted write"):
        native.capture_experiment(project, entries, manifest)
    assert list(entries.iterdir()) == []


@pytest.mark.parametrize("phase", ["after_write", "after_publish"])
def test_bundle_crash_keeps_stage_quarantined_or_complete(tmp_path, phase):
    import subprocess
    import sys

    project, entries = tmp_path / "project", tmp_path / "entries"
    project.mkdir(); entries.mkdir()
    for name in ("a.js", "b.css"):
        (project / name).write_bytes(name.encode())
    code = r'''
import hashlib, os, sys
from video_studio.effect_library import _native_windows as n
c=dict.fromkeys(("static_check","preview","render","audio","ratio_test","reuse_evidence"),"not_run")
m={"id":"VE-bundle-crash","name":"Crash","kind":"component","maturity":"candidate","rights":"owned","source":"synthetic","runtime":"browser","tags":[],"roles":[],"techniques":[],"ratios":[],"checks":c,"assets":[{"path":x,"sha256":hashlib.sha256(x.encode()).hexdigest(),"rights":"owned"} for x in ("a.js","b.css")]}
method="write_all" if sys.argv[3]=="after_write" else "rename_no_replace"
original=getattr(n,method)
def crash(*args):
 original(*args)
 if method=="rename_no_replace" or b'"format":"ve-bundle-v2"' in args[1]: os._exit(42)
setattr(n,method,crash)
n.capture_experiment(sys.argv[1],sys.argv[2],m)
'''
    result = subprocess.run([sys.executable, "-c", code, str(project), str(entries), phase], timeout=30)
    assert result.returncode == 42
    names = [p.name for p in entries.iterdir()]
    if phase == "after_write":
        assert len(names) == 1 and names[0].startswith("stage-")
        assert not (entries / "VE-bundle-crash").exists()
    else:
        from video_studio.effect_library import _native_windows as native
        assert names == ["VE-bundle-crash"]
        assert native.load_experiment(entries, "VE-bundle-crash")[1] == {"a.js": b"a.js", "b.css": b"b.css"}


def test_handle_publish_collision_and_rollback(tmp_path):
    from video_studio.effect_library import _native_windows as n
    root = n.open_root(tmp_path)
    try:
        first = n.create_file(root, "taken")
        n.close(first)
        staged = n.create_file(root, "stage")
        try:
            with pytest.raises(OSError, match="c0000035"):
                n.rename_no_replace(staged, root, "taken")
            n.rename_no_replace(staged, root, "published")
        finally:
            n.close(staged)
        rollback = n.create_file(root, "rollback")
        n.delete_on_close(rollback)
        n.close(rollback)
    finally:
        n.close(root)
    assert (tmp_path / "taken").exists()
    assert (tmp_path / "published").exists()
    assert not (tmp_path / "stage").exists()
    assert not (tmp_path / "rollback").exists()


def test_reject_traversal(tmp_path):
    from video_studio.effect_library import _native_windows as n
    root = n.open_root(tmp_path)
    try:
        for name in ("..", "../outside", "x\\y", "C:foo", "CON.txt", "LPT1", "bad.", "bad?x"):
            with pytest.raises(ValueError):
                n.create_file(root, name)
    finally:
        n.close(root)


def test_junction_is_rejected(tmp_path):
    import subprocess
    from video_studio.effect_library import _native_windows as n
    outside = tmp_path / "outside"
    station = tmp_path / "station"
    outside.mkdir(); station.mkdir()
    link = station / "link"
    env = dict(os.environ, EFFECT_TEST_LINK=str(link), EFFECT_TEST_TARGET=str(outside))
    created = subprocess.run(["powershell", "-NoProfile", "-Command",
                              "New-Item -ItemType Junction -Path $env:EFFECT_TEST_LINK -Target $env:EFFECT_TEST_TARGET | Out-Null"],
                             env=env, capture_output=True, timeout=20)
    if created.returncode:
        pytest.skip("Windows junction setup unavailable")
    root = n.open_root(station)
    try:
        with pytest.raises(OSError, match="c000050b"):
            n.open_directory(root, "link")
    finally:
        n.close(root)
        os.rmdir(link)
    assert not list(outside.iterdir())


def test_open_station_handle_blocks_rename(tmp_path):
    from video_studio.effect_library import _native_windows as n
    station = tmp_path / "station"
    station.mkdir()
    root = n.open_root(station)
    try:
        with pytest.raises(OSError):
            station.rename(tmp_path / "moved")
        handle = n.create_file(root, "inside")
        n.close(handle)
    finally:
        n.close(root)
    assert (station / "inside").exists()


def test_handle_read_write_and_seek_independent(tmp_path):
    from video_studio.effect_library import _native_windows as n
    root = n.open_root(tmp_path)
    try:
        handle = n.create_file(root, "asset")
        n.write_all(handle, b"synthetic effect")
        n.close(handle)
        handle = n.open_file(root, "asset")
        assert n.read_all(handle) == b"synthetic effect"
        n.close(handle)
    finally:
        n.close(root)


def test_capture_experiment_synthetic_and_collision(tmp_path):
    import hashlib
    from video_studio.effect_library import _native_windows as n
    project = tmp_path / "project"; project.mkdir()
    station_root = tmp_path / "station"
    station = station_root / "effect-library" / "entries"; station.mkdir(parents=True)
    (project / "effect.js").write_bytes(b"synthetic reusable effect")
    keys = ("static_check", "preview", "render", "audio", "ratio_test", "reuse_evidence")
    manifest = {"id": "VE-synthetic", "name": "Synthetic", "kind": "component", "maturity": "candidate",
                "rights": "owned", "source": "created synthetic", "runtime": "js", "tags": [],
                "roles": [], "techniques": [], "ratios": [], "checks": dict.fromkeys(keys, "not_run"),
                "asset": {"path": "effect.js", "sha256": hashlib.sha256(b"synthetic reusable effect").hexdigest()}}
    assert n.capture_experiment(project, station, manifest) == "VE-synthetic"
    entry, content = n.load_experiment(station, "VE-synthetic")
    assert entry["id"] == "VE-synthetic" and content == b"synthetic reusable effect"
    from video_studio.effect_library import search
    assert search("synthetic", station=station_root)[0]["id"] == "VE-synthetic"
    second = tmp_path / "second-project"; second.mkdir()
    n.materialize_experiment(station, "VE-synthetic", second, "effect.js")
    assert (second / "effect.js").read_bytes() == b"synthetic reusable effect"
    with pytest.raises(OSError, match="c0000035"):
        n.materialize_experiment(station, "VE-synthetic", second, "effect.js")
    assert sorted(p.name for p in second.iterdir()) == ["effect.js"]
    with pytest.raises(ValueError, match="already exists"):
        n.capture_experiment(project, station, manifest)
    assert sorted(p.name for p in station.iterdir()) == ["VE-synthetic"]


def test_capture_experiment_failure_rolls_back(tmp_path, monkeypatch):
    import hashlib
    from video_studio.effect_library import _native_windows as n
    project = tmp_path / "project"; project.mkdir()
    station = tmp_path / "entries"; station.mkdir()
    (project / "effect.js").write_bytes(b"data")
    keys = ("static_check", "preview", "render", "audio", "ratio_test", "reuse_evidence")
    manifest = {"id": "VE-rollback", "name": "Synthetic", "kind": "component", "maturity": "candidate",
                "rights": "owned", "source": "created synthetic", "runtime": "js", "tags": [],
                "roles": [], "techniques": [], "ratios": [], "checks": dict.fromkeys(keys, "not_run"),
                "asset": {"path": "effect.js", "sha256": hashlib.sha256(b"data").hexdigest()}}
    def fail_write(handle, payload):
        raise OSError("simulated write failure")
    monkeypatch.setattr(n, "write_all", fail_write)
    with pytest.raises(OSError, match="simulated"):
        n.capture_experiment(project, station, manifest)
    assert not list(station.iterdir())


def test_source_handle_blocks_modification_and_ancestor_move(tmp_path):
    from video_studio.effect_library import _native_windows as n
    parent = tmp_path / "parent"; parent.mkdir()
    project = parent / "project"; project.mkdir()
    (project / "asset.js").write_bytes(b"original")
    root = n.open_root(project)
    source = n.open_file(root, "asset.js")
    try:
        with pytest.raises(OSError):
            (project / "asset.js").write_bytes(b"modified")
        with pytest.raises(OSError):
            parent.rename(tmp_path / "moved")
        assert n.read_all(source) == b"original"
    finally:
        n.close(source); n.close(root)


def test_crash_leaves_only_quarantined_stage(tmp_path):
    import subprocess
    import sys
    project = tmp_path / "project"; project.mkdir()
    station = tmp_path / "entries"; station.mkdir()
    (project / "asset.js").write_bytes(b"data")
    code = r'''
import hashlib, os, sys
from video_studio.effect_library import _native_windows as n
checks = dict.fromkeys(("static_check", "preview", "render", "audio", "ratio_test", "reuse_evidence"), "not_run")
m = {"id":"VE-crash","name":"crash","kind":"component","maturity":"candidate","rights":"owned", "source":"synthetic","runtime":"js", "tags":[],"roles":[],"techniques":[],"ratios":[],"checks":checks,"asset":{"path":"asset.js","sha256":hashlib.sha256(b"data").hexdigest()}}
n.write_all = lambda handle, payload: os._exit(42)
n.capture_experiment(sys.argv[1],sys.argv[2],m)
'''
    result = subprocess.run([sys.executable, "-c", code, str(project), str(station)], timeout=30)
    assert result.returncode == 42
    names = [p.name for p in station.iterdir()]
    assert len(names) == 1 and names[0].startswith("stage-")
    assert not (station / "VE-crash").exists()


def test_capture_experiment_rejects_unknown_rights_and_hash(tmp_path):
    import hashlib
    from video_studio.effect_library import _native_windows as n
    project = tmp_path / "project"; project.mkdir()
    station = tmp_path / "station"; station.mkdir()
    (project / "effect.js").write_bytes(b"source")
    keys = ("static_check", "preview", "render", "audio", "ratio_test", "reuse_evidence")
    m = {"id": "VE-invalid", "name": "Synthetic", "kind": "component", "maturity": "candidate",
         "rights": "unknown", "source": "created synthetic", "runtime": "js", "tags": [], "roles": [],
         "techniques": [], "ratios": [], "checks": dict.fromkeys(keys, "not_run"),
         "asset": {"path": "effect.js", "sha256": hashlib.sha256(b"source").hexdigest()}}
    with pytest.raises(ValueError, match="owned or licensed"):
        n.capture_experiment(project, station, m)
    m["rights"] = "owned"; m["asset"]["sha256"] = "0" * 64
    with pytest.raises(ValueError, match="hash mismatch"):
        n.capture_experiment(project, station, m)
    assert not list(station.iterdir())


def test_root_junction_is_rejected(tmp_path):
    import subprocess
    from video_studio.effect_library import _native_windows as n
    outside = tmp_path / "outside"; outside.mkdir()
    link = tmp_path / "link"
    env = dict(os.environ, EFFECT_TEST_LINK=str(link), EFFECT_TEST_TARGET=str(outside))
    result = subprocess.run(["powershell", "-NoProfile", "-Command",
                             "New-Item -ItemType Junction -Path $env:EFFECT_TEST_LINK -Target $env:EFFECT_TEST_TARGET | Out-Null"],
                            env=env, capture_output=True, timeout=20)
    if result.returncode:
        pytest.skip("Windows junction setup unavailable")
    try:
        with pytest.raises(OSError, match="c000050b"):
            n.open_root(link)
    finally:
        os.rmdir(link)


@pytest.mark.parametrize("phase", ["after_write", "after_flush", "after_publish"])
def test_capture_crash_at_publication_boundaries(tmp_path, phase):
    import subprocess
    import sys
    project = tmp_path / "project"; project.mkdir()
    station = tmp_path / "entries"; station.mkdir()
    (project / "asset.js").write_bytes(b"data")
    code = r'''
import hashlib, os, sys
from video_studio.effect_library import _native_windows as n
checks = dict.fromkeys(("static_check", "preview", "render", "audio", "ratio_test", "reuse_evidence"), "not_run")
m = {"id":"VE-crash","name":"crash","kind":"component","maturity":"candidate","rights":"owned", "source":"synthetic","runtime":"js", "tags":[],"roles":[],"techniques":[],"ratios":[],"checks":checks,"asset":{"path":"asset.js","sha256":hashlib.sha256(b"data").hexdigest()}}
phase=sys.argv[3]
for method, target in [("write_all","after_write"),("flush","after_flush"),("rename_no_replace","after_publish")]:
 if phase == target:
  original=getattr(n,method)
  def crash(*a, _original=original):
   _original(*a); os._exit(42)
  setattr(n,method,crash)
n.capture_experiment(sys.argv[1],sys.argv[2],m)
'''
    result = subprocess.run([sys.executable, "-c", code, str(project), str(station), phase], timeout=30)
    assert result.returncode == 42
    names = [p.name for p in station.iterdir()]
    if phase == "after_publish":
        from video_studio.effect_library import _native_windows as n
        assert names == ["VE-crash"]
        assert n.load_experiment(station, "VE-crash")[1] == b"data"
    else:
        assert len(names) == 1 and names[0].startswith("stage-")
        assert not (station / "VE-crash").exists()


def test_materialize_rejects_unknown_rights(tmp_path):
    import hashlib
    import json
    from video_studio.effect_library import _native_windows as n
    source = tmp_path / "source"; source.mkdir()
    station = tmp_path / "entries"; station.mkdir()
    target = tmp_path / "target"; target.mkdir()
    (source / "effect.js").write_bytes(b"source")
    keys = ("static_check", "preview", "render", "audio", "ratio_test", "reuse_evidence")
    m = {"id": "VE-rights", "name": "Synthetic", "kind": "component", "maturity": "candidate",
         "rights": "owned", "source": "created synthetic", "runtime": "js", "tags": [], "roles": [],
         "techniques": [], "ratios": [], "checks": dict.fromkeys(keys, "not_run"),
         "asset": {"path": "effect.js", "sha256": hashlib.sha256(b"source").hexdigest()}}
    n.capture_experiment(source, station, m)
    path = station / "VE-rights" / "entry.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["entry"]["rights"] = "unknown"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="rights"):
        n.materialize_experiment(station, "VE-rights", target, "result.js")
    assert not list(target.iterdir())


def test_capture_rejects_repo_and_legacy_station_ids(tmp_path):
    import hashlib
    from video_studio.effect_library import _native_windows as n
    project = tmp_path / "project"; project.mkdir()
    station = tmp_path / "entries"; station.mkdir()
    (project / "effect.js").write_bytes(b"data")
    keys = ("static_check", "preview", "render", "audio", "ratio_test", "reuse_evidence")
    m = {"id": "VE-sun-rays", "name": "Synthetic", "kind": "component", "maturity": "candidate",
         "rights": "owned", "source": "synthetic", "runtime": "js", "tags": [], "roles": [],
         "techniques": [], "ratios": [], "checks": dict.fromkeys(keys, "not_run"),
         "asset": {"path": "effect.js", "sha256": hashlib.sha256(b"data").hexdigest()}}
    with pytest.raises(ValueError, match="repo catalog"):
        n.capture_experiment(project, station, m)
    m["id"] = "VE-legacy"
    (station / "VE-legacy").mkdir()
    with pytest.raises(ValueError, match="station"):
        n.capture_experiment(project, station, m)


def test_native_atomic_directory_promotion_collision(tmp_path):
    from video_studio.effect_library import _native_windows as n
    root = n.open_root(tmp_path)
    try:
        existing = n.create_directory(root, "VE-existing")
        n.close(existing)
        staged = n.create_directory(root, "stage-dir")
        try:
            handle = n.create_file(staged, "entry.json")
            n.write_all(handle, b"{}")
            n.flush(handle)
            n.close(handle)
            with pytest.raises(OSError, match="c0000035"):
                n.rename_no_replace(staged, root, "VE-existing")
            n.rename_no_replace(staged, root, "VE-new")
        finally:
            n.close(staged)
    finally:
        n.close(root)
    assert (tmp_path / "VE-existing").is_dir()
    assert (tmp_path / "VE-new" / "entry.json").read_bytes() == b"{}"


def test_competing_capture_cannot_duplicate_station_id(tmp_path, monkeypatch):
    import hashlib
    import threading
    from concurrent.futures import ThreadPoolExecutor
    from video_studio.effect_library import _native_windows as n
    project = tmp_path / "project"; project.mkdir()
    station = tmp_path / "entries"; station.mkdir()
    (project / "effect.js").write_bytes(b"data")
    keys = ("static_check", "preview", "render", "audio", "ratio_test", "reuse_evidence")
    m = {"id": "VE-race", "name": "Synthetic", "kind": "component", "maturity": "candidate",
         "rights": "owned", "source": "synthetic", "runtime": "js", "tags": [], "roles": [],
         "techniques": [], "ratios": [], "checks": dict.fromkeys(keys, "not_run"),
         "asset": {"path": "effect.js", "sha256": hashlib.sha256(b"data").hexdigest()}}
    def attempt():
        try:
            return n.capture_experiment(project, station, m)
        except (OSError, ValueError) as exc:
            return str(exc)
    with ThreadPoolExecutor(max_workers=2) as pool:
        result = list(pool.map(lambda _: attempt(), range(2)))
    assert result.count("VE-race") == 1
    assert any(x.startswith("NTSTATUS") or "already exists" in x for x in result)
    assert sorted(p.name for p in station.iterdir()) == ["VE-race"]


def test_corrupt_bundle_marker_does_not_fall_back_to_legacy(tmp_path):
    from video_studio.contract import ContractError
    from video_studio.effect_library import search
    d = tmp_path / "effect-library/entries/VE-corrupt"
    d.mkdir(parents=True)
    (d / "entry.json").write_text('{"format":"wrong", "entry":{}}', encoding="utf-8")
    with pytest.raises(ContractError, match="format"):
        search(station=tmp_path)


def test_materialize_reports_close_failure_after_publish(tmp_path, monkeypatch):
    import hashlib
    from video_studio.effect_library import _native_windows as n
    project = tmp_path / "project"; project.mkdir()
    station = tmp_path / "entries"; station.mkdir()
    target = tmp_path / "target"; target.mkdir()
    (project / "effect.js").write_bytes(b"data")
    checks = dict.fromkeys(("static_check", "preview", "render", "audio", "ratio_test", "reuse_evidence"), "not_run")
    m = {"id":"VE-close", "name":"Synthetic", "kind":"component", "maturity":"candidate",
         "rights":"owned", "source":"synthetic", "runtime":"js", "tags":[], "roles":[],
         "techniques":[], "ratios":[], "checks":checks,
         "asset":{"path":"effect.js", "sha256":hashlib.sha256(b"data").hexdigest()}}
    n.capture_experiment(project, station, m)
    original_rename, original_close = n.rename_no_replace, n.close
    state = {"published": False, "failed": False}
    def publish(*args):
        original_rename(*args)
        state["published"] = True
    def close_once(handle):
        original_close(handle)
        if state["published"] and not state["failed"]:
            state["failed"] = True
            raise OSError("simulated close failure")
    monkeypatch.setattr(n, "rename_no_replace", publish)
    monkeypatch.setattr(n, "close", close_once)
    with pytest.raises(n.PublishedButCloseFailed, match="asset published"):
        n.materialize_experiment(station, "VE-close", target, "result.js")
    assert (target / "result.js").read_bytes() == b"data"


def test_capture_rejects_duplicate_name_and_hash(tmp_path):
    import hashlib
    from video_studio.effect_library import _native_windows as n
    project = tmp_path / "project"; project.mkdir()
    station = tmp_path / "entries"; station.mkdir()
    asset = project / "effect.js"; asset.write_bytes(b"first")
    checks = dict.fromkeys(("static_check", "preview", "render", "audio", "ratio_test", "reuse_evidence"), "not_run")
    m = {"id":"VE-one", "name":"Original", "kind":"component", "maturity":"candidate",
         "rights":"owned", "source":"synthetic", "runtime":"js", "tags":[], "roles":[],
         "techniques":[], "ratios":[], "checks":checks,
         "asset":{"path":"effect.js", "sha256":hashlib.sha256(b"first").hexdigest()}}
    n.capture_experiment(project, station, m)
    m["id"] = "VE-two"; m["name"] = "Other"
    with pytest.raises(ValueError, match="hash already exists"):
        n.capture_experiment(project, station, m)
    asset.write_bytes(b"second"); m["asset"]["sha256"] = hashlib.sha256(b"second").hexdigest()
    m["name"] = "original"
    with pytest.raises(ValueError, match="name already exists"):
        n.capture_experiment(project, station, m)
    assert sorted(p.name for p in station.iterdir()) == ["VE-one"]


def test_stage_inventory_does_not_delete_unverified_entries(tmp_path):
    import json
    from video_studio.effect_library import _native_windows as n
    missing = tmp_path / ("stage-" + "a" * 32); missing.mkdir()
    present = tmp_path / ("stage-" + "b" * 32); present.mkdir()
    (present / "stage.json").write_text(json.dumps({"format":"ve-stage-v1", "stage":present.name,
        "id":"VE-case", "sha256":"a" * 64}), encoding="utf-8")
    results = n.inspect_stages(tmp_path)
    assert {r["status"] for r in results} == {"unverified", "marker_present_unverified"}
    assert missing.exists() and present.exists()


@pytest.mark.parametrize("phase", ["entry_write", "entry_flush"])
def test_capture_crash_after_marker_keeps_inspectable_stage(tmp_path, phase):
    import subprocess
    import sys
    project = tmp_path / "project"; project.mkdir()
    station = tmp_path / "entries"; station.mkdir()
    (project / "asset.js").write_bytes(b"data")
    code = r'''
import hashlib, os, sys
from video_studio.effect_library import _native_windows as n
checks=dict.fromkeys(("static_check","preview","render","audio","ratio_test","reuse_evidence"),"not_run")
m={"id":"VE-crash","name":"crash","kind":"component","maturity":"candidate","rights":"owned","source":"synthetic","runtime":"js","tags":[],"roles":[],"techniques":[],"ratios":[],"checks":checks,"asset":{"path":"asset.js","sha256":hashlib.sha256(b"data").hexdigest()}}
method="write_all" if sys.argv[3] == "entry_write" else "flush"
original=getattr(n,method); count=[0]
def crash(*args):
 original(*args); count[0]+=1
 if count[0] == 2: os._exit(42)
setattr(n,method,crash)
n.capture_experiment(sys.argv[1],sys.argv[2],m)
'''
    result = subprocess.run([sys.executable, "-c", code, str(project), str(station), phase], timeout=30)
    assert result.returncode == 42
    from video_studio.effect_library import _native_windows as n
    stages = n.inspect_stages(station)
    assert len(stages) == 1 and stages[0]["status"] == "marker_present_unverified"
    assert stages[0]["id"] == "VE-crash"
    assert not (station / "VE-crash").exists()


def test_capture_reports_lock_close_failure_after_publish(tmp_path, monkeypatch):
    import hashlib
    from video_studio.effect_library import _native_windows as n
    project = tmp_path / "project"; project.mkdir()
    station = tmp_path / "entries"; station.mkdir()
    (project / "effect.js").write_bytes(b"data")
    checks = dict.fromkeys(("static_check", "preview", "render", "audio", "ratio_test", "reuse_evidence"), "not_run")
    m = {"id":"VE-close-lock", "name":"Synthetic", "kind":"component", "maturity":"candidate",
         "rights":"owned", "source":"synthetic", "runtime":"js", "tags":[], "roles":[],
         "techniques":[], "ratios":[], "checks":checks,
         "asset":{"path":"effect.js", "sha256":hashlib.sha256(b"data").hexdigest()}}
    original_create, original_close = n.create_file, n.close
    state = {"lock": None}
    def capture_lock(root, name):
        handle = original_create(root, name)
        if name == ".capture.lock":
            state["lock"] = handle.value
        return handle
    def fail_lock_close(handle):
        value = handle.value
        original_close(handle)
        if value == state["lock"]:
            raise OSError("simulated lock close failure")
    monkeypatch.setattr(n, "create_file", capture_lock)
    monkeypatch.setattr(n, "close", fail_lock_close)
    with pytest.raises(n.PublishedButCloseFailed, match="entry published; closing lock"):
        n.capture_experiment(project, station, m)
    assert (station / "VE-close-lock" / "entry.json").exists()


def test_public_capture_search_materialize(tmp_path):
    import hashlib
    from video_studio.effect_library import capture, search, materialize
    p1 = tmp_path / "project-one"; p1.mkdir()
    p2 = tmp_path / "project-two"; p2.mkdir()
    station = tmp_path / "station"
    (station / "effect-library/entries").mkdir(parents=True)
    (p1 / "effect.js").write_bytes(b"synthetic public reusable effect")
    keys = ("static_check", "preview", "render", "audio", "ratio_test", "reuse_evidence")
    m = {"id":"VE-public", "name":"Synthetic public", "kind":"component", "maturity":"candidate",
         "rights":"owned", "source":"synthetic", "runtime":"js", "tags":[], "roles":[],
         "techniques":[], "ratios":[], "checks":dict.fromkeys(keys,"not_run"),
         "asset":{"path":"effect.js", "sha256":hashlib.sha256(b"synthetic public reusable effect").hexdigest()}}
    assert capture(p1, station, m) == "VE-public"
    assert search("synthetic public", station=station)[0]["id"] == "VE-public"
    materialize(station, "VE-public", p2, "effect.js")
    assert (p2 / "effect.js").read_bytes() == b"synthetic public reusable effect"


def test_public_capture_reference_and_prompt_metadata(tmp_path, monkeypatch):
    from video_studio.effect_library import capture, search, materialize
    from video_studio.effect_library import _native_windows as n
    project = tmp_path / "project"; project.mkdir()
    station = tmp_path / "station"
    (station / "effect-library/entries").mkdir(parents=True)
    keys = ("static_check", "preview", "render", "audio", "ratio_test", "reuse_evidence")
    entry = {"id": "VE-ref-test", "name": "Reference test", "kind": "reference",
             "maturity": "reference_only", "rights": "unknown", "source": "https://example.com/effects/one",
             "runtime": "online reference", "tags": ["orbit"], "roles": [], "techniques": [],
             "ratios": [], "checks": dict.fromkeys(keys, "not_run")}
    # A reference is metadata, so the project tree is never opened or read.
    real_open = n.open_root
    def guarded_open(path):
        assert os.fspath(path) != os.fspath(project)
        return real_open(path)
    monkeypatch.setattr(n, "open_root", guarded_open)
    assert capture(project, station, entry) == "VE-ref-test"
    assert search("orbit", station=station)[0]["source"] == entry["source"]
    with pytest.raises(ValueError, match="metadata"):
        materialize(station, entry["id"], project, "output.txt")
    duplicate = dict(entry, id="VE-ref-copy", name="Another reference")
    with pytest.raises(ValueError, match="source already exists"):
        capture(project, station, duplicate)
    prompt = dict(entry, id="VE-prompt-test", name="Prompt test", kind="prompt", rights="owned",
                  source="created synthetic", prompt_text="Create a slow orbital glow.")
    assert capture(project, station, prompt) == "VE-prompt-test"
    result = search("slow orbital glow", station=station)
    assert result[0]["prompt_text"] == prompt["prompt_text"]
    assert search("orbit", station=station)[0].get("asset") is None
    with pytest.raises(ValueError, match="prompt.*rights"):
        capture(project, station, dict(prompt, id="VE-unknown", name="Unknown", rights="unknown"))
    with pytest.raises(ValueError, match="HTTP"):
        capture(project, station, dict(entry, id="VE-bad-url", name="Bad", source="local source"))


def test_metadata_capture_crash_is_not_published(tmp_path):
    import subprocess
    import sys
    station = tmp_path / "entries"; station.mkdir()
    code = r'''
import os, sys
from video_studio.effect_library import _native_windows as n
c=dict.fromkeys(("static_check","preview","render","audio","ratio_test","reuse_evidence"),"not_run")
m={"id":"VE-ref-crash","name":"Reference crash","kind":"reference","maturity":"reference_only","rights":"unknown","source":"https://example.com/crash","runtime":"online","tags":[],"roles":[],"techniques":[],"ratios":[],"checks":c}
original=n.write_all; count=[0]
def crash(*args):
 original(*args); count[0]+=1
 if count[0]==2: os._exit(42)
n.write_all=crash
n.capture_experiment(sys.argv[1],sys.argv[2],m)
'''
    result = subprocess.run([sys.executable, "-c", code, str(tmp_path), str(station)], timeout=30)
    assert result.returncode == 42
    from video_studio.effect_library import _native_windows as n
    assert n.search_experiment(station) == []
    assert n.inspect_stages(station)[0]["status"] == "marker_present_unverified"


def test_metadata_reader_rejects_tampered_prompt_rights(tmp_path):
    import json
    from video_studio.contract import ContractError
    from video_studio.effect_library import capture, search
    station = tmp_path / "station"
    entries = station / "effect-library/entries"; entries.mkdir(parents=True)
    keys = ("static_check", "preview", "render", "audio", "ratio_test", "reuse_evidence")
    prompt = {"id": "VE-prompt-rights", "name": "Prompt rights", "kind": "prompt",
              "maturity": "candidate", "rights": "owned", "source": "synthetic",
              "runtime": "text", "tags": [], "roles": [], "techniques": [], "ratios": [],
              "checks": dict.fromkeys(keys, "not_run"), "prompt_text": "synthetic text"}
    capture(tmp_path, station, prompt)
    path = entries / prompt["id"] / "entry.json"
    record = json.loads(path.read_text(encoding="utf-8"))
    record["entry"]["rights"] = "unknown"
    path.write_text(json.dumps(record), encoding="utf-8")
    with pytest.raises(ContractError, match="prompt.*rights"):
        search(station=station)


def test_metadata_size_is_checked_before_publication(tmp_path):
    from video_studio.effect_library import capture, search
    from video_studio.effect_library import _native_windows as n
    station = tmp_path / "station"
    entries = station / "effect-library/entries"; entries.mkdir(parents=True)
    keys = ("static_check", "preview", "render", "audio", "ratio_test", "reuse_evidence")
    prompt = {"id": "VE-size-limit", "name": "Size limit", "kind": "prompt",
              "maturity": "candidate", "rights": "owned", "source": "synthetic",
              "runtime": "text", "tags": [], "roles": [], "techniques": [], "ratios": [],
              "checks": dict.fromkeys(keys, "not_run"), "prompt_text": "x" * n.MAX_METADATA_BYTES}
    with pytest.raises(ValueError, match="metadata.*size limit"):
        capture(tmp_path, station, prompt)
    assert list(entries.iterdir()) == []
    prompt["prompt_text"] = "x" * (n.MAX_METADATA_BYTES - 4096)
    assert capture(tmp_path, station, prompt) == "VE-size-limit"
    assert search("Size limit", station=station)[0]["prompt_text"] == prompt["prompt_text"]


def test_reference_source_cannot_duplicate_prompt_motion(tmp_path):
    from video_studio.effect_library import capture
    station = tmp_path / "station"
    entries = station / "effect-library/entries"; entries.mkdir(parents=True)
    keys = ("static_check", "preview", "render", "audio", "ratio_test", "reuse_evidence")
    entry = {"id": "VE-pm-duplicate", "name": "A distinct name", "kind": "reference",
             "maturity": "reference_only", "rights": "unknown",
             "source": "https://prompt-motion.com/stephanlivera-df17a2", "runtime": "online",
             "tags": [], "roles": [], "techniques": [], "ratios": [],
             "checks": dict.fromkeys(keys, "not_run")}
    with pytest.raises(ValueError, match="Prompt Motion"):
        capture(tmp_path, station, entry)
    assert list(entries.iterdir()) == []


def test_unknown_reference_rejects_arbitrary_content_on_capture_and_read(tmp_path):
    import json
    from video_studio.contract import ContractError
    from video_studio.effect_library import capture, search
    station = tmp_path / "station"
    entries = station / "effect-library/entries"; entries.mkdir(parents=True)
    keys = ("static_check", "preview", "render", "audio", "ratio_test", "reuse_evidence")
    entry = {"id": "VE-safe-ref", "name": "Safe reference", "kind": "reference",
             "maturity": "reference_only", "rights": "unknown", "source": "https://example.com/safe",
             "runtime": "online", "tags": [], "roles": [], "techniques": [], "ratios": [],
             "checks": dict.fromkeys(keys, "not_run"), "repository": "https://example.com/repo",
             "license_note": "See upstream license", "license_url": "https://example.com/license",
             "details": "references/guide.md"}
    for extra in ({"payload": "THIRD PARTY TEXT OR DATA"},
                  {"metadata": {"nested": "third party content"}},
                  {"checks": dict(entry["checks"], extra={"nested": "third party content"})},
                  {"checks": dict(entry["checks"], render={"nested": "third party content"})},
                  {"license_url": "javascript:alert(1)"},
                  {"license_url": "https://user:pass@example.com/license"},
                  {"license_url": "https://example.com/bad path"},
                  {"details": {"nested": "third party content"}}):
        with pytest.raises((ValueError, ContractError)):
            capture(tmp_path, station, dict(entry, **extra))
    assert list(entries.iterdir()) == []
    assert capture(tmp_path, station, entry) == entry["id"]
    assert search("Safe reference", station=station)[0]["repository"] == entry["repository"]
    path = entries / entry["id"] / "entry.json"
    record = json.loads(path.read_text(encoding="utf-8"))
    record["entry"]["license_url"] = "file:///private"
    path.write_text(json.dumps(record), encoding="utf-8")
    with pytest.raises((ValueError, ContractError)):
        search(station=station)
    record["entry"]["license_url"] = entry["license_url"]
    record["entry"]["payload"] = {"nested": "third party content"}
    path.write_text(json.dumps(record), encoding="utf-8")
    with pytest.raises((ValueError, ContractError)):
        search(station=station)

@pytest.mark.parametrize('existing_name,new_name', [('\u1ea2nh s\u00e1ng', 'A\u0309nh sa\u0301ng'), ('A\u0309nh sa\u0301ng', '\u1ea2nh s\u00e1ng')])
@pytest.mark.parametrize('location', ['repo', 'station'])
def test_capture_rejects_canonically_equivalent_names(tmp_path, monkeypatch, existing_name, new_name, location):
    import json
    from video_studio.effect_library import _native_windows as n, resources, distilled_sources
    project = tmp_path / 'project'; project.mkdir()
    entries = tmp_path / 'entries'; entries.mkdir()
    checks = dict.fromkeys(('static_check', 'preview', 'render', 'audio', 'ratio_test', 'reuse_evidence'), 'not_run')
    base = {'id': 'VE-first', 'name': existing_name, 'kind': 'prompt', 'maturity': 'candidate',
            'rights': 'owned', 'source': 'synthetic', 'runtime': 'text', 'tags': [], 'roles': [],
            'techniques': [], 'ratios': [], 'checks': checks, 'prompt_text': 'first distinct prompt'}
    if location == 'repo':
        repo = tmp_path / 'repo'
        index = repo / 'skills/video-theme-library/assets/effect-library/entries.json'
        index.parent.mkdir(parents=True)
        index.write_text(json.dumps([base], ensure_ascii=False), encoding='utf-8')
        monkeypatch.setattr(resources, 'resource_root', lambda: repo)
        monkeypatch.setattr(distilled_sources, 'load_distilled', lambda root: [])
    else:
        n.capture_experiment(project, entries, base)
    second = dict(base, id='VE-second', name=new_name, prompt_text='second distinct prompt')
    with pytest.raises(ValueError, match='name already exists'):
        n.capture_experiment(project, entries, second)
    assert not (entries / 'VE-second').exists()


def test_capture_keeps_distinct_accented_names(tmp_path):
    from video_studio.effect_library import _native_windows as n
    project = tmp_path / 'project'; project.mkdir()
    entries = tmp_path / 'entries'; entries.mkdir()
    checks = dict.fromkeys(('static_check', 'preview', 'render', 'audio', 'ratio_test', 'reuse_evidence'), 'not_run')
    base = {'id': 'VE-first', 'name': '\u00c1nh s\u00e1ng', 'kind': 'prompt', 'maturity': 'candidate',
            'rights': 'owned', 'source': 'synthetic', 'runtime': 'text', 'tags': [], 'roles': [],
            'techniques': [], 'ratios': [], 'checks': checks, 'prompt_text': 'first distinct prompt'}
    n.capture_experiment(project, entries, base)
    second = dict(base, id='VE-second', name='Anh sang', prompt_text='second distinct prompt')
    n.capture_experiment(project, entries, second)
    assert {record['name'] for record in n.search_experiment(entries)} == {base['name'], second['name']}


def test_reference_distinguishes_trailing_slash_but_rejects_same_url(tmp_path):
    from video_studio.effect_library import capture, search

    station = tmp_path / "station"
    (station / "effect-library" / "entries").mkdir(parents=True)
    keys = ("static_check", "preview", "render", "audio", "ratio_test", "reuse_evidence")
    base = {"kind": "reference", "maturity": "reference_only", "rights": "unknown",
            "runtime": "online", "tags": ["synthetic-ref"], "roles": [], "techniques": [],
            "ratios": [], "checks": dict.fromkeys(keys, "not_run")}
    first = dict(base, id="VE-slash-one", name="Slash one", source="https://example.invalid/library")
    second = dict(base, id="VE-slash-two", name="Slash two", source="https://example.invalid/library/")
    assert capture(tmp_path, station, first) == first["id"]
    assert capture(tmp_path, station, second) == second["id"]
    assert {item["source"] for item in search("synthetic ref", station=station)} == {first["source"], second["source"]}
    with pytest.raises(ValueError, match="source already exists"):
        capture(tmp_path, station, dict(base, id="VE-slash-three", name="Slash three",
                                       source="https://EXAMPLE.INVALID/library"))
    with pytest.raises(ValueError, match="source already exists"):
        capture(tmp_path, station, dict(base, id="VE-slash-four", name="Slash four",
                                       source=second["source"]))


def test_reference_key_preserves_empty_query_delimiter():
    from video_studio.effect_library._native_windows import _reference_key
    assert _reference_key("https://EXAMPLE.invalid/library?") != _reference_key("https://example.invalid/library")
    assert _reference_key("https://EXAMPLE.invalid/library?") == _reference_key("https://example.invalid/library?")


def test_reference_key_preserves_ipv6_zone_case():
    from video_studio.effect_library._native_windows import _reference_key
    assert _reference_key("https://[FE80::1%25ZoneA]/x") != _reference_key("https://[fe80::1%25zonea]/x")
    assert _reference_key("https://[FE80::1%25ZoneA]/x") == _reference_key("https://[fe80::1%25ZoneA]/x")


@pytest.mark.parametrize("first_source,second_source", [
    ("https://example.invalid/library", "https://example.invalid/library?"),
    ("https://[fe80::1%25ZoneA]/x", "https://[fe80::1%25zonea]/x"),
])
def test_capture_preserves_distinct_reference_url_parts(tmp_path, first_source, second_source):
    from video_studio.effect_library import capture, search

    station = tmp_path / "station"
    (station / "effect-library" / "entries").mkdir(parents=True)
    keys = ("static_check", "preview", "render", "audio", "ratio_test", "reuse_evidence")
    base = {"kind": "reference", "maturity": "reference_only", "rights": "unknown",
            "runtime": "online", "tags": ["synthetic-distinct"], "roles": [], "techniques": [],
            "ratios": [], "checks": dict.fromkeys(keys, "not_run")}
    capture(tmp_path, station, dict(base, id="VE-parts-one", name="Parts one", source=first_source))
    capture(tmp_path, station, dict(base, id="VE-parts-two", name="Parts two", source=second_source))
    assert {item["source"] for item in search("synthetic distinct", station=station)} == {first_source, second_source}
