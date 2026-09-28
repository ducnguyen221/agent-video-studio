"""`video-studio uninstall` và vòng đời init → doctor → update → uninstall trên trạm giả.

Luật đang được kiểm: gỡ ĐÚNG thứ bộ cài đã đặt, dời chứ không xoá, và không bao giờ đụng một
byte dữ liệu của người dùng. Mỗi kịch bản đặt một file "canary" trong project của trạm — gỡ xong
mà canary đổi hay mất là đỏ, dù mọi thứ khác đúng.
"""
import json
import os
import subprocess

import pytest

from conftest import last_json
from test_doctor import Machine
from video_studio import doctor, station, uninstall
from video_studio.cli import main as cli_main

CANARY = "dữ liệu của người dùng — không được đổi một byte\n"


@pytest.fixture
def repo(tmp_path, monkeypatch):
    """Bản clone giả có `.git/hooks` (để init cài hook) và `.env.example`."""
    r = tmp_path / "repo"
    (r / "video_studio").mkdir(parents=True)
    (r / ".git" / "hooks").mkdir(parents=True)
    (r / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
    (r / ".env.example").write_text("# khuon\nVIDEO_FONT=\nNODE_DIR=\n", encoding="utf-8")
    monkeypatch.setenv("VIDEO_STUDIO_REPO", str(r))
    return r


def run(argv, capsys):
    rc = cli_main(argv)
    out = capsys.readouterr()
    return rc, last_json(out.out), out.err


def _canary(st):
    p = st / "projects" / "mine" / "canary.txt"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(CANARY, encoding="utf-8")
    return p


def _skills(st, tool=".claude/skills"):
    d = st.joinpath(*tool.split("/"))
    return sorted(os.listdir(d)) if d.is_dir() else []


def _old_install(st, names=("video-routing", "video-edit", "hyperframes-core")):
    """Dựng lại thứ `init` của bản trước 0.2.0 đã đặt vào trạm: bản chép skill ở hai thư mục
    host + `skills-lock.json` mang hash từng bản. Bản mới không chép nữa, nhưng `uninstall` vẫn
    phải gỡ sạch những trạm cài từ trước."""
    lock = {"version": 1, "source": station.LOCK_SOURCE, "skills": {}}
    for tool in station.SKILL_TOOLS:
        for name in names:
            p = st.joinpath(*tool.split("/"), name, "SKILL.md")
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(f"---\nname: {name}\n---\nbản chép cũ\n", encoding="utf-8")
            lock["skills"][name] = {"sha256": station._tree_hash(str(p.parent))}
    (st / station.LOCK_FILE).write_text(json.dumps(lock), encoding="utf-8")


# ── vòng đời đầy đủ ────────────────────────────────────────────────────────────────────

def test_init_no_longer_copies_skills_into_the_station(repo, capsys):
    rc, res, err = run(["init", "--yes", "--json"], capsys)
    ws = repo / "workspace"
    assert rc == 0, err
    assert not (ws / ".claude").exists() and not (ws / ".agents").exists()
    assert not (ws / station.LOCK_FILE).exists()


def test_lifecycle_embedded_keeps_every_user_byte(repo, tmp_path, monkeypatch, capsys):
    ws = repo / "workspace"
    rc, res, err = run(["init", "--yes", "--json"], capsys)
    assert rc == 0 and res["mode"] == "embedded" and res["station"] == str(ws), err
    _old_install(ws)
    canary = _canary(ws)
    edited = ws / ".claude" / "skills" / "video-routing" / "SKILL.md"
    edited.write_text(edited.read_text(encoding="utf-8") + "\nghi chú riêng\n", encoding="utf-8")
    (repo / ".env").write_text("VIDEO_FONT=Be Vietnam Pro\n", encoding="utf-8")

    m = Machine()
    monkeypatch.setattr(doctor._env.shutil, "which", m.which)
    monkeypatch.setattr(doctor, "_run", lambda argv, timeout=60: m.run(argv, timeout=timeout))
    rc, res, err = run(["doctor", "--offline", "--json"], capsys)
    assert res["station"] == str(ws)
    assert next(c for c in res["checks"] if c["name"] == "station")["ok"], err

    pulls = []

    def fake_git(argv, **kw):
        pulls.append(argv)
        return subprocess.CompletedProcess(argv, 0, "Already up to date.\n", "")
    monkeypatch.setattr(station.subprocess, "run", fake_git)
    rc, res, err = run(["update", "--json"], capsys)
    assert rc == 0 and pulls and pulls[0][-2:] == ["pull", "--ff-only"], err

    rc, res, err = run(["uninstall", "--json"], capsys)
    assert rc == 0, err
    assert canary.read_text(encoding="utf-8") == CANARY, "uninstall đã đụng dữ liệu người dùng"
    assert (ws / "station.json").is_file() and (ws / "demo").is_dir()
    assert _skills(ws) == ["video-routing"], "chỉ skill đã bị sửa được giữ lại"
    assert _skills(ws, ".agents/skills") == []
    assert not (ws / "skills-lock.json").exists()
    assert not (repo / "studio.local.json").exists()
    assert (repo / ".env").read_text(encoding="utf-8") == "VIDEO_FONT=Be Vietnam Pro\n"
    assert not (repo / ".git" / "hooks" / "pre-commit").exists()
    assert any("video-routing" in k for k in res["kept"]) and any(".env" in k for k in res["kept"])
    assert res["station_kept"] is True and res["next"] == "pip uninstall agent-video-studio"

    # Không xoá thẳng: mọi thứ đã gỡ nằm trong nhật ký của trạm.
    prev = ws / ".video-studio" / "runs" / res["run_id"]
    assert (prev / "prev" / ".agents" / "skills" / "video-routing" / "SKILL.md").is_file()
    assert (prev / "prev-repo" / "studio.local.json").is_file()
    assert json.loads((prev / "journal.json").read_text(encoding="utf-8"))["status"] == "uninstalled"

    # Cài lại là đủ để về như cũ; skill đã sửa vẫn được giữ, không bị đè, không chép thêm.
    rc, res, err = run(["init", "--yes", "--json"], capsys)
    assert rc == 0 and (repo / "studio.local.json").is_file(), err
    assert _skills(ws) == ["video-routing"] and "ghi chú riêng" in edited.read_text(encoding="utf-8")
    assert canary.read_text(encoding="utf-8") == CANARY


def test_lifecycle_separate_station(repo, tmp_path, capsys):
    ext = tmp_path / "tram-ngoai"
    rc, res, err = run(["init", "--station", str(ext), "--json"], capsys)
    assert rc == 0 and res["mode"] == "separate", err
    canary = _canary(ext)
    rc, res, err = run(["uninstall", "--json"], capsys)
    assert rc == 0 and res["station"] == str(ext), err
    assert canary.read_text(encoding="utf-8") == CANARY
    assert _skills(ext) == [] and not (ext / ".claude").exists(), "thư mục skill rỗng phải được dọn"
    assert (ext / "station.json").is_file()
    assert not (repo / "workspace").exists(), "gỡ không được đẻ ra trạm thứ hai"


# ── từng luật một ──────────────────────────────────────────────────────────────────────

def test_dry_run_writes_nothing(repo, capsys):
    run(["init", "--yes", "--json"], capsys)
    ws = repo / "workspace"
    before = sorted(str(p) for p in ws.rglob("*")) + sorted(str(p) for p in repo.iterdir())
    rc, res, err = run(["uninstall", "--dry-run", "--json"], capsys)
    assert rc == 0 and res["dry_run"] and res["plan"] and "removed" not in res
    after = sorted(str(p) for p in ws.rglob("*")) + sorted(str(p) for p in repo.iterdir())
    assert before == after


def test_a_hook_that_is_not_ours_is_kept(repo, capsys):
    hook = repo / ".git" / "hooks" / "pre-commit"
    hook.write_text("#!/bin/sh\necho hook của người khác\n", encoding="utf-8")
    run(["init", "--yes", "--json"], capsys)
    rc, res, err = run(["uninstall", "--json"], capsys)
    assert rc == 0 and hook.read_text(encoding="utf-8").endswith("người khác\n")
    assert any("pre-commit" in k for k in res["kept"])


def test_an_unfilled_dotenv_is_removed(repo, capsys):
    run(["init", "--yes", "--json"], capsys)
    assert (repo / ".env").is_file()
    rc, res, err = run(["uninstall", "--json"], capsys)
    assert rc == 0 and not (repo / ".env").exists()


def test_a_lock_written_by_another_tool_stops_skill_removal(repo, tmp_path, capsys):
    ext = tmp_path / "st"
    (ext / ".claude" / "skills" / "la").mkdir(parents=True)
    (ext / ".claude" / "skills" / "la" / "SKILL.md").write_text("x", encoding="utf-8")
    (ext / "skills-lock.json").write_text(json.dumps({"source": "cong-cu-khac", "skills": {}}),
                                          encoding="utf-8")
    rc, res, err = run(["uninstall", "--station", str(ext), "--json"], capsys)
    assert rc == 0 and (ext / ".claude" / "skills" / "la" / "SKILL.md").is_file()
    assert (ext / "skills-lock.json").is_file() and any("công cụ khác" in k for k in res["kept"])


def test_nothing_installed_is_a_clean_no_op(capsys):
    """Không repo, không biến: không có gì để gỡ — mã 0, nói rõ, không đoán trạm."""
    rc, res, err = run(["uninstall", "--json"], capsys)
    assert rc == 0 and res["station"] is None and res["plan"] == [] and res["notes"]


def test_init_undo_is_not_fooled_by_an_uninstall(repo, capsys):
    """`init --undo` đảo lần INIT gần nhất — nhật ký của uninstall không được chen vào."""
    run(["init", "--yes", "--json"], capsys)
    rc, res, err = run(["uninstall", "--json"], capsys)
    uninstall_run = res["run_id"]
    rc, res, err = run(["init", "--undo", "--dry-run", "--json"], capsys)
    assert rc == 0 and res["run_id"] != uninstall_run


def test_the_hook_mark_matches_what_init_writes():
    assert uninstall.HOOK_MARK in station._hook_text()


def test_a_failure_half_way_puts_everything_back(repo, monkeypatch, capsys):
    """Windows giữ file, hay đường dẫn vượt 260 ký tự (đã gặp thật khi thử trên máy): bước thứ
    N hỏng thì N-1 bước trước phải được trả về — trạm không bao giờ ở trạng thái nửa gỡ."""
    run(["init", "--yes", "--json"], capsys)
    ws = repo / "workspace"
    _old_install(ws)
    before = {str(p.relative_to(ws)) for p in ws.rglob("*") if ".video-studio" not in p.parts}
    real_backup = station._Run.backup
    calls = {"n": 0}

    def flaky(self, rel):
        calls["n"] += 1
        if calls["n"] == 5:
            raise OSError(206, "The filename or extension is too long")
        return real_backup(self, rel)

    monkeypatch.setattr(station._Run, "backup", flaky)
    rc, res, err = run(["uninstall", "--json"], capsys)
    assert rc == 1 and res["ok"] is False and "trả mọi thứ về chỗ cũ" in res["error"]
    after = {str(p.relative_to(ws)) for p in ws.rglob("*") if ".video-studio" not in p.parts}
    assert after == before, "hỏng giữa chừng mà trạm không về như cũ"
    assert (repo / "studio.local.json").is_file(), "phần repo chỉ được chạy khi phần trạm đã xong"
