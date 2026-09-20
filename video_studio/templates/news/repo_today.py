# -*- coding: utf-8 -*-
"""repo_today.py — pipeline "repo nổi bật mỗi ngày" cho News v2.

  fetch  : lấy repo #1 GitHub Trending hôm nay + metadata + README -> repo_today_input.json
  render : đọc kịch bản scenes JSON (LLM/agent soạn từ input) -> video deep-dive (news_v2)

Quy trình /repo-today: fetch  ->  agent đọc input + soạn scenes (bám README, không bịa)
-> render. Cũng dùng được cho cron headless (claude headless tạo scenes).
"""
import argparse
import json
import os
import re
import sys
import urllib.request

from ... import projects

HERE = os.path.dirname(os.path.abspath(__file__))
SCENES_SAMPLE = os.path.join(HERE, "repo_today_scenes.json")
# Dữ liệu thu được là của NGƯỜI DÙNG: ghi vào nháp của trạm, không ghi ngược vào cây repo
# (repo cài dạng wheel còn có thể chỉ-đọc).
INPUT = os.environ.get("REPO_TODAY_INPUT") or ""
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}


def _get(url, timeout=30):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")


def input_path():
    """File input của bước fetch: REPO_TODAY_INPUT → `<trạm>/scratch/repo-today/input.json`."""
    return INPUT or projects.scratch_file("repo-today", "input.json")


def fetch(period="daily"):
    from bs4 import BeautifulSoup
    html = _get(f"https://github.com/trending?since={period}")
    s = BeautifulSoup(html, "lxml")
    art = s.select_one("article.Box-row")
    if not art:
        sys.exit("Không parse được GitHub Trending.")
    a = art.select_one("h2 a")
    full = a["href"].strip("/")                       # owner/repo
    owner, repo = full.split("/", 1)
    stars_today = ""
    for sp in art.select("span.float-sm-right, span.d-inline-block.float-sm-right"):
        if "today" in sp.get_text():
            stars_today = re.sub(r"[^\d,]", "", sp.get_text()).strip()
            break
    if not stars_today:
        m = re.search(r"([\d,]+)\s+stars?\s+today", art.get_text())
        stars_today = m.group(1) if m else ""

    meta = {}
    try:
        meta = json.loads(_get(f"https://api.github.com/repos/{full}"))
    except Exception as e:
        print(f"[warn] API repo meta lỗi: {e}")
    readme = ""
    for ref in ("HEAD", "master", "main"):
        for name in ("README.md", "readme.md", "README.rst"):
            try:
                readme = _get(f"https://raw.githubusercontent.com/{full}/{ref}/{name}")
                break
            except Exception:
                continue
        if readme:
            break
    readme = re.sub(r"\n{3,}", "\n\n", readme)[:7000]

    data = {
        "full_name": full, "owner": owner, "repo": repo,
        "description": (meta.get("description") or "").strip(),
        "language": meta.get("language") or "",
        "stars_total": meta.get("stargazers_count"),
        "stars_today": stars_today,
        "homepage": meta.get("homepage") or "",
        "topics": meta.get("topics") or [],
        "avatar": f"https://github.com/{owner}.png",
        "url": f"https://github.com/{full}",
        "readme": readme,
    }
    dst = input_path()
    os.makedirs(os.path.dirname(dst) or ".", exist_ok=True)
    with open(dst, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"[fetch] #1 trending: {full}  (+{stars_today} sao hôm nay, tổng {data['stars_total']})")
    print(f"[fetch] README {len(readme)} ký tự -> {dst}")
    return data


def render(scenes_path, out_path=None, voice_profile=None, brand=None):
    """Dựng video deep-dive từ kịch bản cảnh. `out_path` BẮT BUỘC do bên gọi quyết.

    Lịch sử chỗ này là một bài học: bản cũ tự đoán thư mục ra (Desktop → thư mục tool →
    thư mục của app khác), và mỗi lần đoán sai thì video rơi vào chỗ không ai tìm. Nay
    thiếu `--out` là LỖI NÓI RA, không phải một mặc định âm thầm.
    """
    from . import news_v2
    obj = json.load(open(scenes_path, encoding="utf-8"))
    scenes = obj["scenes"] if isinstance(obj, dict) else obj
    epi = (obj.get("epi") if isinstance(obj, dict) else "") or "GitHub Trending"
    if not out_path:
        raise SystemExit("ERROR: cần --out <file.mp4> — công cụ không tự chọn thư mục ra.")
    news_v2.render_deepdive(scenes, out_path, epi=epi, voice_profile=voice_profile, brand=brand)
    print("OUT:", out_path)
    return out_path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["fetch", "render"])
    ap.add_argument("--period", default="daily")
    ap.add_argument("--scenes", default=SCENES_SAMPLE)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    if a.mode == "fetch":
        fetch(a.period)
    else:
        render(a.scenes, a.out)


if __name__ == "__main__":
    main()
