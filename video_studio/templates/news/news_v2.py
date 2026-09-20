# -*- coding: utf-8 -*-
"""news_v2.py — bản tin v2 kiểu infographic (escbase-style) + nền động "công nghệ"
(hạt sáng trôi + lưới mờ, GSAP-driven nên HyperFrames render đúng từng frame) + phụ đề
transcript đồng bộ giọng đọc. Đây là seed cho việc nâng news_video.py lên v2.

render_story(item, out_path, ...) — dựng 1 slide layout 'stat' cho 1 tin.
  item = {eyebrow, headline, headline_accent, big, big_label,
          rows:[{ic,k,v,c}], hero_image(url|None), narration}
"""
from __future__ import annotations
import os
import numpy as np
import soundfile as sf

from voice_studio import av, engine

from ... import render
from .news_video import _esc, _proj, _SENT_RE, _tts_normalize, resolve_brand

ACCENTS = ["#00E5FF", "#A78BFA", "#F472B6", "#60A5FA", "#00E676", "#FFC857"]


def _dots(n=34):
    """Vị trí hạt nền tất định (LCG, không Math.random để render ổn định mỗi frame)."""
    s = 12345
    out = []
    for i in range(n):
        s = (1103515245 * s + 12345) & 0x7FFFFFFF
        x = (s % 1000) / 10.0
        s = (1103515245 * s + 12345) & 0x7FFFFFFF
        y = (s % 1000) / 10.0
        s = (1103515245 * s + 12345) & 0x7FFFFFFF
        sz = 2 + s % 4
        col = ["#00E5FF", "#A78BFA", "#00E676"][i % 3]
        out.append((x, y, sz, col, (i % 7) * 0.5, 18 + (i % 9) * 3))
    return out


def _caption_blocks(model, narration, voice_profile, gap=0.16):
    """Synth từng câu, trả (audio_full, dur_full, cues[(start,end,text)])."""
    sr = model.sampling_rate
    text = _tts_normalize((narration or "").strip())
    sents = [s.strip() for s in _SENT_RE.split(text) if s.strip()] or [text]
    parts, cues, t = [], [], 0.0
    sil = np.zeros(int(sr * gap), dtype=np.float32)
    for s in sents:
        a = np.asarray(engine.synth(s, prompt=voice_profile or None, language="Vietnamese",
                                    model=model)[0], dtype=np.float32)
        d = len(a) / sr
        cues.append((round(t, 2), round(t + d + gap, 2), s))
        t += d + gap
        parts.append(a)
        parts.append(sil)
    audio = np.concatenate(parts) if parts else np.zeros(int(sr * 0.2), dtype=np.float32)
    return audio, t, cues


