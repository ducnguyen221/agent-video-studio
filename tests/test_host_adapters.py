"""Adapter host project-local (`.claude/skills`, `.agents/skills`) phải khớp `skills/` trên checkout.

Skill không được chép vào trạm: host mở thư mục repo, thấy adapter, adapter trỏ về skill gốc.
Adapter lệch nguồn (thêm/xoá/đổi mô tả skill mà quên sinh lại) là host định tuyến sai trong im
lặng — test này chạy `--check` trên checkout thật và đỏ ngay khi lệch.
"""
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
GENERATOR = REPO / "scripts" / "build_host_adapters.py"


def test_host_adapters_match_source():
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    result = subprocess.run(
        [sys.executable, str(GENERATOR), "--check"],
        cwd=REPO, env=env, capture_output=True, text=True, encoding="utf-8",
        timeout=60, check=False,
    )
    assert result.returncode == 0, (
        "Adapter lệch nguồn: chạy `python scripts/build_host_adapters.py` rồi xem diff.\n"
        + result.stdout + result.stderr
    )


def test_every_adapter_points_at_an_existing_skill():
    skills = {p.parent.name for p in (REPO / "skills").rglob("SKILL.md")}
    for host in (".claude", ".agents"):
        adapters = sorted((REPO / host / "skills").glob("*/SKILL.md"))
        assert {a.parent.name for a in adapters} == skills, host
        for a in adapters:
            text = a.read_text(encoding="utf-8")
            target = text.split("](", 1)[1].split(")", 1)[0]
            assert (a.parent / target).resolve().is_file(), f"{a}: link hỏng {target}"
            assert "\n---\n" in text and text.startswith("---\nname: "), a
