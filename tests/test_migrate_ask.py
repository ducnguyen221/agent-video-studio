"""`video-studio migrate --to separate` phải HỎI nơi dời, không tự dời vào một thư mục ẩn ở thư mục cá nhân.

Luật: không có `--station` ⇒ hỏi (gợi ý `<OPCOS_WORKSPACES>/video` nếu biến có), hiện đường
tuyệt đối + số file/dung lượng rồi xin xác nhận y/N; không có người ⇒ dừng mã 2. Biến chỉ đọc
từ môi trường thật. Không còn đường mặc định ngầm vào thư mục ẩn ở home.
"""
import os

import pytest

from video_studio import station
from video_studio.cli import main as cli_main
from video_studio.contract import ContractError


@pytest.fixture
def repo(tmp_path, monkeypatch):
    r = tmp_path / "repo"
    (r / "video_studio").mkdir(parents=True)
    (r / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
    (r / ".env.example").write_text("# khuon\nVIDEO_FONT=\n", encoding="utf-8")
    monkeypatch.setenv("VIDEO_STUDIO_REPO", str(r))
    station.do_init(mode="embedded")
    (r / "workspaces" / "projects" / "news").mkdir(parents=True)
    (r / "workspaces" / "projects" / "news" / "meta.json").write_text("{}", encoding="utf-8")
    return r


def _script(*answers):
    """Trả lời lần lượt; ghi lại các câu hỏi để kiểm nội dung."""
    seen, it = [], iter(answers)

    def ask(prompt):
        seen.append(prompt)
        return next(it)
    ask.seen = seen
    return ask


def test_no_station_asks_and_takes_the_typed_destination(repo, tmp_path):
    target = tmp_path / "ngoai"
    ask = _script(str(target), "y")
    res = station.migrate_to_separate(ask=ask)
    assert res["station"] == str(target)
    assert (target / "projects" / "news" / "meta.json").is_file()
    assert not (repo / "workspaces").exists()


def test_the_question_suggests_workspaces_video_and_shows_absolute_path_and_size(
        repo, tmp_path, monkeypatch):
    base = tmp_path / "ws"
    monkeypatch.setenv("OPCOS_WORKSPACES", str(base))
    ask = _script("", "y")                      # Enter = nhận gợi ý
    res = station.migrate_to_separate(ask=ask)
    expect = os.path.abspath(str(base / "video"))
    assert res["station"] == expect
    assert expect in ask.seen[0] and "gợi ý" in ask.seen[0].lower()
    # lượt xác nhận nêu đích tuyệt đối + số file + dung lượng sẽ dời
    assert expect in ask.seen[1] and "file" in ask.seen[1] and "y/N" in ask.seen[1]


def test_a_relative_opcos_workspaces_is_shown_and_used_as_absolute(repo, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OPCOS_WORKSPACES", "rel-ws")
    ask = _script("", "y")
    res = station.migrate_to_separate(ask=ask)
    assert os.path.isabs(res["station"])
    assert res["station"] == os.path.abspath(os.path.join("rel-ws", "video"))


def test_no_suggestion_and_empty_answer_stops_without_moving(repo, tmp_path):
    with pytest.raises(ContractError):
        station.migrate_to_separate(ask=_script(""))
    assert (repo / "workspaces").is_dir()


@pytest.mark.parametrize("no", ["", "n", "N", "no", "khong"])
def test_anything_but_yes_cancels_and_moves_nothing(repo, tmp_path, no):
    target = tmp_path / "ngoai"
    with pytest.raises(ContractError, match="huỷ"):
        station.migrate_to_separate(ask=_script(str(target), no))
    assert (repo / "workspaces" / "projects" / "news" / "meta.json").is_file()
    assert not target.exists()


def test_never_defaults_to_the_hidden_home_station(repo, tmp_path, monkeypatch):
    """Gợi ý nơi dời không bao giờ là một thư mục ẩn ở thư mục cá nhân."""
    monkeypatch.setenv("OPCOS_WORKSPACES", str(tmp_path / "ws"))
    ask = _script("", "n")
    with pytest.raises(ContractError):
        station.migrate_to_separate(ask=ask)
    assert all(os.path.expanduser("~") not in p for p in ask.seen)


def test_an_explicit_target_does_not_ask(repo, tmp_path):
    def boom(prompt):
        pytest.fail("đã có --station thì không hỏi")

    res = station.migrate_to_separate(str(tmp_path / "ngoai"), ask=boom)
    assert res["station"] == str(tmp_path / "ngoai")


def test_a_target_inside_the_workspace_is_refused(repo):
    with pytest.raises(ContractError, match="nằm trong trạm đang dời"):
        station.migrate_to_separate(str(repo / "workspaces" / "con"))
    assert (repo / "workspaces").is_dir()


def test_cli_non_interactive_without_station_is_exit_2_and_names_the_flag(repo, capsys):
    code = cli_main(["migrate", "--to", "separate", "--non-interactive"])
    err = capsys.readouterr().err
    assert code == 2 and "--station" in err and "bắt buộc" in err
    assert (repo / "workspaces").is_dir()


def test_cli_without_a_tty_and_without_station_is_exit_2(repo, capsys, monkeypatch):
    monkeypatch.setattr(station, "_stdin_is_tty", lambda: False)
    code = cli_main(["migrate", "--to", "separate"])
    err = capsys.readouterr().err
    assert code == 2 and "--station" in err and "bắt buộc" in err
    assert (repo / "workspaces").is_dir()


def test_cli_with_station_moves_without_asking(repo, tmp_path):
    target = tmp_path / "ngoai"
    code = cli_main(["migrate", "--to", "separate", "--station", str(target),
                     "--non-interactive"])
    assert code == 0
    assert (target / "projects" / "news" / "meta.json").is_file()


def test_the_help_does_not_promise_the_hidden_default(capsys):
    assert station.migrate_main(["--help"]) == 0
    assert os.path.expanduser("~") not in capsys.readouterr().out


def test_a_destination_that_is_a_file_is_a_clear_error_not_a_traceback(repo, tmp_path):
    f = tmp_path / "la-file"
    f.write_text("x", encoding="utf-8")
    with pytest.raises(ContractError, match="không phải thư mục"):
        station.migrate_to_separate(str(f))
    ask = _script(str(f), "y")
    with pytest.raises(ContractError, match="không phải thư mục"):
        station.migrate_to_separate(ask=ask)
    assert len(ask.seen) == 1 and f.read_text(encoding="utf-8") == "x"
    assert (repo / "workspaces").is_dir()
    assert cli_main(["migrate", "--to", "separate", "--station", str(f)]) == 2


def test_a_pasted_quoted_destination_is_unquoted(repo, tmp_path):
    target = tmp_path / "co dau cach"
    res = station.migrate_to_separate(ask=_script(f'"{target}"', "y"))
    assert res["station"] == str(target) and (target / "projects" / "news" / "meta.json").is_file()


def test_an_existing_secret_env_is_reported_before_the_y_n_question(repo, tmp_path, monkeypatch):
    """Không để người dùng trả lời y rồi mới nghe ".env đã có": kiểm xong trước khi xin y/N."""
    home = tmp_path / "home"
    (home / ".secret" / station.SECRET_DIR_NAME).mkdir(parents=True)
    (home / ".secret" / station.SECRET_DIR_NAME / ".env").write_text("x=1\n", encoding="utf-8")
    monkeypatch.setenv("USERPROFILE", str(home))
    monkeypatch.setenv("HOME", str(home))
    (repo / ".env").write_text("A=1\n", encoding="utf-8")
    ask = _script(str(tmp_path / "ngoai"), "y")
    with pytest.raises(ContractError, match="đã có"):
        station.migrate_to_separate(ask=ask)
    assert len(ask.seen) == 1                    # chỉ câu hỏi đường; chưa tới câu y/N
    assert (repo / "workspaces").is_dir()


# ── đích đi qua điểm nối (junction) vào chính trạm đang dời ─────────────────────────────────────

def _junction(link, target):
    """Tạo điểm nối `link → target` (Windows `mklink /J`, không cần quyền nâng); symlink ở nơi khác."""
    import subprocess
    try:
        os.symlink(str(target), str(link), target_is_directory=True)
        return
    except (OSError, NotImplementedError) as e:
        if os.name != "nt" or subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(target)],
                                             capture_output=True).returncode:
            pytest.skip(f"máy này không tạo được liên kết mềm lẫn điểm nối: {e}")


