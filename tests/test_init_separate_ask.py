"""`init --mode separate` không có đường mặc định ngầm.

Luật: chọn `separate` mà không có `--station` ⇒ có `OPCOS_WORKSPACES` thì gợi ý
`<biến>/video` (đường tuyệt đối): có người thì HỎI xác nhận/đổi, không có người thì dùng luôn
đường đó và nói ra một dòng; không có biến thì có người ⇒ HỎI đường (Enter rỗng = dừng),
không có người ⇒ mã 2 đòi `--station`. Biến chỉ đọc từ môi trường thật (một điểm đọc:
`_env.opcos_base`). Đường dán có ngoặc kép bao quanh được bóc ngoặc.
"""
import json
import os

import pytest

from video_studio import station
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
    assert "--station" in capsys.readouterr().err


def test_there_is_no_implicit_default_path_in_any_prompt_or_error(repo):
    home = os.path.expanduser("~")
    ask = _script("")
    with pytest.raises(ContractError):
        station.choose_mode(mode="separate", ask=ask)
    assert all(home not in p for p in ask.seen)
    with pytest.raises(ContractError) as e:
        station.choose_mode(mode="separate", non_interactive=True)
    assert home not in str(e.value)


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
    (repo / "studio.local.json").write_text(json.dumps({"mode": "separate"}), encoding="utf-8")
    with pytest.raises(ContractError):
        station.choose_mode(non_interactive=True)


def test_pasted_quotes_around_a_path_are_stripped(repo, tmp_path):
    target = tmp_path / "co dau cach"
    assert station.choose_mode(station=f'"{target}"')[1] == str(target)
    assert station.choose_mode(mode="separate", ask=_script(f'"{target}"'))[1] == str(target)
