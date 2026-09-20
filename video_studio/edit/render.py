"""render.py — EDL → một video hoàn chỉnh.

Nguồn: `browser-use/video-use` (MIT, © 2026 Browser Use) — `helpers/render.py`, đọc tại bản
vendored `92c2b34`, có mang theo ba bản sửa upstream sau mốc đó (giữ fps nguồn #55, tôn trọng
góc xoay metadata #137, chọn đúng track tiếng #134 — xem `_ff.py`); **đã sửa** thêm: ffmpeg qua
`_env`, lỗi thành mã thoát theo hợp đồng, và đường trong EDL neo vào thư mục chứa EDL.

**Thứ tự bốn bước không được đổi** — mỗi bước là một bài học:

1. **Cắt từng đoạn riêng**, chỉnh màu và vuốt 30 ms hai đầu tiếng NGAY trong bước này. Vuốt
   sau khi đã nối thì mối nối đã kêu "tạch" rồi.
2. **Nối bằng `-c copy`** (concat demuxer): không giải mã lại ⇒ không mất chất, và nhanh.
3. **Ghép overlay rồi PHỤ ĐỀ SAU CÙNG** trong MỘT filter graph. Phụ đề đi trước overlay thì
   chữ bị đè; overlay phải dịch PTS để khung 0 của nó rơi đúng mốc trong video ra.
4. **Chuẩn âm lượng hai lượt** (-14 LUFS): nền tảng nào cũng tự chuẩn hoá khi đăng, làm trước
   thì mình chọn được điểm rơi thay vì để nền tảng kéo.

`MarginV` của phụ đề không phải khẩu vị mà là vùng an toàn: giao diện của các nền tảng video
dọc che khoảng 25–30 % đáy khung.
"""
import os
import re

from ..contract import ContractError, EngineError, log
from . import _ff, edl as edl_mod, grade as grade_mod

SUB_FORCE_STYLE = ("FontName=Helvetica,FontSize=18,Bold=1,"
                   "PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BackColour=&H00000000,"
                   "BorderStyle=1,Outline=2,Shadow=0,Alignment=2,MarginV=90")

# PQ (HDR10) / HLG → Rec.709 SDR. Hạ độ sâu bit mà KHÔNG tone-map thì file ra vẫn mang metadata
# HDR: máy nào tôn trọng metadata sẽ hiện màu cháy — và chỉ lộ ra sau khi đã đăng.
TONEMAP = ("zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,"
           "tonemap=tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p")

QUALITY = {                       # tên → (chiều cao, preset x264, CRF)
    "final":   (1920, "fast", "20"),
    "preview": (1920, "medium", "22"),
    "draft":   (1280, "ultrafast", "28"),
}
LOUDNORM = {"I": -14.0, "TP": -1.0, "LRA": 11.0}
PUNCT = set(".,!?;:")
FADE = 0.03

__all__ = ["QUALITY", "extract_segment", "concat", "build_master_srt", "composite",
           "loudnorm", "render_edl"]


# ── bước 1: cắt từng đoạn ───────────────────────────────────────────────────────────────

def extract_segment(source, start, duration, out_path, grade_filter="", quality="final",
                    fps=None, probe=None):
    """Cắt một khoảng thành MP4 riêng, đã chỉnh màu và vuốt tiếng hai đầu."""
    p = probe or _ff.probe(source)
    size, preset, crf = QUALITY[quality]
    os.makedirs(os.path.dirname(os.path.abspath(out_path)) or ".", exist_ok=True)
    vf = []
    if p.hdr:
        vf.append(TONEMAP)
    vf.append(f"scale=-2:{size}" if p.portrait else f"scale={size}:-2")
    if grade_filter:
        vf.append(grade_filter)
    fade_out = max(0.0, float(duration) - FADE)
    args = ["-y", "-ss", f"{float(start):.3f}", "-i", str(source), "-t", f"{float(duration):.3f}",
            "-vf", ",".join(vf),
            "-af", f"afade=t=in:st=0:d={FADE},afade=t=out:st={fade_out:.3f}:d={FADE}",
            "-c:v", "libx264", "-preset", preset, "-crf", crf, "-pix_fmt", "yuv420p"]
    # Giữ fps CỦA NGUỒN (upstream #55): ép 24 làm quay 60fps giật, và trộn nhiều fps trong một
    # lần nối `-c copy` thì tiếng trôi dần khỏi hình.
    rate = fps or p.fps
    if rate:
        args += ["-r", f"{rate:g}"]
    amap = p.audio_map()
    if amap:
        args += ["-map", "0:v:0", "-map", amap]
    args += ["-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart",
             str(out_path)]
    _ff.run(args)
    return out_path


