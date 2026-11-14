"""render.py — gọi HyperFrames (một chỗ duy nhất) + lệnh `video-studio render`.

Hai việc:

1. **Vỏ bọc npx.** Bản pipeline cũ có SÁU chỗ dựng lại cùng một lệnh render, mỗi chỗ một
   `timeout`, và chỗ nào cũng cho tiến trình con chạy QUA SHELL. Đưa một argv list qua shell
   là bẫy hai đầu: trên POSIX chỉ phần tử ĐẦU được chạy (mọi tham số rơi mất), còn trên
   Windows thì tham số đi qua bộ tách chuỗi của `cmd.exe`. Ở đây chỉ còn một hàm, không bao
   giờ qua shell, luôn argv list, `npx` lấy bằng `shutil.which` (Windows trả `npx.cmd`), và
   bản HyperFrames lấy từ `_env` nên không thể trôi sang một dải bản không xác định.

2. **Lệnh `render`.** spec JSON (`spec.py`, `schema_version=1`) → mp4 theo template. Với
   `--json`, dòng cuối stdout là:

       {"ok": true, "outputs": [{"kind","path","duration"}], "timings": {...},
        "engine": {"hyperframes","voice_studio","voice_studio_version","video_studio",
                   "contract"}}

Retry: HyperFrames chạy nhiều worker Chromium; short render ngay sau long dễ chết vì tranh
RAM/handle lúc long chưa giải phóng hết — hỏng THOÁNG QUA, chạy lại là qua. Ba lần thử, nghỉ
20 s, và khi hỏng hẳn thì IN stderr của HyperFrames ra log (bản cũ `capture_output` nuốt mất,
để lại traceback Python rỗng không chẩn được).
"""
import argparse
import hashlib
import os
import shutil
import stat
import subprocess
import tempfile
import time

from . import API_VERSION, __version__, _env, _paths, contract, spec as spec_mod, voice
from .contract import ContractError, EngineError, StationMissing

FONT_TOKEN = "__FONT__"
INDEX = "index.html"
DEFAULT_TIMEOUT = 3600
RETRIES = 3
RETRY_SLEEP = 20
# Mức chất lượng khai tường minh cho `hyperframes render` — xem render_project().
QUALITY = "standard"
# GSAP 3.15.0, dist/gsap.min.js from the official npm tarball. No floating script.
PREVIEW_GSAP_SHA256 = "92bb9a96476f983d212a2bc4f54c889039c1696dd4461d40a736860938570fbb"
PREVIEW_GSAP_MAX_BYTES = 1024 * 1024
# Tiền tố lỗi khi môi trường render kẹt — cùng chữ với `probe.STUCK`; bên gọi (runner marketing,
# triage) tìm đúng chuỗi này để nói "khởi động lại máy" thay vì "sửa project".
STUCK_PREFIX = "RENDER_STUCK"

# tên project ở dòng lệnh -> (module template, hàm, mô tả)
TEMPLATES = {
    "effect-preview": ("effect_preview", "render_preview", "xem trước hiệu ứng 16:9, không âm thanh"),
    "news":        ("news", "render_daily", "bản tin ngày: recap 16:9 + short 9:16"),
    "news-weekly": ("news", "render_weekly", "recap tuần 16:9 + short 9:16"),
    "topstory":    ("news", "render_topstory", "deep-dive một tin: long 16:9 + short 9:16"),
    "repo-today":  ("news", "render_repo_today", "deep-dive nhiều cảnh (news v2)"),
}

__all__ = ["FONT_TOKEN", "QUALITY", "STUCK_PREFIX", "TEMPLATES", "render_env", "hyperframes_argv",
           "write_index", "render_project", "do_render_project_dir", "main"]


# ── vỏ bọc HyperFrames ──────────────────────────────────────────────────────────────────

