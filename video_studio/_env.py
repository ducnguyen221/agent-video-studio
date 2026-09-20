"""_env.py — MỘT nơi duy nhất trong package quyết định trạm video, bản HyperFrames, node, ffmpeg,
font nằm ở đâu.

Package sống trong repo; trạm video (project đang dựng, seed, skill cho agent, nháp, cache)
sống trên máy người dùng. Hai bên không giả định vị trí của nhau — mọi đường dẫn đi qua các
hàm dưới đây, đọc biến môi trường MỖI LẦN gọi (không đóng băng lúc import).

Biến hợp đồng:

    VIDEO_STATION        gốc trạm video                       (mặc định ~/.video)
    VIDEO_ROOT           tên cũ của VIDEO_STATION — đọc được, kèm DeprecationWarning
    HYPERFRAMES_VERSION  bản HyperFrames gọi qua npx — PHẢI là bản cụ thể (x.y.z), cấm
                         `latest`/`^`/`~` để lịch chạy không trôi bản âm thầm
                         (mặc định: station.json `hyperframes_version` → DEFAULT_HYPERFRAMES_VERSION)
    HYPERFRAMES_WORKDIR  thư mục chứa project render    (mặc định station.json `projects_dir`
                                                           → $VIDEO_STATION/projects)
    NODE_DIR             thư mục chứa node/npx            (rỗng = tìm trên PATH)
    FFMPEG_DIR           thư mục chứa ffmpeg/ffprobe      (rỗng = tìm trên PATH)
    VIDEO_FONT           font đứng đầu stack chữ          (mặc định stack bắt đầu bằng Inter)
    CHROME_BIN           Chrome cho công cụ chụp ảnh ngoài HyperFrames (tuỳ chọn)
    VOICE_STATION        trạm giọng (lồng tiếng, filler)  — tên cũ OMNIVOICE_DIR = thư mục
                         engine ($VOICE_STATION/omnivoice)

Hai chế độ cài (F17) dùng chung MỘT thứ tự phân giải trạm — `resolve_station()`:

    --station (lệnh đặt VIDEO_STATION trong tiến trình) → VIDEO_STATION → VIDEO_ROOT (cũ)
    → <repo>/studio.local.json ("station_path") → <repo>/workspace/ nếu có → ~/.video

`<repo>` là bản clone đã `pip install -e` (có `pyproject.toml` cạnh package); đặt
`VIDEO_STUDIO_REPO` để trỏ tường minh. Cài dạng wheel thì không có repo ⇒ bỏ hai tầng giữa.
"""
import json
import os
import re
import shutil
import warnings

from .contract import ContractError

LOCAL_CONFIG = "studio.local.json"
WORKSPACE = "workspace"
STATION_FILE = "station.json"

# Bản đã qua render hồi quy (PVi-T13, 20/09/2026): cùng index.html, cùng thời lượng, khung
# trùng tới từng điểm ảnh ở 3/6 mốc đo và PSNR 48–59 dB ở phần còn lại, dung lượng lệch
# +0,007 % — với điều kiện `render` khai `-q standard` (xem render.QUALITY).
DEFAULT_HYPERFRAMES_VERSION = "0.8.54"
_EXACT_VERSION = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.]+)?$")

DEFAULT_FONT_STACK = "Inter, 'Segoe UI', 'Helvetica Neue', Arial, sans-serif"


def env(name):
    """Đọc biến `name` (bỏ khoảng trắng; rỗng coi như chưa đặt)."""
    val = (os.environ.get(name) or "").strip()
    return val or None


def _expand(p):
    return os.path.abspath(os.path.expanduser(p))


def read_json(path):
    """-> (dict, lỗi|None). File không có ⇒ ({}, None); JSON hỏng ⇒ ({}, thông báo)."""
    if not path or not os.path.isfile(path):
        return {}, None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError) as e:
        return {}, f"{path}: {e}"
    if not isinstance(data, dict):
        return {}, f"{path}: không phải object JSON"
    return data, None


# ── repo + trạm ─────────────────────────────────────────────────────────────────────────

def repo_root():
    """Gốc bản clone repo nếu package được cài `-e` từ đó (hoặc VIDEO_STUDIO_REPO); không thì None."""
    r = env("VIDEO_STUDIO_REPO")
    if r:
        return _expand(r)
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if (os.path.isfile(os.path.join(here, "pyproject.toml"))
            and os.path.isdir(os.path.join(here, "video_studio"))):
        return here
    return None


