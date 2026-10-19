"""Bảng quyết định của `init` khi chọn chỗ đặt trạm: {OPCOS_WORKSPACES vắng / đặt nhưng chưa mang
dấu trạm / đặt và đã mang dấu} × {tầng phân giải trong repo: không có · chỉ `workspace` cũ · có
`workspaces` · cả hai} × {câu trả lời giả · --yes · --non-interactive · --mode ...}.

Định nghĩa chung (ưu tiên: `--station` → biến trạm riêng → lựa chọn đã ghi → `--mode` → trạm nhúng
cũ có dữ liệu → `--yes`/không người → có người):
* KHÔNG có `OPCOS_WORKSPACES`: `--yes` ⇒ embedded `<repo>/workspaces`, không hỏi; không người mà
  thiếu cờ ⇒ mã 2 (không đoán chế độ); có người ⇒ bảng chọn [1]/[2].
* CÓ `OPCOS_WORKSPACES`: `--yes` và không người (pipe, `--non-interactive`) ⇒ trạm OpcOS
  `<biến>/video`, không hỏi (đã mang dấu: dùng thẳng; chưa: dựng + một dòng); có người ⇒ ĐÚNG MỘT
  câu nhận đường (Enter = `<biến>/video`; gõ `1`/`2`/`embedded`/`separate` ⇒ mã 2); hết dữ liệu
  (EOF) ở câu đó ⇒ coi như không có người. `--mode separate`: `<biến>/video` đã mang dấu ⇒ dùng thẳng
  0 câu; chưa ⇒ có người hỏi một câu, không người dùng luôn + một dòng.
* Trạm nhúng (`workspaces` hoặc `workspace` cũ) ĐÃ MANG DẤU, chưa ghi lựa chọn, có biến: dữ liệu có
  sẵn thắng biến — `--yes`/không người/EOF/Enter ⇒ GIỮ trạm nhúng (không dời hộ); chỉ khi người
  dùng gõ `chuyen` thì dời vào `<biến>/video` (qua `migrate`, có `y/N`).
* Trạm nhúng cũ `<repo>/workspace` (mang dấu trạm) chỉ được NHẬN khi `workspaces` chưa có, kèm một
  dòng nhắc đổi tên; `init` mới không bao giờ tạo thư mục số ít.

Hình của bộ test (ba repo cùng một hình):
* mỗi dòng bảng là một `pytest.param` với id CỐ ĐỊNH theo tên ô (`cl<NN>-<tên>`), không sinh từ chỉ số
  hay giá trị — chèn dòng không đổi id dòng khác;
* trục biến có ba giá trị: `unset` (không có `OPCOS_WORKSPACES`) · `unmarked` (đặt, `<biến>/video`
  chưa có) · `marked` (đặt, `<biến>/video` đã có `station.json`);
* mỗi dòng khai SỐ CÂU HỎI kỳ vọng và test assert BẰNG đúng số đó (hỏi ít hơn cũng đỏ).
"""
import hashlib
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


EOF = object()        # câu trả lời giả: stdin hết dữ liệu (Windows `< NUL`; pipe cạn)
CTRL_C = object()     # câu trả lời giả: người dùng bấm Ctrl+C


def _layout(world, layout):
    """none · old (chỉ `workspace` cũ mang dấu) · new (`workspaces` rỗng, chưa dấu) · both (cũ mang dấu
    + `workspaces` rỗng) · newm (`workspaces` mang dấu)."""
    r = world["repo"]
    if layout == "newm":
        (r / "workspaces" / "projects").mkdir(parents=True)
        (r / "workspaces" / "station.json").write_text("{}", encoding="utf-8")
        (r / "workspaces" / "projects" / "x.txt").write_text("du lieu cua toi", encoding="utf-8")
    if layout in ("old", "both"):
        (r / "workspace" / "projects").mkdir(parents=True)
        (r / "workspace" / "station.json").write_text("{}", encoding="utf-8")
        (r / "workspace" / "projects" / "x.txt").write_text("du lieu cua toi", encoding="utf-8")
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
            a = next(it)
            if a is EOF:
                raise EOFError
            if a is CTRL_C:
                raise KeyboardInterrupt
            return a
    elif never_ask:
        def ask(prompt):
            seen.append(prompt)
            pytest.fail("không được hỏi: " + prompt)
    return station.choose_mode(ask=ask, **kw)


