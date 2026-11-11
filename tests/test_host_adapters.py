"""Adapter host project-local (`.claude/skills`, `.agents/skills`) phải khớp `skills/` trên checkout.

Skill không được chép vào trạm: host mở thư mục repo, thấy adapter, adapter trỏ về skill gốc.
Adapter lệch nguồn (thêm/xoá/đổi mô tả skill mà quên sinh lại) là host định tuyến sai trong im
lặng — test này chạy `--check` trên checkout thật và đỏ ngay khi lệch.
"""
import json
import hashlib
import os
import subprocess
import sys
from pathlib import Path

import pytest

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


def test_adapter_uses_canonical_skill_in_same_installed_plugin():
    for host in (".claude", ".agents"):
        adapter = REPO / host / "skills" / "video-theme-library" / "SKILL.md"
        text = adapter.read_text(encoding="utf-8")
        assert "chính plugin chứa adapter" in text
        assert "không dùng bản chép trong trạm video hay trong cache" not in text


def test_library_cli_runs_from_plugin_root_when_caller_is_outside(tmp_path):
    """The caller's project is independent of the CLI's import root."""
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    launcher = (
        "import subprocess,sys; "
        "r=subprocess.run([sys.executable,'-m','video_studio.effect_library',"
        "'--q','VE-lens-flare','--limit','1'],cwd=sys.argv[1]); "
        "sys.exit(r.returncode)"
    )
    result = subprocess.run(
        [sys.executable, "-c", launcher, str(REPO)],
        cwd=tmp_path, env=env, capture_output=True, text=True, encoding="utf-8", timeout=60,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)[0]["entry"]["id"] == "VE-lens-flare"


@pytest.mark.skipif(os.name != "nt", reason="secure station writes are Windows-only")
def test_external_project_cli_capture_and_reuse_via_plugin_root(tmp_path):
    project, destination, station = (tmp_path / name for name in ("project", "destination", "station"))
    project.mkdir()
    destination.mkdir()
    (station / "effect-library" / "entries").mkdir(parents=True)
    payload = b"synthetic external project component"
    (project / "effect.js").write_bytes(payload)
    checks = dict.fromkeys(("static_check", "preview", "render", "audio", "ratio_test", "reuse_evidence"), "not_run")
    entry = {"id": "VE-outside-caller", "name": "Outside caller", "kind": "component",
             "maturity": "candidate", "rights": "owned", "source": "synthetic", "runtime": "js",
             "tags": [], "roles": [], "techniques": [], "ratios": [], "checks": checks,
             "asset": {"path": "effect.js", "sha256": hashlib.sha256(payload).hexdigest()}}
    (project / "entry.json").write_text(json.dumps(entry), encoding="utf-8")
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    launcher = ("import subprocess,sys; "
                "r=subprocess.run([sys.executable,'-m','video_studio.effect_library',*sys.argv[2:]],"
                "cwd=sys.argv[1]); sys.exit(r.returncode)")

    def call(*args):
        return subprocess.run([sys.executable, "-c", launcher, str(REPO), *map(str, args)],
                              cwd=tmp_path, env=env, capture_output=True, text=True,
                              encoding="utf-8", timeout=60)

    captured = call("capture", "--project", project, "--station", station, "--manifest", "entry.json")
    assert captured.returncode == 0, captured.stderr
    found = call("--q", entry["id"], "--station", station, "--limit", "1")
    assert found.returncode == 0, found.stderr
    assert json.loads(found.stdout)[0]["entry"]["id"] == entry["id"]
    restored = call("materialize", "--project", destination, "--station", station,
                    "--id", entry["id"], "--name", "effect.js")
    assert restored.returncode == 0, restored.stderr
    assert (destination / "effect.js").read_bytes() == payload
