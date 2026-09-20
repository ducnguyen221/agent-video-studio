"""news_video — slide HyperFrames + lồng tiếng cho bản tin (recap dài + short dọc).

Ba lối vào:
  `make(item, out_path, date, brand, …)`          — một slide tin nóng (khuôn sidecar cũ)
  `make_weekly(video_obj, out_path, date, …)`     — recap 16:9 5–7 phút: slide mở đầu + một
      đoạn cho mỗi tin (2–3 ảnh chồng mờ, lời dẫn tiếng Việt) + slide kết
  `make_weekly_short(video_obj, out_path, …)`     — bản dọc 9:16 ~60–90 s

`video_obj` = object "weekly_video"/"daily_video" của spec:
  { intro, outro, segments: [{aid, headline, narration, images: [url, …]}] }

Project HyperFrames nằm trong TRẠM (`<trạm>/projects/news`), không phải trong repo — đường
dẫn do `video_studio._env` quyết, cấu hình chép một lần từ `demo/`.

THƯƠNG HIỆU KHÔNG CÓ MẶC ĐỊNH: `brand` phải đến từ spec (a · b · site). Thiếu ⇒ mã 2. Mặc
định im lặng chính là cách một engine dùng chung phát tán danh tính của người khác.
"""
from __future__ import annotations

import glob
import difflib
import json
import os
import re
import shutil
import urllib.parse
import urllib.request

import numpy as np
import soundfile as sf

from voice_studio import av, engine, profiles

from ... import _env, projects, render
from ...contract import ContractError
from ...spec import REQUIRED_BRAND

PROJECT = "news"


def _proj():
    """Thư mục project `news` trong trạm (tạo + chép cấu hình từ `demo/` nếu còn thiếu)."""
    return projects.ensure(PROJECT)


_ensure_project = _proj          # tên cũ, các template khác còn gọi

# Chỉ là CÁCH DIỄN ĐẠT mặc định, KHÔNG phải danh tính: a · b · site bắt buộc từ spec, và mọi
# câu chữ dưới đây tự dựng lại từ tên thương hiệu đã khai.
BRAND_DEFAULTS = {
    # Cách diễn đạt mốc thời gian — bản NGÀY đè bằng brand của mình.
    "rank_suffix": "TUẦN NÀY",                     # huy hiệu hạng: "TOP n <rank_suffix>"
    "outro_big": "Hẹn gặp tuần sau!",              # slide kết bản dài
    "outro_sub": "Đọc bản tin đầy đủ kèm audio tại",
    "outro_big_short": "Đọc bản tin<br>đầy đủ",    # slide kết bản short
    "outro_sub_short": "kèm audio + video chi tiết",
}

# Bảng đọc (regex → cách đọc) lấy từ brand.pronounce của spec; nạp ở resolve_brand().
PRONOUNCE = {}


def resolve_brand(brand):
    """Trộn brand của spec lên BRAND_DEFAULTS. Thiếu a/b/site ⇒ ContractError (mã 2).

    Cũng nạp bảng phát âm cho `_tts_normalize` — bản cũ nhét thẳng một tên miền vào regex.
    """
    brand = dict(brand or {})
    missing = [k for k in REQUIRED_BRAND if not str(brand.get(k) or "").strip()]
    if missing:
        raise ContractError(
            "thiếu brand." + ", brand.".join(missing) + " — template không có thương hiệu mặc "
            "định, khai brand trong spec (a, b, site).")
    out = {**BRAND_DEFAULTS, **brand}
    out.setdefault("tagline", f"{out['a']} {out['b']}")
    out.setdefault("tagline_short", f"{out['a']} {out['b']}")
    out.setdefault("welcome", f"Chào mừng đến với {out['a']} {out['b']}")
    set_pronounce(out.get("pronounce"))
    return out


def set_pronounce(table):
    """Nạp bảng phát âm dùng cho mọi lần chuẩn hoá trước TTS trong tiến trình này."""
    PRONOUNCE.clear()
    for pat, rep in (table or {}).items():
        PRONOUNCE[re.compile(pat, re.I)] = rep


def _brandify(html, brand):
    return (html.replace("{BA}", _esc(brand["a"]))
                .replace("{BB}", _esc(brand["b"]))
                .replace("{BSITE}", _esc(brand["site"])))


def _ffmpeg_bin_dir():
    """Thư mục chứa ffmpeg + ffprobe (HyperFrames cần CẢ HAI): FFMPEG_DIR → PATH.

    Bản cũ dò thư mục gói WinGet bằng glob — đúng trên đúng một máy Windows.
    """
    exe = _env.ffmpeg_exe()
    return os.path.dirname(exe) if exe else None


def _esc(s: str) -> str:
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ---- SHORT component library (dùng CHUNG cho daily top_story + weekly) --------
# AI chọn diagram.type trong bộ này; renderer dựng block tương ứng. Mỗi child mang
# id {sid}-b{j} để timeline reveal đúng nhịp đọc (beat-sync). 1 nguồn -> tránh drift.
SHORT_PALETTE = {"stats", "bullets", "tags", "process", "bars", "quote", "bignum", "warning", "verdict"}


def hl_word(w):
    """Caption keyword-highlight (escbase-style): từ mang SỐ LIỆU/thuật ngữ tech
    được tô vàng thay vì trắng khi karaoke chạy tới. True nếu đáng highlight:
    có chữ số/%/x-nhân, ALL-CAPS (GPU, API), hoặc tên tech có hoa giữa từ (GitHub)."""
    t = (w or "").strip(".,;:!?…\"'()")
    if not t:
        return False
    if re.search(r"\d|%", t):
        return True
    if t.isascii() and len(t) >= 2 and t.isupper():
        return True
    return bool(t.isascii() and re.search(r"[a-z][A-Z]", t))


def asr_drift_warn(words, spoken, label=""):
    """E — lưới an toàn: so khớp ASR (giọng đã render) vs lời ĐỊNH đọc. Lệch nhiều
    = giọng/đọc lỗi (nuốt chữ, sai từ) -> cảnh báo trước khi publish. words từ
    _asr_words [(w,start,end)]; spoken = text đưa vào TTS. Best-effort, không chặn."""
    if not words or not spoken:
        return None
    norm = lambda s: set(re.findall(r"\w+", (s or "").lower()))
    sp = norm(spoken)
    if not sp:
        return None
    asr = norm(" ".join(w[0] for w in words))
    overlap = len(sp & asr) / len(sp)
    if overlap < 0.55:
        print(f"  [ASR-guard][WARN] {label}: giọng/đọc có thể LỆCH (trùng {overlap:.0%} < 55%) "
              f"-> kiểm tra clip trước khi publish.", flush=True)
    return overlap


def _bar_pct(val, j, n):
    """Suy ra % chiều rộng thanh bar từ giá trị (vd '70%', '2 triệu', '8.5'); không
    parse được -> thang giảm dần theo thứ tự để vẫn có tương quan thị giác."""
    import re as _re
    m = _re.search(r"(\d+(?:[.,]\d+)?)", str(val or ""))
    if m:
        x = float(m.group(1).replace(",", "."))
        if "%" in str(val):
            return max(6, min(100, x))
        # không phải %: chuẩn hoá tương đối trong cụm (giá trị lớn nhất = 100)
        return x  # caller chuẩn hoá lại theo max
    return int(round(100 - j * (70.0 / max(1, n))))


