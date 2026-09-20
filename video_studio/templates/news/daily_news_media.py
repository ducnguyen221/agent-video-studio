"""Bản tin ngày — bước MEDIA (giọng đọc + video tin nóng HyperFrames).

Chạy sau khi bước viết đã sinh HTML + sidecar JSON. Việc của nó:
  #3  dựng sẵn lời đọc tiếng Việt (profile giọng clone của trạm giọng) cho TL;DR, từng mục,
      và một bản "đọc tất cả" nối liền; ghi mp3 vào kho (audio/<ngày>/) rồi chèn trình phát
      <audio> vào HTML
      (replacing the old free browser speechSynthesis).
  #2  renders a short HyperFrames video for the single HOT item + OmniVoice
      voiceover, saves it (video/<date>.mp4), and embeds it at <!--HOT_VIDEO-->.

Cách gọi:
  python -m video_studio.templates.news.daily_news_media --html <path.html> --repo <repo>
         --date 2026-06-10 [--profile <tên profile giọng>] [--limit N] [--no-video] [--audio-only]
         [--media-base URL] [--no-inject] [--inject-only]
The JSON sidecar is read from "<html>.json".

--media-base: absolute URL prefix for the audio mp3s AND the hot video (e.g. a
  GitHub release download URL ending in /). Without it, relative repo paths are
  used (../../audio/<date>/ and ../../video/<date>.mp4).
--no-inject: synthesize media only, skip HTML injection (wrapper injects later,
  after it knows whether the release upload succeeded).
--inject-only: skip synthesis (no model load), only inject the player/video into
  the HTML. Injection is idempotent (guarded by a <!--MEDIA_INJECTED--> marker).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass
import numpy as np
import soundfile as sf
from voice_studio import engine, profiles

from . import news_video

LANG = "Vietnamese"
FALLBACK_INSTRUCT = "female, young adult, moderate pitch"


_W_TUAN = re.compile(r"\btu[ầa]n\s+[Ww](\d{1,2})\b")
_W_BARE = re.compile(r"\b[Ww](\d{1,2})\b")


def tts_normalize(text):
    """Sửa các từ engine giọng đọc sai trước khi TTS (chữ hiển thị giữ nguyên).

    'W24'/'tuần W24' -> 'tuần 24'; phần còn lại theo bảng `brand.pronounce` của spec — một
    chỗ duy nhất với news_video, không có tên miền nào nằm cứng trong mã.
    """
    text = _W_TUAN.sub(r"tuần \1", text or "")
    text = _W_BARE.sub(r"tuần \1", text)
    for pat, rep in news_video.PRONOUNCE.items():
        text = pat.sub(rep, text)
    return text


def _synth(model, text, prompt):
    text = tts_normalize((text or "").strip())
    if not text:
        return np.zeros(int(model.sampling_rate * 0.2), dtype=np.float32)
    if prompt is not None:
        a = model.generate(text=text, language=LANG, voice_clone_prompt=prompt)[0]
    else:
        a = model.generate(text=text, language=LANG, instruct=FALLBACK_INSTRUCT)[0]
    return np.asarray(a, dtype=np.float32)


def _load_items(html_path):
    """Read the JSON sidecar (preferred) or fall back to parsing the HTML.
    Returns (tldr, items, hot_aid, extra) where extra carries the full sidecar
    (weekly_video / week / range) or {} for the legacy HTML fallback."""
    sidecar = html_path + ".json"
    if os.path.isfile(sidecar):
        with open(sidecar, "r", encoding="utf-8-sig") as f:
            d = json.load(f)
        return d.get("tldr", ""), d.get("items", []), d.get("hot_aid"), d
    # fallback: parse old-format HTML (.tldr + .sum), assign sequential aids
    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()
    tag = re.compile(r"<[^>]+>")
    tl = re.search(r'class="tldr"[^>]*>(.*?)</', html, re.S)
    tldr = tag.sub("", tl.group(1)).strip() if tl else ""
    items = []
    for i, m in enumerate(re.finditer(r'<p class="sum">(.*?)</p>', html, re.S), 1):
        items.append({"aid": i, "summary": tag.sub("", m.group(1)).strip(),
                      "title": "", "hot": False})
    return tldr, items, (1 if items else None), {}


PLAYER_JS = """
<script>
(function(){
  var base="{base}";
  var cur=null;
  function play(src){ if(cur){cur.pause();} cur=new Audio(src); cur.play().catch(function(){}); }
  function stop(){ if(cur){cur.pause(); cur=null;} }
  document.addEventListener("DOMContentLoaded",function(){
    var ra=document.getElementById("readAll"); if(ra) ra.onclick=function(){ play(base+"all.mp3"); };
    var rs=document.getElementById("readStop"); if(rs) rs.onclick=stop;
    document.querySelectorAll(".readbtn").forEach(function(b){
      b.onclick=function(){ var id=b.getAttribute("data-aid"); if(id) play(base+id+".mp3"); };
    });
  });
})();
</script>
""".strip()


MARKER = "<!--MEDIA_INJECTED-->"


def _inject_html(html_path, date, hot_aid, has_video, media_base="", weekly=False,
                 yt_recap="", yt_short=""):
    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()
    if MARKER in html:
        print("[news-media] inject skipped (already injected)")
        return
    # AUDIO is always served by GitHub Pages (committed to git) — correct MIME +
    # range support so phones can play it. Releases force octet-stream/attachment
    # and mobile browsers refuse them.
    base = f"../../audio/{date}/"
    player = MARKER + "\n" + PLAYER_JS.replace("{base}", base)
    if "</body>" in html:
        html = html.replace("</body>", player + "\n</body>", 1)
    else:
        html += player
    # recap video block: YouTube embed (mobile-friendly) >> hosted file fallback
    if "<!--HOT_VIDEO-->" in html and (yt_recap or has_video):
        if weekly:
            label = "🎬 Video recap tuần — các tin nóng nhất"
        else:
            label = "🔥 Tin nóng nhất hôm nay (video + lồng tiếng)"
        if yt_recap:
            inner = (f'<div style="position:relative;width:100%;padding-top:56.25%;'
                     f'border-radius:12px;overflow:hidden">'
                     f'<iframe src="https://www.youtube.com/embed/{yt_recap}" '
                     f'title="Video recap" '
                     f'style="position:absolute;inset:0;width:100%;height:100%;border:0" '
                     f'allow="accelerometer;autoplay;clipboard-write;encrypted-media;'
                     f'gyroscope;picture-in-picture;web-share" '
                     f'referrerpolicy="strict-origin-when-cross-origin" '
                     f'allowfullscreen></iframe></div>')
            links = (f'<a class="vbtn" href="https://youtu.be/{yt_recap}" '
                     f'target="_blank" rel="noopener">▶ Mở Youtube</a>')
            if yt_short:
                links += (f'<a class="vbtn" href="https://www.youtube.com/shorts/{yt_short}" '
                          f'target="_blank" rel="noopener">📱 Youtube Short</a>')
            inner += f'<div class="vid-links">{links}</div>'
        else:
            if media_base:
                b = media_base if media_base.endswith("/") else media_base + "/"
                video_src = f"{b}{date}.mp4"
            else:
                video_src = f"../../video/{date}/{date}.mp4"
            inner = (f'<video controls preload="metadata" '
                     f'style="width:100%;border-radius:12px" src="{video_src}"></video>')
        vid = f'<div class="hot-video"><div class="hot-label">{label}</div>{inner}</div>'
        html = html.replace("<!--HOT_VIDEO-->", vid, 1)
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)


def _save_youtube_ids(html_path, yt_recap, yt_short):
    """Persist uploaded video IDs into the edition sidecar (newsletter uses them)."""
    sidecar = html_path + ".json"
    if not (yt_recap or yt_short) or not os.path.isfile(sidecar):
        return
    with open(sidecar, encoding="utf-8-sig") as f:
        d = json.load(f)
    d["youtube"] = {"recap": yt_recap, "short": yt_short}
    with open(sidecar, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--html", required=True)
    ap.add_argument("--repo", required=True)
    ap.add_argument("--date", required=True)
    ap.add_argument("--profile", default="",
                    help="Tên profile giọng (rỗng = profile mặc định của trạm giọng).")
    ap.add_argument("--limit", type=int, default=0, help="cap items (testing)")
    ap.add_argument("--no-video", action="store_true")
    ap.add_argument("--audio-only", action="store_true")
    ap.add_argument("--media-base", default="", help="fallback absolute URL prefix for the video file")
    ap.add_argument("--brand-config", default="",
                    help="File JSON khai brand của video (a, b, site, pronounce, …) — BẮT BUỘC "
                         "khi có dựng video: template không mang thương hiệu mặc định nào.")
    ap.add_argument("--yt-recap", default="", help="YouTube video ID of the weekly recap (16:9)")
    ap.add_argument("--yt-short", default="", help="YouTube video ID of the vertical short")
    ap.add_argument("--no-inject", action="store_true", help="synthesize only, skip HTML injection")
    ap.add_argument("--inject-only", action="store_true", help="inject HTML only, skip synthesis")
    args = ap.parse_args()

    tldr, items, hot_aid, extra = _load_items(args.html)
    if args.limit:
        items = items[: args.limit]
    brand = None
    if args.brand_config:
        with open(args.brand_config, encoding="utf-8-sig") as f:
            brand = json.load(f)
    print(f"[news-media] {len(items)} items, hot_aid={hot_aid}")

    is_weekly = bool(((extra or {}).get("weekly_video") or {}).get("segments"))

    if args.inject_only:
        video_path = os.path.join(args.repo, "video", args.date, f"{args.date}.mp4")
        _inject_html(args.html, args.date, hot_aid, os.path.isfile(video_path),
                     media_base=args.media_base, weekly=is_weekly,
                     yt_recap=args.yt_recap, yt_short=args.yt_short)
        _save_youtube_ids(args.html, args.yt_recap, args.yt_short)
        print(f"[news-media] DONE (inject-only) -> {args.html}")
        return 0

    model = engine.load()
    sr = model.sampling_rate
    prompt = profiles.get_clone_prompt(model, args.profile or None) or (
        profiles.get_clone_prompt(model, profiles.ensure_default(model)))
    print(f"[news-media] voice profile: {args.profile or profiles.get_default()}")

    audio_dir = os.path.join(args.repo, "audio", args.date)
    os.makedirs(audio_dir, exist_ok=True)
    gap = np.zeros(int(sr * 0.45), dtype=np.float32)

    # #3 — per-item audio + concatenated all.mp3. Per-file skip-if-exists makes a
    # Task Scheduler restart after a partial run cheap; existing files are read
    # back so all.mp3 always covers every item.
    def _piece(fp, text):
        if os.path.isfile(fp):
            try:
                data, _fsr = sf.read(fp, dtype="float32")
                if getattr(data, "ndim", 1) > 1:
                    data = data.mean(axis=1)
                print(f"  {os.path.basename(fp)} exists, reused")
                return np.asarray(data, dtype=np.float32)
            except Exception:
                pass  # unreadable -> re-synthesize below
        a = _synth(model, text, prompt)
        engine.save(a, fp, sr)
        print(f"  {os.path.basename(fp)} ok")
        return a

    full = []
    if tldr:
        full.append(_piece(os.path.join(audio_dir, "tldr.mp3"), tldr))
        full.append(gap)
    for it in items:
        full.append(_piece(os.path.join(audio_dir, f"{it.get('aid')}.mp3"),
                           it.get("summary", "")))
        full.append(gap)
    if full and not os.path.isfile(os.path.join(audio_dir, "all.mp3")):
        engine.save(np.concatenate(full), os.path.join(audio_dir, "all.mp3"), sr)
        print("  all.mp3 ok")

    # #2 — videos, one folder per edition: video/<date>/<date>.mp4 (16:9 recap)
    # + video/<date>/<date>-short.mp4 (9:16 weekly summary short for socials).
    # Both skip the render if a restart already produced them.
    has_video = False
    wv = (extra or {}).get("weekly_video") or {}
    if not args.no_video and not args.audio_only and (wv.get("segments") or hot_aid):
        video_dir = os.path.join(args.repo, "video", args.date)
        out = os.path.join(video_dir, f"{args.date}.mp4")
        if os.path.isfile(out):
            has_video = True
            print(f"  recap video exists, reused -> {out}")
        else:
            try:
                if wv.get("segments"):
                    news_video.make_weekly(wv, out, args.date,
                                           week=extra.get("week", ""),
                                           range_=extra.get("range", ""),
                                           model=model, prompt=prompt, brand=brand)
                else:
                    hot = next((x for x in items if x.get("aid") == hot_aid),
                               items[0] if items else None)
                    if hot:
                        news_video.make(hot, out, args.date, model=model, prompt=prompt,
                                        brand=brand)
                has_video = os.path.isfile(out)
                print(f"  recap video: {has_video} -> {out}")
            except Exception as exc:  # never let video block the weekly run
                print(f"  [warn] recap video failed: {type(exc).__name__}: {exc}")
        # vertical weekly short (best-effort, weekly editions only)
        short = os.path.join(video_dir, f"{args.date}-short.mp4")
        if wv.get("segments"):
            if os.path.isfile(short):
                print(f"  weekly short exists, reused -> {short}")
            else:
                try:
                    news_video.make_weekly_short(wv, short, args.date,
                                                 week=extra.get("week", ""),
                                                 range_=extra.get("range", ""),
                                                 model=model, prompt=prompt, brand=brand)
                    print(f"  weekly short: {os.path.isfile(short)} -> {short}")
                except Exception as exc:
                    print(f"  [warn] weekly short failed: {type(exc).__name__}: {exc}")

    if args.no_inject:
        print(f"[news-media] DONE (no-inject) — media ready for {args.date}")
        return 0
    _inject_html(args.html, args.date, hot_aid, has_video, media_base=args.media_base,
                 weekly=is_weekly, yt_recap=args.yt_recap, yt_short=args.yt_short)
    _save_youtube_ids(args.html, args.yt_recap, args.yt_short)
    print(f"[news-media] DONE — audio+{'video+' if has_video else ''}player injected into {args.html}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
