"""`repo_today._get` chỉ gọi máy GitHub, có trần 8 MiB (RQ-033, TK3). Không ra mạng ngoài."""
import pytest

from video_studio import _netfetch
from video_studio.templates.news import repo_today


def _wire(monkeypatch, status_body=(200, b"<html>ok</html>")):
    seen = []

    class Resp:
        status = status_body[0]
        pos = 0

        def getheader(self, name, default=None):
            return default

        def read(self, amt=None):
            chunk = status_body[1][self.pos:self.pos + (amt or len(status_body[1]))]
            self.pos += len(chunk)
            return chunk

    class Conn:
        def __init__(self, scheme, host, ip, port, timeout):
            seen.append((scheme, host, ip))

        def request(self, *a, **k):
            pass

        def getresponse(self):
            return Resp()

        def close(self):
            pass

    monkeypatch.setattr(_netfetch, "_default_resolver", lambda h, p: ["140.82.112.3"])
    monkeypatch.setattr(_netfetch, "_default_connector", Conn)
    return seen


@pytest.mark.parametrize("url", [
    "https://github.com/trending?since=daily",
    "https://api.github.com/repos/o/r",
    "https://raw.githubusercontent.com/o/r/main/README.md"])
def test_get_accepts_the_three_github_hosts(monkeypatch, url):
    seen = _wire(monkeypatch)
    assert repo_today._get(url) == "<html>ok</html>"
    assert seen[0][0] == "https"


@pytest.mark.parametrize("url", [
    "https://evilgithub.com/x", "https://x.github.com/x", "https://github.com.evil.example/x",
    "http://github.com/x", "https://example.com/x", "http://127.0.0.1/x"])
def test_get_rejects_other_hosts_and_http(monkeypatch, url):
    seen = _wire(monkeypatch)
    with pytest.raises(_netfetch.FetchError):
        repo_today._get(url)
    assert seen == []


def test_get_caps_8_mib(monkeypatch):
    _wire(monkeypatch, (200, b"x" * ((8 << 20) + 1)))
    with pytest.raises(_netfetch.FetchError):
        repo_today._get("https://github.com/trending")


def test_get_decodes_utf8_with_replacement(monkeypatch):
    _wire(monkeypatch, (200, "Việt".encode("utf-8") + b"\xff"))
    assert repo_today._get("https://api.github.com/repos/o/r") == "Việt�"
