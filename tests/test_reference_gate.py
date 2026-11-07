"""`video_studio.reference.gate`: URL, hồ sơ nguồn, cổng tải và kiểm tài sản (thuần, không mạng).

Mọi lỗi là `ContractError` (mã 2). Thông điệp được so bằng chuỗi con vì đó là thứ người dùng đọc.
"""
import copy
import hashlib
import json
import os

import pytest

from video_studio.contract import ContractError
from video_studio.reference import gate

URL = "https://www.example.com/watch?v=abc"


# ---------------------------------------------------------------- check_url

@pytest.mark.parametrize("raw, expected", [
    (" https://www.example.com/watch?v=abc ", "https://www.example.com/watch?v=abc"),
    ("https://abc.de/", "https://abc.de/"),
    ("https://face.cc/", "https://face.cc/"),
    ("https://cafe.example/", "https://cafe.example/"),
    ("http://Example.COM/Path/CaseSensitive", "http://Example.COM/Path/CaseSensitive"),
    ("https://bücher.example/", "https://bücher.example/"),
    ("https://8.8.8.8/x", "https://8.8.8.8/x"),
    ("https://example.com:8443/x", "https://example.com:8443/x"),
])
def test_check_url_accepts_public_https(raw, expected):
    assert gate.check_url(raw) == expected


@pytest.mark.parametrize("raw", ["file:///etc/passwd", "ftp://example.com/a", "-o/x", "javascript:alert(1)", "example.com/a"])
def test_check_url_refuses_scheme(raw):
    with pytest.raises(ContractError, match="chỉ nhận http/https"):
        gate.check_url(raw)


def test_check_url_refuses_credentials():
    with pytest.raises(ContractError, match="thông tin đăng nhập"):
        gate.check_url("https://u:p@example.com/v")


@pytest.mark.parametrize("raw", [
    "http://localhost/x", "http://api.localhost/x", "http://localhost./x",
    "http://127.0.0.1:8080/x", "http://10.0.0.5/x", "http://[::1]/x",
    "http://[::ffff:127.0.0.1]/x", "http://169.254.169.254/latest", "http://0.0.0.0/",
    "http://2130706433/", "http://0x7f000001/", "http://127.1/", "http://0177.0.0.1/",
    "http://127.0.0.1./",
    # IDNA: chữ số và dấu chấm toàn chiều rộng / dấu chấm CJK
    "http://１２７．０．０．１/", "http://127.0.0.1。/", "http://127．0．0．1/", "http://localhost｡/",
    # dải CGNAT
    "http://100.64.0.1/",
    # IPv6 riêng / link-local
    "http://[fe80::1]/", "http://[fc00::1]/",
])
def test_check_url_refuses_internal_hosts(raw):
    with pytest.raises(ContractError, match="host nội bộ"):
        gate.check_url(raw)


@pytest.mark.parametrize("raw", ["http://0x7f.0.0.1/", "http://1.2.3.4.5/", "http://0x/", "http://10.1/"])
def test_check_url_refuses_unparseable_ip_like_host(raw):
    with pytest.raises(ContractError, match="host nội bộ"):
        gate.check_url(raw)


@pytest.mark.parametrize("raw", [
    "https://example.com/a b", "https://example.com/a\tb", "https://example.com/a\nb",
    "https://exa mple.com/", "https://example.com/\x00", "https://example.com/\x7f",
    "https://example.com/a" + "b" * 2100, "", "   ", "https://", "https:///path",
    "https://a..b/", "https://[::1/", "https://example.com:notaport/",
])
def test_check_url_refuses_whitespace_and_length(raw):
    with pytest.raises(ContractError, match="URL không hợp lệ"):
        gate.check_url(raw)


def test_check_url_length_boundary():
    ok = "https://example.com/" + "a" * (2048 - len("https://example.com/"))
    assert len(ok) == 2048 and gate.check_url(ok) == ok
    with pytest.raises(ContractError, match="URL không hợp lệ"):
        gate.check_url(ok + "a")


def test_check_url_refuses_non_string():
    with pytest.raises(ContractError, match="URL không hợp lệ"):
        gate.check_url(None)


# ------------------------------------------------------------- provenance

def test_new_provenance_defaults():
    prov = gate.new_provenance("demo", None, None, None, "2026-11-07")
    assert prov["schema"] == 1
    assert prov["project"] == "demo" and prov["created"] == "2026-11-07"
    assert prov["rights_status"] == "rights_pending"
    assert prov["rights_basis"] is None and prov["rights_proof"] is None
    assert prov["publish_intent"] == "public"
    assert prov["permission"] == {"url": None, "quote": None, "granted_by": None, "granted_at": None}
    assert prov["reference"] == {"url": None, "local_file": None, "sha256": None, "title": None}
    assert prov["fetch"] is None and prov["assets"] == []


