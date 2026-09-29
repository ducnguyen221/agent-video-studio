"""Sinh adapter host project-local cho mọi skill trong `skills/` của repo.

    python scripts/build_host_adapters.py            ghi/cập nhật adapter
    python scripts/build_host_adapters.py --check    chỉ kiểm, lệch nguồn thì mã 1

Mỗi skill có một adapter ở `.claude/skills/<tên>/SKILL.md` (Claude Code) và
`.agents/skills/<tên>/SKILL.md` (Codex, Antigravity). Adapter chỉ mang `name` + `description`
của skill gốc (để host định tuyến) và trỏ về `skills/…/SKILL.md` trong repo — nội dung skill
KHÔNG bị chép. Một nguồn sự thật: sửa skill ở `skills/`, `git pull` là host thấy bản mới.

Không chép skill vào trạm: trạm chỉ giữ dữ liệu người dùng (project, seed, nháp, cache).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "skills"
HOST_DIRS = (ROOT / ".claude" / "skills", ROOT / ".agents" / "skills")
MARK = "— adapter nguồn"


def source_skills() -> dict[str, Path]:
    """{tên: SKILL.md} — mọi thư mục có SKILL.md dưới `skills/` (kể cả lồng một cấp)."""
    found: dict[str, Path] = {}
    for skill in sorted(SOURCE.rglob("SKILL.md")):
        # SKILL.md nằm trong cây của một skill khác (references/, ví dụ) không phải skill riêng —
        # cùng luật với `video_studio.station._repo_skills`.
        if any((p / "SKILL.md").is_file() for p in skill.parent.parents if p != SOURCE
               and SOURCE in p.parents):
            continue
        name = skill.parent.name
        if name in found:
            raise ValueError(f"hai skill trùng tên '{name}': {found[name]} và {skill}")
        found[name] = skill
    return found


def adapter(skill: Path) -> str:
    parts = skill.read_text(encoding="utf-8").split("---", 2)
    if len(parts) < 3:
        raise ValueError(f"skill thiếu frontmatter: {skill}")
    fields = {}
    for line in parts[1].splitlines():
        for key in ("name", "description"):
            if line.startswith(f"{key}:"):
                fields[key] = line
    if set(fields) != {"name", "description"}:
        raise ValueError(f"skill thiếu name/description: {skill.parent.name}")
    name = skill.parent.name
    src = skill.relative_to(ROOT).as_posix()
    return (
        f"---\n{fields['name']}\n{fields['description']}\n---\n\n"
        f"# {name} {MARK}\n\n"
        f"Đọc toàn bộ [SKILL.md](../../../{src}) gốc trong repo trước khi làm. "
        "Mọi reference, script và template của skill phải mở trực tiếp từ thư mục gốc đó; "
        "không dùng bản chép trong trạm video hay trong cache. "
        "Nếu không mở được file gốc, báo thiếu source và dừng tác vụ này.\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="chỉ kiểm, không ghi")
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):      # console Windows cp1252 không in được tiếng Việt
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    skills = source_skills()
    if not skills:
        raise ValueError(f"không thấy skill nào dưới {SOURCE}")
    drift, stale = [], []
    for host_dir in HOST_DIRS:
        for name, skill in skills.items():
            dest = host_dir / name / "SKILL.md"
            expected = adapter(skill)
            if dest.exists() and dest.read_text(encoding="utf-8") == expected:
                continue
            drift.append(dest.relative_to(ROOT).as_posix())
            if not args.check:
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(expected, encoding="utf-8", newline="\n")
        # Adapter của skill đã bị xoá khỏi `skills/`: chỉ gỡ đúng file adapter do script này sinh.
        for dest in sorted(host_dir.glob("*/SKILL.md")) if host_dir.is_dir() else []:
            if dest.parent.name in skills:
                continue
            stale.append(dest.relative_to(ROOT).as_posix())
            if not args.check and MARK in dest.read_text(encoding="utf-8"):
                dest.unlink()
                if not any(dest.parent.iterdir()):
                    dest.parent.rmdir()
    if drift:
        print(("Adapter cần cập nhật: " if args.check else "Đã ghi adapter: ") + ", ".join(drift))
    if stale:
        print("Adapter không còn skill nguồn: " + ", ".join(stale))
    return 1 if args.check and (drift or stale) else 0


if __name__ == "__main__":
    raise SystemExit(main())
