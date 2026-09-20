"""`video-studio init [--station] [--migrate] [--dry-run] [--undo]` trên cây trạm GIẢ.

Cây giả mô phỏng một trạm video đời cũ (trước station.json): project scratch `news/`,
`topstory/` ở gốc, seed `demo/`, skill cài bằng công cụ ngoài, và nhiều thư mục KHÔNG thuộc
quyền của engine (bài giảng, dự án riêng, khách hàng, bản vendored có git, nhạc nền, log cũ).
Luật: di trú chỉ được chạm đúng danh sách cho phép; mọi thứ khác phải y nguyên từng byte.
"""
import hashlib
import io
import json
import os

import pytest

from video_studio import API_VERSION, _env, station
from video_studio.cli import main as cli_main
from conftest import last_json

OTHER_DIRS = ("teach", "powerbi", "client-project", "video-use", "assets", "old-logs")


def _w(path, text="x"):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _pkg(pin):
    return json.dumps({"name": "demo", "scripts": {
        "render": f"npx --yes hyperframes@{pin} render",
        "check": f"npx --yes hyperframes@{pin} lint && npx --yes hyperframes@{pin} validate"}},
        indent=2)


def make_legacy_station(root):
    st = root / "station"
    for proj in ("news", "topstory"):
        _w(st / proj / "hyperframes.json", '{"registry": "r", "paths": {}}')
        _w(st / proj / "meta.json", '{"id": "demo"}')
        _w(st / proj / "package.json", _pkg("0.6.80"))
        _w(st / proj / "index.html", f"<html>{proj}</html>")
    _w(st / "news" / "img" / "s1.jpg", "jpg-bytes")
    _w(st / "topstory" / "media" / "a.png", "png-bytes")
    _w(st / "demo" / "hyperframes.json", "{}")
    _w(st / "demo" / "package.json", _pkg("0.6.80"))
    _w(st / "demo" / "compositions" / "intro.html", "<div/>")
    for tool in (".claude", ".agents"):
        _w(st / tool / "skills" / "legacy-skill" / "SKILL.md", "---\nname: legacy\n---\nold")
        _w(st / tool / "skills" / "video-routing" / "SKILL.md", "---\nname: video-routing\n---\nold")
    _w(st / "skills-lock.json", json.dumps({"version": 1, "skills": {"legacy-skill": {}}}))
    _w(st / "teach" / "make_lecture.ps1", "lecture")
    _w(st / "teach" / "bai" / "b1.md", "bai 1")
    _w(st / "powerbi" / "timings.json", "{}")
    _w(st / "client-project" / "brief.md", "khách hàng")
    _w(st / "video-use" / "helpers" / "render.py", "print(1)")
    _w(st / "video-use" / ".git" / "HEAD", "ref: refs/heads/main")
    _w(st / "assets" / "news-bgm" / "bgm-library.json", "{}")
    _w(st / "old-logs" / "logs" / "a.log", "log")
    _w(st / "AGENT_VIDEO_GUIDE.md", "guide")
    _w(st / "preview.ps1", "preview")
    return st


def make_repo_assets(root, monkeypatch, with_seed=True):
    """Nguồn skill + seed giả thay cho `skills/` và `templates/_seed/` của repo thật."""
    src = root / "repo-src"
    _w(src / "skills" / "video-routing" / "SKILL.md", "---\nname: video-routing\n---\nmới")
    _w(src / "skills" / "hyperframes" / "hf-core" / "SKILL.md", "---\nname: hf-core\n---\nlõi")
    _w(src / "skills" / "hyperframes" / "hf-core" / "references" / "a.md", "tham chiếu")
    monkeypatch.setattr(station, "_skills_root", lambda: str(src / "skills"))
    if with_seed:
        _w(src / "seed" / "hyperframes.json", "{}")
        _w(src / "seed" / "package.json", _pkg("0.0.0"))
        _w(src / "seed" / "compositions" / "intro.html", "<div>seed</div>")
        monkeypatch.setattr(station, "_seed_dir", lambda: str(src / "seed"))
    else:
        monkeypatch.setattr(station, "_seed_dir", lambda: None)
    return src