def short_card_block(typ, items, sid):
    """items = list (a, b) (raw text; a=chính, b=phụ/giá trị). Trả (html, n_children).
    typ ngoài SHORT_PALETTE -> bullets."""
    typ = (typ or "bullets").lower()
    items = [(a or "", b or "") for a, b in items]
    n = len(items)
    if typ == "stats":
        cards = "".join(f'<div class="statc" id="{sid}-b{j}"><b>{_esc(a)}</b><span>{_esc(b)}</span></div>'
                        for j, (a, b) in enumerate(items))
        return f'<div class="salist statgrid">{cards}</div>', n
    if typ == "tags":
        cards = "".join(f'<span class="tag" id="{sid}-b{j}">{_esc(a)}</span>' for j, (a, b) in enumerate(items))
        return f'<div class="salist tagp">{cards}</div>', n
    if typ == "process":
        parts = [f'<span class="proc" id="{sid}-b{j}"><i>{j + 1}</i>{_esc(a)}</span>'
                 for j, (a, b) in enumerate(items)]
        return f'<div class="salist procp">{"".join(parts)}</div>', n
    if typ == "bars":
        raw = [_bar_pct(b, j, n) for j, (a, b) in enumerate(items)]
        mx = max([r for r in raw] or [100]) or 100
        pcts = [max(6, min(100, (r / mx * 100) if mx > 100 or mx < 100 and "%" not in str(items[j][1]) else r))
                for j, r in enumerate(raw)]
        rows = []
        for j, (a, b) in enumerate(items):
            rows.append(f'<div class="barr" id="{sid}-b{j}"><span class="barl">{_esc(a)}</span>'
                        f'<span class="bart"><i style="width:{pcts[j]:.0f}%"></i></span>'
                        f'<span class="barv">{_esc(b)}</span></div>')
        return f'<div class="salist barlist">{"".join(rows)}</div>', n
    if typ == "quote":
        a, b = items[0] if items else ("", "")
        tail = f"<span>{_esc(b)}</span>" if b else ""
        return f'<div class="salist"><div class="quotec" id="{sid}-b0">“{_esc(a)}”{tail}</div></div>', 1
    if typ == "bignum":
        a, b = items[0] if items else ("", "")
        return f'<div class="salist"><div class="bignum" id="{sid}-b0"><b>{_esc(a)}</b><span>{_esc(b)}</span></div></div>', 1
    if typ == "warning":
        # escbase warning-chips: chip hổ phách ⚠ — cho section "lưu ý/cạm bẫy/hiểu nhầm"
        cards = "".join(f'<span class="warnc" id="{sid}-b{j}">⚠ {_esc(a)}</span>' for j, (a, b) in enumerate(items))
        return f'<div class="salist warnp">{cards}</div>', n
    if typ == "verdict":
        # escbase verdict-stamp: card chốt glow — items[0]=(câu chốt, phụ đề nhỏ)
        a, b = items[0] if items else ("", "")
        tail = f"<span>{_esc(b)}</span>" if b else ""
        return f'<div class="salist"><div class="verdictc" id="{sid}-b0"><b>{_esc(a)}</b>{tail}</div></div>', 1
    # bullets (mặc định) — thẻ fill-bullet đánh số
    cards = "".join(f'<div class="sacard" id="{sid}-b{j}"><span class="san">{j + 1}</span>'
                    f'<span class="sat">{_esc(a)}</span></div>' for j, (a, b) in enumerate(items))
    return f'<div class="salist">{cards}</div>', n


# CSS các component SHORT (brand-agnostic: chỉ dùng var(--ac*)/--pan/--bd). Cả 2
# renderer nhúng chuỗi này vào _SHORT_HEAD để 1 nơi định nghĩa.
SHORT_COMPONENT_CSS = """
  .sec .salist.tagp,.story .salist.tagp{flex-direction:row;flex-wrap:wrap;gap:16px;align-content:flex-start}
  .sec .tag,.story .tag{font-size:30px;font-weight:700;color:var(--ac1);background:rgba(0,229,255,.08);
    border:1px solid rgba(0,229,255,.4);border-radius:999px;padding:14px 28px;opacity:0}
  .sec .tag:nth-child(3n),.story .tag:nth-child(3n){color:var(--ac2);border-color:rgba(167,139,250,.5);background:rgba(167,139,250,.10)}
  .sec .tag:nth-child(3n+2),.story .tag:nth-child(3n+2){color:var(--ac3);border-color:rgba(57,255,122,.45);background:rgba(57,255,122,.08)}
  .sec .salist.procp,.story .salist.procp{flex-direction:row;flex-wrap:wrap;align-items:center;gap:14px}
  .sec .proc,.story .proc{display:flex;align-items:center;gap:12px;font-size:27px;font-weight:700;color:var(--tx);
    background:var(--pan);border:1px solid var(--bd);border-radius:16px;padding:13px 22px;opacity:0}
  .sec .proc i,.story .proc i{width:40px;height:40px;border-radius:11px;display:flex;align-items:center;justify-content:center;
    font-style:normal;font-weight:900;color:#08121f;background:linear-gradient(135deg,var(--ac1),var(--ac2))}
  .sec .proc:not(:last-child)::after,.story .proc:not(:last-child)::after{content:"→";color:var(--ac1);font-size:30px;margin-left:4px}
  .sec .salist.barlist,.story .salist.barlist{gap:24px}
  .sec .barr,.story .barr{display:flex;align-items:center;gap:18px;opacity:0}
  .sec .barl,.story .barl{flex:0 0 36%;font-size:27px;font-weight:700;color:var(--tx);line-height:1.2}
  .sec .bart,.story .bart{flex:1 1 0;height:28px;border-radius:999px;background:var(--pan);border:1px solid var(--bd);overflow:hidden}
  .sec .bart i,.story .bart i{display:block;height:100%;border-radius:999px;background:linear-gradient(90deg,var(--ac1),var(--ac2))}
  .sec .barv,.story .barv{flex:0 0 auto;font-size:27px;font-weight:800;color:var(--ac1);font-variant-numeric:tabular-nums}
  .sec .quotec,.story .quotec{font-size:46px;font-weight:800;line-height:1.32;color:var(--tx);border-left:8px solid var(--ac1);
    padding:8px 0 8px 34px;opacity:0}
  .sec .quotec span,.story .quotec span{display:block;font-size:28px;font-weight:600;color:var(--mut);margin-top:18px}
  .sec .bignum,.story .bignum{display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;flex:1 1 0;opacity:0}
  .sec .bignum b,.story .bignum b{font-size:188px;font-weight:900;color:var(--ac1);line-height:.9;font-variant-numeric:tabular-nums}
  .sec .bignum span,.story .bignum span{font-size:38px;color:var(--mut);margin-top:24px;max-width:80%}
  /* escbase warning-chips: chip hổ phách cho lưu ý/cạm bẫy */
  .sec .salist.warnp,.story .salist.warnp{flex-direction:row;flex-wrap:wrap;gap:16px;align-content:flex-start}
  .sec .warnc,.story .warnc{font-size:29px;font-weight:700;color:#FFC857;background:rgba(255,200,87,.10);
    border:1px solid rgba(255,200,87,.45);border-radius:999px;padding:14px 26px;opacity:0}
  /* escbase verdict-stamp: card chốt glow xanh (match cả outro .cover) */
  .sec .verdictc,.story .verdictc,.cover .verdictc{align-self:center;text-align:center;padding:34px 54px;border-radius:24px;opacity:0;
    background:rgba(0,230,118,.08);border:1.5px solid rgba(0,230,118,.55);box-shadow:0 0 46px rgba(0,230,118,.22)}
  .cover .verdictc{display:inline-block;margin-left:auto;margin-right:auto}
  .sec .verdictc b,.story .verdictc b,.cover .verdictc b{display:block;font-size:58px;font-weight:900;line-height:1.15;
    background:linear-gradient(90deg,#7CFFB2,var(--ac1));-webkit-background-clip:text;background-clip:text;color:transparent}
  .sec .verdictc span,.story .verdictc span,.cover .verdictc span{display:block;font-size:27px;color:var(--mut);margin-top:14px}
  .cap .c .kw.hl{font-weight:800}
  /* escbase hook-orb-badge: avatar repo trong orb glow + badge vàng nổi (cover) */
  .cover .hookwrap{position:relative;width:300px;height:300px;margin:0 auto 44px;opacity:0}
  .cover .hookring{position:absolute;inset:-26px;border-radius:50%;border:1.5px solid rgba(0,229,255,.35);
    box-shadow:0 0 60px rgba(0,229,255,.25), inset 0 0 40px rgba(0,229,255,.08)}
  .cover .hookorb{position:absolute;inset:0;border-radius:50%;overflow:hidden;background:#0d1420;
    border:2px solid rgba(255,255,255,.14);box-shadow:0 18px 60px rgba(0,0,0,.6)}
  .cover .hookorb img{width:100%;height:100%;object-fit:cover}
  .cover .hookbadge{position:absolute;top:-30px;right:-56px;width:150px;height:150px;border-radius:50%;
    display:flex;flex-direction:column;align-items:center;justify-content:center;transform:rotate(8deg);opacity:0;
    background:linear-gradient(135deg,#FFC857,#E8A200);color:#1a1204;box-shadow:0 12px 40px rgba(255,200,87,.35)}
  .cover .hookbadge b{font-size:46px;font-weight:900;line-height:1}
  .cover .hookbadge span{font-size:20px;font-weight:800;letter-spacing:.06em;margin-top:6px}
"""


