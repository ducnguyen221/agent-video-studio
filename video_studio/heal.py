"""heal.py — thang tự chữa + gói chẩn đoán khi `probe` báo `RENDER_STUCK` (P1-25).

## Vì sao có file này

Mac mini 02/10/2026 18:30: mọi project HyperFrames hỏng `Navigation timeout` ở frame 0, kể cả
mẫu từng dựng được; Chromium/puppeteer mở cùng trang bình thường; khởi động lại máy là hết và
SAU đó không tái hiện được. Dấu hiệu duy nhất ghi lại được là `WindowServer` 21–35 % CPU lúc máy
rảnh — ghi bằng tay, sau khi đã khởi động lại thì không còn gì để soi. Nguyên nhân gốc vẫn chưa
rõ. Hai thứ thiếu: **chứng cứ chụp ngay lúc kẹt**, và **một thang chữa rẻ** thử trước khi bắt
người khởi động lại máy.

## Thang (chỉ chạy khi lần probe đầu ra `RENDER_STUCK`)

1. Chụp **gói chẩn đoán** vào `<diag-dir>/<YYYYmmdd-HHMMSS>/` (xem `diag_bundle`).
2. Giết tiến trình Chrome/HyperFrames **mồ côi của chính user** (cha đã chết: POSIX `ppid == 1`,
   Windows cha không còn sống; Windows đối chiếu SID chủ tiến trình) — cả cây con của nó. Không đụng tiến trình còn cha: đó có thể là
   một lượt dựng khác đang chạy thật.
3. Xoá thư mục tạm `puppeteer_dev_chrome_profile-*` / `hyperframes*` / `video-studio-probe-*`
   cũ hơn 1 giờ (lượt đang chạy luôn có profile mới hơn thế).
4. Chờ `waits[0]` (60 s) → probe lại. Qua ⇒ xong, mã 0, có ghi đã tự chữa ở bước nào.
5. Vẫn kẹt ⇒ chờ `waits[1]` (600 s) → probe lần cuối.
6. Hết thang mới ném `RENDER_STUCK:` "khởi động lại máy", kèm đường gói chẩn đoán.

Hỏng kiểu KHÁC `RENDER_STUCK` ở bất kỳ lần nào ⇒ ném nguyên lỗi đó: thang này chữa máy kẹt,
không chữa cài đặt hỏng.

## Secret không vào gói

Gói chẩn đoán KHÔNG ghi biến môi trường, không chép `.env`, không ghi dòng lệnh đầy đủ của tiến
trình nào (dòng lệnh có thể mang token): danh sách tiến trình chỉ có pid · cha · tên chương trình
· CPU/bộ nhớ · tuổi. Mọi văn bản ghi ra còn đi qua `_che` — ba lớp: giá trị của biến môi trường
có tên như secret (đọc trong bộ nhớ chỉ để che), tên khoá nhạy cảm, hình dạng token.
"""
from __future__ import annotations

import datetime as _dt
import fnmatch
import getpass
import json
import os
import platform
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time

from . import contract, render
from .contract import EngineError

STUCK = render.STUCK_PREFIX
HINT_REBOOT = "khởi động lại máy rồi chạy lại"
WAITS = (60, 600)                 # giây chờ trước lần probe 2 và 3
PROFILE_AGE = 3600                # thư mục tạm cũ hơn ngần này giây mới xoá
PROFILE_GLOBS = ("puppeteer_dev_chrome_profile-*", "hyperframes*", "video-studio-probe-*")
# `node -e …` / `node.exe" -e …` (Windows có nháy quanh đường chương trình): script nội tuyến của
# bộ cập nhật nền / telemetry HyperFrames — không phải lượt dựng.
_NODE_E = re.compile(r'node(?:\.exe)?"?\s+-e\b')
PROFILE_SCAN_MAX = 5000          # số mục tối đa khi đo mtime mới nhất (đệ quy) của một thư mục tạm
CMD_TIMEOUT = 30                  # giây cho mỗi lệnh chụp chẩn đoán
LOG_SHOW_TIMEOUT = 120            # `log show` 10 phút có thể chậm
TRAN_FILE = 5 * 1024 * 1024       # mỗi file trong gói tối đa 5 MB

_NT = os.name == "nt"             # quy ước "mồ côi" theo hệ (test đổi được)

