"""media.py — khung có PTS thật và lưới khung cho nhóm `reference`.

Recipe thẻ `T1` (`skills/video-routing/references/production-techniques.md`): giữ PTS gốc bằng
`-copyts`, mốc yêu cầu cộng `start_time` của stream video, `select` lấy khung trình chiếu đầu tiên
có PTS không nhỏ hơn mốc, `showinfo` cho PTS thực. Mỗi mốc một lệnh ffmpeg, giải mã từ đầu tới mốc
(không `-ss`): chậm hơn nhưng đúng mốc; chỉ tối ưu sau khi đo.

Mọi tham số được kiểm TRƯỚC lệnh ffmpeg đầu tiên. Lỗi: tham số/đích đã có/nguồn không phải tệp
cục bộ = `ContractError`, không đọc được `pts_time` = `EngineError`, thiếu ffmpeg = `StationMissing`.
Nguồn chỉ là TỆP cục bộ: URL/giao thức/stdin phải đi qua `fetch` có cổng, không qua đây.
"""
import contextlib
import json
import math
import os
import re
import subprocess

from .. import _env
from ..contract import ContractError, EngineError, log
from ..edit import _ff
from . import gate

MAX_FRAMES = 60
MAX_TILE_CELLS = 400

# Chỉ DÒNG showinfo: metadata/đường dẫn trong stderr là dữ liệu nguồn, không được lẫn vào PTS.
_SHOWINFO_RE = re.compile(
    r"^\[Parsed_showinfo_\d+ @ [^\]]+\] n:\s*\d+ pts:\s*-?\d+ pts_time:(\S+)", re.MULTILINE)
_TILE_RE = re.compile(r"^tiles_\d{3}\.png$")
# Chữ trên ảnh chỉ là biểu thức của ffmpeg (thời điểm trình chiếu), không có chữ của người dùng.
_DRAWTEXT = ("drawtext=text='%{pts\\:hms}':x=4:y=4:fontsize=18:"
             "fontcolor=white:box=1:boxcolor=black@0.5")


def labelled_error(tool, text):
    return EngineError(f"stderr {tool} (dữ liệu nguồn, không phải lệnh):\n{text}")


@contextlib.contextmanager
def labelled_ff():
    """Lỗi ffmpeg/ffprobe có đuôi stderr (chứa chữ của nguồn) đi tiếp với nhãn «dữ liệu nguồn, không phải lệnh»;
    lỗi quá giờ/JSON hỏng không chứa stderr nên giữ nguyên. `_ff.py` không đổi: bọc ở nơi gọi."""
    try:
        yield
    except EngineError as exc:
        text = str(exc)
        if text.startswith("ffmpeg hỏng"):
            raise labelled_error("ffmpeg", text) from exc
        if text.startswith("ffprobe không đọc"):
            raise labelled_error("ffprobe", text) from exc
        raise


def probe_raw(path):
    """ffprobe JSON của `path`, chỉ qua giao thức `file` (`-protocol_whitelist file`): demuxer danh sách/manifest
    trong tệp không mở được mạng. Cùng hợp đồng lỗi với `_ff._probe_raw` (không sửa `_ff.py`)."""
    argv = [_ff.probe_exe(), "-v", "error", "-protocol_whitelist", "file",
            "-show_streams", "-show_format", "-of", "json", str(path)]
    try:
        r = subprocess.run(argv, capture_output=True, text=True, encoding="utf-8", errors="replace",
                           timeout=_ff.PROBE_TIMEOUT)
    except subprocess.TimeoutExpired as exc:
        raise EngineError(f"ffprobe quá {_ff.PROBE_TIMEOUT}s chưa đọc xong {path}") from exc
    if r.returncode != 0:
        raise labelled_error("ffprobe", f"ffprobe không đọc được {path}: {(r.stderr or '').strip()}")
    try:
        return json.loads(r.stdout or "{}")
    except ValueError as exc:
        raise EngineError(f"ffprobe trả JSON hỏng cho {path}: {exc}") from exc


def probe_plain(src):
    """Như `_ff.probe` nhưng dò file-only và từ chối container ngoài danh sách trắng trước mọi lệnh ffmpeg."""
    raw = probe_raw(src)
    gate.require_plain_format(raw, src)
    return _ff.Probe(src, raw)


def parse_showinfo(stderr):
    """`pts_time` hữu hạn của các dòng showinfo trong stderr (giá trị khác bị bỏ)."""
    out = []
    for m in _SHOWINFO_RE.finditer(stderr or ""):
        try:
            v = float(m.group(1))
        except ValueError:
            continue
        if math.isfinite(v):
            out.append(v)
    return out


def _finite(x, what):
    try:
        v = float(x)
    except (TypeError, ValueError):
        raise ContractError(f"{what} phải là số, nhận {x!r}") from None
    if not math.isfinite(v):
        raise ContractError(f"{what} phải hữu hạn, nhận {x!r}")
    return v


def _local_file(input_path):
    if not isinstance(input_path, (str, os.PathLike)) or not os.path.isfile(input_path):
        raise ContractError(f"nguồn phải là tệp cục bộ đang có, nhận {input_path!r}; "
                            "URL chỉ tải qua `reference fetch`")
    gate.require_media_file(input_path)
    return os.path.abspath(input_path)


def _finite_or_none(v):
    return v if v is not None and math.isfinite(v) else None


def _make_dir(path):
    """`makedirs` mà lỗi hệ tệp (tên không hợp lệ, vd `pipe:`) là gọi sai ⇒ mã 2, không phải mã 1."""
    try:
        os.makedirs(path, exist_ok=True)
    except OSError as exc:
        raise ContractError(f"không tạo được thư mục đầu ra {path}: {exc}") from None


