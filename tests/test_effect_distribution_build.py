"""Tests for the explicit, fail-closed effect distribution candidate builder."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path

import pytest


SPEC = importlib.util.spec_from_file_location(
    "effect_distribution_builder", Path(__file__).resolve().parents[1] / "scripts/build_effect_distribution.py"
)
builder = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(builder)


def fixture(monkeypatch):
    root = "skills/video-theme-library/assets/prompt-motion/"
    catalog = "skills/video-theme-library/assets/effect-library/entries.json"
    checks = {key: "not_run" for key in ("static_check", "preview", "render", "audio", "ratio_test", "reuse_evidence")}
    record = {"id": "VE-example", "name": "Example", "kind": "component", "maturity": "candidate",
              "rights": "owned", "source": "source.md", "runtime": "test", "tags": [], "roles": [],
              "techniques": [], "ratios": [], "asset": {"path": "skills/sample.js", "sha256": hashlib.sha256(b"asset").hexdigest()},
              "checks": checks}
    rights = "skills/video-theme-library/assets/effect-library/distribution-rights.json"
    content = {catalog: json.dumps([record]).encode(), rights: b'{"schema":"effect-distribution-rights/1","files":{}}', "source.md": b"source", "skills/sample.js": b"asset",
               root + "source/provenance.json": b"{}"}
    cards = []
    for index in range(240):
        name = f"motions/{index}.md"
        cards.append({"file": name})
        content[root + name] = b"[source](../source/provenance.json)"
    content[root + "index.json"] = json.dumps({"entries": cards}).encode()
    resources = list(content)
    manifest = {"schema": "effect-distribution-manifest/1", "files": {}, "resources": resources}

    def refresh():
        manifest["files"] = {k: hashlib.sha256(v).hexdigest() for k, v in content.items()}

    def read(_root, path):
        if path == builder.MANIFEST:
            return json.dumps(manifest).encode()
        return content[path]

    monkeypatch.setattr(builder, "_read_relative", read)
    # source.md is a representative local license/provenance document.
    monkeypatch.setattr(builder, "_source_allowed", lambda path: path in content and '..' not in path)
    refresh()
    return content, manifest, record, refresh


def test_manifest_closure_and_source_tampering(monkeypatch):
    content, manifest, _, _ = fixture(monkeypatch)
    loaded, _ = builder._inputs(None)
    assert len(loaded) == len(content)
    content["skills/sample.js"] = b"tampered"
    with pytest.raises(ValueError, match="source hash mismatch"):
        builder._inputs(None)
    assert manifest["files"]["skills/sample.js"] != hashlib.sha256(content["skills/sample.js"]).hexdigest()


def test_manifest_rejects_missing_card_provenance(monkeypatch):
    content, manifest, _, refresh = fixture(monkeypatch)
    source = "skills/video-theme-library/assets/prompt-motion/source/provenance.json"
    del content[source]
    manifest["resources"].remove(source)
    refresh()
    with pytest.raises(ValueError, match="provenance missing"):
        builder._inputs(None)


def test_manifest_rejects_asset_without_declared_rights(monkeypatch):
    content, _, record, refresh = fixture(monkeypatch)
    record["rights"] = "unknown"
    content["skills/video-theme-library/assets/effect-library/entries.json"] = json.dumps([record]).encode()
    refresh()
    with pytest.raises(ValueError, match="distribution rights"):
        builder._inputs(None)


def test_manifest_rejects_unaccounted_executable_resource(monkeypatch):
    content, manifest, _, refresh = fixture(monkeypatch)
    content["skills/extra.js"] = b"not accounted for"
    manifest["resources"].append("skills/extra.js")
    refresh()
    with pytest.raises(ValueError, match="unaccounted executable"):
        builder._inputs(None)


def test_build_runner_bounds_output_and_timeout(tmp_path):
    import sys

    overflow = builder._run_bounded([sys.executable, "-c", "import sys; sys.stdout.write('x' * 1000000); sys.stdout.flush()"],
                                    tmp_path, total_timeout=10, idle_timeout=5, max_output=8192)
    assert overflow["reason"] == "output_limit"
    assert len(overflow["output"]) <= 4096
    assert not overflow["cleanup_unconfirmed"]
    timeout = builder._run_bounded([sys.executable, "-c", "import time; time.sleep(5)"],
                                   tmp_path, total_timeout=3, idle_timeout=0.3)
    assert timeout["reason"] == "idle_timeout"
    assert timeout["timed_out"] is True
    assert not timeout["cleanup_unconfirmed"]


def test_build_runner_short_heartbeats_reset_idle_clock(tmp_path):
    import sys

    script = "import os,time\nfor i in range(12):\n os.write(1,b'.'); time.sleep(.1)"
    result = builder._run_bounded([sys.executable, "-c", script], tmp_path,
                                  total_timeout=8, idle_timeout=0.6)
    assert result["reason"] is None
    assert result["timed_out"] is False
    assert result["exit_code"] == 0
    assert result["output"] == "." * 12
    assert not result["cleanup_unconfirmed"]


def test_sdist_verifier_rejects_missing_and_duplicate_members():
    import io
    import tarfile

    def archive(rows):
        output = io.BytesIO()
        with tarfile.open(fileobj=output, mode="w:gz") as tar:
            for name, data in rows:
                info = tarfile.TarInfo("package/" + name)
                info.size = len(data)
                tar.addfile(info, io.BytesIO(data))
        return output.getvalue()

    expected = {"video_studio/a.py": b"a", "video_studio/b.py": b"b"}
    builder._validate_sdist(archive(list(expected.items())), expected)
    with pytest.raises(ValueError, match="missing required"):
        builder._validate_sdist(archive([("video_studio/a.py", b"a")]), expected)
    with pytest.raises(ValueError, match="duplicate"):
        builder._validate_sdist(archive(list(expected.items()) + [("video_studio/a.py", b"a")]), expected)
    with pytest.raises(ValueError, match="mismatch"):
        builder._validate_sdist(archive([("video_studio/a.py", b"changed"), ("video_studio/b.py", b"b")]), expected)


@pytest.mark.parametrize("path", ["../private", "workspaces/private.json", "video_studio/.env", "video_studio/credentials.json", "skills/a/../../secret.js"])
def test_source_allowlist_rejects_sensitive_or_escaping_paths(path):
    assert not builder._source_allowed(path)


@pytest.mark.skipif(os.name == "nt", reason="other systems are deliberately fail-closed")
def test_build_is_fail_closed_off_windows(tmp_path):
    with pytest.raises(RuntimeError, match="platform not verified"):
        builder.build(tmp_path)


@pytest.mark.skipif(os.name != "nt", reason="Windows handle primitives required")
def test_source_reader_refuses_junction_to_external_file(tmp_path):
    import subprocess

    root = tmp_path / "root"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    (outside / "private.json").write_text("private sentinel", encoding="utf-8")
    env = os.environ.copy()
    env["EFFECT_TEST_LINK"] = str(root / "redirect")
    env["EFFECT_TEST_TARGET"] = str(outside)
    result = subprocess.run(["powershell", "-NoProfile", "-Command",
                             "New-Item -ItemType Junction -Path $env:EFFECT_TEST_LINK -Target $env:EFFECT_TEST_TARGET | Out-Null"],
                            env=env, capture_output=True, timeout=20)
    if result.returncode:
        pytest.skip("Windows junction setup unavailable")
    handle = builder.nt.open_root(str(root))
    try:
        with pytest.raises(OSError, match="c000050b"):
            builder._read_relative(handle, "redirect/private.json")
    finally:
        builder.nt.close(handle)
        (root / "redirect").rmdir()


@pytest.mark.skipif(os.name != "nt" or os.environ.get("EFFECT_DIST_TEST") != "1",
                    reason="explicit isolated Windows distribution integration test")
def test_isolated_wheel_and_sdist_round_trip(tmp_path):
    import subprocess
    import sys
    import zipfile

    output = tmp_path / "output"
    output.mkdir()
    names = builder.build(output)
    assert len(names) == 2
    source_wheel = next(output.glob("*.whl"))
    source_sdist = next(output.glob("*.tar.gz"))
    rebuilt = tmp_path / "rebuilt"
    rebuilt.mkdir()
    result = subprocess.run([sys.executable, "-m", "pip", "wheel", "--no-cache-dir", "--no-index",
                             "--no-deps", "--no-build-isolation", "--wheel-dir", str(rebuilt), str(source_sdist)],
                            cwd=tmp_path, capture_output=True, timeout=180)
    assert result.returncode == 0, result.stderr.decode("utf-8", errors="replace")
    resource_prefix = "video_studio/_bundled/"
    with zipfile.ZipFile(source_wheel) as first, zipfile.ZipFile(next(rebuilt.glob("*.whl"))) as second:
        first_resources = {n: first.read(n) for n in first.namelist() if n.startswith(resource_prefix)}
        second_resources = {n: second.read(n) for n in second.namelist() if n.startswith(resource_prefix)}
        assert first_resources == second_resources
        assert len([n for n in first_resources if "/prompt-motion/motions/" in n]) == 240
        assert resource_prefix + "NOTICE" in first_resources
        assert resource_prefix + "LICENSE-APACHE" in first_resources
        installed = tmp_path / "installed"
        first.extractall(installed)
        rebuilt_installed = tmp_path / "rebuilt-installed"
        second.extractall(rebuilt_installed)
    # Exercise the bundled asset in both distributions without a checkout sibling.
    for package in (installed, rebuilt_installed):
        project = tmp_path / (package.name + "-project")
        project.mkdir()
        env = os.environ.copy()
        env["PYTHONPATH"] = str(package)
        exercise_repo = '''import hashlib, pathlib, sys
from video_studio.effect_library import materialize_repo
from video_studio.effect_library.resources import resource_root
project = pathlib.Path(sys.argv[1])
source = resource_root() / 'skills/photo-ambient-effects/assets/lens-flare.js'
digest = hashlib.sha256(source.read_bytes()).hexdigest()
materialize_repo('VE-lens-flare', project, 'flare.js')
assert hashlib.sha256((project / 'flare.js').read_bytes()).hexdigest() == digest
try:
    materialize_repo('VE-lens-flare', project, 'flare.js')
except OSError:
    pass
else:
    raise AssertionError('materialize_repo overwrote an existing file')
assert hashlib.sha256((project / 'flare.js').read_bytes()).hexdigest() == digest
'''
        result = subprocess.run([sys.executable, "-c", exercise_repo, str(project)],
                                cwd=tmp_path, env=env, capture_output=True, timeout=60)
        assert result.returncode == 0, result.stderr.decode("utf-8", errors="replace")
    # A separate package may own site-packages/skills; it must not shadow the wheel.
    sibling = installed / "skills/video-theme-library/assets"
    (sibling / "effect-library").mkdir(parents=True)
    (sibling / "effect-library/entries.json").write_text("[]", encoding="utf-8")
    (sibling / "prompt-motion").mkdir(parents=True)
    (sibling / "prompt-motion/index.json").write_text('{"entries": []}', encoding="utf-8")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(installed)
    result = subprocess.run([sys.executable, "-m", "video_studio.effect_library", "--q", "lens flare"],
                            cwd=tmp_path, env=env, capture_output=True, timeout=60)
    assert result.returncode == 0, result.stderr.decode("utf-8", errors="replace")
    assert "VE-lens-flare" in result.stdout.decode("utf-8")
    for query, identifier, source in (
        ("speedramp", "VE-ref-ffmpeg-speedramp", "skills/video-edit/references/ffmpeg-tool-index.md#"),
        ("continuity", "VE-ref-hypit-t7", "skills/video-routing/references/production-techniques.md#"),
    ):
        result = subprocess.run([sys.executable, "-m", "video_studio.effect_library", "--q", query, "--limit", "100"],
                                cwd=tmp_path, env=env, capture_output=True, timeout=60)
        assert result.returncode == 0, result.stderr.decode("utf-8", errors="replace")
        matches = [row["entry"] for row in json.loads(result.stdout.decode("utf-8")) if row["entry"]["id"] == identifier]
        assert len(matches) == 1
        assert matches[0]["source"].startswith(source)
        assert matches[0]["maturity"] == "reference_only"
        assert matches[0]["checks"] and set(matches[0]["checks"].values()) == {"not_run"}
    for query, identifier in (
        ("earshot", "VE-earshot-sound"),
        ("vtake", "VE-vtake-cards"),
        ("video-use", "VE-video-use-editing"),
        ("MP01", "VE-design-studio-motion-patterns"),
        ("MP06", "VE-design-studio-motion-patterns"),
        ("motion spec", "VE-design-studio-motion-spec"),
    ):
        result = subprocess.run([sys.executable, "-m", "video_studio.effect_library", "--q", query, "--limit", "100"],
                                cwd=tmp_path, env=env, capture_output=True, timeout=60)
        assert result.returncode == 0, result.stderr.decode("utf-8", errors="replace")
        row = next(row["entry"] for row in json.loads(result.stdout.decode("utf-8")) if row["entry"]["id"] == identifier)
        assert row["maturity"] == "reference_only" and row["rights"] == "unknown"
        assert (installed / "video_studio/_bundled" / row["source"]).is_file()
    distilled_document = installed / "video_studio/_bundled/skills/video-edit/references/ffmpeg-tool-index.md"
    original_document = distilled_document.read_bytes()
    distilled_document.unlink()
    result = subprocess.run([sys.executable, "-m", "video_studio.effect_library", "--q", "speedramp"],
                            cwd=tmp_path, env=env, capture_output=True, timeout=60)
    assert result.returncode == 2
    distilled_document.write_bytes(original_document)
    exercise = '''import hashlib, pathlib, tempfile
from video_studio.effect_library import capture, materialize, search
with tempfile.TemporaryDirectory() as tmp:
    root=pathlib.Path(tmp); a=root/'a'; b=root/'b'; station=root/'station'
    a.mkdir(); b.mkdir(); (station/'effect-library/entries').mkdir(parents=True)
    payload=b'wheel synthetic'; (a/'a.js').write_bytes(payload)
    entry={'id':'VE-wheel-test','name':'Wheel Test','kind':'component','maturity':'candidate','rights':'owned','source':'synthetic','runtime':'js','tags':[],'roles':[],'techniques':[],'ratios':[], 'asset':{'path':'a.js','sha256':hashlib.sha256(payload).hexdigest()},'checks':{k:'not_run' for k in ('static_check','preview','render','audio','ratio_test','reuse_evidence')}}
    capture(a,station,entry); assert search('wheel test',station=station)[0]['id']=='VE-wheel-test'
    materialize(station,'VE-wheel-test',b,'b.js'); assert (b/'b.js').read_bytes()==payload
'''
    result = subprocess.run([sys.executable, "-c", exercise], cwd=tmp_path, env=env,
                            capture_output=True, timeout=60)
    assert result.returncode == 0, result.stderr.decode("utf-8", errors="replace")
    (installed / "video_studio/_bundled/skills/video-theme-library/assets/prompt-motion/index.json").unlink()
    result = subprocess.run([sys.executable, "-m", "video_studio.effect_library", "--q", "lens flare"],
                            cwd=tmp_path, env=env, capture_output=True, timeout=60)
    assert result.returncode == 2
    assert b"missing or incomplete" in result.stderr