def test_new_provenance_normalizes_reference_url():
    prov = gate.new_provenance("demo", f"  {URL} ", "clip.mp4", "ab" * 32, "2026-11-07")
    assert prov["reference"] == {"url": URL, "local_file": "clip.mp4", "sha256": "ab" * 32, "title": None}
    with pytest.raises(ContractError, match="host nội bộ"):
        gate.new_provenance("demo", "http://127.0.0.1/", None, None, "2026-11-07")


def _project(tmp_path, prov=None):
    proj = tmp_path / "proj"
    proj.mkdir(exist_ok=True)
    gate.save_provenance(str(proj), prov if prov is not None else gate.new_provenance("demo", None, None, None, "2026-11-07"))
    return str(proj)


def test_load_provenance_roundtrip(tmp_path):
    prov = gate.new_provenance("demo", None, None, None, "2026-11-07")
    proj = _project(tmp_path, prov)
    assert gate.load_provenance(proj) == prov


def test_load_provenance_missing_points_to_init(tmp_path):
    with pytest.raises(ContractError, match="chạy `video-studio reference init`"):
        gate.load_provenance(str(tmp_path))


def test_load_provenance_rejects_broken_json(tmp_path):
    (tmp_path / "provenance.json").write_text("{không phải json", encoding="utf-8")
    with pytest.raises(ContractError, match="provenance.json"):
        gate.load_provenance(str(tmp_path))


def test_load_provenance_rejects_non_object(tmp_path):
    (tmp_path / "provenance.json").write_text("[1, 2]", encoding="utf-8")
    with pytest.raises(ContractError, match="provenance.json"):
        gate.load_provenance(str(tmp_path))


def _asset(**kw):
    base = {"path": "assets/a.png", "origin": "user", "owner": "me", "note": ""}
    base.update(kw)
    return base


@pytest.mark.parametrize("mutate, key", [
    (lambda p: p.update(schema=2), "schema"),
    (lambda p: p.update(schema=True), "schema"),
    (lambda p: p.pop("schema"), "schema"),
    (lambda p: p.update(rights_status="maybe"), "rights_status"),
    (lambda p: p.pop("rights_status"), "rights_status"),
    (lambda p: p.update(rights_basis="vibes"), "rights_basis"),
    (lambda p: p.update(rights_proof=123), "rights_proof"),
    (lambda p: p.update(rights_proof=["a"]), "rights_proof"),
    (lambda p: p.update(publish_intent="friends"), "publish_intent"),
    (lambda p: p.update(permission="yes"), "permission"),
    (lambda p: p.update(reference=[]), "reference"),
    (lambda p: p.update(assets={}), "assets"),
    (lambda p: p.update(assets=["a.png"]), "assets[0]"),
    (lambda p: p.update(assets=[_asset(origin="stolen")]), "assets[0].origin"),
    (lambda p: p.update(assets=[_asset(owner="")]), "assets[0].owner"),
    (lambda p: p.update(assets=[_asset(owner="   ")]), "assets[0].owner"),
    (lambda p: p.update(assets=[_asset(owner=None)]), "assets[0].owner"),
    (lambda p: p.update(assets=[_asset(), _asset(path="")]), "assets[1].path"),
    (lambda p: p.update(assets=[_asset(path=7)]), "assets[0].path"),
])
def test_load_provenance_rejects_bad_fields(tmp_path, mutate, key):
    prov = gate.new_provenance("demo", None, None, None, "2026-11-07")
    mutate(prov)
    (tmp_path / "provenance.json").write_text(json.dumps(prov), encoding="utf-8")
    with pytest.raises(ContractError) as err:
        gate.load_provenance(str(tmp_path))
    assert key in str(err.value)


@pytest.mark.parametrize("bad", [
    "/etc/passwd", "\\windows\\system32", "C:/Users/x/a.png", "C:\\Users\\x\\a.png", "D:a.png",
    "../secret.png", "assets/../../secret.png", "assets\\..\\..\\x.png", "..", "//server/share/a.png",
])
def test_load_provenance_rejects_escaping_asset_paths(tmp_path, bad):
    prov = gate.new_provenance("demo", None, None, None, "2026-11-07")
    prov["assets"] = [_asset(path=bad)]
    (tmp_path / "provenance.json").write_text(json.dumps(prov), encoding="utf-8")
    with pytest.raises(ContractError, match=r"assets\[0\]\.path"):
        gate.load_provenance(str(tmp_path))