_TPL = """<!doctype html>
<html lang="vi" data-resolution="landscape"><head><meta charset="UTF-8"/>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>
 html,body{{margin:0;width:1920px;height:1080px;overflow:hidden;font-family:__FONT__}}
 #master-root{{width:1920px;height:1080px;position:relative;color:#F0F0F5;
   background:radial-gradient(1500px 900px at 78% 8%,#15203a 0%,#0a0d18 55%,#070a12 100%)}}
 .grid{{position:absolute;inset:-200px;opacity:.32;pointer-events:none;
   background-image:linear-gradient(rgba(255,255,255,.05) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.05) 1px,transparent 1px);
   background-size:96px 96px}}
 .orb{{position:absolute;border-radius:50%;filter:blur(70px);opacity:.22;pointer-events:none}}
 .dot{{position:absolute;border-radius:50%;pointer-events:none}}
 .brand{{position:absolute;top:48px;left:84px;display:flex;align-items:center;gap:14px;z-index:6}}
 .brand .mk{{width:46px;height:46px;border-radius:12px;background:linear-gradient(135deg,#00E5FF,#2563eb);box-shadow:0 0 20px rgba(0,229,255,.5)}}
 .brand .n{{font-weight:800;font-size:28px}} .brand .n span{{color:#00E5FF}}
 .epi{{position:absolute;top:56px;right:84px;color:#A0A0B0;font-size:24px;z-index:6}}
 .wrap{{position:absolute;left:84px;right:84px;top:200px;z-index:5}}
 .eyebrow{{display:inline-flex;align-items:center;gap:10px;padding:9px 22px;border-radius:999px;
   background:rgba(0,229,255,.08);border:1px solid rgba(0,229,255,.35);color:#00E5FF;font-size:24px;font-weight:700;opacity:0}}
 h1.t{{font-size:84px;font-weight:900;line-height:1.06;margin:22px 0 8px;max-width:1200px;opacity:0}}
 h1.t .g{{background:linear-gradient(90deg,#00E5FF,#A78BFA,#F472B6);-webkit-background-clip:text;background-clip:text;color:transparent}}
 .stat{{display:flex;gap:54px;align-items:center;margin-top:30px;opacity:0}}
 .stat .big{{font-size:150px;font-weight:900;line-height:1;background:linear-gradient(180deg,#fff,#00E5FF);-webkit-background-clip:text;background-clip:text;color:transparent}}
 .stat .lab{{font-size:34px;color:#A0A0B0;max-width:560px;line-height:1.3}}
 .spec{{margin-top:26px;max-width:980px;border-top:1px solid #2A2A3A}}
 .spec .row{{display:grid;grid-template-columns:60px 280px 1fr;align-items:center;gap:10px;padding:20px 6px;border-bottom:1px solid #2A2A3A;opacity:0}}
 .spec .ic{{width:40px;height:40px;border-radius:10px;display:grid;place-items:center;font-size:20px}}
 .spec .k{{font-size:22px;font-weight:800;letter-spacing:1px}}
 .spec .v{{font-size:30px;font-weight:700}}
 .hero{{position:absolute;right:84px;top:210px;width:360px;height:360px;border-radius:22px;object-fit:cover;
   border:1px solid #2A2A3A;box-shadow:0 30px 80px rgba(0,0,0,.55);opacity:0;z-index:5}}
 .cap{{position:absolute;left:0;right:0;bottom:60px;text-align:center;z-index:7}}
 .cap .c{{position:absolute;left:50%;bottom:0;transform:translateX(-50%);max-width:1380px;opacity:0;
   background:rgba(7,10,18,.74);border:1px solid #2A2A3A;border-radius:16px;padding:16px 30px;font-size:30px;line-height:1.34;color:#eaf2ff}}
 #prog{{position:absolute;bottom:0;left:0;height:9px;width:0%;background:linear-gradient(90deg,#00E5FF,#A78BFA);z-index:9}}
</style></head>
<body>
<div id="master-root" data-composition-id="master" data-width="1920" data-height="1080" data-start="0" data-duration="{TOTAL}">
  <div class="grid" id="grid"></div>
  <div class="orb" id="orb1" style="width:520px;height:520px;left:-120px;top:120px;background:#00E5FF"></div>
  <div class="orb" id="orb2" style="width:460px;height:460px;right:-80px;bottom:-60px;background:#A78BFA"></div>
  {DOTS}
  <div class="brand"><span class="mk"></span><div class="n">{BA} <span>{BB}</span></div></div>
  <div class="epi">{EPI}</div>
  {HERO}
  <div class="wrap">
    <span class="eyebrow" id="eb">{EYEBROW}</span>
    <h1 class="t" id="ti">{HEADLINE}</h1>
    <div class="stat" id="st"><div class="big">{BIG}</div><div class="lab">{BIGLAB}</div></div>
    <div class="spec">{ROWS}</div>
  </div>
  <div class="cap">{CAPS}</div>
  <div id="prog"></div>
  <script>
   window.__timelines=window.__timelines||{{}};
   var m=gsap.timeline({{paused:true}});
   m.fromTo("#prog",{{width:"0%"}},{{width:"100%",duration:{TOTAL},ease:"none"}},0);
   // tech bg (GSAP-driven => deterministic per frame)
   m.fromTo("#grid",{{x:0,y:0}},{{x:-96,y:-96,duration:24,repeat:-1,ease:"none"}},0);
   m.to("#orb1",{{x:120,y:-60,duration:14,repeat:-1,yoyo:true,ease:"sine.inOut"}},0);
   m.to("#orb2",{{x:-100,y:40,duration:16,repeat:-1,yoyo:true,ease:"sine.inOut"}},0);
{DOTANIM}
   // content reveal
   m.to("#eb",{{opacity:1,duration:0.5}},0.3);
   m.fromTo("#ti",{{opacity:0,y:40}},{{opacity:1,y:0,duration:0.7,ease:"power2.out"}},0.6);
   m.fromTo("#st",{{opacity:0,y:30}},{{opacity:1,y:0,duration:0.7,ease:"power2.out"}},1.1);
   m.to(".hero",{{opacity:1,duration:0.7}},1.0);
{ROWANIM}
{CAPANIM}
   window.__timelines["master"]=m;
  </script>
</div></body></html>
"""