def test_a_target_through_a_junction_into_the_workspace_is_refused_before_touching_anything(
        repo, tmp_path):
    inside = repo / "workspaces" / "sub"
    inside.mkdir()
    (repo / "workspaces" / "data.txt").write_text("du lieu", encoding="utf-8")
    link = tmp_path / "lnk"
    _junction(link, inside)
    local_before = (repo / "studio.local.json").read_text(encoding="utf-8")
    with pytest.raises(ContractError, match="nằm trong trạm"):
        station.migrate_to_separate(str(link / "new"))
    assert (repo / "workspaces" / "data.txt").read_text(encoding="utf-8") == "du lieu"
    assert (repo / "studio.local.json").read_text(encoding="utf-8") == local_before
    assert not (inside / "new").exists() and not (link / "new").exists()


def test_a_junction_that_is_itself_the_target_is_refused_before_the_yes_no_question(repo, tmp_path):
    link = tmp_path / "lnk"
    _junction(link, repo / "workspaces")
    asked = []
    with pytest.raises(ContractError, match="nằm trong trạm"):
        station.migrate_to_separate(str(link), ask=lambda p: asked.append(p) or "y", confirm=True)
    assert asked == []
    assert (repo / "workspaces" / "projects" / "news" / "meta.json").is_file()


def test_a_workspace_that_is_itself_a_junction_still_refuses_a_target_inside_the_real_folder(
        repo, tmp_path):
    real = tmp_path / "that-su"
    os.rename(repo / "workspaces", real)
    _junction(repo / "workspaces", real)
    with pytest.raises(ContractError, match="nằm trong trạm"):
        station.migrate_to_separate(str(real / "new"))
    assert (real / "projects" / "news" / "meta.json").is_file()


def test_is_inside_compares_real_paths_in_both_directions(tmp_path):
    a = tmp_path / "a"
    (a / "b").mkdir(parents=True)
    link = tmp_path / "lnk"
    _junction(link, a)
    assert station._is_inside(str(link / "b"), str(a))
    assert station._is_inside(str(a / "b"), str(link))
    assert station._is_inside(str(a), str(link)) and not station._is_inside(str(tmp_path), str(a))