# ── che secret: BA LỚP, chạy trên MỌI văn bản trước khi ghi vào gói ──────────────────────
# Lớp 1 — theo GIÁ TRỊ: giá trị của biến môi trường có tên trông như secret (đọc trong bộ nhớ,
#          không ghi ra đâu) bị thay ở mọi chỗ nó xuất hiện. Mẫu nào chưa nghĩ tới cũng không lọt.
# Lớp 2 — theo TÊN KHOÁ: `khoá=giá trị`, `khoá: giá trị`, `"khoá": "giá trị có cách"`, `'khoá':
#          '…'`, `khoá%3D…` (mã hoá URL), cờ `--khoá giá trị`; khoá CHỨA từ nhạy cảm ở bất kỳ vị
#          trí nào (`AWS_SECRET_ACCESS_KEY`, `x-auth`, `refresh_token`…); dòng header
#          `Cookie:`/`Set-Cookie:`/`Authorization:` che tới hết dòng; mật khẩu trong URL
#          `scheme://user:pass@host`.
# Lớp 3 — theo HÌNH DẠNG: khối PEM private key, JWT, khoá AWS/Google, token GitHub/GitLab/npm/
#          OpenAI/Slack/Google OAuth, token bot Telegram, hex ≥ 40 ký tự.
# HIỆU NĂNG LÀ YÊU CẦU, không phải tối ưu (review 04/10): bản trước có `[\w.-]*` không neo ⇒ quay
# lui bậc hai — 40 KB chữ liền mất 74 s, gói 5 MB treo `--heal` đúng lúc cần chữa. Nay mọi tên khoá
# được neo ở đầu từ và có trần độ dài, giá trị có trần độ dài; văn bản bị cắt về TRAN_FILE TRƯỚC khi
# che. `tests/test_heal.py` đo thời gian trên chuỗi xấu nhất.
_TU_NHAY_CAM = (r"(?:token|secret|pass(?:wd|word|phrase)|pwd|api[_-]?key|access[_-]?key"
                r"|private[_-]?key|client[_-]?secret|credential|cookie|authorization|auth(?![a-z])"
                r"|(?<![a-z])sig(?![a-z])|signature)")
_KHOA_TRAN = r"[\w.-]{0,40}?" + _TU_NHAY_CAM + r"[\w.-]{0,40}"
_KHOA = r"(?<![\w.-])" + _KHOA_TRAN       # neo đầu từ: không quay lui giữa một dải chữ dài
_SEP = r"(?::=|=>|[=:]|%3d)"               # `=` `:` `:=` `=>` `%3D` (mã hoá URL)
# Giá trị trong nháy: tới đúng nháy ĐÓNG cùng loại (được chứa nháy kia: "it's x"), trần 4096.
_GT_NHAY = (r"\\(?P<q2>[\"'])(?P<vq2>(?:(?!\\(?P=q2))[^\n]){1,4096})\\(?P=q2)"   # {\"k\":\"v\"}
            r"|(?P<q>[\"'])(?P<vq>(?:\\[^\n]|(?!(?P=q))[^\n\\]){1,4096})(?P=q)")   # "a\"b" — nháy thoát bên trong
# Giá trị trần: tới khoảng trắng / nháy — thà che thừa `,;}&` còn hơn để lộ đuôi secret.
_GT_TRAN = r"(?:(?:bearer|basic|token)\s+)?(?P<v>[^\s\"']{1,512})"
_CHE_KV = re.compile(r"(?i)(?P<k>\\?[\"']?" + _KHOA + r"\\?[\"']?[ \t]{0,8}" + _SEP + r"[ \t]{0,8})"
                     r"(?:" + _GT_NHAY + r"|" + _GT_TRAN + r")")
_CHE_CO = re.compile(r"(?i)(?P<k>(?<![\w-])--?" + _KHOA_TRAN + r"[ \t]{1,8})(?P<v>[^\s\-][^\s]{0,511})")
# Header (cả giữa dòng: `curl -H "Cookie: …"`) che tới HẾT DÒNG; đứng sau `.` thì không phải
# header (nhãn log macOS `[com.apple.Authorization:authd]`).
_CHE_HEADER = re.compile(r"(?i)(?P<k>(?<![\w.-])(?:set-cookie|cookie|proxy-authorization|authorization)"
                         r"[ \t]{0,8}:[ \t]{0,8})(?P<v>[^\n]{1,4096})")
_CHE_URL = re.compile(r"(?i)(?P<k>\b[a-z][a-z0-9+.-]{0,20}://[^/\s:@]{0,256}:)[^@\s/]{1,256}(?=@)")
# Mọi hình dạng neo bằng `(?<![\w-])` (không phải `\b`): `\b` khớp ngay sau `-`, nên chuỗi kiểu
# `eyJ-eyJ-…` mở một điểm bắt đầu mỗi 4 ký tự, mỗi điểm quét tới trần (review vòng 4: 4,65 s/MB).
_CHE_HINH = re.compile(
    r"-----BEGIN [A-Z ]{0,40}PRIVATE KEY(?: BLOCK)?-----(?:[A-Za-z0-9+/=\s:,.()]|-(?!----)){0,20000}"
    r"-----END [A-Z ]{0,40}PRIVATE KEY(?: BLOCK)?-----"                     # PEM/PGP (kể cả Proc-Type:)
    r"|(?i:(?<![\w-])(?:bearer|basic)[ \t]{1,8}[A-Za-z0-9._~+/=-]{8,512})"
    r"|(?<![\w-])eyJ[\w-]{10,2048}\.[\w-]{10,4096}\.[\w-]{5,2048}"          # JWT
    r"|(?<![\w-])(?:AKIA|ASIA)[0-9A-Z]{16}(?![\w-])"                      # khoá AWS
    r"|(?<![\w-])AIza[0-9A-Za-z_-]{35}"                                   # khoá Google API
    r"|(?<!\d)\d{5,12}:[A-Za-z0-9_-]{20,64}(?![\w-])"                  # token bot Telegram (kể cả `/bot123:…`)
    r"|(?<![\w-])(?:sk|ghp|gho|ghs|ghu|ghr|github_pat|glpat|npm|hf|xox[abpr]|xapp|ya29)"
    r"[-_.][A-Za-z0-9_-]{16,256}"
    r"|hooks\.slack\.com/services/[A-Za-z0-9/_-]{10,256}"                 # webhook Slack
    r"|(?<![\w-])[0-9a-fA-F]{40,512}(?![\w-])")