def extract_all(data, base_dir, work_dir, quality="final", fps=None):
    """Cắt mọi đoạn của EDL. -> danh sách file theo đúng thứ tự dựng."""
    default = grade_mod.resolve_filter(data.get("grade", "auto"))
    clips_dir = os.path.join(work_dir, f"clips_{quality}")
    os.makedirs(clips_dir, exist_ok=True)
    probes = {}
    out = []
    log(f"[edit] cắt {len(data['ranges'])} đoạn → {os.path.basename(clips_dir)}/")
    for i, r in enumerate(data["ranges"]):
        src = edl_mod.resolve(data["sources"][r["source"]], base_dir)
        if not os.path.isfile(src):
            raise ContractError(f"sources[{r['source']!r}] trỏ vào file không có: {src}")
        if src not in probes:
            probes[src] = _ff.probe(src)
        start, dur = r["start"], r["end"] - r["start"]
        flt = grade_mod.resolve_filter(r["grade"]) if r.get("grade") else default
        if flt == grade_mod.AUTO:
            flt, _stats = grade_mod.auto_for_clip(src, start=start, duration=dur)
        note = r.get("beat") or r.get("note") or ""
        log(f"  [{i:02d}] {r['source']}  {start:7.2f}-{r['end']:7.2f}  ({dur:5.2f}s)  {note}")
        dst = os.path.join(clips_dir, f"seg_{i:02d}_{r['source']}.mp4")
        extract_segment(src, start, dur, dst, grade_filter=flt, quality=quality, fps=fps,
                        probe=probes[src])
        out.append(dst)
    return out


# ── bước 2: nối không giải mã lại ───────────────────────────────────────────────────────

def concat(segments, out_path, work_dir):
    if not segments:
        raise ContractError("không có đoạn nào để nối")
    listing = os.path.join(work_dir, "_concat.txt")
    with open(listing, "w", encoding="utf-8", newline="\n") as f:
        for p in segments:
            f.write("file '%s'\n" % os.path.abspath(p).replace("\\", "/").replace("'", r"'\''"))
    try:
        _ff.run(["-y", "-f", "concat", "-safe", "0", "-i", listing, "-c", "copy",
                 "-movflags", "+faststart", str(out_path)])
    finally:
        try:
            os.remove(listing)
        except OSError:
            pass
    log(f"[edit] nối → {os.path.basename(out_path)}")
    return out_path


# ── bước 3a: phụ đề theo mốc thời gian của VIDEO RA ─────────────────────────────────────

