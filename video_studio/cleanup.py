"""`video-studio cleanup` — local, CPU-only edits to an existing video.

The supported MVP deliberately accepts a narrow media profile (SDR, 8-bit 4:2:0,
unrotated video). It uses FFmpeg filters directly; it does not run the broader edit
pipeline, which can resize, tone-map, or alter audio.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import statistics
import subprocess
import uuid
from pathlib import Path

from . import _paths, contract
from .contract import ContractError, EngineError, StationMissing
from .edit import _ff

METHODS = ("delogo", "blur", "cover", "crop")
MANIFEST_SUFFIX = ".cleanup.json"
MANIFEST_VERSION = 1
SUPPORTED_PIX_FMTS = {"yuv420p"}
TIMING_SCAN_TIMEOUT = 3600
DELIVERY_NOTE = {
    "delogo": "delogo nội suy pixel lân cận; không đảm bảo khôi phục nền gốc",
    "blur": "blur che chi tiết trong ROI; không khôi phục nền gốc",
    "cover": "cover tô màu đặc trong ROI; không khôi phục nền gốc",
    "crop": "crop loại bỏ phần khung ngoài ROI; không khôi phục nền gốc",
}


def parse_roi(value: str) -> tuple[int, int, int, int]:
    """Parse x,y,width,height (integer pixels, top-left origin)."""
    try:
        parts = value.split(",")
        if len(parts) != 4 or any(not part.strip() for part in parts):
            raise ValueError
        values = tuple(int(part.strip(), 10) for part in parts)
    except (AttributeError, TypeError, ValueError) as exc:
        raise ContractError("--roi cần bốn số nguyên x,y,width,height tính bằng pixel") from exc
    if values[0] < 0 or values[1] < 0 or values[2] <= 0 or values[3] <= 0:
        raise ContractError("--roi cần x,y không âm và width,height lớn hơn 0")
    return values


def validate_roi(roi: tuple[int, int, int, int], width: int, height: int) -> None:
    x, y, w, h = roi
    if width <= 0 or height <= 0 or x + w > width or y + h > height:
        raise ContractError(f"ROI {roi} nằm ngoài khung {width}x{height}")
    if any(value % 2 for value in roi):
        raise ContractError("Phase 1 cần x,y,width,height là số chẵn để giữ đúng ROI trên video 4:2:0")


def validate_method_roi(method: str, roi: tuple[int, int, int, int],
                        width: int, height: int) -> None:
    validate_roi(roi, width, height)
    x, y, w, h = roi
    if method == "delogo" and (x < 1 or y < 1 or x + w >= width or y + h >= height):
        raise ContractError("delogo cần cách mép khung ít nhất 1 pixel ở cả bốn phía")


def validate_range(start: float, end: float, duration: float) -> tuple[float, float]:
    values = (start, end, duration)
    if any(not math.isfinite(value) for value in values):
        raise ContractError("--start, --end và duration phải là số hữu hạn")
    if duration <= 0 or start < 0 or end <= start or end > duration + 0.001:
        raise ContractError(f"khoảng thời gian cần 0 <= start < end <= {duration:.3f}s")
    return float(start), min(float(end), float(duration))


def validate_media(info: _ff.Probe) -> dict:
    """Reject inputs whose rotation, HDR, or pixel format we cannot preserve safely."""
    media = describe_media(info)
    if media["width"] <= 0 or media["height"] <= 0 or not media["duration"]:
        raise ContractError("không đọc được kích thước hoặc thời lượng video")
    if info.rotation:
        raise ContractError(f"video có rotation metadata {info.rotation}°; Phase 1 chưa xử lý rotation")
    if info.hdr:
        raise ContractError("video HDR chưa được hỗ trợ; Phase 1 không tự tone-map")
    if info.pix_fmt not in SUPPORTED_PIX_FMTS:
        raise ContractError(
            f"pixel format {info.pix_fmt or 'không rõ'} chưa được hỗ trợ; cần SDR 8-bit yuv420p")
    if info.video_start_time is None or any(value is None for value in info.audio_start_times):
        raise ContractError("thiếu mốc thời gian stream; không thể xác nhận đồng bộ audio/video")
    return media


def describe_media(info: _ff.Probe) -> dict:
    """Describe an input even when the current editor refuses to process its media profile."""
    reasons = []
    if info.rotation:
        reasons.append(f"rotation metadata {info.rotation}° chưa hỗ trợ")
    if info.hdr:
        reasons.append("HDR chưa hỗ trợ")
    if info.pix_fmt not in SUPPORTED_PIX_FMTS:
        reasons.append(f"pixel format {info.pix_fmt or 'không rõ'} chưa hỗ trợ")
    if info.width <= 0 or info.height <= 0 or info.duration is None or info.duration <= 0:
        reasons.append("thiếu kích thước hoặc thời lượng video")
    if info.video_start_time is None or any(value is None for value in info.audio_start_times):
        reasons.append("thiếu mốc thời gian stream để kiểm tra đồng bộ audio/video")
    return {
        "width": info.width,
        "height": info.height,
        "duration": info.duration,
        "video_start_time": info.video_start_time,
        "audio_start_times": info.audio_start_times,
        "rotation": info.rotation,
        "hdr": info.hdr,
        "pix_fmt": info.pix_fmt,
        "video_codec": info.video_codec,
        "color_range": info.color_range,
        "color_transfer": info.color_transfer,
        "color_primaries": info.color_primaries,
        "color_space": info.color_space,
        "avg_frame_rate": info.avg_frame_rate,
        "r_frame_rate": info.r_frame_rate,
        "fps": info.fps,
        "vfr_check": "NOT_CHECKED",
        "audio_streams": len(info.audio),
        "supported_for_cleanup": not reasons,
        "support_notes": reasons,
    }


def build_filter(method: str, roi: tuple[int, int, int, int], start: float,
                 end: float, color: str = "#000000") -> tuple[str, str]:
    """Return a constrained FFmpeg filter graph and its output video label."""
    if method not in METHODS:
        raise ContractError(f"method không hợp lệ: {method}")
    x, y, w, h = roi
    enable = f"between(t,{start:.9g},{end:.9g})"
    if method == "delogo":
        return (f"[0:v:0]delogo=x={x}:y={y}:w={w}:h={h}:show=0:enable='{enable}'[vout]",
                "vout")
    if method == "cover":
        rgb = validate_color(color)
        return (f"[0:v:0]drawbox=x={x}:y={y}:w={w}:h={h}:color={rgb}:t=fill:"
                f"enable='{enable}'[vout]", "vout")
    if method == "crop":
        return f"[0:v:0]crop=w={w}:h={h}:x={x}:y={y}[vout]", "vout"
    luma_limit = max(0, (min(w, h) - 1) // 2)
    chroma_size = (min(w, h) + 1) // 2
    chroma_limit = max(0, (chroma_size - 1) // 2)
    luma_radius = min(12, luma_limit)
    chroma_radius = min(12, chroma_limit)
    return (f"[0:v:0]split[base][region];[region]crop={w}:{h}:{x}:{y},"
            f"boxblur={luma_radius}:2:{chroma_radius}:2[blurred];[base][blurred]overlay={x}:{y}:"
            f"enable='{enable}'[vout]", "vout")


def validate_color(value: str) -> str:
    color = str(value).strip()
    if len(color) != 7 or color[0] != "#" or any(c not in "0123456789abcdefABCDEF"
                                                  for c in color[1:]):
        raise ContractError("--color nhận mã màu dạng #RRGGBB")
    return "0x" + color[1:].lower()


def _absolute(path: str) -> str:
    return os.path.abspath(os.path.expanduser(path))


def _source_file(path: str) -> str:
    resolved = _absolute(path)
    if not os.path.isfile(resolved):
        raise ContractError(f"không có file video: {resolved}")
    return resolved


def _check_output_path(source: str, output: str, *, allow_existing: bool = False) -> str:
    dest = _absolute(output)
    if not dest.lower().endswith(".mp4"):
        raise ContractError("Phase 1 chỉ xuất .mp4")
    parent = os.path.dirname(dest)
    if not os.path.isdir(parent):
        raise ContractError(f"thư mục nhận output không tồn tại: {parent}")
    if os.path.islink(dest):
        raise ContractError(f"output là symbolic link, từ chối ghi: {dest}")
    if os.path.realpath(source) == os.path.realpath(dest):
        raise ContractError("input và output trỏ cùng file; nguồn không được ghi đè")
    if os.path.exists(dest):
        try:
            same = os.path.samefile(source, dest)
        except OSError:
            same = False
        if same:
            raise ContractError("output là cùng file hoặc hard link với input")
        if not allow_existing:
            raise ContractError(f"output đã tồn tại (mặc định không ghi đè): {dest}")
    return dest


def _sha256(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _manifest_path(output: str) -> str:
    return output + MANIFEST_SUFFIX


def _temp_path(dest: str, marker: str) -> str:
    path = Path(dest)
    return str(path.with_name(f".{path.stem}.{marker}-{uuid.uuid4().hex}{path.suffix}"))


def _publish_no_replace(temp_path: str, dest: str) -> None:
    """Atomically publish a completed same-volume temp file without replacing a race winner."""
    try:
        os.link(temp_path, dest)
    except FileExistsError as exc:
        raise ContractError(f"output vừa được tạo bởi tiến trình khác: {dest}") from exc
    except OSError as exc:
        raise EngineError(f"không thể công bố output nguyên tử: {exc}") from exc
    try:
        os.unlink(temp_path)
    except OSError:
        # The published file is complete. Leaving an owned temp link is safer than removing it.
        pass


def _probe(path: str) -> _ff.Probe:
    return _ff.probe(path)


def _ffprobe_text(path: str, *args: str) -> str:
    argv = [_ff.probe_exe(), "-v", "error", *args, str(path)]
    try:
        result = subprocess.run(argv, capture_output=True, text=True, encoding="utf-8",
                                errors="replace", timeout=TIMING_SCAN_TIMEOUT)
    except subprocess.TimeoutExpired as exc:
        raise EngineError(f"ffprobe scan quá {TIMING_SCAN_TIMEOUT}s: {path}") from exc
    except OSError as exc:
        raise StationMissing(f"không chạy được ffprobe: {exc}") from exc
    if result.returncode:
        raise EngineError(f"ffprobe scan hỏng (mã {result.returncode}): "
                           f"{result.stderr.strip()[-1200:]}")
    return result.stdout


def classify_timestamps(timestamps: list[float]) -> dict:
    """Determine whether every decoded frame has constant presentation-time spacing."""
    if len(timestamps) < 2 or any(not math.isfinite(value) for value in timestamps):
        return {"cfr": False, "frames": len(timestamps), "fps": None,
                "first_pts": None, "last_pts": None}
    intervals = [right - left for left, right in zip(timestamps, timestamps[1:])]
    median = statistics.median(intervals)
    tolerance = max(0.000002, median * 0.00005)
    constant = median > 0 and all(interval > 0 and abs(interval - median) <= tolerance
                                  for interval in intervals)
    return {"cfr": constant, "frames": len(timestamps),
            "fps": round(1 / median, 6) if median > 0 else None,
            "first_pts": timestamps[0], "last_pts": timestamps[-1]}


def check_constant_frame_rate(path: str) -> dict:
    raw = _ffprobe_text(path, "-select_streams", "v:0", "-show_frames", "-show_entries",
                        "frame=best_effort_timestamp_time", "-of", "csv=p=0")
    timestamps = []
    for line in raw.splitlines():
        field = line.strip().split(",", 1)[0]
        try:
            timestamps.append(float(field))
        except ValueError:
            continue
    result = classify_timestamps(timestamps)
    result["status"] = "PASS" if result["cfr"] else "VFR_OR_UNVERIFIABLE"
    return result


def audio_fingerprints(path: str) -> list[dict]:
    """Hash each copied audio track's compressed packet payloads in order."""
    raw = _ffprobe_text(path, "-select_streams", "a", "-show_packets", "-show_data_hash",
                        "sha256", "-show_entries", "packet=stream_index,data_hash",
                        "-of", "csv=p=0")
    tracks: dict[int, hashlib._Hash] = {}
    counts: dict[int, int] = {}
    for line in raw.splitlines():
        parts = line.strip().split(",", 1)
        if len(parts) != 2:
            continue
        try:
            index = int(parts[0])
        except ValueError:
            continue
        data_hash = parts[1].strip()
        if not data_hash:
            continue
        tracks.setdefault(index, hashlib.sha256()).update(data_hash.encode("ascii", "replace"))
        counts[index] = counts.get(index, 0) + 1
    return [{"packets": counts[index], "sha256": tracks[index].hexdigest()}
            for index in sorted(tracks)]


