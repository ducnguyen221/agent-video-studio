"""fetch.py — `reference fetch`: kế hoạch (mặc định) hoặc tải thật (`--go`), sau bảy cổng.

Thứ tự cổng (đủ ở `gate.py`): 1 URL → 2 `--allow-url` → 3 hồ sơ → 4–5 quyền/phép → 6 có yt-dlp →
7 `source/reference.*` chưa có. Tất cả chạy TRƯỚC mọi tiến trình con; hỏng ở đâu dừng ở đó.

CỔNG NÀY LÀ CỔNG THỦ TỤC. Nó chỉ đọc `provenance.json` và `--allow-url`; agent ghi được hồ sơ thì tự mở được
cổng. Rào thật là luật «người dùng nói đúng URL trong chat, agent chép lời đó vào `permission.quote`».

Giới hạn (RF11):
- `--max-filesize` của yt-dlp chỉ áp khi biết kích thước trước; luồng HLS/DASH không khai kích thước có thể
  tải quá trần.
- Kế hoạch (không `--go`) vẫn là một lượt hỏi metadata qua mạng — đúng vì cổng 1–5 đã qua.
- Tên miền phân giải ra IP nội bộ và redirect của yt-dlp tới host nội bộ không chặn ở tầng này.

`--no-plugin-dirs` có ở yt-dlp 2026.07.04 (đo bằng `--help`, không URL) nên nằm cố định trong argv.
Tiến trình con luôn là argv list, không shell, không `--exec`, không cookie. `run` mặc định là
`subprocess.run` được tra lúc gọi (không buộc sẵn lúc định nghĩa) để test thay được.
"""
import datetime
import json
import os
import re
import subprocess

from .. import _env
from ..contract import ContractError, EngineError, StationMissing
from . import gate

PLAN_TIMEOUT = 120
DOWNLOAD_TIMEOUT = 3600
VERSION_TIMEOUT = 30
MAX_MB_RANGE = (1, 4096)
STDERR_TAIL = 15
REFERENCE_STEM = "reference."
_SUB_LANGS = re.compile(r"[A-Za-z0-9-]+(,[A-Za-z0-9-]+){0,4}")
_PARTIAL = (".part", ".ytdl", ".tmp", ".temp")

__all__ = ["authorize", "check_limits", "ytdlp_argv", "plan_fetch", "do_fetch"]


def check_limits(max_mb, sub_langs):
    """`--max-mb` nguyên 1–4096 và `--sub-langs` ≤ 5 mã `[A-Za-z0-9-]+`; sai ⇒ `ContractError` (mã 2)."""
    lo, hi = MAX_MB_RANGE
    if isinstance(max_mb, bool) or not isinstance(max_mb, int) or not lo <= max_mb <= hi:
        raise ContractError(f"--max-mb phải là số nguyên {lo}–{hi} (nhận {max_mb!r})")
    if (not isinstance(sub_langs, str) or _SUB_LANGS.fullmatch(sub_langs) is None
            or any(code.startswith("-") for code in sub_langs.split(","))):   # `-x` bị optparse coi là cờ
        raise ContractError("--sub-langs phải là 1–5 mã ngôn ngữ [A-Za-z0-9-] cách nhau bằng dấu phẩy "
                            f"(nhận {sub_langs!r})")


def ytdlp_argv(exe, url, dest_dir, *, plan, max_mb, sub_langs):
    """Argv yt-dlp cố định; `--` ngay trước URL. Kiểm giới hạn ở đây nên mọi đường đi đều qua."""
    check_limits(max_mb, sub_langs)
    head = [exe, "--ignore-config", "--no-plugin-dirs", "--no-playlist"]
    if plan:
        return [*head, "--skip-download", "--dump-single-json", "--", url]
    return [*head, "--restrict-filenames", "--max-filesize", f"{max_mb}M",
            "--write-subs", "--sub-format", "vtt", "--sub-langs", sub_langs,
            "-P", dest_dir, "-o", "reference.%(ext)s", "--", url]


def authorize(url, allow_url, project_dir):
    """Cổng 1→5 theo thứ tự hợp đồng; trả `(url đã chuẩn hoá, hồ sơ)`.

    `load_provenance` (cổng 3) chỉ chạy khi URL và `--allow-url` đã qua.
    """
    target = gate.check_url(url)
    try:
        allowed = None if allow_url is None else gate.check_url(allow_url)
    except ContractError:
        allowed = None
    if allowed != target:
        raise ContractError("thiếu phép đích danh cho URL này — người dùng phải nói đúng URL trong chat, "
                            "agent chép lời đó vào provenance.json `permission.quote` và lặp URL ở --allow-url")
    prov = gate.load_provenance(project_dir)
    gate.require_fetch_allowed(prov, target, allow_url)
    return target, prov


def _source_dir(project_dir):
    return os.path.join(project_dir, "source")