def _srt_time(seconds):
    ms = int(round(seconds * 1000))
    h, rem = divmod(ms, 3600_000)
    m, rem = divmod(rem, 60_000)
    s, ms = divmod(rem, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _words_in(transcript, start, end):
    out = []
    for w in transcript.get("words") or []:
        if w.get("type") != "word":
            continue
        ws, we = w.get("start"), w.get("end")
        if ws is None or we is None or we <= start or ws >= end:
            continue
        out.append(w)
    return out


def build_master_srt(data, work_dir, out_path):
    """Dựng SRT theo mốc của video RA từ transcript của từng nguồn.

    Cụm 2 từ, VIẾT HOA, ngắt thêm ở dấu câu: kiểu phụ đề đọc được trên điện thoại. Mốc =
    `từ.start − đoạn.start + tổng thời lượng các đoạn trước`.
    """
    import json
    tdir = os.path.join(work_dir, "transcripts")
    entries, offset = [], 0.0
    for r in data["ranges"]:
        seg_start, seg_end = r["start"], r["end"]
        dur = seg_end - seg_start
        tpath = os.path.join(tdir, f"{r['source']}.json")
        if not os.path.isfile(tpath):
            log(f"  ! chưa bóc lời {r['source']} — đoạn này không có phụ đề")
            offset += dur
            continue
        with open(tpath, "r", encoding="utf-8") as f:
            transcript = json.load(f)
        chunk = []
        for w in _words_in(transcript, seg_start, seg_end):
            text = (w.get("text") or "").strip()
            if not text:
                continue
            chunk.append(w)
            if len(chunk) >= 2 or text[-1] in PUNCT:
                entries.append(_cue(chunk, seg_start, seg_end, offset))
                chunk = []
        if chunk:
            entries.append(_cue(chunk, seg_start, seg_end, offset))
        offset += dur
    entries.sort(key=lambda e: e[0])
    lines = []
    for i, (a, b, text) in enumerate(entries, start=1):
        lines += [str(i), f"{_srt_time(a)} --> {_srt_time(b)}", text, ""]
    with open(out_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))
    log(f"[edit] phụ đề → {os.path.basename(out_path)} ({len(entries)} dòng)")
    return out_path


def _cue(chunk, seg_start, seg_end, offset):
    a = max(seg_start, chunk[0].get("start", seg_start)) - seg_start + offset
    b = min(seg_end, chunk[-1].get("end", seg_end)) - seg_start + offset
    if b <= a:
        b = a + 0.4
    text = re.sub(r"\s+", " ", " ".join((w.get("text") or "").strip() for w in chunk)).strip()
    return (max(0.0, a), max(0.0, b), text.rstrip(",;:").upper())


# ── bước 3b: overlay + phụ đề ───────────────────────────────────────────────────────────

def _escape_sub(path):
    return str(path).replace("\\", "/").replace(":", r"\:").replace("'", r"\'")


def composite(base_path, overlays, subtitles, out_path, base_dir):
    """Ghép overlay (đã dịch PTS) rồi đốt phụ đề SAU CÙNG. Không có gì để ghép thì chép sang."""
    has_subs = bool(subtitles) and os.path.isfile(subtitles)
    if not overlays and not has_subs:
        _ff.run(["-y", "-i", str(base_path), "-c", "copy", str(out_path)])
        return out_path
    args = ["-y", "-i", str(base_path)]
    for ov in overlays:
        args += ["-i", edl_mod.resolve(ov["file"], base_dir)]
    parts, current = [], "[0:v]"
    for idx, ov in enumerate(overlays, start=1):
        t = float(ov["start_in_output"])
        parts.append(f"[{idx}:v]setpts=PTS-STARTPTS+{t}/TB[a{idx}]")
    for idx, ov in enumerate(overlays, start=1):
        t = float(ov["start_in_output"])
        end = t + float(ov["duration"])
        label = f"[v{idx}]"
        parts.append(f"{current}[a{idx}]overlay=enable='between(t,{t:.3f},{end:.3f})'{label}")
        current = label
    if has_subs:
        parts.append(f"{current}subtitles='{_escape_sub(subtitles)}'"
                     f":force_style='{SUB_FORCE_STYLE}'[outv]")
        out_label = "[outv]"
    else:
        parts.append(f"{current}null[outv]")
        out_label = "[outv]"
    args += ["-filter_complex", ";".join(parts), "-map", out_label, "-map", "0:a?",
             "-c:v", "libx264", "-preset", "fast", "-crf", "18", "-pix_fmt", "yuv420p",
             "-c:a", "copy", "-movflags", "+faststart", str(out_path)]
    log(f"[edit] ghép → {os.path.basename(out_path)} "
        f"(overlay: {len(overlays)}, phụ đề: {'có' if has_subs else 'không'})")
    _ff.run(args)
    return out_path


