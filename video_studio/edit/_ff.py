"""_ff.py — lớp mỏng trên ffmpeg/ffprobe cho bộ `edit`.

Nguồn ý tưởng: `browser-use/video-use` (MIT, © 2026 Browser Use) — `helpers/render.py`,
`helpers/grade.py`, đọc tại bản vendored `92c2b34`; đã viết lại. Xem `NOTICE`.

Ba khác biệt có chủ đích so với bản gốc:

1. **ffmpeg đến từ `_env`**, không phải chuỗi `"ffmpeg"` rải trong mã: máy nào không có nó
   trên PATH vẫn chạy được bằng `FFMPEG_DIR`, và thiếu hẳn thì ra **mã 3** kèm cách cài chứ
   không phải `FileNotFoundError`.
2. **Thăm dò một lần, trả một object** (`probe`): bản gốc gọi `ffprobe` ba lần cho ba câu hỏi
   (HDR? dọc? bao nhiêu khung hình/giây?) trên mỗi đoạn cắt — với một buổi quay 40 đoạn thì đó
   là 120 tiến trình con cho ba con số.
3. **Chọn đúng track tiếng** (upstream #134): nguồn nhiều track (mic ngoài + mic máy) rất hay
   có một track CÂM; bản gốc lấy `0:a:0` nên dựng ra video im lặng mà vẫn báo thành công.
"""
import json
import subprocess

from .. import _env
from ..contract import EngineError, StationMissing

HDR_TRANSFERS = {"smpte2084", "arib-std-b67"}       # PQ (HDR10) và HLG
#: Trần thời gian cho MỘT lần gọi ffmpeg. `timeout=None` (bản trước) nghĩa là ffmpeg treo thì
#: treo VĨNH VIỄN: lượt lịch 18h không bao giờ kết thúc, không báo hỏng, và cái kẹt lại là một
#: tiến trình con không ai thấy. Nhánh HyperFrames đã có `DEFAULT_TIMEOUT = 3600` — chỗ này
#: lấy cùng con số, và bên gọi vẫn truyền `timeout=` riêng khi biết việc mình lâu hơn.
DEFAULT_TIMEOUT = 3600
#: Thăm dò chỉ đọc metadata nên phải nhanh; lâu hơn thế là nguồn có vấn đề, không phải việc nặng.
PROBE_TIMEOUT = 120
HINT = ("cài ffmpeg (kèm ffprobe) rồi thử lại — hoặc đặt FFMPEG_DIR trỏ thư mục chứa chúng. "
        "Kiểm bằng `video-studio doctor`.")

__all__ = ["exe", "probe_exe", "run", "probe", "Probe"]


def exe():
    p = _env.ffmpeg_exe()
    if not p:
        raise StationMissing("không thấy `ffmpeg` — " + HINT)
    return p


def probe_exe():
    p = _env.ffprobe_exe()
    if not p:
        raise StationMissing("không thấy `ffprobe` — " + HINT)
    return p


def run(args, quiet=True, timeout=DEFAULT_TIMEOUT):
    """Chạy ffmpeg với argv list. Hỏng ⇒ EngineError kèm 15 dòng cuối stderr.

    Bản gốc dùng `stderr=PIPE` rồi bỏ đi: lỗi thật của ffmpeg nằm ở đó, và không in ra thì
    người đọc chỉ thấy "CalledProcessError: returned non-zero".

    Quá `timeout` ⇒ EngineError (mã 1, thử lại được) chứ không phải treo im lặng.
    """
    argv = [exe(), "-hide_banner", "-nostats", *args]
    try:
        r = subprocess.run(argv, capture_output=True, timeout=timeout)
    except subprocess.TimeoutExpired as e:
        raise EngineError(f"ffmpeg quá {timeout}s chưa xong: {' '.join(map(str, args[:6]))}…") from e
    if r.returncode != 0:
        err = (r.stderr or b"").decode("utf-8", "replace")
        tail = "\n".join(err.strip().splitlines()[-15:])
        raise EngineError(f"ffmpeg hỏng (mã {r.returncode}):\n{tail}")
    if not quiet:
        return (r.stderr or b"").decode("utf-8", "replace")
    return ""