def render_env(extra_dirs=()):
    """Môi trường cho tiến trình con: node + ffmpeg ở đầu PATH, engine giọng chạy offline.

    HyperFrames cần CẢ ffmpeg lẫn ffprobe trên PATH. Bản cũ dò thư mục gói WinGet bằng glob —
    chỉ đúng trên một máy Windows; nay đi qua `FFMPEG_DIR` → `shutil.which`.
    """
    env = dict(os.environ)
    dirs = []
    for exe in (_env.node_exe(), _env.ffmpeg_exe()):
        if exe:
            d = os.path.dirname(exe)
            if d and d not in dirs:
                dirs.append(d)
    for d in extra_dirs:
        if d and d not in dirs:
            dirs.append(d)
    if dirs:
        env["PATH"] = os.pathsep.join(dirs) + os.pathsep + env.get("PATH", "")
    env.setdefault("HF_HUB_OFFLINE", "1")
    env.setdefault("TRANSFORMERS_OFFLINE", "1")
    return env


def hyperframes_argv(*args, version=None):
    """argv list gọi HyperFrames qua npx — không bao giờ là một chuỗi lệnh."""
    npx = _env.npx_exe()
    if not npx:
        raise StationMissing(
            "không thấy `npx` (Node ≥ 22). Cài Node rồi chạy `video-studio doctor`; "
            "hoặc đặt NODE_DIR trỏ thư mục chứa node/npx.")
    return [npx, "--yes", _env.hyperframes_spec(version), *args]


def write_index(proj_dir, html):
    """Ghi `index.html` của project + thay chỗ dành cho font.

    Template giữ `__FONT__` thay vì một tên font cứng, vì font sẵn có khác nhau giữa Windows
    và macOS. `_env.font_stack()` đọc `VIDEO_FONT` MỖI LẦN gọi nên đổi biến là đổi ngay.
    """
    path = os.path.join(proj_dir, INDEX)
    os.makedirs(proj_dir, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html.replace(FONT_TOKEN, _env.font_stack()))
    return path


def _apply_env_extra(env, extra):
    """Đặt `extra` vào `env`, xoá trước mọi khoá trùng KHÁC hoa/thường (Windows: giá trị engine thắng; POSIX: cả hai tồn tại)."""
    wanted = {k.lower() for k in extra}
    for k in [k for k in env if k.lower() in wanted]:
        del env[k]
    env.update(extra)


def render_project(proj_dir, out_file, timeout=DEFAULT_TIMEOUT, retries=RETRIES, label="",
                   version=None, sleep=time.sleep, offline=False, env_extra=None):
    """Render `index.html` của project thành video câm `out_file`. -> out_file.

    `out_file` tương đối được hiểu là tương đối với thư mục project (HyperFrames chạy `cwd`
    ở đó). Ném EngineError (mã 1) khi HyperFrames hỏng sau khi đã thử lại.

    `-q standard` được khai TƯỜNG MINH, không để engine tự chọn: từ 0.8.38 mặc định đổi sang
    `looks` (CRF 16), đo trên bản tin thật là **+44…+49 % dung lượng** mà mắt không thấy khác
    (PSNR 45–51 dB). Chất lượng ra là quyết định của người dựng, không phải của bản engine
    tình cờ đang cài — khai rõ thì đổi bản không âm thầm đổi file giao. Cờ này hợp lệ ở cả
    0.7.94 lẫn nhánh 0.8.x nên đường lùi vẫn chạy.
    """
    argv = hyperframes_argv("render", "-o", out_file, "-q", QUALITY, version=version)
    env = render_env()
    if offline:
        _apply_env_extra(env, {"npm_config_offline": "true"})
    if env_extra:
        _apply_env_extra(env, env_extra)
    tag = f"[{label}] " if label else ""
    last = None
    nav = 0                     # số lần thử hỏng vì `Navigation timeout` (không mở được trang)
    for attempt in range(max(1, retries)):
        try:
            subprocess.run(argv, cwd=proj_dir, env=env, check=True, capture_output=True,
                           timeout=timeout)
            return out_file
        except subprocess.TimeoutExpired as e:
            raise EngineError(f"{tag}HyperFrames quá {timeout}s chưa xong ({proj_dir})") from e
        except subprocess.CalledProcessError as e:
            last = e
            err = e.stderr or b""
            err = err.decode("utf-8", "replace") if isinstance(err, bytes) else str(err)
            tail = "\n".join(err.strip().splitlines()[-15:])
            if "navigation timeout" in err.lower():
                nav += 1
            more =" — thử lại sau %ds" % RETRY_SLEEP if attempt < retries - 1 else ""
            contract.log(f"  ! {tag}HyperFrames render hỏng (mã {e.returncode}), "
                         f"lần {attempt + 1}/{retries}{more}\n{tail}")
            if attempt < retries - 1:
                sleep(RETRY_SLEEP)
    # `max(1, retries)` ở vòng lặp: `retries=0` vẫn chạy MỘT lần, nên câu "hỏng sau 0 lần"
    # là sai sự thật với chính vòng lặp ngay trên nó.
    if nav == max(1, retries):
        # P1-24 (Mac mini 02/10/2026): MỌI lần thử chết ở `page.goto … Navigation timeout` (frame
        # 0) là dấu vân tay của môi trường kẹt, không phải lỗi project — mọi project khác cũng
        # hỏng, khởi động lại máy là hết. Nói thẳng điều đó; "chạy doctor" ở đây là chỉ sai hướng.
        raise EngineError(f"{tag}{STUCK_PREFIX}: môi trường render kẹt — HyperFrames không mở được "
                          f"trang ở cả {nav} lần thử (Navigation timeout ở frame 0) — khởi động "
                          f"lại máy rồi chạy lại (kiểm nhanh: `video-studio probe`)")
    raise EngineError(f"{tag}HyperFrames render hỏng sau {max(1, retries)} lần "
                      f"(mã {last.returncode}) — "
                      f"xem log ở trên; chạy `video-studio doctor --hf` để kiểm engine")


