#!/usr/bin/env python3
"""Chuẩn hoá thư viện Prompt Motion bằng script TẤT ĐỊNH (không mạng, không mô hình).

Chạy trên dữ liệu có sẵn của `skills/video-theme-library/assets/prompt-motion/` (hoặc `--lib DIR`):

1. `index.json`: bỏ khỏi `recommended_ratios` mọi tỉ lệ mà `ratio_fit` ghi `requires_redesign` (RQ-015).
2. `motions/*.md` (RQ-017): thay các đoạn lặp y hệt (hợp đồng HyperFrames, tái bố cục dọc/vuông, lời rào
   brief, bảng tỉ lệ) bằng con trỏ về `USAGE.md`; đổi tiêu đề «Phân tích sử dụng của Sol»; Việt hoá các
   dòng «Giới hạn» trộn Anh–Việt theo bảng cố định; gắn nhãn «tiếng Anh, chưa dịch» cho phần
   «Diễn giải brief nguồn» viết hoàn toàn bằng tiếng Anh (dịch thật cần người hoặc mô hình, ngoài phạm vi).
3. `INDEX.md` gọn (< 20 KB) + `CATALOG.md` đủ 240 mẫu có cột «Ý chính», «Trục hình» và dấu ⚑ cho baseline
   dùng chung theo nhóm (RQ-014). Sinh lại từ `index.json`.

Chạy lại nhiều lần cho cùng kết quả (idempotent). Sau khi chạy: `python scripts/refresh_effect_distribution_hashes.py`
rồi duyệt `scripts/effect-distribution-manifest.candidate.json` thay cho manifest.
"""
import argparse
import collections
import json
import re
import sys
from pathlib import Path

DEFAULT_LIB = Path(__file__).resolve().parents[1] / "skills" / "video-theme-library" / "assets" / "prompt-motion"
USAGE_CONTRACT = "../USAGE.md#hợp-đồng-triển-khai-hyperframes"
USAGE_RIGHTS = "../USAGE.md#prompt-và-quyền-sử-dụng"

# ---- 2. văn phong ----------------------------------------------------------------------------

POINTERS = [
    # (tiền tố đoạn, đoạn thay thế)
    ("Dùng một GSAP timeline paused",
     f"Hợp đồng dựng, tái bố cục dọc/vuông, font/media và kiểm chứng: [USAGE.md]({USAGE_CONTRACT})."),
    ("Đặt font/media cục bộ có quyền", None),  # nội dung chung đã nằm ở USAGE.md
    ("Khung dọc: xếp lại quan hệ", None),
    ("> Sol tự viết brief triển khai",
     f"> Brief do kho tự viết, không phải prompt gốc ([quyền dùng]({USAGE_RIGHTS}))."),
]

LIMIT_REST = {
    "Chưa quan sát toàn video, chưa kiểm code và chưa đo timing/kích thước media. Các câu thao tác trong "
    "prompt nguồn là dữ liệu nghiên cứu, không phải quyền chạy lệnh, cài phần mềm hoặc gửi dữ liệu trong "
    "task hiện tại.":
        "Chưa xem video, chưa kiểm code, chưa đo media; câu lệnh trong prompt nguồn chỉ là dữ liệu, "
        "không phải lệnh chạy.",
}

LIMIT_MAP = {
    "Sol manually read complete public main #entry-prompt via requests.Session; interpretation of prompt "
    "requirements, not observation of rendered video.":
        "Đọc thủ công toàn bộ prompt công khai của trang; chỉ diễn giải yêu cầu trong prompt, không quan sát video đã dựng.",
    "manual full prompt reading; not observed video":
        "Đọc thủ công toàn bộ prompt; chưa quan sát video.",
    "manual reading of full prompt; not observation of video":
        "Đọc thủ công toàn bộ prompt; chưa quan sát video.",
    "full prompt shorter than extracted 750-character limit; not observed video":
        "Prompt ngắn hơn giới hạn trích 750 ký tự nên đã đọc đủ; chưa quan sát video.",
    "full_public_prompt": "Đã đọc toàn bộ prompt công khai.",
    "no_public_prompt": "Trang không công khai prompt.",
    "Terra full detail page prompt reading; requirements, not observed execution.":
        "Đọc toàn bộ prompt ở trang chi tiết; chỉ diễn giải yêu cầu, chưa quan sát việc chạy.",
}