SLIDE = """<!doctype html>
<html lang="vi" data-resolution="landscape">
<head><meta charset="UTF-8"/>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>
  html,body{{margin:0;width:1920px;height:1080px;overflow:hidden;font-family:__FONT__}}
  #master-root{{width:1920px;height:1080px;position:relative;
    background:radial-gradient(1200px 700px at 75% 15%,#1b2a4a 0%,#0b1320 60%,#070b14 100%);color:#eef3fb}}
  .brand{{position:absolute;top:54px;left:90px;display:flex;align-items:center;gap:16px}}
  .brand .dot{{width:42px;height:42px;border-radius:10px;background:linear-gradient(135deg,#38bdf8,#2563eb)}}
  .brand .n{{font-size:28px;font-weight:700}} .brand .n span{{color:#38bdf8}}
  .date{{position:absolute;top:62px;right:90px;color:#8aa0c0;font-size:24px}}
  .hot{{position:absolute;top:200px;left:120px;font-size:30px;font-weight:700;color:#fb923c;opacity:0}}
  .t{{position:absolute;top:260px;left:120px;right:120px;font-size:74px;font-weight:800;line-height:1.1;opacity:0}}
  .s{{position:absolute;top:560px;left:120px;right:120px;font-size:46px;line-height:1.4;color:#cbd6ea;opacity:0}}
  #prog{{position:absolute;bottom:0;left:0;height:8px;width:0%;background:linear-gradient(90deg,#38bdf8,#2563eb)}}
</style></head>
<body>
<div id="master-root" data-composition-id="master" data-width="1920" data-height="1080" data-start="0" data-duration="{dur}">
  <div class="brand"><span class="mark"><svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#00f0ff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 5h12v14H6a2 2 0 0 1-2-2z"/><path d="M16 8h2.5a1.5 1.5 0 0 1 1.5 1.5V17a2 2 0 0 1-2 2"/><path d="M7 9h6M7 12.5h6M7 16h4"/></svg></span><div class="n">{ba} <span>{bb}</span></div></div>
  <div class="date">{date}</div>
  <div class="hot">🔥 TIN NÓNG NHẤT HÔM NAY</div>
  <h1 class="t">{title}</h1>
  <p class="s">{summary}</p>
  <div id="prog"></div>
  <script>
    window.__timelines=window.__timelines||{{}};
    var m=gsap.timeline({{paused:true}});
    m.to(".hot",{{opacity:1,duration:0.4}},0.2);
    m.fromTo(".t",{{opacity:0,y:40}},{{opacity:1,y:0,duration:0.7,ease:"power2.out"}},0.5);
    m.fromTo(".s",{{opacity:0,y:30}},{{opacity:1,y:0,duration:0.7,ease:"power2.out"}},1.1);
    m.fromTo("#prog",{{width:"0%"}},{{width:"100%",duration:{dur},ease:"none"}},0);
    window.__timelines["master"]=m;
  </script>
</div>
</body></html>
"""


def make(item, out_path, date, model=None, prompt=None, brand=None):
    title = item.get("title") or item.get("summary", "")[:80]
    summary = item.get("summary", "")
    brand = resolve_brand(brand)
    model = model or engine.load()
    sr = model.sampling_rate

    # 1) lồng tiếng trước, để thời lượng slide khớp lời dẫn
    narration = _tts_normalize(summary or title)
    audio, _sr = engine.synth(narration, prompt=prompt, language="Vietnamese", model=model)
    audio = np.asarray(audio, dtype=np.float32)
    dur = max(6.0, round(len(audio) / sr + 1.0, 1))

    proj = _proj()
    render.write_index(proj, SLIDE.format(dur=dur, date=_esc(date), title=_esc(title),
                                          summary=_esc(summary), ba=_esc(brand["a"]),
                                          bb=_esc(brand["b"])))
    silent = os.path.join(proj, "_silent.mp4")
    render.render_project(proj, silent, timeout=420, label="tin")

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    tmp_wav = out_path + ".__voice.wav"
    sf.write(tmp_wav, audio, sr)
    try:
        av.mux(silent, tmp_wav, out_path, mode="fit")
    finally:
        for p in (tmp_wav, silent):
            try:
                os.remove(p)
            except OSError:
                pass
    return out_path


# ====================== WEEKLY RECAP (multi-segment) ==========================

_SENT_RE = re.compile(r"(?<=[.!?…])\s+")

_ASR_MODEL = None
_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) news-video/1.0"


def _asr_words(audio, sr, lang="vi"):
    """faster-whisper word timestamps cho 1 đoạn audio (np float32 mono đọc bằng TTS).
    Trả [(word, start, end)] giây (tương đối đầu audio). Lỗi/không có -> [] (caller tự fallback)."""
    global _ASR_MODEL
    import tempfile
    tmp = None
    try:
        if _ASR_MODEL is None:
            from faster_whisper import WhisperModel
            _ASR_MODEL = WhisperModel("small", device="cpu", compute_type="int8")
        fd, tmp = tempfile.mkstemp(suffix=".wav")
        os.close(fd)
        sf.write(tmp, audio, sr)
        segs, _ = _ASR_MODEL.transcribe(tmp, language=lang, beam_size=5, word_timestamps=True)
        out = []
        for s in segs:
            for w in (s.words or []):
                wt = (w.word or "").strip()
                if wt:
                    out.append((wt, float(w.start), float(w.end)))
        return out
    except Exception as exc:
        print(f"  [asr] word-caption skip: {type(exc).__name__}: {exc}")
        return []
    finally:
        if tmp and os.path.isfile(tmp):
            try:
                os.remove(tmp)
            except OSError:
                pass


def _words_from_text(audio, sr, spoken):
    """Từ hiển thị trên video = CHỮ GỐC do AI soạn; mốc thời gian mượn của ASR.

    VÌ SAO (30/08/2026): karaoke cũ hiển thị THẲNG chữ Whisper phiên âm lại chính đoạn
    audio vừa tổng hợp — tức là dịch ngược cái mình vừa đọc ra, rồi nung bản dịch ngược
    đó vào video. Whisper `small` sai chính tả cả tiếng Việt lẫn thuật ngữ tiếng Anh,
    trong khi TEXT ĐÚNG đang nằm sẵn ngay đây. Đây là thứ người xem NHÌN THẤY mỗi ngày.

    Chia vai đúng sở trường: ASR canh GIỜ tốt (nó nghe chính audio này), nhưng viết CHỮ
    tệ. Nên lấy mốc thời gian của ASR rồi khớp về từ gốc bằng difflib. Từ gốc nào ASR
    nghe sót thì nội suy giờ từ hai từ liền kề.

    ASR hỏng/trống -> chia đều theo độ dài ký tự: kém chuẩn về giờ nhưng CHỮ VẪN ĐÚNG,
    mà chữ đúng mới là thứ đang phải sửa.
    """
    src = (spoken or "").split()
    if not src:
        return []
    dur = len(audio) / sr if sr else 0.0

    def _even():
        tot = sum(len(w) for w in src) or 1
        out, t = [], 0.0
        for w in src:
            d = dur * len(w) / tot
            out.append((w, round(t, 3), round(t + d, 3)))
            t += d
        return out

    asr = _asr_words(audio, sr)
    if not asr:
        return _even()

    def _n(w):
        return re.sub(r"[^\w]", "", w.strip().lower(), flags=re.UNICODE)

    sm = difflib.SequenceMatcher(a=[_n(w) for w in src],
                                 b=[_n(w[0]) for w in asr], autojunk=False)
    times = [None] * len(src)
    for i, j, n in sm.get_matching_blocks():
        for k in range(n):
            times[i + k] = (asr[j + k][1], asr[j + k][2])
    if not any(times):
        return _even()

    # nội suy các từ ASR nghe sót, kẹp giữa hai mốc đã biết
    known = [i for i, t in enumerate(times) if t]
    for a_i, b_i in zip([None] + known, known + [None]):
        if a_i is None or b_i is None or b_i - a_i <= 1:
            continue
        t0, t1 = times[a_i][1], times[b_i][0]
        span = max(t1 - t0, 0.0)
        seg = src[a_i + 1:b_i]
        tot = sum(len(w) for w in seg) or 1
        t = t0
        for gi, w in enumerate(seg, start=a_i + 1):
            d = span * len(w) / tot
            times[gi] = (t, t + d)
            t += d
    first, last = known[0], known[-1]
    for i in range(first - 1, -1, -1):                 # từ trước mốc khớp đầu tiên
        times[i] = (max(0.0, times[i + 1][0] - 0.25), times[i + 1][0])
    for i in range(last + 1, len(src)):                # từ sau mốc khớp cuối cùng
        times[i] = (times[i - 1][1], min(dur, times[i - 1][1] + 0.25))
    return [(w, round(t[0], 3), round(t[1], 3)) for w, t in zip(src, times)]


def _filler_dir():
    """Ảnh filler on-brand: `<trạm>/projects/news/assets/fillers` (bản cũ nằm trong engine giọng)."""
    return projects.filler_dir(PROJECT)


