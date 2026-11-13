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
import hashlib
import importlib.metadata
import json
import math
import os
import shutil
import tempfile
import time
import uuid

from ..contract import ContractError, StationMissing, log
from . import _ff

VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v", ".mts", ".m2ts"}
DEFAULT_MODEL = "large-v3"
DEFAULT_LANGUAGE = "vi"
INSTALL_HINT = ("cài phần phụ cho việc chỉnh footage: `pip install -e \".[edit]\"` "
                "(kéo theo faster-whisper). Không muốn cài thì dùng `--backend vendored` để gọi "
                "bản video-use đã cài ở trạm.")

_model = None
_model_name = None
_model_device = None
_model_compute_type = None

CACHE_SCHEMA = 1
TRANSCRIPT_SCHEMA = 1
ASR_SETTINGS = {"word_timestamps": True, "vad_filter": True}
BUILTIN_MODEL_NAMES = {
    "tiny", "tiny.en", "base", "base.en", "small", "small.en", "medium", "medium.en",
    "large", "large-v1", "large-v2", "large-v3", "large-v3-turbo", "distil-large-v2",
    "distil-large-v3", "distil-medium.en", "distil-small.en",
}

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


def _cuda_bin_dirs():
    """Các thư mục `nvidia/<pkg>/bin` (cublas, cudnn, cuda_nvrtc) có thật trong sys.path, không trùng."""
    import sys
    found = []
    for base in sys.path:
        for pkg in ("cublas", "cudnn", "cuda_nvrtc"):
            d = os.path.join(base, "nvidia", pkg, "bin")
            if os.path.isdir(d) and d not in found:
                found.append(d)
    return found


def _add_cuda_dll_dirs():
    """Windows: wheel `nvidia-*-cu12` để DLL trong site-packages/nvidia/*/bin, ngoài PATH.

    ctranslate2 tìm `cublas64_12.dll` theo PATH — `os.add_dll_directory` một mình KHÔNG đủ (đo thật:
    bóc lời rơi CPU 39,8 s thay vì GPU 1,7 s). Nên làm cả hai, và phải gọi TRƯỚC khi import
    faster_whisper/ctranslate2. PATH chỉ được thêm ở Windows, không trùng (không phân biệt hoa thường),
    gọi nhiều lần không làm nó phình.
    """
    dirs = _cuda_bin_dirs()
    if hasattr(os, "add_dll_directory"):
        for d in dirs:
            try:
                os.add_dll_directory(d)
            except OSError:
                pass
    if os.name != "nt" or not dirs:
        return

    def key(p):
        return os.path.normpath(p).lower()

    parts = [p for p in os.environ.get("PATH", "").split(os.pathsep) if p]
    have = {key(p) for p in parts}
    new = [d for d in dirs if key(d) not in have]
    if new:
        os.environ["PATH"] = os.pathsep.join(new + parts)


_CUDA_LIB_NAMES = ("cublas", "cudnn", "nvrtc", "libcu", "cuda")
_CUDA_LOAD_WORDS = (".dll", ".so", "library", "not found", "cannot be loaded", "shared object")


def _is_cuda_library_error(exc):
    """Lỗi do THIẾU/không tải được thư viện CUDA (khác với không có GPU/driver): phải có CẢ tên
    thư viện CUDA lẫn từ khoá nạp thư viện. ctranslate2 nạp cuBLAS lười nên lỗi có thể ném ở
    lần `transcribe` đầu, không phải lúc dựng model."""
    text = str(exc).lower()
    return any(n in text for n in _CUDA_LIB_NAMES) and any(w in text for w in _CUDA_LOAD_WORDS)


def _warn_cuda_library(exc):
    log(f"[edit] CẢNH BÁO: thư viện CUDA không tải được ({exc}) — cài nvidia-cublas-cu12, "
        "nvidia-cuda-nvrtc-cu12, nvidia-cudnn-cu12 vào venv này; tạm chạy CPU (chậm hơn)")


def _is_cuda_model(model):
    device = getattr(model, "device", None) or (_model_device if model is _model else None)
    return device == "cuda"


def _reload_cpu_model(model):
    """Bỏ model GPU, nạp lại bản CPU (cùng tên model) và đặt nó làm model chung của tiến trình."""
    global _model
    name = getattr(model, "model_size_or_path", None)
    name = name if isinstance(name, str) and name else (_model_name or DEFAULT_MODEL)
    _model = None
    return load_model(name, prefer_gpu=False)


def _transcribe_wav(model, wav, identity, language):
    segments, info = model.transcribe(
        wav, language=identity["language"] if identity else
        (None if language in (None, "auto") else language), **ASR_SETTINGS)
    return list(segments), info     # generator: lỗi nạp thư viện cũng có thể nổ ở lúc duyệt


