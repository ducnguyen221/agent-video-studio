"""projects.py — thư mục project HyperFrames bên trong TRẠM.

Một "project HyperFrames" = ba file cấu hình (`package.json`, `hyperframes.json`, `meta.json`)
+ một `index.html` do template sinh ra mỗi lần render. Repo không giữ project nào: mọi project
sống trong trạm, dưới `<trạm>/projects/<tên>/`.

Bản `.tts` đời cũ neo đường cứng (`C:\\…\\.video\\news`, `…\\.video\\demo`) ngay trong template.
Ở đây template gọi `projects.ensure("news")`: chỗ đặt do `_env` quyết, seed cấu hình lấy từ
`<trạm>/demo/` đúng như `_ensure_project()` cũ vẫn làm (chép một lần, không đè bản người dùng
đã sửa).

Thiếu trạm hoặc thiếu seed ⇒ `StationMissing` (mã 3) kèm câu lệnh phải chạy — KHÔNG tự dựng
cấu hình đoán mò, vì một `hyperframes.json` sai lặng lẽ cho ra video sai tỉ lệ / sai fps.
"""
import os
import shutil

from . import _env
from .contract import ContractError, StationMissing

CONFIG_FILES = ("package.json", "hyperframes.json", "meta.json")
SEED_PROJECT = "demo"

__all__ = ["CONFIG_FILES", "SEED_PROJECT", "project_dir", "seed_dir", "ensure", "assets_dir",
           "filler_dir", "scratch_file"]


def _check_name(name):
    name = (name or "").strip()
    if not name or name in (".", ".."):
        raise ContractError("tên project rỗng")
    if os.path.isabs(name) or "/" in name or "\\" in name or os.pardir in name.split():
        raise ContractError(f"tên project phải là một tên thư mục đơn, không phải đường dẫn: {name!r}")
    return name


def project_dir(name, station=None):
    """Đường dẫn project (KHÔNG tạo gì)."""
    name = _check_name(name)
    if station:
        return os.path.join(_env._rel_to_station(_env._expand(station), "projects"), name)
    return os.path.join(_env.projects_dir(), name)


def seed_dir(station=None):
    """`<trạm>/demo` — project mẫu mà `init` dựng; nguồn chép cấu hình cho project mới."""
    st = _env._expand(station) if station else _env.station_dir()
    return os.path.join(st, SEED_PROJECT)


def ensure(name, station=None):
    """Tạo (nếu cần) project `name` trong trạm, chép cấu hình còn thiếu từ `demo/`. -> đường dẫn.

    Giữ nguyên hành vi `_ensure_project()` cũ: chỉ chép file CHƯA có, không bao giờ đè.
    """
    proj = project_dir(name, station)
    st = _env._expand(station) if station else _env.station_dir()
    if not os.path.isdir(st):
        raise StationMissing(
            f"chưa có trạm video ở {st} — chạy: video-studio init --station \"{st}\"")
    seed = seed_dir(station)
    os.makedirs(proj, exist_ok=True)
    for fn in CONFIG_FILES:
        dst, src = os.path.join(proj, fn), os.path.join(seed, fn)
        if not os.path.isfile(dst) and os.path.isfile(src):
            shutil.copy2(src, dst)
    missing = [fn for fn in CONFIG_FILES if not os.path.isfile(os.path.join(proj, fn))]
    if "hyperframes.json" in missing:
        raise StationMissing(
            f"project {name!r} thiếu {', '.join(missing)} và trạm chưa có seed ở {seed} — "
            f"chạy: video-studio init --station \"{st}\" (dựng demo/ từ templates/_seed của repo)")
    return proj


def assets_dir(name, sub="", station=None, create=False):
    """`<project>/assets[/<sub>]` — ảnh filler, b-roll, clip do người dùng cấp."""
    d = os.path.join(project_dir(name, station), "assets", *[p for p in sub.split("/") if p])
    if create:
        os.makedirs(d, exist_ok=True)
    return d


def filler_dir(name="news", station=None):
    """Ảnh filler on-brand của project (bản cũ: `<engine giọng>/assets/news_short/fillers`)."""
    return assets_dir(name, "fillers", station)


def scratch_file(*parts, station=None):
    """File nháp trong `<trạm>/scratch/…` (tạo thư mục cha)."""
    st = _env._expand(station) if station else _env.station_dir()
    p = os.path.join(st, "scratch", *parts)
    os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
    return p