def _local_filler(idx, brand_key=""):
    """Ảnh FILLER ON-BRAND người dùng tự chuẩn bị (ưu tiên hơn b-roll Openverse: chất lượng
    cao hơn và đúng thương hiệu). Pool con theo brand: `fillers/<brand_key>/` nếu có, không thì
    `fillers/` chung. Xoay vòng theo idx. Trả đường tuyệt đối, hoặc None khi pool rỗng."""
    base = _filler_dir()
    for d in ([os.path.join(base, brand_key)] if brand_key else []) + [base]:
        try:
            pool = sorted(f for f in os.listdir(d)
                          if f.lower().endswith((".jpg", ".jpeg", ".png", ".webp")))
        except OSError:
            continue
        if pool:
            return os.path.join(d, pool[(idx - 1) % len(pool)])
    return None


_OPENVERSE = "https://api.openverse.org/v1/images/"


def _broll_image(query, out_path, min_bytes=9000):
    """Tải 1 ảnh CC (commercial) từ Openverse theo keyword làm B-ROLL lấp khung khi section
    thiếu ảnh (port ý tưởng material.py của MoneyPrinterTurbo, nguồn keyless). Best-effort:
    lỗi mạng KHÔNG chặn render -> trả None."""
    try:
        url = _OPENVERSE + "?" + urllib.parse.urlencode(
            {"q": query, "page_size": 8, "license_type": "commercial", "mature": "false"})
        req = urllib.request.Request(url, headers={"User-Agent": _UA})
        with urllib.request.urlopen(req, timeout=25) as r:
            data = json.load(r)
    except Exception as exc:
        print(f"  [broll] Openverse lỗi '{query}': {type(exc).__name__}")
        return None
    for item in data.get("results", []):
        src = item.get("url") or ""
        if not src.lower().split("?")[0].endswith((".jpg", ".jpeg", ".png", ".webp")):
            continue
        try:
            if int(item.get("width") or 0) and int(item["width"]) < 700:
                continue   # bỏ ảnh nhỏ/thumbnail (lấp khung sẽ vỡ)
        except (TypeError, ValueError):
            pass
        try:
            req = urllib.request.Request(src, headers={"User-Agent": _UA})
            with urllib.request.urlopen(req, timeout=35) as r:
                blob = r.read()
            if len(blob) < min_bytes:
                continue
            with open(out_path, "wb") as f:
                f.write(blob)
            print(f"  [broll] OK '{query}' -> {item.get('creator', '?')}")
            return out_path
        except Exception:
            continue
    print(f"  [broll] không tải được ảnh cho '{query}'")
    return None


def _caps_events(words, spoken, t, dur):
    """[(start_abs, text)] cho phụ đề short: ưu tiên ASR word-level gom ~7 từ/dòng (mốc theo từ),
    fallback tách câu canh tuyến tính theo độ dài."""
    out = []
    if words:
        line, lstart = [], None
        for w, ws, _we in words:
            if lstart is None:
                lstart = ws
            line.append(w)
            if len(line) >= 7 or w.rstrip().endswith((".", "!", "?", "…", ",", ":", ";")):
                out.append((t + lstart, " ".join(line)))
                line, lstart = [], None
        if line:
            out.append((t + lstart, " ".join(line)))
    else:
        sents = [s.strip() for s in _SENT_RE.split((spoken or "").strip()) if s.strip()]
        if sents:
            span = max(0.6, dur - 0.5)
            tot = sum(len(s) for s in sents) or 1
            acc = 0.25
            for s in sents:
                out.append((t + acc, s))
                acc += span * (len(s) / tot)
    return out


def _karaoke_caps(words, spoken, t, dur, kcaps_html, anim, cidp):
    """Phụ đề KARAOKE (escbase): ASR word-level → dòng ~5 từ, mỗi từ TỐI→TRẮNG đúng mốc đọc.
    Append HTML vào kcaps_html + tween vào anim. Không ASR → fallback cả-dòng fade tuyến tính."""
    if words:
        lines, cur = [], []
        for w in words:
            cur.append(w)
            if len(cur) >= 5 or w[0].rstrip().endswith((".", "!", "?", "…", ",", ";", ":")):
                lines.append(cur)
                cur = []
        if cur:
            lines.append(cur)
        for li, line in enumerate(lines):
            cid = f"{cidp}l{li}"
            ls, le = t + line[0][1], t + line[-1][2]
            spans = "".join(
                f'<span id="{cid}w{wi}" class="kw{" hl" if hl_word(w[0]) else ""}">{_esc(w[0])}</span> '
                for wi, w in enumerate(line))
            kcaps_html.append(f'<div class="c" id="{cid}">{spans}</div>')
            anim.append(f'    m.to("#{cid}",{{opacity:1,duration:0.14}},{ls:.2f});')
            anim.append(f'    m.to("#{cid}",{{opacity:0,duration:0.14}},{max(ls + 0.3, le + 0.06):.2f});')
            for wi, w in enumerate(line):
                # escbase: từ số liệu/thuật ngữ tô VÀNG, từ thường tô trắng
                col = "#FFC857" if hl_word(w[0]) else "#ffffff"
                anim.append(f'    m.to("#{cid}w{wi}",{{color:"{col}",duration:0.08}},{t + w[1]:.2f});')
        return
    sents = [s.strip() for s in _SENT_RE.split((spoken or "").strip()) if s.strip()]
    span = max(0.6, dur - 0.5)
    tot = sum(len(s) for s in sents) or 1
    acc = 0.25
    for ci, s in enumerate(sents):
        cid = f"{cidp}c{ci}"
        cs = t + acc
        acc += span * (len(s) / tot)
        kcaps_html.append(f'<div class="c" id="{cid}">{_esc(s)}</div>')
        anim.append(f'    m.to("#{cid}",{{opacity:1,duration:0.18}},{cs:.2f});')
        anim.append(f'    m.to("#{cid}",{{opacity:0,duration:0.18}},{max(cs + 0.3, t + acc - 0.1):.2f});')


def _seg_bullets(seg, n=3, max_len=92):
    """Slide bullets for a segment: sidecar 'bullets' if present, else the first
    n narration sentences trimmed at a word boundary."""
    bullets = [b.strip() for b in (seg.get("bullets") or []) if b and b.strip()]
    if not bullets:
        for s in _SENT_RE.split((seg.get("narration") or "").strip()):
            s = s.strip().rstrip(".")
            if not s:
                continue
            if len(s) > max_len:
                s = s[:max_len].rsplit(" ", 1)[0] + "…"
            bullets.append(s)
    return bullets[:n]


_W_TUAN = re.compile(r"\btu[ầa]n\s+[Ww](\d{1,2})\b")
_W_BARE = re.compile(r"\b[Ww](\d{1,2})\b")


def _tts_normalize(text):
    """Sửa những từ engine giọng đọc sai trước khi TTS (chữ hiển thị giữ nguyên).

    'W24'/'tuần W24' -> 'tuần 24'; phần còn lại theo bảng `brand.pronounce` của spec — tên
    miền, tên riêng, từ viết tắt của mỗi thương hiệu một khác, engine không đoán hộ.
    """
    text = _W_TUAN.sub(r"tuần \1", text or "")
    text = _W_BARE.sub(r"tuần \1", text)
    for pat, rep in PRONOUNCE.items():
        text = pat.sub(rep, text)
    return text


def _synth_long(model, text, prompt, max_chunk=240):
    """Synthesize long narration in sentence chunks (OmniVoice quality drops on
    very long inputs), concatenated with short pauses."""
    sr = model.sampling_rate
    text = _tts_normalize((text or "").strip())
    if not text:
        return np.zeros(int(sr * 0.2), dtype=np.float32)
    # GIỌNG = profile CLONE, KHÔNG bao giờ rơi về instruct= (mỗi câu một người nói khác).
    # Caller quên truyền prompt thì tự lấy clone prompt của profile mặc định.
    if prompt is None:
        prompt = profiles.get_clone_prompt(model)
        if prompt is None:
            print("[news_video][WARN] không tìm thấy voice profile — KHÔNG render bằng giọng "
                  "synthetic. Tạo một profile giọng trước (voice-studio), rồi khai tên nó ở "
                  "voice.profile trong spec.", flush=True)
    chunks, cur = [], ""
    for s in _SENT_RE.split(text):
        if cur and len(cur) + len(s) + 1 > max_chunk:
            chunks.append(cur)
            cur = s
        else:
            cur = (cur + " " + s).strip()
    if cur:
        chunks.append(cur)
    gap = np.zeros(int(sr * 0.18), dtype=np.float32)
    parts = []
    for c in chunks:
        a, _sr = engine.synth(c, prompt=prompt, language="Vietnamese", model=model)
        parts.append(np.asarray(a, dtype=np.float32))
        parts.append(gap)
    out = np.concatenate(parts) if parts else np.zeros(int(sr * 0.2), dtype=np.float32)
    return engine.normalize(out)


