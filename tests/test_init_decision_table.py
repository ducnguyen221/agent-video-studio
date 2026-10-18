"""Bảng quyết định của `init` khi chọn chỗ đặt trạm: {OPCOS_WORKSPACES đặt/không} × {tầng phân
giải trong repo: không có · chỉ `workspace` cũ · có `workspaces` · cả hai} × {câu trả lời giả ·
--yes · --non-interactive · --mode ...}.

Định nghĩa chung: `--yes` KHÔNG BAO GIỜ hỏi (kể cả có terminal) và luôn là embedded
`<repo>/workspaces`; `--non-interactive` thiếu cả `--yes` lẫn `--mode` ⇒ mã 2 (không đoán chế độ);
tương tác: bảng chọn hai đường, có `OPCOS_WORKSPACES` thì Enter = separate `<biến>/video` (rồi hỏi
xác nhận/đổi đường); `--mode separate`: có biến ⇒ `<biến>/video`, không biến ⇒ hỏi đường (không
người ⇒ mã 2). Trạm nhúng cũ `<repo>/workspace` (mang dấu trạm) chỉ được NHẬN khi `workspaces` chưa
có, kèm một dòng nhắc đổi tên; `init` mới không bao giờ tạo thư mục số ít.
"""
import json
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
    return {"repo": r, "ws": tmp_path / "ws", "typed": tmp_path / "typed"}


def _layout(world, layout):
    r = world["repo"]
    if layout in ("old", "both"):
        (r / "workspace" / "projects").mkdir(parents=True)
        (r / "workspace" / "station.json").write_text("{}", encoding="utf-8")
    if layout in ("new", "both"):
        (r / "workspaces").mkdir(parents=True)


def _run(world, monkeypatch, layout, var, answers=None, tty=False, never_ask=False, **kw):
    _layout(world, layout)
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
    elif never_ask:
        def ask(prompt):
            pytest.fail("không được hỏi: " + prompt)
    return station.choose_mode(ask=ask, **kw), seen


def _embedded(world, layout):
    sub = "workspace" if layout == "old" else "workspaces"
    return ("embedded", str(world["repo"] / sub))


def _expect(world, layout, kind):
    return {"embedded": _embedded(world, layout),
            "var": ("separate", os.path.abspath(str(world["ws"] / "video"))),
            "typed": ("separate", str(world["typed"]))}[kind]


T, F = True, False
# (biến, câu trả lời giả, tty, kwargs, kết quả: embedded | var | typed | exit2)
ROWS = [
    # ── tương tác (ask giả) ──
    (F, [""], F, {}, "embedded"),                       # Enter = [1] embedded
    (F, ["1"], F, {}, "embedded"),
    (F, ["2", "TYPED"], F, {}, "typed"),
    (F, ["2", ""], F, {}, "exit2"),                     # đường rỗng, không gợi ý
    (F, ["x"], F, {}, "exit2"),
    (T, ["", ""], F, {}, "var"),                        # có biến: Enter = separate rồi Enter nhận
    (T, ["", "TYPED"], F, {}, "typed"),                 # …đổi được đường
    (T, ["1"], F, {}, "embedded"),
    (T, ["2", ""], F, {}, "var"),
    # ── không hỏi ──
    (F, None, F, {"yes": True}, "embedded"),
    (T, None, F, {"yes": True}, "embedded"),            # --yes ra <repo>/workspaces dù có biến
    (F, None, T, {"yes": True, "never_ask": True}, "embedded"),   # có terminal vẫn không hỏi
    (T, None, T, {"yes": True, "never_ask": True}, "embedded"),
    (F, None, F, {"non_interactive": True, "yes": True}, "embedded"),
    (F, None, F, {"non_interactive": True}, "exit2"),   # không đoán chế độ
    (T, None, F, {"non_interactive": True}, "exit2"),
    (F, None, F, {}, "exit2"),                          # không terminal, không --yes
    # ── --mode ──
    (T, None, F, {"mode": "separate", "non_interactive": True}, "var"),
    (F, None, F, {"mode": "separate", "non_interactive": True}, "exit2"),
    (T, None, F, {"mode": "separate", "yes": True}, "var"),
    (T, None, T, {"mode": "separate", "yes": True, "never_ask": True}, "var"),
    (F, None, T, {"mode": "separate", "yes": True, "never_ask": True}, "exit2"),
    (T, [""], F, {"mode": "separate"}, "var"),
    (F, ["TYPED"], F, {"mode": "separate"}, "typed"),
    (F, [""], F, {"mode": "separate"}, "exit2"),
    (F, None, F, {"mode": "embedded"}, "embedded"),
    (T, None, F, {"mode": "embedded", "yes": True}, "embedded"),
]
LAYOUTS = ["none", "old", "new", "both"]