def inspect_video(path: str) -> dict:
    source = _source_file(path)
    info = _probe(source)
    media = describe_media(info)
    timing = check_constant_frame_rate(source)
    media["vfr_check"] = timing["status"]
    media["frame_count"] = timing["frames"]
    media["measured_fps"] = timing["fps"]
    media["supported_for_cleanup"] = media["supported_for_cleanup"] and timing["cfr"]
    if not timing["cfr"]:
        media["support_notes"].append("VFR hoặc frame timing chưa xác minh được")
    return {"input": source, "sha256": _sha256(source), "media": media}


def _filter_args(graph: str) -> list[str]:
    return ["-filter_complex", graph, "-map", "[vout]", "-map", "0:a?",
            "-c:v", "libx264", "-preset", "medium", "-crf", "18",
            "-pix_fmt", "yuv420p", "-fps_mode", "passthrough", "-c:a", "copy",
            "-map_metadata", "0", "-map_chapters", "0", "-movflags", "+faststart"]


def _color_args(info) -> list[str]:
    args = []
    for option, value in (("-color_range", info.color_range),
                          ("-color_primaries", info.color_primaries),
                          ("-color_trc", info.color_transfer),
                          ("-colorspace", info.color_space)):
        if value and value != "unknown":
            args.extend((option, value))
    return args


