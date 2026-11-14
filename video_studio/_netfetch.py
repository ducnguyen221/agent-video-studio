# -*- coding: utf-8 -*-
"""_netfetch.py — tải HTTP(S) công khai an toàn cho đầu vào ngoài (RQ-033).

Một trách nhiệm: lấy về tối đa `max_bytes` từ một URL mà KHÔNG gọi vào mạng nội bộ.
  - phân giải tên máy MỘT lần, kiểm MỌI địa chỉ bằng bảng chặn tường minh, rồi kết nối tới đúng IP đã kiểm
    (không để `urlopen` phân giải lại → chống DNS rebinding); HTTPS bọc TLS với tên máy gốc (SNI + kiểm chứng chỉ);
  - chuyển hướng tự theo, MỖI bước kiểm lại đủ các luật TRƯỚC khi kết nối (SSRF mù qua `Location`);
  - trần byte và hạn tổng thời gian; vượt thì từ chối, không cắt cụt im lặng;
  - host không phân giải được thì từ chối (đóng).
Không dùng biến proxy: ghim IP và proxy loại trừ nhau.
Bộ phân giải (`resolver`) và bộ kết nối (`connector`) tiêm được để test không ra mạng ngoài.
"""
import http.client
import ipaddress
import socket
import ssl
import time
import urllib.parse

MAX_URL_LEN = 2048
REDIRECT_STATUS = (301, 302, 303, 307, 308)

# Danh sách chặn TƯỜNG MINH, không dựa vào `is_global`/`is_private` của `ipaddress` (bảng đó đổi theo bản Python:
# CPython 3.10.11 coi 192.0.0.8 là global, trước bản vá CVE-2024-4032). Nguồn: IANA IPv4 Special-Purpose Address
# Registry và IANA IPv6 Special-Purpose Address Registry (iana.org/assignments/iana-ipv4-special-registry,
# iana-ipv6-special-registry), cộng khối reserved/multicast. Cờ của `ipaddress` vẫn được kiểm thêm, không thay thế.
# Bảng này dùng chung với `reference/gate.py` (một nguồn).
_BLOCKED_V4 = tuple(ipaddress.ip_network(n) for n in (
    "0.0.0.0/8", "10.0.0.0/8", "100.64.0.0/10", "127.0.0.0/8", "169.254.0.0/16", "172.16.0.0/12",
    "192.0.0.0/24", "192.0.2.0/24", "192.31.196.0/24", "192.52.193.0/24", "192.88.99.0/24", "192.168.0.0/16",
    "192.175.48.0/24", "198.18.0.0/15", "198.51.100.0/24", "203.0.113.0/24", "224.0.0.0/4", "240.0.0.0/4",
    "255.255.255.255/32"))
# `::ffff:0:0/96` (IPv4-mapped) có trong bảng cho đủ, nhưng địa chỉ mapped được gỡ ra và kiểm bằng bảng IPv4
# TRƯỚC khi tới đây, nên `::ffff:8.8.8.8` vẫn qua còn `::ffff:127.0.0.1` thì bị chặn.
# `fec0::/10` (site-local cũ) đã bỏ khỏi registry (RFC 3879) nhưng chặn cho chắc.
# `::/96` (IPv4-compatible `::a.b.c.d`) mang IPv4 nội bộ nhưng `is_global` của `ipaddress` vẫn báo True.
_BLOCKED_V6 = tuple(ipaddress.ip_network(n) for n in (
    "::/96", "::/128", "::1/128", "::ffff:0:0/96", "::ffff:0:0:0/96", "64:ff9b::/96", "64:ff9b:1::/48", "100::/64",
    "2001::/23", "2001:db8::/32", "2002::/16", "3fff::/20", "5f00::/16", "fc00::/7", "fe80::/10", "fec0::/10",
    "ff00::/8"))


def ip_is_internal(ip):
    """True nếu `ip` (đối tượng `ipaddress`) không phải địa chỉ công khai."""
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped is not None:
        ip = ip.ipv4_mapped
    blocked = _BLOCKED_V4 if isinstance(ip, ipaddress.IPv4Address) else _BLOCKED_V6
    return (any(ip in net for net in blocked)
            or ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved
            or ip.is_multicast or ip.is_unspecified or not ip.is_global)


class FetchError(Exception):
    """Không tải được an toàn (URL sai, địa chỉ không công khai, vượt trần, hết hạn, lỗi mạng)."""


def _now():
    return time.monotonic()


def _parse(url, allowed_hosts):
    """-> (scheme, host, port, host_header, path). `FetchError` nếu URL không được phép."""
    if not isinstance(url, str):
        raise FetchError("URL không phải chuỗi")
    url = url.strip()
    if not url:
        raise FetchError("URL rỗng")
    if len(url) > MAX_URL_LEN:
        raise FetchError(f"URL dài hơn {MAX_URL_LEN} ký tự")
    if any(ch.isspace() or ord(ch) < 32 or ord(ch) == 127 for ch in url):
        raise FetchError("URL có khoảng trắng hoặc ký tự điều khiển")
    if "\\" in url:            # bộ phân tích WHATWG coi `\` như `/`: hai bên sẽ thấy host khác nhau
        raise FetchError("URL có dấu gạch ngược")
    try:
        parts = urllib.parse.urlsplit(url)
        host = parts.hostname
        port = parts.port
    except ValueError as exc:
        raise FetchError(f"URL không hợp lệ: {exc}") from None
    scheme = parts.scheme.lower()
    if scheme not in ("http", "https"):
        raise FetchError("chỉ nhận URL http/https")
    if "@" in parts.netloc:
        raise FetchError("URL có thông tin đăng nhập (user@host)")
    host = (host or "").lower().rstrip(".")
    if not host:
        raise FetchError("URL thiếu tên máy")
    if port is not None and not 1 <= port <= 65535:
        raise FetchError(f"cổng {port} không hợp lệ")
    if allowed_hosts is not None:
        if scheme != "https":
            raise FetchError("máy này chỉ nhận https")
        if host not in {h.lower().rstrip(".") for h in allowed_hosts}:
            raise FetchError(f"máy {host} không nằm trong danh sách được phép")
    default = 443 if scheme == "https" else 80
    eff_port = port or default
    shown = f"[{host}]" if ":" in host else host
    host_header = shown if eff_port == default else f"{shown}:{eff_port}"
    path = parts.path or "/"
    if parts.query:
        path += "?" + parts.query
    return scheme, host, eff_port, host_header, path


