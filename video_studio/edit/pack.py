"""pack.py — gom transcript mức TỪ thành file markdown mức CỤM để agent đọc mà chọn đoạn cắt.

Nguồn: `browser-use/video-use` (MIT, © 2026 Browser Use) — `helpers/pack_transcripts.py`, đọc
tại bản vendored `92c2b34`; **đã sửa**: đọc/ghi luôn `encoding="utf-8"` (bản gốc dùng
`Path.read_text()` theo locale, nên trên Windows cp1252 một transcript tiếng Việt là
`UnicodeDecodeError`), và hàm trả dữ liệu thay vì in ra.

Đây là tài sản giá trị nhất của bộ `edit`: một giờ quay ở dạng JSON mức từ là hàng trăm nghìn
token, cùng nội dung đó ở dạng cụm có mốc `[bắt đầu-kết thúc]` chỉ còn một phần mười — mà vẫn
đủ chính xác để chỉ ra điểm cắt, vì mốc lấy từ biên của từ thật.
"""
import json
import os

SILENCE = 0.5

__all__ = ["SILENCE", "group_into_phrases", "pack_file", "render_markdown", "pack_dir"]


def _fmt_time(seconds):
    return f"{float(seconds):06.2f}"


def _fmt_dur(seconds):
    if seconds < 60:
        return f"{seconds:.1f}s"
    m = int(seconds // 60)
    return f"{m}m {seconds - m * 60:04.1f}s"


def group_into_phrases(words, silence=SILENCE):
    """Danh sách từ (khuôn Scribe) → danh sách cụm {start, end, text, speaker_id}.

    Ngắt cụm khi: khoảng lặng ≥ `silence`, hoặc đổi người nói. Mục `spacing` chỉ mang thông tin
    khoảng lặng; `audio_event` (tiếng cười, tiếng gõ) được giữ trong ngoặc vì nó là manh mối
    chọn đoạn, không phải rác.
    """
    phrases, cur, start, speaker, prev_end = [], [], None, None, None

    def flush():
        nonlocal cur, start, speaker
        parts = []
        for w in cur:
            raw = (w.get("text") or "").strip()
            if not raw:
                continue
            if w.get("type") == "audio_event" and not raw.startswith("("):
                raw = f"({raw})"
            parts.append(raw)
        if parts:
            text = " ".join(parts)
            for a, b in ((" ,", ","), (" .", "."), (" ?", "?"), (" !", "!")):
                text = text.replace(a, b)
            last = cur[-1]
            phrases.append({"start": start, "end": last.get("end", last.get("start", start)),
                            "text": text, "speaker_id": speaker})
        cur, start, speaker = [], None, None

    for w in words or []:
        kind = w.get("type", "word")
        if kind == "spacing":
            s, e = w.get("start"), w.get("end")
            if s is not None and e is not None and e - s >= silence:
                flush()
            continue
        s = w.get("start")
        if s is None:
            continue
        spk = w.get("speaker_id")
        if speaker is not None and spk is not None and spk != speaker:
            flush()
        if prev_end is not None and s - prev_end >= silence:
            flush()
        if start is None:
            start, speaker = s, spk
        cur.append(w)
        prev_end = w.get("end", s)
    flush()
    return phrases


def pack_file(path, silence=SILENCE):
    """-> (tên nguồn, thời lượng, cụm). `path` là transcript JSON của một file quay."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    phrases = group_into_phrases(data.get("words"), silence)
    duration = (phrases[-1]["end"] - phrases[0]["start"]) if phrases else 0.0
    return os.path.splitext(os.path.basename(path))[0], duration, phrases


def render_markdown(entries, silence=SILENCE):
    lines = ["# Bản ghi lời đã gom cụm", "",
             f"Cụm được ngắt ở khoảng lặng ≥ {silence:.1f}s hoặc khi đổi người nói.",
             "Dùng mốc `[bắt đầu-kết thúc]` (giây) để chỉ đoạn cắt trong EDL.", ""]
    for name, duration, phrases in entries:
        lines.append(f"## {name}  (dài {_fmt_dur(duration)}, {len(phrases)} cụm)")
        if not phrases:
            lines += ["  _không nghe thấy lời nào_", ""]
            continue
        for p in phrases:
            spk = p.get("speaker_id")
            tag = ""
            if spk is not None:
                s = str(spk)
                tag = " S" + (s[len("speaker_"):] if s.startswith("speaker_") else s)
            lines.append(f"  [{_fmt_time(p['start'])}-{_fmt_time(p['end'])}]{tag} {p['text']}")
        lines.append("")
    return "\n".join(lines)


def pack_dir(transcripts_dir, out_path, silence=SILENCE):
    """Gom mọi `*.json` trong `transcripts_dir` → một file markdown. -> dict tóm tắt."""
    files = sorted(os.path.join(transcripts_dir, n) for n in os.listdir(transcripts_dir)
                   if n.lower().endswith(".json"))
    entries = [pack_file(p, silence) for p in files]
    os.makedirs(os.path.dirname(os.path.abspath(out_path)) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(render_markdown(entries, silence))
    return {"path": os.path.abspath(out_path), "sources": len(entries),
            "phrases": sum(len(e[2]) for e in entries),
            "runtime": round(sum(e[1] for e in entries), 2)}