def _audio_signature(info) -> list[dict]:
    return [{"codec": str(stream.get("codec_name") or ""),
             "sample_rate": str(stream.get("sample_rate") or ""),
             "channels": int(stream.get("channels") or 0),
             "channel_layout": str(stream.get("channel_layout") or "")}
            for stream in info.audio]


def _validate_render_pair(source_info, output_info, source_timing: dict,
                          output_timing: dict, *, expected_duration: float) -> None:
    """Reject output before publication unless timing, stream origin, and color survive."""
    if not output_timing.get("cfr"):
        raise EngineError("PTS/count khung output không khớp nguồn CFR")
    source_fps, output_fps = source_timing.get("fps"), output_timing.get("fps")
    if not source_fps or not output_fps or abs(source_fps - output_fps) > 0.001:
        raise EngineError("frame rate output không khớp nguồn")
    tolerance = max(0.05, 0.5 / (source_fps or 30.0))
    if source_info.video_start_time is None or output_info.video_start_time is None:
        raise EngineError("thiếu mốc PTS video để xác nhận output")
    source_audio_starts = list(source_info.audio_start_times)
    output_audio_starts = list(output_info.audio_start_times)
    if (len(source_audio_starts) != len(output_audio_starts) or
            any(value is None for value in source_audio_starts + output_audio_starts)):
        raise EngineError("mốc bắt đầu audio output không khớp nguồn")
    if source_audio_starts:
        offsets_match = all(
            abs((source_info.video_start_time - source_audio) -
                (output_info.video_start_time - output_audio)) <= tolerance
            for source_audio, output_audio in zip(source_audio_starts, output_audio_starts))
    else:
        offsets_match = abs(source_info.video_start_time - output_info.video_start_time) <= tolerance
    if not offsets_match:
        raise EngineError("AV start offset output không khớp nguồn")
    color_fields = ("pix_fmt", "color_range", "color_transfer", "color_primaries", "color_space")
    if any(getattr(source_info, field) != getattr(output_info, field) for field in color_fields):
        raise EngineError("pixel format/color metadata output không khớp nguồn")
    if output_info.duration is None or abs(output_info.duration - expected_duration) > max(
            0.15, 2 / (source_fps or 30.0)):
        raise EngineError("thời lượng output không khớp khoảng đã yêu cầu")


