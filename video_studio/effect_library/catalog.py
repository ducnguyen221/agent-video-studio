"""Validate and capture one self-contained effect into an explicitly chosen station."""
from pathlib import Path, PurePosixPath, PureWindowsPath
import json
import re
import os
import unicodedata
from urllib.parse import urlsplit

from video_studio.contract import ContractError

CHECKS = ("static_check", "preview", "render", "audio", "ratio_test", "reuse_evidence")
KINDS = {"reference", "prompt", "preset", "component", "template", "media_asset"}
MATURITIES = {"reference_only", "candidate", "implemented", "verified"}


def validate_entry(entry):
    if not isinstance(entry, dict):
        raise ContractError("Entry must be an object")
    try:
        json.dumps(entry, allow_nan=False)
    except (TypeError, ValueError, RecursionError) as exc:
        raise ContractError("Entry must contain valid finite JSON metadata") from exc
    for field in ("id", "name", "kind", "maturity", "rights", "source", "runtime"):
        if not isinstance(entry.get(field), str) or not entry[field].strip():
            raise ContractError(f"Missing {field}")
    if not re.fullmatch(r"VE-[a-z0-9]+(?:-[a-z0-9]+)*", entry["id"]):
        raise ContractError("Invalid VE ID")
    if entry["kind"] not in KINDS or entry["maturity"] not in MATURITIES:
        raise ContractError("Invalid kind or maturity")
    source = entry["source"]
    if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", source):
        try:
            parsed = urlsplit(source)
            if (parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname or
                    parsed.username is not None or parsed.password is not None or
                    "\\" in source or
                    any(ch.isspace() or ord(ch) < 32 for ch in source)):
                raise ValueError("Invalid URL")
            _ = parsed.port
        except ValueError as exc:
            raise ContractError("Unsupported or invalid source URL") from exc
    if entry["rights"] not in {"owned", "licensed", "unknown"}:
        raise ContractError("Invalid rights")
    if entry["rights"] == "licensed":
        license_info = entry.get("license")
        if not isinstance(license_info, dict) or any(not isinstance(license_info.get(k), str) or not license_info[k].strip() for k in ("id", "source", "terms")):
            raise ContractError("Licensed entries require license id, source, and terms")
    for field in ("tags", "roles", "techniques", "ratios"):
        if not isinstance(entry.get(field), list) or not all(isinstance(x, str) and x for x in entry[field]):
            raise ContractError(f"Invalid {field}")
    checks = entry.get("checks")
    if not isinstance(checks, dict) or any(checks.get(k) not in ("not_run", "pass", "fail") for k in CHECKS):
        raise ContractError("Missing or invalid checks")
    evidence = entry.get("evidence", {})
    if not isinstance(evidence, dict) or any(checks[k] == "pass" and (not isinstance(evidence.get(k), str) or not evidence[k].strip()) for k in CHECKS):
        raise ContractError("Passing checks require evidence")
    if entry["maturity"] == "verified" and (checks["render"] != "pass" or checks["reuse_evidence"] != "pass"):
        raise ContractError("verified needs render and reuse evidence")
    asset = entry.get("asset")
    if "assets" in entry:
        if asset is not None or entry["kind"] in {"reference", "prompt"}:
            raise ContractError("Bundle cannot contain a single asset or metadata-only kind")
        assets = entry["assets"]
        if not isinstance(assets, list) or not 2 <= len(assets) <= 64:
            raise ContractError("Bundle requires between 2 and 64 assets")
        if entry["rights"] not in {"owned", "licensed"}:
            raise ContractError("Bundle requires owned or licensed rights")
        paths = set()
        for item in assets:
            if not isinstance(item, dict) or set(item) - {"path", "sha256", "rights", "license"}:
                raise ContractError("Invalid bundle asset")
            if not isinstance(item.get("path"), str) or not re.fullmatch(r"[a-f0-9]{64}", str(item.get("sha256", ""))):
                raise ContractError("Missing bundle asset path or SHA-256")
            parts = _relative(item["path"]).parts
            if "/".join(parts) != item["path"]:
                raise ContractError("Bundle path must use canonical separators")
            if len(parts) > 8:
                raise ContractError("Bundle path exceeds depth limit")
            from ._native_windows import _component
            for part in parts:
                try:
                    _component(part)
                except (ValueError, UnicodeError) as exc:
                    raise ContractError("Invalid bundle path component") from exc
            key = tuple(unicodedata.normalize("NFC", part).casefold() for part in parts)
            if any(key == previous or key[:len(previous)] == previous or previous[:len(key)] == key for previous in paths):
                raise ContractError("Conflicting bundle paths")
            paths.add(key)
            if item.get("rights") not in {"owned", "licensed"}:
                raise ContractError("Every bundle asset requires owned or licensed rights")
            if item["rights"] == "licensed":
                license_info = item.get("license")
                if not isinstance(license_info, dict) or any(not isinstance(license_info.get(k), str) or not license_info[k].strip() for k in ("id", "source", "terms")):
                    raise ContractError("Licensed bundle assets require license id, source, and terms")
        return entry
    if asset is None and entry["kind"] in {"reference", "prompt"}:
        return entry
    if not isinstance(asset, dict) or not isinstance(asset.get("path"), str) or not re.fullmatch(r"[a-f0-9]{64}", str(asset.get("sha256", ""))):
        raise ContractError("Missing asset path or SHA-256")
    _relative(asset["path"])
    return entry


