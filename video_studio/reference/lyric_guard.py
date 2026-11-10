"""Kiểm tài sản khai báo, không chứng minh phụ thuộc HTML/JS hay chặn race.

Caller chỉ được dùng kết quả cho renderer có hợp đồng đóng tự kiểm soát; hàm này không
quan sát renderer và không tự render hoặc ghép âm thanh.
"""
import os
from pathlib import Path
import re
import stat

from ..contract import ContractError
from . import gate


def _files(root: Path, *, required: bool) -> list[Path]:
    """Enumerate regular files; directory, link and traversal errors fail closed."""
    try:
        st = root.lstat()
    except FileNotFoundError:
        if not required:
            return []
        raise ContractError(f"thiếu thư mục {root.name}") from None
    if gate._is_link(str(root)) or not stat.S_ISDIR(st.st_mode):
        raise ContractError(f"thư mục {root.name} không hợp lệ")

    def fail(exc: OSError) -> None:
        raise exc

    found = []
    for parent, dirs, files in os.walk(str(root), followlinks=False, onerror=fail):
        for name in (*dirs, *files):
            path = Path(parent) / name
            mode = path.lstat().st_mode
            if gate._is_link(str(path)):
                raise ContractError("không cho phép link trong cây tài sản hoặc mẫu")
            if name in dirs:
                if not stat.S_ISDIR(mode):
                    raise ContractError("mục con không phải thư mục")
            elif not stat.S_ISREG(mode):
                raise ContractError("tài sản không phải tệp thường")
            else:
                found.append(path)
    return found


def _paths(manifest: object) -> tuple[str, tuple[str, ...]]:
    if not isinstance(manifest, dict) or set(manifest) != {"audio", "assets"}:
        raise ContractError("manifest chỉ nhận audio và assets")
    audio, assets = manifest["audio"], manifest["assets"]
    if not isinstance(audio, str) or not isinstance(assets, list):
        raise ContractError("audio phải là đường dẫn; assets phải là danh sách")
    paths = [audio, *assets]
    for path in paths:
        if not isinstance(path, str):
            raise ContractError("đường tài sản phải là chuỗi")
        parts = path.split("/")
        if (parts[:2] != ["composition", "media"] or len(parts) < 3
                or any(part in ("", ".", "..") for part in parts)
                or any("\\" in part or ":" in part or "\x00" in part for part in parts)):
            raise ContractError("tài sản phải nằm trong composition/media")
    if len(paths) != len(set(paths)):
        raise ContractError("khai trùng đường tài sản")
    return audio, tuple(sorted(assets))


def prepare(project: str | Path, manifest: object) -> dict:
    """Kiểm hồ sơ và băm tập đã khai tại thời điểm gọi, không tạo file hay render."""
    root = Path(project).absolute()
    audio, assets = _paths(manifest)
    paths = (audio, *assets)
    try:
        if gate._is_link(str(root)):
            raise ContractError("project không được là link")
        result = gate.audit_assets(str(root), str(root / "composition" / "media"))
        if not result["ok"] or result["checked"] == 0:
            raise ContractError("audit tài sản không đạt hoặc không kiểm tệp nào")
        prov = gate.load_provenance(str(root))
        declared = [entry["path"] for entry in prov.get("assets", [])]
        if len(declared) != len(paths) or set(declared) != set(paths):
            raise ContractError("manifest và hồ sơ tài sản không khớp")
        actual = {p.relative_to(root).as_posix() for p in _files(root / "composition" / "media", required=True)}
        if actual != set(paths):
            raise ContractError("tập file thực tế không khớp manifest")
        hashes = {path: gate.sha256_file(str(root / Path(path))) for path in paths}
        sources = _files(root / "source", required=True) + _files(root / "evidence", required=False)
        source_hashes = {gate.sha256_file(str(path)) for path in sources}
        recorded_hashes = set()
        for section in ("reference", "fetch"):
            value = prov.get(section)
            digest = value.get("sha256") if isinstance(value, dict) else None
            if digest is not None:
                if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", digest):
                    raise ContractError("hash nguồn không hợp lệ")
                recorded_hashes.add(digest.lower())
        if not recorded_hashes:
            raise ContractError("chưa có hash video mẫu trong hồ sơ để đối chiếu")
        source_hashes.update(recorded_hashes)
        if source_hashes.intersection(hashes.values()):
            raise ContractError("tài sản trùng byte với nguồn")
        provenance_hash = gate.sha256_file(str(root / gate.PROVENANCE_FILE))
    except OSError as exc:
        raise ContractError(f"không thể kiểm tài sản: {exc}") from None
    return {"scope": "declared_only", "audio": audio, "assets": list(assets), "sha256": hashes,
            "provenance_sha256": provenance_hash}


def verify_snapshot(project: str | Path, manifest: object, snapshot: object) -> None:
    """Kiểm lại; không ngăn thay đổi ngay sau khi hàm trả về."""
    if prepare(project, manifest) != snapshot:
        raise ContractError("tài sản hoặc hồ sơ đã đổi sau khi kiểm")
