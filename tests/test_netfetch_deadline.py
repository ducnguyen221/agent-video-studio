"""Hạn tổng thời gian tải với socket THẬT trên loopback, URL không ASCII, không hạ https xuống http
(RQ-033, TK1; sửa phát hiện của security review: máy chủ nhỏ giọt không được kéo dài quá hạn)."""
import socket
import threading
import time

import pytest

from video_studio import _netfetch as nf

PUBLIC = "93.184.216.34"


@pytest.fixture
def loopback_ok(monkeypatch):
    monkeypatch.setattr(nf, "ip_is_internal", lambda ip: False)     # chỉ cho test: đích là loopback


def _serve(handler):
    srv = socket.socket()
    srv.bind(("127.0.0.1", 0))
    srv.listen(1)

    def run():
        try:
            conn, _ = srv.accept()
            try:
                conn.recv(4096)
                handler(conn)
            except OSError:
                pass
            finally:
                conn.close()
        finally:
            srv.close()
    threading.Thread(target=run, daemon=True).start()
    return srv.getsockname()[1]


def _fetch(port, **kw):
    return nf.fetch_public(f"http://example.test:{port}/a.png", max_bytes=10 ** 6,
                           resolver=lambda h, p: ["127.0.0.1"], **kw)


def test_trickling_body_is_cut_at_the_total_deadline(loopback_ok):
    def handler(conn):
        conn.sendall(b"HTTP/1.1 200 OK\r\nContent-Type: image/png\r\n\r\n")
        for _ in range(60):
            conn.sendall(b"x")                                      # một byte mỗi 0,3 giây
            time.sleep(0.3)
    port = _serve(handler)
    t0 = time.monotonic()
    with pytest.raises(nf.FetchError):
        _fetch(port, total_deadline=1.0)
    assert time.monotonic() - t0 < 4.0


def test_trickling_headers_are_cut_at_the_total_deadline(loopback_ok):
    def handler(conn):
        for ch in b"HTTP/1.1 200 OK\r\nContent-Type: image/png\r\n":
            conn.sendall(bytes([ch]))                               # tiêu đề nhỏ giọt, không bao giờ kết thúc
            time.sleep(0.3)
    port = _serve(handler)
    t0 = time.monotonic()
    with pytest.raises(nf.FetchError):
        _fetch(port, total_deadline=1.0)
    assert time.monotonic() - t0 < 4.0


def test_fast_response_inside_the_deadline_still_works(loopback_ok):
    def handler(conn):
        conn.sendall(b"HTTP/1.1 200 OK\r\nContent-Type: image/png\r\nContent-Length: 3\r\nConnection: close\r\n\r\nabc")
    port = _serve(handler)
    url, ct, data = _fetch(port, total_deadline=5.0)
    assert data == b"abc" and ct == "image/png"


# ── URL không ASCII (RF3) ────────────────────────────────────────────────────────────────

class _Resp:
    status = 200

    def __init__(self):
        self.sent = False

    def getheader(self, name, default=None):
        return {"content-type": "image/png"}.get(name.lower(), default)

    def read(self, amt=None):
        if self.sent:
            return b""
        self.sent = True
        return b"ok"


def _conn_factory(log):
    class Conn:
        def __init__(self, scheme, host, ip, port, timeout):
            self.host = host

        def request(self, method, path, headers=None):
            log.append((self.host, path, headers["Host"]))

        def getresponse(self):
            return _Resp()

        def close(self):
            pass
    return Conn


def test_non_ascii_path_and_host_do_not_raise_unicode_errors():
    log = []
    out = nf.fetch_public("https://bücher.example/ảnh đẹp.png?từ=khóa".replace(" ", "%20"), max_bytes=10,
                          resolver=lambda h, p: [PUBLIC], connector=_conn_factory(log))
    assert out[2] == b"ok"
    host, path, host_header = log[0]
    assert host == "xn--bcher-kva.example" and host_header == "xn--bcher-kva.example"
    assert path.isascii() and path.startswith("/%E1%BA%A3nh%20") and "t%E1%BB%AB=kh%C3%B3a" in path


def test_unencodable_host_is_a_fetch_error_not_a_unicode_error():
    with pytest.raises(nf.FetchError):
        nf.fetch_public("https://" + "é" * 80 + ".example/a.png", max_bytes=10,
                        resolver=lambda h, p: [PUBLIC], connector=_conn_factory([]))


# ── không hạ https xuống http (RF7) ──────────────────────────────────────────────────────

def test_https_to_http_redirect_is_refused():
    class Redirect(_Resp):
        status = 302

        def getheader(self, name, default=None):
            return "http://img.example.com/a.png" if name.lower() == "location" else default

    log = []

    class Conn:
        def __init__(self, scheme, host, ip, port, timeout):
            log.append(scheme)

        def request(self, *a, **k):
            pass

        def getresponse(self):
            return Redirect()

        def close(self):
            pass
    with pytest.raises(nf.FetchError):
        nf.fetch_public("https://img.example.com/a.png", max_bytes=10, resolver=lambda h, p: [PUBLIC], connector=Conn)
    assert log == ["https"]                                         # không kết nối tới http