def _embedded(world, layout):
    sub = "workspace" if layout == "old" else "workspaces"
    return ("embedded", str(world["repo"] / sub))


def _oc(world):
    return os.path.abspath(str(world["ws"] / "video"))


def _expect(world, layout, kind):
    return {"embedded": _embedded(world, layout),
            "var": ("separate", _oc(world)),
            "typed": ("separate", str(world["typed"]))}[kind]


def _rows(*cells):
    """(tên ô, [biến…], câu trả lời giả, tty, kwargs, kết quả, số câu hỏi[, fr16]) → `pytest.param` có
    id `<tên ô>-<giá trị biến>`. Biến `unset` một dòng; `unmarked`/`marked` mỗi giá trị một dòng.
    `fr16` = dòng này đi qua nhánh "trạm nhúng mang dấu, chưa ghi lựa chọn, có biến" khi tầng là
    `old`/`both` (xem `test_decision_table`)."""
    out = []
    for name, var_values, answers, tty, kw, want, asks, *rest in cells:
        fr16 = bool(rest and rest[0])
        for var in var_values:
            asks_for = asks[var] if isinstance(asks, dict) else asks
            out.append(pytest.param(var, answers, tty, kw, want, asks_for, fr16,
                                    id=f"{name}-{var}"))
    return out