_TEN_BIEN_BI_MAT = re.compile(r"(?i)" + _TU_NHAY_CAM)
# Tên khớp mẫu nhưng KHÔNG phải secret: `PWD` = thư mục đang làm (shell POSIX luôn đặt) — che nó là
# xoá mọi đường dẫn dự án trong stack trace.
_TEN_KHONG_BI_MAT = {"PWD", "OLDPWD"}
GIA_TRI_TOI_THIEU = 8             # giá trị env ngắn hơn ngần này không che (tránh che "1", "true")
# Giá trị KHÔNG phải secret dù đứng sau tên khoá nhạy cảm (`"auth": true`, `OAuth: disabled`).
_GT_THUONG = {"true", "false", "null", "none", "nil", "yes", "no", "on", "off", "enabled",
              "disabled", "undefined", "required", "optional", "valid", "invalid", "loaded",
              "missing", "expired", "sha1", "sha256", "sha512", "rsa", "oauth", "oauth2", "basic",
              "bearer", "password", "<da-che>"}
# Khoá MẠNH (mật khẩu/secret thật): giá trị KHÔNG BAO GIỜ được miễn che, kể cả toàn số (PIN).
_KHOA_MANH = re.compile(r"(?i)pass|pwd|secret|private|credential|pin(?![a-z])")
_DUOI_KHOA = re.compile(r"(?i)[\"'\s]*(?::=|=>|[=:]|%3d)[\"'\s]*$")   # bỏ dấu tách khỏi tên khoá
# Nhãn hệ con trong log macOS: `[com.apple.Authorization:authd]` — không phải secret.
_NHAN_LOG = re.compile(r"[a-z][a-z0-9_.-]{0,40}\]")
_SO_VI_TRI = re.compile(r"\d{1,9}(?:[:.]\d{1,9}){0,3}[,;)}\]]?")   # `token.js:12:3`, `1.2.3`


def gia_tri_bi_mat(env=None) -> list[str]:
    """Giá trị của biến môi trường có TÊN trông như secret, dài trước — chỉ để che, không ghi ra."""
    env = os.environ if env is None else env
    ra = {str(v) for k, v in env.items()
          if str(k).upper() not in _TEN_KHONG_BI_MAT and _TEN_BIEN_BI_MAT.search(str(k))
          and len(str(v or "")) >= GIA_TRI_TOI_THIEU}
    return sorted(ra, key=len, reverse=True)


def _la_so_dem(v: str) -> bool:
    """`token_count: 123`, `cookie: 42`, `token.js:12:3`, `true` — không phải secret."""
    v = (v or "").strip()
    return (v.lower().rstrip(",;)}]") in _GT_THUONG
            or (_SO_VI_TRI.fullmatch(v) is not None and len(v.replace(":", "").replace(".", "")) < 10))


def _che_kv(m) -> str:
    k = m.group("k")
    ten = _DUOI_KHOA.sub("", k).strip("\\\"' ").upper()
    manh = _KHOA_MANH.search(ten) is not None
    if m.group("q2"):                                    # {\"k\":\"v\"}
        return k + "\\" + m.group("q2") + "<da-che>" + "\\" + m.group("q2")
    if m.group("q"):
        if not manh and _la_so_dem(m.group("vq")):
            return m.group(0)
        return k + m.group("q") + "<da-che>" + m.group("q")
    v = m.group("v") or ""
    # `PWD=/đường/dẫn` (biến shell) giữ; `Pwd=Hunter2` trong chuỗi kết nối ODBC thì che.
    if ten in _TEN_KHONG_BI_MAT and re.match(r"[/~]|[A-Za-z]:[\\/]", v):
        return m.group(0)
    if not manh and _la_so_dem(v):
        return m.group(0)
    if ten.startswith("COM.APPLE.") and _NHAN_LOG.fullmatch(v):     # [com.apple.X:authd]
        return m.group(0)
    return m.group(0)[: len(m.group(0)) - len(v)] + "<da-che>"