def _render(source: str, dest: str, method: str, roi: tuple[int, int, int, int],
            start: float, end: float, *, color: str = "#000000",
            preview: bool = False) -> dict:
    info = _probe(source)
    media = validate_media(info)
    input_timing = check_constant_frame_rate(source)
    if not input_timing["cfr"]:
        raise ContractError("VFR hoặc frame timing chưa xác minh được; Phase 1 chỉ sửa CFR đã đo")
    input_audio = [] if preview else audio_fingerprints(source)
    validate_method_roi(method, roi, info.width, info.height)
    start, end = validate_range(start, end, info.duration)
    if method == "crop" and (start > 0.001 or end < info.duration - 0.001):
        raise ContractError("crop đổi kích thước toàn bộ video; yêu cầu khoảng 0 đến hết video")
    if method == "crop" and any(value % 2 for value in roi):
        raise ContractError("crop với libx264/yuv420p cần x,y,width,height là số chẵn")

    dest = _check_output_path(source, dest)
    sidecar = None if preview else _manifest_path(dest)
    if sidecar and os.path.lexists(sidecar):
        raise ContractError(f"manifest đã tồn tại (mặc định không ghi đè): {sidecar}")
    source_hash = _sha256(source)
    temp = _temp_path(dest, "preview" if preview else "render")
    graph, _ = build_filter(method, roi, start, end, color)
    argv = ["-i", source, *(_filter_args(graph)), *_color_args(info),
            "-ss", f"{start:.9g}",
            "-t", f"{end - start:.9g}", temp] if preview else [
                "-i", source, *(_filter_args(graph)), *_color_args(info), temp]
    try:
        _ff.run(argv)
        output_info = _probe(temp)
        if output_info.duration is None or output_info.duration <= 0:
            raise EngineError("ffprobe không đo được output vừa render")
        expected_size = (roi[2], roi[3]) if method == "crop" else (info.width, info.height)
        if (output_info.width, output_info.height) != expected_size:
            raise EngineError("kích thước output không khớp phép xử lý: "
                              f"{output_info.width}x{output_info.height}, cần "
                              f"{expected_size[0]}x{expected_size[1]}")
        if len(output_info.audio) != len(info.audio):
            raise EngineError("số track audio output không khớp nguồn")
        if _audio_signature(output_info) != _audio_signature(info):
            raise EngineError("cấu hình track audio output không khớp nguồn")
        output_timing = check_constant_frame_rate(temp)
        _validate_render_pair(info, output_info, input_timing, output_timing,
                              expected_duration=end - start if preview else info.duration)
        if not preview and output_timing["frames"] != input_timing["frames"]:
            raise EngineError("số khung output không khớp nguồn CFR")
        output_audio = [] if preview else audio_fingerprints(temp)
        if not preview and output_audio != input_audio:
            raise EngineError("payload audio output không khớp audio nguồn; không công bố output")
        if preview:
            media["vfr_check"] = "PASS"
            media["frame_count"] = input_timing["frames"]
            media["measured_fps"] = input_timing["fps"]
            _publish_no_replace(temp, dest)
            return {"output": dest, "method": method, "preview": True,
                    "duration": output_info.duration, "media": media,
                    "frame_count": output_timing["frames"],
                    "audio_streams": len(output_info.audio),
                    "visual_review": "NOT_CHECKED"}

        manifest = {
            "schema_version": MANIFEST_VERSION,
            "tool": "video-studio cleanup",
            "input": source,
            "input_sha256": source_hash,
            "output": dest,
            "output_sha256": _sha256(temp),
            "operation": {"method": method, "roi": {"x": roi[0], "y": roi[1],
                          "width": roi[2], "height": roi[3]},
                          "start": start, "end": end, "color": color if method == "cover" else None},
            "source_media": {**media, "vfr_check": "PASS",
                             "frame_count": input_timing["frames"],
                             "measured_fps": input_timing["fps"]},
            "output_media": {"width": output_info.width, "height": output_info.height,
                             "duration": output_info.duration,
                             "fps": output_info.fps,
                             "video_start_time": output_info.video_start_time,
                             "audio_start_times": output_info.audio_start_times,
                             "pix_fmt": output_info.pix_fmt,
                             "color_range": output_info.color_range,
                             "color_transfer": output_info.color_transfer,
                             "color_primaries": output_info.color_primaries,
                             "color_space": output_info.color_space,
                             "frame_count": output_timing["frames"],
                             "audio_streams": len(output_info.audio),
                             "vfr_check": "PASS"},
            "audio_fingerprints": {"source": input_audio, "output": output_audio},
            "audio_signature": {"source": _audio_signature(info),
                                "output": _audio_signature(output_info)},
            "technical_checks": {"source_hash": "PASS", "output_probe": "PASS",
                                 "geometry": "PASS", "audio_stream_count": "PASS",
                                 "audio_payloads": "PASS", "frame_timing": "PASS"},
            "visual_review": "NOT_CHECKED",
            "result_note": DELIVERY_NOTE[method],
        }
        manifest_temp = _temp_path(sidecar, "manifest")
        try:
            if _sha256(source) != source_hash:
                raise EngineError("nguồn đã thay đổi trong lúc render; output không được công bố")
            with open(manifest_temp, "x", encoding="utf-8", newline="\n") as stream:
                json.dump(manifest, stream, ensure_ascii=False, indent=2)
                stream.write("\n")
            _publish_no_replace(temp, dest)
            published_stat = os.stat(dest, follow_symlinks=False)
            try:
                _publish_no_replace(manifest_temp, sidecar)
            except Exception:
                # Remove only the output inode published by this call.
                try:
                    current_stat = os.stat(dest, follow_symlinks=False)
                    if (current_stat.st_dev, current_stat.st_ino) == (
                            published_stat.st_dev, published_stat.st_ino):
                        os.unlink(dest)
                except OSError:
                    pass
                raise
        finally:
            try:
                if os.path.exists(manifest_temp):
                    os.unlink(manifest_temp)
            except OSError:
                pass
        return {"output": dest, "manifest": sidecar, "method": method,
                "duration": output_info.duration, "technical_checks": manifest["technical_checks"],
                "visual_review": "NOT_CHECKED", "result_note": DELIVERY_NOTE[method]}
    finally:
        try:
            if os.path.exists(temp):
                os.unlink(temp)
        except OSError:
            pass


