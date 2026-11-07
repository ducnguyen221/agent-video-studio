"""gate.py — lõi cổng của nhóm `reference`: URL, hồ sơ nguồn, cổng tải, kiểm tài sản.

Thuần: không tiến trình con, không mạng. Mọi lỗi là `ContractError` (mã thoát 2).

Thứ tự bảy cổng của `fetch` (dừng ở cổng đầu tiên hỏng; 1–5 ở đây, 6–7 ở `fetch.py`):

    1 check_url(url)                    URL được phép tải
      |
    2 allow_url == url                  người dùng đã nói đích danh URL này
      |
    3 load_provenance(project)          hồ sơ nguồn có và hợp lệ   (bên gọi nạp `prov`)
      |
    4 rights_status == approved,        quyền được duyệt, có căn cứ; căn cứ khác
      rights_basis, rights_proof        own_content thì phải có chứng từ
      |
    5 permission.* khớp url,            phép ghi đủ chữ; reference.url (nếu có) khớp
      reference.url null/== url
      |
    6 yt-dlp có trên máy                (fetch.py, mã 3 nếu thiếu)
      |
    7 source/reference.* chưa có        (fetch.py, không ghi đè)

`assets[].path` trong hồ sơ là đường TƯƠNG ĐỐI so với thư mục project (vd `assets/hero.png`).
"""
import datetime
import hashlib
import ipaddress
import json
import os
import re
import stat
import tempfile
from urllib.parse import urlsplit

from video_studio.contract import ContractError

RIGHTS = ("approved", "rights_pending", "blocked")
BASES = ("own_content", "written_permission", "license")
ORIGINS = ("user", "generated", "template", "reference")
BUILD_ORIGINS = ("user", "generated", "template")

# Đuôi tệp video/âm thanh mà ffmpeg được mở: danh sách playlist (m3u8, ffconcat, sdp…) có thể kéo tệp khác lên.
MEDIA_EXTS = frozenset(("mp4", "m4v", "mov", "mkv", "webm", "avi", "flv", "ts", "mts", "m2ts", "mpg", "mpeg",
                        "ogv", "ogg", "wmv", "3gp", "mp3", "m4a", "aac", "wav", "flac", "opus"))

# ffmpeg chọn demuxer theo NỘI DUNG (đuôi `.mp4` vẫn có thể là danh sách/manifest kéo tệp khác lên). Chỉ nhận
# container thường (danh sách trắng): MỌI phần của `format_name` (ffprobe, cách nhau dấu phẩy) phải thuộc tập này.
PLAIN_FORMATS = frozenset(("mov", "mp4", "m4a", "3gp", "3g2", "mj2", "matroska", "webm", "avi", "flv", "mpegts",
                           "mpeg", "ogg", "asf", "mp3", "aac", "wav", "w64", "flac", "aiff"))
_QUOTE_END = r"""(?=$|\s|[.,;:!?)\]}>»"'”’…—–])"""

PROVENANCE_FILE = "provenance.json"
MAX_URL_LEN = 2048
_LAST_LABEL_NUMERIC = re.compile(r"0x[0-9a-f]*|[0-9]+")
# Danh sách chặn TƯỜNG MINH, không dựa vào `is_global`/`is_private` của `ipaddress` (bảng đó đổi theo bản Python:
# CPython 3.10.11 coi 192.0.0.8 là global, trước bản vá CVE-2024-4032). Nguồn: IANA IPv4 Special-Purpose Address
# Registry và IANA IPv6 Special-Purpose Address Registry (iana.org/assignments/iana-ipv4-special-registry,
# iana-ipv6-special-registry), cộng khối reserved/multicast. Cờ của `ipaddress` vẫn được kiểm thêm, không thay thế.
_BLOCKED_V4 = tuple(ipaddress.ip_network(n) for n in (
    "0.0.0.0/8", "10.0.0.0/8", "100.64.0.0/10", "127.0.0.0/8", "169.254.0.0/16", "172.16.0.0/12",
    "192.0.0.0/24", "192.0.2.0/24", "192.31.196.0/24", "192.52.193.0/24", "192.88.99.0/24", "192.168.0.0/16",
    "192.175.48.0/24", "198.18.0.0/15", "198.51.100.0/24", "203.0.113.0/24", "224.0.0.0/4", "240.0.0.0/4",
    "255.255.255.255/32"))
