"""Top Story — DEEP-DIVE video for ONE hot AI story (long 16:9 + short 9:16).

BEAT-SYNCED narration (v2): the voiceover READS the on-screen text and then
explains it in plain language. Each section is a sequence of beats — lead-in,
one beat per bullet POINT, one beat per SmartArt step — and every visual
element (bullet line, diagram box) fades in exactly when its narration beat
starts. Media panel cycles images/clips during the lead+points span; the
diagram takes over the panel for its own beats.

Section JSON (v2 schema; v1 "narration"+"bullets" still accepted as fallback):

  {
    "title": "<=8 từ>",
    "lead": "1-2 câu dẫn dắt phần này",
    "points": [
      {"text": "<bullet hiển thị, <=12 từ>",
       "say":  "đọc bullet + giảng giải chi tiết dễ hiểu, 2-4 câu"}
    ],
    "media": [ {"type":"image","src":...}, {"type":"clip","src":"clips/c1.mp4"} ],
    "diagram": {
      "type": "flow|versus|stack|stats", "title": "...",
      "say": "1 câu giới thiệu sơ đồ (optional)",
      "items": [{"t":"...", "d":"...", "say": "giải thích bước này 1-2 câu"}],
      // versus: dùng CHÍNH "items" với đúng 2 phần tử (cột trái vs phải).
      //         (khuôn cũ "left"/"right":{h,items} vẫn được hỗ trợ ngược)
    }
  }

Cách gọi (lối chính là `video-studio render --project topstory`; CLI dưới đây giữ cho
việc chạy tay một số báo):
  python -m video_studio.templates.news.top_story_video --json brief.json --out-dir DIR
         --date 2026-06-12 --brand-a A --brand-b B --site <nơi đọc ở outro>
         [--profile <tên profile giọng>] [--long-only | --short-only]

Embedded clips follow the HyperFrames timed-clip contract (<video muted
playsinline data-start data-duration data-track-index>) and are ffmpeg-fit to
the FULL section duration so they can never run out before their window ends.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import numpy as np
import soundfile as sf

from voice_studio import av, engine, profiles

from ... import _env, projects, render
from . import news_video as nv

PROJECT = "topstory"


def _proj():
    """Thư mục project `topstory` trong trạm (tạo + chép cấu hình từ `demo/` nếu thiếu)."""
    return projects.ensure(PROJECT)


# Chỉ là cách diễn đạt, không phải danh tính. a · b · site BẮT BUỘC đến từ spec.
BRAND_DEFAULTS = {"kicker": "🔥 TIN NÓNG NHẤT HÔM NAY"}
BRAND = {}

# B-ROLL fallback (Openverse) khi section thiếu ảnh: ưu tiên ảnh TECH TRỪU TƯỢNG sạch (xoay vòng
# theo section để không trùng). Ảnh ĐÚNG chủ đề nên do research cấp ở JSON `media`; đây chỉ lấp khung.
BROLL_QUERIES = ["abstract technology background dark blue", "futuristic digital network glowing",
                 "data visualization abstract dark", "neural network nodes abstract",
                 "circuit board macro blue", "digital particles wave abstract dark"]
BROLL_FALLBACK = os.environ.get("VIDEO_BROLL_QUERY") or BROLL_QUERIES[0]

_VN_WD = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]


def _vn_display(date_iso):
    import datetime
    try:
        dt = datetime.datetime.strptime(date_iso, "%Y-%m-%d")
        return f"{_VN_WD[dt.weekday()]} · {dt.strftime('%d/%m/%Y')}"
    except Exception:
        return date_iso


def _ffbin(name):
    """ffmpeg/ffprobe: FFMPEG_DIR → PATH. Bản cũ tự nối `.exe` — sai ở mọi máy không-Windows."""
    return (_env.ffmpeg_exe() if name == "ffmpeg" else _env.ffprobe_exe()) or name


def _clip_duration(path):
    out = subprocess.run([_ffbin("ffprobe"), "-v", "error", "-show_entries",
                          "format=duration", "-of", "csv=p=0", path],
                         capture_output=True, text=True, timeout=60)
    try:
        return float(out.stdout.strip())
    except Exception:
        return 0.0


def _fit_clip(src, dst, want):
    """Re-encode `src` to EXACTLY `want` seconds (trim, or freeze last frame),
    muted, h264 yuv420p 30fps with dense keyframes for accurate seeking."""
    d = _clip_duration(src)
    vf = "scale=trunc(iw/2)*2:trunc(ih/2)*2,fps=30"
    if d <= 0.1:
        raise ValueError(f"unreadable clip: {src}")
    if d < want - 0.05:
        vf += f",tpad=stop_mode=clone:stop_duration={want - d + 0.2:.2f}"
    cmd = [_ffbin("ffmpeg"), "-y", "-i", src, "-t", f"{want:.2f}", "-an",
           "-vf", vf, "-c:v", "libx264", "-preset", "veryfast", "-crf", "22",
           "-g", "30", "-pix_fmt", "yuv420p", dst]
    subprocess.run(cmd, check=True, capture_output=True, timeout=600)
    return dst


# ------------------------------- SmartArt --------------------------------

def _it(x):
    """Normalize a diagram item to (title, desc). PHÒNG THỦ schema drift từ research
    (20260707: {value,label} / {label,desc} / {text} / {bullet} / chuỗi trần đều từng
    xuất hiện -> card rỗng chữ trên video đã đăng)."""
    if isinstance(x, dict):
        # cặp {value,label}: value = số to, label = nhãn (stats)
        if x.get("value") is not None and x.get("label") is not None and not x.get("t"):
            return str(x["value"]), str(x["label"])
        t = (x.get("t") or x.get("v") or x.get("title") or x.get("text") or x.get("name")
             or x.get("label") or x.get("bullet") or x.get("value") or "")
        d = (x.get("d") or x.get("l") or x.get("desc") or x.get("description")
             or x.get("detail") or x.get("sub") or x.get("say_short") or "")
        return str(t), str(d)
    return str(x or ""), ""


def _norm_diagram(diag):
    """Chuẩn hoá diagram về dạng {type, title, items[...]}: nhận steps/rows thay items,
    nhận versus dạng {left/right:{title|h, points|items}} -> 2 item phẳng. KHÔNG items
    được thì trả nguyên (caller tự fallback)."""
    if not isinstance(diag, dict):
        return {}
    d = dict(diag)
    if not d.get("items"):
        alt = d.get("steps") or d.get("rows") or d.get("points")
        if isinstance(alt, list) and alt:
            d["items"] = alt
    if not d.get("items"):
        pair = []
        for k in ("left", "a"), ("right", "b"):
            side = d.get(k[0]) or d.get(k[1])
            if isinstance(side, dict):
                pts = side.get("points") or side.get("items") or []
                sub = " · ".join(_it(p)[0] for p in pts[:4] if _it(p)[0])
                pair.append({"t": side.get("title") or side.get("h") or "", "d": sub})
            elif isinstance(side, str):
                pair.append({"t": side, "d": ""})
        if len(pair) == 2 and (pair[0]["t"] or pair[1]["t"]):
            d["items"] = pair
    return d


def diagram_html(diag, did):
    """Inline SmartArt for the media panel. Children get ids {did}-sN so the
    timeline can reveal each one exactly when its narration beat starts."""
    diag = _norm_diagram(diag)
    typ = (diag or {}).get("type", "flow")
    title = nv._esc(diag.get("title", ""))
    head = f'<div class="dtitle">{title}</div>' if title else ""
    if typ == "versus":
        items = list(diag.get("items") or [])
        if items:  # current schema: flat 2-item list [{t,d,say}, ...]
            cols = []
            for j, x in enumerate(items[:2]):
                t, d = _it(x)
                cls = "dl" if j == 0 else "dr"
                sub = f'<div class="dd">{nv._esc(d)}</div>' if d else ""
                cols.append(f'<div class="dcol {cls}" id="{did}-s{j}">'
                            f'<h4>{nv._esc(t)}</h4>{sub}</div>')
            while len(cols) < 2:
                cols.append(f'<div class="dcol dr" id="{did}-s{len(cols)}"></div>')
        else:  # back-compat: legacy {left:{h,items}, right:{h,items}}
            cols = []
            for k, cls in (("left", "dl"), ("right", "dr")):
                c = diag.get(k) or {}
                lis = "".join(f"<li>{nv._esc(_it(i)[0])}</li>" for i in (c.get("items") or []))
                cols.append(f'<div class="dcol {cls}" id="{did}-s{len(cols)}">'
                            f'<h4>{nv._esc(c.get("h", ""))}</h4><ul>{lis}</ul></div>')
        body = f'<div class="dvs">{cols[0]}<div class="dvsb">VS</div>{cols[1]}</div>'
    elif typ == "stack":
        items = list(diag.get("items") or [])
        rows = []
        for j, x in enumerate(reversed(items)):  # draw top layer first
            t, d = _it(x)
            sub = f'<span class="dd">{nv._esc(d)}</span>' if d else ""
            rows.append(f'<div class="dlayer" id="{did}-s{j}">{nv._esc(t)}{sub}</div>')
        body = f'<div class="dstack">{"".join(rows)}</div>'
    elif typ == "stats":
        cards = []
        for j, x in enumerate(diag.get("items") or []):
            v, l = _it(x)
            cards.append(f'<div class="dstat" id="{did}-s{j}">'
                         f'<b>{nv._esc(v)}</b><span>{nv._esc(l)}</span></div>')
        body = f'<div class="dstats">{"".join(cards)}</div>'
    elif typ in ("bullets", "warning"):  # fill-bullet SmartArt (warning: long dùng chung thẻ; short có chip hổ phách riêng)
        rows = []
        for j, x in enumerate(diag.get("items") or []):
            t, d = _it(x)
            sub = f'<span class="dd">{nv._esc(d)}</span>' if d else ""
            rows.append(f'<div class="dbul" id="{did}-s{j}"><span class="dbn">{j + 1}</span>'
                        f'<span class="dbt">{nv._esc(t)}{sub}</span></div>')
        body = f'<div class="dbullets">{"".join(rows)}</div>'
    else:  # flow
        steps = []
        items = list(diag.get("items") or [])
        for j, x in enumerate(items):
            t, d = _it(x)
            sub = f'<span class="dd">{nv._esc(d)}</span>' if d else ""
            steps.append(f'<div class="dstep" id="{did}-s{j}">{nv._esc(t)}{sub}</div>')
            if j < len(items) - 1:
                steps.append('<div class="darr">▼</div>')
        body = f'<div class="dflow">{"".join(steps)}</div>'
    return f'{head}{body}'


def _diag_child_count(diag):
    diag = _norm_diagram(diag)
    typ = (diag or {}).get("type", "flow")
    if typ == "versus":
        return 2
    return len(diag.get("items") or [])


def _diag_say_pairs(diag):
    """[(child_dom_idx, say)] in NARRATION order. say may be None.
    stack children are drawn top-first, so the DOM index is reversed."""
    diag = _norm_diagram(diag)
    typ = (diag or {}).get("type", "flow")
    out = []
    if typ == "versus":
        items = list(diag.get("items") or [])
        if items:
            for k, x in enumerate(items[:2]):
                out.append((k, x.get("say") if isinstance(x, dict) else None))
        else:
            for k, side in enumerate(("left", "right")):
                out.append((k, (diag.get(side) or {}).get("say")))
    elif typ == "stack":
        items = list(diag.get("items") or [])
        n = len(items)
        for i, x in enumerate(items):  # narrate bottom-up
            out.append((n - 1 - i, x.get("say") if isinstance(x, dict) else None))
    else:
        for i, x in enumerate(diag.get("items") or []):
            out.append((i, x.get("say") if isinstance(x, dict) else None))
    return out


# ------------------------------ templates --------------------------------

# News v2: near-black bg, Inter, accent CSS vars (--ac1..--ac4 set per-brand via {ACSS}),
# rounded cards + glow, animated tech bg (dots/orbs/grid, GSAP-driven), transcript caption bar.
_V2_BASE = """
  :root{--ac1:#00E5FF;--ac2:#A78BFA;--ac3:#00E676;--ac4:#FFC857;
        --tx:#F0F0F5;--mut:#A0A0B0;--bd:#2A2A3A;--pan:#161620}
  *{font-family:__FONT__}
  .grid{position:absolute;inset:-200px;opacity:.28;pointer-events:none;z-index:0;
    background-image:linear-gradient(rgba(255,255,255,.05) 1px,transparent 1px),
      linear-gradient(90deg,rgba(255,255,255,.05) 1px,transparent 1px);background-size:92px 92px}
  .orb{position:absolute;border-radius:50%;filter:blur(75px);opacity:.18;pointer-events:none;z-index:0}
  .dot{position:absolute;border-radius:50%;pointer-events:none;z-index:0}
  .cap{position:absolute;left:0;right:0;text-align:center;z-index:8}
  .cap .c{position:absolute;left:50%;transform:translateX(-50%);opacity:0;
    background:rgba(7,9,15,.76);border:1px solid var(--bd);border-radius:15px;color:#eaf2ff}
"""

_DIAG_CSS = """
  .pitem{position:absolute;inset:0;opacity:0}
  .diag{display:flex;flex-direction:column;align-items:center;justify-content:center;
    padding:30px;width:100%;height:100%;box-sizing:border-box}
  .dtitle{font-size:28px;font-weight:800;color:var(--mut);margin:0 0 24px;text-align:center}
  .dflow{display:flex;flex-direction:column;align-items:center;width:100%}
  .dstep{width:90%;background:var(--pan);border:1px solid var(--bd);border-left:4px solid var(--ac1);border-radius:16px;
    padding:15px 20px;font-size:25px;font-weight:700;text-align:left;color:var(--tx);opacity:0}
  .dstep .dd{display:block;font-size:19px;font-weight:400;color:var(--mut);margin-top:4px}
  .darr{font-size:22px;color:var(--ac1);line-height:1.15;margin:4px 0}
  .dvs{display:flex;align-items:stretch;gap:16px;width:100%}
  .dvsb{align-self:center;font-size:26px;font-weight:900;color:var(--ac4)}
  .dcol{flex:1;border-radius:18px;padding:18px 20px;opacity:0;background:var(--pan);border:1px solid var(--bd)}
  .dcol.dl{border-top:3px solid var(--ac1)}
  .dcol.dr{border-top:3px solid var(--ac2)}
  .dcol h4{margin:0 0 10px;font-size:25px;color:var(--tx)}
  .dcol ul{margin:0;padding-left:20px;font-size:21px;line-height:1.5;color:var(--mut)}
  .dcol .dd{font-size:21px;line-height:1.5;color:var(--mut)}
  .dstack{display:flex;flex-direction:column-reverse;gap:12px;width:88%}
  .dlayer{border-radius:14px;padding:14px 18px;font-size:23px;font-weight:700;text-align:center;
    color:var(--tx);background:var(--pan);border:1px solid var(--bd);border-left:4px solid var(--ac1);opacity:0}
  .dlayer:nth-child(2n){border-left-color:var(--ac2)}
  .dlayer .dd{display:block;font-size:18px;font-weight:400;color:var(--mut)}
  .dstats{display:grid;grid-template-columns:repeat(2,1fr);gap:18px;width:92%}
  .dstat{border:1px solid var(--bd);border-radius:18px;padding:20px 16px;text-align:center;
    background:var(--pan);opacity:0}
  .dstat b{display:block;font-size:48px;font-weight:900;color:var(--ac1);font-variant-numeric:tabular-nums}
  .dstat span{font-size:20px;color:var(--mut)}
  .dbullets{display:flex;flex-direction:column;gap:18px;width:96%}
  .dbul{display:flex;align-items:center;gap:18px;background:var(--pan);border:1px solid var(--bd);
    border-left:5px solid var(--ac1);border-radius:18px;padding:18px 22px;opacity:0}
  .dbul:nth-child(2n){border-left-color:var(--ac2)}
  .dbul:nth-child(3n){border-left-color:var(--ac3)}
  .dbn{flex:0 0 auto;width:50px;height:50px;border-radius:14px;display:flex;align-items:center;justify-content:center;
    font-size:27px;font-weight:900;color:#08121f;background:linear-gradient(135deg,var(--ac1),var(--ac2))}
  .dbt{font-size:28px;font-weight:700;color:var(--tx);line-height:1.25}
  .dbt .dd{display:block;font-size:20px;font-weight:400;color:var(--mut);margin-top:4px}
"""

_LONG_HEAD = """<!doctype html>
<html lang="vi" data-resolution="landscape">
<head><meta charset="UTF-8"/>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>
  html,body{margin:0;width:1920px;height:1080px;overflow:hidden}
  #master-root{width:1920px;height:1080px;position:relative;color:var(--tx);
    background:radial-gradient(1400px 820px at 78% 8%,#15203a 0%,#0a0d18 55%,#070a12 100%)}
""" + _V2_BASE + """
  .brand{position:absolute;top:54px;left:90px;display:flex;align-items:center;gap:16px;z-index:6}
  .brand .mark{width:48px;height:48px;border-radius:13px;background:linear-gradient(135deg,var(--ac1),#2563eb);box-shadow:0 0 20px rgba(0,229,255,.45)}
  .brand .n{font-size:30px;font-weight:800}.brand .n span{color:var(--ac1)}
  .epi{position:absolute;top:62px;right:90px;color:var(--mut);font-size:26px;z-index:6}
  .seg{position:absolute;inset:0;opacity:0;z-index:2}
  .cover{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:0 160px}
  .cover .kick{display:inline-flex;align-items:center;font-size:30px;font-weight:700;color:var(--ac1);
    background:rgba(0,229,255,.08);border:1px solid rgba(0,229,255,.4);border-radius:999px;padding:11px 30px;margin-bottom:40px}
  .cover .big{font-size:150px;font-weight:900;letter-spacing:-1px;line-height:1.05;max-width:1680px}
  .cover .sub{font-size:38px;color:var(--mut);margin-top:34px}
  .cover .sub2{font-size:30px;color:#67809f;margin-top:14px}
  .sec .chip{position:absolute;top:160px;left:90px;font-size:26px;font-weight:700;color:var(--ac1);
    background:rgba(0,229,255,.08);border:1px solid rgba(0,229,255,.4);border-radius:999px;padding:8px 26px;z-index:4}
  .sec .txt{position:absolute;left:90px;top:250px;width:860px;z-index:4}
  .sec .hl{font-size:56px;font-weight:900;line-height:1.16}
  .sec .bul{margin:34px 0 0;padding:0;list-style:none;font-size:30px;line-height:1.45;color:var(--mut)}
  .sec .bul li{position:relative;margin-top:18px;padding-left:40px;opacity:0}
  .sec .bul li::before{content:"";position:absolute;left:0;top:14px;width:20px;height:3px;border-radius:2px;background:var(--ac1)}
  .sec .bul li.on{color:var(--tx)}
  .sec .panel{position:absolute;right:90px;top:200px;width:840px;height:660px;border-radius:24px;overflow:hidden;
    box-shadow:0 30px 80px rgba(0,0,0,.55);background:var(--pan);border:1px solid var(--bd)}
  .sec .panel img,.sec .panel video{position:absolute;inset:0;width:100%;height:100%;object-fit:contain}
  .sec .panel img{opacity:0}
  .sec.nopanel .txt{left:50%;transform:translateX(-50%);text-align:center;top:300px;width:1500px}
  .cap{bottom:56px}.cap .c{bottom:0;max-width:1400px;padding:14px 30px;font-size:29px;line-height:1.34}
  .cap .c .kw{color:#76859c}   /* karaoke long (như short): từ chưa đọc TỐI, tween trắng/vàng đúng nhịp */
  #prog{position:absolute;bottom:0;left:0;height:9px;width:0%;background:linear-gradient(90deg,var(--ac1),var(--ac2));z-index:9}
""" + _DIAG_CSS + nv.SHORT_COMPONENT_CSS + """
</style></head>
<body>
<div id="master-root" data-composition-id="master" data-width="1920" data-height="1080" data-start="0" data-duration="{TOTAL}">{ACSS}
  <div class="grid" id="grid"></div>
  <div class="orb" id="orb1" style="width:540px;height:540px;left:-120px;top:120px;background:var(--ac1)"></div>
  <div class="orb" id="orb2" style="width:480px;height:480px;right:-90px;bottom:-70px;background:var(--ac2)"></div>
  {BG}
  <div class="brand"><span class="mark"></span><div class="n">{BA} <span>{BB}</span></div></div>
  <div class="epi">{EPI}</div>
  {SEGS}
  <div class="cap">{CAPS}</div>
  <div id="prog"></div>
  <script>
    window.__timelines=window.__timelines||{};
    var m=gsap.timeline({paused:true});
    m.fromTo("#prog",{width:"0%"},{width:"100%",duration:{TOTAL},ease:"none"},0);
    m.fromTo("#grid",{x:0,y:0},{x:-92,y:-92,duration:26,repeat:{RGRID},ease:"none"},0);
    m.to("#orb1",{x:130,y:-60,duration:15,repeat:{RORB1},yoyo:true,ease:"sine.inOut"},0);
    m.to("#orb2",{x:-110,y:50,duration:17,repeat:{RORB2},yoyo:true,ease:"sine.inOut"},0);
{BGANIM}
{ANIM}
    window.__timelines["master"]=m;
  </script>
</div>
</body></html>
"""

_SHORT_HEAD = """<!doctype html>
<html lang="vi" data-resolution="portrait">
<head><meta charset="UTF-8"/>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>
  html,body{margin:0;width:1080px;height:1920px;overflow:hidden}
  #master-root{width:1080px;height:1920px;position:relative;color:var(--tx);
    background:radial-gradient(900px 1200px at 50% 8%,#15203a 0%,#0a0d18 55%,#070a12 100%)}
""" + _V2_BASE + """
  .brand{position:absolute;top:64px;left:64px;display:flex;align-items:center;gap:14px;z-index:6}
  .brand .mark{width:54px;height:54px;border-radius:15px;background:linear-gradient(135deg,var(--ac1),#2563eb);box-shadow:0 0 20px rgba(0,229,255,.45)}
  .brand .n{font-size:34px;font-weight:800}.brand .n span{color:var(--ac1)}
  .epi{position:absolute;top:74px;right:64px;color:var(--mut);font-size:26px;z-index:6}
  .site{position:absolute;bottom:46px;left:0;right:0;text-align:center;color:#67809f;font-size:28px;z-index:6}
  .seg{position:absolute;inset:0;opacity:0;z-index:2}
  .cover{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:0 70px}
  .cover .kick{display:inline-flex;font-size:30px;font-weight:700;color:var(--ac1);
    background:rgba(0,229,255,.08);border:1px solid rgba(0,229,255,.4);border-radius:999px;padding:10px 26px;margin-bottom:36px}
  .cover .big{font-size:88px;font-weight:900;letter-spacing:-2px;line-height:1.08}
  .cover .sub2{font-size:32px;color:#67809f;margin-top:26px}
  .sec .chip{position:absolute;top:210px;left:64px;font-size:30px;font-weight:700;color:var(--ac1);
    background:rgba(0,229,255,.08);border:1px solid rgba(0,229,255,.4);border-radius:999px;padding:9px 26px;z-index:4}
  .sec .hl{position:absolute;top:300px;left:64px;right:64px;font-size:56px;font-weight:900;line-height:1.16;z-index:4}
  /* SHORT v3: SmartArt fill-bullet (TRÊN) + ẢNH lấp khung (DƯỚI) -> không để ô trống */
  /* content zone = FLEX column, GAP ĐỀU giữa các khối (cards <-> ảnh); bộ TEMPLATE để mix */
  .sec .content{position:absolute;left:64px;right:64px;top:466px;bottom:416px;display:flex;flex-direction:column;gap:34px;z-index:4}
  .sec .salist{display:flex;flex-direction:column;gap:18px;flex:0 0 auto}
  .sec .sacard{display:flex;align-items:center;gap:18px;background:var(--pan);border:1px solid var(--bd);
    border-left:6px solid var(--ac1);border-radius:20px;padding:20px 24px;opacity:0;box-shadow:0 10px 30px rgba(0,0,0,.35)}
  .sec .sacard:nth-child(2n){border-left-color:var(--ac2)}
  .sec .sacard:nth-child(3n){border-left-color:var(--ac3)}
  .sec .san{flex:0 0 auto;width:56px;height:56px;border-radius:15px;display:flex;align-items:center;justify-content:center;
    font-size:30px;font-weight:900;color:#08121f;background:linear-gradient(135deg,var(--ac1),var(--ac2))}
  .sec .sat{font-size:31px;font-weight:700;color:var(--tx);line-height:1.24}
  .sec .statc{display:flex;flex-direction:column;align-items:flex-start;background:var(--pan);border:1px solid var(--bd);
    border-left:6px solid var(--ac3);border-radius:20px;padding:22px 28px;opacity:0;box-shadow:0 10px 30px rgba(0,0,0,.35)}
  .sec .statc b{font-size:62px;font-weight:900;color:var(--ac1);line-height:1;font-variant-numeric:tabular-nums}
  .sec .statc span{font-size:27px;color:var(--mut);margin-top:8px;line-height:1.25}
  .sec .heroimg{position:relative;flex:1 1 0;min-height:0;border-radius:26px;overflow:hidden;
    border:1px solid var(--bd);box-shadow:0 24px 70px rgba(0,0,0,.55);background:#0b0e18}
  /* 20260707: cover→contain — ảnh OG/screenshot GitHub có CHỮ bị crop mất thông tin;
     contain + nền panel = card kiểu escbase, ảnh hiện TRỌN VẸN */
  .sec .heroimg{background:var(--pan)}
  .sec .heroimg img,.sec .heroimg video{position:absolute;inset:0;width:100%;height:100%;object-fit:contain;opacity:0}
  /* TEMPLATE mix: a=cards↑·ảnh↓ (default) | b=ảnh↑·cards↓ | c=ảnh↑ LỚN·cards↓ gọn */
  .sec .content.tpl-b .heroimg{order:1}.sec .content.tpl-b .salist{order:2}
  .sec .content.tpl-c .heroimg{order:1;flex:1.7 1 0}.sec .content.tpl-c .salist{order:2}
  .sec.noimg .content{justify-content:center;gap:30px}
  .sec.noimg .sacard{padding:30px 28px}.sec.noimg .sat{font-size:37px}
  .cap{bottom:150px}.cap .c{bottom:0;max-width:960px;padding:18px 30px;font-size:40px;line-height:1.3;font-weight:600}
  .cap .c .kw{color:#76859c}   /* karaoke: từ chưa đọc TỐI, tween -> trắng đúng nhịp đọc */
  #prog{position:absolute;top:0;left:0;height:12px;width:0%;background:linear-gradient(90deg,var(--ac1),var(--ac2));z-index:9}
""" + _DIAG_CSS + nv.SHORT_COMPONENT_CSS + """
</style></head>
<body>
<div id="master-root" data-composition-id="master" data-width="1080" data-height="1920" data-start="0" data-duration="{TOTAL}">{ACSS}
  <div class="grid" id="grid"></div>
  <div class="orb" id="orb1" style="width:480px;height:480px;left:-120px;top:120px;background:var(--ac1)"></div>
  <div class="orb" id="orb2" style="width:420px;height:420px;right:-90px;bottom:60px;background:var(--ac2)"></div>
  {BG}
  <div class="brand"><span class="mark"></span><div class="n">{BA} <span>{BB}</span></div></div>
  <div class="epi">{EPI}</div>
  <div class="site">{BSITE}</div>
  {SEGS}
  <div class="cap">{CAPS}</div>
  <div id="prog"></div>
  <script>
    window.__timelines=window.__timelines||{};
    var m=gsap.timeline({paused:true});
    m.fromTo("#prog",{width:"0%"},{width:"100%",duration:{TOTAL},ease:"none"},0);
    m.fromTo("#grid",{x:0,y:0},{x:-92,y:-92,duration:26,repeat:{RGRID},ease:"none"},0);
    m.to("#orb1",{x:120,y:-60,duration:15,repeat:{RORB1},yoyo:true,ease:"sine.inOut"},0);
    m.to("#orb2",{x:-100,y:50,duration:17,repeat:{RORB2},yoyo:true,ease:"sine.inOut"},0);
{BGANIM}
{ANIM}
    window.__timelines["master"]=m;
  </script>
</div>
</body></html>
"""


# ------------------------------ build core --------------------------------

def _prep_media(sec, sec_i, json_dir, full_dur, tag):
    """Materialize one section's images/clips into the project folder.
    Returns [{"kind": "image"|"clip", "src": rel}]. Clips are ffmpeg-fit to the
    FULL section duration so their display window can never outrun the file."""
    media_dir = os.path.join(_proj(), "media")
    os.makedirs(media_dir, exist_ok=True)
    out = []
    _items = sec.get("media") or []
    if isinstance(_items, (dict, str)):  # schema drift: object đơn/chuỗi -> bọc list
        _items = [_items]
    for j, it in enumerate(_items):
        # Phòng thủ schema drift từ research: chuỗi URL trần -> {"type","src"};
        # dict thiếu "src" -> nhận path/source/url (20260707: run repo-weekly sinh
        # {"type","path","source"} làm crash 'str' object has no attribute 'get').
        if isinstance(it, str):
            it = {"type": "image", "src": it}
        elif isinstance(it, dict) and not it.get("src"):
            it = dict(it)
            it["src"] = it.get("path") or it.get("source") or it.get("url") or ""
        if not isinstance(it, dict):
            continue
        typ = (it.get("type") or "image").lower()
        try:
            if typ == "image":
                src = it.get("src") or ""
                if src.lower().startswith("http"):
                    got = nv._download_images([src], media_dir, f"{tag}{sec_i}x{j}", max_n=1)
                    if not got:
                        continue
                    out.append({"kind": "image", "src": "media/" + os.path.basename(got[0])})
                else:
                    p = src if os.path.isabs(src) else os.path.join(json_dir, src)
                    if not os.path.isfile(p):
                        continue
                    dst = os.path.join(media_dir, f"{tag}{sec_i}_{j}{os.path.splitext(p)[1]}")
                    shutil.copy2(p, dst)
                    out.append({"kind": "image", "src": "media/" + os.path.basename(dst)})
            else:  # clip / gif -> exact-fit muted mp4
                src = it.get("src") or ""
                p = src if os.path.isabs(src) else os.path.join(json_dir, src)
                if not os.path.isfile(p):
                    print(f"    [warn] clip missing: {src}")
                    continue
                dst = os.path.join(media_dir, f"{tag}{sec_i}_{j}.mp4")
                _fit_clip(p, dst, full_dur)
                out.append({"kind": "clip", "src": "media/" + os.path.basename(dst)})
        except Exception as exc:
            print(f"    [warn] media s{sec_i}/{j} failed: {type(exc).__name__}: {exc}")
    return out


def _sec_bullets(sec, max_n, max_len):
    """Bullet texts: v2 points[].text, else v1 bullets/narration."""
    pts = sec.get("points") or []
    if pts:
        out = []
        for p in pts[:max_n]:
            # phòng thủ key drift: text/bullet/t/point hoặc chuỗi trần (20260707: research
            # dùng "bullet" -> video dài mất sạch bullet)
            if isinstance(p, dict):
                b = (p.get("text") or p.get("bullet") or p.get("t") or p.get("point") or "").strip()
            else:
                b = str(p or "").strip()
            if not b:
                continue
            if len(b) > max_len:
                b = b[:max_len].rsplit(" ", 1)[0] + "…"
            out.append(b)
        if out:
            return out
    return nv._seg_bullets(sec, n=max_n, max_len=max_len)


def _bullets_diagram(sec, max_n=4, max_len=64):
    """Dựng SmartArt 'fill-bullet' từ points của section (dùng cho SHORT khi section
    KHÔNG có diagram riêng): mỗi ý chính -> 1 thẻ tô màu (thay vì bullet text trơn).
    Giữ 'say' để beat-sync nếu có narration beats."""
    items = []
    for p in (sec.get("points") or [])[:max_n]:
        if isinstance(p, dict):
            t = (p.get("text") or p.get("bullet") or p.get("t") or p.get("point") or "").strip()
            say = p.get("say")
        else:
            t, say = str(p).strip(), None
        if not t:
            continue
        if len(t) > max_len:
            t = t[:max_len].rsplit(" ", 1)[0] + "…"
        items.append({"t": t, "say": say})
    if not items:  # v1 fallback: bullets/narration
        for b in _sec_bullets(sec, max_n=max_n, max_len=max_len):
            if b:
                items.append({"t": b})
    return {"type": "bullets", "items": items} if items else None


_CAP_SPLIT = re.compile(r"(?<=[.!?…])\s+")


def _caption_chunks(text, max_len=68):
    """Tách narration thành các MẨU PHỤ ĐỀ ngắn (theo câu; câu dài cắt tiếp theo dấu phẩy/
    khoảng trắng) để mỗi dòng caption ngắn gọn, vừa khung short."""
    out = []
    for s in _CAP_SPLIT.split((text or "").strip()):
        s = s.strip()
        while len(s) > max_len:
            cut = s.rfind(",", 30, max_len)
            if cut < 30:
                cut = s.rfind(" ", 30, max_len)
            if cut < 30:
                cut = max_len
            out.append(s[:cut + 1].strip(" ,"))
            s = s[cut + 1:].strip()
        if s:
            out.append(s)
    return out


def _short_caps(blk, sec, t, dur, kcaps_html, anim, cidp):
    """Phụ đề KARAOKE (escbase-style): ASR word-level -> dòng ~5 từ; từng từ TỐI->SÁNG đúng mốc
    đọc (highlight theo nhịp). Append HTML vào kcaps_html + tween vào anim. Không ASR -> fallback
    cả dòng fade (tách câu canh tuyến tính)."""
    words = blk.get("caps_words") or []
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
                f'<span id="{cid}w{wi}" class="kw{" hl" if nv.hl_word(w[0]) else ""}">{nv._esc(w[0])}</span> '
                for wi, w in enumerate(line))
            kcaps_html.append(f'<div class="c" id="{cid}">{spans}</div>')
            anim.append(f'    m.to("#{cid}",{{opacity:1,duration:0.14}},{ls:.2f});')
            anim.append(f'    m.to("#{cid}",{{opacity:0,duration:0.14}},{max(ls + 0.3, le + 0.06):.2f});')
            for wi, w in enumerate(line):   # karaoke: từ số liệu/thuật ngữ VÀNG, còn lại trắng (escbase)
                col = "#FFC857" if nv.hl_word(w[0]) else "#ffffff"
                anim.append(f'    m.to("#{cid}w{wi}",{{color:"{col}",duration:0.08}},{t + w[1]:.2f});')
        return
    chunks = _caption_chunks(sec.get("narration_short") or sec.get("lead") or "")
    span = max(0.6, dur - 0.5)
    total_ch = sum(len(c) for c in chunks) or 1
    acc = 0.25
    for ci, c in enumerate(chunks):
        cid = f"{cidp}c{ci}"
        cs = t + acc
        acc += span * (len(c) / total_ch)
        kcaps_html.append(f'<div class="c" id="{cid}">{nv._esc(c)}</div>')
        anim.append(f'    m.to("#{cid}",{{opacity:1,duration:0.18}},{cs:.2f});')
        anim.append(f'    m.to("#{cid}",{{opacity:0,duration:0.18}},{max(cs + 0.3, t + acc - 0.1):.2f});')


def _synth_section_beats(model, sec, prompt, sr, gap=0.3):
    """Synthesize one section as a list of narration beats.
    Returns (audio, dur_no_pad, beats) where beats = [(kind, idx, offset_s)]:
      ("lead", None) · ("point", j) · ("dlead", None) · ("dstep", child_dom_idx)."""
    parts, beats = [], []
    off = 0.0
    z = np.zeros(int(sr * gap), dtype=np.float32)

    def add(kind, idx, text):
        nonlocal off
        a = nv._synth_long(model, text, prompt)
        beats.append((kind, idx, off, (text or "").strip()))  # keep text for transcript caption
        parts.append(a)
        parts.append(z)
        off += len(a) / sr + gap

    lead = sec.get("lead") or sec.get("narration") or sec.get("title", "")
    add("lead", None, lead)
    for j, pt in enumerate(sec.get("points") or []):
        add("point", j, pt.get("say") or pt.get("text", ""))
    diag = sec.get("diagram")
    if diag:
        if diag.get("say"):
            add("dlead", None, diag["say"])
        for child, say in _diag_say_pairs(diag):
            if say:
                add("dstep", child, say)
    return np.concatenate(parts), off, beats


def _bg_dots(n=30, total=None):
    """Deterministic tech bg: faint drifting dots (GSAP-driven so HyperFrames renders
    each frame correctly). Returns (html, anim_lines).

    Repeats are FINITE and sized to cover the whole video: HyperFrames renders by
    deterministically seeking the timeline, and an infinite tween (repeat:-1) expands
    into an unbounded seek index -> Chromium throws "Set maximum size exceeded" and the
    whole render fails. A finite repeat that outlasts `total` looks identical on screen."""
    span = (total or 600) + 20  # cover full duration + max start delay, with margin
    s = 20260616
    html, anim = [], []
    for i in range(n):
        s = (1103515245 * s + 12345) & 0x7FFFFFFF; x = (s % 1000) / 10.0
        s = (1103515245 * s + 12345) & 0x7FFFFFFF; y = (s % 1000) / 10.0
        s = (1103515245 * s + 12345) & 0x7FFFFFFF; sz = 2 + s % 4
        col = ["var(--ac1)", "var(--ac2)", "var(--ac3)"][i % 3]
        dly, dur = (i % 7) * 0.5, 18 + (i % 9) * 3
        rep = int(span // dur) + 1  # finite, never -1 (unbounded -> render crash)
        html.append(f'<div class="dot" id="bd{i}" style="left:{x:.1f}%;top:{y:.1f}%;width:{sz}px;'
                    f'height:{sz}px;background:{col};opacity:.5;box-shadow:0 0 8px {col}"></div>')
        anim.append(f'    m.to("#bd{i}",{{y:"-=40",x:"+=16",opacity:.14,duration:{dur},'
                    f'repeat:{rep},yoyo:true,ease:"sine.inOut"}},{dly:.1f});')
    return "".join(html), "\n".join(anim)


def _accent_css():
    """Per-brand accent override via env TOPSTORY_ACCENTS='ac1,ac2,ac3,ac4' (set by runner
    for Data). Empty -> template defaults (AI cyan/violet)."""
    acc = os.environ.get("TOPSTORY_ACCENTS", "").strip()
    if not acc:
        return ""
    p = [c.strip() for c in acc.split(",") if c.strip()]
    names = ["--ac1", "--ac2", "--ac3", "--ac4"]
    decl = ";".join(f"{n}:{c}" for n, c in zip(names, p))
    return f"<style>:root{{{decl}}}</style>"


def _build(story, blocks, total, head, json_dir, tag):
    """Assemble the composition HTML. blocks = list of dicts:
    {kind: intro|sec|outro, sec, audio, dur, beats|None}."""
    segs_html, anim, caps_ev, kcaps_html = [], [], [], []
    t = 0.0
    sec_i = 0
    track = 1
    for blk in blocks:
        kind, sec, dur, beats = blk["kind"], blk.get("sec"), blk["dur"], blk.get("beats")
        if kind == "intro":
            sid = "seg-cover"
            # escbase hook-orb-badge: JSON top-level "repo" -> avatar chủ repo trong orb
            # phát sáng + badge vàng nổi (số sao tăng) trên cover. Không có repo -> cover cũ.
            orb = ""
            rp = story.get("_repo") or {}
            if rp.get("full_name"):
                owner = str(rp["full_name"]).split("/")[0]
                m_badge = re.search(r"\+?\d+(?:[.,]\d+)?\s*[kKmM]?", str(rp.get("stars_gained") or ""))
                badge = (m_badge.group(0).replace(" ", "") if m_badge else
                         (f"{int(rp['stars']/1000)}k" if rp.get("stars") else ""))
                if badge:
                    badge_html = f'<div class="hookbadge" id="{sid}-bdg"><b>{nv._esc(badge)}</b><span>SAO ★</span></div>'
                else:
                    badge_html = ""
                orb = (f'<div class="hookwrap" id="{sid}-orb"><div class="hookring"></div>'
                       f'<div class="hookorb"><img src="https://github.com/{nv._esc(owner)}.png"></div>'
                       + badge_html + '</div>')
            # Autoscale tiêu đề: headline dài -> giảm cỡ chữ để không tràn/quá to màn hình
            _hl = story.get("headline", "")
            _base = 150 if tag == "L" else 108
            _fs = _base * (1.0 if len(_hl) <= 38 else 0.86 if len(_hl) <= 52 else 0.74 if len(_hl) <= 66 else 0.64)
            inner = (f'<div class="cover">' + orb + f'<div class="kick">{nv._esc(BRAND["kicker"])}</div>'
                     f'<div class="big" style="font-size:{_fs:.0f}px">{nv._esc(_hl)}</div>'
                     f'<div class="sub2">{nv._esc(story.get("_display", ""))}'
                     + (f' · Nguồn: {nv._esc(story["source"])}' if story.get("source") else "")
                     + '</div></div>')
            segs_html.append(f'<section class="seg" id="{sid}">{inner}</section>')
            anim.append(f'    m.fromTo("#{sid} .big",{{y:40,opacity:0}},{{y:0,opacity:1,duration:0.7,ease:"power3.out"}},0.35);')
            if orb:
                anim.append(f'    m.fromTo("#{sid}-orb",{{scale:0.85,opacity:0}},{{scale:1,opacity:1,duration:0.6,ease:"power2.out"}},0.15);')
                anim.append(f'    m.fromTo("#{sid}-bdg",{{scale:0.4,opacity:0}},{{scale:1,opacity:1,duration:0.5,ease:"back.out(2)"}},0.7);')
            if tag == "L" and blk.get("caps_words"):   # long: karaoke như short
                _short_caps(blk, {}, t, dur, kcaps_html, anim, f"{sid}cap")
        elif kind == "outro":
            sid = "seg-outro"
            # escbase verdict-stamp: JSON có top-level "verdict" {t: câu chốt, d: phụ đề}
            # -> card chốt glow HIỆN TRƯỚC dòng theo dõi (video review/repo).
            vjs = story.get("verdict") or {}
            vstamp = ""
            if isinstance(vjs, dict) and vjs.get("t"):
                vstamp = (f'<div class="verdictc" id="{sid}-vd" style="margin-bottom:56px">'
                          f'<b>{nv._esc(vjs["t"])}</b>'
                          + (f'<span>{nv._esc(vjs["d"])}</span>' if vjs.get("d") else "") + '</div>')
            inner = ('<div class="cover">' + vstamp + '<div class="big">Theo dõi để xem<br>mỗi ngày</div>'
                     '<div class="sub2">Tin AI nóng nhất, phân tích chuyên sâu hằng ngày</div></div>')
            segs_html.append(f'<section class="seg" id="{sid}">{inner}</section>')
            if vstamp:
                anim.append(f'    m.fromTo("#{sid}-vd",{{scale:0.7,opacity:0}},'
                            f'{{scale:1,opacity:1,duration:0.55,ease:"back.out(1.6)"}},0.3);')
            if tag == "L" and blk.get("caps_words"):   # long: karaoke như short
                _short_caps(blk, {}, t, dur, kcaps_html, anim, f"{sid}cap")
        else:
            sec_i += 1
            sid = f"{tag}sec-{sec_i}"
            if tag == "S":
                # ===== SHORT v3: SmartArt fill-bullet (TRÊN) + ẢNH lấp khung (DƯỚI) + caption word-level =====
                # AI chọn component qua diagram.type (cả palette: stats/bullets/tags/
                # process/bars/quote/bignum). Không hợp lệ -> fill-bullet từ points.
                sdiag = _norm_diagram(sec.get("diagram") or {})
                styp = (sdiag.get("type") or "").lower()
                if styp in nv.SHORT_PALETTE and sdiag.get("items"):
                    items = [_it(x) for x in list(sdiag["items"])[:4]]
                else:
                    styp = "bullets"
                    bd = _bullets_diagram(sec, max_n=3, max_len=56)
                    items = [_it(x) for x in (bd or {}).get("items", [])]
                sa_div, n_children = nv.short_card_block(styp, items, sid)
                smedia = _prep_media(sec, sec_i, json_dir, dur, tag)[:1]
                img_div = ""
                if smedia:
                    m0 = smedia[0]
                    if m0["kind"] == "clip":
                        img_div = (f'<div class="heroimg"><video id="{sid}-im" data-start="{t + 0.2:.2f}" '
                                   f'data-duration="{max(1.0, dur):.2f}" data-track-index="{track}" '
                                   f'src="{m0["src"]}" muted playsinline></video></div>')
                        track += 1
                    else:
                        img_div = f'<div class="heroimg"><img id="{sid}-im" src="{nv._esc(m0["src"])}"></div>'
                cls2 = "seg sec" if img_div else "seg sec noimg"
                chip = f'<span class="chip">PHẦN {sec_i}</span>'
                # AI chọn layout qua sec.layout ∈ {a,b,c}; thiếu -> xoay vòng để không đơn điệu.
                tpl = str(sec.get("layout") or "").lower()
                if tpl not in ("a", "b", "c"):
                    tpl = ("a", "b", "c")[(sec_i - 1) % 3]
                inner = (f'{chip}<div class="hl">{nv._esc(sec.get("title") or "")}</div>'
                         f'<div class="content tpl-{tpl}">{sa_div}{img_div}</div>')
                segs_html.append(f'<section class="{cls2}" id="{sid}">{inner}</section>')
                anim.append(f'    m.to("#{sid}",{{opacity:1,duration:0.45}},{t:.2f});')
                # BEAT-SYNC: cards hiện (trượt lên) RẢI theo nhịp đọc (mốc từ ASR), không dồn 1 lúc.
                _w = blk.get("caps_words") or []
                wspan = (_w[-1][2] if _w else max(0.6, dur - 0.6))
                n_it = max(1, n_children)
                for j in range(n_children):
                    rt = t + 0.45 + j / n_it * wspan * 0.55   # thẻ đầu hiện SỚM, các thẻ sau rải theo nhịp
                    anim.append(f'    m.fromTo("#{sid}-b{j}",{{opacity:0,y:26}},{{opacity:1,y:0,duration:0.4,ease:"power2.out"}},{rt:.2f});')
                if img_div and smedia[0]["kind"] == "image":
                    anim.append(f'    m.to("#{sid}-im",{{opacity:1,duration:0.45}},{t + 0.25:.2f});')
                    anim.append(f'    m.fromTo("#{sid}-im",{{scale:1.0}},{{scale:1.06,duration:{max(1.0, dur):.2f},ease:"none"}},{t + 0.45:.2f});')
                if t + dur < total - 0.1:
                    anim.append(f'    m.to("#{sid}",{{opacity:0,duration:0.45}},{t + dur - 0.45:.2f});')
                _short_caps(blk, sec, t, dur, kcaps_html, anim, f"{sid}cap")
                t += dur
                continue
            media = _prep_media(sec, sec_i, json_dir, dur, tag)[:1]  # v2: 1 ảnh hero liên quan nhất
            diag = sec.get("diagram")
            if tag == "S" and not diag:
                diag = _bullets_diagram(sec)   # SHORT: ý chính -> fill-bullet SmartArt (thay bullet text trơn)
            has_panel = bool(media or diag)
            cls = "seg sec" if has_panel else "seg sec nopanel"

            # ---- beat timing ----------------------------------------------
            # diagram window = [first diagram beat, end of section]
            diag_start = None
            if beats:
                for k, _i, off, _t in beats:
                    if k in ("dlead", "dstep"):
                        diag_start = off
                        break
            if diag and diag_start is None:
                if media:
                    diag_start = max(0.6, (dur - 0.5) * 0.62)   # ảnh hero hiện trước, SmartArt sau
                else:
                    # SHORT (không beats): hiện SmartArt SỚM để xem rõ cả section; LONG giữ cuối
                    diag_start = 0.6 if tag == "S" else max(0.6, dur - 0.5)
            med_end = (diag_start if diag else dur - 0.5)

            # ---- panel HTML -----------------------------------------------
            pitems = []
            n_med = len(media)
            for j, mitem in enumerate(media):
                mid = f"{sid}-m{j}"
                if mitem["kind"] == "clip":
                    share = max(1.0, (med_end - 0.3) / max(1, n_med))
                    st = t + 0.3 + j * share
                    pitems.append(
                        f'<video id="{mid}" data-start="{st:.2f}" data-duration="{share:.2f}" '
                        f'data-track-index="{track}" src="{mitem["src"]}" muted playsinline></video>')
                    track += 1
                else:
                    pitems.append(f'<img class="pitem" id="{mid}" src="{nv._esc(mitem["src"])}">')
            if diag:
                did = f"{sid}-d"
                pitems.append(f'<div class="pitem" id="{sid}-dg"><div class="diag" id="{did}">'
                              f'{diagram_html(diag, did)}</div></div>')
            panel = f'<div class="panel">{"".join(pitems)}</div>' if pitems else ""

            # ---- text column ----------------------------------------------
            # SHORT: SmartArt fill-bullet thay bullet text trơn -> KHÔNG render .bul nữa.
            bullets = _sec_bullets(sec, max_n=5, max_len=90) if tag == "L" else []
            bul_html = "".join(f'<li id="{sid}-b{j}">{nv._esc(b)}</li>' for j, b in enumerate(bullets))
            bul_div = f'<ul class="bul">{bul_html}</ul>' if bullets else ""
            chip = f'<span class="chip">PHẦN {sec_i}</span>'
            if tag == "L":
                inner = (f'{chip}<div class="txt"><div class="hl">{nv._esc(sec.get("title") or "")}</div>'
                         f'{bul_div}</div>{panel}')
            else:
                inner = (f'{chip}<div class="hl">{nv._esc(sec.get("title") or "")}</div>'
                         f'{bul_div}{panel}')
            segs_html.append(f'<section class="{cls}" id="{sid}">{inner}</section>')

            # ---- animations -----------------------------------------------
            if beats:
                # BEAT-SYNCED: each bullet/diagram step appears with its narration
                for k, idx, off, btext in beats:
                    at = t + off + 0.1
                    # transcript-bar cũ = FALLBACK khi không có ASR words (karaoke thay thế)
                    if btext and not blk.get("caps_words"):
                        caps_ev.append((t + off, btext))
                    if k == "point" and idx < len(bullets):
                        anim.append(f'    m.to("#{sid}-b{idx}",{{opacity:1,duration:0.45}},{at:.2f});')
                        # highlight the active line, dim it when the next starts
                        anim.append(f'    m.to("#{sid}-b{idx}",{{color:"#F0F0F5",duration:0.3}},{at:.2f});')
                    elif k == "dstep":
                        anim.append(f'    m.to("#{did}-s{idx}",{{opacity:1,y:0,duration:0.45}},{at:.2f});')
                if diag:
                    anim.append(f'    m.to("#{sid}-dg",{{opacity:1,duration:0.5}},{t + diag_start:.2f});')
                    # steps with no dedicated beat: reveal with the diagram itself
                    voiced = {i for k, i, _o, _t in beats if k == "dstep"}
                    for c in range(_diag_child_count(diag)):
                        if c not in voiced:
                            anim.append(f'    m.to("#{did}-s{c}",{{opacity:1,duration:0.4}},{t + diag_start + 0.4 + c * 0.3:.2f});')
            else:
                # fallback (v1 schema / short): stagger bullets, stagger diagram
                for j in range(len(bullets)):
                    anim.append(f'    m.to("#{sid}-b{j}",{{opacity:1,duration:0.45}},{t + 1.0 + j * 0.4:.2f});')
                if diag:
                    anim.append(f'    m.to("#{sid}-dg",{{opacity:1,duration:0.5}},{t + diag_start:.2f});')
                    for c in range(_diag_child_count(diag)):
                        anim.append(f'    m.to("#{did}-s{c}",{{opacity:1,duration:0.4}},{t + diag_start + 0.4 + c * 0.35:.2f});')
                # SHORT: phụ đề transcript từ narration_short — tách câu, canh giờ theo độ dài ký tự
                # (short synth cả section 1 block, không có beats nên ước lượng tuyến tính).
                if tag == "S":
                    chunks = _caption_chunks(sec.get("narration_short") or sec.get("lead") or "")
                    if chunks:
                        span = max(0.6, dur - 0.5)
                        total_ch = sum(len(c) for c in chunks) or 1
                        acc = 0.25
                        for c in chunks:
                            caps_ev.append((t + acc, c))
                            acc += span * (len(c) / total_ch)

            if tag == "L" and blk.get("caps_words"):   # long: karaoke word-level như short
                _short_caps(blk, sec, t, dur, kcaps_html, anim, f"{sid}cap")

            # media crossfade across the media window (images only; clips are timed)
            if n_med:
                share = (med_end - 0.3) / n_med
                for j, mitem in enumerate(media):
                    if mitem["kind"] == "clip":
                        continue
                    st = t + 0.3 + j * share
                    mid = f"{sid}-m{j}"
                    anim.append(f'    m.to("#{mid}",{{opacity:1,duration:0.6}},{st:.2f});')
                    anim.append(f'    m.fromTo("#{mid}",{{scale:1.0}},{{scale:1.07,duration:{share:.2f},ease:"none"}},{st:.2f});')
                    if j < n_med - 1 or diag:
                        anim.append(f'    m.to("#{mid}",{{opacity:0,duration:0.6}},{st + share:.2f});')

        anim.append(f'    m.to("#{sid}",{{opacity:1,duration:0.45}},{t:.2f});')
        if t + dur < total - 0.1:
            anim.append(f'    m.to("#{sid}",{{opacity:0,duration:0.45}},{t + dur - 0.45:.2f});')
        t += dur

    # transcript captions: each beat's spoken text shows until the next beat starts
    caps_ev.sort(key=lambda e: e[0])
    caps_html, cap_anim = [], []
    for i, (start, txt) in enumerate(caps_ev):
        end = caps_ev[i + 1][0] if i + 1 < len(caps_ev) else total
        cid = f"cap{i}"
        caps_html.append(f'<div class="c" id="{cid}">{nv._esc(txt)}</div>')
        cap_anim.append(f'    m.to("#{cid}",{{opacity:1,duration:0.22}},{start:.2f});')
        cap_anim.append(f'    m.to("#{cid}",{{opacity:0,duration:0.22}},{max(start + 0.4, end - 0.12):.2f});')
    if kcaps_html:
        # KARAOKE (short + long từ 20260707): tween từng từ đã nằm trong `anim`;
        # ghép thêm caps_html transcript-bar của các block ASR-fail (fallback).
        caps_html = kcaps_html + caps_html
    bg_html, bg_anim = _bg_dots(total=total)

    # Background grid/orbs: finite repeat counts that outlast the video. repeat:-1
    # (infinite) is unbounded and overflows HyperFrames' seek index ("Set maximum
    # size exceeded"), failing the render — see _bg_dots() for the full note.
    def _rep(dur):
        return int(((total or 600) + 20) // dur) + 1

    html = (head.replace("{ACSS}", _accent_css())
                .replace("{TOTAL}", str(total))
                .replace("{RGRID}", str(_rep(26)))
                .replace("{RORB1}", str(_rep(15)))
                .replace("{RORB2}", str(_rep(17)))
                .replace("{EPI}", nv._esc(story.get("_display", "")))
                .replace("{BA}", nv._esc(BRAND["a"])).replace("{BB}", nv._esc(BRAND["b"]))
                .replace("{BSITE}", nv._esc(BRAND["site"]))
                .replace("{BG}", bg_html)
                .replace("{BGANIM}", bg_anim)
                .replace("{CAPS}", "\n  ".join(caps_html))
                .replace("{SEGS}", "\n  ".join(segs_html))
                .replace("{ANIM}", "\n".join(anim + cap_anim)))
    return html


def _render(html, out_path, voice, sr, silent_name, timeout=3600):
    """Ghi index.html → render câm (có thử lại) → ghép giọng. Trả out_path.

    Vòng thử lại nằm trong `render.render_project`: HyperFrames chạy nhiều worker Chromium,
    short render NGAY SAU long dễ chết vì tranh RAM/handle lúc long chưa giải phóng hết —
    hỏng thoáng qua, chạy lại là qua; và stderr của HyperFrames LUÔN được in ra log.
    """
    proj = _proj()
    render.write_index(proj, html)
    silent = os.path.join(proj, silent_name)
    render.render_project(proj, silent, timeout=timeout, label="top-story")
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


def _voice_track(blocks, sr, pad):
    parts = []
    for blk in blocks:
        parts.append(blk["audio"])
        parts.append(np.zeros(int(sr * pad), dtype=np.float32))
    return np.concatenate(parts)


def make_long(story, out_path, model, prompt, json_dir):
    sr = model.sampling_rate
    pad = 0.8
    sections = story.get("sections") or []
    if not sections:
        raise ValueError("top_story.sections is empty")
    media_dir = os.path.join(_proj(), "media")
    if os.path.isdir(media_dir):
        shutil.rmtree(media_dir, ignore_errors=True)

    print("  [long] synthesizing narration (beat-synced) ...", flush=True)
    blocks = []
    _intro_txt = story.get("intro") or story.get("headline", "")
    a = nv._synth_long(model, _intro_txt, prompt)
    blocks.append({"kind": "intro", "audio": a, "dur": len(a) / sr + pad, "beats": None,
                   # chữ karaoke = TEXT GỐC (giờ mượn ASR). Trước đây hiển thị thẳng chữ
                   # Whisper phiên âm ngược từ chính audio này -> sai chính tả nung vào video.
                   "caps_words": nv._words_from_text(a, sr, _intro_txt)})
    for i, sec in enumerate(sections, 1):
        audio, raw_dur, beats = _synth_section_beats(model, sec, prompt, sr)
        # dur MUST be len(audio)/sr + pad — _voice_track appends `pad` of silence
        # after every block, so any other value drifts A/V by the difference.
        blocks.append({"kind": "sec", "sec": sec, "audio": audio,
                       "dur": raw_dur + pad, "beats": beats,
                       "caps_words": nv._words_from_text(
                           audio, sr, " ".join(b[3] for b in beats))})
        print(f"  [long] section {i}: {len(beats)} beats, ~{raw_dur:.0f}s", flush=True)
    _outro_txt = story.get("outro") or "Cảm ơn bạn đã theo dõi."
    a = nv._synth_long(model, _outro_txt, prompt)
    blocks.append({"kind": "outro", "audio": a, "dur": len(a) / sr + pad, "beats": None,
                   "caps_words": nv._words_from_text(a, sr, _outro_txt)})
    total = round(sum(b["dur"] for b in blocks), 2)
    print(f"  [long] total ~{total:.0f}s", flush=True)

    # chapters sidecar
    chapters, tcur = [], 0.0
    for blk in blocks:
        if blk["kind"] == "intro":
            chapters.append({"t": 0, "label": "Mở đầu"})
        elif blk["kind"] == "outro":
            chapters.append({"t": round(tcur), "label": "Kết"})
        else:
            chapters.append({"t": round(tcur), "label": blk["sec"].get("title", "")})
        tcur += blk["dur"]
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path + ".chapters.json", "w", encoding="utf-8") as f:
        json.dump(chapters, f, ensure_ascii=False, indent=1)

    html = _build(story, blocks, total, _LONG_HEAD, json_dir, "L")
    print("  [long] rendering (HyperFrames) ...", flush=True)
    return _render(html, out_path, _voice_track(blocks, sr, pad), sr, "_silent_long.mp4")


def make_short(story, out_path, model, prompt, json_dir):
    sr = model.sampling_rate
    pad = 0.6
    sections = story.get("sections") or []
    if not sections:
        raise ValueError("top_story.sections is empty")

    print("  [short] synthesizing narration ...", flush=True)
    blocks = []
    media_dir = os.path.join(_proj(), "media")
    os.makedirs(media_dir, exist_ok=True)
    headline_kw = (story.get("image_query") or story.get("headline") or "technology").strip()
    intro = story.get("intro_short") or f"{story.get('headline', '')}. Đây là tin AI nóng nhất hôm nay."
    a = nv._synth_long(model, intro, prompt)
    blocks.append({"kind": "intro", "audio": a, "dur": len(a) / sr + pad, "beats": None,
                   "caps_words": nv._words_from_text(a, sr, intro)})
    for i, sec in enumerate(sections, 1):
        lead = sec.get("lead") or sec.get("narration") or ""
        first = nv._SENT_RE.split(lead.strip())[0] if lead.strip() else ""
        spoken = sec.get("narration_short") or f"{sec.get('title', '')}. {first}"
        a = nv._synth_long(model, spoken, prompt)
        slim = dict(sec)
        med = sec.get("media") or []
        if isinstance(med, (dict, str)):  # schema drift: object đơn/chuỗi -> bọc list
            med = [med]
        slim["media"] = med[:1]
        # GIỮ diagram: section `stats` -> stat-card số to (escbase); type khác -> fill-bullet từ points.
        # FRAME-FILL: section KHÔNG có ảnh -> tải 1 ảnh B-ROLL (Openverse) lấp khung, tránh ô trống.
        # Openverse tìm theo TIẾNG ANH: rút token latin (entity) từ headline/title + fallback generic.
        if not slim["media"]:
            # Ưu tiên FILLER on-brand tự chuẩn bị (assets/news_short/fillers/), rồi mới b-roll Openverse.
            local = nv._local_filler(i, brand_key=BRAND.get("filler_pool", ""))
            if local:
                slim["media"] = [{"type": "image", "src": local}]
            else:
                bp = os.path.join(media_dir, f"broll_S{i}.jpg")
                qprimary = (sec.get("image_query") or "").strip()   # research cấp (tiếng Anh) nếu có
                rot = BROLL_QUERIES[(i - 1) % len(BROLL_QUERIES)]
                for q in [x for x in (qprimary, rot, BROLL_FALLBACK) if x]:
                    if nv._broll_image(q, bp):
                        slim["media"] = [{"type": "image", "src": bp}]
                        break
        nv.asr_drift_warn(nv._asr_words(a, sr), spoken, label=f"short PHẦN {i}")  # lưới an toàn
        words = nv._words_from_text(a, sr, spoken)   # phụ đề word-level, CHỮ GỐC
        blocks.append({"kind": "sec", "sec": slim, "audio": a,
                       "dur": len(a) / sr + pad, "beats": None, "caps_words": words})
        print(f"  [short] section {i} ok ({len(a)/sr:.0f}s, {len(words)} words)", flush=True)
    _outro_s = story.get("outro_short") or "Theo dõi để xem tin AI nóng nhất mỗi ngày."
    a = nv._synth_long(model, _outro_s, prompt)
    blocks.append({"kind": "outro", "audio": a, "dur": len(a) / sr + pad, "beats": None,
                   "caps_words": nv._words_from_text(a, sr, _outro_s)})
    total = round(sum(b["dur"] for b in blocks), 2)
    print(f"  [short] total ~{total:.0f}s", flush=True)

    html = _build(story, blocks, total, _SHORT_HEAD, json_dir, "S")
    print("  [short] rendering (HyperFrames) ...", flush=True)
    return _render(html, out_path, _voice_track(blocks, sr, pad), sr, "_silent_short.mp4",
                   timeout=1800)


def _apply_branding(b):
    """Nạp thương hiệu cho tiến trình này từ spec (hoặc một edition của batch).

    KHÔNG có đường lùi: template không mang thương hiệu nào sẵn, thiếu a/b/site ⇒ mã 2.
    Giá trị rỗng trong `b` coi như không khai (để --brand-a "" không xoá giá trị đã nạp).
    """
    given = {k: v for k, v in (b or {}).items() if str(v or "").strip()}
    merged = nv.resolve_brand({**BRAND_DEFAULTS, **BRAND, **given})
    BRAND.clear()
    BRAND.update(merged)


def _render_one(json_path, out_dir, date, model, prompt, long_only=False, short_only=False):
    """Render 1 edition (long+short) bằng model+prompt ĐÃ load sẵn (tái dùng cho batch)."""
    with open(json_path, encoding="utf-8-sig") as f:
        d = json.load(f)
    story = d.get("top_story") or d
    if not story.get("sections"):
        raise SystemExit(f"ERROR: top_story.sections missing in {json_path}")
    story["_display"] = d.get("display_date") or _vn_display(date)
    if d.get("verdict") and not story.get("verdict"):   # verdict-stamp: JSON để top-level
        story["verdict"] = d["verdict"]
    if d.get("repo"):                                   # hook-orb-badge trên cover (repo flow)
        story["_repo"] = d["repo"]
    json_dir = os.path.dirname(os.path.abspath(json_path))
    os.makedirs(out_dir, exist_ok=True)
    long_out = os.path.join(out_dir, f"{date}-top.mp4")
    short_out = os.path.join(out_dir, f"{date}-top-short.mp4")
    print(f"[top-story] {date} · {len(story['sections'])} sections", flush=True)
    if not short_only:
        if os.path.isfile(long_out):
            print(f"[top-story] long exists, reused -> {long_out}", flush=True)
        else:
            make_long(story, long_out, model, prompt, json_dir)
            print(f"[top-story] long -> {long_out} ({os.path.getsize(long_out)//1024} KB)", flush=True)
    if not long_only:
        if os.path.isfile(short_out):
            print(f"[top-story] short exists, reused -> {short_out}", flush=True)
        else:
            make_short(story, short_out, model, prompt, json_dir)
            print(f"[top-story] short -> {short_out} ({os.path.getsize(short_out)//1024} KB)", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default="")
    ap.add_argument("--out-dir", default="")
    ap.add_argument("--date", default="")
    ap.add_argument("--profile", default="",
                    help="Tên profile giọng (rỗng = profile mặc định của trạm giọng).")
    ap.add_argument("--long-only", action="store_true")
    ap.add_argument("--short-only", action="store_true")
    ap.add_argument("--brand-a", default="")
    ap.add_argument("--brand-b", default="")
    ap.add_argument("--kicker", default="")
    ap.add_argument("--site", default="")
    ap.add_argument("--batch", default="",
                    help="(B) JSON manifest [{json,out_dir,date,branding:{a,b,kicker,site},short_only?}] "
                         "— render NHIỀU edition (ai+data / daily+weekly) trong 1 process = load model 1 LẦN.")
    args = ap.parse_args()

    model = engine.load()
    prompt = (profiles.get_clone_prompt(model, args.profile or None) or
              profiles.get_clone_prompt(model, profiles.ensure_default(model)))
    print(f"[top-story] voice: {args.profile or profiles.get_default()}", flush=True)

    if args.batch:
        with open(args.batch, encoding="utf-8-sig") as f:
            editions = json.load(f)
        print(f"[top-story] BATCH {len(editions)} edition(s) — 1 lần load model.", flush=True)
        for ed in editions:
            _apply_branding(ed.get("branding"))
            _render_one(ed["json"], ed["out_dir"], ed["date"], model, prompt,
                        ed.get("long_only", False), ed.get("short_only", False))
        print("[top-story] BATCH DONE", flush=True)
        return 0

    if not (args.json and args.out_dir and args.date):
        raise SystemExit("ERROR: cần --json/--out-dir/--date (hoặc --batch <manifest>).")
    _apply_branding({"a": args.brand_a, "b": args.brand_b, "kicker": args.kicker, "site": args.site})
    _render_one(args.json, args.out_dir, args.date, model, prompt, args.long_only, args.short_only)
    print("[top-story] DONE", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
