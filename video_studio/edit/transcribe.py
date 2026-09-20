"""transcribe.py — bóc lời từ file quay bằng **faster-whisper chạy tại máy**, không cần khoá API.

Nguồn: bản adapt local của `browser-use/video-use` (upstream MIT, © 2026 Browser Use) —
`helpers/transcribe_whisper.py`; **đã sửa**: ffmpeg qua `_ff`, thiếu thư viện thì ra **mã 3**
kèm lệnh cài, và không còn `sitecustomize.py` (UTF-8 cho console đã do `video_studio.cli` đặt).

Vì sao mặc định là bản chạy tại máy: đường cũ của upstream gọi một dịch vụ ASR trả phí, tức mỗi
buổi quay là một hoá đơn, một khoá API phải giữ, và toàn bộ tiếng nói của người dùng rời khỏi
máy họ. Bản tại máy không có ba thứ đó. Đổi lại: **không phân biệt người nói** (`speaker_id`
luôn null) và ít "ờ… à…" hơn bản dịch vụ — hai việc đó thì dùng `--backend vendored`.

Kết quả ghi ra `<work>/transcripts/<tên file>.json` đúng khuôn mà `pack.py` đọc:

    {"text": "…", "language_code": "vi",
     "words": [{"type": "word", "text": "…", "start": 1.23, "end": 1.56, "speaker_id": null}]}
"""
import json
import os
import tempfile
import time

from ..contract import StationMissing, log
from . import _ff

VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v", ".mts", ".m2ts"}
DEFAULT_MODEL = "large-v3"
DEFAULT_LANGUAGE = "vi"
INSTALL_HINT = ("cài phần phụ cho việc chỉnh footage: `pip install -e \".[edit]\"` "
                "(kéo theo faster-whisper). Không muốn cài thì dùng `--backend vendored` để gọi "
                "bản video-use đã cài ở trạm.")

_model = None
_model_name = None

__all__ = ["VIDEO_EXTS", "videos_in", "available", "transcribe_one", "transcribe_all"]


def videos_in(path):
    """Một file quay, hoặc mọi file quay trong một thư mục (sắp theo tên)."""
    path = os.path.abspath(path)
    if os.path.isfile(path):
        return [path]
    if not os.path.isdir(path):
        raise StationMissing(f"không có footage ở {path}")
    return sorted(os.path.join(path, n) for n in os.listdir(path)
                  if os.path.splitext(n)[1].lower() in VIDEO_EXTS)


def available():
    """faster-whisper có trong venv này không (không nạp model)."""
    import importlib.util
    return importlib.util.find_spec("faster_whisper") is not None


def _add_cuda_dll_dirs():
    """Windows: wheel `nvidia-*-cu12` để DLL trong site-packages/nvidia/*/bin, ngoài PATH.

    Không thêm thì ctranslate2 không thấy cublas/cudnn và ta lặng lẽ chạy CPU (chậm 10 lần)
    trên một máy có GPU.
    """
    import sys
    if not hasattr(os, "add_dll_directory"):
        return
    for base in sys.path:
        for pkg in ("cublas", "cudnn"):
            d = os.path.join(base, "nvidia", pkg, "bin")
            if os.path.isdir(d):
                try:
                    os.add_dll_directory(d)
                except OSError:
                    pass


def load_model(name=None, prefer_gpu=True):
    """Nạp model một lần cho cả tiến trình (một GPU ⇒ bóc lời tuần tự, không song song)."""
    global _model, _model_name
    name = name or os.environ.get("VIDEO_WHISPER_MODEL") or DEFAULT_MODEL
    if _model is not None and _model_name == name:
        return _model
    try:
        from faster_whisper import WhisperModel
    except ImportError as e:
        raise StationMissing("bước bóc lời cần `faster-whisper` — " + INSTALL_HINT) from e
    _add_cuda_dll_dirs()
    if prefer_gpu:
        try:
            _model = WhisperModel(name, device="cuda", compute_type="float16")
            _model_name = name
            return _model
        except Exception:      # noqa: BLE001 — không có GPU/driver là chuyện thường, lùi về CPU
            log("[edit] không dùng được GPU cho bóc lời — chạy CPU (chậm hơn)")
    _model = WhisperModel(name, device="cpu", compute_type="int8")
    _model_name = name
    return _model


def extract_audio(video, dest):
    """Tách tiếng ra WAV 16 kHz mono — đúng thứ whisper cần, và chọn ĐÚNG track (xem `_ff`)."""
    p = _ff.probe(video)
    amap = p.audio_map()
    if amap is None:
        raise StationMissing(f"{os.path.basename(video)} không có track tiếng nào dùng được — "
                             "không bóc lời được từ file câm")
    _ff.run(["-y", "-i", str(video), "-map", amap, "-vn", "-ac", "1", "-ar", "16000",
             "-c:a", "pcm_s16le", str(dest)])
    return dest


def _to_scribe(segments, info, model_name):
    words, text = [], []
    for seg in segments:
        text.append(seg.text)
        for w in getattr(seg, "words", None) or []:
            words.append({"type": "word", "text": w.word.strip(),
                          "start": round(float(w.start), 3), "end": round(float(w.end), 3),
                          "speaker_id": None})
    return {"text": "".join(text).strip(),
            "language_code": getattr(info, "language", None),
            "words": words,
            "_source": f"faster-whisper/{model_name}"}


def transcribe_one(video, work_dir, language=DEFAULT_LANGUAGE, force=False, model=None):
    """Bóc lời một file → đường dẫn transcript. Có sẵn thì dùng lại (trừ khi `force`)."""
    out_dir = os.path.join(work_dir, "transcripts")
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, os.path.splitext(os.path.basename(video))[0] + ".json")
    if os.path.isfile(out) and not force:
        log(f"[edit] dùng lại bản đã bóc: {os.path.basename(out)}")
        return out
    m = model or load_model()
    t0 = time.time()
    with tempfile.TemporaryDirectory() as tmp:
        wav = os.path.join(tmp, "audio.wav")
        extract_audio(video, wav)
        log(f"[edit] bóc lời {os.path.basename(video)} …")
        segments, info = m.transcribe(wav, language=None if language in (None, "auto") else
                                      language, word_timestamps=True, vad_filter=True)
        payload = _to_scribe(list(segments), info, _model_name or DEFAULT_MODEL)
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    log(f"[edit] → {os.path.basename(out)} ({len(payload['words'])} từ, "
        f"{time.time() - t0:.1f}s)")
    return out


def transcribe_all(footage, work_dir, language=DEFAULT_LANGUAGE, force=False):
    videos = videos_in(footage)
    if not videos:
        raise StationMissing(f"không có file quay nào trong {footage} "
                             f"(nhận: {', '.join(sorted(VIDEO_EXTS))})")
    model = load_model()
    return [transcribe_one(v, work_dir, language=language, force=force, model=model)
            for v in videos]