@pytest.mark.parametrize("layout", LAYOUTS)
@pytest.mark.parametrize("var,answers,tty,kw,want", ROWS)
def test_decision_table(world, monkeypatch, layout, var, answers, tty, kw, want):
    if answers is not None:
        answers = [str(world["typed"]) if a == "TYPED" else a for a in answers]
    if want == "exit2":
        with pytest.raises(ContractError):
            _run(world, monkeypatch, layout, var, answers, tty, **dict(kw))
        return
    (mode, path, _why), _seen = _run(world, monkeypatch, layout, var, answers, tty, **dict(kw))
    assert (mode, path) == _expect(world, layout, want)


@pytest.mark.parametrize("layout", LAYOUTS)
def test_the_reminder_appears_exactly_when_the_old_layout_is_around(world, monkeypatch, capsys,
                                                                    layout):
    _run(world, monkeypatch, layout, F, None, F, yes=True)
    lines = [ln for ln in capsys.readouterr().err.splitlines() if "bố cục cũ" in ln]
    assert len(lines) == (1 if layout in ("old", "both") else 0)
    if lines:
        assert "workspaces" in lines[0]


def test_the_choice_table_shows_the_real_embedded_path_and_the_enter_default(world, monkeypatch):
    (_r, seen) = _run(world, monkeypatch, "none", F, [""], F)
    assert "<repo>/workspaces/" in seen[0] and "bấm Enter" in seen[0]
    (_r, seen) = _run(world, monkeypatch, "none", T, ["", ""], F)
    expect = os.path.abspath(str(world["ws"] / "video"))
    assert "Enter = [2]" in seen[0] and expect in seen[0] and expect in seen[1]


# ── lựa chọn đã ghi trong studio.local.json ───────────────────────────────────────────────
# (đã ghi, tầng, câu trả lời, kwargs, kết quả). "rec" = đường đã ghi.
REC_ROWS = [
    ("embedded", "none", {"yes": True}, "embedded"),
    ("embedded", "none", {"non_interactive": True}, "embedded"),    # đã chọn rồi: không mã 2
    ("embedded", "none", {}, "embedded"),
    ("embedded", "old", {}, "embedded"),
    ("embedded", "both", {"mode": "embedded"}, "embedded"),
    ("separate", "none", {"non_interactive": True}, "rec"),
    ("separate", "new", {"yes": True}, "rec"),
    (None, "none", {"non_interactive": True}, "exit2"),
]


@pytest.mark.parametrize("prev,layout,kw,want", REC_ROWS)
def test_a_recorded_choice_is_kept_without_asking(world, monkeypatch, prev, layout, kw, want):
    if prev:
        cfg = {"mode": prev}
        if prev == "separate":
            cfg["station_path"] = str(world["typed"])
        (world["repo"] / "studio.local.json").write_text(json.dumps(cfg), encoding="utf-8")
    if want == "exit2":
        with pytest.raises(ContractError):
            _run(world, monkeypatch, layout, F, None, F, **dict(kw))
        return
    (mode, path, _why), _ = _run(world, monkeypatch, layout, F, None, F, never_ask=True, **dict(kw))
    exp = _embedded(world, layout) if want == "embedded" else ("separate", str(world["typed"]))
    assert (mode, path) == exp


def test_a_station_flag_and_a_chosen_variable_never_ask(world, monkeypatch):
    mode, path, _ = station.choose_mode(station=str(world["typed"]),
                                        ask=lambda p: pytest.fail("không được hỏi"))
    assert (mode, path) == ("separate", str(world["typed"]))
    monkeypatch.setenv("VIDEO_STATION", str(world["typed"]))
    mode, path, why = station.choose_mode(yes=True, ask=lambda p: pytest.fail("không được hỏi"))
    assert (mode, path) == ("separate", str(world["typed"])) and "VIDEO_STATION" in why
    with pytest.raises(ContractError):
        station.choose_mode(mode="embedded")             # hai nguồn sự thật
