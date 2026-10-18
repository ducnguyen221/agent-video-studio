"""Bảng quyết định của `init` khi chọn chỗ đặt trạm: {trạm cũ dưới home có/không} × {OPCOS_WORKSPACES
đặt/không} × {câu trả lời giả · --yes · --non-interactive · --mode ...}.

Định nghĩa chung: `--yes` KHÔNG BAO GIỜ hỏi (kể cả có terminal) và dùng trạm mới = embedded
`<repo>/workspace`; `--non-interactive` thiếu cả `--yes` lẫn `--mode` ⇒ mã 2 (không đoán chế độ);
tương tác: Enter ở câu hỏi ba đường = [1] trạm mới (nhãn in đường thật: `<biến>/video` nếu biến
đặt, không thì `<repo>/workspace`); `--mode separate`: có biến ⇒ `<biến>/video`, không biến ⇒ hỏi
đường (không người ⇒ mã 2); `--mode embedded` khi có trạm cũ bị từ chối. Trạm cũ chỉ được nhận qua
`--station`, `--migrate` hoặc câu trả lời [2].
"""
import os

import pytest

from video_studio import station
from video_studio.contract import ContractError


@pytest.fixture
def world(tmp_path, monkeypatch):
    r = tmp_path / "repo"
    (r / "video_studio").mkdir(parents=True)
    (r / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
    (r / ".env.example").write_text("# khuon\n", encoding="utf-8")
    monkeypatch.setenv("VIDEO_STUDIO_REPO", str(r))
    home = tmp_path / "home"
    home.mkdir(exist_ok=True)
    monkeypatch.setenv("USERPROFILE", str(home))
    monkeypatch.setenv("HOME", str(home))
    return {"repo": r, "home": home, "ws": tmp_path / "ws", "typed": tmp_path / "typed"}


def _run(world, monkeypatch, legacy, var, answers=None, tty=False, **kw):
    if legacy:
        (world["home"] / ".video" / "projects").mkdir(parents=True)
    if var:
        monkeypatch.setenv("OPCOS_WORKSPACES", str(world["ws"]))
    monkeypatch.setattr(station, "_stdin_is_tty", lambda: tty)
    seen = []
    ask = None
    if answers is not None:
        it = iter(answers)

        def ask(prompt):
            seen.append(prompt)
            return next(it)
    else:
        def ask_never(prompt):
            pytest.fail("không được hỏi: " + prompt)
        ask = None if not kw.pop("never_ask", False) else ask_never
    res = station.choose_mode(ask=ask, **kw)
    return res, seen


def _expect(world, kind):
    return {"embedded": ("embedded", str(world["repo"] / "workspace")),
            "var": ("separate", os.path.abspath(str(world["ws"] / "video"))),
            "old": ("separate", str(world["home"] / ".video")),
            "typed": ("separate", str(world["typed"]))}[kind]


# (trạm cũ, biến, câu trả lời giả, tty, kwargs, kết quả: loại đường | "exit2")
T, F = True, False
ROWS = [
    # ── có trạm cũ, tương tác (ask giả) ──
    (T, F, [""], F, {}, "embedded"),                      # Enter = [1]
    (T, T, ["", ""], F, {}, "var"),                       # Enter = [1] rồi Enter nhận <biến>/video
    (T, F, ["1"], F, {}, "embedded"),
    (T, T, ["1", ""], F, {}, "var"),
    (T, T, ["1", "TYPED"], F, {}, "typed"),               # [1] có biến: đổi được đường
    (T, F, ["2"], F, {}, "old"),
    (T, T, ["2"], F, {}, "old"),
    (T, F, ["3"], F, {}, "exit2"),
    (T, T, ["3"], F, {}, "exit2"),
    (T, F, ["x"], F, {}, "exit2"),
    # ── có trạm cũ, không hỏi ──
    (T, F, None, F, {"yes": True}, "embedded"),
    (T, T, None, F, {"yes": True}, "embedded"),
    (T, F, None, T, {"yes": True, "never_ask": True}, "embedded"),   # có terminal vẫn không hỏi
    (T, T, None, T, {"yes": True, "never_ask": True}, "embedded"),
    (T, F, None, F, {"non_interactive": True, "yes": True}, "embedded"),
    (T, F, None, F, {"non_interactive": True}, "exit2"),  # không đoán chế độ
    (T, T, None, F, {"non_interactive": True}, "exit2"),
    (T, F, None, F, {}, "exit2"),                         # không terminal, không --yes
    # ── có trạm cũ, --mode ──
    (T, T, None, F, {"mode": "separate", "non_interactive": True}, "var"),
    (T, F, None, F, {"mode": "separate", "non_interactive": True}, "exit2"),
    (T, T, None, F, {"mode": "separate", "yes": True}, "var"),
    (T, F, None, F, {"mode": "separate", "yes": True}, "exit2"),
    (T, T, None, T, {"mode": "separate", "yes": True, "never_ask": True}, "var"),
    (T, F, None, T, {"mode": "separate", "yes": True, "never_ask": True}, "exit2"),
    (T, T, [""], F, {"mode": "separate"}, "var"),
    (T, F, ["TYPED"], F, {"mode": "separate"}, "typed"),
    (T, F, [""], F, {"mode": "separate"}, "exit2"),
    (T, F, None, F, {"mode": "embedded"}, "exit2"),       # hai nguồn sự thật
    (T, T, None, F, {"mode": "embedded", "yes": True}, "exit2"),
    # ── không có trạm cũ ──
    (F, F, None, F, {"yes": True}, "embedded"),
    (F, T, None, F, {"yes": True}, "embedded"),
    (F, F, None, T, {"yes": True, "never_ask": True}, "embedded"),
    (F, F, None, F, {"non_interactive": True}, "exit2"),
    (F, T, None, F, {"non_interactive": True}, "exit2"),
    (F, F, None, F, {"non_interactive": True, "yes": True}, "embedded"),
    (F, F, [""], F, {}, "embedded"),
    (F, F, ["1"], F, {}, "embedded"),
    (F, T, ["2", ""], F, {}, "var"),
    (F, F, ["2", "TYPED"], F, {}, "typed"),
    (F, T, None, F, {"mode": "separate", "non_interactive": True}, "var"),
    (F, F, None, F, {"mode": "separate", "non_interactive": True}, "exit2"),
    (F, T, None, F, {"mode": "separate", "yes": True}, "var"),
    (F, F, None, T, {"mode": "separate", "yes": True, "never_ask": True}, "exit2"),
    (F, F, None, F, {"mode": "embedded"}, "embedded"),
]


@pytest.mark.parametrize("legacy,var,answers,tty,kw,want", ROWS)
def test_decision_table(world, monkeypatch, legacy, var, answers, tty, kw, want):
    if answers is not None:
        answers = [str(world["typed"]) if a == "TYPED" else a for a in answers]
    if want == "exit2":
        with pytest.raises(ContractError):
            _run(world, monkeypatch, legacy, var, answers, tty, **dict(kw))
        return
    (mode, path, _why), _seen = _run(world, monkeypatch, legacy, var, answers, tty, **dict(kw))
    assert (mode, path) == _expect(world, want)


def test_the_first_label_is_the_real_path_and_enter_means_the_new_station(world, monkeypatch):
    (mode, path, _why), seen = _run(world, monkeypatch, True, True, ["", ""])
    expect = os.path.abspath(str(world["ws"] / "video"))
    assert path == expect and expect in seen[0] and str(world["home"] / ".video") in seen[0]
    assert "Không trả lời gì = [1]" in seen[0]


def test_the_first_label_without_the_variable_is_the_repo_workspace(world, monkeypatch):
    (_mode, path, _why), seen = _run(world, monkeypatch, True, False, [""])
    assert path == str(world["repo"] / "workspace") and path in seen[0]


def test_yes_says_one_line_about_the_old_station_and_leaves_it_alone(world, monkeypatch, capsys):
    (_mode, _path, _why), _ = _run(world, monkeypatch, True, False, None, yes=True)
    old = world["home"] / ".video"
    lines = [ln for ln in capsys.readouterr().err.splitlines() if str(old) in ln]
    assert len(lines) == 1 and f"--station {old}" in lines[0]
    assert [p.name for p in old.iterdir()] == ["projects"]


def test_refusing_embedded_lists_the_neutral_options(world, monkeypatch):
    with pytest.raises(ContractError) as e:
        _run(world, monkeypatch, True, False, None, mode="embedded")
    msg = str(e.value)
    assert "hai nguồn sự thật" in msg and "--station" in msg and "--mode separate" in msg