def _download_images(urls, dest_dir, seg_idx, max_n=3):
    """Best-effort download of segment images. Returns project-relative paths."""
    os.makedirs(dest_dir, exist_ok=True)
    out = []
    for j, u in enumerate((urls or [])[:max_n]):
        try:
            req = urllib.request.Request(u, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "Accept": "image/*,*/*;q=0.8"})
            with urllib.request.urlopen(req, timeout=20) as r:
                ct = (r.headers.get("Content-Type") or "").lower()
                data = r.read(12_000_000)
            if len(data) < 4000:
                continue
            if "image" not in ct and not re.search(r"\.(jpe?g|png|webp|gif)([?#]|$)", u, re.I):
                continue
            ext = ".jpg"
            for k, v in (("png", ".png"), ("webp", ".webp"), ("gif", ".gif"), ("jpeg", ".jpg")):
                if k in ct:
                    ext = v
                    break
            fp = os.path.join(dest_dir, f"s{seg_idx}_{j}{ext}")
            with open(fp, "wb") as f:
                f.write(data)
            out.append(f"img/{os.path.basename(fp)}")
            print(f"    image s{seg_idx}_{j} ok ({len(data)//1024} KB)")
        except Exception as exc:
            print(f"    [warn] image {seg_idx}/{j} failed: {type(exc).__name__}")
    return out


# ---- SmartArt/infographic cho recap tuần (port từ top_story_video.py) ----
# Dùng CSS var (--ac1.. / --pan / --bd / --tx / --mut) — định nghĩa trong :root của template.
_WK_DIAG_CSS = """
  .imgs .diag{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;
    padding:34px;box-sizing:border-box;background:#0a1122}
  .dtitle{font-size:30px;font-weight:800;color:var(--mut);margin:0 0 26px;text-align:center}
  .dflow{display:flex;flex-direction:column;align-items:center;width:100%}
  .dstep{width:92%;background:var(--pan);border:1px solid var(--bd);border-left:4px solid var(--ac1);
    border-radius:16px;padding:16px 22px;font-size:27px;font-weight:700;text-align:left;color:var(--tx);opacity:0}
  .dstep .dd{display:block;font-size:20px;font-weight:400;color:var(--mut);margin-top:4px}
  .darr{font-size:24px;color:var(--ac1);line-height:1.15;margin:5px 0}
  .dvs{display:flex;align-items:stretch;gap:18px;width:100%}
  .dvsb{align-self:center;font-size:28px;font-weight:900;color:var(--ac4)}
  .dcol{flex:1;border-radius:18px;padding:20px 22px;opacity:0;background:var(--pan);border:1px solid var(--bd)}
  .dcol.dl{border-top:3px solid var(--ac1)}.dcol.dr{border-top:3px solid var(--ac2)}
  .dcol h4{margin:0 0 12px;font-size:27px;color:var(--tx)}
  .dcol ul{margin:0;padding-left:22px;font-size:23px;line-height:1.5;color:var(--mut)}
  .dstack{display:flex;flex-direction:column-reverse;gap:13px;width:90%}
  .dlayer{border-radius:14px;padding:15px 20px;font-size:25px;font-weight:700;text-align:center;color:var(--tx);
    background:var(--pan);border:1px solid var(--bd);border-left:4px solid var(--ac1);opacity:0}
  .dlayer:nth-child(2n){border-left-color:var(--ac2)}
  .dlayer .dd{display:block;font-size:19px;font-weight:400;color:var(--mut)}
  .dstats{display:grid;grid-template-columns:repeat(2,1fr);gap:20px;width:94%}
  .dstat{border:1px solid var(--bd);border-radius:18px;padding:22px 16px;text-align:center;background:var(--pan);opacity:0}
  .dstat b{display:block;font-size:52px;font-weight:900;color:var(--ac1);font-variant-numeric:tabular-nums}
  .dstat span{font-size:21px;color:var(--mut)}
"""


def _wk_it(x):
    if isinstance(x, dict):
        return x.get("t") or x.get("v") or "", x.get("d") or x.get("l") or ""
    return str(x), ""


def _wk_diag_children(diag):
    return 2 if (diag or {}).get("type") == "versus" else len(diag.get("items") or [])


def _wk_diagram_html(diag, did):
    """Inline SmartArt cho panel phải của 1 segment recap. Con có id {did}-sN để stagger."""
    typ = (diag or {}).get("type", "flow")
    head = f'<div class="dtitle">{_esc(diag.get("title", ""))}</div>' if diag.get("title") else ""
    if typ == "versus":
        cols = []
        for k, cls in (("left", "dl"), ("right", "dr")):
            c = diag.get(k) or {}
            lis = "".join(f"<li>{_esc(_wk_it(i)[0])}</li>" for i in (c.get("items") or []))
            cols.append(f'<div class="dcol {cls}" id="{did}-s{len(cols)}"><h4>{_esc(c.get("h",""))}</h4><ul>{lis}</ul></div>')
        body = f'<div class="dvs">{cols[0]}<div class="dvsb">VS</div>{cols[1]}</div>'
    elif typ == "stack":
        items = list(diag.get("items") or [])
        rows = []
        for j, x in enumerate(reversed(items)):
            t, d = _wk_it(x)
            sub = f'<span class="dd">{_esc(d)}</span>' if d else ""
            rows.append(f'<div class="dlayer" id="{did}-s{j}">{_esc(t)}{sub}</div>')
        body = f'<div class="dstack">{"".join(rows)}</div>'
    elif typ == "stats":
        cards = []
        for j, x in enumerate(diag.get("items") or []):
            v, l = _wk_it(x)
            cards.append(f'<div class="dstat" id="{did}-s{j}"><b>{_esc(v)}</b><span>{_esc(l)}</span></div>')
        body = f'<div class="dstats">{"".join(cards)}</div>'
    else:  # flow
        items = list(diag.get("items") or [])
        steps = []
        for j, x in enumerate(items):
            t, d = _wk_it(x)
            sub = f'<span class="dd">{_esc(d)}</span>' if d else ""
            steps.append(f'<div class="dstep" id="{did}-s{j}">{_esc(t)}{sub}</div>')
            if j < len(items) - 1:
                steps.append('<div class="darr">▼</div>')
        body = f'<div class="dflow">{"".join(steps)}</div>'
    return f'{head}{body}'