def load_model(name=None, prefer_gpu=True):
    """Nạp model một lần cho cả tiến trình (một GPU ⇒ bóc lời tuần tự, không song song)."""
    global _model, _model_name, _model_device, _model_compute_type
    name = name or os.environ.get("VIDEO_WHISPER_MODEL") or DEFAULT_MODEL
    if _model is not None and _model_name == name:
        return _model
    _add_cuda_dll_dirs()      # TRƯỚC import: ctranslate2 dò DLL CUDA theo PATH lúc nạp
    try:
        from faster_whisper import WhisperModel
    except ImportError as e:
        raise StationMissing("bước bóc lời cần `faster-whisper` — " + INSTALL_HINT) from e
    if prefer_gpu:
        try:
            _model = WhisperModel(name, device="cuda", compute_type="float16")
            _model_name = name
            _model_device, _model_compute_type = "cuda", "float16"
            return _model
        except Exception as e:  # noqa: BLE001 — không có GPU/driver là chuyện thường, lùi về CPU
            if _is_cuda_library_error(e):
                _warn_cuda_library(e)
            else:
                log("[edit] không dùng được GPU cho bóc lời — chạy CPU (chậm hơn)")
    _model = WhisperModel(name, device="cpu", compute_type="int8")
    _model_name = name
    _model_device, _model_compute_type = "cpu", "int8"
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
            if not _valid_time(w.start) or not _valid_time(w.end) or w.start > w.end:
                raise ContractError("ASR trả timestamp không hợp lệ; giữ bản transcript cũ")
            words.append({"type": "word", "text": w.word.strip(),
                          "start": round(float(w.start), 3), "end": round(float(w.end), 3),
                          "speaker_id": None})
    return {"text": "".join(text).strip(),
            "language_code": getattr(info, "language", None),
            "words": words,
            "_source": f"faster-whisper/{model_name}"}


def _effective_model_metadata(model):
    """Thông tin model/runtime dùng để phân biệt cache; None nghĩa là không thể reuse an toàn."""
    name = getattr(model, "model_size_or_path", None)
    if name is None and model is _model:
        name = _model_name
    if not isinstance(name, str) or name.strip().lower() not in BUILTIN_MODEL_NAMES:
        return None
    try:
        runtime = {"faster_whisper": importlib.metadata.version("faster-whisper"),
                   "ctranslate2": importlib.metadata.version("ctranslate2")}
    except importlib.metadata.PackageNotFoundError:
        return None
    device = getattr(model, "device", None)
    compute_type = getattr(model, "compute_type", None)
    if model is _model:
        device = device or _model_device
        compute_type = compute_type or _model_compute_type
    if not isinstance(device, str) or not isinstance(compute_type, str):
        return None
    return {"name": name.strip().lower(), "runtime": runtime,
            "device": device, "compute_type": compute_type}


def _sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _source_fingerprint(path):
    """Hash current bytes on every call; stat is only a stability guard, never a cache key."""
    before = os.stat(path)
    digest = _sha256_file(path)
    after = os.stat(path)
    if (before.st_size, before.st_mtime_ns, before.st_ino) != (
            after.st_size, after.st_mtime_ns, after.st_ino):
        raise ContractError(f"nguồn thay đổi trong khi đang băm: {os.path.basename(path)}")
    return digest


def _snapshot_source(source, snapshot, temp_dir):
    """Copy and hash one bounded snapshot; extraction must use this exact file."""
    try:
        copy_budget = shutil.disk_usage(temp_dir).free // 2
        expected_size = os.stat(source).st_size
        if expected_size > copy_budget:
            raise ContractError("không đủ dung lượng tạm để tạo snapshot footage "
                                "(giới hạn là một nửa dung lượng trống); giữ transcript cũ")
        digest = hashlib.sha256()
        copied = 0
        with open(source, "rb") as input_stream, open(snapshot, "wb") as output_stream:
            for chunk in iter(lambda: input_stream.read(1024 * 1024), b""):
                copied += len(chunk)
                if copied > copy_budget:
                    raise ContractError("snapshot footage vượt giới hạn dung lượng tạm; "
                                        "giữ transcript cũ")
                digest.update(chunk)
                output_stream.write(chunk)
            output_stream.flush()
            os.fsync(output_stream.fileno())
        return digest.hexdigest()
    except ContractError:
        raise
    except OSError as exc:
        raise ContractError("không tạo được snapshot footage trong thư mục tạm; "
                            "kiểm tra quyền và dung lượng, transcript cũ được giữ") from exc


def _require_live_source_matches(source, expected_hash, stage):
    try:
        current_hash = _source_fingerprint(source)
    except OSError as exc:
        raise ContractError(f"không kiểm tra được footage {stage}; giữ transcript cũ") from exc
    if current_hash != expected_hash:
        raise ContractError(f"nguồn đổi {stage}; không dùng cache hoặc lưu transcript: "
                            f"{os.path.basename(source)}")