# `::ffff:0:0/96` (IPv4-mapped) có trong bảng cho đủ, nhưng địa chỉ mapped được gỡ ra và kiểm bằng bảng IPv4
# TRƯỚC khi tới đây, nên `::ffff:8.8.8.8` vẫn qua còn `::ffff:127.0.0.1` thì bị chặn.
# `fec0::/10` (site-local cũ) đã bỏ khỏi registry (RFC 3879) nhưng chặn cho chắc.
_BLOCKED_V6 = tuple(ipaddress.ip_network(n) for n in (
    "::/128", "::1/128", "::ffff:0:0/96", "::ffff:0:0:0/96", "64:ff9b::/96", "64:ff9b:1::/48", "100::/64",
    "2001::/23", "2001:db8::/32", "2002::/16", "3fff::/20", "5f00::/16", "fc00::/7", "fe80::/10", "fec0::/10",
    "ff00::/8"))
_LDH_HOST = re.compile(r"[a-z0-9-]+(\.[a-z0-9-]+)*\.?")
_HEX64 = re.compile(r"[0-9a-fA-F]{64}")
_INTENTS = ("public", "private")


# ------------------------------------------------------------------ URL

def _invalid(why):
    return ContractError(f"URL không hợp lệ: {why}")


def _internal(host):
    return ContractError(f"URL bị từ chối: host nội bộ ({host})")


def _ip_is_internal(ip):
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped is not None:
        ip = ip.ipv4_mapped
    blocked = _BLOCKED_V4 if isinstance(ip, ipaddress.IPv4Address) else _BLOCKED_V6
    return (any(ip in net for net in blocked)
            or ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved
            or ip.is_multicast or ip.is_unspecified or not ip.is_global)


def check_url(url):
    """Trả URL đã `strip` nếu được phép tải; ngược lại `ContractError`.

    Chuẩn hoá IDNA chỉ dùng cho phép kiểm host — URL trả về không bị viết lại.
    """
    if not isinstance(url, str):
        raise _invalid("không phải chuỗi")
    url = url.strip()
    if not url:
        raise _invalid("rỗng")
    if len(url) > MAX_URL_LEN:
        raise _invalid(f"dài hơn {MAX_URL_LEN} ký tự")
    if any(ch.isspace() or ord(ch) < 32 or ord(ch) == 127 for ch in url):
        raise _invalid("có khoảng trắng hoặc ký tự điều khiển")
    if "\\" in url:  # bộ phân tích WHATWG coi `\` như `/`: cổng và bên tải sẽ thấy host khác nhau
        raise _invalid("có dấu gạch ngược")
    try:
        parts = urlsplit(url)
        host = parts.hostname
        parts.port  # noqa: B018 — cổng sai kiểu ném ValueError
    except ValueError as exc:
        raise _invalid(str(exc)) from None
    if parts.scheme.lower() not in ("http", "https"):
        raise ContractError("URL bị từ chối: chỉ nhận http/https")
    if "@" in parts.netloc:
        raise ContractError("URL bị từ chối: có thông tin đăng nhập (user:pass@)")
    if not host:
        raise _invalid("thiếu host")

    if "[" in parts.netloc:  # IPv6 literal đi thẳng ipaddress, không qua IDNA
        try:
            ip = ipaddress.ip_address(host.split("%", 1)[0])
        except ValueError:
            raise _invalid("IPv6 sai") from None
        if _ip_is_internal(ip):
            raise _internal(host)
        return url

    try:
        host = host.encode("idna").decode("ascii")
    except UnicodeError:
        raise _invalid("host không chuẩn hoá được (IDNA)") from None
    host = host.lower()
    if not _LDH_HOST.fullmatch(host):  # chặn `%xx`, `_`, ký tự lạ mà bộ phân tích khác giải mã khác
        raise _invalid("host chứa ký tự ngoài chữ, số, gạch nối, dấu chấm")
    if host.endswith("."):
        host = host[:-1]
    if not host:
        raise _invalid("thiếu host")
    if host == "localhost" or host.endswith(".localhost"):
        raise _internal(host)
    if _LAST_LABEL_NUMERIC.fullmatch(host.rsplit(".", 1)[-1]):
        # nhãn cuối là số: chuẩn URL coi là IPv4 (kể cả viết tắt/bát phân/hex) — parse không được thì từ chối
        try:
            ip = ipaddress.IPv4Address(host)
        except ValueError:
            raise _internal(host) from None
        if _ip_is_internal(ip):
            raise _internal(host)
    return url