_WEEKLY_HEAD = """<!doctype html>
<html lang="vi" data-resolution="landscape">
<head><meta charset="UTF-8"/>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>
  :root{--ac1:#00f0ff;--ac2:#bd00ff;--ac3:#39ff7a;--ac4:#ffd166;
        --tx:#eef3fb;--mut:#9db2d4;--bd:rgba(255,255,255,.14);--pan:#0e1730}
  html,body{margin:0;width:1920px;height:1080px;overflow:hidden;font-family:__FONT__}
  #master-root{width:1920px;height:1080px;position:relative;color:#eef3fb;
    background:radial-gradient(1300px 760px at 75% 12%,#101a33 0%,#070d1c 55%,#04060a 100%)}
  #master-root::before{content:"";position:absolute;inset:0;opacity:.5;pointer-events:none;
    background-image:linear-gradient(rgba(255,255,255,.05) 1px,transparent 1px),
      linear-gradient(90deg,rgba(255,255,255,.05) 1px,transparent 1px);background-size:90px 90px}
  .brand{position:absolute;top:54px;left:90px;display:flex;align-items:center;gap:16px;z-index:5}
  .brand .mark{width:50px;height:50px;border-radius:50%;display:grid;place-items:center;
    border:2px solid rgba(0,240,255,.5);
    background:radial-gradient(circle,rgba(0,240,255,.22),rgba(189,0,255,.08) 55%,rgba(4,6,10,.95) 78%);
    box-shadow:0 0 20px rgba(0,240,255,.4)}
  .brand .n{font-size:30px;font-weight:800}.brand .n span{color:#00f0ff}
  .epi{position:absolute;top:60px;right:90px;color:#8aa0c0;font-size:26px;z-index:5}
  .seg{position:absolute;inset:0;opacity:0}
  .cover{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center}
  .cover .big{font-size:192px;font-weight:800;letter-spacing:-1px;line-height:1.02}
  .cover .big span{color:#00f0ff}
  .cover .sub{font-size:52px;color:#9db2d4;margin-top:30px}
  .cover .sub2{font-size:64px;color:#8aa6cc;font-weight:600;margin-top:24px}
  .story .txt{position:absolute;left:90px;top:200px;width:860px;z-index:4}
  .story .rank{display:inline-block;font-size:30px;font-weight:800;color:#04060a;background:linear-gradient(90deg,#00f0ff,#39ff7a);
    border-radius:10px;padding:6px 22px;margin-bottom:28px}
  .story .hl{font-size:62px;font-weight:800;line-height:1.16}
  .story .bul{margin:36px 0 0;padding:0;list-style:none;font-size:31px;line-height:1.45;color:#c3d0e4}
  .story .bul li{position:relative;margin-top:18px;padding-left:36px;opacity:0}
  .story .bul li::before{content:"▸";position:absolute;left:0;color:#00f0ff}
  .story .imgs{position:absolute;right:90px;top:200px;width:840px;height:680px;border-radius:24px;overflow:hidden;
    box-shadow:0 30px 80px rgba(0,0,0,.55);background:#0a1122}
  .story .imgs img{position:absolute;inset:0;width:100%;height:100%;object-fit:contain;opacity:0}
  .story.noimg .txt{left:50%;transform:translateX(-50%);text-align:center;top:330px;width:1400px}
  .wave{position:absolute;left:90px;bottom:120px;display:flex;gap:10px;z-index:4}
  .wave i{width:10px;border-radius:6px;background:#00f0ff;opacity:.85;animation:eq 1.1s ease-in-out infinite}
  .wave i:nth-child(2n){animation-delay:.2s;background:#bd00ff}.wave i:nth-child(3n){animation-delay:.45s}
  @keyframes eq{0%,100%{height:18px}50%{height:64px}}
  #prog{position:absolute;bottom:0;left:0;height:10px;width:0%;background:linear-gradient(90deg,#00f0ff,#bd00ff);z-index:9}
""" + _WK_DIAG_CSS + """
</style></head>
<body>
<div id="master-root" data-composition-id="master" data-width="1920" data-height="1080" data-start="0" data-duration="{TOTAL}">
  <div class="brand"><span class="mark"><svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#00f0ff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 5h12v14H6a2 2 0 0 1-2-2z"/><path d="M16 8h2.5a1.5 1.5 0 0 1 1.5 1.5V17a2 2 0 0 1-2 2"/><path d="M7 9h6M7 12.5h6M7 16h4"/></svg></span><div class="n">{BA} <span>{BB}</span></div></div>
  <div class="epi">{EPI}</div>
  <div class="wave">{WAVE}</div>
  {SEGS}
  <div id="prog"></div>
  <script>
    window.__timelines=window.__timelines||{};
    var m=gsap.timeline({paused:true});
    m.fromTo("#prog",{width:"0%"},{width:"100%",duration:{TOTAL},ease:"none"},0);
{ANIM}
    window.__timelines["master"]=m;
  </script>
</div>
</body></html>
"""


def make_weekly(video_obj, out_path, date, week="", range_="", model=None, prompt=None, brand=None):
    """Render the 5-7 minute weekly recap video. Returns out_path."""
    model = model or engine.load()
    sr = model.sampling_rate
    brand = resolve_brand(brand)
    segments = (video_obj or {}).get("segments") or []
    if not segments:
        raise ValueError("weekly_video.segments is empty")

    proj = _proj()
    img_dir = os.path.join(proj, "img")
    if os.path.isdir(img_dir):
        shutil.rmtree(img_dir, ignore_errors=True)

    intro_txt = (video_obj.get("intro") or
                 f"{brand['welcome']}, bản tin tuần {week}.")
    outro_txt = (video_obj.get("outro") or
                 "Cảm ơn bạn đã theo dõi. Hẹn gặp lại trong bản tin tuần sau.")

    # 1) narration first (slide timings follow the audio)
    print("  [video] synthesizing narration ...")
    pad = 0.8  # visual + audio pad per block, keeps A/V aligned
    blocks = []  # (kind, seg_or_none, audio, dur)
    a = _synth_long(model, intro_txt, prompt)
    blocks.append(("intro", None, a, len(a) / sr + pad))
    for i, seg in enumerate(segments, 1):
        a = _synth_long(model, seg.get("narration") or seg.get("headline", ""), prompt)
        blocks.append(("story", seg, a, len(a) / sr + pad))
        print(f"  [video] narration segment {i} ok ({len(a)/sr:.0f}s)")
    a = _synth_long(model, outro_txt, prompt)
    blocks.append(("outro", None, a, len(a) / sr + pad))
    total = round(sum(b[3] for b in blocks), 2)
    print(f"  [video] total duration ~{total:.0f}s")

    # chapters sidecar (exact segment start times) -> YouTube description
    chapters, tcur = [], 0.0
    for kind, seg, _a2, dur in blocks:
        if kind == "intro":
            chapters.append({"t": 0, "label": "Mở đầu"})
        elif kind == "outro":
            chapters.append({"t": round(tcur), "label": "Kết — đọc bản tin đầy đủ"})
        else:
            n = len(chapters)  # 1-based TOP number = n (intro already added)
            chapters.append({"t": round(tcur),
                             "label": f"TOP {n} – {seg.get('headline', '')}"})
        tcur += dur
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path + ".chapters.json", "w", encoding="utf-8") as f:
        json.dump(chapters, f, ensure_ascii=False, indent=1)

    # 2) images per story segment
    seg_imgs = {}
    for i, seg in enumerate(segments, 1):
        seg_imgs[i] = _download_images(seg.get("images"), img_dir, i)

    # 3) build the single-composition slide HTML with absolute-time animations
    segs_html, anim = [], []
    t = 0.0
    story_i = 0
    for kind, seg, _a, dur in blocks:
        if kind == "intro":
            sid = "seg-intro"
            _cp = brand.get("cover_period") or (f"Tuần {_esc(week)}" if week else "")
            _cp_sfx = f" · {_cp}" if _cp else ""
            inner = (f'<div class="cover"><div class="big">{_esc(brand["a"])} <span>{_esc(brand["b"])}</span></div>'
                     f'<div class="sub">{_esc(brand["tagline"])}{_cp_sfx}</div>'
                     f'<div class="sub2">{_esc(range_)}</div></div>')
            segs_html.append(f'<section class="seg" id="{sid}">{inner}</section>')
        elif kind == "outro":
            sid = "seg-outro"
            inner = (f'<div class="cover"><div class="big">{brand.get("outro_big", "Hẹn gặp tuần sau!")}</div>'
                     f'<div class="sub">{brand.get("outro_sub", "Đọc bản tin đầy đủ kèm audio tại")}</div>'
                     f'<div class="sub2">{_esc(brand["site"])}</div></div>')
            segs_html.append(f'<section class="seg" id="{sid}">{inner}</section>')
        else:
            story_i += 1
            sid = f"seg-{story_i}"
            diag = seg.get("diagram")
            imgs = (seg_imgs.get(story_i) or [])[:1]  # tối đa 1 ảnh hero (hiện ĐẦY ĐỦ, không crop)
            cls = "seg story" if (diag or imgs) else "seg story noimg"
            pitems = []
            for j, p in enumerate(imgs):
                pitems.append(f'<img id="{sid}-im{j}" src="{_esc(p)}">')
            did = f"{sid}-d"
            if diag:
                pitems.append(f'<div class="diag" id="{did}" style="opacity:0">{_wk_diagram_html(diag, did)}</div>')
            panel_div = f'<div class="imgs">{"".join(pitems)}</div>' if pitems else ""
            bullets = _seg_bullets(seg, n=2 if diag else 3)
            bul_html = "".join(
                f'<li id="{sid}-b{j}">{_esc(b)}</li>' for j, b in enumerate(bullets))
            bul_div = f'<ul class="bul">{bul_html}</ul>' if bullets else ""
            inner = (f'<div class="txt"><span class="rank">TOP {story_i} {brand.get("rank_suffix", "TUẦN NÀY")}</span>'
                     f'<div class="hl">{_esc(seg.get("headline") or "")}</div>{bul_div}</div>{panel_div}')
            segs_html.append(f'<section class="{cls}" id="{sid}">{inner}</section>')
            for j in range(len(bullets)):
                anim.append(f'    m.to("#{sid}-b{j}",{{opacity:1,duration:0.45}},{t + 1.0 + j * 0.4:.2f});')
            # panel: ảnh hero hiện trước (nếu có), rồi SmartArt chiếm panel phần còn lại
            n_img = len(imgs)
            img_end = (t + 0.3 + (dur - 1.0) * 0.42) if (diag and n_img) else (t + dur - 0.3)
            for j in range(n_img):
                st = t + 0.3
                anim.append(f'    m.to("#{sid}-im{j}",{{opacity:1,duration:0.6}},{st:.2f});')
                anim.append(f'    m.fromTo("#{sid}-im{j}",{{scale:1.0}},{{scale:1.06,duration:{max(0.5, img_end - st):.2f},ease:"none"}},{st:.2f});')
                if diag:
                    anim.append(f'    m.to("#{sid}-im{j}",{{opacity:0,duration:0.5}},{img_end:.2f});')
            if diag:
                dstart = (img_end + 0.2) if n_img else (t + 1.0)
                anim.append(f'    m.to("#{did}",{{opacity:1,duration:0.5}},{dstart:.2f});')
                nch = _wk_diag_children(diag)
                span = max(0.4, (t + dur - 0.4 - (dstart + 0.4)) / max(1, nch))
                for c in range(nch):
                    anim.append(f'    m.to("#{did}-s{c}",{{opacity:1,duration:0.45}},{dstart + 0.4 + c * span:.2f});')
        # segment fade in/out on the master timeline
        anim.append(f'    m.to("#{sid}",{{opacity:1,duration:0.45}},{t:.2f});')
        if t + dur < total - 0.1:
            anim.append(f'    m.to("#{sid}",{{opacity:0,duration:0.45}},{t + dur - 0.45:.2f});')
        t += dur

    epi = brand.get("epi") or (f"Tuần {week} · {range_}" if range_ else f"Tuần {week}")
    html = (_WEEKLY_HEAD
            .replace("{TOTAL}", str(total))
            .replace("{EPI}", _esc(epi))
            .replace("{WAVE}", "<i></i>" * 7)
            .replace("{SEGS}", "\n  ".join(segs_html))
            .replace("{ANIM}", "\n".join(anim)))
    html = _brandify(html, brand)
    render.write_index(proj, html)

    # 4) render video câm (timeout dài: ~6 phút khung hình)
    silent = os.path.join(proj, "_silent.mp4")
    print("  [video] rendering slides (HyperFrames) ...")
    render.render_project(proj, silent, timeout=3600, label="recap")

    # 5) assemble the voice track with the same pads, then mux
    parts = []
    for blk in blocks:
        parts.append(blk[2])   # audio (block 4-tuple recap / 6-tuple short)
        parts.append(np.zeros(int(sr * pad), dtype=np.float32))
    voice = np.concatenate(parts)

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    tmp_wav = out_path + ".__voice.wav"
    sf.write(tmp_wav, voice, sr)
    try:
        av.mux(silent, tmp_wav, out_path, mode="fit")
    finally:
        for p in (tmp_wav, silent):
            try:
                os.remove(p)
            except OSError:
                pass
    return out_path