def _che(s: str, bi_mat=None) -> str:
    s = s or ""
    for v in (gia_tri_bi_mat() if bi_mat is None else bi_mat):
        s = s.replace(v, "<da-che>")
    s = _CHE_HINH.sub("<da-che>", s)          # PEM/JWT trước: header bên dưới che tới hết dòng
    s = _CHE_HEADER.sub(lambda m: m.group(0) if _la_so_dem(m.group("v"))
                        else m.group("k") + "<da-che>", s)
    s = _CHE_URL.sub(lambda m: m.group("k") + "<da-che>", s)
    s = _CHE_KV.sub(_che_kv, s)
    return _CHE_CO.sub(lambda m: m.group("k") + "<da-che>", s)


def _che_duoi_pem(b: bytes) -> bytes:
    """Cắt về 5 MB có thể rơi GIỮA một khối PEM: dòng BEGIN mất, thân khoá còn — che từ đầu tới END."""
    i = b.find(b"PRIVATE KEY-----")
    if i < 0:
        return b
    j = b.find(b"-----END ")
    if 0 <= j < i and b.find(b"-----BEGIN ", 0, j) < 0:
        return b"<da-che>" + b[i + len(b"PRIVATE KEY-----"):]
    return b


def _run_out(argv, timeout=CMD_TIMEOUT, run=subprocess.run) -> str | None:
    """CHỈ stdout của lệnh (None nếu không chạy được / mã ≠ 0) — để parse, không trộn stderr."""
    try:
        r = run(argv, capture_output=True, timeout=timeout)
    except (subprocess.TimeoutExpired, OSError):
        return None
    if r.returncode != 0:
        return None
    out = r.stdout or b""
    return out.decode("utf-8", "replace") if isinstance(out, bytes) else str(out)


