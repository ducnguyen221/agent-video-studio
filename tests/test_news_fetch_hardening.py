"""Ảnh tin tải qua `_netfetch.fetch_public` (RQ-033, TK2): không chuyển hướng/IP nội bộ, có trần, B-ROLL và
API Openverse cũng đi qua cổng tải. Không ra mạng ngoài: bộ phân giải và bộ kết nối được thay."""
import json

import pytest

PNG = b"\x89PNG" + b"0" * 5000


class _Resp:
    def __init__(self, status=200, headers=None, body=b""):
        self.status = status
        self._h = {k.lower(): v for k, v in (headers or {}).items()}
        self._body, self.pos = body, 0

    def getheader(self, name, default=None):
        return self._h.get(name.lower(), default)

    def read(self, amt=None):
        end = len(self._body) if amt is None else min(len(self._body), self.pos + amt)
        chunk, self.pos = self._body[self.pos:end], end
        return chunk


def _wire(news, monkeypatch, routes, ips=None):
    """Thay phân giải + kết nối mặc định của `_netfetch`. `routes[(host, path)] -> _Resp`. -> nhật ký kết nối."""
    log = []

    def resolver(host, port):
        if ips and host in ips:
            return ips[host]
        return ["93.184.216.34"]

    class Conn:
        def __init__(self, scheme, host, ip, port, timeout):
            self.host, self.ip, self.path = host, ip, None

        def request(self, method, path, headers=None):
            self.path = path
            log.append((self.host, self.ip, path))

        def getresponse(self):
            return routes[(self.host, self.path)]

        def close(self):
            pass

    monkeypatch.setattr(news._netfetch, "_default_resolver", resolver)
    monkeypatch.setattr(news._netfetch, "_default_connector", Conn)
    return log


def test_download_images_blocks_redirect_to_internal_before_connecting(news, monkeypatch, tmp_path, capsys):
    routes = {("img.example.com", "/a.png"): _Resp(302, {"Location": "http://169.254.169.254/latest"})}
    log = _wire(news, monkeypatch, routes, ips={"169.254.169.254": ["169.254.169.254"]})
    got = news._download_images(["https://img.example.com/a.png"], str(tmp_path / "d"), 1)
    assert got == []
    assert [h for h, _ip, _p in log] == ["img.example.com"]         # đích nội bộ không được kết nối
    assert "[warn] image 1/0 bỏ" in capsys.readouterr().out
    assert not list((tmp_path / "d").glob("*"))


def test_download_images_pins_the_resolved_address(news, monkeypatch, tmp_path):
    routes = {("img.example.com", "/a.png"): _Resp(200, {"Content-Type": "image/png"}, PNG)}
    log = _wire(news, monkeypatch, routes)
    got = news._download_images(["https://img.example.com/a.png"], str(tmp_path / "d"), 1)
    assert got == ["img/s1_0.png"] and log == [("img.example.com", "93.184.216.34", "/a.png")]