def package_repo():
    """Thư mục chứa MÃ đang chạy (nơi có `skills/`, `templates/` đi kèm), kể cả khi
    VIDEO_STUDIO_REPO trỏ chỗ khác."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def local_config(repo=None):
    """Nội dung `<repo>/studio.local.json` (lựa chọn chế độ cài), {} nếu không có."""
    repo = repo or repo_root()
    return read_json(os.path.join(repo, LOCAL_CONFIG))[0] if repo else {}


def default_station():
    return os.path.join(os.path.expanduser("~"), ".video")


def has_marker(path):
    """Thư mục có phải một trạm video không: có station.json, có projects/, hoặc là trạm đời
    cũ (trước khi có station.json) có seed `demo/hyperframes.json`."""
    if not path or not os.path.isdir(path):
        return False
    return (os.path.isfile(os.path.join(path, STATION_FILE))
            or os.path.isdir(os.path.join(path, "projects"))
            or os.path.isfile(os.path.join(path, "demo", "hyperframes.json")))


def resolve_station():
    """-> (gốc trạm, nguồn). Nguồn ∈ VIDEO_STATION · VIDEO_ROOT · studio.local.json ·
    workspace · default. Đọc lại mỗi lần gọi."""
    st = env("VIDEO_STATION")
    if st:
        return _expand(st), "VIDEO_STATION"
    old = env("VIDEO_ROOT")
    if old:
        warnings.warn("Biến VIDEO_ROOT đã đổi tên thành VIDEO_STATION; tên cũ còn đọc được "
                      "một phiên bản nữa.", DeprecationWarning, stacklevel=2)
        return _expand(old), "VIDEO_ROOT"
    repo = repo_root()
    if repo:
        sp = (local_config(repo).get("station_path") or "").strip()
        if sp:
            sp = os.path.expanduser(sp)
            return (sp if os.path.isabs(sp) else os.path.abspath(os.path.join(repo, sp))), LOCAL_CONFIG
        ws = os.path.join(repo, WORKSPACE)
        if os.path.isdir(ws):
            return ws, WORKSPACE
    return default_station(), "default"


def station_dir():
    return resolve_station()[0]


def station_info(station=None):
    """Nội dung `station.json` của trạm ({} nếu chưa có hoặc hỏng)."""
    return read_json(os.path.join(station or station_dir(), STATION_FILE))[0]


def _rel_to_station(st, rel):
    rel = os.path.expanduser(str(rel))
    return rel if os.path.isabs(rel) else os.path.join(st, *rel.replace("\\", "/").split("/"))


def projects_dir():
    """Thư mục project render: HYPERFRAMES_WORKDIR → station.json projects_dir → <trạm>/projects."""
    w = env("HYPERFRAMES_WORKDIR")
    if w:
        return _expand(w)
    st = station_dir()
    return _rel_to_station(st, station_info(st).get("projects_dir") or "projects")


# ── HyperFrames ─────────────────────────────────────────────────────────────────────────

def check_version(v, origin="HYPERFRAMES_VERSION"):
    v = (v or "").strip()
    if not _EXACT_VERSION.match(v):
        raise ContractError(
            f"{origin}={v!r} không phải một bản cụ thể (x.y.z). Không dùng latest/^/~: lịch chạy "
            "phải gọi đúng bản đã kiểm, nâng bản là việc có chủ đích (`video-studio doctor "
            "--check-updates` chỉ báo).")
    return v


def hyperframes_version(station=None):
    """HYPERFRAMES_VERSION → station.json hyperframes_version (của `station`, mặc định trạm đang
    phân giải) → mặc định. Luôn trả bản đã kiểm định dạng."""
    v = env("HYPERFRAMES_VERSION")
    if v:
        return check_version(v)
    sv = station_info(station).get("hyperframes_version")
    if sv:
        return check_version(str(sv), "station.json hyperframes_version")
    return DEFAULT_HYPERFRAMES_VERSION


def hyperframes_spec(version=None):
    """Chuỗi gói cho npx: `hyperframes@<bản cụ thể>`."""
    return "hyperframes@" + check_version(version or hyperframes_version())


# ── công cụ ngoài ───────────────────────────────────────────────────────────────────────

def _tool(name, dir_var):
    d = env(dir_var)
    if d:
        found = shutil.which(name, path=_expand(d))
        if found:
            return found
    return shutil.which(name)


def node_exe():
    return _tool("node", "NODE_DIR")


def npx_exe():
    """npx: NODE_DIR → PATH. Windows trả `npx.cmd` — gọi bằng argv list, `shell=False`."""
    return _tool("npx", "NODE_DIR")


def npm_exe():
    return _tool("npm", "NODE_DIR")


def ffmpeg_exe():
    return _tool("ffmpeg", "FFMPEG_DIR")


def ffprobe_exe():
    return _tool("ffprobe", "FFMPEG_DIR")


def chrome_bin():
    c = env("CHROME_BIN")
    return _expand(c) if c else None


def font_stack():
    """Stack font CSS: VIDEO_FONT (nếu đặt) đứng đầu, rồi Inter và các font hệ thống."""
    f = env("VIDEO_FONT")
    return f"'{f}', {DEFAULT_FONT_STACK}" if f else DEFAULT_FONT_STACK


def hyperframes_cache():
    """Cache runtime của HyperFrames (Chromium headless, font) — ~/.cache/hyperframes."""
    return os.path.join(os.path.expanduser("~"), ".cache", "hyperframes")


# ── trạm giọng ──────────────────────────────────────────────────────────────────────────

def voice_station():
    """Gốc trạm giọng: VOICE_STATION → cha của OMNIVOICE_DIR (tên cũ) → None."""
    v = env("VOICE_STATION")
    if v:
        return _expand(v)
    eng = env("OMNIVOICE_DIR")
    if eng:
        return os.path.dirname(_expand(eng))
    return None


def voice_engine_dir():
    """Thư mục engine giọng: OMNIVOICE_DIR nếu chỉ tên cũ được đặt, không thì <trạm giọng>/omnivoice."""
    if not env("VOICE_STATION") and env("OMNIVOICE_DIR"):
        return _expand(env("OMNIVOICE_DIR"))
    vs = voice_station()
    return os.path.join(vs, "omnivoice") if vs else None


def filler_source_candidates():
    """Chỗ có thể chứa filler cho short tin (trạm giọng đời cũ giữ ở engine, đời mới ở assets)."""
    out = []
    eng = voice_engine_dir()
    if eng:
        out.append(os.path.join(eng, "assets", "news_short", "fillers"))
    vs = voice_station()
    if vs:
        alt = os.path.join(vs, "assets", "news_short", "fillers")
        if alt not in out:
            out.append(alt)
    return out