def _run_text(argv, timeout=CMD_TIMEOUT, run=subprocess.run) -> str:
    """Chạy một lệnh chụp chẩn đoán -> văn bản (kể cả khi hỏng). Không bao giờ ném."""
    try:
        r = run(argv, capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return f"(quá {timeout}s: {' '.join(argv)})"
    except OSError as e:
        return f"(không chạy được {argv[0]}: {e})"
    out = r.stdout or b""
    err = r.stderr or b""
    if isinstance(out, bytes):
        out = out.decode("utf-8", "replace")
    if isinstance(err, bytes):
        err = err.decode("utf-8", "replace")
    head = "" if r.returncode == 0 else f"(mã {r.returncode})\n"
    return head + out + (("\n--- stderr ---\n" + err) if err.strip() else "")


# ── danh sách tiến trình (pid, ppid, tên, giờ tạo, dòng lệnh chỉ để so) ────────────────

# Windows: chỉ tiến trình CÙNG phiên đăng nhập với chính lệnh này (task "highest privileges" không
# được với sang Chrome của user khác); `Tao` = giờ tạo (FILETIME) để chống PID bị cấp lại.
_PS_WIN = ("$s = (Get-CimInstance Win32_Process -Filter \"ProcessId=$PID\").SessionId; "
           "@(Get-CimInstance Win32_Process | Where-Object { $_.SessionId -eq $s } | "
           "Select-Object ProcessId,ParentProcessId,Name,CommandLine,"
           "@{n='Tao';e={ if ($_.CreationDate) { $_.CreationDate.ToFileTimeUtc() } else { 0 } }}) "
           "| ConvertTo-Json -Compress")


def list_processes(run=subprocess.run, log=None) -> list[dict]:
    """-> [{pid, ppid, name, cmd, tao}] của user hiện tại. Rỗng (kèm một dòng log) nếu không đọc được.

    `cmd` (dòng lệnh) CHỈ dùng để nhận diện trong bộ nhớ — không bao giờ ghi ra gói. `tao` = giờ
    tạo (Windows; POSIX `None` — ở đó cha chết thì ppid đổi về 1, không có chuyện PID cấp lại).
    """
    log = log or contract.log
    ra = []
    if os.name == "nt":
        out = _run_out(["powershell", "-NoProfile", "-NonInteractive", "-Command", _PS_WIN], run=run)
        try:
            i = min(k for k in ((out or "").find("["), (out or "").find("{")) if k >= 0)
            data, _ = json.JSONDecoder().raw_decode(out[i:])
        except (ValueError, TypeError):
            log("[probe] WARN: không đọc được danh sách tiến trình (Win32_Process) — bỏ bước giết mồ côi")
            return []
        for d in data if isinstance(data, list) else [data]:
            try:
                ra.append({"pid": int(d.get("ProcessId")), "ppid": int(d.get("ParentProcessId") or 0),
                           "name": str(d.get("Name") or ""), "cmd": str(d.get("CommandLine") or ""),
                           "tao": int(d.get("Tao") or 0) or None})
            except (TypeError, ValueError, AttributeError):
                continue
        return ra
    # Hai lượt `ps`: `comm` (tên chương trình — được ghi ra gói) và `command` (dòng lệnh — chỉ để
    # nhận diện, không ghi ra đâu cả).
    uid = str(os.getuid())
    ten = {}
    for line in (_run_out(["ps", "-U", uid, "-o", "pid=,comm="], run=run) or "").splitlines():
        parts = line.strip().split(None, 1)
        if len(parts) == 2 and parts[0].isdigit():
            ten[int(parts[0])] = os.path.basename(parts[1].strip())
    out = _run_out(["ps", "-U", uid, "-o", "pid=,ppid=,command="], run=run)
    if out is None:
        log("[probe] WARN: không đọc được danh sách tiến trình (ps) — bỏ bước giết mồ côi")
        return []
    for line in out.splitlines():
        parts = line.strip().split(None, 2)
        if len(parts) < 3 or not parts[0].isdigit() or not parts[1].isdigit():
            continue
        pid = int(parts[0])
        ra.append({"pid": pid, "ppid": int(parts[1]), "name": ten.get(pid, "?"), "cmd": parts[2],
                   "tao": None})
    return ra


def _la_bo_dung(p: dict) -> bool:
    """Gốc thuộc BỘ DỰNG: Chrome headless của puppeteer/HyperFrames, hoặc node đang `hyperframes render`.

    Hẹp có chủ đích (review 04/10): HyperFrames còn đẻ tiến trình CỐ Ý tách cha — `preview
    --background`, bộ cập nhật nền `node -e`, telemetry — và chrome-devtools MCP cũng mở Chrome qua
    puppeteer (không headless). Chúng mồ côi theo thiết kế; giết chúng là phá việc của người khác.
    """
    s = (p.get("cmd") or "").lower()
    n = (p.get("name") or "").lower()
    if "chrome-headless-shell" in s or "chrome-headless-shell" in n:
        return True
    if ("chrome" in n or "chromium" in n) and "--headless" in s and "puppeteer_dev_chrome_profile" in s:
        return True
    return ("hyperframes" in s and re.search(r"\brender\b", s) is not None
            and "preview" not in s and _NODE_E.search(s) is None)


def find_orphans(procs: list[dict], self_pid: int | None = None, nt: bool | None = None) -> list[dict]:
    """Tiến trình bộ dựng MỒ CÔI + cả cây con của chúng (thứ tự: gốc trước).

    Mồ côi = cha không còn: POSIX bị nhận về `init`/`launchd` (`ppid == 1`); Windows cha không
    có trong danh sách sống, HOẶC "cha" sinh SAU con (PID của cha đã chết bị cấp lại cho tiến
    trình khác — Windows không cập nhật ParentProcessId). Cây con chỉ nhận con sinh sau cha, vì
    cùng lý do. Tiến trình còn cha (một lượt dựng khác đang chạy) KHÔNG bị đụng.
    """
    self_pid = os.getpid() if self_pid is None else self_pid
    nt = _NT if nt is None else nt
    theo_pid = {p["pid"]: p for p in procs}
    con: dict[int, list[dict]] = {}
    for p in procs:
        con.setdefault(p["ppid"], []).append(p)

    def sau(a, b):
        """a sinh SAU b? (thiếu giờ tạo ⇒ không kết luận được ⇒ False)"""
        return bool(a.get("tao") and b.get("tao") and a["tao"] > b["tao"])

    def mo_coi(p):
        if nt:
            cha = theo_pid.get(p["ppid"])
            return cha is None or sau(cha, p)
        return p["ppid"] == 1

    goc = [p for p in procs if _la_bo_dung(p) and mo_coi(p) and p["pid"] != self_pid]
    ra, da = [], set()
    hang = list(goc)
    while hang:
        p = hang.pop(0)
        if p["pid"] in da or p["pid"] == self_pid:
            continue
        da.add(p["pid"])
        ra.append(p)
        hang.extend(c for c in con.get(p["pid"], []) if not sau(p, c))
    return ra


def _sid_cua(pid: int) -> str | None:
    """SID chủ của tiến trình `pid` (Windows) qua ctypes — <1 ms/tiến trình. Không đọc được ⇒ None.

    Review 04/10: bản PowerShell `GetOwnerSid` tốn ~0,5 s/tiến trình ⇒ hơn ~35 pid là quá trần,
    đúng lúc nhiều Chrome mồ côi tích lại. Dùng `ctypes.WinDLL(...)` RIÊNG, không `ctypes.windll`
    (bộ đệm dùng chung toàn tiến trình — đặt argtypes ở đó là đổi hành vi của mã khác).
    """
    import ctypes
    from ctypes import wintypes
    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    adv = ctypes.WinDLL("advapi32", use_last_error=True)
    k32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    k32.OpenProcess.restype = wintypes.HANDLE
    k32.CloseHandle.argtypes = [wintypes.HANDLE]
    k32.LocalFree.argtypes = [ctypes.c_void_p]
    k32.LocalFree.restype = ctypes.c_void_p
    adv.OpenProcessToken.argtypes = [wintypes.HANDLE, wintypes.DWORD, ctypes.POINTER(wintypes.HANDLE)]
    adv.GetTokenInformation.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p,
                                        wintypes.DWORD, ctypes.POINTER(wintypes.DWORD)]
    adv.ConvertSidToStringSidW.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_void_p)]
    h = k32.OpenProcess(0x1000, False, int(pid))     # PROCESS_QUERY_LIMITED_INFORMATION
    if not h:
        return None
    try:
        tok = wintypes.HANDLE()
        if not adv.OpenProcessToken(h, 0x0008, ctypes.byref(tok)):  # TOKEN_QUERY
            return None
        try:
            n = wintypes.DWORD(0)
            adv.GetTokenInformation(tok, 1, None, 0, ctypes.byref(n))  # 1 = TokenUser
            if not n.value:
                return None
            buf = ctypes.create_string_buffer(n.value)
            if not adv.GetTokenInformation(tok, 1, buf, n, ctypes.byref(n)):
                return None
            psid = ctypes.cast(buf, ctypes.POINTER(ctypes.c_void_p))[0]   # TOKEN_USER.User.Sid
            chuoi = ctypes.c_void_p()
            if not adv.ConvertSidToStringSidW(psid, ctypes.byref(chuoi)):
                return None
            try:
                return ctypes.wstring_at(chuoi.value)
            finally:
                k32.LocalFree(chuoi)
        finally:
            k32.CloseHandle(tok)
    finally:
        k32.CloseHandle(h)


