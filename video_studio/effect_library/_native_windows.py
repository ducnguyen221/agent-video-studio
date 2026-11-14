"""Windows handle-relative primitives for capture, load and materialize (called from catalog.py)."""
import ctypes
import os
import re
import unicodedata

MAX_METADATA_BYTES = 1024 * 1024
MAX_RECORD_BYTES = 90 * 1024 * 1024
MAX_BUNDLE_BYTES = 64 * 1024 * 1024


def _bundle_identity(assets):
    """Identify a bundle by all normalized relative paths and their hashes."""
    import hashlib
    import json
    import unicodedata
    canonical = sorted((unicodedata.normalize("NFC", item["path"]).casefold(), item["sha256"]) for item in assets)
    return hashlib.sha256(json.dumps(canonical, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest()


def _reference_key(url):
    """Fold ASCII scheme and host case without altering URL delimiters or zone IDs."""
    match = re.fullmatch(r"([A-Za-z][A-Za-z0-9+.-]*://)([^/?#]*)(.*)", url, re.DOTALL)
    if not match:
        return url
    scheme, authority, remainder = match.groups()
    userinfo, separator, hostport = authority.rpartition("@")
    if not separator:
        hostport = authority
    ascii_fold = str.maketrans("ABCDEFGHIJKLMNOPQRSTUVWXYZ", "abcdefghijklmnopqrstuvwxyz")
    if hostport.startswith("[") and "]" in hostport:
        end = hostport.index("]")
        host, suffix = hostport[:end], hostport[end:]
        zone = host.find("%")
        hostport = ((host if zone < 0 else host[:zone]).translate(ascii_fold)
                    + ("" if zone < 0 else host[zone:]) + suffix.translate(ascii_fold))
    else:
        hostport = hostport.translate(ascii_fold)
    return scheme.translate(ascii_fold) + (userinfo + separator if separator else "") + hostport + remainder

if os.name == "nt":
    from ctypes import wintypes

    class _UnicodeString(ctypes.Structure):
        _fields_ = [("length", wintypes.USHORT), ("maximum", wintypes.USHORT), ("buffer", wintypes.LPWSTR)]

    class _Attributes(ctypes.Structure):
        _fields_ = [("length", wintypes.ULONG), ("root", wintypes.HANDLE),
                    ("name", ctypes.POINTER(_UnicodeString)), ("attributes", wintypes.ULONG),
                    ("security", ctypes.c_void_p), ("quality", ctypes.c_void_p)]

    class _IoStatus(ctypes.Structure):
        _fields_ = [("status", ctypes.c_void_p), ("information", ctypes.c_size_t)]

    class _AttributeTag(ctypes.Structure):
        _fields_ = [("attributes", wintypes.DWORD), ("tag", wintypes.DWORD)]

    class _Rename(ctypes.Structure):
        _fields_ = [("replace", ctypes.c_ubyte), ("root", wintypes.HANDLE),
                    ("length", wintypes.ULONG), ("name", wintypes.WCHAR * 256)]

    _nt = ctypes.WinDLL("ntdll")
    _kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    _nt.NtCreateFile.argtypes = [ctypes.POINTER(wintypes.HANDLE), wintypes.ULONG, ctypes.POINTER(_Attributes),
                                  ctypes.POINTER(_IoStatus), ctypes.c_void_p, wintypes.ULONG, wintypes.ULONG,
                                  wintypes.ULONG, wintypes.ULONG, ctypes.c_void_p, wintypes.ULONG]
    _nt.NtCreateFile.restype = ctypes.c_long
    _nt.NtSetInformationFile.argtypes = [wintypes.HANDLE, ctypes.POINTER(_IoStatus), ctypes.c_void_p,
                                          wintypes.ULONG, wintypes.ULONG]
    _nt.NtSetInformationFile.restype = ctypes.c_long
    _kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    _kernel.GetFileInformationByHandleEx.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
    _kernel.GetFileInformationByHandleEx.restype = wintypes.BOOL


class _LegacyRecord(Exception):
    """A plain legacy manifest, handled by the legacy reader."""


class PublishedButCloseFailed(OSError):
    """The publish succeeded, but closing a native handle failed."""


def _check(status):
    if status < 0:
        raise OSError(f"NTSTATUS 0x{status & 0xffffffff:08x}")


def _component(name):
    if not isinstance(name, str) or not name or name in (".", "..") or any(x in name for x in "\\/:\x00"):
        raise ValueError("expected a single relative component")
    if (any(ord(ch) < 32 or ch in '<>"|?*' for ch in name) or name.endswith((' ', '.')) or
            re.fullmatch(r'(?i)(con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?', name)):
        raise ValueError("invalid Windows component")
    if len(name.encode("utf-16-le")) > 510:
        raise ValueError("name too long")


def _open(root, name, access, disposition, options, share=7):
    buffer = ctypes.create_unicode_buffer(name)
    length = len(name.encode("utf-16-le"))
    if length > 65532:
        raise ValueError("name too long")
    text = _UnicodeString(length, length, ctypes.cast(buffer, wintypes.LPWSTR))
    attrs = _Attributes(ctypes.sizeof(_Attributes), root, ctypes.pointer(text), 0x1040, None, None)
    io = _IoStatus()
    handle = wintypes.HANDLE()
    status = _nt.NtCreateFile(ctypes.byref(handle), access | 0x80, ctypes.byref(attrs), ctypes.byref(io),
                              None, 0x80, share, disposition, options | (0 if options & 1 else 0x00400000), None, 0)
    _check(status)
    try:
        attributes = _AttributeTag()
        if not _kernel.GetFileInformationByHandleEx(handle, 9, ctypes.byref(attributes), ctypes.sizeof(attributes)):
            raise ctypes.WinError(ctypes.get_last_error())
        if attributes.attributes & (0x1000 | 0x40000 | 0x400000):
            raise OSError("offline or recall-on-access item is prohibited")
    except BaseException:
        _kernel.CloseHandle(handle)
        raise
    return handle


def open_root(path):
    """Open one absolute directory without following filesystem reparse points."""
    if os.name != "nt":
        raise OSError("Windows native API unavailable")
    path = os.fspath(path)
    if not os.path.isabs(path) or not os.path.splitdrive(path)[0] or path.startswith("\\\\"):
        raise ValueError("expected a local absolute Windows path")
    return _open(None, "\\??\\" + path, 0x00100003, 1, 0x21, share=3)


def create_file(root, name):
    _component(name)
    return _open(root, name, 0x00110102, 2, 0x60, share=3)


def open_directory(root, name):
    _component(name)
    return _open(root, name, 0x00100003, 1, 0x21, share=3)


def rename_no_replace(handle, destination_root, name):
    _component(name)
    entry = _Rename()
    entry.root = destination_root
    entry.name = name
    entry.length = len(name.encode("utf-16-le"))
    io = _IoStatus()
    status = _nt.NtSetInformationFile(handle, ctypes.byref(io), ctypes.byref(entry),
                                       _Rename.name.offset + entry.length, 10)
    _check(status)


def delete_on_close(handle):
    io = _IoStatus()
    delete = ctypes.c_ubyte(1)
    status = _nt.NtSetInformationFile(handle, ctypes.byref(io), ctypes.byref(delete), 1, 13)
    _check(status)


def close(handle):
    if not _kernel.CloseHandle(handle):
        raise ctypes.WinError(ctypes.get_last_error())


def open_file(root, name):
    _component(name)
    return _open(root, name, 0x00100001, 1, 0x60, share=1)


def read_all(handle, limit=64 * 1024 * 1024):
    if os.name != "nt":
        raise OSError("Windows native API unavailable")
    _kernel.ReadFile.argtypes = [wintypes.HANDLE, ctypes.c_void_p, wintypes.DWORD,
                                  ctypes.POINTER(wintypes.DWORD), ctypes.c_void_p]
    _kernel.ReadFile.restype = wintypes.BOOL
    chunks = []
    size = 0
    while True:
        buffer = ctypes.create_string_buffer(65536)
        count = wintypes.DWORD()
        if not _kernel.ReadFile(handle, buffer, len(buffer), ctypes.byref(count), None):
            raise ctypes.WinError(ctypes.get_last_error())
        if not count.value:
            return b"".join(chunks)
        size += count.value
        if size > limit:
            raise ValueError("asset exceeds size limit")
        chunks.append(buffer.raw[:count.value])


def write_all(handle, payload):
    if os.name != "nt":
        raise OSError("Windows native API unavailable")
    _kernel.WriteFile.argtypes = [wintypes.HANDLE, ctypes.c_void_p, wintypes.DWORD,
                                   ctypes.POINTER(wintypes.DWORD), ctypes.c_void_p]
    _kernel.WriteFile.restype = wintypes.BOOL
    for offset in range(0, len(payload), 65536):
        part = payload[offset:offset + 65536]
        buf = ctypes.create_string_buffer(part)
        written = wintypes.DWORD()
        if not _kernel.WriteFile(handle, buf, len(part), ctypes.byref(written), None):
            raise ctypes.WinError(ctypes.get_last_error())
        if written.value != len(part):
            raise OSError("short write")


def flush(handle):
    _kernel.FlushFileBuffers.argtypes = [wintypes.HANDLE]
    _kernel.FlushFileBuffers.restype = wintypes.BOOL
    if not _kernel.FlushFileBuffers(handle):
        raise ctypes.WinError(ctypes.get_last_error())


def _verify_repo_assets(root, assets, handles):
    """Verify bytes while appending pinned handles for the caller to close."""
    import hashlib
    from .catalog import _relative
    opened = []
    for asset in assets:
        parent = root
        parts = _relative(asset["path"]).parts
        for part in parts[:-1]:
            parent = open_directory(parent, part)
            handles.append(parent)
        handle = open_file(parent, parts[-1])
        handles.append(handle)
        opened.append((asset, handle))
    total = 0
    for asset, handle in opened:
        payload = read_all(handle, limit=MAX_BUNDLE_BYTES - total)
        total += len(payload)
        if hashlib.sha256(payload).hexdigest() != asset["sha256"]:
            raise ValueError("repo asset hash mismatch")


def verify_repo_bundle(root, record, handles):
    """Verify a validated bundle and return its canonical content identity."""
    from .catalog import validate_entry

    validate_entry(record)
    assets = record.get("assets")
    if not assets:
        raise ValueError("repo bundle requires assets")
    _verify_repo_assets(root, assets, handles)
    return _bundle_identity(assets)


def capture_experiment(project, entries, manifest):
    """Experimental single-file station format; caller supplies existing roots explicitly."""
    import base64
    import hashlib
    import json
    import uuid
    from .catalog import _relative, _validate_metadata_entry, validate_entry
    from .search import _strict_json_loads

    # Freeze caller-owned mutable metadata before validating or reading files.
    manifest = _strict_json_loads(json.dumps(manifest, ensure_ascii=False, allow_nan=False))
    validate_entry(manifest)
    bundle = manifest.get("assets")
    metadata_only = manifest.get("asset") is None and bundle is None
    if metadata_only:
        _validate_metadata_entry(manifest)
        record = {"format": "ve-metadata-v1", "entry": manifest}
        identity = (manifest["source"] if manifest["kind"] == "reference" else manifest["prompt_text"]).encode("utf-8")
        content_hash = hashlib.sha256(identity).hexdigest()
    elif bundle is not None:
        # Hold all source handles open until the entire snapshot is read. Each
        # open denies writers/deletes and never follows a reparse point.
        from contextlib import ExitStack
        file_handles = []
        with ExitStack() as handles:
            root = open_root(project)
            handles.callback(close, root)
            for item in bundle:
                parent = root
                parts = _relative(item["path"]).parts
                for part in parts[:-1]:
                    parent = open_directory(parent, part)
                    handles.callback(close, parent)
                file_handle = open_file(parent, parts[-1])
                handles.callback(close, file_handle)
                file_handles.append(file_handle)
            encoded = {}
            total = 0
            for item, handle in zip(bundle, file_handles):
                data = read_all(handle, limit=MAX_BUNDLE_BYTES)
                total += len(data)
                if total > MAX_BUNDLE_BYTES:
                    raise ValueError("bundle exceeds size limit")
                if hashlib.sha256(data).hexdigest() != item["sha256"]:
                    raise ValueError("bundle asset hash mismatch")
                encoded[item["path"]] = base64.b64encode(data).decode("ascii")
        content_hash = _bundle_identity(bundle)
        record = {"format": "ve-bundle-v2", "entry": manifest, "assets_base64": encoded}
    else:
        if manifest["rights"] not in {"owned", "licensed"}:
            raise ValueError("capture requires an owned or licensed file")
        project_root = open_root(project)
        roots = [project_root]
        try:
            parts = _relative(manifest["asset"]["path"]).parts
            for part in parts[:-1]:
                roots.append(open_directory(roots[-1], part))
            source = open_file(roots[-1], parts[-1])
            try:
                data = read_all(source)
            finally:
                close(source)
        finally:
            for handle in reversed(roots):
                close(handle)
        content_hash = hashlib.sha256(data).hexdigest()
        if content_hash != manifest["asset"]["sha256"]:
            raise ValueError("asset hash mismatch")
        record = {"format": "ve-bundle-v1", "entry": manifest, "asset_base64": base64.b64encode(data).decode("ascii")}
    payload = json.dumps(record, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    if metadata_only and len(payload) > MAX_METADATA_BYTES:
        raise ValueError("metadata exceeds size limit")
    if len(payload) > MAX_RECORD_BYTES:
        raise ValueError("entry exceeds size limit")
    from .resources import resource_root
    from .distilled_sources import load_distilled
    # Search merges these records into the same ID namespace. Refuse to
    # publish when the canonical sources cannot be read or the ID is taken.
    if any(row["id"].casefold() == manifest["id"].casefold()
           for row in load_distilled(resource_root())):
        raise ValueError("entry ID already exists in distilled references")
    repo_handles = []
    published = False
    try:
        repo_handles.append(open_root(resource_root()))
        for part in ("skills", "video-theme-library", "assets", "effect-library"):
            repo_handles.append(open_directory(repo_handles[-1], part))
        index_handle = open_file(repo_handles[-1], "entries.json")
        repo_handles.append(index_handle)
        repo_records = _strict_json_loads(read_all(index_handle, limit=4 * 1024 * 1024).decode("utf-8-sig"))
        if not isinstance(repo_records, list):
            raise ValueError("invalid repo catalog")
        for entry in repo_records:
            validate_entry(entry)
            if entry.get("assets") is not None:
                identity = verify_repo_bundle(repo_handles[0], entry, repo_handles)
                if bundle is not None and identity == content_hash:
                    raise ValueError("bundle already exists in repo catalog")
            if entry["id"].casefold() == manifest["id"].casefold():
                raise ValueError("entry ID already exists in repo catalog")
            if unicodedata.normalize("NFC", entry["name"]).casefold() == unicodedata.normalize("NFC", manifest["name"]).casefold():
                raise ValueError("entry name already exists in repo catalog")
            if not metadata_only and bundle is None and entry.get("asset") and entry["asset"]["sha256"] == content_hash:
                raise ValueError("asset hash already exists in repo catalog")
            if metadata_only and entry["kind"] == manifest["kind"] and (
                    _reference_key(entry["source"]) == _reference_key(manifest["source"]) if manifest["kind"] == "reference"
                    else entry.get("prompt_text") == manifest["prompt_text"]):
                raise ValueError("metadata source already exists in repo catalog")
        if metadata_only and manifest["kind"] == "reference":
            pm_root = repo_handles[0]
            for part in ("skills", "video-theme-library", "assets", "prompt-motion"):
                pm_root = open_directory(pm_root, part)
                repo_handles.append(pm_root)
            pm_index = open_file(pm_root, "index.json")
            repo_handles.append(pm_index)
            pm_data = _strict_json_loads(read_all(pm_index, limit=10 * 1024 * 1024).decode("utf-8-sig"))
            if not isinstance(pm_data, dict) or not isinstance(pm_data.get("entries"), list):
                raise ValueError("invalid Prompt Motion catalog")
            for pm_entry in pm_data["entries"]:
                if not isinstance(pm_entry, dict) or not isinstance(pm_entry.get("source_facts"), dict):
                    raise ValueError("invalid Prompt Motion entry")
                source_url = pm_entry["source_facts"].get("url")
                if not isinstance(source_url, str) or not source_url:
                    raise ValueError("invalid Prompt Motion source URL")
                if _reference_key(source_url) == _reference_key(manifest["source"]):
                    raise ValueError("reference source already exists in Prompt Motion catalog")
        root = open_root(entries)
        staged = None
        lock = None
        published = False
        try:
            lock = create_file(root, ".capture.lock")
            delete_on_close(lock)
            existing = {name.casefold() for name in os.listdir(entries)}
            if manifest["id"].casefold() in existing:
                raise ValueError("entry ID already exists in station")
            for current in search_experiment(entries):
                if unicodedata.normalize("NFC", current["name"]).casefold() == unicodedata.normalize("NFC", manifest["name"]).casefold():
                    raise ValueError("entry name already exists in station")
                if bundle is not None and current.get("assets") and _bundle_identity(current["assets"]) == content_hash:
                    raise ValueError("bundle already exists in station")
                if not metadata_only and bundle is None and current.get("asset") and current["asset"]["sha256"] == content_hash:
                    raise ValueError("asset hash already exists in station")
                if metadata_only and current["kind"] == manifest["kind"] and (
                        _reference_key(current["source"]) == _reference_key(manifest["source"]) if manifest["kind"] == "reference"
                        else current.get("prompt_text") == manifest["prompt_text"]):
                    raise ValueError("metadata source already exists in station")
            stage_name = "stage-" + uuid.uuid4().hex
            staged = create_directory(root, stage_name)
            file_handle = None
            marker_handle = None
            try:
                marker_handle = create_file(staged, "stage.json")
                marker = json.dumps({"format": "ve-stage-v1", "stage": stage_name,
                                     "id": manifest["id"], "sha256": content_hash},
                                    separators=(",", ":")).encode("utf-8")
                write_all(marker_handle, marker)
                flush(marker_handle)
                close(marker_handle)
                marker_handle = None
                file_handle = create_file(staged, "entry.json")
                write_all(file_handle, payload)
                flush(file_handle)
                close(file_handle)
                file_handle = None
                rename_no_replace(staged, root, manifest["id"])
                published = True
            except BaseException as original:
                try:
                    if marker_handle is not None:
                        delete_on_close(marker_handle)
                        close(marker_handle)
                        marker_handle = None
                    else:
                        try:
                            marker_handle = _open(staged, "stage.json", 0x00110000, 1, 0x60)
                        except OSError as exc:
                            if "0xc0000034" not in str(exc):
                                raise
                        else:
                            delete_on_close(marker_handle)
                            close(marker_handle)
                            marker_handle = None
                    if file_handle is not None:
                        delete_on_close(file_handle)
                        close(file_handle)
                    else:
                        try:
                            file_handle = _open(staged, "entry.json", 0x00110000, 1, 0x60)
                        except OSError as exc:
                            if "0xc0000034" not in str(exc):
                                raise
                        else:
                            delete_on_close(file_handle)
                            close(file_handle)
                    delete_on_close(staged)
                except BaseException as rollback:
                    if marker_handle is not None:
                        try:
                            close(marker_handle)
                        except OSError:
                            pass
                    if file_handle is not None:
                        try:
                            close(file_handle)
                        except OSError:
                            pass
                    raise OSError(f"capture failed; stage cleanup also failed: {rollback}") from original
                raise
            finally:
                try:
                    close(staged)
                except OSError as exc:
                    if published:
                        raise PublishedButCloseFailed("entry published; closing entry handle failed") from exc
                    raise
        finally:
            try:
                if lock is not None:
                    try:
                        close(lock)
                    except OSError as exc:
                        if published:
                            raise PublishedButCloseFailed("entry published; closing lock handle failed") from exc
                        raise
            finally:
                try:
                    close(root)
                except OSError as exc:
                    if published:
                        raise PublishedButCloseFailed("entry published; closing directory handle failed") from exc
                    raise
    finally:
        close_failure = None
        for handle in reversed(repo_handles):
            try:
                close(handle)
            except OSError as exc:
                close_failure = exc
        if close_failure:
            if published:
                raise PublishedButCloseFailed("entry published; closing catalog handle failed") from close_failure
            raise close_failure
    return manifest["id"]


def _decode_asset_base64(value):
    """Decode a JSON string; malformed types and encodings are catalog errors."""
    import base64
    import binascii

    if not isinstance(value, str):
        raise ValueError("invalid asset encoding")
    try:
        return base64.b64decode(value, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise ValueError("invalid asset encoding") from exc


def _load_record(root, identifier):
    import hashlib
    import json
    from .catalog import _validate_metadata_entry, validate_entry
    from .search import _strict_json_loads

    _component(identifier)
    directory = open_directory(root, identifier)
    try:
        handle = open_file(directory, "entry.json")
        try:
            blob = read_all(handle, limit=90 * 1024 * 1024)
        finally:
            close(handle)
    finally:
        close(directory)
    record = _strict_json_loads(blob.decode("utf-8"))
    if isinstance(record, dict) and "format" not in record and "id" in record and "entry" not in record:
        raise _LegacyRecord()
    if isinstance(record, dict) and record.get("format") == "ve-metadata-v1":
        entry = _validate_metadata_entry(record["entry"])
        if entry["id"] != identifier:
            raise ValueError("entry ID mismatch")
        return entry, None
    if isinstance(record, dict) and record.get("format") == "ve-bundle-v2":
        entry = validate_entry(record["entry"])
        if entry["id"] != identifier or not entry.get("assets"):
            raise ValueError("entry ID or bundle assets mismatch")
        values = record.get("assets_base64")
        expected = {item["path"] for item in entry["assets"]}
        if not isinstance(values, dict) or set(values) != expected:
            raise ValueError("bundle payload paths mismatch")
        decoded = {}
        total = 0
        for item in entry["assets"]:
            try:
                data = _decode_asset_base64(values[item["path"]])
            except ValueError as exc:
                raise ValueError("invalid bundle asset encoding") from exc
            total += len(data)
            if total > MAX_BUNDLE_BYTES or hashlib.sha256(data).hexdigest() != item["sha256"]:
                raise ValueError("bundle asset size or hash mismatch")
            decoded[item["path"]] = data
        return entry, decoded
    if not isinstance(record, dict) or record.get("format") != "ve-bundle-v1":
        raise ValueError("unknown or missing entry format")
    entry = validate_entry(record["entry"])
    if entry["id"] != identifier or not entry.get("asset"):
        raise ValueError("entry ID or asset mismatch")
    data = _decode_asset_base64(record["asset_base64"])
    if hashlib.sha256(data).hexdigest() != entry["asset"]["sha256"]:
        raise ValueError("asset hash mismatch")
    return entry, data


def load_experiment(entries, identifier):
    root = open_root(entries)
    try:
        return _load_record(root, identifier)
    finally:
        close(root)


def _load_legacy(root, identifier):
    import hashlib
    import json
    from .catalog import _relative, validate_entry
    from .search import _strict_json_loads

    handles = [open_directory(root, identifier)]
    try:
        f = open_file(handles[-1], "entry.json")
        try:
            entry = validate_entry(_strict_json_loads(read_all(f, limit=4 * 1024 * 1024).decode("utf-8")))
        finally:
            close(f)
        if entry["id"] != identifier:
            raise ValueError("station entry ID/path mismatch")
        if entry.get("assets") is not None:
            raise ValueError("multi-file bundles require a versioned record")
        if entry.get("asset") is not None:
            parts = _relative(entry["asset"]["path"]).parts
            for part in parts[:-1]:
                handles.append(open_directory(handles[-1], part))
            f = open_file(handles[-1], parts[-1])
            try:
                data = read_all(f)
            finally:
                close(f)
            if hashlib.sha256(data).hexdigest() != entry["asset"]["sha256"]:
                raise ValueError("station asset hash mismatch")
        return entry
    finally:
        for handle in reversed(handles):
            close(handle)


def search_experiment(entries, query=""):
    """Search published experiment records; stages remain quarantined and untouched."""
    from .search import _fold
    root = open_root(entries)
    try:
        names = os.listdir(entries)
        records = []
        for name in sorted(names):
            if name.startswith("stage-") or name == ".capture.lock":
                continue
            if not name.startswith("VE-"):
                raise ValueError(f"unexpected station entry: {name}")
            identifier = name
            try:
                entry, _ = _load_record(root, identifier)
            except _LegacyRecord:
                entry = _load_legacy(root, identifier)
            if _fold(query) in _fold(entry["name"] + " " + " ".join(entry["tags"])):
                records.append(entry)
        return records
    finally:
        close(root)


def materialize_experiment(entries, identifier, project, name):
    """Copy one verified experimental asset to an existing project without replacement."""
    _component(name)
    entry, data = load_experiment(entries, identifier)
    if data is None:
        raise ValueError("metadata entries cannot be materialized as files")
    if isinstance(data, dict):
        raise ValueError("multi-file bundle materialization is not available")
    if entry["rights"] not in {"owned", "licensed"}:
        raise ValueError("materialization requires owned or licensed rights")
    return _publish_asset(data, project, name)


def materialize_repo_experiment(repo_root, identifier, project, name):
    """Read a catalog entry and its asset through a pinned repository root."""
    import hashlib
    import json
    from contextlib import ExitStack
    from .catalog import _relative, validate_entry
    from .search import _strict_json_loads

    _component(name)
    if not isinstance(identifier, str):
        raise ValueError("invalid repository entry ID")
    with ExitStack() as handles:
        root = open_root(os.fspath(repo_root))
        handles.callback(close, root)
        directory = root
        for part in ("skills", "video-theme-library", "assets", "effect-library"):
            directory = open_directory(directory, part)
            handles.callback(close, directory)
        index = open_file(directory, "entries.json")
        handles.callback(close, index)
        records = _strict_json_loads(read_all(index, limit=4 * 1024 * 1024).decode("utf-8-sig"))
        if not isinstance(records, list):
            raise ValueError("invalid repo catalog")
        seen = set()
        selected = None
        for entry in records:
            validate_entry(entry)
            key = entry["id"].casefold()
            if key in seen:
                raise ValueError("duplicate repo entry ID")
            seen.add(key)
            if entry["id"] == identifier:
                selected = entry
        if selected is None:
            raise ValueError("repository entry not found")
        if (selected["kind"] not in {"component", "preset"} or
                selected["rights"] not in {"owned", "licensed"} or
                not isinstance(selected.get("asset"), dict) or selected.get("assets") is not None):
            raise ValueError("repository entry is not a reusable single-file component or preset")
        parts = _relative(selected["asset"]["path"]).parts
        directory = root
        for part in parts[:-1]:
            directory = open_directory(directory, part)
            handles.callback(close, directory)
        source = open_file(directory, parts[-1])
        handles.callback(close, source)
        data = read_all(source)
        if hashlib.sha256(data).hexdigest() != selected["asset"]["sha256"]:
            raise ValueError("repo asset hash mismatch")
    return _publish_asset(data, project, name)


def _publish_asset(data, project, name):
    import uuid

    _component(name)
    root = open_root(project)
    published = False
    try:
        handle = create_file(root, "stage-" + uuid.uuid4().hex)
        try:
            write_all(handle, data)
            flush(handle)
            rename_no_replace(handle, root, name)
            published = True
        except BaseException as original:
            try:
                delete_on_close(handle)
            except BaseException as rollback:
                raise OSError(f"materialization failed; stage cleanup also failed: {rollback}") from original
            raise
        finally:
            try:
                close(handle)
            except OSError as exc:
                if published:
                    raise PublishedButCloseFailed("asset published; closing file handle failed") from exc
                raise
    finally:
        try:
            close(root)
        except OSError as exc:
            if published:
                raise PublishedButCloseFailed("asset published; closing directory handle failed") from exc
            raise


def create_directory(root, name):
    _component(name)
    return _open(root, name, 0x00110003, 2, 0x21, share=3)


def inspect_stages(entries):
    """Inventory quarantined stages; markers are claims, not authorization to delete."""
    import json
    root = open_root(entries)
    results = []
    try:
        for name in sorted(os.listdir(entries)):
            if not re.fullmatch(r"stage-[0-9a-f]{32}", name):
                continue
            try:
                directory = open_directory(root, name)
                try:
                    handle = open_file(directory, "stage.json")
                    try:
                        marker = json.loads(read_all(handle, limit=65536).decode("utf-8"))
                    finally:
                        close(handle)
                finally:
                    close(directory)
                if not isinstance(marker, dict) or marker.get("format") != "ve-stage-v1" or marker.get("stage") != name:
                    raise ValueError("invalid stage marker")
                if not re.fullmatch(r"VE-[a-z0-9]+(?:-[a-z0-9]+)*", str(marker.get("id", ""))) or not re.fullmatch(r"[a-f0-9]{64}", str(marker.get("sha256", ""))):
                    raise ValueError("invalid stage identity")
                results.append({"stage": name, "status": "marker_present_unverified", "id": marker["id"], "sha256": marker["sha256"]})
            except (OSError, ValueError, UnicodeError) as exc:
                results.append({"stage": name, "status": "unverified", "error": str(exc)})
        return results
    finally:
        close(root)
