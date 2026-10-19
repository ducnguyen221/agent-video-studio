"""Bảng quyết định của `init` khi chọn chỗ đặt trạm: {OPCOS_WORKSPACES vắng / đặt nhưng chưa mang
dấu trạm / đặt và đã mang dấu} × {tầng phân giải trong repo: không có · chỉ `workspace` cũ · có
`workspaces` · cả hai} × {câu trả lời giả · --yes · --non-interactive · --mode ...}.

Định nghĩa chung: `--yes` KHÔNG BAO GIỜ hỏi (kể cả có terminal) và luôn là embedded
`<repo>/workspaces`; `--non-interactive` thiếu cả `--yes` lẫn `--mode` ⇒ mã 2 (không đoán chế độ);
tương tác: bảng chọn hai đường, có `OPCOS_WORKSPACES` thì Enter = separate `<biến>/video` (rồi hỏi
xác nhận/đổi đường); `--mode separate`: có biến ⇒ `<biến>/video`, không biến ⇒ hỏi đường (không
người ⇒ mã 2). Trạm nhúng cũ `<repo>/workspace` (mang dấu trạm) chỉ được NHẬN khi `workspaces` chưa
có, kèm một dòng nhắc đổi tên; `init` mới không bao giờ tạo thư mục số ít.

Hình của bộ test (ba repo cùng một hình):
* mỗi dòng bảng là một `pytest.param` với id CỐ ĐỊNH theo tên ô (`cl<NN>-<tên>`), không sinh từ chỉ số
  hay giá trị — chèn dòng không đổi id dòng khác;
* trục biến có ba giá trị: `unset` (không có `OPCOS_WORKSPACES`) · `unmarked` (đặt, `<biến>/video`
  chưa có) · `marked` (đặt, `<biến>/video` đã có `station.json`);
* mỗi dòng khai SỐ CÂU HỎI kỳ vọng và test assert BẰNG đúng số đó (hỏi ít hơn cũng đỏ).
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


def _set_var(world, monkeypatch, var):
    """Trục biến: unset · unmarked (đặt, `<biến>/video` chưa có) · marked (đặt và đã mang dấu)."""
    if var == "unset":
        return
    monkeypatch.setenv("OPCOS_WORKSPACES", str(world["ws"]))
    if var == "marked":
        (world["ws"] / "video").mkdir(parents=True)
        (world["ws"] / "video" / "station.json").write_text("{}", encoding="utf-8")


def _run(world, monkeypatch, layout, var, answers=None, tty=False, never_ask=False, seen=None,
         **kw):
    """Gọi `choose_mode`; mọi câu hỏi được ghi vào `seen` (kể cả khi hàm ném lỗi)."""
    _layout(world, layout)
    _set_var(world, monkeypatch, var)
    monkeypatch.setattr(station, "_stdin_is_tty", lambda: tty)
    seen = [] if seen is None else seen
    ask = None
    if answers is not None:
        it = iter(answers)

        def ask(prompt):
            seen.append(prompt)
            return next(it)
    elif never_ask:
        def ask(prompt):
            seen.append(prompt)
            pytest.fail("không được hỏi: " + prompt)
    return station.choose_mode(ask=ask, **kw)


def _embedded(world, layout):
    sub = "workspace" if layout == "old" else "workspaces"
    return ("embedded", str(world["repo"] / sub))


def _expect(world, layout, kind):
    return {"embedded": _embedded(world, layout),
            "var": ("separate", os.path.abspath(str(world["ws"] / "video"))),
            "typed": ("separate", str(world["typed"]))}[kind]


def _rows(*cells):
    """(tên ô, [biến…], câu trả lời giả, tty, kwargs, kết quả, số câu hỏi) → `pytest.param` có id
    `<tên ô>-<giá trị biến>`. Biến `unset` một dòng; `unmarked`/`marked` mỗi giá trị một dòng."""
    out = []
    for name, var_values, answers, tty, kw, want, asks in cells:
        for var in var_values:
            asks_for = asks[var] if isinstance(asks, dict) else asks
            out.append(pytest.param(var, answers, tty, kw, want, asks_for, id=f"{name}-{var}"))
    return out


U = ("unset",)
V = ("unmarked", "marked")
# (ô, biến, câu trả lời giả, tty, kwargs, kết quả: embedded | var | typed | exit2, số câu hỏi)
ROWS = _rows(
    # ── tương tác (ask giả) ──
    ("cl01-enter-table", U, [""], False, {}, "embedded", 1),            # Enter = [1] embedded
    ("cl02-one-embedded", U, ["1"], False, {}, "embedded", 1),
    ("cl03-two-then-path", U, ["2", "TYPED"], False, {}, "typed", 2),
    ("cl04-two-then-empty", U, ["2", ""], False, {}, "exit2", 2),       # đường rỗng, không gợi ý
    ("cl05-bad-answer", U, ["x"], False, {}, "exit2", 1),
    ("cl27-enter-var", V, ["", ""], False, {}, "var", 2),               # Enter = separate rồi Enter nhận
    ("cl28-typed-var", V, ["", "TYPED"], False, {}, "typed", 2),        # …đổi được đường
    ("cl29-one-var", V, ["1"], False, {}, "embedded", 1),
    ("cl30-two-var", V, ["2", ""], False, {}, "var", 2),
    # ── không hỏi ──
    ("cl08-yes", U, None, False, {"yes": True}, "embedded", 0),
    ("cl22-yes-var", V, None, False, {"yes": True}, "embedded", 0),     # --yes ra <repo>/workspaces dù có biến
    ("cl08-yes-tty", U, None, True, {"yes": True, "never_ask": True}, "embedded", 0),
    ("cl22-yes-tty-var", V, None, True, {"yes": True, "never_ask": True}, "embedded", 0),
    ("cl09-ni-yes", U, None, False, {"non_interactive": True, "yes": True}, "embedded", 0),
    ("cl11-ni", U, None, False, {"non_interactive": True}, "exit2", 0),  # không đoán chế độ
    ("cl25-ni-var", V, None, False, {"non_interactive": True}, "exit2", 0),
    ("cl10-notty-noflag", U, None, False, {}, "exit2", 0),               # không terminal, không --yes
    # ── --mode ──
    ("cl37-sep-ni-var", V, None, False, {"mode": "separate", "non_interactive": True}, "var", 0),
    ("cl15-sep-ni", U, None, False, {"mode": "separate", "non_interactive": True}, "exit2", 0),
    ("cl37-sep-yes-var", V, None, False, {"mode": "separate", "yes": True}, "var", 0),
    ("cl37-sep-yes-tty-var", V, None, True,
     {"mode": "separate", "yes": True, "never_ask": True}, "var", 0),
    ("cl15-sep-yes-tty", U, None, True,
     {"mode": "separate", "yes": True, "never_ask": True}, "exit2", 0),
    ("cl36-sep-enter-var", V, [""], False, {"mode": "separate"}, "var", 1),
    ("cl13-sep-typed", U, ["TYPED"], False, {"mode": "separate"}, "typed", 1),
    ("cl14-sep-enter-novar", U, [""], False, {"mode": "separate"}, "exit2", 1),
    ("cl12-mode-embedded", U, None, False, {"mode": "embedded"}, "embedded", 0),
    ("cl38-mode-embedded-yes-var", V, None, False, {"mode": "embedded", "yes": True},
     "embedded", 0),
    # ── `--non-interactive --yes` có biến (ô thiếu của bảng cũ) ──
    ("cl23-ni-yes-var", V, None, False, {"non_interactive": True, "yes": True}, "embedded", 0),
)
LAYOUTS = ["none", "old", "new", "both"]


@pytest.mark.parametrize("layout", LAYOUTS)
@pytest.mark.parametrize("var,answers,tty,kw,want,asks", ROWS)
def test_decision_table(world, monkeypatch, layout, var, answers, tty, kw, want, asks):
    if answers is not None:
        answers = [str(world["typed"]) if a == "TYPED" else a for a in answers]
    seen = []
    if want == "exit2":
        with pytest.raises(ContractError):
            _run(world, monkeypatch, layout, var, answers, tty, seen=seen, **dict(kw))
        assert len(seen) == asks
        return
    mode, path, _why = _run(world, monkeypatch, layout, var, answers, tty, seen=seen, **dict(kw))
    assert (mode, path) == _expect(world, layout, want)
    assert len(seen) == asks


@pytest.mark.parametrize("layout", LAYOUTS)
def test_the_reminder_appears_exactly_when_the_old_layout_is_around(world, monkeypatch, capsys,
                                                                    layout):
    _run(world, monkeypatch, layout, "unset", None, False, yes=True)
    lines = [ln for ln in capsys.readouterr().err.splitlines() if "bố cục cũ" in ln]
    assert len(lines) == (1 if layout in ("old", "both") else 0)
    if lines:
        assert "workspaces" in lines[0]


def test_the_choice_table_shows_the_real_embedded_path_and_the_enter_default(world, monkeypatch):
    seen = []
    _run(world, monkeypatch, "none", "unset", [""], False, seen=seen)
    assert "<repo>/workspaces/" in seen[0] and "bấm Enter" in seen[0]
    seen = []
    _run(world, monkeypatch, "none", "unmarked", ["", ""], False, seen=seen)
    expect = os.path.abspath(str(world["ws"] / "video"))
    assert "Enter = [2]" in seen[0] and expect in seen[0] and expect in seen[1]


# ── lựa chọn đã ghi trong studio.local.json ───────────────────────────────────────────────
# (đã ghi, tầng, biến, kwargs, kết quả). "rec" = đường đã ghi.
REC_ROWS = [
    pytest.param("embedded", "none", "unset", {"yes": True}, "embedded", id="cl20-rec-embedded-yes"),
    pytest.param("embedded", "none", "unset", {"non_interactive": True}, "embedded",
                 id="cl20-rec-embedded-ni"),                          # đã chọn rồi: không mã 2
    pytest.param("embedded", "none", "unset", {}, "embedded", id="cl20-rec-embedded-ask"),
    pytest.param("embedded", "old", "unset", {}, "embedded", id="cl20-rec-embedded-old"),
    pytest.param("embedded", "both", "unset", {"mode": "embedded"}, "embedded",
                 id="cl20-rec-embedded-mode"),
    pytest.param("separate", "none", "unset", {"non_interactive": True}, "rec",
                 id="cl21-rec-separate-ni"),
    pytest.param("separate", "new", "unset", {"yes": True}, "rec", id="cl21-rec-separate-yes-new"),
    pytest.param(None, "none", "unset", {"non_interactive": True}, "exit2", id="cl11-rec-none-ni"),
    # ── biến đặt: lựa chọn đã ghi thắng biến (ASSUMPTION của SPEC) ──
    pytest.param("embedded", "none", "unmarked", {"yes": True}, "embedded",
                 id="cl39-rec-embedded-yes-unmarked"),
    pytest.param("embedded", "none", "marked", {"yes": True}, "embedded",
                 id="cl39-rec-embedded-yes-marked"),
    pytest.param("embedded", "none", "unmarked", {"non_interactive": True, "yes": True},
                 "embedded", id="cl39-rec-embedded-ni-yes-unmarked"),
    pytest.param("embedded", "none", "marked", {}, "embedded", id="cl39-rec-embedded-ask-marked"),
    pytest.param("separate", "none", "unmarked", {"yes": True}, "rec",
                 id="cl40-rec-separate-yes-unmarked"),
    pytest.param("separate", "none", "marked", {"non_interactive": True}, "rec",
                 id="cl40-rec-separate-ni-marked"),
]


@pytest.mark.parametrize("prev,layout,var,kw,want", REC_ROWS)
def test_a_recorded_choice_is_kept_without_asking(world, monkeypatch, prev, layout, var, kw, want):
    if prev:
        cfg = {"mode": prev}
        if prev == "separate":
            cfg["station_path"] = str(world["typed"])
        (world["repo"] / "studio.local.json").write_text(json.dumps(cfg), encoding="utf-8")
    seen = []
    if want == "exit2":
        with pytest.raises(ContractError):
            _run(world, monkeypatch, layout, var, None, False, seen=seen, **dict(kw))
        assert seen == []
        return
    mode, path, _why = _run(world, monkeypatch, layout, var, None, False, never_ask=True,
                            seen=seen, **dict(kw))
    exp = _embedded(world, layout) if want == "embedded" else ("separate", str(world["typed"]))
    assert (mode, path) == exp
    assert seen == []


def test_a_station_flag_and_a_chosen_variable_never_ask(world, monkeypatch):
    mode, path, _ = station.choose_mode(station=str(world["typed"]),
                                        ask=lambda p: pytest.fail("không được hỏi"))
    assert (mode, path) == ("separate", str(world["typed"]))
    monkeypatch.setenv("VIDEO_STATION", str(world["typed"]))
    mode, path, why = station.choose_mode(yes=True, ask=lambda p: pytest.fail("không được hỏi"))
    assert (mode, path) == ("separate", str(world["typed"])) and "VIDEO_STATION" in why
    with pytest.raises(ContractError):
        station.choose_mode(mode="embedded")             # hai nguồn sự thật
