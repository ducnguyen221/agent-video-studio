"""Thư viện Prompt Motion (`skills/video-theme-library/assets/prompt-motion/`) và lệnh lọc
`scripts/motion_find.py`.

Thư viện là 240 Markdown + `index.json` + `INDEX.md` sinh cùng nhau; lệch một chỗ là agent tra
INDEX thấy một mã nhưng mở file ra không có, hoặc lọc JSON ra mẫu đã bị xoá. Các khẳng định dưới
đây là những gì review độc lập đã kiểm bằng tay (đợt 0.7.0) — giữ chúng thành test để lần sinh lại
thư viện sau không lặng lẽ phá hợp đồng. Không cần mạng, Node hay HyperFrames.
"""
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
LIB = REPO / "skills" / "video-theme-library" / "assets" / "prompt-motion"
SCRIPT = REPO / "scripts" / "motion_find.py"


def _load_script():
    spec = importlib.util.spec_from_file_location("motion_find", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def entries():
    return json.loads((LIB / "index.json").read_text(encoding="utf-8"))["entries"]


def _frontmatter(path):
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    assert m, f"{path.name}: thiếu frontmatter"
    out = {}
    for line in m.group(1).splitlines():
        if ":" in line and not line.startswith(" "):
            k, v = line.split(":", 1)
            out[k.strip()] = v.strip().strip('"')
    return out


# ---- hợp đồng của thư viện -------------------------------------------------------------------

def test_ids_urls_files_are_unique_and_match(entries):
    ids = [e["id"] for e in entries]
    urls = [e["source_facts"]["url"] for e in entries]
    assert len(ids) == len(set(ids)), "ID trùng trong index.json"
    assert len(urls) == len(set(urls)), "URL nguồn trùng trong index.json"
    md = sorted(p.name for p in (LIB / "motions").glob("*.md"))
    assert sorted(Path(e["file"]).name for e in entries) == md, "index.json ↔ motions/*.md lệch"


def test_frontmatter_matches_index(entries):
    for e in entries:
        fm = _frontmatter(LIB / e["file"])
        assert fm.get("id") == e["id"], e["file"]
        assert fm.get("source_url") == e["source_facts"]["url"], e["file"]
        assert Path(e["file"]).stem == e["id"][len("PM-"):], e["file"]


def test_every_id_is_listed_in_index_md(entries):
    index_md = (LIB / "INDEX.md").read_text(encoding="utf-8")
    missing = [e["id"] for e in entries if e["id"] not in index_md]
    assert not missing, f"INDEX.md thiếu: {missing[:5]}"


def test_no_entry_claims_archived_prompt_or_runtime_test(entries):
    # Kho chỉ giữ bản chuyển thể tự viết; chưa entry nào được render kiểm chứng.
    for e in entries:
        assert e["source_facts"].get("original_prompt_archived") is False, e["id"]
        assert e["sol_analysis"].get("runtime_tested") is False, e["id"]
        fm = _frontmatter(LIB / e["file"])
        assert fm.get("original_prompt_archived") == "false", e["file"]
        assert fm.get("runtime_tested") == "false", e["file"]


def test_relative_links_resolve():
    broken = []
    for md in [*LIB.glob("*.md"), *(LIB / "motions").glob("*.md")]:
        for target in re.findall(r"\]\(([^)#\s]+)(?:#[^)]*)?\)", md.read_text(encoding="utf-8")):
            if "://" in target or target.startswith("mailto:"):
                continue
            if not (md.parent / target).exists():
                broken.append(f"{md.relative_to(LIB)} → {target}")
    assert not broken, broken[:10]


def test_ratio_fit_values_are_known(entries):
    for e in entries:
        for ratio, fit in e["sol_analysis"]["ratio_fit"].items():
            assert ratio in {"16:9", "9:16", "1:1"}, e["id"]
            assert fit["fit"] in {"preferred", "adaptable", "requires_redesign"}, e["id"]
            assert fit["effort"] in {"low", "medium", "high"}, e["id"]


# ---- lệnh lọc ---------------------------------------------------------------------------------

def test_find_filters_role_ratio_and_ranks_individual_first(entries):
    mf = _load_script()
    res = mf.find(entries, role="explain", ratio="16:9")
    assert res, "phải có mẫu explain cho 16:9"
    for e in res:
        sa = e["sol_analysis"]
        assert "explain" in sa["scene_roles"]
        assert sa["ratio_fit"]["16:9"]["fit"] in ("preferred", "adaptable")
    kinds = [e["sol_analysis"].get("adaptation_detail") == "shared_category_baseline" for e in res]
    assert kinds == sorted(kinds), "baseline nhóm phải đứng sau đề xuất riêng"


def test_find_query_ignores_diacritics():
    mf = _load_script()
    fake = [{"id": "PM-a", "name": "Số liệu nhảy", "sol_analysis": {}, "source_facts": {}},
            {"id": "PM-b", "name": "Khác", "sol_analysis": {}, "source_facts": {}}]
    assert [e["id"] for e in mf.find(fake, query="so lieu")] == ["PM-a"]
    assert mf.find(fake, query="khong-co") == []


def test_cli_prints_utf8_lines_and_exit_codes(tmp_path):
    ok = subprocess.run([sys.executable, str(SCRIPT), "--role", "explain", "--ratio", "16:9",
                         "--limit", "3"], capture_output=True, timeout=60, check=False)
    assert ok.returncode == 0, ok.stderr
    lines = ok.stdout.decode("utf-8").strip().splitlines()
    assert len(lines) == 3 and all(ln.startswith("PM-") for ln in lines)

    none = subprocess.run([sys.executable, str(SCRIPT), "--q", "zzzz-khong-ton-tai"],
                          capture_output=True, timeout=60, check=False)
    assert none.returncode == 1

    bad = subprocess.run([sys.executable, str(SCRIPT), "--index", str(tmp_path / "missing.json")],
                         capture_output=True, timeout=60, check=False)
    assert bad.returncode == 2