# ── phiên bản engine (cho khối "engine" của JSON kết quả) ───────────────────────────────

def engine_versions():
    """Khối `engine` của JSON kết quả (docs/CONTRACT.md §2).

    `voice_studio` là bản HỢP ĐỒNG của repo giọng (API_VERSION) — đúng nghĩa repo giọng tự
    trả ở `speak`/`narrate`, để bên gọi đọc một khoá mà không phải biết lệnh nào sinh ra nó.
    Bản phát hành của gói giọng đi khoá riêng `voice_studio_version`. `video_studio` giữ nghĩa
    cũ (bản phát hành của repo này); hợp đồng của repo này ở `contract`.
    """
    out = {"hyperframes": None, "voice_studio": None, "voice_studio_version": None,
           "video_studio": __version__, "contract": API_VERSION}
    try:
        out["hyperframes"] = _env.hyperframes_version()
    except ContractError:
        pass
    out["voice_studio"] = voice.api_version()
    out["voice_studio_version"] = voice.version()
    return out


def apply_bgm(outputs, spec):
    """Trộn nhạc nền của spec vào từng file đã dựng. -> danh sách file đã trộn.

    Nhạc nền là khoá `bgm.style` của spec, và nó chỉ có nghĩa SAU khi video đã có giọng —
    nên nó được trộn ở đây, một lần cho mỗi file ra, thay vì rải vào từng template. Thiếu
    nhạc (style lạ, thư viện chưa có) KHÔNG làm hỏng lượt render: file gốc giữ nguyên và
    log nói rõ, vì mất nhạc nền là khuyết điểm còn mất cả video là hỏng việc.
    """
    style = (spec_mod.bgm_of(spec) or {}).get("style")
    if not style:
        return []
    volume = (spec_mod.bgm_of(spec) or {}).get("volume")
    mixed = []
    for o in outputs:
        try:
            if voice.mix_bgm(o["path"], style, volume):
                mixed.append(o["path"])
            else:
                contract.log(f"  ! nhạc nền '{style}' không trộn được vào {o['path']} — "
                             "giữ nguyên bản không nhạc (kiểm thư viện nhạc của trạm giọng)")
        except StationMissing as e:
            # Thiếu trạm giọng / thiếu thư viện nhạc: mọi file sau cũng thế, dừng thử luôn.
            contract.log(f"  ! bỏ qua nhạc nền: {e}")
            break
        except Exception as e:      # noqa: BLE001 — xem docstring: mất nhạc ≠ hỏng lượt render
            # Chỉ cứu `StationMissing` là hứa một đằng làm một nẻo: một file nhạc hỏng hay một
            # lỗi ffmpeg trong `av.mix_bgm` sẽ thoát MÃ 1 **sau khi mp4 đã nằm trên đĩa**.
            # Bên gọi đọc mã 1 là "render hỏng, thử lại", nên nó render lại cả lượt rồi đâm
            # vào đúng file nhạc đó — hỏng mãi mãi, và tốn cả một lượt render mỗi lần.
            contract.log(f"  ! nhạc nền '{style}' lỗi trên {o['path']}: "
                         f"{e.__class__.__name__}: {e} — giữ nguyên bản không nhạc")
    return mixed