def sha256_file(path):
    """SHA-256 hex của tệp, đọc từng khối."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# ----------------------------------------------------------- provenance

def new_provenance(name, url, local_file, sha256, today):
    """Hồ sơ nguồn bản 1 ở trạng thái mặc định (`rights_pending`, chưa có phép)."""
    return {
        "schema": 1,
        "project": name,
        "created": today,
        "reference": {
            "url": check_url(url) if url else None,
            "local_file": local_file,
            "sha256": sha256,
            "title": None,
        },
        "rights_status": "rights_pending",
        "rights_basis": None,
        "rights_proof": None,
        "publish_intent": "public",
        "permission": {"url": None, "quote": None, "granted_by": None, "granted_at": None},
        "fetch": None,
        "assets": [],
    }


def _escapes_project(path):
    norm = path.replace("\\", "/")
    return (norm.startswith("/") or re.match(r"^[A-Za-z]:", norm) is not None
            or ".." in norm.split("/"))


def _bad(key, why):
    return ContractError(f"{PROVENANCE_FILE}: {key} {why}")


def _check_provenance(prov):
    if not isinstance(prov, dict):
        raise ContractError(f"{PROVENANCE_FILE}: phải là một object JSON")
    schema = prov.get("schema")
    if isinstance(schema, bool) or schema != 1:
        raise _bad("schema", f"phải là 1 (đang {schema!r})")
    if prov.get("rights_status") not in RIGHTS:
        raise _bad("rights_status", f"phải thuộc {list(RIGHTS)} (đang {prov.get('rights_status')!r})")
    if prov.get("rights_basis") is not None and prov["rights_basis"] not in BASES:
        raise _bad("rights_basis", f"phải null hoặc thuộc {list(BASES)} (đang {prov['rights_basis']!r})")
    if prov.get("rights_proof") is not None and not isinstance(prov["rights_proof"], str):
        raise _bad("rights_proof", "phải là chuỗi hoặc null")
    if "publish_intent" in prov and prov["publish_intent"] not in _INTENTS:
        raise _bad("publish_intent", f"phải thuộc {list(_INTENTS)}")
    for key in ("reference", "permission"):
        if key in prov and not isinstance(prov[key], dict):
            raise _bad(key, "phải là object")
    assets = prov.get("assets", [])
    if not isinstance(assets, list):
        raise _bad("assets", "phải là danh sách")
    for i, a in enumerate(assets):
        where = f"assets[{i}]"
        if not isinstance(a, dict):
            raise _bad(where, "phải là object")
        path = a.get("path")
        if not isinstance(path, str) or not path.strip():
            raise _bad(f"{where}.path", "phải là chuỗi không rỗng")
        if _escapes_project(path):
            raise _bad(f"{where}.path", f"phải tương đối, không `..` (đang {path!r})")
        if a.get("origin") not in ORIGINS:
            raise _bad(f"{where}.origin", f"phải thuộc {list(ORIGINS)} (đang {a.get('origin')!r})")
        if not isinstance(a.get("owner"), str) or not a["owner"].strip():
            raise _bad(f"{where}.owner", "không được trống")


def load_provenance(project_dir):
    """Đọc và kiểm `provenance.json`; thiếu, hỏng hay sai schema ⇒ `ContractError` nêu đúng khoá."""
    path = os.path.join(project_dir, PROVENANCE_FILE)
    if not os.path.isfile(path):
        raise ContractError(f"thiếu {path} — chạy `video-studio reference init` trước")
    try:
        with open(path, encoding="utf-8") as fh:
            prov = json.load(fh)
    except (OSError, ValueError) as exc:
        raise ContractError(f"{PROVENANCE_FILE}: không đọc được ({exc})") from None
    _check_provenance(prov)
    return prov


def save_provenance(project_dir, prov):
    """Ghi hồ sơ bằng tệp tạm cùng thư mục + `os.replace`; giữ khoá lạ. Trả đường tệp."""
    path = os.path.join(project_dir, PROVENANCE_FILE)
    fd, tmp = tempfile.mkstemp(prefix=".provenance-", suffix=".tmp", dir=project_dir)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(prov, fh, ensure_ascii=False, indent=2)
            fh.write("\n")
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    return path


# ----------------------------------------------------------- fetch gate

def is_media_name(path):
    """True nếu đuôi (không phân biệt hoa thường) là container video/âm thanh trong `MEDIA_EXTS`."""
    return os.path.splitext(str(path))[1][1:].lower() in MEDIA_EXTS


def require_media_file(path):
    """`ContractError` nếu `path` không có đuôi video/âm thanh (playlist, danh sách, văn bản… không được mở)."""
    if not is_media_name(path):
        ext = os.path.splitext(str(path))[1] or "không có đuôi"
        raise ContractError(f"chỉ nhận tệp video/âm thanh ({', '.join(sorted(MEDIA_EXTS))}); đuôi {ext} "
                            f"không được nhận: {path}")


def require_plain_format(raw, path):
    """`ContractError` nếu `format.format_name` thiếu, hoặc có phần ngoài `PLAIN_FORMATS` (danh sách trắng)."""
    fmt = (raw.get("format") or {}).get("format_name") if isinstance(raw, dict) else None
    names = [n.strip().lower() for n in str(fmt or "").split(",")]
    bad = [n for n in names if n not in PLAIN_FORMATS]
    if bad:
        shown = ",".join(n for n in bad if n) or "(không rõ)"
        raise ContractError(f"định dạng {shown} không phải video/âm thanh thường (đọc theo nội dung, "
                            f"có thể kéo tệp khác lên): {path}")


def _blank(value):
    return not isinstance(value, str) or not value.strip()


def _norm(url):
    try:
        return check_url(url)
    except ContractError:
        return None


def require_fetch_allowed(prov, url, allow_url):
    """Cổng 1, 2, 4, 5 của `fetch` (cổng 3 là việc nạp `prov`); dừng ở cổng đầu tiên hỏng.

    So `url`, `allow_url`, `permission.url`, `reference.url` trên bản đã qua `check_url`
    (chỉ `strip`, không hạ chữ thường).
    """
    target = check_url(url)

    allowed = None if allow_url is None else _norm(allow_url)
    if allowed is None or allowed != target:
        raise ContractError("thiếu phép đích danh cho URL này: truyền --allow-url đúng URL cần tải")

    status, basis = prov.get("rights_status"), prov.get("rights_basis")
    if status != "approved":
        raise ContractError(f"rights_status đang là {status!r}: chỉ phân tích từ mô tả hoặc tệp người dùng có quyền, "
                            "không tải")
    if basis not in BASES:
        raise ContractError(f"rights_basis là {basis!r}, cần một trong {list(BASES)}")
    if basis != "own_content" and _blank(prov.get("rights_proof")):
        raise ContractError(f"rights_proof trống: rights_basis {basis!r} cần chứng từ (tệp, URL hoặc số hợp đồng)")

    perm = prov.get("permission") or {}
    if _norm(perm.get("url")) != target:
        raise ContractError("permission.url phải bằng URL cần tải")
    for key in ("quote", "granted_by"):
        if _blank(perm.get(key)):
            raise ContractError(f"permission.{key} trống")
    quote = perm["quote"].strip()
    if not any(re.search(re.escape(c) + _QUOTE_END, quote) for c in (target, url.strip())):
        raise ContractError("permission.quote phải chứa đúng URL cần tải (lời người dùng nói đích danh URL)")
    stamp = perm.get("granted_at")
    if isinstance(stamp, str) and stamp[-1:] in ("Z", "z"):  # Python 3.10 chưa nhận hậu tố Z
        stamp = stamp[:-1] + "+00:00"
    try:
        datetime.datetime.fromisoformat(stamp)
        has_time = re.search(r"\d[T ]\d{1,2}:\d{2}", stamp) is not None
    except (TypeError, ValueError):
        has_time = False
    if not has_time:
        raise ContractError("permission.granted_at phải là ngày giờ ISO 8601, có cả phần giờ")

    ref_url = (prov.get("reference") or {}).get("url")
    if ref_url is not None and _norm(ref_url) != target:
        raise ContractError("reference.url lệch URL cần tải")


# ------------------------------------------------------------ audit

LINK_PROBLEM = "liên kết mềm không được kiểm"


def _is_link(path):
    """Liên kết mềm hoặc junction Windows (`islink` không thấy junction; `isjunction` có từ Python 3.12)."""
    if os.path.islink(path):
        return True
    isjunction = getattr(os.path, "isjunction", None)
    if isjunction is not None:
        return isjunction(path)
    try:  # đường lùi cho Python < 3.12: junction là reparse point loại MOUNT_POINT
        tag = getattr(os.lstat(path), "st_reparse_tag", 0)
    except OSError:
        return False
    return tag == getattr(stat, "IO_REPARSE_TAG_MOUNT_POINT", 0xA0000003)


def _rel(path, base):
    return os.path.relpath(path, base).replace(os.sep, "/")


def _walk_files(root):
    """Mọi mục không phải thư mục dưới `root`; liên kết/junction tới thư mục tính là một mục và không được đi vào.

    Gốc `root` do bên gọi kiểm trước (`_is_link`).
    """
    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        dirnames.sort()
        links = [d for d in dirnames if _is_link(os.path.join(dirpath, d))]
        dirnames[:] = [d for d in dirnames if d not in links]
        for name in sorted(filenames + links):
            yield os.path.join(dirpath, name)


def _reference_hashes(project_dir, prov):
    """(sha256 → đường tương đối, phát hiện) của tư liệu mẫu: tệp thường trong `source/` và `evidence/**`.

    Gốc `source/` hay `evidence/`, hoặc mục lồng bên trong, là liên kết ⇒ phát hiện, không băm vào trong. Thêm các băm đã ghi trong hồ sơ
    (`reference.sha256`, `fetch.sha256`; chuỗi hex 64 ký tự, giá trị lạ bỏ qua) — không đọc lại tệp ngoài project.
    """
    found, findings = {}, []
    for sub in ("source", "evidence"):
        root = os.path.join(project_dir, sub)
        if _is_link(root):
            findings.append({"path": sub, "problem": LINK_PROBLEM})
            continue
        for path in _walk_files(root):
            if _is_link(path):
                findings.append({"path": _rel(path, project_dir), "problem": LINK_PROBLEM})
                continue
            if not os.path.isfile(path):
                continue
            found.setdefault(sha256_file(path), _rel(path, project_dir))
    for section, label in (("reference", "(reference.local_file)"), ("fetch", "(fetch.file)")):
        recorded = (prov.get(section) or {}).get("sha256") if isinstance(prov.get(section), dict) else None
        if isinstance(recorded, str) and _HEX64.fullmatch(recorded.strip()):
            found.setdefault(recorded.strip().lower(), label)
    return found, findings


def _is_inside(base, path):
    try:
        return os.path.commonpath([os.path.normcase(base), os.path.normcase(path)]) == os.path.normcase(base)
    except ValueError:  # khác ổ đĩa trên Windows
        return False


def _reached_through_link(project_dir, assets_dir):
    """True nếu đường tới `assets_dir` đi qua liên kết/junction ở cấp nào đó (so `realpath` với đường chuẩn hoá)."""
    rel = os.path.relpath(assets_dir, os.path.abspath(project_dir))
    expected = os.path.join(os.path.realpath(project_dir), rel)
    return os.path.normcase(os.path.realpath(assets_dir)) != os.path.normcase(os.path.normpath(expected))


def audit_assets(project_dir, assets_dir=None):
    """Kiểm thư mục tài sản với hồ sơ: `{"ok", "checked", "findings": [{"path", "problem"}]}`.

    `checked` = số mục có thật trong thư mục tài sản. Thư mục không tồn tại ⇒ ok, 0. Gốc thư mục tài sản
    là liên kết/junction ⇒ phát hiện, không đi vào. `assets_dir` ngoài project ⇒ `ContractError`.
    Không đọc spec/EDL.
    """
    prov = load_provenance(project_dir)
    assets_dir = os.path.abspath(assets_dir or os.path.join(project_dir, "assets"))  # bỏ `..`, `.`, dấu phân cách cuối
    outside = ContractError(f"thư mục tài sản {assets_dir} phải nằm trong project {project_dir}")
    if not _is_inside(os.path.abspath(project_dir), assets_dir):
        raise outside
    if _is_link(assets_dir):
        return {"ok": False, "checked": 0,
                "findings": [{"path": _rel(assets_dir, project_dir), "problem": LINK_PROBLEM}]}
    if not _is_inside(os.path.realpath(project_dir), os.path.realpath(assets_dir)):
        raise outside
    if _reached_through_link(project_dir, assets_dir):
        return {"ok": False, "checked": 0,
                "findings": [{"path": _rel(assets_dir, project_dir), "problem": LINK_PROBLEM}]}
    if not os.path.isdir(assets_dir):
        return {"ok": True, "checked": 0, "findings": []}

    declared = {}
    for a in prov.get("assets", []):
        declared.setdefault(os.path.normpath(a["path"].replace("\\", "/")).replace(os.sep, "/"), []).append(a)
    ref_hashes, findings = _reference_hashes(project_dir, prov)
    seen, checked = set(), 0

    def add(rel, problem):
        item = {"path": rel, "problem": problem}
        if item not in findings:
            findings.append(item)

    for path in _walk_files(assets_dir):
        rel = _rel(path, project_dir)
        checked += 1
        seen.add(rel)
        entries = declared.get(rel)
        if _is_link(path):
            add(rel, LINK_PROBLEM)
            continue
        if entries is None:
            hidden = os.path.basename(path).startswith(".")
            add(rel, "tệp ẩn chưa khai" if hidden else "chưa khai trong assets")
        else:
            if len({(e["origin"], e.get("owner")) for e in entries}) > 1:
                add(rel, "khai trùng mâu thuẫn")
            for entry in entries:
                if entry["origin"] not in BUILD_ORIGINS:
                    add(rel, "origin reference không được dùng để dựng")
                if _blank(entry.get("owner")):
                    add(rel, "owner trống")
        if not os.path.isfile(path):
            continue
        same = ref_hashes.get(sha256_file(path))  # khai hay chưa đều so hash với tư liệu mẫu
        if same:
            add(rel, f"trùng byte với tệp mẫu {same}")

    for rel in declared:
        if rel not in seen:
            add(rel, "khai nhưng không có tệp")

    return {"ok": not findings, "checked": checked, "findings": findings}