def voice_with_fillers(root, monkeypatch):
    fill = root / "voice" / "omnivoice" / "assets" / "news_short" / "fillers"
    _w(fill / "data" / "f1.json", '{"a": 1}')
    monkeypatch.setenv("VOICE_STATION", str(root / "voice"))
    return fill


def snapshot(path, skip=(".video-studio",)):
    """{đường tương đối: sha256 | '<dir>'} cho cả cây (bỏ thư mục nhật ký của engine)."""
    out = {}
    for dp, dn, fn in os.walk(path):
        rel_dp = os.path.relpath(dp, path)
        dn[:] = [d for d in dn if not (rel_dp == "." and d in skip)]
        for d in dn:
            out[os.path.normpath(os.path.join(rel_dp, d))] = "<dir>"
        for n in fn:
            with open(os.path.join(dp, n), "rb") as f:
                out[os.path.normpath(os.path.join(rel_dp, n))] = hashlib.sha256(f.read()).hexdigest()
    return out


def sub(snap, top):
    return {k: v for k, v in snap.items() if k == top or k.startswith(top + os.sep)}


def run(argv, capsys):
    rc = cli_main(argv)
    out = capsys.readouterr()
    return rc, out.out, out.err


# ── dry-run ─────────────────────────────────────────────────────────────────────────────

def test_dry_run_prints_plan_and_writes_nothing(tmp_path, monkeypatch, capsys):
    st = make_legacy_station(tmp_path)
    make_repo_assets(tmp_path, monkeypatch)
    voice_with_fillers(tmp_path, monkeypatch)
    before = snapshot(st)
    rc, out, err = run(["init", "--station", str(st), "--migrate", "--dry-run", "--json"], capsys)
    assert rc == 0, err
    assert snapshot(st) == before
    assert not (st / ".video-studio").exists()
    res = last_json(out)
    assert res["dry_run"] is True and res["mode"] == "separate"
    ops = {(p["op"], p.get("path") or p.get("dst")) for p in res["plan"]}
    assert ("move", "projects/news") in ops and ("move", "projects/topstory") in ops
    assert ("write", "station.json") in ops
    for name in OTHER_DIRS:
        assert name in res["untouched"]
    assert "xem trước" in err


# ── di trú thật ─────────────────────────────────────────────────────────────────────────

def test_migrate_moves_projects_and_leaves_others_byte_identical(tmp_path, monkeypatch, capsys):
    st = make_legacy_station(tmp_path)
    make_repo_assets(tmp_path, monkeypatch)
    voice_with_fillers(tmp_path, monkeypatch)
    monkeypatch.setenv("HYPERFRAMES_VERSION", "0.8.51")
    before = snapshot(st)
    rc, out, err = run(["init", "--station", str(st), "--migrate", "--json"], capsys)
    assert rc == 0, err
    after = snapshot(st)
    # không đụng
    for top in OTHER_DIRS + ("AGENT_VIDEO_GUIDE.md", "preview.ps1"):
        assert sub(after, top) == sub(before, top), top
    # skill đời cũ (không có trong repo) bị GỠ khi --migrate — nhưng chỉ đúng chúng
    for tool in (".claude", ".agents"):
        assert sub(before, os.path.join(tool, "skills", "legacy-skill")), "cây thử phải có skill cũ"
        assert sub(after, os.path.join(tool, "skills", "legacy-skill")) == {}
    # đã dời, giữ cấu hình project
    assert not (st / "news").exists() and not (st / "topstory").exists()
    assert (st / "projects" / "news" / "hyperframes.json").is_file()
    assert (st / "projects" / "news" / "meta.json").is_file()
    assert (st / "projects" / "news" / "img" / "s1.jpg").read_text(encoding="utf-8") == "jpg-bytes"
    assert (st / "projects" / "topstory" / "media" / "a.png").is_file()
    # ghim bản HyperFrames
    for pkg in ("projects/news/package.json", "projects/topstory/package.json", "demo/package.json"):
        text = (st / pkg).read_text(encoding="utf-8")
        assert "hyperframes@0.8.51" in text and "0.6.80" not in text, pkg
    # filler từ trạm giọng
    assert (st / "projects" / "news" / "assets" / "fillers" / "data" / "f1.json").is_file()
    # cây chuẩn
    for d in ("projects", "scratch", "cache"):
        assert (st / d).is_dir()
    info = json.loads((st / "station.json").read_text(encoding="utf-8"))
    assert info["contract"] == API_VERSION and info["mode"] == "separate"
    assert info["hyperframes_version"] == "0.8.51" and info["projects_dir"] == "projects"
    assert info["video_use"]["dir"] == "video-use"
    assert info["voice_station"] == str(tmp_path / "voice")
    # skill chép từ repo; bản cũ khác nội dung được thay (có lưu bản cũ để --undo)
    for tool in (".claude", ".agents"):
        assert "mới" in (st / tool / "skills" / "video-routing" / "SKILL.md").read_text(encoding="utf-8")
        assert (st / tool / "skills" / "hf-core" / "references" / "a.md").is_file()
    lock = json.loads((st / "skills-lock.json").read_text(encoding="utf-8"))
    assert lock["source"] == "agent-video-studio"
    assert set(lock["skills"]) == {"video-routing", "hf-core"}
    res = last_json(out)
    assert "legacy-skill" in res["legacy_skills"]
    assert sorted(res["pruned_skills"]) == [".agents/skills/legacy-skill",
                                            ".claude/skills/legacy-skill"]