# ── lệnh render ─────────────────────────────────────────────────────────────────────────

def missing_dependency(exc, project=""):
    """ImportError của template → StationMissing (mã 3) kèm lệnh cài.

    Bên gọi cần phân biệt "render sập, thử lại đi" (mã 1) với "máy chưa cài đủ" (mã 3). Một
    traceback `ModuleNotFoundError` nói đúng sự thật nhưng nói cho sai người.
    """
    name = getattr(exc, "name", None) or "một phụ thuộc"
    what = f"template {project!r}" if project else "bước render"
    # Không khuyên `pip install -e ".[voice]"`: extra đó đòi gói `agent-voice-studio` mà pip
    # không tìm được khi chưa có bản clone repo giọng, nên lệnh hỏng ngay. Đường duy nhất là
    # INSTALL.md mục 5b; thấy bản clone anh em thì in đúng đường của máy này (như doctor).
    try:
        sib = _env.sibling_repo("voice_studio")
    except Exception:           # noqa: BLE001 — chỉ là gợi ý; không được đổi mã thoát
        sib = None
    if sib:
        how = (f"thấy repo giọng cạnh repo này: `python -m pip install -e \"{sib}[engine]\"` "
               "bằng python của CÙNG venv")
    else:
        how = ("clone repo giọng agent-voice-studio cạnh repo này rồi cài vào CÙNG venv: "
               "`pip install -e \"<repo giọng>[engine]\"`")
    return StationMissing(
        f"{what} cần `{name}`, venv này chưa có. Cài repo giọng (INSTALL.md mục 5b) — {how}. "
        "Kiểm bằng `video-studio doctor`.")


def _template(project):
    if project not in TEMPLATES:
        raise ContractError(f"project lạ: {project!r} (có: {', '.join(sorted(TEMPLATES))})")
    pkg, func, _desc = TEMPLATES[project]
    import importlib
    try:
        mod = importlib.import_module(f"video_studio.templates.{pkg}")
        return getattr(mod, func)
    except ImportError as e:
        raise missing_dependency(e, project) from e


def _read_preview_gsap(path):
    """Read pinned GSAP via handle-relative Windows no-recall primitives only."""
    if os.name != "nt":
        raise ContractError("effect-preview chưa hỗ trợ đọc GSAP an toàn trên hệ điều hành này")
    from .effect_library import _native_windows as native
    full = os.path.abspath(path)
    parent, name = os.path.split(full)
    root = handle = None
    try:
        try:
            root = native.open_root(parent)
            handle = native.open_file(root, name)
            gsap_bytes = native.read_all(handle, PREVIEW_GSAP_MAX_BYTES)
        finally:
            try:
                if handle is not None:
                    native.close(handle)
            finally:
                if root is not None:
                    native.close(root)
    except (OSError, ValueError) as exc:
        raise ContractError(f"Không đọc được GSAP cục bộ: {exc}") from exc
    if hashlib.sha256(gsap_bytes).hexdigest() != PREVIEW_GSAP_SHA256:
        raise ContractError("GSAP SHA-256 không khớp bản 3.15.0 đã ghim")
    return gsap_bytes


def do_render(args):
    data = spec_mod.load(args.input, brand_file=args.brand or None)
    gsap_file = getattr(args, "gsap_file", "")
    if gsap_file and args.project != "effect-preview":
        raise ContractError("--gsap-file chỉ hỗ trợ effect-preview")
    if args.project == "effect-preview":
        if not gsap_file:
            raise ContractError("effect-preview cần --gsap-file trỏ tới GSAP JavaScript cục bộ")
        data["_gsap_bytes"] = _read_preview_gsap(gsap_file)
    if args.voice_profile:
        data["voice"] = {**spec_mod.voice_of(data), "profile": args.voice_profile}
    # Đường dẫn tương đối trong spec (ảnh, clip) neo vào THƯ MỤC CHỨA SPEC, không vào cwd.
    data["_spec_path"] = os.path.abspath(args.input)
    if getattr(args, "images", ""):      # kiểm TRƯỚC khi tạo --out: lỗi mã 2 không để lại thư mục rỗng
        spec_mod.apply_images(data, args.images, args.project)
    out_dir = os.path.abspath(args.out or ".")
    os.makedirs(out_dir, exist_ok=True)
    fn = _template(args.project)
    t0 = time.time()
    try:
        outputs = fn(data, out_dir)
    except ImportError as e:
        raise missing_dependency(e, args.project) from e
    res = {"project": args.project, "out": out_dir, "outputs": outputs,
           "timings": {"total": round(time.time() - t0, 2)},
           "engine": engine_versions()}
    mixed = apply_bgm(outputs, data)
    if mixed:
        res["bgm"] = {"style": spec_mod.bgm_of(data).get("style"), "mixed": mixed}
    return res


