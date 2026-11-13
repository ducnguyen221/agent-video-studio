"""Quy trình «tìm ảnh» (RQ-027) và việc skills/ + templates/ không chứa đường dẫn máy."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOC = ROOT / "skills" / "video-routing" / "references" / "news-image-search.md"
MACHINE_PATH = re.compile(r"[A-Za-z]:[\\/](?:Users|Windows|Program)|/Users/[A-Za-z]|/home/[a-z]", re.I)


def test_doc_states_required_rules():
    t = DOC.read_text(encoding="utf-8")
    for needle in ("assets/ATTRIBUTION", "https", "localhost", "file:", "IP nội bộ",
                   "giấy phép", "storyboard", "dossier", "thumbnail", "Ken Burns"):
        assert needle in t.lower() or needle in t, needle


def test_skill_links_to_the_step():
    s = (ROOT / "skills" / "video-routing" / "SKILL.md").read_text(encoding="utf-8")
    assert "references/news-image-search.md" in s


def test_theme_library_says_news_templates_skip_motion_library():
    s = (ROOT / "skills" / "video-theme-library" / "SKILL.md").read_text(encoding="utf-8")
    assert "không** đọc catalog layout hay thư viện motion" in s
    assert "render --project-dir" in s


def test_no_machine_paths_in_skills_or_assets():
    bad = []
    for base in (ROOT / "skills", ROOT / "templates"):
        for p in base.rglob("*"):
            if p.is_file() and p.suffix.lower() in {".md", ".txt", ".json", ".html"} \
                    and p.stat().st_size < 3_000_000:
                text = p.read_text(encoding="utf-8", errors="ignore")
                for i, line in enumerate(text.splitlines(), 1):
                    if MACHINE_PATH.search(line):
                        bad.append(f"{p.relative_to(ROOT)}:{i}")
    for p in ROOT.glob("**/assets/ATTRIBUTION*"):
        if ".claude" not in p.parts and MACHINE_PATH.search(
                p.read_text(encoding="utf-8", errors="ignore")):
            bad.append(str(p))
    assert not bad, bad[:10]
