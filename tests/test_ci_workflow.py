"""Cổng cho `.github/workflows/tests.yml`.

CI chỉ chạy thật sau khi repo được push, nên lỗi cú pháp hay thiếu một OS **không lộ ra ở máy**
— nó lộ ra lúc mở pull request, tức sau khi mọi thứ đã rời tay. Bộ test này kiểm tại chỗ đúng
những thứ hỏng theo kiểu đó: YAML đọc được, đủ hai hệ điều hành, và CI không lén cài engine nặng
(nếu nó cài thì bộ test hết còn là bằng chứng "chạy được trên máy trần").
"""
from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

ROOT = Path(__file__).resolve().parent.parent
WF = ROOT / ".github" / "workflows" / "tests.yml"


@pytest.fixture(scope="module")
def wf():
    assert WF.is_file(), "repo phải có workflow test"
    return yaml.safe_load(WF.read_text(encoding="utf-8"))


def test_workflow_is_valid_yaml_with_a_job(wf):
    assert wf["jobs"], "workflow không có job nào"
    # `on:` bị YAML 1.1 đọc thành boolean True — chấp nhận cả hai cách viết.
    assert ("on" in wf) or (True in wf), "workflow không có trigger"


def test_matrix_covers_both_operating_systems(wf):
    job = wf["jobs"]["test"]
    oses = job["strategy"]["matrix"]["os"]
    assert any(o.startswith("windows") for o in oses), "thiếu Windows"
    assert any(o.startswith("macos") for o in oses), "thiếu macOS"
    assert job["strategy"]["fail-fast"] is False, \
        "fail-fast=true giấu mất lỗi của OS còn lại — đúng thứ CI hai OS sinh ra để thấy"


def test_ci_installs_the_package_and_runs_pytest(wf):
    runs = " ".join(s.get("run", "") for s in wf["jobs"]["test"]["steps"])
    assert "pip install -e" in runs and '[test]' in runs
    assert "pytest" in runs


def test_ci_does_not_install_a_heavy_engine(wf):
    """Bộ test phải xanh trên máy trần. CI cài Node/ffmpeg/model là tự bỏ mất phép thử đó."""
    steps = wf["jobs"]["test"]["steps"]
    text = " ".join(s.get("run", "") + " " + s.get("uses", "") for s in steps).lower()
    for heavy in ("setup-node", "npm install", "npx ", "ffmpeg", "torch", "faster-whisper"):
        assert heavy not in text, f"CI không được cài/gọi {heavy}"


def test_ci_checks_out_the_repo(wf):
    """Cổng `git check-ignore` chỉ chạy trên một cây git thật — không checkout thì chúng skip câm."""
    uses = [s.get("uses", "") for s in wf["jobs"]["test"]["steps"]]
    assert any(u.startswith("actions/checkout@") for u in uses)
