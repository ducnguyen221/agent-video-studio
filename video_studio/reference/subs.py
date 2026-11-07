"""subs.py — transcript của video mẫu: phụ đề gốc trước, bóc lời tại máy sau.

Thứ tự nguồn: `--subs` -> phụ đề cạnh video / trong `<project>/source/` -> luồng chữ nhúng trong video
-> ASR (`edit.transcribe.transcribe_one`). Chữ trong phụ đề là DỮ LIỆU: chỉ được đọc, không bao giờ
chạy; nhánh duy nhất gọi tiến trình con là ffmpeg/ffprobe ở nhánh nhúng.

Lỗi: tham số sai, phụ đề hỏng/quá lớn, transcript đã có mà thiếu `--force` = `ContractError`;
thiếu faster-whisper khi không có phụ đề = `StationMissing`.
"""
import json
import os
import re
import tempfile

from .. import _env
from ..contract import ContractError, StationMissing, log
from ..edit import _ff

MAX_SUBS_BYTES = 5 * 1024 * 1024

_LANG_RE = re.compile(r"[A-Za-z0-9-]{1,16}")
_TEXT_CODECS = ("subrip", "ass", "ssa", "webvtt", "mov_text")
_TAG_RE = re.compile(r"<[^>]*>|\{\\[^}]*\}")
_TIME_RE = r"(?:(\d+):)?(\d{1,2}):(\d{2})[.,](\d{1,3})"
_CUE_LINE = re.compile(r"\s*" + _TIME_RE + r"\s*-->\s*" + _TIME_RE)
_MERGE_GAP = 0.001


# ------------------------------------------------------------------ parse

def _seconds(h, m, s, frac):
    return int(h or 0) * 3600 + int(m) * 60 + int(s) + float("0." + frac)


def _clean(lines):
    text = _TAG_RE.sub("", " ".join(lines))
    return " ".join(text.split())


def _parse_blocks(text):
    cues = []
    blocks = re.split(r"\n\s*\n", (text or "").replace("\r\n", "\n").replace("\r", "\n"))
    for block in blocks:
        lines = block.strip("\n").split("\n")
        first = lines[0].strip().lstrip("﻿") if lines else ""
        if first.split(" ")[0] in ("NOTE", "STYLE", "REGION") or first.startswith("WEBVTT"):
            continue
        for i, line in enumerate(lines):
            m = _CUE_LINE.match(line)
            if not m:
                continue
            g = m.groups()
            start = _seconds(g[0], g[1], g[2], g[3])
            end = _seconds(g[4], g[5], g[6], g[7])
            body = _clean(lines[i + 1:])
            if end >= start and body:
                cues.append({"start": start, "end": end, "text": body})
            break
    return cues


def parse_srt(text):
    """Cue `{"start","end","text"}` từ SRT; khối hỏng thời điểm hoặc `end < start` bị bỏ."""
    return _parse_blocks(text)


def parse_vtt(text):
    """Như `parse_srt` cho WebVTT; cue liền nhau cùng chữ, nối thời gian -> gộp (`end` lấy cue sau)."""
    merged = []
    for cue in _parse_blocks(text):
        if (merged and merged[-1]["text"] == cue["text"]
                and cue["start"] <= merged[-1]["end"] + _MERGE_GAP):
            merged[-1]["end"] = max(merged[-1]["end"], cue["end"])
        else:
            merged.append(dict(cue))
    return merged


def cues_to_transcript(cues, language, source):
    """Transcript theo contract mục 7: độ mịn `cue`, không giả vờ là từng từ."""
    return {
        "text": " ".join(c["text"] for c in cues),
        "language_code": language,
        "words": [{"type": "cue", "text": c["text"], "start": c["start"], "end": c["end"],
                   "speaker_id": None} for c in cues],
        "granularity": "cue",
        "_source": source,
    }


def _read_cues(path):
    ext = os.path.splitext(path)[1].lower()
    if ext not in (".srt", ".vtt"):
        raise ContractError(f"phụ đề phải là .srt hoặc .vtt, nhận {ext or 'không đuôi'}: {path}")
    if os.path.getsize(path) > MAX_SUBS_BYTES:
        raise ContractError(f"phụ đề lớn hơn {MAX_SUBS_BYTES} byte: {path}")
    with open(path, "rb") as f:
        text = f.read().decode("utf-8-sig", errors="replace")
    cues = parse_srt(text) if ext == ".srt" else parse_vtt(text)
    if not cues:
        raise ContractError(f"phụ đề không đọc được (0 cue hợp lệ): {path}")
    return cues


# ------------------------------------------------------------------ nguồn