def _transcript_dir(work_dir):
    work_path = os.path.abspath(work_dir)
    output_dir = os.path.join(work_path, "transcripts")
    # Hai luồng cùng tạo `transcripts` lần đầu: realpath trên đường đang được tạo dở có thể trả dạng
    # khác (Windows) và làm commonpath lỗi ValueError. Trạng thái đó chỉ thoáng qua: thử lại có hạn.
    for attempt in range(3):
        effective_work = os.path.normcase(os.path.realpath(work_path))
        effective_output = os.path.normcase(os.path.realpath(output_dir))
        try:
            common = os.path.normcase(os.path.realpath(os.path.commonpath(
                [effective_work, effective_output])))
            break
        except ValueError as exc:
            if attempt == 2:
                raise ContractError("thư mục transcript nằm ngoài nơi làm việc đã chọn") from exc
            time.sleep(0.01)
    if common != effective_work:
        raise ContractError("thư mục transcripts trỏ ra ngoài nơi làm việc đã chọn "
                            "qua symlink/junction; không ghi file")
    return output_dir


def _preflight_transcript_targets(videos, work_dir):
    output_dir = _transcript_dir(work_dir)
    effective_dir = os.path.realpath(output_dir)
    seen = {}
    for video in videos:
        name = os.path.splitext(os.path.basename(video))[0] + ".json"
        target_key = os.path.normcase(os.path.join(effective_dir, name))
        if target_key in seen:
            raise ContractError(f"nhiều footage cùng đường dẫn transcript {name}; "
                                "đổi tên nguồn hoặc tách thành các lượt riêng")
        seen[target_key] = video
    return output_dir


def _valid_time(value):
    if not isinstance(value, (int, float)) or isinstance(value, bool) or value < 0:
        return False
    try:
        return math.isfinite(float(value))
    except (OverflowError, ValueError):
        return False


def _transcript_identity(source_hash, model_metadata, language):
    effective_language = None if language in (None, "auto") else language
    return {"source_sha256": source_hash,
            "model": model_metadata,
            "language": effective_language,
            "settings": dict(ASR_SETTINGS),
            "schema_version": TRANSCRIPT_SCHEMA}


def _sha256_bytes(value):
    return hashlib.sha256(value).hexdigest()


def _valid_payload(payload):
    if not isinstance(payload, dict) or not isinstance(payload.get("text"), str):
        return False
    if payload.get("language_code") is not None and not isinstance(
            payload.get("language_code"), str):
        return False
    words = payload.get("words")
    if not isinstance(words, list):
        return False
    for word in words:
        if not isinstance(word, dict) or word.get("type") != "word":
            return False
        if not isinstance(word.get("text"), str):
            return False
        if not _valid_time(word.get("start")) or not _valid_time(word.get("end")):
            return False
        if word["start"] > word["end"]:
            return False
    return True


def _read_cache(out, metadata_path, expected_identity):
    """Return payload only when sidecar, payload hash, and generation all agree."""
    if not os.path.isfile(out) or os.path.islink(out):
        return None, "missing payload" if not os.path.exists(out) else "payload is a symlink"
    if not os.path.isfile(metadata_path) or os.path.islink(metadata_path):
        return None, "missing metadata" if not os.path.exists(metadata_path) else "metadata is a symlink"
    try:
        with open(metadata_path, "r", encoding="utf-8") as stream:
            metadata = json.load(stream)
        with open(out, "r", encoding="utf-8") as stream:
            payload = json.load(stream)
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None, "payload or metadata is corrupt"
    if not isinstance(metadata, dict):
        return None, "metadata is invalid"
    if metadata.get("cache_schema") != CACHE_SCHEMA:
        return None, "metadata schema mismatch"
    if metadata.get("identity") != expected_identity:
        return None, "source/model/settings/language/schema mismatch"
    if not _valid_payload(payload):
        return None, "payload is invalid"
    generation = metadata.get("generation")
    if not isinstance(generation, str) or payload.get("_cache_generation") != generation:
        return None, "payload and metadata generation mismatch"
    if metadata.get("output_sha256") != _sha256_file(out):
        return None, "payload fingerprint mismatch"
    return payload, "hit"


def _write_temp(path, content):
    """Write a durable temporary beside its destination so os.replace stays same-filesystem."""
    fd, temp_path = tempfile.mkstemp(prefix=".transcript-", suffix=".tmp",
                                     dir=os.path.dirname(path))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        return temp_path
    except BaseException:
        try:
            os.close(fd)
        except OSError:
            pass
        try:
            os.unlink(temp_path)
        except OSError:
            pass
        raise


