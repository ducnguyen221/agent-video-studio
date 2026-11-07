"""media.py — khung có PTS thật và lưới khung cho nhóm `reference`.

Recipe thẻ `T1` (`skills/video-routing/references/production-techniques.md`): giữ PTS gốc bằng
`-copyts`, mốc yêu cầu cộng `start_time` của stream video, `select` lấy khung trình chiếu đầu tiên
có PTS không nhỏ hơn mốc, `showinfo` cho PTS thực. Mỗi mốc một lệnh ffmpeg, giải mã từ đầu tới mốc
(không `-ss`): chậm hơn nhưng đúng mốc; chỉ tối ưu sau khi đo.

Mọi tham số được kiểm TRƯỚC lệnh ffmpeg đầu tiên. Lỗi: tham số/đích đã có = `ContractError`,
không đọc được `pts_time` = `EngineError`, thiếu ffmpeg = `StationMissing`.
"""
import glob
import json
import math
import os
import re

from .. import _env
from ..contract import ContractError, EngineError, log
from ..edit import _ff

MAX_FRAMES = 60
MAX_TILE_CELLS = 400

_PTS_RE = re.compile(r"pts_time:\s*(-?[0-9.]+(?:[eE][-+]?[0-9]+)?|nan|inf|-inf)", re.IGNORECASE)
# Chữ trên ảnh chỉ là biểu thức của ffmpeg (thời điểm trình chiếu), không có chữ của người dùng.
_DRAWTEXT = ("drawtext=text='%{pts\\:hms}':x=4:y=4:fontsize=18:"
             "fontcolor=white:box=1:boxcolor=black@0.5")


def parse_showinfo(stderr):
    """Mọi `pts_time` hữu hạn trong stderr của `showinfo` (giá trị khác bị bỏ)."""
    out = []
    for m in _PTS_RE.finditer(stderr or ""):
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


def _frame_name(mark):
    return f"frame_{int(round(mark * 1000)):06d}.png"


def extract_frames(input_path, out_dir, at, force=False):
    """Trích khung tại các mốc `at` (giây từ đầu stream video). Ghi `out_dir/frames.json`."""
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

    info = _ff.probe(input_path)
    if info.video_start_time is None:
        raise ContractError("origin chưa xác định: stream video không khai start_time hữu hạn; "
                            "không giả định bằng 0")
    if info.duration is None:
        log("cảnh báo: không rõ thời lượng, bỏ kiểm mốc so với thời lượng")
    else:
        late = [m for m in marks if m > info.duration]
        if late:
            raise ContractError(f"mốc {late[0]} vượt thời lượng {info.duration}s")

    if not force:
        for n in names:
            if os.path.exists(os.path.join(out_dir, n)):
                raise ContractError(f"{n} đã có trong {out_dir}; dùng --force để ghi đè")
    os.makedirs(out_dir, exist_ok=True)

    result = []
    for mark, name in zip(marks, names):
        t_abs = info.video_start_time + mark
        vf = f"select='gte(t,{t_abs:.6f})',trim=end_frame=1,showinfo"
        stderr = _ff.run(["-y", "-copyts", "-i", str(input_path), "-vf", vf,
                          "-frames:v", "1", "-fps_mode", "passthrough", "-update", "1",
                          os.path.join(out_dir, name)], quiet=False)
        pts = parse_showinfo(stderr)
        if not pts:
            raise EngineError(f"không đọc được pts_time từ ffmpeg cho mốc {mark}s")
        result.append({"requested": mark, "pts_abs": pts[0],
                       "pts_time": round(pts[0] - info.video_start_time, 4), "file": name})
    _write_json(os.path.join(out_dir, "frames.json"), result)
    return result


def contact_sheets(input_path, out_dir, every, cols=4, rows=4, width=320, label=False,
                   force=False):
    """Lưới khung mỗi `every` giây. Ghi `out_dir/tiles.json`; thời điểm ô chỉ là gần đúng."""
    every = _finite(every, "every")
    if every <= 0:
        raise ContractError("every phải lớn hơn 0")
    for what, v, lo, hi in (("cols", cols, 1, 10), ("rows", rows, 1, 10),
                            ("width", width, 64, 1920)):
        if not isinstance(v, int) or isinstance(v, bool) or not lo <= v <= hi:
            raise ContractError(f"{what} phải là số nguyên từ {lo} đến {hi}, nhận {v!r}")

    info = _ff.probe(input_path)
    if info.duration is None:
        raise ContractError("không rõ thời lượng nên không tính được số ô của lưới")
    cells = max(1, math.ceil(info.duration / every))
    if cells > MAX_TILE_CELLS:
        raise ContractError(f"{cells} ô vượt trần {MAX_TILE_CELLS}: tăng --every")
    per_sheet = cols * rows
    n_sheets = math.ceil(cells / per_sheet)

    existing = glob.glob(os.path.join(out_dir, "tiles_*.png"))
    if existing and not force:
        raise ContractError(f"{os.path.basename(existing[0])} đã có trong {out_dir}; "
                            "dùng --force để ghi đè")

    use_label = False
    if label:
        filters = _env.ffmpeg_filters()
        if filters and "drawtext" in filters:
            use_label = True
        else:
            log("cảnh báo: ffmpeg không có bộ lọc drawtext, tạo lưới không nhãn")

    os.makedirs(out_dir, exist_ok=True)
    for old in existing:  # chỉ tới đây khi force: tránh tờ cũ lẫn vào lượt mới
        os.remove(old)
    every_s = f"{every:g}"
    parts = [f"fps=1/{every_s}", f"scale={width}:-2"]
    if use_label:
        parts.append(_DRAWTEXT)
    parts.append(f"tile={cols}x{rows}")
    _ff.run(["-y", "-i", str(input_path), "-vf", ",".join(parts),
             os.path.join(out_dir, "tiles_%03d.png")], quiet=False)

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