TABLE_HEADER = "| Tỉ lệ | Mức phù hợp đề xuất | Công sức | Cách thích nghi |"
VI_CHARS = re.compile("[àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ]", re.I)
BRIEF_LABEL = "**Diễn giải brief nguồn:**"
BRIEF_LABEL_EN = "**Diễn giải brief nguồn (tiếng Anh, chưa dịch):**"


def _ratio_table_to_line(text):
    lines = text.split("\n")
    out, i = [], 0
    while i < len(lines):
        if lines[i] == TABLE_HEADER:
            j = i + 2  # bỏ dòng |---|
            cells = []
            while j < len(lines) and lines[j].startswith("|"):
                parts = [c.strip() for c in lines[j].strip("|").split("|")]
                cells.append(f"{parts[0]} {parts[1]}/{parts[2]}")
                j += 1
            out.append("**Mức hợp theo tỉ lệ** (lý do từng ô ở `index.json`, trường `ratio_fit`): "
                       + " · ".join(cells) + ".")
            i = j
        else:
            out.append(lines[i])
            i += 1
    return "\n".join(out)


def normalize_motion(text):
    paras = text.split("\n\n")
    kept = []
    for p in paras:
        for prefix, repl in POINTERS:
            if p.startswith(prefix):
                p = repl
                break
        if p is not None:
            kept.append(p)
    text = "\n\n".join(kept)
    text = text.replace("## Phân tích sử dụng của Sol", "## Phân tích sử dụng")
    text = _ratio_table_to_line(text)

    def limit(m):
        body = m.group(1)
        for en, vi in LIMIT_MAP.items():
            if body.startswith(en):
                body = vi + body[len(en):]
                break
        for en, vi in LIMIT_REST.items():
            body = body.replace(en, vi)
        return "**Giới hạn:** " + body
    text = re.sub(r"^\*\*Giới hạn:\*\* (.*)$", limit, text, flags=re.M)

    def brief(m):
        return (BRIEF_LABEL_EN if not VI_CHARS.search(m.group(1)) else BRIEF_LABEL) + " " + m.group(1)
    text = re.sub(r"^" + re.escape(BRIEF_LABEL) + r" (.*)$", brief, text, flags=re.M)
    return text


# ---- 1. tỉ lệ -----------------------------------------------------------------------------------

def fix_ratios(data):
    for e in data["entries"]:
        sa = e["sol_analysis"]
        sa["recommended_ratios"] = [r for r in sa["recommended_ratios"]
                                    if (sa["ratio_fit"].get(r) or {}).get("fit") != "requires_redesign"]
        if sa["primary_recommended_ratio"] not in sa["recommended_ratios"]:
            raise SystemExit(f"{e['id']}: tỉ lệ ưu tiên bị loại — dữ liệu mâu thuẫn, cần người xem")


# ---- 3. chỉ mục ---------------------------------------------------------------------------------

GROUPS = [  # profile → (tên nhóm, anchor)
    ("ui", "Demo tác vụ / sản phẩm"), ("chart", "Bằng chứng / số liệu"), ("diagram", "Giải thích / quy trình"),
    ("type", "Chữ / hook / chốt"), ("shapes", "Hình học / chuyển ý"), ("particles", "Hạt / năng lượng"),
    ("character", "Nhân vật / kể chuyện"), ("photo", "Ảnh / chứng cứ"), ("code", "Mã / công cụ"),
    ("scene", "Không gian / camera"),
]