def test_migrate_works_when_skills_and_repo_are_on_different_drives(tmp_path, monkeypatch, capsys):
    """`skills/` của repo và gốc repo KHÁC ổ đĩa ⇒ vẫn chạy, `skills-lock.json` ghi đường tuyệt đối.

    Runner Windows của GitHub checkout ở `D:\\a\\…` còn `TEMP` ở `C:\\`, nên `_skills_root()`
    (thư mục tạm của test) và `_env.package_repo()` (bản checkout) nằm trên hai ổ khác nhau —
    một tình huống HỢP LỆ mà máy để mọi thứ trên ổ `C:` không bao giờ dựng được. Ở đây nó được
    dựng lại đúng cơ chế của runner: chính `os.path.relpath` ném `ValueError`, và CHỈ khi
    `start` là gốc repo giả — mọi phép tính đường trong cùng một cây vẫn chạy thật, nên phép
    thử không bao giờ xanh nhờ một hàm giả dễ dãi, và nó chạy y hệt trên macOS.
    """
    other = os.path.join("D:" + os.sep if os.name == "nt" else os.sep, "a", "agent-video-studio")
    real_relpath = os.path.relpath

    def cross_drive(path, start=os.curdir):
        if os.path.normpath(str(start)) == os.path.normpath(other):
            raise ValueError(f"path is on mount {str(path)[:2]!r}, start on mount 'D:'")
        return real_relpath(path, start)

    monkeypatch.setattr(os.path, "relpath", cross_drive)
    monkeypatch.setattr(_env, "package_repo", lambda: other)

    st = make_legacy_station(tmp_path)
    src = make_repo_assets(tmp_path, monkeypatch)
    rc, out, err = run(["init", "--station", str(st), "--migrate", "--json"], capsys)
    assert rc == 0, err
    lock = json.loads((st / "skills-lock.json").read_text(encoding="utf-8"))
    assert set(lock["skills"]) == {"video-routing", "hf-core"}
    want = str(src / "skills" / "video-routing").replace(os.sep, "/")
    assert lock["skills"]["video-routing"]["path"] == want
    for info in lock["skills"].values():
        assert not info["path"].startswith(".."), "khác ổ đĩa thì không có đường tương đối nào đúng"


# ── dọn skill đời cũ ở trạm ─────────────────────────────────────────────────────────────

def test_plain_init_reports_legacy_skills_but_never_removes_them(tmp_path, monkeypatch, capsys):
    """Không `--migrate` thì chỉ BÁO. Gỡ dữ liệu người dùng phải là một lựa chọn tường minh."""
    st = make_legacy_station(tmp_path)
    make_repo_assets(tmp_path, monkeypatch)
    rc, out, err = run(["init", "--station", str(st), "--json"], capsys)
    assert rc == 0, err
    res = last_json(out)
    assert "legacy-skill" in res["legacy_skills"]
    assert res["pruned_skills"] == []
    for tool in (".claude", ".agents"):
        assert (st / tool / "skills" / "legacy-skill" / "SKILL.md").is_file()