def chu_so_huu_windows(pids, sid_cua=None) -> tuple[str | None, dict]:
    """-> (SID của chính tiến trình này, {pid: SID chủ}). Không đọc được SID của mình ⇒ (None, {})."""
    sid_cua = sid_cua or _sid_cua
    try:
        me = sid_cua(os.getpid())
    except (OSError, AttributeError, ValueError):
        return None, {}
    if not me:
        return None, {}
    ra = {}
    for pid in pids:
        try:
            v = sid_cua(int(pid))
        except (OSError, AttributeError, ValueError):
            v = None
        if v:
            ra[int(pid)] = v
    return me, ra


def kill_orphans(procs: list[dict] | None = None, run=subprocess.run, kill=None, owner=None,
                 log=None) -> list[dict]:
    """Giết tiến trình bộ dựng mồ côi của user. -> [{pid, name}] đã gửi lệnh giết. Không ném.

    Giết ĐÚNG danh sách đã tính (Windows không `/T`: taskkill tự đi theo ParentProcessId và dính
    đúng lỗi PID cấp lại). Ngay trước khi giết, đọc lại danh sách: pid nào đổi tên/giờ tạo ⇒ bỏ.
    Windows: lọc theo PHIÊN chưa đủ — task "dù user có đăng nhập hay không" chạy ở phiên 0 chung
    với task của user khác — nên còn đối chiếu SID chủ tiến trình với SID của chính mình
    (`owner`, mặc định `chu_so_huu_windows` — ctypes, <1 ms/tiến trình); pid không đọc được chủ
    thì bỏ riêng pid đó, không đọc được SID của chính mình ⇒ KHÔNG giết gì. POSIX: `ps -U <uid>`
    đã chỉ trả tiến trình của user này.
    """
    log = log or contract.log
    procs = list_processes(run) if procs is None else procs
    nan = find_orphans(procs)
    if not nan:
        return []
    if _NT:
        me, sid = (owner or chu_so_huu_windows)([p["pid"] for p in nan])
        if not me:
            log("[probe] WARN: không đọc được chủ sở hữu tiến trình — KHÔNG giết tiến trình nào")
            return []
        la = [p for p in nan if sid.get(p["pid"]) != me]
        if la:
            log(f"[probe] bỏ qua {len(la)} tiến trình mồ côi không thuộc user này (hoặc không đọc "
                f"được chủ): {', '.join(sorted({p['name'] for p in la}))}")
        nan = [p for p in nan if sid.get(p["pid"]) == me]
        if not nan:
            return []
    # Đọc lại SAU khi hỏi chủ — khe hở cho PID bị cấp lại càng hẹp càng tốt.
    moi = {p["pid"]: p for p in list_processes(run)}
    if kill is None:
        def kill(pid):
            if os.name == "nt":
                run(["taskkill", "/F", "/PID", str(pid)], capture_output=True, timeout=CMD_TIMEOUT)
            else:
                os.kill(pid, signal.SIGKILL)
    ra = []
    for p in nan:
        q = moi.get(p["pid"])
        if q is None or q.get("name") != p.get("name") or q.get("tao") != p.get("tao"):
            continue
        try:
            kill(p["pid"])
            ra.append({"pid": p["pid"], "name": p["name"]})
        except (OSError, subprocess.SubprocessError):
            continue
    return ra


# ── thư mục tạm cũ ─────────────────────────────────────────────────────────────────────

def _moi_nhat(p: str) -> float:
    """mtime MỚI NHẤT trong cây `p` (tối đa PROFILE_SCAN_MAX mục): thư mục cấp một của Chrome ít khi
    đổi mtime dù profile đang được dùng."""
    m = os.path.getmtime(p)
    dem = 0
    for goc, dirs, files in os.walk(p):
        for n in dirs + files:
            dem += 1
            if dem > PROFILE_SCAN_MAX:
                return m
            try:
                m = max(m, os.lstat(os.path.join(goc, n)).st_mtime)
            except OSError:
                continue
    return m


