"""Bản tin NGÀY — chỉ video + short (không sinh HTML).

Đọc một JSON brief (bước nghiên cứu ghi ra) rồi dựng HAI file bằng giọng clone của trạm
giọng, dùng lại chính template HyperFrames của bản recap tuần
(news_video.make_weekly / make_weekly_short) nhưng đổi cách diễn đạt sang bản NGÀY
("HÔM NAY" thay cho "TUẦN NÀY"):

  <out-dir>/<date>.mp4         landscape 16:9 recap (~3-4 min)
  <out-dir>/<date>-short.mp4   vertical 9:16 short (~60-90s)

JSON shape (top-level "daily_video", or "weekly_video", or a bare object with
"segments" — all accepted):

  {
    "date": "12/06/2026",
    "display_date": "Thứ Sáu · 12/06/2026",
    "daily_video": {
      "intro": "...", "outro": "...", "outro_short": "...(optional)",
      "segments": [
        { "aid": 1, "headline": "<=10 từ", "narration": "90-150 từ tiếng Việt",
          "bullets": ["<=12 từ", "..."], "images": ["https://...jpg", "..."] },
        ... 4-6 segments ...
      ]
    }
  }

Cách gọi (lối chính là `video-studio render --project news`; CLI dưới đây giữ cho việc
chạy tay một số báo):
  python -m video_studio.templates.news.daily_hot_video --json <path.json> --out-dir <dir>
         --date 2026-06-12 --brand-config brand.json
         [--display-date "Thứ Sáu · 12/06/2026"] [--profile <tên profile giọng>]
         [--long-only | --short-only]

KHÔNG đăng gì (không git / YouTube / email) — chỉ sinh hai file MP4. Chạy lại rẻ: file ra
đã có thì dùng lại thay vì render lần nữa.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from voice_studio import engine, profiles

from . import news_video


# Cách diễn đạt của bản NGÀY (đè lên wording tuần của news_video.BRAND_DEFAULTS).
# KHÔNG có a/b/site ở đây: tên thương hiệu và nơi đọc ở outro bắt buộc đến từ spec.
DAILY_WORDING = {
    "rank_suffix": "HÔM NAY",
    "cover_period": "HÔM NAY",
    # "epi" được đặt bằng ngày hiển thị lúc chạy
    "outro_big": "Cảm ơn đã xem!",
    "outro_sub": "Theo dõi để cập nhật mỗi ngày",
    "outro_big_short": "Theo dõi để<br>xem mỗi ngày",
    "outro_sub_short": "Bản tin cập nhật hằng ngày",
}


_VN_WD = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]


def _vn_display(date_iso):
    """'2026-06-12' -> 'Thứ Sáu · 12/06/2026'. Falls back to the raw string."""
    import datetime
    try:
        dt = datetime.datetime.strptime(date_iso, "%Y-%m-%d")
        return f"{_VN_WD[dt.weekday()]} · {dt.strftime('%d/%m/%Y')}"
    except Exception:
        return date_iso


def _load_video_obj(path):
    with open(path, "r", encoding="utf-8-sig") as f:
        d = json.load(f)
    vo = d.get("daily_video") or d.get("weekly_video")
    if not vo and d.get("segments"):
        vo = d
    if not vo or not vo.get("segments"):
        raise SystemExit(f"ERROR: no segments found in {path}")
    return d, vo


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", required=True, help="Path to the daily JSON brief.")
    ap.add_argument("--out-dir", required=True, help="Folder for the two mp4 outputs.")
    ap.add_argument("--date", required=True, help="YYYY-MM-DD (used in the file names).")
    ap.add_argument("--display-date", default="", help='Cover/epi date line, e.g. "Thứ Sáu · 12/06/2026".')
    ap.add_argument("--profile", default="",
                    help="Tên profile giọng (rỗng = profile mặc định của trạm giọng).")
    ap.add_argument("--brand-config", default="",
                    help="File JSON khai brand (a, b, site, …) — BẮT BUỘC nếu spec chưa có.")
    ap.add_argument("--long-only", action="store_true")
    ap.add_argument("--short-only", action="store_true")
    args = ap.parse_args()

    d, vo = _load_video_obj(args.json)
    display = args.display_date or _vn_display(args.date)

    brand = {**DAILY_WORDING, "epi": display}
    if d.get("brand"):
        brand.update(d["brand"])
    if args.brand_config:
        with open(args.brand_config, encoding="utf-8-sig") as f:
            brand.update(json.load(f))

    os.makedirs(args.out_dir, exist_ok=True)
    long_out = os.path.join(args.out_dir, f"{args.date}.mp4")
    short_out = os.path.join(args.out_dir, f"{args.date}-short.mp4")

    print(f"[daily-video] {len(vo['segments'])} segments · date {display}", flush=True)
    model = engine.load()
    prompt = (profiles.get_clone_prompt(model, args.profile or None) or
              profiles.get_clone_prompt(model, profiles.ensure_default(model)))
    print(f"[daily-video] voice profile: {args.profile or profiles.get_default()}", flush=True)

    # range_ carries the display date so the cover sub2 / epi show it (week left empty).
    if not args.short_only:
        if os.path.isfile(long_out):
            print(f"[daily-video] recap exists, reused -> {long_out}", flush=True)
        else:
            print("[daily-video] rendering landscape recap ...", flush=True)
            news_video.make_weekly(vo, long_out, args.date, week="", range_=display,
                                   model=model, prompt=prompt, brand=brand)
            print(f"[daily-video] recap -> {long_out} ({os.path.getsize(long_out)//1024} KB)", flush=True)

    if not args.long_only:
        if os.path.isfile(short_out):
            print(f"[daily-video] short exists, reused -> {short_out}", flush=True)
        else:
            print("[daily-video] rendering vertical short ...", flush=True)
            news_video.make_weekly_short(vo, short_out, args.date, week="", range_=display,
                                         model=model, prompt=prompt, brand=brand)
            print(f"[daily-video] short -> {short_out} ({os.path.getsize(short_out)//1024} KB)", flush=True)

    print("[daily-video] DONE", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