def test_save_provenance_keeps_unknown_keys_and_is_atomic(tmp_path, monkeypatch):
    prov = gate.new_provenance("demo", None, None, None, "2026-11-07")
    prov["x_note"] = {"giữ": "nguyên", "n": 1}
    proj = _project(tmp_path, prov)
    again = gate.load_provenance(proj)
    assert again["x_note"] == {"giữ": "nguyên", "n": 1}
    raw = (tmp_path / "proj" / "provenance.json").read_text(encoding="utf-8")
    assert "giữ" in raw and raw.endswith("\n")  # tiếng Việt không bị escape

    # ghi hỏng giữa chừng: bản cũ còn nguyên, không để tệp tạm lại
    before = raw
    monkeypatch.setattr(os, "replace", lambda *a, **k: (_ for _ in ()).throw(OSError("đĩa đầy")))
    prov2 = copy.deepcopy(prov)
    prov2["rights_status"] = "approved"
    with pytest.raises(OSError):
        gate.save_provenance(proj, prov2)
    monkeypatch.undo()
    assert (tmp_path / "proj" / "provenance.json").read_text(encoding="utf-8") == before
    assert sorted(os.listdir(proj)) == ["provenance.json"]


# -------------------------------------------------------------- fetch gate

def _ok_prov(url=URL, **over):
    prov = gate.new_provenance("demo", None, None, None, "2026-11-07")
    prov.update(
        rights_status="approved", rights_basis="written_permission", rights_proof="thư cấp phép ngày 2026-11-01",
        permission={"url": url, "quote": f"được dùng {url} cho bản chuyển thể", "granted_by": "chủ kênh", "granted_at": "2026-11-01T09:00:00+07:00"},
    )
    prov.update(over)
    return prov


def test_fetch_gate_passes_when_everything_in_order():
    assert gate.require_fetch_allowed(_ok_prov(), URL, URL) is None


def _set(**kw):
    def f(prov):
        prov.update(kw)
    return f


def _perm(**kw):
    def f(prov):
        prov["permission"] = dict(prov["permission"], **kw)
    return f


@pytest.mark.parametrize("url, allow, mutate, needle", [
    ("file:///etc/passwd", "file:///etc/passwd", None, "chỉ nhận http/https"),
    ("http://127.0.0.1/x", "http://127.0.0.1/x", None, "host nội bộ"),
    (URL, None, None, "thiếu phép đích danh"),
    (URL, "https://www.example.com/other", None, "thiếu phép đích danh"),
    (URL, "không phải url", None, "thiếu phép đích danh"),
    (URL, URL, _set(rights_status="rights_pending"), "chỉ phân tích"),
    (URL, URL, _set(rights_status="blocked"), "chỉ phân tích"),
    (URL, URL, _set(rights_basis=None), "rights_basis"),
    (URL, URL, _set(rights_basis="vibes"), "rights_basis"),
    (URL, URL, _set(rights_proof=None), "rights_proof"),
    (URL, URL, _set(rights_proof="   "), "rights_proof"),
    (URL, URL, _set(rights_basis="license", rights_proof=""), "rights_proof"),
    (URL, URL, _perm(url="https://www.example.com/other"), "permission.url"),
    (URL, URL, _perm(url=None), "permission.url"),
    (URL, URL, _perm(quote=""), "permission.quote"),
    (URL, URL, _perm(quote="  "), "permission.quote"),
    (URL, URL, _perm(granted_by=None), "permission.granted_by"),
    (URL, URL, _perm(granted_at="hôm qua"), "permission.granted_at"),
    (URL, URL, _perm(granted_at=None), "permission.granted_at"),
    (URL, URL, _set(reference={"url": "https://www.example.com/other", "local_file": None, "sha256": None, "title": None}), "reference.url"),
])
def test_fetch_gate_order(url, allow, mutate, needle):
    prov = _ok_prov()
    if mutate:
        mutate(prov)
    with pytest.raises(ContractError) as err:
        gate.require_fetch_allowed(prov, url, allow)
    assert needle in str(err.value)


def test_fetch_gate_own_content_needs_no_proof():
    prov = _ok_prov(rights_basis="own_content", rights_proof=None)
    assert gate.require_fetch_allowed(prov, URL, URL) is None