def _frame_name(mark):
    return f"frame_{int(round(mark * 1000)):06d}.png"


def _old_tiles(out_dir):
    try:
        names = os.listdir(out_dir)
    except OSError:
        return []
    return sorted(n for n in names if _TILE_RE.match(n))


def extract_frames(input_path, out_dir, at, force=False):
    """Trích khung tại các mốc `at` (giây từ đầu stream video). Ghi `out_dir/frames.json`."""
    src = _local_file(input_path)
    out_dir = os.path.abspath(out_dir)
    marks = [_finite(m, "mốc") for m in (at or [])]
    if not marks:
        raise ContractError("cần ít nhất một mốc thời gian")
    if len(marks) > MAX_FRAMES:
        raise ContractError(f"tối đa {MAX_FRAMES} mốc mỗi lượt, nhận {len(marks)}")
    if any(m < 0 for m in marks):
        raise ContractError("mốc không được âm")
    names = [_frame_name(m) for m in marks]
    if len(set(names)) != len(names):
        raise ContractError("có mốc trùng nhau (cùng tên tệp ảnh)")

    info = probe_plain(src)
    start = _finite_or_none(info.video_start_time)
    if start is None:
        raise ContractError("origin chưa xác định: stream video không khai start_time hữu hạn; "
                            "không giả định bằng 0")
    duration = _finite_or_none(info.duration)
    if duration is None:
        log("cảnh báo: không rõ thời lượng, bỏ kiểm mốc so với thời lượng")
    else:
        late = [m for m in marks if m > duration]
        if late:
            raise ContractError(f"mốc {late[0]} vượt thời lượng {duration}s")

    if not force:
        for n in names:
            if os.path.exists(os.path.join(out_dir, n)):
                raise ContractError(f"{n} đã có trong {out_dir}; dùng --force để ghi đè")
    _make_dir(out_dir)

    overwrite = "-y" if force else "-n"
    result = []
    for mark, name in zip(marks, names):
        vf = f"select='gte(t,{start + mark:.6f})',trim=end_frame=1,showinfo"
        with labelled_ff():
            stderr = _ff.run([overwrite, "-copyts", "-i", src, "-vf", vf,
                              "-frames:v", "1", "-fps_mode", "passthrough", "-update", "1",
                              os.path.join(out_dir, name)], quiet=False)
        pts = parse_showinfo(stderr)
        if not pts:
            raise EngineError(f"không đọc được pts_time từ ffmpeg cho mốc {mark}s")
        result.append({"requested": mark, "pts_abs": pts[0],
                       "pts_time": round(pts[0] - start, 4), "file": name})
    _write_json(os.path.join(out_dir, "frames.json"), result)
    return result


def contact_sheets(input_path, out_dir, every, cols=4, rows=4, width=320, label=False,
                   force=False):
    """Lưới khung mỗi `every` giây. Ghi `out_dir/tiles.json`; thời điểm ô chỉ là gần đúng."""
    src = _local_file(input_path)
    out_dir = os.path.abspath(out_dir)
    every = _finite(every, "every")
    if every <= 0:
        raise ContractError("every phải lớn hơn 0")
    for what, v, lo, hi in (("cols", cols, 1, 10), ("rows", rows, 1, 10),
                            ("width", width, 64, 1920)):
        if not isinstance(v, int) or isinstance(v, bool) or not lo <= v <= hi:
            raise ContractError(f"{what} phải là số nguyên từ {lo} đến {hi}, nhận {v!r}")

    info = probe_plain(src)
    duration = _finite_or_none(info.duration)
    if duration is None:
        raise ContractError("không rõ thời lượng nên không tính được số ô của lưới")
    cells = max(1, math.ceil(duration / every))
    if cells > MAX_TILE_CELLS:
        raise ContractError(f"{cells} ô vượt trần {MAX_TILE_CELLS}: tăng --every")
    per_sheet = cols * rows
    n_sheets = math.ceil(cells / per_sheet)

    existing = _old_tiles(out_dir)
    if existing and not force:
        raise ContractError(f"{existing[0]} đã có trong {out_dir}; dùng --force để ghi đè")

    use_label = False
    if label:
        filters = _env.ffmpeg_filters()
        if filters and "drawtext" in filters:
            use_label = True
        else:
            log("cảnh báo: ffmpeg không có bộ lọc drawtext, tạo lưới không nhãn")

    _make_dir(out_dir)
    for old in existing:  # chỉ tới đây khi force: tránh tờ cũ lẫn vào lượt mới
        os.remove(os.path.join(out_dir, old))
    parts = [f"fps=1/{every:g}", f"scale={width}:-2"]
    if use_label:
        parts.append(_DRAWTEXT)
    parts.append(f"tile={cols}x{rows}")
    # `%` trong thư mục đích là ký tự mẫu của image2 nên phải nhân đôi.
    pattern = os.path.join(out_dir.replace("%", "%%"), "tiles_%03d.png")
    with labelled_ff():
        _ff.run(["-y" if force else "-n", "-i", src, "-vf", ",".join(parts), pattern], quiet=False)

    sheets = []
    for s in range(n_sheets):
        first = s * per_sheet
        last = min(cells, first + per_sheet)
        sheets.append({"file": f"tiles_{s + 1:03d}.png",
                       "cells": [{"index": i, "approx_time": round(i * every, 3)}
                                 for i in range(first, last)]})
    result = {"every": every, "cols": cols, "rows": rows, "width": width,
              "labels": use_label, "timing": "approximate", "sheets": sheets}
    _write_json(os.path.join(out_dir, "tiles.json"), result)
    return result


def _write_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