def _probe_raw(path):
    argv = [probe_exe(), "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path)]
    try:
        # ffprobe trên một file trên ổ mạng / OneDrive placeholder treo được như ffmpeg.
        r = subprocess.run(argv, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=PROBE_TIMEOUT)
    except subprocess.TimeoutExpired as e:
        raise EngineError(f"ffprobe quá {PROBE_TIMEOUT}s chưa đọc xong {path}") from e
    if r.returncode != 0:
        raise EngineError(f"ffprobe không đọc được {path}: {(r.stderr or '').strip()}")
    try:
        return json.loads(r.stdout or "{}")
    except ValueError as e:
        raise EngineError(f"ffprobe trả JSON hỏng cho {path}: {e}") from e


def _fps_of(stream):
    for key in ("avg_frame_rate", "r_frame_rate"):
        raw = str(stream.get(key) or "")
        if "/" in raw:
            num, _, den = raw.partition("/")
            try:
                num, den = float(num), float(den)
            except ValueError:
                continue
            if den > 0 and num > 0:
                return round(num / den, 4)
    return None


def _rotation_of(stream):
    """Góc xoay khai trong metadata (iPhone quay dọc ghi 90/270 thay vì đổi w/h)."""
    for sd in stream.get("side_data_list") or []:
        if "rotation" in sd:
            try:
                return int(abs(float(sd["rotation"]))) % 360
            except (TypeError, ValueError):
                pass
    tags = stream.get("tags") or {}
    try:
        return int(abs(float(tags.get("rotate", 0)))) % 360
    except (TypeError, ValueError):
        return 0


class Probe:
    """Những gì bước cắt cần biết về một file nguồn — đo MỘT lần."""

    def __init__(self, path, data):
        self.path = str(path)
        streams = data.get("streams") or []
        v = next((s for s in streams if s.get("codec_type") == "video"), {})
        self.width = int(v.get("width") or 0)
        self.height = int(v.get("height") or 0)
        self.rotation = _rotation_of(v)
        self.fps = _fps_of(v)
        self.hdr = str(v.get("color_transfer") or "") in HDR_TRANSFERS
        self.audio = [s for s in streams if s.get("codec_type") == "audio"]
        try:
            self.duration = float((data.get("format") or {}).get("duration"))
        except (TypeError, ValueError):
            self.duration = None

    @property
    def portrait(self):
        """Khung dọc — tính CẢ góc xoay metadata (upstream #137: nguồn quay dọc từ điện thoại
        khai 1920×1080 + rotation 90, đoán theo w/h thô là ra video nằm ngang bị bóp)."""
        w, h = self.width, self.height
        if self.rotation in (90, 270):
            w, h = h, w
        return h > w

    def audio_map(self):
        """`-map` cho track tiếng đáng dùng (upstream #134). None nếu nguồn không có tiếng.

        Chọn track NHIỀU KÊNH nhất, rồi tới track đầu tiên; track khai 0 kênh bị loại vì đó
        là thứ tạo ra video câm mà lệnh vẫn báo xanh.
        """
        usable = [s for s in self.audio if int(s.get("channels") or 0) > 0]
        if not usable:
            return None
        best = max(usable, key=lambda s: (int(s.get("channels") or 0), -int(s.get("index") or 0)))
        # `-map 0:a:N` đếm theo THỨ TỰ TRACK TIẾNG của file, nên N là vị trí trong danh sách
        # audio gốc — không phải trong danh sách đã lọc.
        return f"0:a:{self.audio.index(best)}"


def probe(path):
    return Probe(path, _probe_raw(path))