def _publish(out, metadata_path, payload, identity):
    generation = uuid.uuid4().hex
    payload["_cache_generation"] = generation
    payload_text = json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    metadata = {"cache_schema": CACHE_SCHEMA,
                "identity": identity,
                "generation": generation,
                "output_sha256": _sha256_bytes(payload_text.encode("utf-8"))}
    metadata_text = json.dumps(metadata, ensure_ascii=False, sort_keys=True,
                               indent=2, allow_nan=False) + "\n"
    payload_temp = _write_temp(out, payload_text)
    metadata_temp = None
    try:
        metadata_temp = _write_temp(metadata_path, metadata_text)
        # No reader can accept a torn pair: the payload embeds this generation and
        # the sidecar verifies both its generation and content fingerprint.
        os.replace(payload_temp, out)
        payload_temp = None
        os.replace(metadata_temp, metadata_path)
        metadata_temp = None
    finally:
        for temp_path in (payload_temp, metadata_temp):
            if temp_path:
                try:
                    os.unlink(temp_path)
                except FileNotFoundError:
                    pass


def transcribe_one(video, work_dir, language=DEFAULT_LANGUAGE, force=False, model=None):
    """Bóc lời một file → đường dẫn transcript. Có sẵn thì dùng lại (trừ khi `force`)."""
    out_dir = _transcript_dir(work_dir)
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, os.path.splitext(os.path.basename(video))[0] + ".json")
    metadata_path = out + ".meta"
    t0 = time.time()
    try:
        temporary_directory = tempfile.TemporaryDirectory()
    except OSError as exc:
        raise ContractError("không tạo được thư mục tạm cho snapshot footage; "
                            "transcript cũ được giữ") from exc
    with temporary_directory as tmp:
        suffix = os.path.splitext(video)[1] or ".media"
        snapshot = os.path.join(tmp, "source" + suffix)
        source_hash = _snapshot_source(video, snapshot, tmp)
        _require_live_source_matches(video, source_hash, "sau khi tạo snapshot")
        m = model or load_model()
        _require_live_source_matches(video, source_hash, "sau khi nạp model")
        model_metadata = _effective_model_metadata(m)
        identity = (_transcript_identity(source_hash, model_metadata, language)
                    if model_metadata is not None else None)
        if not force and identity is not None:
            cached, reason = _read_cache(out, metadata_path, identity)
            if cached is not None:
                _require_live_source_matches(video, source_hash, "trước khi dùng cache")
                log(f"[edit] dùng lại bản đã bóc: {os.path.basename(out)}")
                return out
        else:
            reason = "unknown model metadata" if model_metadata is None else "forced refresh"
        log(f"[edit] cache transcript miss ({reason}): {os.path.basename(out)}")
        wav = os.path.join(tmp, "audio.wav")
        extract_audio(snapshot, wav)
        log(f"[edit] bóc lời {os.path.basename(video)} …")
        try:
            segments, info = _transcribe_wav(m, wav, identity, language)
        except Exception as exc:   # noqa: BLE001 — chỉ lỗi thư viện CUDA của model GPU được cứu
            if not (_is_cuda_model(m) and _is_cuda_library_error(exc)):
                raise
            _warn_cuda_library(exc)
            m = _reload_cpu_model(m)
            model_metadata = _effective_model_metadata(m)
            identity = (_transcript_identity(source_hash, model_metadata, language)
                        if model_metadata is not None else None)
            segments, info = _transcribe_wav(m, wav, identity, language)
        payload = _to_scribe(segments, info,
                             (model_metadata or {}).get("name", _model_name or DEFAULT_MODEL))
        _require_live_source_matches(video, source_hash, "trong khi bóc lời")
        if not _valid_payload(payload):
            raise ContractError("ASR trả transcript sai cấu trúc; giữ bản transcript cũ")
        if identity is not None:
            _publish(out, metadata_path, payload, identity)
        else:
            payload_text = json.dumps(payload, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
            payload_temp = _write_temp(out, payload_text)
            try:
                os.replace(payload_temp, out)
                payload_temp = None
            finally:
                if payload_temp:
                    try:
                        os.unlink(payload_temp)
                    except FileNotFoundError:
                        pass
    log(f"[edit] → {os.path.basename(out)} ({len(payload['words'])} từ, "
        f"{time.time() - t0:.1f}s)")
    return out


def transcribe_all(footage, work_dir, language=DEFAULT_LANGUAGE, force=False):
    videos = videos_in(footage)
    if not videos:
        raise StationMissing(f"không có file quay nào trong {footage} "
                             f"(nhận: {', '.join(sorted(VIDEO_EXTS))})")
    _preflight_transcript_targets(videos, work_dir)
    model = load_model()
    return [transcribe_one(v, work_dir, language=language, force=force, model=model)
            for v in videos]