def apply_cleanup(source: str, output: str, method: str, roi: tuple[int, int, int, int],
                  start: float, end: float, color: str = "#000000") -> dict:
    return _render(_source_file(source), output, method, roi, start, end, color=color)


def preview_cleanup(source: str, output: str, method: str, roi: tuple[int, int, int, int],
                    start: float, end: float, color: str = "#000000") -> dict:
    return _render(_source_file(source), output, method, roi, start, end,
                   color=color, preview=True)


def _manifest_int(value, name: str, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ContractError(f"manifest: {name} phải là số nguyên >= {minimum}")
    return value


def _manifest_number(value, name: str, *, positive: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ContractError(f"manifest: {name} phải là số hữu hạn")
    number = float(value)
    if positive and number <= 0:
        raise ContractError(f"manifest: {name} phải lớn hơn 0")
    return number


def _validate_manifest_shape(manifest) -> tuple[dict, dict]:
    """Validate untrusted sidecar structure before using its values in checks."""
    if (not isinstance(manifest, dict) or isinstance(manifest.get("schema_version"), bool) or
            manifest.get("schema_version") != MANIFEST_VERSION):
        raise ContractError("manifest không đúng schema_version 1")
    for key in ("input", "output"):
        if not isinstance(manifest.get(key), str) or not manifest[key]:
            raise ContractError(f"manifest: {key} phải là đường dẫn")
    for key in ("input_sha256", "output_sha256"):
        if not isinstance(manifest.get(key), str) or not re.fullmatch(
                r"[0-9a-f]{64}", manifest[key]):
            raise ContractError(f"manifest: {key} phải là SHA-256 hex")

    operation = manifest.get("operation")
    if not isinstance(operation, dict) or operation.get("method") not in METHODS:
        raise ContractError("manifest: operation.method không hợp lệ")
    roi_data = operation.get("roi")
    if not isinstance(roi_data, dict) or set(roi_data) != {"x", "y", "width", "height"}:
        raise ContractError("manifest: operation.roi không đúng cấu trúc")
    roi = tuple(_manifest_int(roi_data.get(key), f"operation.roi.{key}")
                for key in ("x", "y", "width", "height"))
    if roi[2] == 0 or roi[3] == 0:
        raise ContractError("manifest: ROI cần width,height lớn hơn 0")
    if any(value % 2 for value in roi):
        raise ContractError("manifest: ROI phải căn chỉnh chẵn")
    start = _manifest_number(operation.get("start"), "operation.start")
    end = _manifest_number(operation.get("end"), "operation.end", positive=True)
    if start < 0 or end <= start:
        raise ContractError("manifest: khoảng thời gian không hợp lệ")
    if operation.get("method") == "cover":
        validate_color(operation.get("color"))
    elif operation.get("color") is not None:
        raise ContractError("manifest: color chỉ hợp lệ với cover")

    media_fields = ("source_media", "output_media")
    media = []
    color_fields = ("pix_fmt", "color_range", "color_transfer", "color_primaries", "color_space")
    for field in media_fields:
        value = manifest.get(field)
        if not isinstance(value, dict):
            raise ContractError(f"manifest: {field} phải là object")
        for key in ("width", "height", "audio_streams", "frame_count"):
            _manifest_int(value.get(key), f"{field}.{key}", 1 if key in ("width", "height", "frame_count") else 0)
        _manifest_number(value.get("duration"), f"{field}.duration", positive=True)
        fps_field = "measured_fps" if field == "source_media" else "fps"
        _manifest_number(value.get(fps_field), f"{field}.{fps_field}", positive=True)
        if value.get("vfr_check") != "PASS":
            raise ContractError(f"manifest: {field}.vfr_check phải PASS")
        for key in color_fields:
            if not isinstance(value.get(key), str):
                raise ContractError(f"manifest: {field}.{key} phải là chuỗi")
        _manifest_number(value.get("video_start_time"), f"{field}.video_start_time")
        audio_starts = value.get("audio_start_times")
        if not isinstance(audio_starts, list):
            raise ContractError(f"manifest: {field}.audio_start_times phải là danh sách")
        for index, item in enumerate(audio_starts):
            _manifest_number(item, f"{field}.audio_start_times[{index}]")
        media.append(value)
    source_media, output_media = media
    try:
        validate_method_roi(operation["method"], roi, source_media["width"], source_media["height"])
    except ContractError as exc:
        raise ContractError(f"manifest: {exc}") from exc
    if operation["method"] == "crop" and (start > 0.001 or end < source_media["duration"] - 0.001):
        raise ContractError("manifest: crop phải áp dụng toàn thời lượng")
    if end > source_media["duration"] + 0.001:
        raise ContractError("manifest: operation.end vượt duration nguồn")
    expected_size = (roi[2], roi[3]) if operation["method"] == "crop" else (
        source_media["width"], source_media["height"])
    if (output_media["width"], output_media["height"]) != expected_size:
        raise ContractError("manifest: output geometry không khớp phương pháp/ROI")
    if output_media["audio_streams"] != source_media["audio_streams"]:
        raise ContractError("manifest: số audio stream output không khớp nguồn")
    if output_media["frame_count"] != source_media["frame_count"]:
        raise ContractError("manifest: frame_count output không khớp nguồn")
    if abs(float(output_media["fps"]) - float(source_media["measured_fps"])) > 0.001:
        raise ContractError("manifest: frame rate output không khớp nguồn")
    if any(source_media[key] != output_media[key] for key in color_fields):
        raise ContractError("manifest: color metadata output không khớp nguồn")

    fingerprints = manifest.get("audio_fingerprints")
    if not isinstance(fingerprints, dict):
        raise ContractError("manifest: audio_fingerprints phải là object")
    for side in ("source", "output"):
        entries = fingerprints.get(side)
        if not isinstance(entries, list):
            raise ContractError(f"manifest: audio_fingerprints.{side} phải là danh sách")
        for index, entry in enumerate(entries):
            if not isinstance(entry, dict):
                raise ContractError(f"manifest: audio_fingerprints.{side}[{index}] phải là object")
            _manifest_int(entry.get("packets"), f"audio_fingerprints.{side}[{index}].packets")
            if not isinstance(entry.get("sha256"), str) or not re.fullmatch(
                    r"[0-9a-f]{64}", entry["sha256"]):
                raise ContractError(f"manifest: audio_fingerprints.{side}[{index}].sha256 không hợp lệ")
    if any(len(fingerprints[side]) != media[index]["audio_streams"]
           for index, side in enumerate(("source", "output"))):
        raise ContractError("manifest: số audio fingerprints không khớp số audio stream")
    signature = manifest.get("audio_signature")
    if not isinstance(signature, dict):
        raise ContractError("manifest: audio_signature phải là object")
    for side in ("source", "output"):
        entries = signature.get(side)
        if not isinstance(entries, list):
            raise ContractError(f"manifest: audio_signature.{side} phải là danh sách")
        for index, entry in enumerate(entries):
            if not isinstance(entry, dict) or any(not isinstance(entry.get(key), str)
                    for key in ("codec", "sample_rate", "channel_layout")):
                raise ContractError(f"manifest: audio_signature.{side}[{index}] không hợp lệ")
            _manifest_int(entry.get("channels"), f"audio_signature.{side}[{index}].channels")
    if signature["source"] != signature["output"]:
        raise ContractError("manifest: audio signature output không khớp nguồn")
    if (len(signature["source"]) != source_media["audio_streams"] or
            len(signature["output"]) != output_media["audio_streams"]):
        raise ContractError("manifest: số audio signature không khớp số audio stream")
    checks = manifest.get("technical_checks")
    if not isinstance(checks, dict) or not checks or any(value != "PASS" for value in checks.values()):
        raise ContractError("manifest: technical_checks phải chứa các kiểm tra PASS")
    if manifest.get("visual_review") != "NOT_CHECKED":
        raise ContractError("manifest: visual_review không hợp lệ")
    return source_media, output_media


def verify_cleanup(source: str, output: str, manifest_path: str | None = None) -> dict:
    source = _source_file(source)
    output = _absolute(output)
    if not os.path.isfile(output) or os.path.islink(output):
        raise ContractError(f"không có output video regular file: {output}")
    try:
        if os.path.samefile(source, output):
            raise ContractError("input và output là cùng file/hard link")
    except OSError:
        pass
    sidecar = _absolute(manifest_path) if manifest_path else _manifest_path(output)
    if not os.path.isfile(sidecar) or os.path.islink(sidecar):
        raise ContractError(f"không có manifest regular file: {sidecar}")
    try:
        with open(sidecar, "r", encoding="utf-8") as stream:
            manifest = json.load(stream)
    except (OSError, ValueError) as exc:
        raise ContractError(f"manifest không đọc được: {exc}") from exc
    expected_source, expected_output = _validate_manifest_shape(manifest)

    recorded_source = manifest.get("input")
    recorded_output = manifest.get("output")
    if (not isinstance(recorded_source, str) or os.path.realpath(recorded_source) !=
            os.path.realpath(source) or not isinstance(recorded_output, str) or
            os.path.realpath(recorded_output) != os.path.realpath(output)):
        raise ContractError("đường dẫn input/output không khớp manifest")
    actual_source_hash = _sha256(source)
    actual_output_hash = _sha256(output)
    checks = {
        "source_hash": "PASS" if actual_source_hash == manifest.get("input_sha256") else "FAIL",
        "output_hash": "PASS" if actual_output_hash == manifest.get("output_sha256") else "FAIL",
    }
    source_info = _probe(source)
    output_info = _probe(output)
    source_timing = check_constant_frame_rate(source)
    output_timing = check_constant_frame_rate(output)
    source_audio = audio_fingerprints(source)
    output_audio = audio_fingerprints(output)
    checks["input_probe"] = ("PASS" if source_info.width > 0 and source_info.duration else "FAIL")
    checks["output_probe"] = ("PASS" if output_info.width > 0 and output_info.duration else "FAIL")
    checks["input_cfr"] = "PASS" if source_timing["cfr"] else "FAIL"
    checks["output_cfr"] = "PASS" if output_timing["cfr"] else "FAIL"
    checks["frame_count"] = ("PASS" if source_timing["frames"] == expected_source.get("frame_count")
                             and output_timing["frames"] == expected_output.get("frame_count")
                             and source_timing["frames"] == output_timing["frames"] else "FAIL")
    checks["geometry"] = (
        "PASS" if (source_info.width, source_info.height) ==
        (expected_source.get("width"), expected_source.get("height")) and
        (output_info.width, output_info.height) ==
        (expected_output.get("width"), expected_output.get("height")) else "FAIL")
    checks["audio_stream_count"] = (
        "PASS" if len(source_info.audio) == expected_source.get("audio_streams") ==
        len(output_info.audio) == expected_output.get("audio_streams") else "FAIL")
    expected_audio = manifest.get("audio_fingerprints") or {}
    checks["audio_payloads"] = (
        "PASS" if source_audio == expected_audio.get("source") ==
        output_audio == expected_audio.get("output") else "FAIL")
    expected_signature = manifest.get("audio_signature") or {}
    checks["audio_signature"] = (
        "PASS" if _audio_signature(source_info) == expected_signature.get("source") ==
        _audio_signature(output_info) == expected_signature.get("output") else "FAIL")
    fps = source_timing.get("fps") or 0
    tolerance = max(0.15, 2 / fps) if fps > 0 else 0.15
    source_duration = source_info.duration or 0
    output_duration = output_info.duration or 0
    checks["duration"] = (
        "PASS" if abs(source_duration - float(expected_source.get("duration") or 0)) <= tolerance
        and abs(output_duration - float(expected_output.get("duration") or 0)) <= tolerance
        and abs(source_duration - output_duration) <= tolerance else "FAIL")
    source_vstart = source_info.video_start_time
    output_vstart = output_info.video_start_time
    source_astarts = [value for value in source_info.audio_start_times if value is not None]
    output_astarts = [value for value in output_info.audio_start_times if value is not None]
    checks["av_sync_origin"] = (
        "PASS" if source_vstart is not None and output_vstart is not None and
        len(source_astarts) == len(output_astarts) and
        all(abs((source_vstart - source_a) - (output_vstart - output_a)) <=
            max(0.05, 0.5 / (fps or 30.0))
            for source_a, output_a in zip(source_astarts, output_astarts)) else "FAIL")
    expected_fps = expected_source.get("measured_fps")
    output_fps = output_timing.get("fps")
    checks["frame_rate"] = (
        "PASS" if expected_fps and output_fps and source_timing.get("fps") and
        abs(source_timing["fps"] - float(expected_fps)) <= 0.001 and
        abs(source_timing["fps"] - output_fps) <= 0.001 else "FAIL")
    color_fields = ("pix_fmt", "color_range", "color_transfer", "color_primaries", "color_space")
    checks["color_metadata"] = (
        "PASS" if all(getattr(source_info, field) == getattr(output_info, field)
                       for field in color_fields) else "FAIL")
    passed = all(value == "PASS" for value in checks.values())
    return {"input": source, "output": output, "manifest": sidecar,
            "technical_checks": checks, "visual_review": "NOT_CHECKED",
            "ok": passed, "overall": "NOT_CHECKED"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="video-studio cleanup",
                                     description="Sửa có cấu trúc một vùng trên video local.")
    sub = parser.add_subparsers(dest="action", required=True)
    inspect = sub.add_parser("inspect", help="đọc metadata và hash nguồn")
    inspect.add_argument("--input", required=True)
    inspect.add_argument("--json", action="store_true")
    for action in ("preview", "apply"):
        item = sub.add_parser(action, help="render một phương pháp lên vùng/thời gian đã chọn")
        item.add_argument("--input", required=True)
        item.add_argument("--out", required=True, help="thư mục nhận output")
        item.add_argument("--name", default="preview.mp4" if action == "preview" else "cleaned.mp4",
                          help="tên file mp4; mặc định không ghi đè")
        item.add_argument("--method", choices=METHODS, required=True)
        item.add_argument("--roi", required=True, help="x,y,width,height theo pixel")
        item.add_argument("--start", required=True, type=float, help="giây từ đầu nguồn")
        item.add_argument("--end", required=True, type=float, help="giây kết thúc trong nguồn")
        item.add_argument("--color", default="#000000", help="màu cover #RRGGBB")
        item.add_argument("--json", action="store_true")
    verify = sub.add_parser("verify", help="hash và dò lại output từ manifest hiện tại")
    verify.add_argument("--input", required=True)
    verify.add_argument("--out", required=True, help="thư mục chứa video đã cleanup")
    verify.add_argument("--name", default="cleaned.mp4", help="tên output đã cleanup")
    verify.add_argument("--manifest", help="mặc định <output>.cleanup.json")
    verify.add_argument("--json", action="store_true")
    return parser


def do_cleanup(args: argparse.Namespace) -> dict:
    if args.action == "inspect":
        return {"action": "inspect", **inspect_video(args.input)}
    if args.action == "verify":
        name = _paths.plain_name(args.name, "--name")
        out_dir = _absolute(args.out)
        os.makedirs(out_dir, exist_ok=True)
        output = _paths.join_out(out_dir, name, "--name")
        result = verify_cleanup(args.input, output, args.manifest)
        if not result["ok"]:
            raise EngineError("verify phát hiện nguồn/output không còn khớp manifest")
        return {"action": "verify", **result}
    roi = parse_roi(args.roi)
    render = preview_cleanup if args.action == "preview" else apply_cleanup
    name = _paths.plain_name(args.name, "--name")
    out_dir = _absolute(args.out)
    os.makedirs(out_dir, exist_ok=True)
    output = _paths.join_out(out_dir, name, "--name")
    return {"action": args.action, **render(args.input, output, args.method,
                                             roi, args.start, args.end, args.color)}


def main(argv: list[str] | None = None) -> int:
    args, code = contract.parse(build_parser(), argv)
    if args is None:
        return code
    return contract.run(do_cleanup, args, args.json)


if __name__ == "__main__":
    raise SystemExit(main())