def test_fetch_gate_reference_url_none_or_equal_passes():
    prov = _ok_prov(reference={"url": None, "local_file": None, "sha256": None, "title": None})
    assert gate.require_fetch_allowed(prov, URL, URL) is None
    prov["reference"]["url"] = URL
    assert gate.require_fetch_allowed(prov, URL, URL) is None


def test_fetch_gate_stops_at_first_failing_gate():
    # hỏng đồng thời URL-allow, rights_status và permission: báo cổng 2 trước
    prov = _ok_prov(rights_status="blocked")
    prov["permission"]["quote"] = ""
    with pytest.raises(ContractError, match="thiếu phép đích danh"):
        gate.require_fetch_allowed(prov, URL, None)
    # qua cổng 2, báo rights_status trước permission
    with pytest.raises(ContractError, match="rights_status"):
        gate.require_fetch_allowed(prov, URL, URL)


def test_fetch_gate_compares_normalized_urls():
    padded = f"  {URL}  "
    prov = _ok_prov(url=padded)
    prov["reference"]["url"] = padded
    assert gate.require_fetch_allowed(prov, padded, URL) is None
    assert gate.require_fetch_allowed(prov, URL, padded) is None
    # chỉ strip, không hạ chữ thường: đường dẫn phân biệt hoa thường
    with pytest.raises(ContractError, match="thiếu phép đích danh"):
        gate.require_fetch_allowed(prov, URL, URL.replace("watch", "WATCH"))
    upper = _ok_prov(url=URL.replace("watch", "WATCH"))
    with pytest.raises(ContractError, match="permission.url"):
        gate.require_fetch_allowed(upper, URL, URL)


# ------------------------------------------------------------ sha256_file

def test_sha256_file(tmp_path):
    p = tmp_path / "a.bin"
    data = "xin chào".encode("utf-8") * 100000  # nhiều hơn một khối đọc
    p.write_bytes(data)
    assert gate.sha256_file(str(p)) == hashlib.sha256(data).hexdigest()
    empty = tmp_path / "e.bin"
    empty.write_bytes(b"")
    assert gate.sha256_file(str(empty)) == hashlib.sha256(b"").hexdigest()


# ------------------------------------------------------------- audit_assets

def _write(proj, rel, data=b"x"):
    p = os.path.join(proj, *rel.split("/"))
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "wb") as fh:
        fh.write(data)
    return p


def _declare(proj, *assets):
    prov = gate.load_provenance(proj)
    prov["assets"] = list(assets)
    gate.save_provenance(proj, prov)


def test_audit_clean_project(tmp_path):
    proj = _project(tmp_path)
    _write(proj, "source/reference.mp4", b"mau")
    _write(proj, "assets/hero.png", b"hero")
    _write(proj, "assets/sub/clip.mp4", b"clip")
    _declare(proj, _asset(path="assets/hero.png"), _asset(path="assets/sub/clip.mp4", origin="generated"),
             _asset(path="assets/hero.png"))  # khai trùng không làm hỏng
    out = gate.audit_assets(proj)
    assert out == {"ok": True, "checked": 2, "findings": []}


def test_audit_no_assets_dir_is_ok(tmp_path):
    proj = _project(tmp_path)
    assert gate.audit_assets(proj) == {"ok": True, "checked": 0, "findings": []}


def test_audit_findings(tmp_path):
    proj = _project(tmp_path)
    _write(proj, "source/reference.mp4", b"video mau")
    _write(proj, "assets/undeclared.png", b"u")
    _write(proj, "assets/from_ref.mp4", b"video mau")
    _write(proj, "assets/refused.png", b"r")
    _declare(
        proj,
        _asset(path="assets/from_ref.mp4"),                      # trùng byte với source/
        _asset(path="assets/refused.png", origin="reference"),   # origin cấm dựng
        _asset(path="assets/missing.png"),                       # khai nhưng không có tệp
    )
    out = gate.audit_assets(proj)
    problems = {(f["path"], f["problem"].split(" <")[0]) for f in out["findings"]}
    assert out["ok"] is False and out["checked"] == 3  # chỉ đếm tệp có thật trong thư mục tài sản
    assert ("assets/undeclared.png", "chưa khai trong assets") in problems
    assert ("assets/refused.png", "origin reference không được dùng để dựng") in problems
    assert ("assets/missing.png", "khai nhưng không có tệp") in problems
    dup = [f for f in out["findings"] if f["path"] == "assets/from_ref.mp4"]
    assert len(dup) == 1 and "trùng byte với tệp mẫu source/reference.mp4" in dup[0]["problem"]