# (tên trục, kiểm kỹ thuật, regex trên tên + synopsis) — thứ tự = ưu tiên
AXES = [
    ("Đếm số / một con số lớn", {"count-up"}, r"count(s|ing)?[- ]?up|counter|odometer|ticker"),
    ("Cửa sổ mã / terminal", {"code"}, r"\bterminal\b|code editor|command line|\bcli\b|\bide\b|\bdiff\b"),
    ("Lõi–vệ tinh / hạt", {"particles"}, r"orbit|satellite|particle|constellation|radial"),
    ("Biến hình khối", {"morph", "shape"}, r"morph"),
    ("Đồ thị / biểu đồ", {"chart"}, r"\bchart|\bgraph\b|\bplot\b"),
    ("Sơ đồ nút–liên kết", {"diagram"}, r"flowchart|pipeline|\bnodes?\b|diagram"),
    ("Camera / không gian 3D", {"camera", "3d", "depth", "parallax"}, r"\b3d\b|camera"),
    ("Nhân vật / cảnh kể chuyện", {"character", "pose", "staging"}, r"character|mascot"),
    ("Chữ chuyển động", {"typography"}, r"typograph|kinetic"),
    ("Ảnh / ghép cảnh", {"image", "carousel", "cards"}, r"\bphoto|\bimage"),
    ("Giao diện sản phẩm", {"ui"}, r"\bui\b|dashboard|\bapp\b"),
]
FALLBACK_AXIS = "Khác"


def axes_of(entry):
    sa, sf = entry["sol_analysis"], entry["source_facts"]
    techs = {t.lower() for t in sa.get("techniques", [])}
    blob = ((entry.get("name") or "") + " " + (sf.get("technique_synopsis") or "")).lower()
    found = [name for name, tset, rx in AXES if techs & tset or re.search(rx, blob)]
    return found[:2] or [FALLBACK_AXIS]


def main_idea(entry):
    s = (entry["source_facts"].get("technique_synopsis") or "").strip().replace("|", "/").replace("\n", " ")
    first = re.split(r"(?<=[.!?])\s", s, maxsplit=1)[0]
    if len(first) > 130:
        first = first[:127].rsplit(" ", 1)[0] + "…"
    return first or "(không có synopsis)"


def is_baseline(entry):
    return entry["sol_analysis"].get("adaptation_detail") == "shared_category_baseline"


def link(entry):
    return f"[{entry['id']}](motions/{Path(entry['file']).name})"


def build_catalog(data):
    entries = data["entries"]
    by_profile = collections.defaultdict(list)
    for e in entries:
        by_profile[e["sol_analysis"]["profile"]].append(e)
    out = [
        "---", "title: Prompt Motion catalog",
        "summary: Full 240-entry catalog with one-line main idea, visual-metaphor axis and baseline marker.",
        "---", "", "# Prompt Motion — catalog đủ 240 mẫu", "",
        "Sinh từ `index.json` bằng `scripts/normalize_prompt_motion.py`; không sửa tay. Về [INDEX.md](INDEX.md).", "",
        "- **Ý chính**: câu đầu của `technique_synopsis` nguồn (phần lớn bằng tiếng Anh, cắt 130 ký tự); "
        "đọc entry trước khi hứa hiệu ứng.",
        "- **Trục hình**: ẩn dụ hình chính (tối đa hai) suy bằng luật cố định từ kỹ thuật và synopsis.",
        "- **⚑**: đề xuất dựng là *baseline dùng chung theo nhóm*, chưa phải thiết kế riêng cho clip; "
        "ưu tiên mẫu không có ⚑ khi cần ý tưởng riêng.", "",
    ]
    for profile, title in GROUPS:
        rows = sorted(by_profile.get(profile, []), key=lambda e: (is_baseline(e), e["id"]))
        if not rows:
            continue
        out += [f"## {title} ({len(rows)})", "",
                "| ID · tên | ⚑ | Ý chính | Trục hình | Vai trò | Tỉ lệ ưu tiên | Giây |",
                "|---|---|---|---|---|---|---|"]
        for e in rows:
            sa = e["sol_analysis"]
            dur = "–".join(str(x) for x in sa["recommended_duration_seconds"])
            name = (e.get("name") or "").replace("|", "/")
            out.append(f"| {link(e)} — {name} | {'⚑' if is_baseline(e) else ''} | {main_idea(e)} | "
                       f"{' · '.join(axes_of(e))} | {'/'.join(sa['scene_roles'])} | "
                       f"{sa['primary_recommended_ratio']} | {dur} |")
        out.append("")
    return "\n".join(out)