# ===================== DEEP-DIVE (đa cảnh) =====================
# CSS dùng SINGLE brace (KHÔNG đưa qua .format) — tránh bẫy doubled-brace.
V2_CSS = """<style>
 html,body{margin:0;width:1920px;height:1080px;overflow:hidden;font-family:__FONT__}
 #master-root{width:1920px;height:1080px;position:relative;color:#F0F0F5;
   background:radial-gradient(1500px 900px at 78% 8%,#15203a 0%,#0a0d18 55%,#070a12 100%)}
 .grid{position:absolute;inset:-200px;opacity:.30;pointer-events:none;
   background-image:linear-gradient(rgba(255,255,255,.05) 1px,transparent 1px),linear-gradient(90deg,rgba(255,255,255,.05) 1px,transparent 1px);background-size:96px 96px}
 .orb{position:absolute;border-radius:50%;filter:blur(72px);opacity:.20;pointer-events:none}
 .dot{position:absolute;border-radius:50%;pointer-events:none}
 .brand{position:absolute;top:48px;left:84px;display:flex;align-items:center;gap:14px;z-index:8}
 .brand .mk{width:46px;height:46px;border-radius:12px;background:linear-gradient(135deg,#00E5FF,#2563eb);box-shadow:0 0 20px rgba(0,229,255,.5)}
 .brand .n{font-weight:800;font-size:28px}.brand .n span{color:#00E5FF}
 .epi{position:absolute;top:56px;right:84px;color:#A0A0B0;font-size:24px;z-index:8}
 .scene{position:absolute;left:84px;right:84px;top:190px;opacity:0}
 .eyebrow{display:inline-flex;align-items:center;gap:10px;padding:9px 22px;border-radius:999px;
   background:rgba(0,229,255,.08);border:1px solid rgba(0,229,255,.35);color:#00E5FF;font-size:24px;font-weight:700}
 h1.t{font-size:78px;font-weight:900;line-height:1.06;margin:20px 0 6px;max-width:1300px}
 h1.t .g{background:linear-gradient(90deg,#00E5FF,#A78BFA,#F472B6);-webkit-background-clip:text;background-clip:text;color:transparent}
 .stat{display:flex;gap:54px;align-items:center;margin-top:26px}
 .stat .big{font-size:140px;font-weight:900;line-height:1;background:linear-gradient(180deg,#fff,#00E5FF);-webkit-background-clip:text;background-clip:text;color:transparent}
 .stat .lab{font-size:32px;color:#A0A0B0;max-width:520px;line-height:1.3}
 .spec{margin-top:22px;max-width:980px;border-top:1px solid #2A2A3A}
 .spec .row{display:grid;grid-template-columns:60px 270px 1fr;align-items:center;gap:10px;padding:16px 6px;border-bottom:1px solid #2A2A3A}
 .spec .ic{width:40px;height:40px;border-radius:10px;display:grid;place-items:center;font-size:20px}
 .spec .k{font-size:21px;font-weight:800;letter-spacing:1px}.spec .v{font-size:28px;font-weight:700}
 .cards{display:grid;grid-template-columns:repeat(3,1fr);gap:26px;margin-top:40px}
 .card{background:#1A1A24;border:1px solid #2A2A3A;border-radius:20px;padding:32px;opacity:0}
 .card .ci{width:62px;height:62px;border-radius:15px;display:grid;place-items:center;font-size:30px;margin-bottom:20px}
 .card h3{font-size:32px;font-weight:800;margin:0 0 12px}.card p{font-size:24px;color:#A0A0B0;line-height:1.42;margin:0}
 .hero{position:absolute;right:84px;top:200px;width:340px;height:340px;border-radius:22px;object-fit:cover;border:1px solid #2A2A3A;box-shadow:0 30px 80px rgba(0,0,0,.55)}
 .cover{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center}
 .cover .big{font-size:104px;font-weight:900}.cover .big span{color:#00E5FF}
 .cover .sub{font-size:38px;color:#A0A0B0;margin-top:22px}.cover .sub2{font-size:28px;color:#6B6B7B;margin-top:14px}
 .cap{position:absolute;left:0;right:0;bottom:56px;text-align:center;z-index:9;height:90px}
 .cap .c{position:absolute;left:50%;bottom:0;transform:translateX(-50%);max-width:1400px;opacity:0;
   background:rgba(7,10,18,.74);border:1px solid #2A2A3A;border-radius:16px;padding:14px 30px;font-size:29px;line-height:1.34;color:#eaf2ff}
 #prog{position:absolute;bottom:0;left:0;height:9px;width:0%;background:linear-gradient(90deg,#00E5FF,#A78BFA);z-index:10}
</style>"""