U = ("unset",)
V = ("unmarked", "marked")
# (ô, biến, câu trả lời giả, tty, kwargs, kết quả: embedded | var | typed | exit2, số câu hỏi, fr16)
ROWS = _rows(
    # ── tương tác (ask giả) ──
    ("cl01-enter-table", U, [""], False, {}, "embedded", 1),            # Enter = [1] embedded
    ("cl02-one-embedded", U, ["1"], False, {}, "embedded", 1),
    ("cl03-two-then-path", U, ["2", "TYPED"], False, {}, "typed", 2),
    ("cl04-two-then-empty", U, ["2", ""], False, {}, "exit2", 2),       # đường rỗng, không gợi ý
    ("cl05-bad-answer", U, ["x"], False, {}, "exit2", 1),
    ("cl06-eof-novar", U, [EOF], False, {}, "exit2", 1),                # Windows `< NUL`: không biến ⇒ mã 2
    # có biến, có người: ĐÚNG MỘT câu nhận đường (Enter = <biến>/video)
    ("cl27-enter-var", V, [""], False, {}, "var", 1, True),
    ("cl28-typed-var", V, ["TYPED"], False, {}, "typed", 1, True),
    ("cl29-one-var", V, ["1"], False, {}, "exit2", 1, True),            # CQ1: câu này nhận ĐƯỜNG
    ("cl30-two-var", V, ["2"], False, {}, "exit2", 1, True),
    ("cl31-embedded-word-var", V, ["embedded"], False, {}, "exit2", 1, True),
    ("cl32-separate-word-var", V, ["separate"], False, {}, "exit2", 1, True),
    ("cl26-eof-var", V, [EOF], False, {}, "var", 1, True),              # hết dữ liệu = không người
    # ── không hỏi ──
    ("cl08-yes", U, None, False, {"yes": True}, "embedded", 0),
    ("cl22-yes-var", V, None, False, {"yes": True}, "var", 0, True),
    ("cl08-yes-tty", U, None, True, {"yes": True, "never_ask": True}, "embedded", 0),
    ("cl22-yes-tty-var", V, None, True, {"yes": True, "never_ask": True}, "var", 0, True),
    ("cl09-ni-yes", U, None, False, {"non_interactive": True, "yes": True}, "embedded", 0),
    ("cl23-ni-yes-var", V, None, False, {"non_interactive": True, "yes": True}, "var", 0, True),
    ("cl11-ni", U, None, False, {"non_interactive": True}, "exit2", 0),  # không đoán chế độ
    ("cl25-ni-var", V, None, False, {"non_interactive": True}, "var", 0, True),
    ("cl25-ni-tty-var", V, None, True, {"non_interactive": True, "never_ask": True}, "var", 0,
     True),
    ("cl10-notty-noflag", U, None, False, {}, "exit2", 0),               # không terminal, không --yes
    ("cl24-notty-noflag-var", V, None, False, {}, "var", 0, True),
    # ── --mode (lựa chọn tường minh đi trước nhánh trạm nhúng cũ) ──
    ("cl37-sep-ni-var", V, None, False, {"mode": "separate", "non_interactive": True}, "var", 0),
    ("cl15-sep-ni", U, None, False, {"mode": "separate", "non_interactive": True}, "exit2", 0),
    ("cl37-sep-yes-var", V, None, False, {"mode": "separate", "yes": True}, "var", 0),
    ("cl37-sep-yes-tty-var", V, None, True,
     {"mode": "separate", "yes": True, "never_ask": True}, "var", 0),
    ("cl15-sep-yes-tty", U, None, True,
     {"mode": "separate", "yes": True, "never_ask": True}, "exit2", 0),
    # `--mode separate` có người: đã mang dấu ⇒ dùng thẳng, 0 câu; chưa ⇒ 1 câu
    ("cl36-sep-enter-var", V, [""], False, {"mode": "separate"}, "var",
     {"unmarked": 1, "marked": 0}),
    ("cl13-sep-typed", U, ["TYPED"], False, {"mode": "separate"}, "typed", 1),
    ("cl14-sep-enter-novar", U, [""], False, {"mode": "separate"}, "exit2", 1),
    ("cl12-mode-embedded", U, None, False, {"mode": "embedded"}, "embedded", 0),
    ("cl38-mode-embedded-yes-var", V, None, False, {"mode": "embedded", "yes": True},
     "embedded", 0),
)
LAYOUTS = ["none", "old", "new", "both"]


@pytest.mark.parametrize("layout", LAYOUTS)
@pytest.mark.parametrize("var,answers,tty,kw,want,asks,fr16", ROWS)
def test_decision_table(world, monkeypatch, layout, var, answers, tty, kw, want, asks, fr16):
    if answers is not None:
        answers = [str(world["typed"]) if a == "TYPED" else a for a in answers]
    if fr16 and layout in ("old", "both"):
        # trạm nhúng cũ mang dấu thắng biến: giữ, không bao giờ dựng trạm OpcOS rỗng cạnh dữ liệu cũ.
        # `old`: có người thì có ĐÚNG MỘT câu giữ/chuyển (mọi câu trả lời khác `chuyen` = giữ);
        # `both` (mới chưa dấu): không câu nào.
        want = "embedded"
        asks = 1 if (layout == "old" and answers is not None) else 0
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


def test_the_choice_table_without_a_variable_shows_the_real_embedded_path(world, monkeypatch):
    seen = []
    _run(world, monkeypatch, "none", "unset", [""], False, seen=seen)
    assert "<repo>/workspaces/" in seen[0] and "bấm Enter" in seen[0]
    assert "OPCOS_WORKSPACES đã đặt" not in seen[0]       # bảng [1]/[2] không còn lời gợi ý của biến