def test_download_images_over_cap_is_rejected_not_truncated(news, monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(news, "IMAGE_MAX_BYTES", 6000)
    routes = {("img.example.com", "/a.png"): _Resp(200, {"Content-Type": "image/png"}, b"\x89PNG" + b"0" * 7000)}
    _wire(news, monkeypatch, routes)
    assert news._download_images(["https://img.example.com/a.png"], str(tmp_path / "d"), 1) == []
    assert "[warn] image 1/0 bỏ" in capsys.readouterr().out
    assert not list((tmp_path / "d").glob("s1_0*"))


def test_download_images_unresolvable_host_is_dropped(news, monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(news._netfetch, "_default_resolver", lambda h, p: (_ for _ in ()).throw(OSError("x")))
    assert news._download_images(["https://khong-co.example/a.png"], str(tmp_path / "d"), 1) == []
    assert "bỏ" in capsys.readouterr().out


def test_public_http_url_blocks_nat64_and_unresolvable(news, monkeypatch):
    monkeypatch.setattr(news.socket, "getaddrinfo",
                        lambda h, *a, **k: [(0, 0, 0, "", ("64:ff9b::7f00:1", 0))])
    assert news._public_http_url("https://x.example/a.png") is False        # RF29
    monkeypatch.setattr(news.socket, "getaddrinfo", lambda *a, **k: (_ for _ in ()).throw(OSError("x")))
    assert news._public_http_url("https://x.example/a.png") is False        # CQ3: đóng, không "cho qua"


def _openverse(items):
    return _Resp(200, {"Content-Type": "application/json"}, json.dumps({"results": items}).encode())


def test_broll_openverse_api_goes_through_fetch_with_host_allowlist(news, monkeypatch, tmp_path):
    seen = {}

    def fake(url, **kw):
        seen["api"] = (url, kw)
        return url, "application/json", json.dumps({"results": []}).encode()

    monkeypatch.setattr(news._netfetch, "fetch_public", fake)
    assert news._broll_image("hà nội", str(tmp_path / "b.jpg")) is None
    url, kw = seen["api"]
    assert url.startswith("https://api.openverse.org/v1/images/")
    assert kw["allowed_hosts"] == ("api.openverse.org",) and kw["max_bytes"] == 2 << 20


def test_broll_image_url_from_openverse_goes_through_fetch(news, monkeypatch, tmp_path):
    calls = []

    def fake(url, **kw):
        calls.append((url, kw.get("max_bytes"), kw.get("allowed_hosts")))
        if "openverse" in url:
            item = {"url": "http://127.0.0.1/a.jpg", "width": 2000, "creator": "x"}
            return url, "application/json", json.dumps({"results": [item]}).encode()
        raise news._netfetch.FetchError("không phải máy công khai")

    monkeypatch.setattr(news._netfetch, "fetch_public", fake)
    assert news._broll_image("q", str(tmp_path / "b.jpg")) is None
    assert calls[1][0] == "http://127.0.0.1/a.jpg"                         # đi qua cổng tải, không urlopen
    assert calls[1][1] == news.IMAGE_MAX_BYTES and calls[1][2] is None
    assert not (tmp_path / "b.jpg").exists()


def test_broll_rejects_non_image_content_type(news, monkeypatch, tmp_path):
    def fake(url, **kw):
        if "openverse" in url:
            item = {"url": "https://img.example.com/a.jpg", "width": 2000, "creator": "x"}
            return url, "application/json", json.dumps({"results": [item]}).encode()
        return url, "text/html", b"<html>" + b"0" * 20000

    monkeypatch.setattr(news._netfetch, "fetch_public", fake)
    assert news._broll_image("q", str(tmp_path / "b.jpg")) is None
    assert not (tmp_path / "b.jpg").exists()


def test_broll_image_saves_a_valid_image(news, monkeypatch, tmp_path):
    def fake(url, **kw):
        if "openverse" in url:
            item = {"url": "https://img.example.com/a.jpg", "width": 2000, "creator": "x"}
            return url, "application/json", json.dumps({"results": [item]}).encode()
        return url, "image/jpeg", b"\xff\xd8" + b"0" * 20000

    monkeypatch.setattr(news._netfetch, "fetch_public", fake)
    assert news._broll_image("q", str(tmp_path / "b.jpg")) == str(tmp_path / "b.jpg")
    assert (tmp_path / "b.jpg").stat().st_size == 20002


@pytest.mark.parametrize("var", ["HTTPS_PROXY", "HTTP_PROXY"])
def test_proxy_hint_in_warning_when_connection_fails(news, monkeypatch, tmp_path, capsys, var):
    monkeypatch.setenv(var, "http://proxy.local:3128")

    def fake(url, **kw):
        raise news._netfetch.FetchError("không kết nối được img.example.com: OSError")

    monkeypatch.setattr(news._netfetch, "fetch_public", fake)
    assert news._download_images(["https://img.example.com/a.png"], str(tmp_path / "d"), 1) == []
    assert "không dùng proxy" in capsys.readouterr().out