def _sc_inner(sc):
    """Inner HTML của 1 scene theo layout."""
    L = sc.get("layout")
    if L == "cover":
        return (f'<div class="cover"><div class="big">{_esc(sc.get("big_a",""))} '
                f'<span>{_esc(sc.get("big_b",""))}</span></div>'
                f'<div class="sub">{_esc(sc.get("sub",""))}</div>'
                f'<div class="sub2">{_esc(sc.get("sub2",""))}</div></div>')
    if L == "outro":
        return (f'<div class="cover"><div class="big">{_esc(sc.get("big",""))}</div>'
                f'<div class="sub">{_esc(sc.get("sub",""))}</div>'
                f'<div class="sub2">{_esc(sc.get("sub2",""))}</div></div>')
    if L == "stat":
        hl = _esc(sc.get("headline", ""))
        if sc.get("headline_accent"):
            hl = hl.replace(_esc(sc["headline_accent"]), f'<span class="g">{_esc(sc["headline_accent"])}</span>')
        rows = ""
        for j, r in enumerate(sc.get("rows", [])):
            c = r.get("c", ACCENTS[j % len(ACCENTS)])
            rows += (f'<div class="row"><span class="ic" style="background:{c}22;color:{c}">{_esc(r.get("ic","◈"))}</span>'
                     f'<span class="k" style="color:{c}">{_esc(r.get("k",""))}</span>'
                     f'<span class="v">{_esc(r.get("v",""))}</span></div>')
        hero = f'<img class="hero" src="{_esc(sc["hero_image"])}">' if sc.get("hero_image") else ""
        return (f'{hero}<span class="eyebrow">{_esc(sc.get("eyebrow",""))}</span>'
                f'<h1 class="t">{hl}</h1>'
                f'<div class="stat"><div class="big">{_esc(sc.get("big",""))}</div>'
                f'<div class="lab">{_esc(sc.get("big_label",""))}</div></div>'
                f'<div class="spec">{rows}</div>')
    # pillars (default)
    cards = ""
    for j, it in enumerate(sc.get("items", [])):
        c = it.get("c", ACCENTS[j % len(ACCENTS)])
        cards += (f'<div class="card" data-card><div class="ci" style="background:{c}22;color:{c}">{_esc(it.get("ic","◆"))}</div>'
                  f'<h3>{_esc(it.get("title",""))}</h3><p>{_esc(it.get("desc",""))}</p></div>')
    return (f'<span class="eyebrow">{_esc(sc.get("eyebrow",""))}</span>'
            f'<h1 class="t">{_esc(sc.get("heading",""))}</h1>'
            f'<div class="cards">{cards}</div>')