def old_profiles(tmpdir: str | None = None, older_than=PROFILE_AGE, now=None,
                 procs: list[dict] | None = None) -> list[str]:
    """Thư mục tạm của Chrome/HyperFrames cũ hơn `older_than` VÀ không tiến trình sống nào nhắc tới
    (`procs`: dòng lệnh chứa tên thư mục ⇒ đang dùng, vd một lượt truyện render dài > 1 h)."""
    tmpdir = tmpdir or tempfile.gettempdir()
    now = time.time() if now is None else now
    dang_dung = " ".join((p.get("cmd") or "") for p in (procs or [])).lower()
    ra = []
    try:
        names = os.listdir(tmpdir)
    except OSError:
        return []
    for n in sorted(names):
        if not any(fnmatch.fnmatch(n, g) for g in PROFILE_GLOBS):
            continue
        if n.lower() in dang_dung:
            continue
        p = os.path.join(tmpdir, n)
        try:
            if os.path.islink(p) or not os.path.isdir(p):
                continue
            if now - _moi_nhat(p) > older_than:
                ra.append(p)
        except OSError:
            continue
    return ra


def clean_profiles(tmpdir: str | None = None, older_than=PROFILE_AGE, now=None,
                   procs: list[dict] | None = None) -> list[str]:
    """Xoá thư mục tạm của Chrome/HyperFrames cũ và không ai dùng. -> [đã xoá]. Không ném."""
    ra = []
    for p in old_profiles(tmpdir, older_than, now, procs):
        shutil.rmtree(p, ignore_errors=True)
        if not os.path.exists(p):
            ra.append(p)
    return ra


# ── gói chẩn đoán ──────────────────────────────────────────────────────────────────────

def _ghi(d: str, ten: str, text: str) -> None:
    b = (text or "").encode("utf-8", "replace")
    dau = b""
    if len(b) > TRAN_FILE:            # cắt TRƯỚC khi che: che có chi phí theo độ dài
        dau = b"(...cat phan dau, giu " + str(TRAN_FILE).encode() + b" byte cuoi)\n"
        b = _che_duoi_pem(b[-TRAN_FILE:])
    b = dau + _che(b.decode("utf-8", "replace")).encode("utf-8", "replace")
    with open(os.path.join(d, ten), "wb") as f:
        f.write(b)


def _bang_tien_trinh(run) -> str:
    if os.name == "nt":
        ps = ("Get-Process | Sort-Object CPU -Descending | Select-Object -First 40 Id,ProcessName,"
              "CPU,WorkingSet64,StartTime | Format-Table -AutoSize | Out-String -Width 200")
        return _run_text(["powershell", "-NoProfile", "-NonInteractive", "-Command", ps], run=run)
    # `comm` (tên chương trình), KHÔNG `command`: dòng lệnh đầy đủ có thể mang token.
    txt = _run_text(["ps", "-Ao", "pid,ppid,user,pcpu,pmem,etime,comm"], run=run)
    dong = txt.splitlines()
    if len(dong) < 2:
        return txt

    def cpu(l):
        try:
            return float(l.split()[3])
        except (IndexError, ValueError):
            return 0.0
    return "\n".join([dong[0]] + sorted(dong[1:], key=cpu, reverse=True)[:40]) + "\n"


def diag_bundle(root: str, error: str = "", output: str = "", run=subprocess.run,
                now=None, tmpdir: str | None = None, procs: list[dict] | None = None) -> str:
    """Chụp chứng cứ lúc kẹt vào `<root>/<YYYYmmdd-HHMMSS>/` -> đường thư mục. Không ném OSError
    ra ngoài vì từng file: một lệnh hỏng chỉ để lại dòng "(không chạy được …)" trong file đó."""
    now = now or _dt.datetime.now()
    d = os.path.join(root, now.strftime("%Y%m%d-%H%M%S"))
    os.makedirs(d, exist_ok=True)
    mac = sys.platform == "darwin"
    procs = list_processes(run) if procs is None else procs
    bo_dung = [p for p in procs if _la_bo_dung(p)]
    mo_coi = {p["pid"] for p in find_orphans(procs)}
    _ghi(d, "probe-error.txt", (error or "") + ("\n\n--- output ---\n" + output if output else ""))
    _ghi(d, "ps-top-cpu.txt", _bang_tien_trinh(run))
    _ghi(d, "render-procs.txt",
         f"{len(bo_dung)} tiến trình bộ dựng (Chrome/HyperFrames) của user, {len(mo_coi)} mồ côi\n"
         + "".join(f"pid={p['pid']} ppid={p['ppid']} name={p['name']}"
                   f"{' MO_COI' if p['pid'] in mo_coi else ''}\n" for p in bo_dung))
    tmp = tmpdir or tempfile.gettempdir()
    dong = []
    ts = time.time()
    try:
        for n in sorted(os.listdir(tmp)):
            if any(fnmatch.fnmatch(n, g) for g in PROFILE_GLOBS):
                try:
                    tuoi = int(ts - os.path.getmtime(os.path.join(tmp, n)))
                except OSError:
                    tuoi = -1
                dong.append(f"{n}  tuoi={tuoi}s")
    except OSError as e:
        dong.append(f"(không đọc được {tmp}: {e})")
    _ghi(d, "temp-profiles.txt", f"{tmp}\n" + "\n".join(dong) + "\n")
    if mac:
        _ghi(d, "pmset-assertions.txt", _run_text(["pmset", "-g", "assertions"], run=run))
        _ghi(d, "pmset-therm.txt", _run_text(["pmset", "-g", "therm"], run=run))
        _ghi(d, "log-show-windowserver-coreaudiod.txt", _run_text(
            ["log", "show", "--last", "10m", "--style", "compact", "--predicate",
             'process == "WindowServer" OR process == "coreaudiod"'],
            timeout=LOG_SHOW_TIMEOUT, run=run))
    tom = {"time": now.isoformat(timespec="seconds"), "platform": platform.platform(),
           "user": getpass.getuser(), "render_procs": len(bo_dung), "orphans": len(mo_coi),
           "temp_profiles": len(dong)}
    _ghi(d, "summary.json", json.dumps(tom, ensure_ascii=False, indent=2))
    return d