def test_with_a_variable_the_only_question_names_the_path_and_has_no_table(world, monkeypatch):
    seen = []
    _run(world, monkeypatch, "none", "unmarked", [""], False, seen=seen)
    assert len(seen) == 1 and _oc(world) in seen[0] and "OPCOS_WORKSPACES" in seen[0]
    assert "[1]" not in seen[0] and "[2]" not in seen[0] and "KHUYẾN NGHỊ" not in seen[0]


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
    pytest.param("embedded", "old", "unmarked", {"yes": True}, "embedded",
                 id="cl39-rec-embedded-yes-old-unmarked"),   # đã ghi embedded thắng cả nhánh "giữ"
    pytest.param("embedded", "old", "marked", {}, "embedded", id="cl39-rec-embedded-ask-old-marked"),
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


# Bản ghi `separate` mà thiếu `station_path` là bản ghi hỏng: mã 2, 0 câu, nêu `--station` — với MỌI
# cách gọi, có hay không có biến (không đoán trạm OpcOS, không hỏi đường).
@pytest.mark.parametrize("var", ["unset", "unmarked", "marked"])
@pytest.mark.parametrize("kw,answers", [
    pytest.param({"yes": True}, None, id="cl41-yes"),
    pytest.param({}, [""], id="cl41-person"),
    pytest.param({"non_interactive": True}, None, id="cl41-ni"),
    pytest.param({}, None, id="cl41-notty"),
])
def test_a_recorded_separate_choice_without_a_path_is_code_2_and_asks_nothing(
        world, monkeypatch, var, kw, answers):
    (world["repo"] / "studio.local.json").write_text(json.dumps({"mode": "separate"}),
                                                     encoding="utf-8")
    seen = []
    with pytest.raises(ContractError) as e:
        _run(world, monkeypatch, "none", var, answers, False, seen=seen, **dict(kw))
    assert "--station" in str(e.value)
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


# ── trạm nhúng đã mang dấu, chưa ghi lựa chọn, máy có OPCOS_WORKSPACES: dữ liệu có sẵn thắng biến ──
KEEP_LAYOUTS = ["newm", "old"]        # `workspaces` mang dấu · chỉ `workspace` cũ mang dấu
MIGRATE_HINT = "migrate --to separate"


def _hash_tree(root):
    out = {}
    for dp, _dn, fn in os.walk(root):
        for n in fn:
            p = os.path.join(dp, n)
            with open(p, "rb") as f:
                out[os.path.relpath(p, root)] = hashlib.sha256(f.read()).hexdigest()
    return out


def _keep_lines(err):
    return [ln for ln in err.splitlines() if "giữ trạm trong repo" in ln]


def _assert_kept(world, layout, var, choice, err):
    """Đã GIỮ trạm nhúng: đúng đường, không cờ dời, ĐÚNG MỘT dòng nêu cách dời sau (hoặc, khi
    `<biến>/video` cũng đã là trạm, dòng "hai trạm" không gợi ý `migrate`)."""
    assert (choice.mode, choice.path) == _embedded(world, layout)
    assert choice.then_migrate is None
    lines = _keep_lines(err)
    assert len(lines) == 1 and choice.path in lines[0]
    if var == "marked":
        assert "hai trạm" in lines[0] and MIGRATE_HINT not in lines[0]
        assert f"--station {_oc(world)}" in lines[0]
    else:
        assert f"{MIGRATE_HINT} --station {_oc(world)}" in lines[0] and "hai trạm" not in lines[0]


@pytest.mark.parametrize("var", V)
@pytest.mark.parametrize("layout", KEEP_LAYOUTS)
@pytest.mark.parametrize("kw,tty", [
    pytest.param({"yes": True, "never_ask": True}, False, id="cl51-keep-yes"),
    pytest.param({}, False, id="cl52-keep-notty"),                     # không có ask nào để gọi
    pytest.param({"non_interactive": True, "never_ask": True}, True, id="cl53-keep-ni"),
])
def test_old_station_with_data_is_kept_without_asking(world, monkeypatch, capsys, kw, tty, layout,
                                                      var):
    seen = []
    choice = _run(world, monkeypatch, layout, var, None, tty, seen=seen, **dict(kw))
    assert seen == []
    _assert_kept(world, layout, var, choice, capsys.readouterr().err)


