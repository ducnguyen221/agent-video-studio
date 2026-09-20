"""render.py — gọi HyperFrames (một chỗ duy nhất) + lệnh `video-studio render`.

Hai việc:

1. **Vỏ bọc npx.** Bản `.tts` cũ có SÁU chỗ dựng lại cùng một lệnh render, mỗi chỗ một
   `timeout`, và chỗ nào cũng cho tiến trình con chạy QUA SHELL. Đưa một argv list qua shell
   là bẫy hai đầu: trên POSIX chỉ phần tử ĐẦU được chạy (mọi tham số rơi mất), còn trên
   Windows thì tham số đi qua bộ tách chuỗi của `cmd.exe`. Ở đây chỉ còn một hàm, không bao
   giờ qua shell, luôn argv list, `npx` lấy bằng `shutil.which` (Windows trả `npx.cmd`), và
   bản HyperFrames lấy từ `_env` nên không thể trôi sang một dải bản không xác định.

2. **Lệnh `render`.** spec JSON (`spec.py`, `schema_version=1`) → mp4 theo template. Với
   `--json`, dòng cuối stdout là:

       {"ok": true, "outputs": [{"kind","path","duration"}], "timings": {...},
        "engine": {"hyperframes","voice_studio","video_studio"}}

Retry: HyperFrames chạy nhiều worker Chromium; short render ngay sau long dễ chết vì tranh
RAM/handle lúc long chưa giải phóng hết — hỏng THOÁNG QUA, chạy lại là qua. Ba lần thử, nghỉ
20 s, và khi hỏng hẳn thì IN stderr của HyperFrames ra log (bản cũ `capture_output` nuốt mất,
để lại traceback Python rỗng không chẩn được).
"""
import argparse
import os
import subprocess
import time

from . import API_VERSION, __version__, _env, contract, spec as spec_mod, voice
from .contract import ContractError, EngineError, StationMissing

FONT_TOKEN = "__FONT__"
INDEX = "index.html"
DEFAULT_TIMEOUT = 3600
RETRIES = 3
RETRY_SLEEP = 20

# tên project ở dòng lệnh -> (module template, hàm, mô tả)
TEMPLATES = {
    "news":        ("news", "render_daily", "bản tin ngày: recap 16:9 + short 9:16"),
    "news-weekly": ("news", "render_weekly", "recap tuần 16:9 + short 9:16"),
    "topstory":    ("news", "render_topstory", "deep-dive một tin: long 16:9 + short 9:16"),
    "repo-today":  ("news", "render_repo_today", "deep-dive nhiều cảnh (news v2)"),
}

__all__ = ["FONT_TOKEN", "TEMPLATES", "render_env", "hyperframes_argv", "write_index",
           "render_project", "main"]


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


def render_project(proj_dir, out_file, timeout=DEFAULT_TIMEOUT, retries=RETRIES, label="",
                   version=None, sleep=time.sleep):
    """Render `index.html` của project thành video câm `out_file`. -> out_file.

    `out_file` tương đối được hiểu là tương đối với thư mục project (HyperFrames chạy `cwd`
    ở đó). Ném EngineError (mã 1) khi HyperFrames hỏng sau khi đã thử lại.
    """
    argv = hyperframes_argv("render", "-o", out_file, version=version)
    env = render_env()
    tag = f"[{label}] " if label else ""
    last = None
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
            more = " — thử lại sau %ds" % RETRY_SLEEP if attempt < retries - 1 else ""
            contract.log(f"  ! {tag}HyperFrames render hỏng (mã {e.returncode}), "
                         f"lần {attempt + 1}/{retries}{more}\n{tail}")
            if attempt < retries - 1:
                sleep(RETRY_SLEEP)
    raise EngineError(f"{tag}HyperFrames render hỏng sau {retries} lần (mã {last.returncode}) — "
                      f"xem log ở trên; chạy `video-studio doctor --hf` để kiểm engine")


# ── phiên bản engine (cho khối "engine" của JSON kết quả) ───────────────────────────────

def engine_versions():
    out = {"hyperframes": None, "voice_studio": None, "video_studio": __version__,
           "contract": API_VERSION}
    try:
        out["hyperframes"] = _env.hyperframes_version()
    except ContractError:
        pass
    out["voice_studio"] = voice.version()
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
            contract.log(f"  ! bỏ qua nhạc nền: {e}")
            break
    return mixed


# ── lệnh render ─────────────────────────────────────────────────────────────────────────

def missing_dependency(exc, project=""):
    """ImportError của template → StationMissing (mã 3) kèm lệnh cài.

    Bên gọi cần phân biệt "render sập, thử lại đi" (mã 1) với "máy chưa cài đủ" (mã 3). Một
    traceback `ModuleNotFoundError` nói đúng sự thật nhưng nói cho sai người.
    """
    name = getattr(exc, "name", None) or "một phụ thuộc"
    what = f"template {project!r}" if project else "bước render"
    return StationMissing(
        f"{what} cần `{name}`, venv này chưa có. Cài phần phụ cho việc render: "
        "`pip install -e \".[voice]\"` — và repo giọng (agent-voice-studio) phải nằm trong "
        "CÙNG venv. Kiểm bằng `video-studio doctor`.")


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


def do_render(args):
    data = spec_mod.load(args.input, brand_file=args.brand or None)
    if args.voice_profile:
        data["voice"] = {**spec_mod.voice_of(data), "profile": args.voice_profile}
    # Đường dẫn tương đối trong spec (ảnh, clip) neo vào THƯ MỤC CHỨA SPEC, không vào cwd.
    data["_spec_path"] = os.path.abspath(args.input)
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


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="video-studio render",
        description="spec JSON (schema_version=1) → video theo template. Thương hiệu, giọng, "
                    "nhạc nền và danh sách file ra đều nằm trong spec — engine không có mặc "
                    "định nào mang danh tính.",
        epilog="project: " + " · ".join(f"{k} ({v[2]})" for k, v in sorted(TEMPLATES.items())))
    ap.add_argument("--project", required=True, choices=sorted(TEMPLATES),
                    help="template dùng để dựng")
    ap.add_argument("--input", required=True, help="file spec JSON")
    ap.add_argument("--out", required=True, help="thư mục nhận file ra")
    ap.add_argument("--brand", default="", help="file brand.json đè khối brand của spec")
    ap.add_argument("--voice-profile", default="", help="đè voice.profile của spec")
    ap.add_argument("--json", action="store_true", help="in một dòng JSON kết quả ra stdout")
    args, code = contract.parse(ap, argv)
    if args is None:
        return code

    def fn(a):
        res = do_render(a)
        for o in res["outputs"]:
            contract.log(f"[render] {o['kind']} -> {o['path']}"
                         + (f" ({o['duration']:.1f}s)" if o.get("duration") else ""))
        return res
    return contract.run(fn, args, args.json)
