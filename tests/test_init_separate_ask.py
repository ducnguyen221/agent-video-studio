"""`init --mode separate` không còn đường mặc định ngầm vào `~/.video`.

Luật: chọn `separate` mà không có `--station` ⇒ có `OPCOS_WORKSPACES` thì gợi ý
`<biến>/video` (đường tuyệt đối): có người thì HỎI xác nhận/đổi, không có người thì dùng luôn
đường đó và nói ra một dòng; không có biến thì có người ⇒ HỎI đường (Enter rỗng = dừng),
không có người ⇒ mã 2 đòi `--station`. Không bao giờ rơi về `~/.video`. Biến chỉ đọc từ môi
trường thật (một điểm đọc: `_env.opcos_base`).
"""
import os

import pytest

from video_studio import _env, station
from video_studio.contract import ContractError


@pytest.fixture
def repo(tmp_path, monkeypatch):
    r = tmp_path / "repo"
    (r / "video_studio").mkdir(parents=True)
    (r / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
    (r / ".env.example").write_text("# khuon\nVIDEO_FONT=\n", encoding="utf-8")
    monkeypatch.setenv("VIDEO_STUDIO_REPO", str(r))
    monkeypatch.setattr(station, "_stdin_is_tty", lambda: False)
    return r


def _script(*answers):
    seen, it = [], iter(answers)

    def ask(prompt):
        seen.append(prompt)
        return next(it)
    ask.seen = seen
    return ask


def test_the_legacy_helper_is_not_called_default(repo):
    assert hasattr(_env, "legacy_station") and not hasattr(_env, "default_station")
    assert _env.legacy_station().endswith(".video")


def test_interactive_without_variable_asks_and_takes_the_typed_path(repo, tmp_path):
    target = tmp_path / "ngoai"
    ask = _script(str(target))
    mode, path, _why = station.choose_mode(mode="separate", ask=ask)
    assert (mode, path) == ("separate", str(target))
    assert "Enter" in ask.seen[0] and "dừng" in ask.seen[0]


def test_interactive_empty_answer_without_variable_stops(repo):
    with pytest.raises(ContractError):
        station.choose_mode(mode="separate", ask=_script(""))


def test_interactive_with_variable_suggests_and_enter_accepts(repo, tmp_path, monkeypatch):
    base = tmp_path / "ws"
    monkeypatch.setenv("OPCOS_WORKSPACES", str(base))
    ask = _script("")
    mode, path, _why = station.choose_mode(mode="separate", ask=ask)
    expect = os.path.abspath(str(base / "video"))
    assert (mode, path) == ("separate", expect)
    assert expect in ask.seen[0] and "OPCOS_WORKSPACES" in ask.seen[0]


def test_interactive_with_variable_lets_the_user_change_the_path(repo, tmp_path, monkeypatch):
    monkeypatch.setenv("OPCOS_WORKSPACES", str(tmp_path / "ws"))
    other = tmp_path / "khac"
    _mode, path, _why = station.choose_mode(mode="separate", ask=_script(str(other)))
    assert path == str(other)


def test_table_choice_two_then_asks_for_the_path(repo, tmp_path):
    target = tmp_path / "ngoai"
    ask = _script("2", str(target))
    mode, path, _why = station.choose_mode(ask=ask)
    assert (mode, path) == ("separate", str(target))
    assert len(ask.seen) == 2


def test_non_interactive_with_variable_uses_the_suggestion_and_says_so(
        repo, tmp_path, monkeypatch, capsys):
    base = tmp_path / "ws"
    monkeypatch.setenv("OPCOS_WORKSPACES", str(base))
    mode, path, _why = station.choose_mode(mode="separate", non_interactive=True)
    expect = os.path.abspath(str(base / "video"))
    assert (mode, path) == ("separate", expect)
    assert expect in capsys.readouterr().err


def test_a_relative_variable_becomes_an_absolute_path(repo, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OPCOS_WORKSPACES", "rel-ws")
    _mode, path, _why = station.choose_mode(mode="separate", non_interactive=True)
    assert os.path.isabs(path) and path == os.path.abspath(os.path.join("rel-ws", "video"))


def test_non_interactive_without_variable_exits_2_asking_for_station(repo, capsys):
    assert station.init_main(["--mode", "separate", "--non-interactive"]) == 2
    err = capsys.readouterr().err
    assert "--station" in err and ".video" not in err.replace(".video-studio", "")


def test_never_falls_back_to_the_hidden_home_station(repo, tmp_path, monkeypatch):
    legacy = os.path.join(os.path.expanduser("~"), ".video")
    ask = _script("")
    with pytest.raises(ContractError):
        station.choose_mode(mode="separate", ask=ask)
    assert all(legacy not in p for p in ask.seen)
    with pytest.raises(ContractError) as e:
        station.choose_mode(mode="separate", non_interactive=True)
    assert legacy not in str(e.value)


def test_the_variable_is_read_only_from_the_real_environment(repo, tmp_path, monkeypatch):
    monkeypatch.delenv("OPCOS_WORKSPACES", raising=False)
    (repo / ".env").write_text("OPCOS_WORKSPACES=" + str(tmp_path / "ws") + "\n", encoding="utf-8")
    with pytest.raises(ContractError):
        station.choose_mode(mode="separate", non_interactive=True)


def test_station_flag_and_embedded_do_not_ask(repo, tmp_path):
    def boom(prompt):
        pytest.fail("không được hỏi")

    assert station.choose_mode(station=str(tmp_path / "s"), ask=boom)[1] == str(tmp_path / "s")
    assert station.choose_mode(mode="embedded", ask=boom)[0] == "embedded"


def test_a_recorded_separate_choice_without_path_asks_instead_of_guessing(repo):
    import json
    (repo / "studio.local.json").write_text(json.dumps({"mode": "separate"}), encoding="utf-8")
    with pytest.raises(ContractError):
        station.choose_mode(non_interactive=True)


# ── trạm cũ dưới home: không bao giờ tự nhận ──────────────────────────────────────────────

def _legacy(tmp_path, monkeypatch):
    home = tmp_path / "home"
    (home / ".video" / "projects").mkdir(parents=True)
    monkeypatch.setenv("USERPROFILE", str(home))
    monkeypatch.setenv("HOME", str(home))
    return home / ".video"


def test_mode_separate_with_a_legacy_station_and_the_variable_uses_the_variable_path(
        repo, tmp_path, monkeypatch, capsys):
    """Ca đã tái hiện: `~/.video` mang dấu + OPCOS_WORKSPACES đặt (chưa mang dấu)."""
    old = _legacy(tmp_path, monkeypatch)
    base = tmp_path / "ws"
    monkeypatch.setenv("OPCOS_WORKSPACES", str(base))
    expect = os.path.abspath(str(base / "video"))
    mode, path, _why = station.choose_mode(mode="separate", non_interactive=True)
    assert (mode, path) == ("separate", expect)
    err = capsys.readouterr().err
    assert str(old) in err and f"--station {old}" in err
    asked = _script("")
    mode, path, _why = station.choose_mode(mode="separate", ask=asked)
    assert (mode, path) == ("separate", expect) and expect in asked.seen[0]


def test_mode_separate_with_a_legacy_station_and_no_variable_never_returns_it(
        repo, tmp_path, monkeypatch):
    old = _legacy(tmp_path, monkeypatch)
    with pytest.raises(ContractError) as e:
        station.choose_mode(mode="separate", non_interactive=True)
    assert "--station" in str(e.value)
    with pytest.raises(ContractError):
        station.choose_mode(mode="separate", ask=_script(""))
    mine = tmp_path / "toi"
    assert station.choose_mode(mode="separate", ask=_script(str(mine)))[1] == str(mine)
    assert station.choose_mode(station=str(old))[1] == str(old)       # --station vẫn nhận được
    assert station.choose_mode(migrate=True)[1] == str(old)           # --migrate là ý định tường minh


def test_yes_uses_the_new_station_and_says_so_once(repo, tmp_path, monkeypatch, capsys):
    old = _legacy(tmp_path, monkeypatch)
    mode, path, _why = station.choose_mode(yes=True)
    assert (mode, path) == ("embedded", str(repo / "workspace"))
    err = capsys.readouterr().err
    lines = [ln for ln in err.splitlines() if str(old) in ln]
    assert len(lines) == 1 and f"--station {old}" in lines[0]


def test_yes_with_the_variable_and_a_legacy_station_is_still_embedded(repo, tmp_path, monkeypatch):
    _legacy(tmp_path, monkeypatch)
    monkeypatch.setenv("OPCOS_WORKSPACES", str(tmp_path / "ws"))
    mode, path, _why = station.choose_mode(yes=True)
    assert (mode, path) == ("embedded", str(repo / "workspace"))


@pytest.mark.parametrize("kwargs", [{"non_interactive": True}, {}])
def test_no_one_to_ask_and_no_yes_with_a_legacy_station_exits_2(kwargs, repo, tmp_path, monkeypatch):
    _legacy(tmp_path, monkeypatch)
    with pytest.raises(ContractError):
        station.choose_mode(**kwargs)


def test_three_way_question_labels_match_the_real_paths(repo, tmp_path, monkeypatch):
    old = _legacy(tmp_path, monkeypatch)
    ask = _script("1")
    mode, path, _why = station.choose_mode(ask=ask)
    assert (mode, path) == ("embedded", str(repo / "workspace"))
    q = ask.seen[0]
    assert str(repo / "workspace") in q and str(old) in q
    assert "[1]" in q and "[2]" in q and "[3]" in q
    assert station.choose_mode(ask=_script("2"))[:2] == ("separate", str(old))
    assert station.choose_mode(ask=_script(""))[:2] == ("embedded", str(repo / "workspace"))
    for stop in ("3", "x"):
        with pytest.raises(ContractError) as e:
            station.choose_mode(ask=_script(stop))
        assert str(old) in str(e.value)


def test_three_way_question_one_with_the_variable_is_workspaces_video(repo, tmp_path, monkeypatch):
    _legacy(tmp_path, monkeypatch)
    monkeypatch.setenv("OPCOS_WORKSPACES", str(tmp_path / "ws"))
    ask = _script("1", "")                  # [1] rồi Enter nhận <biến>/video
    mode, path, _why = station.choose_mode(ask=ask)
    expect = os.path.abspath(str(tmp_path / "ws" / "video"))
    assert (mode, path) == ("separate", expect) and expect in ask.seen[0]


def test_pasted_quotes_around_a_path_are_stripped(repo, tmp_path):
    target = tmp_path / "co dau cach"
    assert station.choose_mode(station=f'"{target}"')[1] == str(target)
    assert station.choose_mode(mode="separate", ask=_script(f'"{target}"'))[1] == str(target)