@pytest.mark.parametrize("var", V)
@pytest.mark.parametrize("layout", KEEP_LAYOUTS)
@pytest.mark.parametrize("answer", [
    pytest.param("", id="cl54-keep-enter"),
    pytest.param("khong", id="cl54-keep-other-word"),
    pytest.param("2", id="cl54-keep-digit"),
    pytest.param("xin chuyen", id="cl54-keep-sentence"),
])
def test_a_person_who_says_nothing_special_keeps_the_old_station(world, monkeypatch, capsys,
                                                                 answer, layout, var):
    seen = []
    choice = _run(world, monkeypatch, layout, var, [answer], False, seen=seen)
    assert len(seen) == 1 and "chuyen" in seen[0] and choice.path in seen[0]
    _assert_kept(world, layout, var, choice, capsys.readouterr().err)


@pytest.mark.parametrize("var", V)
@pytest.mark.parametrize("layout", KEEP_LAYOUTS)
@pytest.mark.parametrize("answer", [
    pytest.param("chuyen", id="cl55-move-chuyen"),
    pytest.param("chuyển", id="cl55-move-accented"),
    pytest.param("c", id="cl55-move-c"),
    pytest.param("  CHUYEN ", id="cl55-move-upper-padded"),
])
def test_typing_the_move_word_only_sets_the_flag_and_moves_nothing(world, monkeypatch, answer,
                                                                   layout, var):
    """Hàm chọn chế độ KHÔNG dời gì: nó trả `embedded` kèm cờ `then_migrate`; `do_init` mới làm tiếp."""
    _layout(world, layout)
    _set_var(world, monkeypatch, var)
    before = _hash_tree(str(world["repo"]))
    before_ws = _hash_tree(str(world["ws"])) if world["ws"].exists() else {}
    monkeypatch.setattr(station, "_stdin_is_tty", lambda: False)
    seen = []
    choice = station.choose_mode(ask=lambda p: seen.append(p) or answer)
    assert len(seen) == 1
    assert (choice.mode, choice.path) == _embedded(world, layout)
    assert choice.then_migrate == _oc(world)
    assert _hash_tree(str(world["repo"])) == before and not (world["repo"] / "studio.local.json").exists()
    assert (_hash_tree(str(world["ws"])) if world["ws"].exists() else {}) == before_ws
    assert not (world["ws"] / "video" / "projects" / "x.txt").exists()


@pytest.mark.parametrize("var", V)
@pytest.mark.parametrize("layout", KEEP_LAYOUTS)
def test_eof_at_the_keep_or_move_question_keeps(world, monkeypatch, capsys, layout, var):
    """Khác câu đường (EOF ⇒ trạm OpcOS): ở đây "không nói gì" = giữ."""
    seen = []
    choice = _run(world, monkeypatch, layout, var, [EOF], False, seen=seen)
    assert len(seen) == 1
    _assert_kept(world, layout, var, choice, capsys.readouterr().err)


@pytest.mark.parametrize("layout", KEEP_LAYOUTS)
def test_ctrl_c_at_the_keep_or_move_question_propagates(world, monkeypatch, layout):
    with pytest.raises(KeyboardInterrupt):
        _run(world, monkeypatch, layout, "unmarked", [CTRL_C], False)
    assert not (world["repo"] / "studio.local.json").exists()


