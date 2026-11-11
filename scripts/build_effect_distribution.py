"""Build isolated Windows distribution candidates from a pinned source manifest.

This is an explicit, offline staging command; it does not install or publish.
The manifest must be reviewed and refreshed when a listed input changes.
"""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import posixpath
import re
import subprocess
import sys
import tarfile
import tempfile
import threading
import time
import zipfile


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from video_studio.effect_library import _native_windows as nt  # noqa: E402
from video_studio.effect_library.catalog import validate_entry  # noqa: E402

MANIFEST = "scripts/effect-distribution-manifest.json"


def _read_relative(root, relative):
    parts = PurePosixPath(relative).parts
    if not parts or any(p in (".", "..") for p in relative.split("/")):
        raise ValueError("unsafe manifest path")
    handles = []
    try:
        parent = root
        for part in parts[:-1]:
            parent = nt.open_directory(parent, part)
            handles.append(parent)
        file = nt.open_file(parent, parts[-1])
        handles.append(file)
        return nt.read_all(file)
    finally:
        for handle in reversed(handles):
            nt.close(handle)


def _source_allowed(path):
    if not isinstance(path, str) or not path or "\\" in path:
        return False
    p = PurePosixPath(path)
    if p.is_absolute() or any(part in ("", ".", "..") for part in path.split("/")):
        return False
    if any(part.startswith(".") for part in p.parts):
        return False
    if any(word in p.name.lower() for word in ("credential", "secret", "token", "auth.json")):
        return False
    if path in {"pyproject.toml", "README.md", "LICENSE", "LICENSE-APACHE", "NOTICE", "upstream.json", "docs/THEME-LIBRARY.md", "docs/CONTRACT.md", "docs/reference-to-remix.md"}:
        return True
    if path.startswith("video_studio/"):
        return p.suffix in {".py", ".html", ".json", ".md"} and "_bundled" not in p.parts
    return path.startswith("skills/") and p.suffix in {".md", ".json", ".js", ".mjs", ".css"}


def _inputs(root):
    manifest = json.loads(_read_relative(root, MANIFEST).decode("utf-8"))
    if manifest.get("schema") != "effect-distribution-manifest/1":
        raise ValueError("unknown distribution manifest")
    files = manifest.get("files")
    resources = manifest.get("resources")
    if not isinstance(files, dict) or not isinstance(resources, list) or len(set(resources)) != len(resources):
        raise ValueError("invalid distribution manifest")
    if (any(not _source_allowed(p) for p in files) or not set(resources).issubset(files) or
            any(p.startswith("video_studio/") or p in {"pyproject.toml", "README.md"} for p in resources)):
        raise ValueError("distribution manifest contains forbidden input")
    contents = {}
    for name, expected in files.items():
        if not isinstance(expected, str) or len(expected) != 64:
            raise ValueError("invalid source hash")
        content = _read_relative(root, name)
        if hashlib.sha256(content).hexdigest() != expected:
            raise ValueError(f"source hash mismatch: {name}")
        contents[name] = content
    catalog = json.loads(contents["skills/video-theme-library/assets/effect-library/entries.json"])
    catalog_assets = set()
    for entry in catalog:
        validate_entry(entry)
        for path in (entry.get("source"), entry.get("details"), (entry.get("license") or {}).get("source")):
            if path and "://" not in path and path not in resources:
                raise ValueError(f"referenced resource missing: {path}")
        asset = entry.get("asset")
        if asset:
            catalog_assets.add(asset["path"])
            if entry.get("rights") not in {"owned", "licensed"}:
                raise ValueError("asset without declared distribution rights")
            if entry.get("rights") == "licensed" and not all(entry.get("license", {}).get(k) for k in ("id", "source", "terms")):
                raise ValueError("licensed asset missing provenance")
            if asset["path"] not in resources or files[asset["path"]] != asset["sha256"]:
                raise ValueError("asset missing or hash mismatch")
    rights_path = "skills/video-theme-library/assets/effect-library/distribution-rights.json"
    if rights_path not in resources:
        raise ValueError("distribution rights inventory missing")
    inventory = json.loads(contents[rights_path])
    if inventory.get("schema") != "effect-distribution-rights/1" or not isinstance(inventory.get("files"), dict):
        raise ValueError("invalid distribution rights inventory")
    executable = {p for p in resources if PurePosixPath(p).suffix in {".js", ".mjs", ".css"}}
    if set(inventory["files"]) != executable - catalog_assets:
        raise ValueError("unaccounted executable resource rights")
    for path, terms in inventory["files"].items():
        if (not isinstance(terms, dict) or not isinstance(terms.get("license"), str) or not terms["license"].strip()
                or terms.get("provenance") not in resources or not isinstance(terms.get("notices"), list)
                or not terms["notices"] or any(n not in resources for n in terms["notices"])):
            raise ValueError(f"missing resource rights evidence: {path}")
    motion_root = "skills/video-theme-library/assets/prompt-motion/"
    index = json.loads(contents[motion_root + "index.json"])
    cards = [motion_root + e["file"] for e in index["entries"]]
    if len(cards) != 240 or len(set(cards)) != 240 or any(p not in resources for p in cards):
        raise ValueError("Prompt Motion index/card set is incomplete")
    for card in cards:
        for link in re.findall(r"\]\(([^)]*)\)", contents[card].decode("utf-8")):
            path = link.split("#", 1)[0]
            if not path or "://" in path:
                continue
            resolved = posixpath.normpath(posixpath.join(posixpath.dirname(card), path))
            if resolved not in resources:
                raise ValueError(f"Prompt Motion provenance missing: {resolved}")
    for name in resources:
        if not name.endswith(".md"):
            continue
        for link in re.findall(r"\]\(([^)]*)\)", contents[name].decode("utf-8")):
            path = link.split("#", 1)[0]
            if not path or "://" in path or path.startswith("mailto:"):
                continue
            resolved = posixpath.normpath(posixpath.join(posixpath.dirname(name), path))
            if resolved not in resources:
                raise ValueError(f"bundled reference missing: {resolved}")
    return contents, resources