# ── `render --project-dir`: project HyperFrames tự dựng ─────────────────────────────────

# `npx` đọc `.npmrc`/`package.json`/`node_modules` ở cwd: một project lạ mang theo `.npmrc` đổi
# được registry, `node_modules/.bin` chiếm được tên lệnh. Nên project KHÔNG chạy tại chỗ: nó
# được chép (chỉ phần tĩnh) sang thư mục tạm do engine sở hữu, và những thứ trên bị TỪ CHỐI.
FORBIDDEN_NAMES = frozenset({".npmrc", "package.json", "node_modules"})
STATIC_EXTS = frozenset({
    ".html", ".css", ".js", ".mjs", ".json", ".svg", ".txt", ".png", ".jpg", ".jpeg", ".webp",
    ".gif", ".avif", ".mp4", ".webm", ".mov", ".mp3", ".wav", ".m4a", ".ogg", ".woff",
    ".woff2", ".ttf", ".otf"})
ASSET_DIR = "assets"
PROJECT_MAX_BYTES = 1 << 30
_REPARSE = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)


def _is_link(st):
    """Symlink hoặc junction/reparse point (Windows) — chỉ nhìn `lstat`, không đi theo."""
    return stat.S_ISLNK(st.st_mode) or bool(getattr(st, "st_file_attributes", 0) & _REPARSE)


class _Scanned(list):
    """Danh sách `[(đường tuyệt đối, đường tương đối)]` kèm `.stats[rel] = (kích thước, mtime_ns)` đo LÚC QUÉT."""
    stats = None


def _scan_project(root):
    """-> [(đường tuyệt đối, đường tương đối)] cần chép (kèm `.stats`); ContractError nếu project không an toàn."""
    if not os.path.isdir(root) or _is_link(os.lstat(root)):
        raise ContractError(f"--project-dir phải là một thư mục thật (không phải liên kết): {root}")
    files, total, stats = _Scanned(), 0, {}
    files.stats = stats
    stack = [("", root)]
    while stack:
        rel_dir, cur = stack.pop()
        with os.scandir(cur) as it:
            entries = sorted(it, key=lambda e: e.name)
        for e in entries:
            rel = f"{rel_dir}{e.name}"
            if e.name.lower() in FORBIDDEN_NAMES:
                raise ContractError(
                    f"project có `{rel}` — bị từ chối vì npx đọc tệp này ở thư mục chạy và có thể đổi "
                    "registry hoặc chiếm lệnh. Bỏ `.npmrc`, `package.json`, `node_modules/` khỏi project "
                    "(thư viện đặt tĩnh trong assets/).")
            st = e.stat(follow_symlinks=False)
            if _is_link(st):
                raise ContractError(f"project có liên kết `{rel}` (symlink/junction) — không đi theo; "
                                    "chép tệp thật vào project")
            if stat.S_ISDIR(st.st_mode):
                if rel_dir == "" and e.name != ASSET_DIR:
                    raise ContractError(f"thư mục `{rel}/` không được nhận — chỉ `{ASSET_DIR}/` "
                                        "(và `index.html`, tệp tĩnh ở gốc)")
                stack.append((rel + "/", e.path))
            elif stat.S_ISREG(st.st_mode):
                if os.path.splitext(e.name)[1].lower() not in STATIC_EXTS:
                    raise ContractError(f"tệp `{rel}` không phải tài nguyên tĩnh được nhận")
                total += st.st_size
                if total > PROJECT_MAX_BYTES:
                    raise ContractError("project quá lớn (> 1 GiB)")
                files.append((e.path, rel))
                stats[rel] = (st.st_size, st.st_mtime_ns)
            else:
                raise ContractError(f"`{rel}` không phải tệp thường")
    if INDEX not in [r for _a, r in files]:
        raise ContractError(f"project thiếu `{INDEX}` ở gốc: {root}")
    return files