@pytest.mark.parametrize("var", V)
@pytest.mark.parametrize("kw,answers", [
    pytest.param({"yes": True}, None, id="cl62-both-yes"),
    pytest.param({}, None, id="cl62-both-notty"),
    pytest.param({}, ["chuyen"], id="cl62-both-person"),
])
def test_both_layouts_keep_quietly_and_never_ask_to_move(world, monkeypatch, capsys, kw, answers,
                                                         var):
    """`workspace` cũ mang dấu + `workspaces` mới còn rỗng: dời thư mục rỗng là vô nghĩa. Giữ (trên
    `workspaces`), nhắc gộp, 0 câu — kể cả khi có người — và KHÔNG in dòng `migrate`."""
    seen = []
    choice = _run(world, monkeypatch, "both", var, answers, False, seen=seen, **dict(kw))
    assert seen == []
    assert (choice.mode, choice.path) == _embedded(world, "both") and choice.then_migrate is None
    err = capsys.readouterr().err
    assert "bố cục cũ" in err and MIGRATE_HINT not in err


@pytest.mark.parametrize("layout", KEEP_LAYOUTS)
@pytest.mark.parametrize("kw,answers,asks", [
    pytest.param({"mode": "separate", "yes": True}, None, 0, id="cl64-sep-yes"),
    pytest.param({"mode": "separate"}, [""], 1, id="cl64-sep-person"),
])
def test_an_explicit_mode_separate_still_builds_the_opcos_station(world, monkeypatch, kw, answers,
                                                                  asks, layout):
    """Lựa chọn tường minh đi TRƯỚC nhánh "giữ trạm cũ" — khoá để không ai "sửa" nó."""
    seen = []
    choice = _run(world, monkeypatch, layout, "unmarked", answers, False, seen=seen, **dict(kw))
    assert (choice.mode, choice.path) == ("separate", _oc(world))
    assert len(seen) == asks


@pytest.mark.parametrize("layout", KEEP_LAYOUTS)
def test_a_chosen_outside_station_beats_the_old_station(world, monkeypatch, layout):
    monkeypatch.setenv("VIDEO_STATION", str(world["typed"]))
    choice = _run(world, monkeypatch, layout, "unmarked", None, False, never_ask=True, yes=True)
    assert (choice.mode, choice.path) == ("separate", str(world["typed"]))


# ── giá trị lạ của OPCOS_WORKSPACES (nhóm C của bảng) ─────────────────────────────────────

def _init(monkeypatch, capsys, *argv, tty=False):
    monkeypatch.setattr(station, "_stdin_is_tty", lambda: tty)
    rc = station.init_main([*argv, "--json"])
    cap = capsys.readouterr()
    return rc, cap.out, cap.err


def _json_of(out):
    return json.loads([ln for ln in out.splitlines() if ln.strip()][-1])


def test_cl45_a_blank_variable_counts_as_absent(world, monkeypatch, capsys):
    monkeypatch.setenv("OPCOS_WORKSPACES", "   ")
    rc, out, _err = _init(monkeypatch, capsys, "--yes")
    assert rc == 0 and _json_of(out)["station"] == str(world["repo"] / "workspaces")


def test_cl46_a_relative_variable_gives_an_absolute_station(world, monkeypatch, capsys, tmp_path):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OPCOS_WORKSPACES", "relws")
    want = os.path.abspath(os.path.join("relws", "video"))
    rc, out, _err = _init(monkeypatch, capsys, "--yes")
    assert rc == 0 and _json_of(out)["station"] == want and os.path.isabs(want)
    local = json.loads((world["repo"] / "studio.local.json").read_text(encoding="utf-8"))
    assert local["mode"] == "separate" and local["station_path"] == want


@pytest.mark.parametrize("argv", [
    pytest.param(["--yes"], id="cl47-yes"),
    pytest.param(["--non-interactive"], id="cl47-ni"),
    pytest.param(["--mode", "separate", "--yes"], id="cl47-mode-separate-yes"),
])
def test_cl47_a_variable_that_is_a_file_is_code_2_and_names_the_variable(
        world, monkeypatch, capsys, tmp_path, argv):
    f = tmp_path / "la-mot-file"
    f.write_text("khong phai thu muc", encoding="utf-8")
    monkeypatch.setenv("OPCOS_WORKSPACES", str(f))
    rc, _out, err = _init(monkeypatch, capsys, *argv)
    assert rc == 2 and "OPCOS_WORKSPACES" in err and "Traceback" not in err
    assert f.read_text(encoding="utf-8") == "khong phai thu muc"
    assert not (world["repo"] / "studio.local.json").exists()
    assert not (world["repo"] / "workspaces").exists()