def test_migrate_prune_keeps_a_restorable_copy(tmp_path, monkeypatch, capsys):
    """Gỡ = dời vào nhật ký, KHÔNG xoá đệ quy: `--undo` phải trả lại từng byte."""
    st = make_legacy_station(tmp_path)
    make_repo_assets(tmp_path, monkeypatch)
    old = (st / ".claude" / "skills" / "legacy-skill" / "SKILL.md").read_text(encoding="utf-8")
    assert run(["init", "--station", str(st), "--migrate"], capsys)[0] == 0
    assert not (st / ".claude" / "skills" / "legacy-skill").exists()
    # bản cũ còn nằm đâu đó dưới nhật ký của lần init
    saved = list((st / ".video-studio").rglob("legacy-skill/SKILL.md"))
    assert saved, "gỡ mà không lưu bản cũ thì --undo không trả lại được"
    assert saved[0].read_text(encoding="utf-8") == old
    assert run(["init", "--station", str(st), "--undo"], capsys)[0] == 0
    assert (st / ".claude" / "skills" / "legacy-skill" / "SKILL.md").read_text(encoding="utf-8") == old


def test_migrate_never_prunes_a_skill_the_repo_provides(tmp_path, monkeypatch, capsys):
    """Skill trùng tên với repo được THAY (có lưu bản cũ), không bị tính là đời cũ."""
    st = make_legacy_station(tmp_path)
    make_repo_assets(tmp_path, monkeypatch)
    rc, out, err = run(["init", "--station", str(st), "--migrate", "--json"], capsys)
    assert rc == 0, err
    res = last_json(out)
    assert "video-routing" not in res["legacy_skills"]
    assert not any("video-routing" in rel for rel in res["pruned_skills"])
    assert (st / ".claude" / "skills" / "video-routing" / "SKILL.md").is_file()


def test_dry_run_prints_prune_but_writes_nothing(tmp_path, monkeypatch, capsys):
    st = make_legacy_station(tmp_path)
    make_repo_assets(tmp_path, monkeypatch)
    before = snapshot(st)
    rc, out, err = run(["init", "--station", str(st), "--migrate", "--dry-run"], capsys)
    assert rc == 0, err
    log = out + err
    assert "legacy-skill" in log and "gỡ skill đời cũ" in log
    assert snapshot(st) == before


def test_undo_restores_tree_exactly(tmp_path, monkeypatch, capsys):
    st = make_legacy_station(tmp_path)
    make_repo_assets(tmp_path, monkeypatch)
    voice_with_fillers(tmp_path, monkeypatch)
    before = snapshot(st)
    assert run(["init", "--station", str(st), "--migrate"], capsys)[0] == 0
    assert snapshot(st) != before
    rc, out, err = run(["init", "--station", str(st), "--undo", "--json"], capsys)
    assert rc == 0, err
    assert snapshot(st) == before
    assert last_json(out)["undone"] > 0
    # hết việc để hoàn tác ⇒ mã 2
    assert run(["init", "--station", str(st), "--undo"], capsys)[0] == 2


def test_undo_dry_run_changes_nothing(tmp_path, monkeypatch, capsys):
    st = make_legacy_station(tmp_path)
    make_repo_assets(tmp_path, monkeypatch)
    assert run(["init", "--station", str(st), "--migrate"], capsys)[0] == 0
    mid = snapshot(st)
    assert run(["init", "--station", str(st), "--undo", "--dry-run"], capsys)[0] == 0
    assert snapshot(st) == mid


def test_undo_keeps_file_user_edited_after_init(tmp_path, monkeypatch, capsys):
    st = make_legacy_station(tmp_path)
    make_repo_assets(tmp_path, monkeypatch)
    assert run(["init", "--station", str(st), "--migrate"], capsys)[0] == 0
    sj = st / "station.json"
    sj.write_text('{"sửa": "tay"}', encoding="utf-8")
    rc, out, err = run(["init", "--station", str(st), "--undo", "--json"], capsys)
    assert rc == 0
    assert sj.read_text(encoding="utf-8") == '{"sửa": "tay"}'
    assert any("station.json" in k for k in last_json(out)["kept"])
    assert (st / "news" / "hyperframes.json").is_file()