def test_audit_flags_empty_owner(tmp_path, monkeypatch):
    proj = _project(tmp_path)
    _write(proj, "assets/a.png", b"a")
    _declare(proj, _asset(path="assets/a.png"))
    real_load = gate.load_provenance

    def tampered(p):  # load_provenance đã chặn owner rỗng; audit vẫn phải tự bắt
        d = real_load(p)
        d["assets"][0]["owner"] = "  "
        return d
    monkeypatch.setattr(gate, "load_provenance", tampered)
    out = gate.audit_assets(proj)
    assert [f["problem"] for f in out["findings"]] == ["owner trống"]


def test_audit_flags_reference_frame_copied_to_assets(tmp_path):
    proj = _project(tmp_path)
    frame = b"\x89PNG khung 1000ms"
    _write(proj, "evidence/frames/frame_001000.png", frame)
    _write(proj, "assets/looks_mine.png", frame)
    _declare(proj, _asset(path="assets/looks_mine.png", origin="user"))
    out = gate.audit_assets(proj)
    assert out["ok"] is False
    assert any("trùng byte với tệp mẫu evidence/frames/frame_001000.png" in f["problem"] for f in out["findings"])


def test_audit_flags_hidden_file(tmp_path):
    proj = _project(tmp_path)
    _write(proj, "assets/.hero.png", b"h")
    out = gate.audit_assets(proj)
    assert out["ok"] is False
    assert out["findings"] == [{"path": "assets/.hero.png", "problem": "tệp ẩn chưa khai"}]


def test_audit_checks_declared_hidden_file_like_a_normal_one(tmp_path):
    proj = _project(tmp_path)
    _write(proj, "source/reference.mp4", b"mau")
    _write(proj, "assets/.hero.png", b"mau")
    _declare(proj, _asset(path="assets/.hero.png"))
    out = gate.audit_assets(proj)
    assert out["checked"] == 1
    assert [f["problem"] for f in out["findings"]] == ["trùng byte với tệp mẫu source/reference.mp4"]


def test_audit_flags_symlink(tmp_path):
    proj = _project(tmp_path)
    target = tmp_path / "outside.png"
    target.write_bytes(b"o")
    os.makedirs(os.path.join(proj, "assets"))
    try:
        os.symlink(str(target), os.path.join(proj, "assets", "link.png"))
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"hệ điều hành không cho tạo liên kết mềm: {exc}")
    out = gate.audit_assets(proj)
    assert out["ok"] is False
    assert {"path": "assets/link.png", "problem": "liên kết mềm không được kiểm"} in out["findings"]


def test_audit_custom_assets_dir(tmp_path):
    proj = _project(tmp_path)
    _write(proj, "other/a.png", b"a")
    _declare(proj, _asset(path="other/a.png"))
    assert gate.audit_assets(proj, os.path.join(proj, "other")) == {"ok": True, "checked": 1, "findings": []}
    assert gate.audit_assets(proj) == {"ok": True, "checked": 0, "findings": []}  # assets/ không có


def test_audit_requires_provenance(tmp_path):
    with pytest.raises(ContractError, match="reference init"):
        gate.audit_assets(str(tmp_path))


# ------------------------------------------------- vòng sửa 1: lệch bộ phân tích URL

BACKSLASH = chr(92)


@pytest.mark.parametrize("raw", [
    "http://169.254.169.%32%35%34/latest", "http://127.0.0.%31/", "http://loc%61lhost/",
    "http://10.0.0.%35/x", "http://127.0.0.1%2e/", "http://localhost%2e/",
    "http://%31%32%37.0.0.1/", "http://my_host.example.com/", "http://exa$mple.com/",
])
def test_check_url_refuses_percent_encoded_or_non_ldh_host(raw):
    with pytest.raises(ContractError, match="URL không hợp lệ"):
        gate.check_url(raw)


@pytest.mark.parametrize("raw", [
    "http://127.0.0.1" + BACKSLASH + ".example.com/watch",
    "http://169.254.169.254" + BACKSLASH + ".example.com/latest",
    "http://127.0.0.1" + BACKSLASH + "/",
    "https://example.com/a" + BACKSLASH + "b",
    "https://example.com/?q=" + BACKSLASH,
])
def test_check_url_refuses_backslash_anywhere(raw):
    with pytest.raises(ContractError, match="URL không hợp lệ"):
        gate.check_url(raw)


@pytest.mark.parametrize("raw", [
    "http://[fe80::1%25eth0]/", "http://192.0.0.8/", "http://198.18.0.1/", "http://[64:ff9b::7f00:1]/",
    "http://[2001:db8::1]/", "http://[::ffff:100.64.0.1]/",
])
def test_check_url_refuses_non_global_ip_literals(raw):
    with pytest.raises(ContractError):
        gate.check_url(raw)