def _check_language(language):
    if language != "auto" and not (isinstance(language, str) and _LANG_RE.fullmatch(language)):
        raise ContractError("--language không hợp lệ: chỉ nhận 'auto' hoặc 1-16 ký tự "
                            "chữ, số, dấu gạch ngang")


def find_sidecar(video, project_dir, language):
    """Phụ đề cạnh video rồi trong `<project>/source/`; None nếu không có."""
    _check_language(language)
    stem = os.path.splitext(os.path.basename(video))[0]
    names = [f"{stem}.vtt", f"{stem}.srt"]
    if language != "auto":
        names = [f"{stem}.{language}.vtt", f"{stem}.{language}.srt"] + names
    for d in (os.path.dirname(os.path.abspath(video)), os.path.join(project_dir, "source")):
        for name in names:
            p = os.path.join(d, name)
            if os.path.isfile(p):
                return p
    return None


def _pick_text_stream(raw, language):
    """(k, index) của luồng chữ được chọn; k = thứ tự trong các luồng phụ đề (cho `-map 0:s:k`)."""
    subtitle = [s for s in (raw.get("streams") or []) if s.get("codec_type") == "subtitle"]
    text = [(k, s) for k, s in enumerate(subtitle) if s.get("codec_name") in _TEXT_CODECS]
    if not text:
        return None
    chosen = text[0]
    if language and language != "auto":
        for k, s in text:
            if str((s.get("tags") or {}).get("language", "")).lower() == language.lower():
                chosen = (k, s)
                break
    return chosen[0], chosen[1].get("index", chosen[0])


def _extract_embedded(video, dest_dir, language=None):
    if not _env.ffprobe_exe():
        return None
    picked = _pick_text_stream(_ff._probe_raw(video), language)
    if picked is None:
        return None
    k, index = picked
    dest = os.path.join(dest_dir, "embedded.srt")
    _ff.run(["-y", "-i", str(video), "-map", f"0:s:{k}", "-c:s", "srt", dest])
    if not os.path.isfile(dest):
        return None
    return dest, index


def extract_embedded(video, dest_dir):
    """Xuất luồng phụ đề chữ đầu tiên của video ra `dest_dir`; None nếu không có ffprobe/luồng chữ."""
    got = _extract_embedded(video, dest_dir)
    return got[0] if got else None


def _write_json(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
            f.write("\n")
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def _from_cues(cues, language, source, out, stream=None):
    transcript = cues_to_transcript(cues, None if language == "auto" else language, source)
    if stream is not None:
        transcript["_source_stream"] = stream
    _write_json(out, transcript)
    return {"transcript": out, "source": source, "granularity": "cue", "entries": len(cues)}


def transcribe(input_path, project_dir, subs=None, language="vi", force=False):
    """Transcript của `input_path` vào `<project>/transcripts/<stem>.json`.

    Nhánh phụ đề ghi tệp KHÔNG kèm `.meta`; lượt ASR sau đó (`force`, hoặc không còn phụ đề)
    coi nó là cache miss và ghi đè — đúng ý. Chiều ngược (đã có bản ASR, nay đưa `subs`) cần `force`.
    """
    _check_language(language)
    if not os.path.isfile(input_path):
        raise ContractError(f"--input không phải tệp: {input_path}")
    if not os.path.isdir(project_dir):
        raise ContractError(f"--project không phải thư mục: {project_dir}")
    stem = os.path.splitext(os.path.basename(input_path))[0]
    out = os.path.join(project_dir, "transcripts", stem + ".json")
    if os.path.exists(out) and not force:
        raise ContractError(f"đã có transcript {out}; thêm --force để ghi đè")

    if subs is not None:
        if not os.path.isfile(subs):
            raise ContractError(f"--subs không phải tệp: {subs}")
        return _from_cues(_read_cues(subs), language, "subtitles:file", out)

    side = find_sidecar(input_path, project_dir, language)
    if side:
        return _from_cues(_read_cues(side), language, "subtitles:sidecar", out)

    with tempfile.TemporaryDirectory() as tmp:
        got = _extract_embedded(input_path, tmp, language)
        if got:
            return _from_cues(_read_cues(got[0]), language, "subtitles:embedded", out, got[1])

    from ..edit import transcribe as asr
    if not asr.available():
        raise StationMissing("không có phụ đề và chưa có `faster-whisper` — đưa phụ đề bằng "
                             "--subs, hoặc " + asr.INSTALL_HINT)
    log(f"[reference] không có phụ đề gốc, bóc lời tại máy: {os.path.basename(input_path)}")
    path = asr.transcribe_one(input_path, project_dir,
                              language=None if language == "auto" else language, force=force)
    with open(path, encoding="utf-8") as f:
        entries = len(json.load(f).get("words") or [])
    return {"transcript": path, "source": "asr:faster-whisper", "granularity": "word",
            "entries": entries}