def _stage_file(root, parts, data, directories, held_files):
    parent = root
    prefix = ()
    for part in parts[:-1]:
        prefix += (part,)
        if prefix not in directories:
            directories[prefix] = nt.create_directory(parent, part)
        parent = directories[prefix]
    handle = nt.create_file(parent, parts[-1])
    try:
        nt.write_all(handle, data)
        nt.flush(handle)
    finally:
        nt.close(handle)
    handle = nt.open_file(parent, parts[-1])
    if nt.read_all(handle) != data:
        nt.close(handle)
        raise ValueError("staged input changed before pinning")
    held_files.append(handle)


def _run_bounded(args, cwd, *, total_timeout=180, idle_timeout=60, max_output=1024 * 1024):
    """Return separate outcome fields and retain only a bounded output tail."""
    from video_studio.probe import _kill_tree

    started = time.monotonic()
    state = {"last_output": started, "total": 0, "tail": b"", "overflow": False, "read_error": None}
    lock = threading.Lock()
    flags = {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == "nt" else {"start_new_session": True}
    try:
        process = subprocess.Popen(args, cwd=cwd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT, **flags)
    except OSError as exc:
        return {"exit_code": None, "elapsed": time.monotonic() - started, "timed_out": False,
                "reason": "spawn_error", "output": "", "error": str(exc), "cleanup_unconfirmed": False}

    def read_output():
        try:
            while True:
                # BufferedReader.read(8192) may wait for 8192 bytes or EOF,
                # hiding short progress writes from the idle-timeout clock.
                chunk = os.read(process.stdout.fileno(), 8192)
                if not chunk:
                    break
                with lock:
                    state["last_output"] = time.monotonic()
                    state["total"] += len(chunk)
                    state["tail"] = (state["tail"] + chunk)[-4096:]
                    if state["total"] > max_output:
                        state["overflow"] = True
                        break
        except OSError as exc:
            with lock:
                state["read_error"] = str(exc)

    reader = threading.Thread(target=read_output, daemon=True)
    reader.start()
    reason = None
    timed_out = False
    while True:
        now = time.monotonic()
        with lock:
            overflow, last = state["overflow"], state["last_output"]
        if overflow:
            reason = "output_limit"
        elif now - started >= total_timeout:
            reason, timed_out = "total_timeout", True
        elif now - last >= idle_timeout:
            reason, timed_out = "idle_timeout", True
        elif process.poll() is not None and not reader.is_alive():
            break
        if reason:
            _kill_tree(process)
            break
        time.sleep(0.05)
    reader.join(timeout=2)
    with lock:
        tail, read_error = state["tail"], state["read_error"]
    cleanup_unconfirmed = process.poll() is None or reader.is_alive()
    if read_error and not reason:
        reason = "read_error"
    return {"exit_code": process.poll(), "elapsed": time.monotonic() - started, "timed_out": timed_out,
            "reason": reason, "output": tail.decode("utf-8", "replace"), "error": read_error,
            "cleanup_unconfirmed": cleanup_unconfirmed}


def _run(args, cwd, label):
    outcome = _run_bounded(args, cwd)
    if outcome["reason"] or outcome["exit_code"] != 0 or outcome["cleanup_unconfirmed"]:
        raise RuntimeError(f"{label} failed: {outcome}")


def _validate_sdist(payload, expected):
    """Reject missing, changed, duplicate or unexpected regular members."""
    seen = set()
    with tarfile.open(fileobj=io.BytesIO(payload), mode="r:gz") as archive:
        root = None
        for item in archive.getmembers():
            if item.isdir():
                continue
            if not item.isfile() or "/" not in item.name:
                raise ValueError("unexpected sdist entry")
            prefix, name = item.name.split("/", 1)
            if root is None:
                root = prefix
            if prefix != root or name in seen:
                raise ValueError("duplicate or inconsistent sdist member")
            seen.add(name)
            if name in expected:
                if archive.extractfile(item).read() != expected[name]:
                    raise ValueError(f"sdist member mismatch: {name}")
            elif not re.fullmatch(r"(?:PKG-INFO|setup\.cfg|agent_video_studio\.egg-info/(?:PKG-INFO|SOURCES\.txt|dependency_links\.txt|entry_points\.txt|requires\.txt|top_level\.txt))", name):
                raise ValueError(f"unexpected sdist member: {name}")
    missing = set(expected) - seen
    if missing:
        raise ValueError(f"sdist missing required members: {sorted(missing)[:5]}")


def build(out):
    if os.name != "nt":
        raise RuntimeError("distribution staging unavailable: platform not verified")
    source = nt.open_root(str(ROOT))
    try:
        contents, resources = _inputs(source)
    finally:
        nt.close(source)
    with tempfile.TemporaryDirectory(prefix="video-effect-build-") as tmp:
        temporary = Path(tmp)
        stage = temporary / "source"
        stage.mkdir()
        root = nt.open_root(str(stage))
        directories, held = {}, []
        try:
            patterns = ", ".join(json.dumps("_bundled/" + p) for p in sorted(resources))
            project = contents["pyproject.toml"].decode("utf-8")
            if project.count("video_studio = [") != 1:
                raise ValueError("unexpected package data configuration")
            contents["pyproject.toml"] = project.replace("video_studio = [", "video_studio = [" + patterns + ", ", 1).encode("utf-8")
            contents["MANIFEST.in"] = "".join("include video_studio/_bundled/" + p + "\n" for p in sorted(resources)).encode("utf-8")
            for name in resources:
                contents["video_studio/_bundled/" + name] = contents[name]
            for name, data in sorted(contents.items()):
                _stage_file(root, PurePosixPath(name).parts, data, directories, held)
            (stage / "dist").mkdir()
            _run([sys.executable, "-c", 'import setuptools.build_meta as b; b.build_sdist("dist")'], stage, "sdist")
            _run([sys.executable, "-m", "pip", "wheel", "--no-cache-dir", "--no-index", "--no-deps", "--no-build-isolation", "--wheel-dir", "dist", "."], stage, "wheel")
            dist_handle = nt.open_directory(root, "dist")
            try:
                artifact_names = os.listdir(stage / "dist")
                wheels = [n for n in artifact_names if re.fullmatch(r"agent_video_studio-[A-Za-z0-9_.+-]+\.whl", n)]
                sdists = [n for n in artifact_names if re.fullmatch(r"agent_video_studio-[A-Za-z0-9_.+-]+\.tar\.gz", n)]
                if len(wheels) != 1 or len(sdists) != 1 or len(artifact_names) != 2:
                    raise ValueError("unexpected distribution output inventory")
                artifacts = {}
                for name in (sdists[0], wheels[0]):
                    handle = nt.open_file(dist_handle, name)
                    try:
                        artifacts[name] = nt.read_all(handle, limit=128 * 1024 * 1024)
                    finally:
                        nt.close(handle)
            finally:
                nt.close(dist_handle)
            with zipfile.ZipFile(io.BytesIO(artifacts[wheels[0]])) as archive:
                names = archive.namelist()
                expected = {name: data for name, data in contents.items() if name.startswith("video_studio/")}
                if len(set(names)) != len(names):
                    raise ValueError("duplicate wheel member")
                for name, data in expected.items():
                    if name not in names or archive.read(name) != data:
                        raise ValueError(f"wheel member mismatch: {name}")
                for name in names:
                    if name in expected:
                        continue
                    if not re.fullmatch(r"agent_video_studio-[^/]+\.dist-info/(?:METADATA|WHEEL|RECORD|entry_points\.txt|top_level\.txt|licenses/(?:LICENSE|LICENSE-APACHE|NOTICE))", name):
                        raise ValueError(f"unexpected wheel member: {name}")
            expected_sdist = {name: data for name, data in contents.items() if name.startswith("video_studio/") or name in {"pyproject.toml", "README.md", "LICENSE", "LICENSE-APACHE", "NOTICE", "MANIFEST.in"}}
            _validate_sdist(artifacts[sdists[0]], expected_sdist)
            # abspath preserves reparse points for open_root to reject; resolve()
            # would follow one before the native safety check.
            destination = nt.open_root(os.path.abspath(out))
            published = []
            try:
                for name, payload in artifacts.items():
                    temp_name = ".effect-build-" + __import__("uuid").uuid4().hex
                    target = nt.create_file(destination, temp_name)
                    try:
                        nt.write_all(target, payload)
                        nt.flush(target)
                        nt.rename_no_replace(target, destination, name)
                        published.append(name)
                    except BaseException:
                        nt.delete_on_close(target)
                        raise
                    finally:
                        nt.close(target)
            except BaseException as exc:
                raise RuntimeError(f"distribution failed; already published: {published}") from exc
            finally:
                nt.close(destination)
            return published
        finally:
            for handle in reversed(held):
                nt.close(handle)
            for handle in reversed(list(directories.values())):
                nt.close(handle)
            nt.close(root)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True, help="existing local output directory; never overwrites")
    args = parser.parse_args()
    try:
        print(json.dumps(build(args.out), ensure_ascii=False))
        return 0
    except (ValueError, OSError, RuntimeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