def test_http_to_https_to_http_is_refused_at_the_second_downgrade():
    class Redirect(_Resp):
        status = 302

        def __init__(self, to):
            super().__init__()
            self.to = to

        def getheader(self, name, default=None):
            return self.to if name.lower() == "location" else default

    queue = [Redirect("https://img.example.com/b"), Redirect("http://img.example.com/c")]
    log = []

    class Conn:
        def __init__(self, scheme, host, ip, port, timeout):
            log.append(scheme)

        def request(self, *a, **k):
            pass

        def getresponse(self):
            return queue.pop(0)

        def close(self):
            pass
    with pytest.raises(nf.FetchError):
        nf.fetch_public("http://img.example.com/a", max_bytes=10, resolver=lambda h, p: [PUBLIC], connector=Conn)
    assert log == ["http", "https"]


# ── vòng 2 của security review: thân chunked + Connection: close, thân cụt ───────────────

def test_chunked_close_body_with_slow_chunk_size_line_is_cut_at_the_deadline(loopback_ok):
    def handler(conn):
        conn.sendall(b"HTTP/1.1 200 OK\r\nContent-Type: image/png\r\nTransfer-Encoding: chunked\r\n"
                     b"Connection: close\r\n\r\n")
        for _ in range(60):
            conn.sendall(b"1")                                      # dòng kích thước chunk nhỏ giọt, không bao giờ xong
            time.sleep(0.3)
    port = _serve(handler)
    t0 = time.monotonic()
    with pytest.raises(nf.FetchError):
        _fetch(port, total_deadline=1.0)
    assert time.monotonic() - t0 < 4.0


def test_connection_cut_by_the_deadline_is_never_reported_as_success(loopback_ok):
    def handler(conn):
        conn.sendall(b"HTTP/1.1 200 OK\r\nContent-Type: image/png\r\nTransfer-Encoding: chunked\r\n"
                     b"Connection: close\r\n\r\n5\r\nhello\r\n")
        time.sleep(6)                                               # rồi im lặng
    port = _serve(handler)
    t0 = time.monotonic()
    with pytest.raises(nf.FetchError):
        _fetch(port, total_deadline=1.0)
    assert time.monotonic() - t0 < 4.0


def test_truncated_content_length_body_is_an_error(loopback_ok):
    def handler(conn):
        conn.sendall(b"HTTP/1.1 200 OK\r\nContent-Type: image/png\r\nContent-Length: 1000\r\nConnection: close\r\n\r\n0123456789")
    port = _serve(handler)
    with pytest.raises(nf.FetchError):
        _fetch(port, total_deadline=5.0)


class _HeaderResp(_Resp):
    def __init__(self, length):
        super().__init__()
        self.length = length

    def getheader(self, name, default=None):
        if name.lower() == "content-length":
            return self.length
        return super().getheader(name, default)


@pytest.mark.parametrize("length", ["²", "٣", "9" * 5000, "abc", "", "-1", "+5"])
def test_odd_content_length_never_leaks_a_value_error(length):
    try:
        out = nf.fetch_public("https://img.example.com/a", max_bytes=1000, resolver=lambda h, p: [PUBLIC],
                              connector=lambda *a: type("C", (), {
                                  "request": lambda self, *x, **k: None,
                                  "getresponse": lambda self: _HeaderResp(length),
                                  "close": lambda self: None})())
    except nf.FetchError:
        return                                          # từ chối cũng được; ValueError thì không
    assert out[2] == b"ok"


def test_huge_declared_content_length_is_refused_before_reading():
    with pytest.raises(nf.FetchError):
        nf.fetch_public("https://img.example.com/a", max_bytes=1000, resolver=lambda h, p: [PUBLIC],
                        connector=lambda *a: type("C", (), {
                            "request": lambda self, *x, **k: None,
                            "getresponse": lambda self: _HeaderResp("9" * 5000),
                            "close": lambda self: None})())


def test_invalid_caller_header_is_a_fetch_error(loopback_ok):
    port = _serve(lambda conn: None)
    with pytest.raises(nf.FetchError):
        _fetch(port, total_deadline=5.0, headers={"X-Test": "a\nb"})


def test_chunked_body_with_a_stale_content_length_is_not_called_truncated(loopback_ok):
    def handler(conn):
        conn.sendall(b"HTTP/1.1 200 OK\r\nContent-Type: image/png\r\nTransfer-Encoding: chunked\r\n"
                     b"Content-Length: 3\r\nConnection: close\r\n\r\n5\r\nhello\r\n0\r\n\r\n")
    port = _serve(handler)
    assert _fetch(port, total_deadline=5.0)[2] == b"hello"


def test_zero_total_deadline_is_refused():
    with pytest.raises(nf.FetchError):
        nf.fetch_public("https://img.example.com/a", max_bytes=10, total_deadline=0,
                        resolver=lambda h, p: [PUBLIC], connector=_conn_factory([]))