def _relative(value):
    p = PurePosixPath(value)
    w = PureWindowsPath(value)
    if (not value or "\\" in value or p.is_absolute() or w.drive or
            any(x in (".", "..") for x in value.split("/")) or
            any(any(c in x for c in '<>:"|?*') or x.endswith((' ', '.')) for x in value.split('/'))):
        raise ContractError("Unsafe relative path")
    return p


def _safe_file(root, relative):
    root = Path(root)
    if root.is_symlink() or not root.is_dir():
        raise ContractError("Root must be an existing non-symlink directory")
    path = root
    for part in _relative(relative).parts:
        path = path / part
        if path.is_symlink():
            raise ContractError("Symlink in asset path")
    if not path.is_file() or not path.resolve().is_relative_to(root.resolve()):
        raise ContractError("Asset missing or outside root")
    return path


def _validate_metadata_entry(entry):
    """Validate an asset-free reference or an explicitly owned/licensed prompt."""
    validate_entry(entry)
    if entry.get("asset") is not None:
        raise ValueError("metadata entry cannot include an asset")
    if entry["kind"] == "reference":
        if entry["rights"] == "unknown":
            # Reference-only entries may not carry arbitrary unlicensed content in
            # extra JSON fields. Text fields remain user-supplied claims, not proof
            # of rights; callers must still avoid copying protected material.
            allowed = {"id", "name", "kind", "maturity", "rights", "source", "runtime", "tags",
                       "roles", "techniques", "ratios", "checks", "asset", "description",
                       "repository", "license_note", "license_url", "details"}
            if set(entry) - allowed:
                raise ValueError("unknown-rights reference contains unsupported fields")
            if set(entry["checks"]) != set(CHECKS):
                raise ValueError("unknown-rights reference has unsupported checks fields")
            for field in ("name", "source", "runtime", "description", "repository", "license_note", "license_url", "details"):
                value = entry.get(field)
                if value is not None and (not isinstance(value, str) or len(value) > 2048):
                    raise ValueError(f"invalid reference metadata field: {field}")
            for field in ("tags", "roles", "techniques", "ratios"):
                if len(entry[field]) > 128 or any(len(item) > 256 for item in entry[field]):
                    raise ValueError(f"reference metadata field exceeds limit: {field}")
        source = entry["source"]
        if "\\" in source or any(ch.isspace() or ord(ch) < 32 for ch in source):
            raise ValueError("reference requires a valid HTTP(S) source")
        parsed = urlsplit(source)
        if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
            raise ValueError("reference requires an HTTP(S) source")
        if "license_url" in entry:
            value = entry["license_url"]
            try:
                if not isinstance(value, str) or not value or "\\" in value or any(ch.isspace() or ord(ch) < 32 for ch in value):
                    raise ValueError("invalid license URL")
                license_url = urlsplit(value)
                if (license_url.scheme.lower() not in {"http", "https"} or not license_url.hostname or
                        license_url.username is not None or license_url.password is not None):
                    raise ValueError("invalid license URL")
                _ = license_url.port
            except ValueError as exc:
                raise ValueError("license_url requires a valid HTTP(S) URL") from exc
        if entry.get("prompt_text") is not None:
            raise ValueError("reference cannot include prompt content")
        if entry["maturity"] != "reference_only":
            raise ValueError("reference metadata must remain reference_only")
    elif entry["kind"] == "prompt":
        if entry["rights"] not in {"owned", "licensed"}:
            raise ValueError("prompt requires owned or licensed rights")
        if not isinstance(entry.get("prompt_text"), str) or not entry["prompt_text"].strip():
            raise ValueError("prompt requires prompt_text")
    else:
        raise ValueError("asset-free capture only supports reference or prompt")
    return entry


def capture(project, station, manifest):
    """Capture one file or metadata on Windows into an explicit station."""
    try:
        snapshot = json.loads(json.dumps(manifest, allow_nan=False, ensure_ascii=False))
    except (TypeError, ValueError, RecursionError) as exc:
        raise ContractError("Entry must contain valid finite JSON metadata") from exc
    validate_entry(snapshot)
    if os.name != "nt":
        raise ContractError("Capture unavailable: secure station writes not verified on this platform")
    from ._native_windows import capture_experiment
    return capture_experiment(project, Path(station) / "effect-library" / "entries", snapshot)


def materialize(station, identifier, project, name):
    """Materialize one captured file on Windows without replacing an existing file."""
    if os.name != "nt":
        raise ContractError("Materialization unavailable: secure writes not verified on this platform")
    from ._native_windows import materialize_experiment
    return materialize_experiment(Path(station) / "effect-library" / "entries", identifier, project, name)


def materialize_repo(identifier, project, name):
    """Materialize a single verified repository component without replacing files."""
    if os.name != "nt":
        raise ContractError("Materialization unavailable: secure writes not verified on this platform")
    from ._native_windows import materialize_repo_experiment
    from .resources import resource_root
    return materialize_repo_experiment(resource_root(), identifier, project, name)


def read_bundle(station, identifier):
    """Read a verified multi-file bundle into memory without writing a project."""
    if os.name != "nt":
        raise ContractError("Bundle reading unavailable: secure station reads not verified on this platform")
    from ._native_windows import load_experiment
    entry, data = load_experiment(Path(station) / "effect-library" / "entries", identifier)
    if not isinstance(data, dict) or entry["rights"] not in {"owned", "licensed"}:
        raise ContractError("Entry is not a readable multi-file bundle")
    return data