def test_cl47_a_station_slot_that_is_a_file_is_code_2_and_names_the_variable(
        world, monkeypatch, capsys):
    world["ws"].mkdir()
    (world["ws"] / "video").write_text("la mot file", encoding="utf-8")
    monkeypatch.setenv("OPCOS_WORKSPACES", str(world["ws"]))
    rc, _out, err = _init(monkeypatch, capsys, "--yes")
    assert rc == 2 and "OPCOS_WORKSPACES" in err and "Traceback" not in err
    assert (world["ws"] / "video").read_text(encoding="utf-8") == "la mot file"
    assert not (world["repo"] / "studio.local.json").exists()


# Ba ô sau CHỈ ghi lại hành vi hiện tại (dựng, không chặn, không xoá gì). Security hẹp quyết có chặn
# không — nếu chặn thì đổi kỳ vọng ba test này, không phải việc mới.
def test_cl48_a_variable_inside_the_repo_builds_there_current_behaviour(world, monkeypatch, capsys):
    """hành vi hiện tại — security hẹp quyết"""
    inside = world["repo"] / "ws"
    monkeypatch.setenv("OPCOS_WORKSPACES", str(inside))
    rc, out, _err = _init(monkeypatch, capsys, "--yes")
    assert rc == 0 and _json_of(out)["station"] == os.path.abspath(str(inside / "video"))
    assert (inside / "video" / "station.json").is_file()


def test_cl49_a_variable_that_is_itself_a_station_nests_current_behaviour(world, monkeypatch,
                                                                         capsys):
    """hành vi hiện tại — security hẹp quyết"""
    world["ws"].mkdir()
    (world["ws"] / "station.json").write_text("{}", encoding="utf-8")
    monkeypatch.setenv("OPCOS_WORKSPACES", str(world["ws"]))
    rc, out, _err = _init(monkeypatch, capsys, "--yes")
    assert rc == 0 and _json_of(out)["station"] == _oc(world)
    assert (world["ws"] / "video" / "station.json").is_file()
    assert (world["ws"] / "station.json").read_text(encoding="utf-8") == "{}"


def test_cl50_a_non_empty_unmarked_slot_is_used_and_kept_current_behaviour(world, monkeypatch,
                                                                          capsys):
    """hành vi hiện tại — security hẹp quyết"""
    (world["ws"] / "video").mkdir(parents=True)
    (world["ws"] / "video" / "cua-toi.txt").write_text("giu nguyen", encoding="utf-8")
    monkeypatch.setenv("OPCOS_WORKSPACES", str(world["ws"]))
    rc, out, _err = _init(monkeypatch, capsys, "--yes")
    assert rc == 0 and _json_of(out)["station"] == _oc(world)
    assert (world["ws"] / "video" / "cua-toi.txt").read_text(encoding="utf-8") == "giu nguyen"
    assert (world["ws"] / "video" / "station.json").is_file()


def test_a_wheel_install_without_a_repo_has_no_embedded_station_to_keep(world, monkeypatch,
                                                                       tmp_path):
    """Không có bản clone repo thì không có trạm nhúng nào để giữ: `--yes` ra thẳng trạm OpcOS."""
    monkeypatch.setenv("VIDEO_STUDIO_REPO", str(tmp_path / "khong-phai-repo"))
    monkeypatch.setenv("OPCOS_WORKSPACES", str(world["ws"]))
    mode, path, _why = station.choose_mode(yes=True, ask=lambda p: pytest.fail("không được hỏi"))
    assert (mode, path) == ("separate", _oc(world))