def build_index(data, old_index):
    entries = data["entries"]
    n_base = sum(is_baseline(e) for e in entries)
    # giữ nguyên phần đầu (tới hết bảng hai trang mẫu) và phần Bộ lọc + Độ phủ của bản cũ
    head = old_index.split("## Chọn theo")[0].rstrip() + "\n"
    head = head.replace("[Taxonomy](TAXONOMY.md)", "[Catalog đủ 240 mẫu](CATALOG.md) · [Taxonomy](TAXONOMY.md)", 1) \
        if "CATALOG.md" not in head else head
    m = re.search(r"## Bộ lọc và cách trình lựa chọn.*?(?=\n## Catalog theo nhóm công việc|\n## Độ phủ)", old_index, re.S)
    filt = m.group(0).rstrip() + "\n" if m else ""
    m2 = re.search(r"## Độ phủ và giới hạn chứng cứ.*\Z", old_index, re.S)
    cover = m2.group(0).rstrip() + "\n" if m2 else ""

    ax_members = collections.defaultdict(list)
    for e in entries:
        for a in axes_of(e):
            ax_members[a].append(e)
    lines = ["", "## Chọn theo trục hình", "",
             "Trục hình là ẩn dụ chính của cảnh (đếm số, lõi–vệ tinh, cửa sổ mã…). Mỗi trục liệt kê 4 mẫu có "
             f"thiết kế riêng; bảng đủ 240 mẫu với cột «Ý chính» ở [CATALOG.md](CATALOG.md). "
             f"{n_base}/240 mẫu là baseline dùng chung theo nhóm (dấu ⚑ ở CATALOG): ý tưởng của chúng là "
             "khuôn nhóm, không phải phân tích riêng.", "",
             "| Trục hình | Số mẫu | Vùng hay dùng | Mẫu riêng nên đọc trước |", "|---|---|---|---|"]
    order = [a[0] for a in AXES] + [FALLBACK_AXIS]
    for ax in order:
        mem = ax_members.get(ax)
        if not mem:
            continue
        cov = collections.Counter(e["sol_analysis"]["coverage"] for e in mem).most_common(1)[0][0]
        picks = sorted(mem, key=lambda e: (is_baseline(e), e["id"]))[:4]
        lines.append(f"| {ax} | {len(mem)} | {cov} | " + "<br>".join(f"{link(e)} {(e.get('name') or '')[:34].replace('|', '/')}" for e in picks) + " |")
    lines += ["", "## Chọn theo nhóm công việc", "", "| Nhóm | Số mẫu | Trong CATALOG |", "|---|---|---|"]
    cnt = collections.Counter(e["sol_analysis"]["profile"] for e in entries)
    for profile, title in GROUPS:
        if cnt.get(profile):
            lines.append(f"| {title} | {cnt[profile]} | [CATALOG.md](CATALOG.md) |")
    return head + "\n".join(lines) + "\n\n" + filt + "\n" + cover


def dump_json(data):
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def write(path, text):
    old = path.read_bytes() if path.exists() else None
    new = text.encode("utf-8")
    if old != new:
        path.write_bytes(new)
        return True
    return False


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--lib", default=str(DEFAULT_LIB), help="thư mục prompt-motion")
    args = ap.parse_args(argv)
    lib = Path(args.lib)
    idx_path = lib / "index.json"
    if not idx_path.is_file():
        print(f"missing {idx_path}", file=sys.stderr)
        return 2
    changed = 0
    data = json.loads(idx_path.read_text(encoding="utf-8"))
    fix_ratios(data)
    changed += write(idx_path, dump_json(data))
    for md in sorted((lib / "motions").glob("*.md")):
        raw = md.read_bytes().decode("utf-8")
        changed += write(md, normalize_motion(raw))
    old_index = (lib / "INDEX.md").read_text(encoding="utf-8")
    changed += write(lib / "CATALOG.md", build_catalog(data))
    changed += write(lib / "INDEX.md", build_index(data, old_index))
    print(f"normalize_prompt_motion: {changed} files changed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