def render_deepdive(scenes, out_path, epi="", model=None, voice_profile=None, brand=None):
    """Dựng video deep-dive nhiều cảnh (1 composition, nền động persist, phụ đề sync)."""
    brand = resolve_brand(brand)
    model = model or engine.load()
    sr = model.sampling_rate
    pad = 0.5

    # 1) narration per scene -> audio + cues (global timeline)
    blocks, total = [], 0.0
    for sc in scenes:
        a, d, cues = _caption_blocks(model, sc.get("narration", ""), voice_profile)
        blocks.append({"sc": sc, "audio": a, "start": total, "dur": d, "cues": cues})
        total += d + pad
    total = round(total, 2)

    # 2) bg dots
    dots_html, anim = [], []
    for i, (x, y, sz, col, dly, drift) in enumerate(_dots()):
        dots_html.append(f'<div class="dot" id="d{i}" style="left:{x:.1f}%;top:{y:.1f}%;width:{sz}px;'
                         f'height:{sz}px;background:{col};opacity:.5;box-shadow:0 0 8px {col}"></div>')
        anim.append(f'm.to("#d{i}",{{y:"-=40",x:"+=18",opacity:.14,duration:{drift},repeat:-1,yoyo:true,ease:"sine.inOut"}},{dly:.1f});')

    # 3) scenes html + animations
    secs, caps = [], []
    for k, b in enumerate(blocks):
        sid = f"sc{k}"
        secs.append(f'<section class="scene" id="{sid}">{_sc_inner(b["sc"])}</section>')
        st, en = b["start"], b["start"] + b["dur"]
        anim.append(f'm.to("#{sid}",{{opacity:1,duration:0.5}},{st:.2f});')
        if k < len(blocks) - 1:
            anim.append(f'm.to("#{sid}",{{opacity:0,duration:0.45}},{en:.2f});')
        # stagger pillar cards
        anim.append(f'm.to("#{sid} [data-card]",{{opacity:1,duration:0.45,stagger:0.18}},{st+0.4:.2f});')
        # captions (per sentence) on global timeline
        for (ca, cb, txt) in b["cues"]:
            cid = f"cap{len(caps)}"
            caps.append(f'<div class="c" id="{cid}">{_esc(txt)}</div>')
            g0, g1 = b["start"] + ca, b["start"] + cb
            anim.append(f'm.to("#{cid}",{{opacity:1,duration:0.22}},{g0:.2f});')
            anim.append(f'm.to("#{cid}",{{opacity:0,duration:0.22}},{max(g0+0.3,g1-0.12):.2f});')

    head = (f'<!doctype html><html lang="vi" data-resolution="landscape"><head><meta charset="UTF-8"/>'
            f'<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800;900&display=swap" rel="stylesheet">'
            f'<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>{V2_CSS}</head><body>')
    body = (f'<div id="master-root" data-composition-id="master" data-width="1920" data-height="1080" '
            f'data-start="0" data-duration="{total}">'
            f'<div class="grid" id="grid"></div>'
            f'<div class="orb" id="orb1" style="width:520px;height:520px;left:-120px;top:120px;background:#00E5FF"></div>'
            f'<div class="orb" id="orb2" style="width:460px;height:460px;right:-80px;bottom:-60px;background:#A78BFA"></div>'
            + "".join(dots_html)
            + f'<div class="brand"><span class="mk"></span><div class="n">{_esc(brand["a"])} '
              f'<span>{_esc(brand["b"])}</span></div></div>'
            + f'<div class="epi">{_esc(epi)}</div>'
            + "".join(secs)
            + f'<div class="cap">{"".join(caps)}</div><div id="prog"></div>')
    # script: literal JS braces are SINGLE here (plain string, not f-string-substituted region)
    bg_anim = ('m.fromTo("#grid",{x:0,y:0},{x:-96,y:-96,duration:24,repeat:-1,ease:"none"},0);'
               'm.to("#orb1",{x:120,y:-60,duration:14,repeat:-1,yoyo:true,ease:"sine.inOut"},0);'
               'm.to("#orb2",{x:-100,y:40,duration:16,repeat:-1,yoyo:true,ease:"sine.inOut"},0);')
    script = ('<script>window.__timelines=window.__timelines||{};'
              'var m=gsap.timeline({paused:true});'
              f'm.fromTo("#prog",{{width:"0%"}},{{width:"100%",duration:{total},ease:"none"}},0);'
              + bg_anim + "".join(anim)
              + 'window.__timelines["master"]=m;</script>')
    html = head + body + script + "</div></body></html>"

    proj = _proj()
    render.write_index(proj, html)
    silent = os.path.join(proj, "_silent_dd.mp4")
    print(f"[v2dd] {len(scenes)} cảnh ~{total:.0f}s — render ...")
    render.render_project(proj, silent, timeout=1800, label="deep-dive")

    parts = []
    for b in blocks:
        parts.append(b["audio"])
        parts.append(np.zeros(int(sr * pad), dtype=np.float32))
    voice = np.concatenate(parts)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    tmp = out_path + ".__v.wav"
    sf.write(tmp, voice, sr)
    try:
        av.mux(silent, tmp, out_path, mode="fit")
    finally:
        for p in (tmp, silent):
            try:
                os.remove(p)
            except OSError:
                pass
    print(f"[v2dd] done -> {out_path}")
    return out_path


