"""edl.py — hợp đồng dữ liệu của bước cắt: **EDL** (edit decision list).

    {
      "sources":  {"<tên>": "<đường dẫn file quay>"},          // tương đối = so với file EDL
      "ranges":   [{"source": "<tên>", "start": 12.4, "end": 19.0, "beat": "ghi chú"?,
                    "grade": "<preset|filter>"?}],
      "grade":    "auto" | "<tên preset>" | "<chuỗi filter ffmpeg>",   // mặc định "auto"
      "overlays": [{"file": "<mp4/mov có alpha>", "start_in_output": 3.0, "duration": 2.5}],
      "subtitles": "master.srt" | null
    }

Nguồn: `browser-use/video-use` (MIT, © 2026 Browser Use) — khuôn EDL đọc từ `helpers/render.py`
bản vendored `92c2b34`; **đã sửa**: upstream không kiểm gì, cứ `edl["ranges"]` mà đọc. Một EDL
thiếu khoá ở đó là `KeyError` giữa chừng — sau khi đã cắt mất mười phút. Ở đây EDL sai là
**mã 2 trước khi chạm ffmpeg**, và thông báo nói rõ đoạn thứ mấy sai chỗ nào.
"""
import json
import os

from ..contract import ContractError

RANGE_KEYS = {"source", "start", "end", "beat", "note", "grade"}
OVERLAY_KEYS = {"file", "start_in_output", "duration"}

__all__ = ["load", "validate", "resolve", "total_duration"]


def _num(value, where):
    try:
        return float(value)
    except (TypeError, ValueError):
        raise ContractError(f"{where}: phải là số, nhận {value!r}") from None


def validate(data, origin="edl"):
    """Kiểm EDL. -> bản đã chuẩn hoá. Sai ⇒ ContractError (mã 2)."""
    if not isinstance(data, dict):
        raise ContractError(f"{origin}: EDL phải là một object JSON")
    sources = data.get("sources")
    if not isinstance(sources, dict) or not sources:
        raise ContractError(f"{origin}: thiếu \"sources\" — {{tên: đường dẫn file quay}}")
    for name, path in sources.items():
        if not isinstance(path, str) or not path.strip():
            raise ContractError(f"{origin}: sources[{name!r}] phải là một đường dẫn")
    ranges = data.get("ranges")
    if not isinstance(ranges, list) or not ranges:
        raise ContractError(f"{origin}: thiếu \"ranges\" — danh sách đoạn cắt theo thứ tự dựng")
    out_ranges = []
    for i, r in enumerate(ranges):
        where = f"{origin}: ranges[{i}]"
        if not isinstance(r, dict):
            raise ContractError(f"{where} phải là object")
        unknown = set(r) - RANGE_KEYS
        if unknown:
            raise ContractError(f"{where} có khoá lạ: {', '.join(sorted(unknown))}")
        src = r.get("source")
        if src not in sources:
            raise ContractError(f"{where}: source {src!r} không có trong \"sources\" "
                                f"({', '.join(sorted(sources))})")
        start, end = _num(r.get("start"), where + ".start"), _num(r.get("end"), where + ".end")
        if end <= start:
            raise ContractError(f"{where}: end ({end}) phải lớn hơn start ({start})")
        if start < 0:
            raise ContractError(f"{where}: start âm ({start})")
        out_ranges.append({**r, "start": start, "end": end})
    overlays = data.get("overlays") or []
    if not isinstance(overlays, list):
        raise ContractError(f"{origin}: \"overlays\" phải là danh sách")
    out_over = []
    for i, ov in enumerate(overlays):
        where = f"{origin}: overlays[{i}]"
        if not isinstance(ov, dict):
            raise ContractError(f"{where} phải là object")
        unknown = set(ov) - OVERLAY_KEYS
        if unknown:
            raise ContractError(f"{where} có khoá lạ: {', '.join(sorted(unknown))}")
        if not isinstance(ov.get("file"), str) or not ov["file"].strip():
            raise ContractError(f"{where}: thiếu \"file\"")
        out_over.append({"file": ov["file"],
                         "start_in_output": _num(ov.get("start_in_output"),
                                                 where + ".start_in_output"),
                         "duration": _num(ov.get("duration"), where + ".duration")})
    subs = data.get("subtitles")
    if subs is not None and not isinstance(subs, str):
        raise ContractError(f"{origin}: \"subtitles\" phải là đường dẫn .srt hoặc null")
    grade = data.get("grade", "auto")
    if grade is not None and not isinstance(grade, str):
        raise ContractError(f"{origin}: \"grade\" phải là chuỗi (\"auto\", tên preset, hoặc "
                            "chuỗi filter ffmpeg)")
    return {"sources": dict(sources), "ranges": out_ranges, "overlays": out_over,
            "subtitles": subs, "grade": grade if grade is not None else "none"}


def load(path):
    if not path or not os.path.isfile(path):
        raise ContractError(f"không có file EDL: {path}")
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
    except ValueError as e:
        raise ContractError(f"{path}: JSON hỏng — {e}") from e
    return validate(data, origin=os.path.basename(path))


def resolve(rel, base):
    """Đường trong EDL: tuyệt đối thì giữ, tương đối thì so với THƯ MỤC CHỨA EDL (không phải cwd)."""
    rel = os.path.expanduser(str(rel))
    return os.path.abspath(rel if os.path.isabs(rel) else os.path.join(base, rel))


def total_duration(data):
    return round(sum(r["end"] - r["start"] for r in data["ranges"]), 3)