# ── thang ──────────────────────────────────────────────────────────────────────────────

def _stuck(e: Exception) -> bool:
    return isinstance(e, EngineError) and str(e).startswith(STUCK)


def ladder(probe_fn, timeout, diag_dir=None, waits=WAITS, sleep=time.sleep, run=subprocess.run,
           kill=None, tmpdir=None, log=contract.log):
    """Chạy probe; kẹt thì chụp gói + tự chữa + thử lại theo `waits`. -> kết quả probe + "heal".

    Ném `EngineError` `RENDER_STUCK:` (kèm `.diag`) khi hết thang; lỗi khác ném nguyên.
    """
    try:
        res = probe_fn(timeout)
        return dict(res, heal=None)
    except Exception as e:      # noqa: BLE001 — chỉ bắt để phân loại, lỗi khác ném lại nguyên
        if not _stuck(e):
            raise
        loi_dau = e
    goc = diag_dir or os.path.join(tempfile.gettempdir(), "video-studio-render-stuck")
    try:
        diag = diag_bundle(goc, str(loi_dau), getattr(loi_dau, "output", ""), run=run, tmpdir=tmpdir)
    except OSError as e:
        diag = f"(không ghi được gói chẩn đoán vào {goc}: {e})"
    log(f"[probe] {STUCK} — đã chụp gói chẩn đoán: {diag}")
    log(f"RENDER_DIAG={diag}")
    procs = list_processes(run)
    giet = kill_orphans(procs, run=run, kill=kill, log=log)
    # Tiến trình vừa giết không còn "dùng" profile của nó — bỏ khỏi danh sách trước khi xoá, nếu
    # không chính profile của Chrome mồ côi sẽ được giữ lại (review vòng 2).
    da_giet = {p["pid"] for p in giet}
    xoa = clean_profiles(tmpdir, procs=[p for p in procs if p["pid"] not in da_giet])
    log(f"[probe] tự chữa: giết {len(giet)} tiến trình bộ dựng mồ côi"
        + (f" ({', '.join(sorted({p['name'] for p in giet}))})" if giet else "")
        + f", xoá {len(xoa)} thư mục tạm cũ > {PROFILE_AGE // 3600} h")
    heal = {"diag": diag, "killed": len(giet), "cleaned": len(xoa), "waits": list(waits)}
    loi = loi_dau
    for buoc, cho in enumerate(waits, start=2):
        log(f"[probe] chờ {cho}s rồi thử lại (lần {buoc}/{len(waits) + 1}) ...")
        sleep(cho)
        try:
            res = probe_fn(timeout)
        except Exception as e:  # noqa: BLE001
            if not _stuck(e):
                raise
            loi = e
            continue
        log(f"[probe] render thử OK sau tự chữa (lần {buoc}) — gói chẩn đoán giữ ở {diag}")
        log(f"RENDER_HEAL=recovered step={buoc}")
        return dict(res, heal=dict(heal, recovered=True, step=buoc))
    log(f"RENDER_HEAL=failed steps={len(waits) + 1}")
    duoi = str(loi).split("\n", 1)[1][-600:] if "\n" in str(loi) else ""
    out = EngineError(
        f"{STUCK}: môi trường render kẹt — đã tự chữa (giết {len(giet)} tiến trình mồ côi, xoá "
        f"{len(xoa)} thư mục tạm cũ, thử lại {len(waits)} lần trong {sum(waits)}s) vẫn kẹt — "
        f"{HINT_REBOOT}. Gói chẩn đoán: {diag}" + ("\n" + duoi if duoi else ""))
    out.diag = diag
    raise out