def render_story(item, out_path, date="", model=None, voice_profile=None, brand=None):
    brand = resolve_brand(brand)
    model = model or engine.load()
    sr = model.sampling_rate

    # 1) narration + caption cues
    audio, dur, cues = _caption_blocks(model, item.get("narration", ""), voice_profile)
    total = round(dur + 1.2, 2)

    # 2) bg dots html + anim
    dots_html, dot_anim = [], []
    for i, (x, y, sz, col, dly, drift) in enumerate(_dots()):
        dots_html.append(f'<div class="dot" id="d{i}" style="left:{x:.1f}%;top:{y:.1f}%;'
                         f'width:{sz}px;height:{sz}px;background:{col};opacity:.55;'
                         f'box-shadow:0 0 8px {col}"></div>')
        dot_anim.append(f'   m.to("#d{i}",{{y:"-=40",x:"+=18",opacity:.15,duration:{drift},'
                        f'repeat:-1,yoyo:true,ease:"sine.inOut"}},{dly:.1f});')

    # 3) spec rows
    rows_html, row_anim = [], []
    for j, r in enumerate(item.get("rows", [])):
        c = r.get("c", ACCENTS[j % len(ACCENTS)])
        rows_html.append(
            f'<div class="row" id="r{j}"><span class="ic" style="background:{c}22;color:{c}">{_esc(r.get("ic","◈"))}</span>'
            f'<span class="k" style="color:{c}">{_esc(r.get("k",""))}</span>'
            f'<span class="v">{_esc(r.get("v",""))}</span></div>')
        row_anim.append(f'   m.to("#r{j}",{{opacity:1,duration:0.4}},{1.5 + j*0.25:.2f});')

    # 4) caption blocks timed to narration
    caps_html, cap_anim = [], []
    for k, (a, b, txt) in enumerate(cues):
        caps_html.append(f'<div class="c" id="cap{k}">{_esc(txt)}</div>')
        cap_anim.append(f'   m.to("#cap{k}",{{opacity:1,duration:0.25}},{a:.2f});')
        cap_anim.append(f'   m.to("#cap{k}",{{opacity:0,duration:0.25}},{max(a+0.3,b-0.15):.2f});')

    hero = (f'<img class="hero" src="{_esc(item["hero_image"])}">'
            if item.get("hero_image") else "")
    headline = item.get("headline", "")
    if item.get("headline_accent"):
        headline = headline.replace(item["headline_accent"],
                                    f'<span class="g">{_esc(item["headline_accent"])}</span>')
    else:
        headline = _esc(headline)

    # NB: _TPL uses doubled braces for literal CSS/JS, single braces for fields -> use .format()
    html = _TPL.format(
        TOTAL=total,
        EPI=_esc(item.get("eyebrow_epi", date)),
        DOTS="\n  ".join(dots_html),
        HERO=hero,
        BA=_esc(brand["a"]),
        BB=_esc(brand["b"]),
        EYEBROW=_esc(item.get("eyebrow", "")),
        HEADLINE=headline,
        BIG=_esc(item.get("big", "")),
        BIGLAB=_esc(item.get("big_label", "")),
        ROWS="\n    ".join(rows_html),
        CAPS="\n    ".join(caps_html),
        DOTANIM="\n".join(dot_anim),
        ROWANIM="\n".join(row_anim),
        CAPANIM="\n".join(cap_anim),
    )

    proj = _proj()
    render.write_index(proj, html)
    silent = os.path.join(proj, "_silent_v2.mp4")
    print(f"[v2] render slide ~{total:.0f}s ...")
    render.render_project(proj, silent, timeout=900, label="slide")

    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    tmp = out_path + ".__v.wav"
    sf.write(tmp, audio, sr)
    try:
        av.mux(silent, tmp, out_path, mode="fit")
    finally:
        for p in (tmp, silent):
            try:
                os.remove(p)
            except OSError:
                pass
    print(f"[v2] done -> {out_path}")
    return out_path
