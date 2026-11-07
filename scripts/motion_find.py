# -*- coding: utf-8 -*-
"""Lọc thư viện Prompt Motion mà không phải đọc `index.json` (≈1,8 MB) vào context.

Mỗi entry in một dòng: ID · tên · vai trò · coverage · độ hợp tỉ lệ · cường độ · loại đề xuất ·
ý chính · link nguồn · file. Đề xuất riêng xếp trước baseline nhóm; tỉ lệ `preferred` trước
`adaptable`; khớp từ khoá `--q` nhiều hơn thì lên trước.

Ví dụ:
  python scripts/motion_find.py --role proof --ratio 16:9 --technique count-up
  python scripts/motion_find.py --role explain --coverage partial --individual --limit 5
  python scripts/motion_find.py --id PM-yunn260414-60d996 --json

Chỉ dùng thư viện chuẩn; luôn in UTF-8 (console Windows mặc định cp1252 làm vỡ tiếng Việt).
Mã thoát: 0 có kết quả · 1 không entry nào khớp · 2 gọi sai / không đọc được index.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_INDEX = os.path.join(HERE, os.pardir, "skills", "video-theme-library", "assets",
                             "prompt-motion", "index.json")
FIT_RANK = {"preferred": 0, "adaptable": 1, "requires_redesign": 2}


def _fold(text):
    """Chữ thường, bỏ dấu — để `--q "so lieu"` khớp "số liệu"."""
    text = unicodedata.normalize("NFD", str(text or "").lower()).replace("đ", "d")
    return "".join(c for c in text if unicodedata.category(c) != "Mn")


def load_entries(path):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data["entries"] if isinstance(data, dict) else data


def summarize(entry, ratio=None):
    sa = entry.get("sol_analysis") or {}
    sf = entry.get("source_facts") or {}
    rf = sa.get("ratio_fit") or {}
    ratio = ratio or sa.get("primary_recommended_ratio") or "16:9"
    fit = rf.get(ratio) or {}
    return {
        "id": entry.get("id"),
        "name": entry.get("name"),
        "roles": sa.get("scene_roles") or [],
        "coverage": sa.get("coverage"),
        "ratio": ratio,
        "fit": fit.get("fit"),
        "effort": fit.get("effort"),
        "intensity": sa.get("intensity"),
        "techniques": sa.get("techniques") or [],
        "kind": sa.get("adaptation_detail"),
        "description": sa.get("description"),
        "url": sf.get("url"),
        "file": entry.get("file"),
    }


def _haystack(entry):
    sa = entry.get("sol_analysis") or {}
    sf = entry.get("source_facts") or {}
    parts = [entry.get("id"), entry.get("name"), sa.get("description"), sa.get("rhythm"),
             sa.get("content_capacity"), sf.get("technique_synopsis"),
             " ".join(sa.get("keywords") or []), " ".join(sa.get("techniques") or []),
             " ".join(sf.get("tags") or [])]
    return _fold(" ".join(str(p) for p in parts if p))


def find(entries, role=None, ratio=None, coverage=None, intensity=None, technique=None,
         query=None, individual=False, preferred_only=False, ids=None):
    terms = [_fold(t) for t in (query or "").split() if t.strip()]
    out = []
    for e in entries:
        sa = e.get("sol_analysis") or {}
        if ids and e.get("id") not in ids:
            continue
        if role and role not in (sa.get("scene_roles") or []):
            continue
        if coverage and sa.get("coverage") != coverage:
            continue
        if intensity and sa.get("intensity") != intensity:
            continue
        if technique and technique not in (sa.get("techniques") or []):
            continue
        if individual and sa.get("adaptation_detail") == "shared_category_baseline":
            continue
        fit = ((sa.get("ratio_fit") or {}).get(ratio) or {}).get("fit") if ratio else None
        if ratio and fit not in ("preferred", "adaptable"):
            continue
        if preferred_only and ratio and fit != "preferred":
            continue
        hits = 0
        if terms:
            hay = _haystack(e)
            hits = sum(1 for t in terms if t in hay)
            if hits == 0:
                continue
        baseline = sa.get("adaptation_detail") == "shared_category_baseline"
        out.append((baseline, FIT_RANK.get(fit, 3), -hits, e.get("id") or "", e))
    out.sort(key=lambda t: t[:4])
    return [t[4] for t in out]


def _line(s):
    kind = "baseline" if s["kind"] == "shared_category_baseline" else "riêng"
    return (f'{s["id"]} | {s["name"]} | {"/".join(s["roles"])} | {s["coverage"]} | '
            f'{s["ratio"]} {s["fit"]}/{s["effort"]} | {s["intensity"]} | {kind} | '
            f'{s["description"]} | {s["url"]} | {s["file"]}')


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Lọc thư viện Prompt Motion theo việc của cảnh.")
    ap.add_argument("--role", help="vai trò cảnh: hook, explain, proof, emphasis, transition, closing, cta, ambient")
    ap.add_argument("--ratio", help="tỉ lệ cần giao: 16:9, 9:16, 1:1 (giữ preferred + adaptable)")
    ap.add_argument("--preferred", action="store_true", help="chỉ giữ tỉ lệ preferred")
    ap.add_argument("--coverage", choices=["fullscreen", "partial"])
    ap.add_argument("--intensity", choices=["low", "medium", "high"])
    ap.add_argument("--technique", help="vd. typography, ui, diagram, chart, count-up, path, particles, 3d")
    ap.add_argument("--q", dest="query", help="từ khoá (không phân biệt dấu) trên tên, ý chính, kỹ thuật")
    ap.add_argument("--individual", action="store_true", help="bỏ entry baseline dùng chung của nhóm")
    ap.add_argument("--id", action="append", dest="ids", help="lấy đúng ID (lặp được)")
    ap.add_argument("--limit", type=int, default=10)
    ap.add_argument("--json", action="store_true", help="in JSON tóm tắt thay vì dòng")
    ap.add_argument("--index", default=DEFAULT_INDEX, help="đường tới index.json")
    a = ap.parse_args(argv)
    if a.limit < 1:
        ap.error("--limit phải ≥ 1")
    try:
        entries = load_entries(a.index)
    except (OSError, ValueError, KeyError) as exc:
        print(f"[motion_find] không đọc được index: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    res = find(entries, role=a.role, ratio=a.ratio, coverage=a.coverage, intensity=a.intensity,
               technique=a.technique, query=a.query, individual=a.individual,
               preferred_only=a.preferred, ids=set(a.ids) if a.ids else None)
    shown = [summarize(e, a.ratio) for e in res[:a.limit]]
    if a.json:
        print(json.dumps({"total": len(res), "shown": shown}, ensure_ascii=False, indent=1))
    else:
        for s in shown:
            print(_line(s))
        print(f"-- {len(shown)}/{len(res)} entry khớp", file=sys.stderr)
    return 0 if res else 1


if __name__ == "__main__":
    sys.exit(main())