@pytest.mark.parametrize("raw", [
    "https://8.8.8.8/", "https://[::ffff:8.8.8.8]/", "https://[2606:4700:4700::1111]/x",
    "https://xn--bcher-kva.example/", "https://a-b.example.com./x",
])
def test_check_url_still_accepts_public_ip_literals_and_ldh_hosts(raw):
    assert gate.check_url(raw) == raw


@pytest.mark.parametrize("stamp", ["2026-11-07T10:00:00Z", "2026-11-07T10:00:00z", "2026-11-07T10:00:00+07:00", "2026-11-07 10:00", "2099-01-01T00:00:00"])
def test_fetch_gate_accepts_iso_granted_at_incl_z_suffix(stamp):
    prov = _ok_prov()
    prov["permission"]["granted_at"] = stamp
    assert gate.require_fetch_allowed(prov, URL, URL) is None


@pytest.mark.parametrize("stamp", ["", "Z", "2026-13-45T00:00:00Z", 20261107, "2026-11-07"])
def test_fetch_gate_refuses_bad_granted_at(stamp):
    prov = _ok_prov()
    prov["permission"]["granted_at"] = stamp
    with pytest.raises(ContractError, match="permission.granted_at"):
        gate.require_fetch_allowed(prov, URL, URL)


def test_fetch_gate_quote_must_name_the_url():
    for quote in ("ok", "được dùng cho bản chuyển thể", "https://www.example.com/other"):
        prov = _ok_prov()
        prov["permission"]["quote"] = quote
        with pytest.raises(ContractError) as err:
            gate.require_fetch_allowed(prov, URL, URL)
        assert "permission.quote" in str(err.value) and "URL" in str(err.value)


def test_fetch_gate_quote_with_original_or_normalized_url_passes():
    padded = f"  {URL}  "
    prov = _ok_prov(url=padded)
    prov["permission"]["quote"] = f"đồng ý: {URL}"
    assert gate.require_fetch_allowed(prov, padded, URL) is None
    prov["permission"]["quote"] = f"đồng ý:{padded}"
    assert gate.require_fetch_allowed(prov, padded, URL) is None


# ------------------------------------------------- vòng sửa 1: liên kết, khai trùng, ngoài project

def _make_dir_link(link, target):
    """Liên kết thư mục: junction trên Windows (không cần admin), symlink nơi khác; skip nếu không tạo được."""
    try:
        if os.name == "nt":
            import _winapi
            _winapi.CreateJunction(str(target), str(link))
        else:
            os.symlink(str(target), str(link), target_is_directory=True)
    except (OSError, NotImplementedError, ImportError, AttributeError) as exc:
        pytest.skip(f"không tạo được liên kết thư mục: {exc}")