# ====================== WEEKLY SHORT (vertical 9:16) ==========================

_SHORT_HEAD = """<!doctype html>
<html lang="vi" data-resolution="portrait">
<head><meta charset="UTF-8"/>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>
  :root{--ac1:#00f0ff;--ac2:#bd00ff;--ac3:#39ff7a;--pan:#0e1730;
        --bd:rgba(255,255,255,.14);--tx:#eaf2ff;--mut:#9db2d4}
  html,body{margin:0;width:1080px;height:1920px;overflow:hidden;font-family:__FONT__}
  #master-root{width:1080px;height:1920px;position:relative;color:#eef3fb;
    background:radial-gradient(900px 1200px at 50% 8%,#101a33 0%,#070d1c 55%,#04060a 100%)}
  .brand{position:absolute;top:64px;left:64px;display:flex;align-items:center;gap:14px;z-index:5}
  .brand .mark{width:54px;height:54px;border-radius:50%;display:grid;place-items:center;
    border:2px solid rgba(0,240,255,.5);
    background:radial-gradient(circle,rgba(0,240,255,.22),rgba(189,0,255,.08) 55%,rgba(4,6,10,.95) 78%);
    box-shadow:0 0 20px rgba(0,240,255,.4)}
  .brand .n{font-size:34px;font-weight:800}.brand .n span{color:#00f0ff}
  .epi{position:absolute;top:74px;right:64px;color:#8aa0c0;font-size:26px;z-index:5}
  .site{position:absolute;bottom:54px;left:0;right:0;text-align:center;color:#67809f;font-size:28px;z-index:5}
  .seg{position:absolute;inset:0;opacity:0}
  .cover{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:0 70px}
  .cover .big{font-size:108px;font-weight:800;letter-spacing:-2px;line-height:1.05}
  .cover .big span{color:#00f0ff}
  .cover .sub{font-size:44px;color:#9db2d4;margin-top:30px}
  .cover .sub2{font-size:34px;color:#67809f;margin-top:16px}
  .story .rank{position:absolute;top:220px;left:64px;font-size:34px;font-weight:800;color:#04060a;
    background:linear-gradient(90deg,#00f0ff,#39ff7a);border-radius:12px;padding:8px 26px;z-index:4}
  .story .hl{position:absolute;top:308px;left:64px;right:64px;font-size:60px;font-weight:800;line-height:1.16;z-index:4}
  /* SHORT v3: SmartArt fill-bullet (TRÊN) + ẢNH lấp khung (DƯỚI) + caption to */
  .story .content{position:absolute;left:64px;right:64px;top:466px;bottom:416px;display:flex;flex-direction:column;gap:34px;z-index:4}
  .story .salist{display:flex;flex-direction:column;gap:18px;flex:0 0 auto}
  .story .sacard{display:flex;align-items:center;gap:18px;background:#0e1730;border:1px solid rgba(255,255,255,.14);
    border-left:6px solid #00f0ff;border-radius:20px;padding:20px 24px;opacity:0;box-shadow:0 10px 30px rgba(0,0,0,.35)}
  .story .sacard:nth-child(2n){border-left-color:#bd00ff}
  .story .sacard:nth-child(3n){border-left-color:#39ff7a}
  .story .san{flex:0 0 auto;width:56px;height:56px;border-radius:15px;display:flex;align-items:center;justify-content:center;
    font-size:30px;font-weight:900;color:#04060a;background:linear-gradient(135deg,#00f0ff,#bd00ff)}
  .story .sat{font-size:31px;font-weight:700;color:#eef3fb;line-height:1.24}
  .story .statc{display:flex;flex-direction:column;align-items:flex-start;background:#0e1730;border:1px solid rgba(255,255,255,.14);
    border-left:6px solid #39ff7a;border-radius:20px;padding:22px 28px;opacity:0;box-shadow:0 10px 30px rgba(0,0,0,.35)}
  .story .statc b{font-size:62px;font-weight:900;color:#00f0ff;line-height:1;font-variant-numeric:tabular-nums}
  .story .statc span{font-size:27px;color:#9db2d4;margin-top:8px;line-height:1.25}
  .cap .c .kw{color:#76859c}
  .story .heroimg{position:relative;flex:1 1 0;min-height:0;border-radius:26px;overflow:hidden;
    border:1px solid rgba(255,255,255,.14);box-shadow:0 24px 70px rgba(0,0,0,.55);background:#0a1122}
  .story .heroimg img,.story .heroimg video{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;opacity:0}
  .story .content.tpl-b .heroimg{order:1}.story .content.tpl-b .salist{order:2}
  .story .content.tpl-c .heroimg{order:1;flex:1.7 1 0}.story .content.tpl-c .salist{order:2}
  .story.noimg .content{justify-content:center;gap:30px}
  .story.noimg .sacard{padding:30px 28px}.story.noimg .sat{font-size:37px}
  .cap{position:absolute;left:0;right:0;bottom:150px;text-align:center;z-index:8}
  .cap .c{position:absolute;left:50%;transform:translateX(-50%);bottom:0;opacity:0;max-width:960px;
    background:rgba(7,9,15,.78);border:1px solid rgba(255,255,255,.14);border-radius:15px;color:#eaf2ff;
    padding:18px 30px;font-size:40px;line-height:1.3;font-weight:600}
  #prog{position:absolute;top:0;left:0;height:12px;width:0%;background:linear-gradient(90deg,#00f0ff,#bd00ff);z-index:9}
""" + SHORT_COMPONENT_CSS + """
</style></head>
<body>
<div id="master-root" data-composition-id="master" data-width="1080" data-height="1920" data-start="0" data-duration="{TOTAL}">
  <div class="brand"><span class="mark"><svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="#00f0ff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4 5h12v14H6a2 2 0 0 1-2-2z"/><path d="M16 8h2.5a1.5 1.5 0 0 1 1.5 1.5V17a2 2 0 0 1-2 2"/><path d="M7 9h6M7 12.5h6M7 16h4"/></svg></span><div class="n">{BA} <span>{BB}</span></div></div>
  <div class="epi">{EPI}</div>
  <div class="site">{BSITE}</div>
  {SEGS}
  <div class="cap">{CAPS}</div>
  <div id="prog"></div>
  <script>
    window.__timelines=window.__timelines||{};
    var m=gsap.timeline({paused:true});
    m.fromTo("#prog",{width:"0%"},{width:"100%",duration:{TOTAL},ease:"none"},0);
{ANIM}
    window.__timelines["master"]=m;
  </script>
</div>
</body></html>
"""