def test_migrate_is_idempotent(tmp_path, monkeypatch, capsys):
    st = make_legacy_station(tmp_path)
    make_repo_assets(tmp_path, monkeypatch)
    assert run(["init", "--station", str(st), "--migrate"], capsys)[0] == 0
    first = snapshot(st)
    rc, out, _ = run(["init", "--station", str(st), "--migrate", "--json"], capsys)
    assert rc == 0
    assert last_json(out)["plan"] == []
    assert snapshot(st) == first


def test_conflict_stops_before_touching_anything(tmp_path, monkeypatch, capsys):
    st = make_legacy_station(tmp_path)
    make_repo_assets(tmp_path, monkeypatch)
    _w(st / "projects" / "news" / "index.html", "đã có")
    before = snapshot(st)
    rc, out, err = run(["init", "--station", str(st), "--migrate", "--json"], capsys)
    assert rc == 2
    assert "projects/news" in last_json(out)["error"]
    assert snapshot(st) == before


def test_failure_midway_rolls_back(tmp_path, monkeypatch, capsys):
    st = make_legacy_station(tmp_path)
    make_repo_assets(tmp_path, monkeypatch)
    before = snapshot(st)
    real = station._move_tree
    calls = {"n": 0}

    def flaky(src, dst):
        calls["n"] += 1
        if calls["n"] == 2:
            raise station.ContractError("giả lập: file đang bị giữ")
        return real(src, dst)
    monkeypatch.setattr(station, "_move_tree", flaky)
    rc, out, err = run(["init", "--station", str(st), "--migrate"], capsys)
    assert rc == 2
    assert snapshot(st) == before
    assert "hoàn tác" in err


def test_migrate_on_missing_station_is_code_3(tmp_path, monkeypatch, capsys):
    make_repo_assets(tmp_path, monkeypatch)
    rc, _, _ = run(["init", "--station", str(tmp_path / "nope"), "--migrate"], capsys)
    assert rc == 3


def test_broken_station_json_is_code_2(tmp_path, monkeypatch, capsys):
    st = make_legacy_station(tmp_path)
    make_repo_assets(tmp_path, monkeypatch)
    _w(st / "station.json", "{hỏng")
    assert run(["init", "--station", str(st), "--migrate"], capsys)[0] == 2


def test_plain_init_does_not_migrate_or_replace(tmp_path, monkeypatch, capsys):
    """Không có --migrate: không dời project cũ, không thay skill khác nội dung — chỉ báo."""
    st = make_legacy_station(tmp_path)
    make_repo_assets(tmp_path, monkeypatch)
    rc, out, _ = run(["init", "--station", str(st), "--json"], capsys)
    assert rc == 0
    assert (st / "news" / "index.html").is_file()
    assert "old" in (st / ".claude" / "skills" / "video-routing" / "SKILL.md").read_text(encoding="utf-8")
    res = last_json(out)
    assert any("--migrate" in n for n in res["notes"])
    assert json.loads((st / "skills-lock.json").read_text(encoding="utf-8")).get("source") is None


# ── trạm mới + chế độ (M8) ──────────────────────────────────────────────────────────────

def test_fresh_station_from_seed_and_undo(tmp_path, monkeypatch, capsys):
    make_repo_assets(tmp_path, monkeypatch)
    st = tmp_path / "new-station"
    rc, out, err = run(["init", "--station", str(st), "--json"], capsys)
    assert rc == 0, err
    assert (st / "demo" / "compositions" / "intro.html").is_file()
    pkg = (st / "demo" / "package.json").read_text(encoding="utf-8")
    assert f"hyperframes@{_env.DEFAULT_HYPERFRAMES_VERSION}" in pkg and "0.0.0" not in pkg
    for d in ("projects", "scratch", "cache", ".claude/skills/hf-core", ".agents/skills/video-routing"):
        assert (st / d).is_dir(), d
    assert run(["init", "--station", str(st), "--undo"], capsys)[0] == 0
    assert snapshot(st) == {}