def _regular(st):
    return stat.S_ISREG(st.st_mode) and not _is_link(st)


def _stage_project(files, dest):
    """Chép project sang `dest`. Mã 2 nếu một tệp đổi (liên kết, kích thước, giờ sửa) so với lúc quét, hoặc tổng vượt trần.

    TOCTOU chỉ được THU HẸP, không loại hẳn: so `lstat` trước và sau mỗi lần chép với số đo lúc quét."""
    stats = getattr(files, "stats", None) or {}
    total = 0
    for src, rel in files:
        dst = os.path.join(dest, *rel.split("/"))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        before = os.lstat(src)
        want = stats.get(rel, (before.st_size, before.st_mtime_ns))
        if not _regular(before) or (before.st_size, before.st_mtime_ns) != want:
            raise ContractError(f"`{rel}` đã đổi sau khi quét (liên kết, kích thước hoặc giờ sửa) — chạy lại")
        shutil.copyfile(src, dst, follow_symlinks=False)
        after = os.lstat(src)
        copied = os.lstat(dst)
        if not _regular(after) or (after.st_size, after.st_mtime_ns) != want:
            raise ContractError(f"`{rel}` đổi trong lúc chép — chạy lại")
        if not _regular(copied) or copied.st_size != want[0]:
            raise ContractError(f"bản chép của `{rel}` không phải tệp thường đúng kích thước")
        total += copied.st_size
        if total > PROJECT_MAX_BYTES:
            raise ContractError("project quá lớn (> 1 GiB)")


def _project_name(src_dir):
    """Tên file ra từ tên thư mục project: phải là MỘT tên tệp trần (`plain_name`); gốc ổ đĩa -> `project`."""
    base = os.path.basename(src_dir.rstrip(os.sep + (os.altsep or ""))) or "project"
    return _paths.plain_name(base, "--project-dir")


def _check_final(final):
    """Đích `OUT/<tên>.mp4`: liên kết/junction/thư mục -> mã 2; tệp thường đã có -> cảnh báo ghi đè."""
    try:
        st = os.lstat(final)
    except FileNotFoundError:
        return
    if _is_link(st) or stat.S_ISDIR(st.st_mode):
        raise ContractError(f"đích {final} là liên kết hoặc thư mục — từ chối ghi, chọn --out khác")
    if not stat.S_ISREG(st.st_mode):
        raise ContractError(f"đích {final} không phải tệp thường — từ chối ghi")
    contract.log(f"  [warn] ghi đè {final}")


def _check_tail(raw, limit=60):
    """`limit` dòng cuối của `raw`; có cắt thì thêm dòng nói đã cắt bao nhiêu dòng đầu."""
    lines = raw.strip().splitlines()
    if len(lines) <= limit:
        return "\n".join(lines)
    return f"(cắt {len(lines) - limit} dòng đầu)\n" + "\n".join(lines[-limit:])


