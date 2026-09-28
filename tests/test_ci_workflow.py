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


def test_ci_has_a_job_that_checks_the_hashes_against_real_upstream(wf):
    """Cổng hash trong repo là tự quy chiếu — chỗ CHỨNG MINH nó nằm ở job có mạng này.

    Xoá job đi là cổng hash quay lại thành tautology mà không gì báo, nên chính job ấy phải
    được canh: có mặt, bật đúng công tắc, và chạy đúng bộ test.
    """
    job = wf["jobs"].get("upstream")
    assert job, "thiếu job so hash skill với manifest upstream"
    steps = job["steps"]
    assert any(s.get("env", {}).get("VIDEO_STUDIO_CHECK_UPSTREAM") == "1" for s in steps), \
        "job không bật VIDEO_STUDIO_CHECK_UPSTREAM ⇒ test online bị skip, job xanh vô nghĩa"
    assert any("test_upstream_skills.py" in s.get("run", "") for s in steps)


def test_ci_checks_out_the_repo(wf):
    """Cổng `git check-ignore` chỉ chạy trên một cây git thật — không checkout thì chúng skip câm."""
    uses = [s.get("uses", "") for s in wf["jobs"]["test"]["steps"]]
    assert any(u.startswith("actions/checkout@") for u in uses)


def _triggers(wf):
    return wf.get("on", wf.get(True))


def test_push_runs_on_every_branch(wf):
    """Lọc `push` về `[main]` là để nhánh làm việc chạy không có CI tới tận lúc mở PR."""
    push = _triggers(wf).get("push", "missing")
    assert push != "missing", "workflow phải chạy khi push"
    assert not (push or {}).get("branches"), "push không được lọc nhánh — mọi nhánh đều phải được đo"
    assert "pull_request" in _triggers(wf)


def _min_python():
    import re
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    m = re.search(r'requires-python\s*=\s*">=\s*(\d+\.\d+)"', text)
    assert m, "pyproject phải khai requires-python dạng >=x.y"
    return m.group(1)


def test_matrix_covers_the_python_range(wf):
    """Ma trận phải chạm ĐẦU DƯỚI mà pyproject hứa — hứa 3.10 mà chỉ đo 3.12 là hứa suông."""
    versions = [str(v) for v in wf["jobs"]["test"]["strategy"]["matrix"]["python-version"]]
    assert _min_python() in versions, f"ma trận thiếu bản thấp nhất {_min_python()}: {versions}"
    assert len(versions) >= 3, "cần ít nhất ba bản Python: đầu dưới, bản đang dùng, bản mới"
    # YAML đọc 3.10 không nháy thành số 3.1 — bản đó không tồn tại, runner sẽ đỏ vì lý do vớ vẩn.
    assert "3.1" not in versions, "viết '3.10' trong nháy, không thì YAML đọc thành 3.1"


def test_every_action_is_pinned_to_a_commit_sha(wf):
    """Tag `@v4` là con trỏ di động; chỉ SHA 40 ký tự mới cố định đúng mã CI sẽ chạy."""
    import re
    loose = []
    for name, job in wf["jobs"].items():
        for step in job.get("steps", []):
            uses = step.get("uses")
            if uses and not re.fullmatch(r"[\w.-]+/[\w.-]+@[0-9a-f]{40}", uses):
                loose.append(f"{name}: {uses}")
    assert not loose, "action chưa ghim SHA:\n  " + "\n  ".join(loose)


def test_checkout_does_not_persist_credentials(wf):
    """Job test không cần push; token để lại trong `.git/config` chỉ là thứ cho mã lạ mượn."""
    for name, job in wf["jobs"].items():
        for step in job.get("steps", []):
            if step.get("uses", "").startswith("actions/checkout@"):
                assert (step.get("with") or {}).get("persist-credentials") is False, name