def test_no_seed_in_repo_is_reported_not_fatal(tmp_path, monkeypatch, capsys):
    make_repo_assets(tmp_path, monkeypatch, with_seed=False)
    st = tmp_path / "s"
    rc, out, _ = run(["init", "--station", str(st), "--json"], capsys)
    assert rc == 0
    assert not (st / "demo").exists()
    assert any("_seed" in n for n in last_json(out)["notes"])


def test_station_flag_means_separate_never_asks(tmp_path, monkeypatch, capsys):
    """M8: --station tường minh = separate, không hỏi, không tạo workspace/ trong repo."""
    make_repo_assets(tmp_path, monkeypatch)
    repo = tmp_path / "repo"
    (repo / "video_studio").mkdir(parents=True)
    (repo / "pyproject.toml").write_text("", encoding="utf-8")
    monkeypatch.setenv("VIDEO_STUDIO_REPO", str(repo))
    monkeypatch.setattr("sys.stdin", io.StringIO(""))
    rc, out, _ = run(["init", "--station", str(tmp_path / "s"), "--json"], capsys)
    assert rc == 0
    res = last_json(out)
    assert res["mode"] == "separate" and res["reason"] == "--station"
    assert not (repo / "workspace").exists()
    local = json.loads((repo / "studio.local.json").read_text(encoding="utf-8"))
    assert local["mode"] == "separate" and local["station_path"] == str(tmp_path / "s")


def test_legacy_home_station_detected_without_flag(tmp_path, monkeypatch, capsys):
    """~/.video đời cũ (chưa station.json, biến chưa đặt) vẫn được nhận ra ⇒ separate, không hỏi."""
    make_repo_assets(tmp_path, monkeypatch)
    home_st = make_legacy_station(tmp_path)
    os.replace(home_st, tmp_path / "home" / ".video")
    rc, out, _ = run(["init", "--migrate", "--dry-run", "--json"], capsys)
    assert rc == 0
    res = last_json(out)
    assert res["mode"] == "separate" and "~/.video" in res["reason"]


def test_embedded_needs_a_human_choice(tmp_path, monkeypatch, capsys):
    make_repo_assets(tmp_path, monkeypatch)
    repo = tmp_path / "repo"
    (repo / "video_studio").mkdir(parents=True)
    (repo / "pyproject.toml").write_text("", encoding="utf-8")
    monkeypatch.setenv("VIDEO_STUDIO_REPO", str(repo))
    monkeypatch.setattr("sys.stdin", io.StringIO(""))
    rc, out, err = run(["init", "--json"], capsys)
    assert rc == 2 and "embedded" in err and "KHUYẾN NGHỊ" in err
    assert not (repo / "workspace").exists()
    rc, out, _ = run(["init", "--yes", "--json"], capsys)
    assert rc == 0
    assert last_json(out)["mode"] == "embedded"
    assert (repo / "workspace" / "station.json").is_file()


def test_migrate_refuses_embedded(tmp_path, monkeypatch, capsys):
    make_repo_assets(tmp_path, monkeypatch)
    repo = tmp_path / "repo"
    (repo / "video_studio").mkdir(parents=True)
    (repo / "pyproject.toml").write_text("", encoding="utf-8")
    monkeypatch.setenv("VIDEO_STUDIO_REPO", str(repo))
    assert run(["init", "--yes", "--migrate"], capsys)[0] == 2


def test_invalid_hyperframes_version_is_code_2(tmp_path, monkeypatch, capsys):
    make_repo_assets(tmp_path, monkeypatch)
    monkeypatch.setenv("HYPERFRAMES_VERSION", "latest")
    assert run(["init", "--station", str(tmp_path / "s")], capsys)[0] == 2
    assert not (tmp_path / "s").exists()


def test_plan_guard_refuses_paths_outside_allowlist(tmp_path):
    with pytest.raises(AssertionError):
        station._guard([{"op": "move", "src": "teach", "dst": "projects/teach"}])