def do_render_project_dir(args):
    """check --strict rồi render project tự dựng bằng engine ghim. Mã 2 nếu project không an toàn/không qua check."""
    src_dir = os.path.abspath(args.project_dir)
    out_dir = os.path.abspath(args.out)
    files = _scan_project(src_dir)                      # kiểm TRƯỚC khi tạo --out
    name = _project_name(src_dir)                       # tên tệp trần, kiểm TRƯỚC khi tạo gì
    final = _paths.join_out(out_dir, name + ".mp4", "--project-dir")
    _check_final(final)
    t0 = time.time()
    with tempfile.TemporaryDirectory(prefix="video-studio-proj-") as work:
        proj = os.path.join(work, "project")
        os.makedirs(proj)
        _stage_project(files, proj)
        # Hai file rỗng RIÊNG: npm báo "double-loading config" và thoát nếu user và global trỏ cùng một file.
        user_rc = os.path.join(work, "empty-user.npmrc")
        global_rc = os.path.join(work, "empty-global.npmrc")
        for rc in (user_rc, global_rc):
            open(rc, "w").close()
        env_extra = {"npm_config_userconfig": user_rc, "npm_config_globalconfig": global_rc}
        env = render_env()
        _apply_env_extra(env, env_extra)
        try:
            chk = subprocess.run(hyperframes_argv("check", "--strict"), cwd=proj, env=env,
                                 capture_output=True, timeout=DEFAULT_TIMEOUT)
        except subprocess.TimeoutExpired as e:
            raise EngineError(f"HyperFrames check quá {DEFAULT_TIMEOUT}s chưa xong") from e
        if chk.returncode:
            raw = chk.stderr or chk.stdout or b""
            raw = raw.decode("utf-8", "replace") if isinstance(raw, bytes) else str(raw)
            tail = _check_tail(raw)
            raise ContractError(f"project không qua `check --strict` (mã {chk.returncode}):\n{tail}")
        tmp_out = os.path.join(work, "render.mp4")
        render_project(proj, tmp_out, label=name, env_extra=env_extra)
        if not os.path.isfile(tmp_out):
            raise EngineError("HyperFrames báo xong nhưng không thấy file ra")
        os.makedirs(out_dir, exist_ok=True)
        fd, part = tempfile.mkstemp(dir=out_dir, prefix=".render-", suffix=".mp4.part")   # tên không đoán được
        os.close(fd)
        try:
            shutil.copyfile(tmp_out, part)
            _check_final(final)                         # kiểm lại ngay trước khi thay thế
            os.replace(part, final)
        except BaseException:
            if os.path.lexists(part):
                os.remove(part)
            raise
    return {"project_dir": src_dir, "out": out_dir,
            "outputs": [{"kind": "video", "path": final, "duration": None}],
            "timings": {"total": round(time.time() - t0, 2)}, "engine": engine_versions()}


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="video-studio render",
        description="spec JSON (schema_version=1) → video theo template. Thương hiệu, giọng, "
                    "nhạc nền và danh sách file ra đều nằm trong spec — engine không có mặc "
                    "định nào mang danh tính.",
        epilog="project: " + " · ".join(f"{k} ({v[2]})" for k, v in sorted(TEMPLATES.items())))
    ap.add_argument("--project", default="", choices=[""] + sorted(TEMPLATES),
                    help="template dùng để dựng (bắt buộc nếu không có --project-dir)")
    ap.add_argument("--project-dir", default="",
                    help="thư mục project HyperFrames tự dựng (index.html + assets/): check --strict "
                         "rồi render bằng engine ghim; chép sang thư mục tạm, từ chối .npmrc, "
                         "package.json, node_modules, liên kết")
    ap.add_argument("--input", default="", help="file spec JSON")
    ap.add_argument("--out", required=True, help="thư mục nhận file ra")
    ap.add_argument("--brand", default="", help="file brand.json đè khối brand của spec")
    ap.add_argument("--voice-profile", default="", help="đè voice.profile của spec")
    ap.add_argument("--gsap-file", default="", help="file GSAP cục bộ cho effect-preview")
    ap.add_argument("--images", default="",
                    help="images.json: ghép ảnh của người dùng vào đúng cảnh/đoạn/phần "
                         "(repo-today, news, news-weekly, topstory), một ảnh hoặc danh sách ảnh mỗi cảnh (cục bộ hoặc URL; "
                         "nhiều ảnh trừ repo-today), thay ảnh/clip của cảnh đó; xem docs/CONTRACT.md")
    ap.add_argument("--json", action="store_true", help="in một dòng JSON kết quả ra stdout")
    args, code = contract.parse(ap, argv)
    if args is None:
        return code

    def fn(a):
        if a.project_dir:
            if a.project or a.input:
                raise ContractError("--project-dir không đi cùng --project/--input")
            res = do_render_project_dir(a)
        else:
            if not a.project or not a.input:
                raise ContractError("cần --project và --input (hoặc --project-dir)")
            res = do_render(a)
        for o in res["outputs"]:
            contract.log(f"[render] {o['kind']} -> {o['path']}"
                         + (f" ({o['duration']:.1f}s)" if o.get("duration") else ""))
        return res
    return contract.run(fn, args, args.json)