# ── bước 4: chuẩn âm lượng ──────────────────────────────────────────────────────────────

def _measure(path):
    import json
    flt = (f"loudnorm=I={LOUDNORM['I']}:TP={LOUDNORM['TP']}:LRA={LOUDNORM['LRA']}"
           ":print_format=json")
    err = _ff.run(["-y", "-i", str(path), "-af", flt, "-vn", "-f", "null", "-"], quiet=False)
    a, b = err.rfind("{"), err.rfind("}")
    if a == -1 or b <= a:
        return None
    try:
        data = json.loads(err[a:b + 1])
    except ValueError:
        return None
    need = {"input_i", "input_tp", "input_lra", "input_thresh", "target_offset"}
    return data if need <= set(data) else None


def loudnorm(in_path, out_path, one_pass=False):
    """Chuẩn về -14 LUFS. Hai lượt (đo rồi chỉnh) trừ khi `one_pass`. -> True nếu hai lượt."""
    base = f"loudnorm=I={LOUDNORM['I']}:TP={LOUDNORM['TP']}:LRA={LOUDNORM['LRA']}"
    m = None if one_pass else _measure(in_path)
    if m:
        flt = (base + f":measured_I={m['input_i']}:measured_TP={m['input_tp']}"
                      f":measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}"
                      f":offset={m['target_offset']}:linear=true")
    else:
        flt = base
    _ff.run(["-y", "-i", str(in_path), "-c:v", "copy", "-af", flt,
             "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart",
             str(out_path)])
    return bool(m)


# ── ráp lại ─────────────────────────────────────────────────────────────────────────────

def render_edl(data, base_dir, work_dir, out_path, quality="final", build_subtitles=False,
               subtitles=True, normalize=True, fps=None):
    """EDL đã kiểm → video hoàn chỉnh. -> dict kết quả."""
    if quality not in QUALITY:
        raise ContractError(f"mức chất lượng lạ: {quality} (có: {', '.join(QUALITY)})")
    os.makedirs(work_dir, exist_ok=True)
    os.makedirs(os.path.dirname(os.path.abspath(out_path)) or ".", exist_ok=True)
    segments = extract_all(data, base_dir, work_dir, quality=quality, fps=fps)
    base = os.path.join(work_dir, f"base_{quality}.mp4")
    concat(segments, base, work_dir)

    subs = None
    if subtitles:
        if build_subtitles:
            subs = build_master_srt(data, work_dir, os.path.join(work_dir, "master.srt"))
        elif data.get("subtitles"):
            cand = edl_mod.resolve(data["subtitles"], base_dir)
            if os.path.isfile(cand):
                subs = cand
            else:
                log(f"  ! EDL trỏ phụ đề không có: {cand} — bỏ qua")

    if normalize:
        tmp = os.path.splitext(out_path)[0] + ".prenorm.mp4"
        composite(base, data["overlays"], subs, tmp, base_dir)
        two_pass = loudnorm(tmp, out_path)
        try:
            os.remove(tmp)
        except OSError:
            pass
    else:
        two_pass = False
        composite(base, data["overlays"], subs, out_path, base_dir)
    if not os.path.isfile(out_path):
        raise EngineError(f"ffmpeg kết thúc nhưng không có file ra: {out_path}")
    size = os.path.getsize(out_path)
    log(f"[edit] xong: {out_path} ({size / (1024 * 1024):.1f} MB)")
    return {"outputs": [{"kind": "video", "path": os.path.abspath(out_path),
                         "duration": edl_mod.total_duration(data)}],
            "segments": len(segments), "quality": quality, "subtitles": subs,
            "loudnorm": "two-pass" if two_pass else ("one-pass" if normalize else "off"),
            "bytes": size}
