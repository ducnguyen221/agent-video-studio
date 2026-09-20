"""grade.py — chỉnh màu: vài preset, và một phép chỉnh TỰ ĐỘNG có chặn biên.

Nguồn: `browser-use/video-use` (MIT, © 2026 Browser Use) — `helpers/grade.py`, đọc tại bản
vendored `92c2b34`; **đã sửa**: ffmpeg/ffprobe đi qua `_ff`, thăm dò thời lượng dùng `_ff.probe`,
và hàm phân tích trả về cùng một `dict` thống kê để bên gọi ghi vào log/JSON kết quả.

Vì sao "tự động" mà vẫn an toàn: phép chỉnh chỉ chữa BA khuyết tật đo được — thiếu sáng, bẹt
tương phản, nhạt màu — và mọi trục bị chặn ở ±8 %. Nó không bao giờ áp một LOOK (teal/orange,
curve phim): muốn look thì gọi preset tường minh. Mục tiêu là "sạch", không phải "đã chỉnh màu".
"""
import os
import tempfile

from . import _ff

PRESETS = {
    # Nền an toàn: gần như không thấy, chỉ chống bẹt.
    "subtle": "eq=contrast=1.03:saturation=0.98",
    # Chỉnh nhẹ + S-curve, không lệch màu.
    "neutral_punch": ("eq=contrast=1.06:brightness=0.0:saturation=1.0,"
                      "curves=master='0/0 0.25/0.23 0.75/0.77 1/1'"),
    # Preset SÁNG TÁC, chỉ dùng khi được yêu cầu: +12 % tương phản, tối chân đen, ám ấm.
    "warm_cinematic": ("eq=contrast=1.12:brightness=-0.02:saturation=0.88,"
                       "colorbalance=rs=0.02:gs=0.0:bs=-0.03:rm=0.04:gm=0.01:bm=-0.02:"
                       "rh=0.08:gh=0.02:bh=-0.05,"
                       "curves=master='0/0 0.25/0.22 0.75/0.78 1/1'"),
    # Không chỉnh gì — dùng làm cờ "để nguyên nguồn này".
    "none": "",
}
AUTO = "__AUTO__"
NEUTRAL_STATS = {"y_mean": 0.5, "y_range": 0.72, "sat_mean": 0.25}

__all__ = ["PRESETS", "AUTO", "get_preset", "resolve_filter", "analyze", "auto_filter"]


def get_preset(name):
    if name not in PRESETS:
        raise KeyError(f"preset lạ '{name}'. Có: {', '.join(sorted(PRESETS))}")
    return PRESETS[name]


def resolve_filter(grade):
    """Khoá `grade` của EDL: tên preset · chuỗi filter ffmpeg · "auto". -> chuỗi filter | AUTO."""
    grade = (grade or "").strip()
    if not grade:
        return ""
    if grade == "auto":
        return AUTO
    if grade in PRESETS:
        return PRESETS[grade]
    if grade.replace("_", "").replace("-", "").isalnum():
        raise KeyError(f"preset lạ '{grade}'. Có: {', '.join(sorted(PRESETS))} "
                       "(chuỗi filter ffmpeg phải chứa '=' hoặc ',')")
    return grade


def _parse_stats(text):
    """Đọc metadata của `signalstats` → thống kê chuẩn hoá về 0..1.

    `signalstats` báo theo ĐỘ SÂU BIT của khung đã giải mã (8 bit → 0-255, 10 bit → 0-1023),
    nên phải chia theo `YBITDEPTH` — quên bước này thì nguồn 10 bit trông như tối đen và phép
    chỉnh tự động sẽ kéo sáng một clip vốn đã đúng.
    """
    vals = {"YAVG": [], "YMIN": [], "YMAX": [], "SATAVG": []}
    depth = 8
    for line in text.splitlines():
        line = line.strip()
        if "lavfi.signalstats." not in line or "=" not in line:
            continue
        key = line.split("lavfi.signalstats.", 1)[1].split("=", 1)[0]
        try:
            v = float(line.rsplit("=", 1)[1])
        except (ValueError, IndexError):
            continue
        if key == "YBITDEPTH":
            depth = int(v)
        elif key in vals:
            vals[key].append(v)
    if not vals["YAVG"]:
        return dict(NEUTRAL_STATS)
    top = (2 ** depth) - 1

    def mean(xs):
        return sum(xs) / len(xs)

    y_range = ((mean(vals["YMAX"]) - mean(vals["YMIN"])) / top
               if vals["YMAX"] and vals["YMIN"] else NEUTRAL_STATS["y_range"])
    return {"y_mean": mean(vals["YAVG"]) / top,
            "y_range": y_range,
            "sat_mean": mean(vals["SATAVG"]) / top if vals["SATAVG"] else NEUTRAL_STATS["sat_mean"]}


def analyze(video, start=0.0, duration=None, samples=10):
    """Lấy mẫu vài khung của một khoảng → {y_mean, y_range, sat_mean} (0..1)."""
    if duration is None:
        duration = getattr(_ff.probe(video), "duration", None) or 10.0
    fps = max(0.5, min(samples / max(float(duration), 0.1), 10.0))
    fd, meta = tempfile.mkstemp(suffix=".txt")
    os.close(fd)
    try:
        _ff.run(["-y", "-ss", f"{float(start):.3f}", "-i", str(video),
                 "-t", f"{float(duration):.3f}",
                 "-vf", f"fps={fps:.2f},signalstats,metadata=print:file={meta}",
                 "-f", "null", "-"])
        with open(meta, "r", encoding="utf-8", errors="replace") as f:
            return _parse_stats(f.read())
    finally:
        try:
            os.remove(meta)
        except OSError:
            pass


def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


def auto_filter(stats):
    """Thống kê → chuỗi filter `eq=…` (hoặc rỗng nếu clip đã cân). Mọi trục chặn ở ±8 %."""
    y_mean, y_range, sat = stats["y_mean"], stats["y_range"], stats["sat_mean"]

    if y_range < 0.65:                    # bẹt: nâng nhẹ, [0.50, 0.65] → [1.08, 1.03]
        t = _clamp((y_range - 0.50) / 0.15, 0.0, 1.0)
        contrast = 1.08 - 0.05 * t
    else:
        contrast = 1.03
    if y_mean < 0.42:                     # tối: kéo gamma, [0.30, 0.42] → [1.10, 1.02]
        t = _clamp((y_mean - 0.30) / 0.12, 0.0, 1.0)
        gamma = 1.10 - 0.08 * t
    elif y_mean > 0.60:                   # hơi cháy: kéo lại một chút
        gamma = 0.97
    else:
        gamma = 1.0
    if sat < 0.18:
        saturation = 1.04
    elif sat > 0.38:
        saturation = 0.96
    else:
        saturation = 0.98                 # màn hình tiêu dùng vốn đã đẩy màu
    parts = []
    for key, val in (("contrast", _clamp(contrast, 0.94, 1.08)),
                     ("gamma", _clamp(gamma, 0.94, 1.10)),
                     ("saturation", _clamp(saturation, 0.94, 1.06))):
        if abs(val - 1.0) > 0.005:
            parts.append(f"{key}={val:.3f}")
    return "eq=" + ":".join(parts) if parts else ""


def auto_for_clip(video, start=0.0, duration=None):
    """-> (chuỗi filter, thống kê) cho đúng khoảng sắp cắt."""
    stats = analyze(video, start=start, duration=duration)
    return auto_filter(stats), stats