def _default_resolver(host, port):
    seen = []
    for info in socket.getaddrinfo(host, port, type=socket.SOCK_STREAM):
        if info[4][0] not in seen:
            seen.append(info[4][0])
    return seen


class _PinnedConnection(http.client.HTTPConnection):
    """Kết nối tới IP đã ghim; HTTPS dùng tên máy GỐC cho SNI và kiểm chứng chỉ."""

    def __init__(self, scheme, host, ip, port, timeout):
        super().__init__(host, port, timeout=timeout)
        self._ip, self._tls, self._name = ip, scheme == "https", host

    def connect(self):
        sock = socket.create_connection((self._ip, self.port), self.timeout)
        if self._tls:
            ctx = ssl.create_default_context()
            try:
                sock = ctx.wrap_socket(sock, server_hostname=self._name)
            except Exception:
                sock.close()
                raise
        self.sock = sock


def _default_connector(scheme, host, ip, port, timeout):
    return _PinnedConnection(scheme, host, ip, port, timeout)


def _addresses(host, port, resolver):
    """Mọi địa chỉ của `host`, đã kiểm công khai; phân giải đúng MỘT lần."""
    try:
        ips = [ipaddress.ip_address(host)]
    except ValueError:
        try:
            raw = resolver(host, port)
        except (OSError, ValueError) as exc:
            raise FetchError(f"không phân giải được {host}: {type(exc).__name__}") from None
        try:
            ips = [ipaddress.ip_address(str(i).split("%", 1)[0]) for i in raw]
        except ValueError:
            raise FetchError(f"địa chỉ của {host} không hợp lệ") from None
    if not ips:
        raise FetchError(f"không phân giải được {host}")
    for ip in ips:
        if ip_is_internal(ip):
            raise FetchError(f"{host} → {ip} không phải máy công khai")
    return [str(i) for i in ips]


def _read_body(resp, max_bytes, deadline):
    chunks, total = [], 0
    while True:
        if _now() > deadline:
            raise FetchError("quá hạn tổng thời gian tải")
        chunk = resp.read(min(65536, max_bytes + 1 - total))
        if not chunk:
            return b"".join(chunks)
        total += len(chunk)
        chunks.append(chunk)
        if total > max_bytes:
            raise FetchError(f"phản hồi vượt trần {max_bytes} byte")


def fetch_public(url, *, max_bytes, timeout=20, total_deadline=60, headers=None, allowed_hosts=None,
                 max_redirects=3, resolver=None, connector=None):
    """Tải `url` công khai. -> (url cuối, content-type chữ thường, bytes). `FetchError` khi không an toàn/không tải được.

    `allowed_hosts`: `None` = mọi máy công khai; còn lại = chỉ các tên máy này (khớp nguyên tên, chỉ https),
    kiểm lại ở mỗi chuyển hướng. `resolver(host, port) -> [ip]` và `connector(scheme, host, ip, port, timeout)`
    được tra lúc gọi."""
    resolver = resolver or _default_resolver
    connector = connector or _default_connector
    deadline = _now() + total_deadline
    current = url
    for _hop in range(max_redirects + 1):
        scheme, host, port, host_header, path = _parse(current, allowed_hosts)
        ips = _addresses(host, port, resolver)
        req_headers = {"Host": host_header, "Connection": "close", **(headers or {})}
        resp, conn, last = None, None, None
        for ip in ips:
            conn = connector(scheme, host, ip, port, max(1, min(timeout, deadline - _now())))
            try:
                conn.request("GET", path, headers=req_headers)
                resp = conn.getresponse()
                break
            except (OSError, http.client.HTTPException) as exc:
                last = exc
                conn.close()
                conn = None
        if resp is None:
            raise FetchError(f"không kết nối được {host}: {type(last).__name__}")
        try:
            status = resp.status
            if status in REDIRECT_STATUS:
                location = (resp.getheader("Location") or "").strip()
                if not location:
                    raise FetchError(f"chuyển hướng {status} thiếu Location")
                current = urllib.parse.urljoin(current, location)
                continue
            if not 200 <= status < 300:
                raise FetchError(f"máy trả mã {status}")
            declared = resp.getheader("Content-Length")
            if declared is not None:
                try:
                    too_big = int(declared) > max_bytes
                except ValueError:
                    too_big = False
                if too_big:
                    raise FetchError(f"phản hồi khai {declared} byte, vượt trần {max_bytes}")
            data = _read_body(resp, max_bytes, deadline)
            return current, (resp.getheader("Content-Type") or "").lower(), data
        except (OSError, http.client.HTTPException) as exc:
            raise FetchError(f"đọc phản hồi từ {host} lỗi: {type(exc).__name__}") from None
        finally:
            conn.close()
    raise FetchError(f"quá {max_redirects} lần chuyển hướng")