def make_weekly_short(video_obj, out_path, date, week="", range_="", model=None, prompt=None, brand=None):
    """Render the ~60-90s VERTICAL (1080x1920) weekly summary short: intro +
    one quick slide per TOP-5 story (headline + first narration sentence) +
    closing CTA. Returns out_path."""
    model = model or engine.load()
    sr = model.sampling_rate
    brand = resolve_brand(brand)
    segments = (video_obj or {}).get("segments") or []
    if not segments:
        raise ValueError("weekly_video.segments is empty")

    proj = _proj()
    img_dir = os.path.join(proj, "img")

    intro_txt = (video_obj.get("intro") or
                 f"Đây là tóm tắt nhanh các tin AI nóng nhất tuần {week}.")
    outro_txt = (video_obj.get("outro_short") or
                 f"Xem bản tin đầy đủ kèm video chi tiết tại trang {brand['site']}.")

    pad = 0.6
    blocks = []
    a = _synth_long(model, intro_txt, prompt)
    # chữ karaoke = TEXT GỐC (giờ mượn ASR) — xem _words_from_text
    blocks.append(("intro", None, a, len(a) / sr + pad,
                   _words_from_text(a, sr, intro_txt), intro_txt))
    for i, seg in enumerate(segments, 1):
        first = _SENT_RE.split((seg.get("narration") or "").strip())[0]
        spoken = f"Số {i}. {seg.get('headline', '')}. {first}"
        a = _synth_long(model, spoken, prompt)
        asr_drift_warn(_asr_words(a, sr), spoken, label=f"weekly short TOP {i}")  # lưới an toàn
        _w = _words_from_text(a, sr, spoken)
        blocks.append(("story", seg, a, len(a) / sr + pad, _w, spoken))
        print(f"  [short] narration {i} ok ({len(a)/sr:.0f}s)")
    a = _synth_long(model, outro_txt, prompt)
    blocks.append(("outro", None, a, len(a) / sr + pad,
                   _words_from_text(a, sr, outro_txt), outro_txt))
    total = round(sum(b[3] for b in blocks), 2)
    print(f"  [short] total ~{total:.0f}s")

    # reuse images downloaded by the long recap when present; fetch if missing
    seg_imgs = {}
    for i, seg in enumerate(segments, 1):
        have = sorted(glob.glob(os.path.join(img_dir, f"s{i}_*"))) if os.path.isdir(img_dir) else []
        if have:
            seg_imgs[i] = ["img/" + os.path.basename(p) for p in have]
        else:
            seg_imgs[i] = _download_images(seg.get("images"), img_dir, i)

    segs_html, anim, caps_ev, kcaps_html = [], [], [], []
    t = 0.0
    story_i = 0
    _wkbq = ["abstract technology background dark blue", "data visualization abstract dark",
             "futuristic digital network glowing", "neural network nodes abstract dark"]
    for kind, seg, _a, dur, words, spoken in blocks:
        if kind == "intro":
            sid = "seg-intro"
            _cp = brand.get("cover_period") or (f"Tuần {_esc(week)}" if week else "")
            _cp_br = f"<br>{_cp}" if _cp else ""
            inner = (f'<div class="cover"><div class="big">{_esc(brand["a"])} <span>{_esc(brand["b"])}</span>'
                     + _cp_br + '</div>'
                     f'<div class="sub">{_esc(brand["tagline_short"])}</div>'
                     f'<div class="sub2">{_esc(range_)}</div></div>')
            segs_html.append(f'<section class="seg" id="{sid}">{inner}</section>')
        elif kind == "outro":
            sid = "seg-outro"
            inner = (f'<div class="cover"><div class="big">{brand.get("outro_big_short", "Đọc bản tin<br>đầy đủ")}</div>'
                     f'<div class="sub">{brand.get("outro_sub_short", "kèm audio + video chi tiết")}</div>'
                     f'<div class="sub2">{_esc(brand["site"])}</div></div>')
            segs_html.append(f'<section class="seg" id="{sid}">{inner}</section>')
        else:
            story_i += 1
            sid = f"seg-{story_i}"
            # AI chọn component qua diagram.type (stats/bullets/tags/process/bars/quote/
            # bignum). Không hợp lệ -> fill-bullet từ bullets.
            sdiag = seg.get("diagram") or {}
            styp = (sdiag.get("type") or "").lower()
            if styp in SHORT_PALETTE and sdiag.get("items"):
                items = [_wk_it(x) for x in list(sdiag["items"])[:4]]
            else:
                styp = "bullets"
                items = [(b, "") for b in _seg_bullets(seg, n=3, max_len=58)]
            sa_div, n_it = short_card_block(styp, items, sid)
            # ẢNH lấp khung: ảnh segment -> b-roll fallback nếu thiếu
            imgs = seg_imgs.get(story_i) or []
            img_src = imgs[0] if imgs else None
            if not img_src:
                local = _local_filler(story_i)   # filler on-brand tự chuẩn bị, ưu tiên hơn b-roll
                if local:
                    dst = os.path.join(img_dir, f"filler_s{story_i}{os.path.splitext(local)[1]}")
                    shutil.copy2(local, dst)
                    img_src = "img/" + os.path.basename(dst)
                else:
                    bp = os.path.join(img_dir, f"broll_s{story_i}.jpg")
                    if _broll_image(_wkbq[(story_i - 1) % len(_wkbq)], bp):
                        img_src = "img/" + os.path.basename(bp)
            img_div = f'<div class="heroimg"><img id="{sid}-im" src="{_esc(img_src)}"></div>' if img_src else ""
            cls = "seg story" if img_div else "seg story noimg"
            # AI chọn layout qua seg.layout ∈ {a,b,c}; thiếu -> xoay vòng.
            tpl = str(seg.get("layout") or "").lower()
            if tpl not in ("a", "b", "c"):
                tpl = ("a", "b", "c")[(story_i - 1) % 3]
            inner = (f'<span class="rank">TOP {story_i}</span>'
                     f'<div class="hl">{_esc(seg.get("headline") or "")}</div>'
                     f'<div class="content tpl-{tpl}">{sa_div}{img_div}</div>')
            segs_html.append(f'<section class="{cls}" id="{sid}">{inner}</section>')
            # BEAT-SYNC reveal (trượt lên) rải theo nhịp đọc (mốc ASR)
            wspan = (words[-1][2] if words else max(0.6, dur - 0.6))
            for j in range(n_it):
                rt = t + 0.45 + j / max(1, n_it) * wspan * 0.55
                anim.append(f'    m.fromTo("#{sid}-b{j}",{{opacity:0,y:26}},{{opacity:1,y:0,duration:0.4,ease:"power2.out"}},{rt:.2f});')
            if img_src:
                anim.append(f'    m.to("#{sid}-im",{{opacity:1,duration:0.45}},{t + 0.25:.2f});')
                anim.append(f'    m.fromTo("#{sid}-im",{{scale:1.0}},{{scale:1.06,duration:{max(1.0, dur):.2f},ease:"none"}},{t + 0.45:.2f});')
            _karaoke_caps(words, spoken, t, dur, kcaps_html, anim, f"{sid}cap")
        anim.append(f'    m.to("#{sid}",{{opacity:1,duration:0.4}},{t:.2f});')
        if t + dur < total - 0.1:
            anim.append(f'    m.to("#{sid}",{{opacity:0,duration:0.4}},{t + dur - 0.4:.2f});')
        t += dur

    # ----- phụ đề KARAOKE (tween từng từ đã ở trong `anim`) -----
    caps_html = kcaps_html

    epi = brand.get("epi") or (f"Tuần {week}" if week else date)
    html = (_SHORT_HEAD
            .replace("{TOTAL}", str(total))
            .replace("{EPI}", _esc(epi))
            .replace("{SEGS}", "\n  ".join(segs_html))
            .replace("{CAPS}", "\n  ".join(caps_html))
            .replace("{ANIM}", "\n".join(anim)))
    html = _brandify(html, brand)
    render.write_index(proj, html)

    silent = os.path.join(proj, "_silent_short.mp4")
    print("  [short] rendering slides (HyperFrames) ...")
    render.render_project(proj, silent, timeout=1800, label="short")

    parts = []
    for blk in blocks:
        parts.append(blk[2])   # audio (block 4-tuple recap / 6-tuple short)
        parts.append(np.zeros(int(sr * pad), dtype=np.float32))
    voice = np.concatenate(parts)

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    tmp_wav = out_path + ".__voice.wav"
    sf.write(tmp_wav, voice, sr)
    try:
        av.mux(silent, tmp_wav, out_path, mode="fit")
    finally:
        for p in (tmp_wav, silent):
            try:
                os.remove(p)
            except OSError:
                pass
    return out_path
