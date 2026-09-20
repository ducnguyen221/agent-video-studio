"""Hai chế độ cài (F17): `embedded` (trạm trong repo) và `separate` (trạm ngoài).

Ba thứ được kiểm ở đây, và cả ba đều là chỗ đã suýt hỏng:

* **Không bao giờ đẻ `workspace/` trên máy đã có trạm ngoài** — hai trạm cho một repo là hai
  nguồn sự thật, và cái sai chỉ lộ ra khi người dùng "mất" project.
* **Không tự chọn thay người dùng** khi không có ai trả lời: in bảng lựa chọn rồi thoát mã 2.
* **Chế độ embedded phải có hai lớp rào** (`.gitignore` + hook `pre-commit`) trước khi có một
  byte dữ liệu nào nằm trong repo.
"""
import io
import json
import os
import zipfile

import pytest

from video_studio import _env, precommit, station
from video_studio.contract import ContractError, StationMissing


@pytest.fixture
def repo(tmp_path, monkeypatch):
    """Một bản clone giả: có pyproject + package + skills + templates như repo thật."""
    r = tmp_path / "repo"
    (r / "video_studio").mkdir(parents=True)
    (r / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
    monkeypatch.setenv("VIDEO_STUDIO_REPO", str(r))
    return r


def _ask(answer):
    return lambda prompt: answer


# ── chọn chế độ ────────────────────────────────────────────────────────────────────────

def test_enter_means_embedded(repo):
    mode, st, why = station.choose_mode(ask=_ask(""))
    assert mode == "embedded" and st == str(repo / "workspace") and why == "người dùng chọn"


def test_two_means_separate(repo):
    mode, st, _why = station.choose_mode(ask=_ask("2"))
    assert mode == "separate" and st == _env.default_station()


def test_station_flag_is_separate_without_asking(repo, tmp_path):
    def boom(prompt):
        pytest.fail("--station rồi thì không được hỏi nữa")

    mode, st, why = station.choose_mode(station=str(tmp_path / "ngoai"), ask=boom)
    assert mode == "separate" and why == "--station" and st == str(tmp_path / "ngoai")


def test_an_existing_outside_station_wins_and_is_never_asked_about(repo, tmp_path, monkeypatch):
    outside = tmp_path / "co-san"
    (outside / "projects").mkdir(parents=True)
    monkeypatch.setenv("VIDEO_STATION", str(outside))
    mode, st, why = station.choose_mode(ask=lambda p: pytest.fail("không được hỏi"))
    assert (mode, st) == ("separate", str(outside))
    assert "VIDEO_STATION" in why


def test_a_legacy_home_station_is_recognised(repo, tmp_path, monkeypatch):
    """Trạm đời cũ chưa có station.json vẫn phải được nhận ra (mâu thuẫn M8 của kế hoạch)."""
    home = tmp_path / "home"
    (home / ".video" / "demo").mkdir(parents=True)
    (home / ".video" / "demo" / "hyperframes.json").write_text("{}", encoding="utf-8")
    monkeypatch.setenv("USERPROFILE", str(home))
    monkeypatch.setenv("HOME", str(home))
    mode, st, why = station.choose_mode(ask=lambda p: pytest.fail("không được hỏi"))
    assert mode == "separate" and st == str(home / ".video") and "trạm" in why


def test_asking_for_embedded_on_a_machine_with_an_outside_station_is_refused(
        repo, tmp_path, monkeypatch):
    monkeypatch.setenv("VIDEO_STATION", str(tmp_path / "ngoai"))
    (tmp_path / "ngoai" / "projects").mkdir(parents=True)
    with pytest.raises(ContractError) as e:
        station.choose_mode(mode="embedded")
    assert "hai nguồn sự thật" in str(e.value)


def test_no_one_to_answer_prints_the_table_and_exits_code_2(repo, capsys, monkeypatch):
    monkeypatch.setattr(station, "_stdin_is_tty", lambda: False)
    assert station.init_main([]) == 2
    err = capsys.readouterr().err
    assert "embedded" in err and "separate" in err and "KHUYẾN NGHỊ" in err
    assert not (repo / "workspace").exists(), "chưa ai chọn mà đã tạo workspace/"


def test_previous_choice_is_remembered(repo):
    (repo / "studio.local.json").write_text(json.dumps({"mode": "embedded"}), encoding="utf-8")
    mode, _st, why = station.choose_mode(ask=lambda p: pytest.fail("đã chọn rồi thì đừng hỏi"))
    assert mode == "embedded" and "studio.local.json" in why


def test_embedded_needs_a_clone(monkeypatch, tmp_path):
    monkeypatch.setenv("VIDEO_STUDIO_REPO", str(tmp_path / "khong-phai-repo"))
    with pytest.raises(ContractError) as e:
        station.choose_mode(mode="embedded")
    assert "wheel" in str(e.value)


# ── dựng trạm theo từng chế độ ─────────────────────────────────────────────────────────

def test_embedded_builds_the_station_inside_the_repo(repo):
    res = station.do_init(mode="embedded")
    ws = repo / "workspace"
    assert res["mode"] == "embedded" and res["station"] == str(ws)
    for d in ("projects", "scratch", "cache"):
        assert (ws / d).is_dir()
    assert (ws / "station.json").is_file()
    assert json.loads((repo / "studio.local.json").read_text(encoding="utf-8"))["mode"] == "embedded"


def test_separate_never_creates_a_workspace(repo, tmp_path):
    st = tmp_path / "ngoai"
    res = station.do_init(station=str(st))
    assert res["mode"] == "separate"
    assert not (repo / "workspace").exists()
    assert (st / "station.json").is_file()


def test_a_brand_new_station_gets_the_sample_tree(repo, tmp_path):
    station.do_init(station=str(tmp_path / "moi"))
    st = tmp_path / "moi"
    assert (st / "README.md").is_file()
    assert (st / "projects" / "_example" / "README.md").is_file()
    assert (st / "templates" / "README.md").is_file()


def test_an_existing_station_is_not_littered_with_sample_files(repo, tmp_path):
    st = tmp_path / "dang-dung"
    (st / "projects" / "news").mkdir(parents=True)
    station.do_init(station=str(st))
    assert not (st / "README.md").exists(), "trạm đang dùng là của người ta"
    assert not (st / "templates").exists()


def test_init_is_idempotent(repo, tmp_path):
    st = str(tmp_path / "st")
    station.do_init(station=st)
    again = station.do_init(station=st)
    assert again["plan"] == []


def test_dry_run_writes_nothing(repo, tmp_path):
    st = tmp_path / "xem-truoc"
    res = station.do_init(station=str(st), dry_run=True)
    assert res["plan"] and not st.exists()


# ── hai lớp rào của chế độ embedded ────────────────────────────────────────────────────

def test_embedded_installs_the_pre_commit_hook(repo):
    (repo / ".git" / "hooks").mkdir(parents=True)
    res = station.do_init(mode="embedded")
    hook = repo / ".git" / "hooks" / "pre-commit"
    assert res["hook"] == "installed" and hook.is_file()
    assert "video_studio.precommit" in hook.read_text(encoding="utf-8")


def test_an_existing_hook_is_never_overwritten(repo):
    (repo / ".git" / "hooks").mkdir(parents=True)
    hook = repo / ".git" / "hooks" / "pre-commit"
    hook.write_text("#!/bin/sh\necho hook cua nguoi khac\n", encoding="utf-8")
    assert station.do_init(mode="embedded")["hook"] == "kept"
    assert "nguoi khac" in hook.read_text(encoding="utf-8")


def test_separate_mode_does_not_install_a_hook(repo, tmp_path):
    (repo / ".git" / "hooks").mkdir(parents=True)
    assert "hook" not in station.do_init(station=str(tmp_path / "st"))


@pytest.mark.parametrize("path,blocked", [
    ("workspace/projects/news/index.html", True),
    ("studio.local.json", True),
    (".env", True),
    (".env.production", True),
    (".env.example", False),
    ("docs/a.mp4", True),
    ("skills/x/font.woff2", True),
    ("templates/_seed/assets/swiss-grid.svg", False),   # .svg là văn bản, không phải media
    # Ngoại lệ media từng mở CẢ THƯ MỤC `templates/_seed/assets/`: hôm nay nó chỉ có README,
    # nhưng một ngoại lệ theo thư mục thì ai đặt gì vào đó sau này cũng lọt.
    ("templates/_seed/assets/logo.png", True),
    ("templates/_seed/assets/nhac.mp3", True),
    ("video_studio/render.py", False),
])
def test_hook_blocks_what_must_never_be_committed(path, blocked):
    assert bool(precommit.blocked_path(path)) is blocked


def test_no_media_exception_opens_a_whole_folder():
    """Giáo lý của `.gitignore` repo này: không bao giờ mở cả thư mục cho file nhị phân."""
    assert all(not a.endswith("/") for a in precommit.MEDIA_ALLOW), \
        f"ngoại lệ theo THƯ MỤC: {[a for a in precommit.MEDIA_ALLOW if a.endswith('/')]}"


def test_hook_spots_a_token_in_an_added_line():
    diff = ("+++ b/config.py\n"
            "+API_KEY = \"" + "s" * 40 + "\"\n"
            "-API_KEY = old\n")
    assert precommit.token_lines(diff)


def test_hook_ignores_a_removed_line():
    assert precommit.token_lines("+++ b/a.py\n-token = \"" + "s" * 40 + "\"\n") == []


# ── backup / migrate / update ──────────────────────────────────────────────────────────

def test_backup_skips_scratch_and_cache(repo, tmp_path):
    st = tmp_path / "st"
    station.do_init(station=str(st))
    (st / "projects" / "news").mkdir(parents=True)
    (st / "projects" / "news" / "meta.json").write_text("{}", encoding="utf-8")
    (st / "scratch" / "rac.mp4").write_text("x", encoding="utf-8")
    (st / "cache" / "x.bin").write_text("x", encoding="utf-8")
    out = station.backup(str(tmp_path / "bak.zip"), station=str(st))
    names = set(out["files"])
    assert "projects/news/meta.json" in names
    assert not [n for n in names if n.startswith(("scratch/", "cache/", ".video-studio/"))]
    with zipfile.ZipFile(out["out"]) as z:
        manifest = json.loads(z.read("manifest.json"))
        assert manifest["station"] == str(st)
        assert "station/projects/news/meta.json" in z.namelist()


def test_backup_of_a_missing_station_is_code_3(tmp_path):
    with pytest.raises(StationMissing):
        station.backup(str(tmp_path / "b.zip"), station=str(tmp_path / "khong-co"))


def test_migrate_moves_the_workspace_out_and_rewrites_the_choice(repo, tmp_path):
    station.do_init(mode="embedded")
    (repo / "workspace" / "projects" / "news").mkdir(parents=True)
    (repo / "workspace" / "projects" / "news" / "meta.json").write_text("{}", encoding="utf-8")
    target = tmp_path / "ngoai"
    res = station.migrate_to_separate(str(target))
    assert res["station"] == str(target)
    assert not (repo / "workspace").exists()
    assert (target / "projects" / "news" / "meta.json").is_file()
    local = json.loads((repo / "studio.local.json").read_text(encoding="utf-8"))
    assert local["mode"] == "separate" and local["station_path"] == str(target)
    assert json.loads((target / "station.json").read_text(encoding="utf-8"))["mode"] == "separate"


def test_migrate_refuses_a_non_empty_target_before_moving_anything(repo, tmp_path):
    station.do_init(mode="embedded")
    target = tmp_path / "co-do-roi"
    target.mkdir()
    (target / "cua-toi.txt").write_text("x", encoding="utf-8")
    with pytest.raises(ContractError) as e:
        station.migrate_to_separate(str(target))
    assert "không rỗng" in str(e.value)
    assert (repo / "workspace").is_dir(), "chưa đụng gì khi từ chối"


def test_migrate_without_embedded_is_refused(repo, tmp_path):
    with pytest.raises(ContractError) as e:
        station.migrate_to_separate(str(tmp_path / "x"))
    assert "embedded" in str(e.value)


def test_update_needs_a_git_clone(repo):
    with pytest.raises(ContractError) as e:
        station.update()
    assert "bản clone" in str(e.value)


def test_update_never_cleans(repo, monkeypatch):
    (repo / ".git").mkdir()
    seen = {}

    class R:
        returncode, stdout, stderr = 0, "Already up to date.", ""

    def fake_run(argv, **kw):
        seen["argv"] = argv
        return R()

    monkeypatch.setattr(station.subprocess, "run", fake_run)
    assert station.update()["output"] == "Already up to date."
    assert seen["argv"][-2:] == ["pull", "--ff-only"]
    assert "clean" not in seen["argv"]


def test_a_failing_pull_keeps_everything(repo, monkeypatch):
    (repo / ".git").mkdir()

    class R:
        returncode, stdout, stderr = 1, "", "local changes"

    monkeypatch.setattr(station.subprocess, "run", lambda argv, **kw: R())
    with pytest.raises(Exception) as e:
        station.update()
    assert "Không xoá gì" in str(e.value)