def test_audit_flags_directory_link_inside_assets(tmp_path):
    proj = _project(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secret.png").write_bytes(b"s")
    os.makedirs(os.path.join(proj, "assets"))
    _make_dir_link(os.path.join(proj, "assets", "jump"), outside)
    out = gate.audit_assets(proj)
    assert out["ok"] is False
    assert {"path": "assets/jump", "problem": "liên kết mềm không được kiểm"} in out["findings"]
    assert not any("secret.png" in f["path"] for f in out["findings"])  # không đi vào


def test_audit_flags_assets_root_that_is_a_link(tmp_path):
    proj = _project(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "a.png").write_bytes(b"a")
    _make_dir_link(os.path.join(proj, "assets"), outside)
    out = gate.audit_assets(proj)
    assert out["ok"] is False
    assert out["findings"] == [{"path": "assets", "problem": "liên kết mềm không được kiểm"}]


@pytest.mark.parametrize("root", ["source", "evidence"])
def test_audit_flags_reference_root_that_is_a_link_without_hashing_inside(tmp_path, root):
    proj = _project(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    payload = b"mau nam ngoai"
    (outside / "big.mp4").write_bytes(payload)
    _make_dir_link(os.path.join(proj, root), outside)
    _write(proj, "assets/copy.mp4", payload)
    _declare(proj, _asset(path="assets/copy.mp4"))
    out = gate.audit_assets(proj)
    assert out["ok"] is False
    assert {"path": root, "problem": "liên kết mềm không được kiểm"} in out["findings"]
    assert not any("trùng byte" in f["problem"] for f in out["findings"])  # không băm vào trong


def test_audit_flags_contradicting_duplicate_declarations(tmp_path):
    proj = _project(tmp_path)
    _write(proj, "assets/a.png", b"a")
    _declare(proj, _asset(path="assets/a.png", origin="user"), _asset(path="assets/a.png", origin="reference"))
    problems = [f["problem"] for f in gate.audit_assets(proj)["findings"]]
    assert "khai trùng mâu thuẫn" in problems
    assert "origin reference không được dùng để dựng" in problems  # mục sau không bị che
    _declare(proj, _asset(path="assets/a.png", owner="me"), _asset(path="assets/./a.png", owner="other"))
    assert "khai trùng mâu thuẫn" in [f["problem"] for f in gate.audit_assets(proj)["findings"]]


def test_audit_refuses_assets_dir_outside_project(tmp_path):
    proj = _project(tmp_path)
    outside = tmp_path / "elsewhere"
    outside.mkdir()
    with pytest.raises(ContractError, match="nằm trong project"):
        gate.audit_assets(proj, str(outside))
    with pytest.raises(ContractError, match="nằm trong project"):
        gate.audit_assets(proj, os.path.join(proj, "..", "elsewhere"))


def test_audit_different_drive_is_a_contract_error(tmp_path, monkeypatch):
    proj = _project(tmp_path)
    os.makedirs(os.path.join(proj, "assets"))

    def other_drive(*a, **k):
        raise ValueError("path is on mount 'D:', start on mount 'C:'")
    monkeypatch.setattr(os.path, "commonpath", other_drive)
    with pytest.raises(ContractError, match="nằm trong project"):
        gate.audit_assets(proj)


# ------------------------------------------------- vòng sửa 2: junction không có isjunction, liên kết cấp giữa

@pytest.mark.skipif(os.name != "nt", reason="đường lùi reparse-point chỉ có nghĩa trên Windows")
def test_audit_flags_junction_when_os_path_has_no_isjunction(tmp_path, monkeypatch):
    """Python 3.10/3.11 trên Windows không có `os.path.isjunction`."""
    monkeypatch.delattr(os.path, "isjunction", raising=False)
    proj = _project(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secret.png").write_bytes(b"s")
    os.makedirs(os.path.join(proj, "assets"))
    _make_dir_link(os.path.join(proj, "assets", "jump"), outside)
    assert not os.path.islink(os.path.join(proj, "assets", "jump"))  # đúng là junction, không phải symlink
    out = gate.audit_assets(proj)
    assert {"path": "assets/jump", "problem": "liên kết mềm không được kiểm"} in out["findings"]
    assert not any("secret.png" in f["path"] for f in out["findings"])


def test_is_link_fallback_is_false_for_plain_dirs_and_missing_paths(tmp_path, monkeypatch):
    monkeypatch.delattr(os.path, "isjunction", raising=False)
    assert gate._is_link(str(tmp_path)) is False
    assert gate._is_link(str(tmp_path / "không-có")) is False


def test_audit_flags_assets_dir_reached_through_a_link_in_the_middle(tmp_path):
    proj = _project(tmp_path)
    real = os.path.join(proj, "real")
    os.makedirs(os.path.join(real, "sub"))
    _write(proj, "real/sub/a.png", b"a")
    _make_dir_link(os.path.join(proj, "alias"), real)
    out = gate.audit_assets(proj, os.path.join(proj, "alias", "sub"))
    assert out["ok"] is False and out["checked"] == 0
    assert out["findings"] == [{"path": "alias/sub", "problem": "liên kết mềm không được kiểm"}]


def test_audit_refuses_assets_dir_reached_through_a_link_out_of_project(tmp_path):
    proj = _project(tmp_path)
    outside = tmp_path / "outside"
    (outside / "assets").mkdir(parents=True)
    (outside / "assets" / "a.png").write_bytes(b"a")
    _make_dir_link(os.path.join(proj, "x"), outside)
    with pytest.raises(ContractError, match="nằm trong project"):
        gate.audit_assets(proj, os.path.join(proj, "x", "assets"))


def test_audit_flags_link_assets_root_even_with_trailing_separator(tmp_path):
    proj = _project(tmp_path)
    real = os.path.join(proj, "real")
    os.makedirs(real)
    _make_dir_link(os.path.join(proj, "assets"), real)
    out = gate.audit_assets(proj, os.path.join(proj, "assets") + os.sep)
    assert out["findings"] == [{"path": "assets", "problem": "liên kết mềm không được kiểm"}]


def test_audit_accepts_assets_dir_with_trailing_separator_and_dot_segments(tmp_path):
    proj = _project(tmp_path)
    _write(proj, "assets/a.png", b"a")
    _declare(proj, _asset(path="assets/a.png"))
    for variant in (os.path.join(proj, "assets") + os.sep, os.path.join(proj, ".", "assets"), os.path.join(proj, "x", "..", "assets")):
        assert gate.audit_assets(proj, variant) == {"ok": True, "checked": 1, "findings": []}


# ------------------------------------------------- vòng sửa 3: tệp chưa khai cũng được so hash

@pytest.mark.parametrize("name", ["looks_mine.png", ".looks_mine.png"])
def test_audit_hashes_undeclared_files_too(tmp_path, name):
    proj = _project(tmp_path)
    frame = b"\x89PNG khung 1000ms"
    _write(proj, "evidence/frames/frame_001000.png", frame)
    _write(proj, f"assets/{name}", frame)
    out = gate.audit_assets(proj)
    problems = [f["problem"] for f in out["findings"] if f["path"] == f"assets/{name}"]
    assert out["ok"] is False
    assert ("tệp ẩn chưa khai" if name.startswith(".") else "chưa khai trong assets") in problems
    assert "trùng byte với tệp mẫu evidence/frames/frame_001000.png" in problems
    assert len(problems) == 2


def test_audit_undeclared_unique_file_gets_only_the_undeclared_finding(tmp_path):
    proj = _project(tmp_path)
    _write(proj, "evidence/frames/frame_001000.png", b"mau")
    _write(proj, "assets/own.png", b"khac")
    out = gate.audit_assets(proj)
    assert [f["problem"] for f in out["findings"]] == ["chưa khai trong assets"]


# ------------------------------------------------- vòng sửa 4: băm đã ghi trong hồ sơ

def _record_hash(proj, section, key, value):
    prov = gate.load_provenance(proj)
    prov[section] = dict(prov.get(section) or {}, **{key: value})
    gate.save_provenance(proj, prov)


@pytest.mark.parametrize("section, label", [("reference", "reference.local_file"), ("fetch", "fetch.file")])
def test_audit_matches_hash_recorded_in_provenance(tmp_path, section, label):
    proj = _project(tmp_path)
    payload = b"tep mau dua bang --file"
    _record_hash(proj, section, "sha256", hashlib.sha256(payload).hexdigest().upper())  # chữ hoa vẫn khớp
    _write(proj, "assets/copy.mp4", payload)
    _declare(proj, _asset(path="assets/copy.mp4", origin="user"))
    out = gate.audit_assets(proj)
    assert out["ok"] is False
    assert [f["problem"] for f in out["findings"]] == [f"trùng byte với tệp mẫu ({label})"]


@pytest.mark.parametrize("bad", [None, "", "xyz", "ab" * 31, "g" * 64, 123, ["a"]])
def test_audit_ignores_malformed_recorded_hash(tmp_path, bad):
    proj = _project(tmp_path)
    _write(proj, "assets/a.mp4", b"a")
    _declare(proj, _asset(path="assets/a.mp4"))
    _record_hash(proj, "reference", "sha256", bad)
    assert gate.audit_assets(proj) == {"ok": True, "checked": 1, "findings": []}


def test_audit_prefers_real_file_name_over_recorded_label(tmp_path):
    proj = _project(tmp_path)
    payload = b"tep"
    _write(proj, "source/reference.mp4", payload)
    _record_hash(proj, "reference", "sha256", hashlib.sha256(payload).hexdigest())
    _write(proj, "assets/copy.mp4", payload)
    _declare(proj, _asset(path="assets/copy.mp4"))
    assert [f["problem"] for f in gate.audit_assets(proj)["findings"]] == ["trùng byte với tệp mẫu source/reference.mp4"]


# ------------------------------------------------- TK12 sửa 1: liên kết lồng trong source/, evidence/

@pytest.mark.parametrize("rel", ["source/clips", "evidence/frames/jump", "evidence/jump"])
def test_audit_flags_nested_link_inside_reference_dirs(tmp_path, rel):
    proj = _project(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    payload = b"mau nam ngoai"
    (outside / "ref.bin").write_bytes(payload)
    link = os.path.join(proj, *rel.split("/"))
    os.makedirs(os.path.dirname(link), exist_ok=True)
    _make_dir_link(link, outside)
    _write(proj, "assets/mine.bin", payload)
    _declare(proj, _asset(path="assets/mine.bin"))
    out = gate.audit_assets(proj)
    assert out["ok"] is False
    assert {"path": rel, "problem": "liên kết mềm không được kiểm"} in out["findings"]