def _preflight(project_dir):
    """Cổng 6 (có yt-dlp, mã 3) và cổng 7 (chưa có `source/reference.*`, mã 2). Trả `(exe, source_dir)`."""
    exe = _env.ytdlp_exe()
    if exe is None:
        raise StationMissing("không tìm thấy yt-dlp: cài yt-dlp rồi chạy `video-studio doctor`, "
                             "hoặc đặt YTDLP_DIR (agent không tự cài)")
    src = _source_dir(project_dir)
    if gate._is_link(src):
        raise ContractError(f"{src} là liên kết — từ chối ghi qua liên kết")
    if os.path.isdir(src):
        existing = sorted(n for n in os.listdir(src) if n.lower().startswith(REFERENCE_STEM))
        if existing:
            raise ContractError(f"source/ đã có {existing[0]} — không ghi đè; dời hoặc xoá tay nếu muốn tải lại")
    return exe, src


def _tail(text):
    lines = (text or "").strip().splitlines()
    return "\n".join(lines[-STDERR_TAIL:])


def _run(run, argv, timeout, what):
    try:
        done = run(argv, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
    except subprocess.TimeoutExpired:
        raise EngineError(f"yt-dlp ({what}) quá {timeout} giây") from None
    except OSError as exc:
        raise EngineError(f"không chạy được yt-dlp ({what}): {exc}") from None
    if done.returncode != 0:
        raise EngineError(f"yt-dlp ({what}) thoát mã {done.returncode}:\n{_tail(done.stderr)}")
    return done


def _mb(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return round(value / (1024 * 1024), 1)


def plan_fetch(url, project_dir, run=None):
    """Hỏi metadata (không tải) và trả kế hoạch; không ghi gì vào project."""
    run = run or subprocess.run
    exe, src = _preflight(project_dir)
    argv = ytdlp_argv(exe, url, src, plan=True, max_mb=MAX_MB_RANGE[0], sub_langs="en")
    done = _run(run, argv, PLAN_TIMEOUT, "kế hoạch")
    try:
        meta = json.loads(done.stdout)
    except ValueError:
        meta = None
    if not isinstance(meta, dict):
        raise EngineError(f"yt-dlp trả metadata không phải JSON object:\n{_tail(done.stderr or done.stdout)}")
    size = meta.get("filesize_approx") if meta.get("filesize_approx") is not None else meta.get("filesize")
    return {"plan": {"source": url, "dest_dir": src, "title": meta.get("title"),
                     "duration": meta.get("duration"), "filesize_approx_mb": _mb(size), "download": False},
            "next": "Đây mới là kế hoạch, chưa tải gì. Người dùng đồng ý tải thì chạy lại đúng lệnh này kèm "
                    "--go (tuỳ chọn --max-mb, --sub-langs)."}


def _tool_version(run, exe):
    try:
        done = run([exe, "--version"], capture_output=True, text=True, encoding="utf-8", errors="replace",
                   timeout=VERSION_TIMEOUT)
    except (subprocess.TimeoutExpired, OSError):
        return None
    if done.returncode != 0:
        return None
    return (done.stdout or "").strip() or None


def _outputs(src):
    """(media, [phụ đề]) là tệp `reference.*` yt-dlp vừa tạo; tệp dở dang không tính."""
    media, subs = [], []
    for name in sorted(os.listdir(src)):
        low = name.lower()
        if not low.startswith(REFERENCE_STEM) or not os.path.isfile(os.path.join(src, name)):
            continue
        if low.endswith(".vtt"):
            subs.append(name)
        elif not low.endswith(_PARTIAL):
            media.append(name)
    return media, subs


def do_fetch(url, project_dir, max_mb, sub_langs, run=None):
    """Tải thật vào `<project>/source/reference.*` và ghi khoá `fetch` của `provenance.json`."""
    run = run or subprocess.run
    check_limits(max_mb, sub_langs)
    exe, src = _preflight(project_dir)
    os.makedirs(src, exist_ok=True)
    _run(run, ytdlp_argv(exe, url, src, plan=False, max_mb=max_mb, sub_langs=sub_langs),
         DOWNLOAD_TIMEOUT, "tải")
    media, subs = _outputs(src)
    if not media:
        raise EngineError("yt-dlp không tạo tệp video trong source/ (quá --max-mb?)")
    path = os.path.join(src, media[0])
    record = {
        "fetched_at": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "file": f"source/{media[0]}",
        "sha256": gate.sha256_file(path),
        "tool": "yt-dlp",
        "tool_version": _tool_version(run, exe),
        "subtitles": [f"source/{n}" for n in subs],
    }
    prov = gate.load_provenance(project_dir)
    prov["fetch"] = record
    ref = prov.get("reference")
    if not isinstance(ref, dict):
        ref = prov["reference"] = {}
    if ref.get("url") is None:
        ref["url"] = url
    gate.save_provenance(project_dir, prov)
    return {"fetch": record, "project": project_dir}
