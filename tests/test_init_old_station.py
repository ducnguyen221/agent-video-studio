"""`init` trên máy đã có trạm nhúng mang dấu (có dữ liệu) mà chưa ghi lựa chọn, nay đặt
`OPCOS_WORKSPACES`: dữ liệu có sẵn thắng biến.

* không người / `--yes` / Enter / EOF ⇒ GIỮ trạm nhúng, ghi `mode: embedded`, in một dòng chỉ cách dời sau;
* người dùng gõ `chuyen` ⇒ HAI câu: giữ/chuyển, rồi `y/N` của `migrate`. Hàm chọn chế độ không dời gì:
  `do_init` ghi `embedded` trước, rồi (không `--dry-run`) kiểm đích không rỗng (mã 2, TRƯỚC `y/N`) và
  hỏi `y/N`. `n`/Enter/EOF ở `y/N` ⇒ giữ, mã 0. Ctrl+C ở bất kỳ câu nào ⇒ mã 2, không traceback.
"""
import hashlib
import json
import os

import pytest

from video_studio import contract, station
from video_studio.contract import ContractError

MIGRATE_HINT = "migrate --to separate"


@pytest.fixture
def scene(tmp_path, monkeypatch):
    """Repo có trạm nhúng `workspaces/` mang dấu + dữ liệu; máy đặt OPCOS_WORKSPACES (`<biến>/video` chưa có)."""
    r = tmp_path / "repo"
    (r / "video_studio").mkdir(parents=True)
    (r / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
    (r / ".env.example").write_text("# khuon\nVIDEO_FONT=\n", encoding="utf-8")
    st = r / "workspaces"
    (st / "projects" / "news").mkdir(parents=True)
    (st / "projects" / "news" / "meta.json").write_text('{"ten": "ban tin"}', encoding="utf-8")
    (st / "projects" / "news" / "anh.bin").write_bytes(bytes(range(256)))
    (st / "station.json").write_text(json.dumps({"contract": "1.0", "mode": "embedded"}),
                                     encoding="utf-8")
    ws = tmp_path / "opcos-ws"
    monkeypatch.setenv("VIDEO_STUDIO_REPO", str(r))
    monkeypatch.setenv("OPCOS_WORKSPACES", str(ws))
    monkeypatch.setattr(station, "_stdin_is_tty", lambda: False)
    return {"repo": r, "st": st, "ws": ws, "oc": os.path.abspath(str(ws / "video"))}


def _hashes(root):
    out = {}
    for dp, _dn, fn in os.walk(root):
        for n in fn:
            p = os.path.join(dp, n)
            with open(p, "rb") as f:
                out[os.path.relpath(p, root).replace(os.sep, "/")] = hashlib.sha256(f.read()).hexdigest()
    return out


def _data(root):
    """Băm mọi file của trạm TRỪ `station.json` (init ghi lại file đó khi chạy lại trên trạm cũ)."""
    return {rel: d for rel, d in _hashes(root).items() if rel != "station.json"}


def _still_there(before, root):
    """Mọi file có trước đó vẫn còn nguyên từng byte (init chỉ được THÊM file mẫu, không sửa/xoá)."""
    after = _data(root)
    return all(after.get(rel) == digest for rel, digest in before.items())


def _script(*answers):
    """ask giả: mỗi lần hỏi lấy một câu trả lời (sentinel ném EOF/Ctrl+C); hỏi nhiều hơn thì đỏ."""
    seen, it = [], iter(answers)

    def ask(prompt):
        seen.append(prompt)
        try:
            a = next(it)
        except StopIteration:
            pytest.fail("hỏi nhiều hơn dự kiến: " + prompt)
        if a == "<EOF>":
            raise EOFError
        if a == "<CTRL-C>":
            raise KeyboardInterrupt
        return a
    ask.seen = seen
    return ask


def _local(scene):
    return json.loads((scene["repo"] / "studio.local.json").read_text(encoding="utf-8"))


def test_move_and_yes_moves_every_file_and_records_separate(scene):
    before = _hashes(scene["st"])
    ask = _script("chuyen", "y")
    res = station.do_init(ask=ask)
    assert len(ask.seen) == 2 and "y/N" in ask.seen[1]
    assert (res["mode"], res["station"]) == ("separate", scene["oc"])
    assert not scene["st"].exists()
    after = _hashes(scene["oc"])
    for rel, digest in before.items():
        if rel != "station.json":                           # station.json: chỉ `mode` đổi
            assert after[rel] == digest, rel
    sj = json.loads(open(os.path.join(scene["oc"], "station.json"), encoding="utf-8").read())
    assert sj["mode"] == "separate" and sj["contract"] == "1.0"
    local = _local(scene)
    assert local["mode"] == "separate" and local["station_path"] == scene["oc"]


@pytest.mark.parametrize("second", [
    pytest.param("n", id="no"),
    pytest.param("", id="enter"),
    pytest.param("<EOF>", id="eof"),
])
def test_move_but_declined_at_the_yes_no_question_keeps_everything(scene, capsys, second):
    before = _data(scene["st"])
    ask = _script("chuyen", second)
    res = station.do_init(ask=ask)
    assert len(ask.seen) == 2
    assert (res["mode"], res["station"]) == ("embedded", str(scene["st"]))
    assert _local(scene)["mode"] == "embedded"
    assert _still_there(before, scene["st"])                                  # 0 byte dời
    assert not os.path.exists(scene["oc"])
    assert MIGRATE_HINT in capsys.readouterr().err                           # chỉ lệnh dời sau


def test_move_into_a_non_empty_target_is_code_2_before_the_yes_no_question(scene):
    os.makedirs(scene["oc"])
    with open(os.path.join(scene["oc"], "cua-nguoi-khac.txt"), "w", encoding="utf-8") as f:
        f.write("khong dung vao")
    before = _data(scene["st"])
    ask = _script("chuyen")                                  # câu thứ hai mà bị hỏi ⇒ đỏ
    with pytest.raises(ContractError, match="không rỗng"):
        station.do_init(ask=ask)
    assert len(ask.seen) == 1
    assert _local(scene)["mode"] == "embedded"               # trạm cũ đã ghi và dùng được
    assert _still_there(before, scene["st"])
    assert os.listdir(scene["oc"]) == ["cua-nguoi-khac.txt"]


def test_two_stations_move_is_code_2_because_the_target_is_not_empty(scene):
    os.makedirs(scene["oc"])
    with open(os.path.join(scene["oc"], "station.json"), "w", encoding="utf-8") as f:
        f.write("{}")
    ask = _script("chuyen")
    with pytest.raises(ContractError, match="không rỗng"):
        station.do_init(ask=ask)
    assert len(ask.seen) == 1 and _local(scene)["mode"] == "embedded"


def test_dry_run_with_move_prints_the_plan_and_changes_nothing(scene, capsys):
    before = _hashes(str(scene["repo"]))
    ask = _script("chuyen")
    res = station.do_init(ask=ask, dry_run=True)
    assert len(ask.seen) == 1                                # không có câu y/N khi chỉ xem trước
    assert res["then_migrate"] == scene["oc"] and res["dry_run"] is True
    assert _hashes(str(scene["repo"])) == before             # 0 byte: kể cả studio.local.json
    assert not (scene["repo"] / "studio.local.json").exists() and not os.path.exists(scene["oc"])
    station._print_init(res)
    assert "sẽ dời" in capsys.readouterr().err


def test_dry_run_with_yes_keeps_and_writes_nothing(scene):
    before = _hashes(str(scene["repo"]))
    res = station.do_init(yes=True, dry_run=True)
    assert (res["mode"], res["station"]) == ("embedded", str(scene["st"]))
    assert _hashes(str(scene["repo"])) == before and not (scene["repo"] / "studio.local.json").exists()


def test_a_second_init_after_keeping_asks_nothing_and_stays_quiet(scene, capsys):
    station.do_init(yes=True)                                # giữ + ghi `embedded`
    first = capsys.readouterr().err
    assert MIGRATE_HINT in first
    ask = _script()                                          # bất kỳ câu hỏi nào ⇒ đỏ
    res = station.do_init(ask=ask)
    assert ask.seen == [] and res["mode"] == "embedded"
    assert MIGRATE_HINT not in capsys.readouterr().err       # lựa chọn đã ghi: không nhắc lại


def test_after_a_confirmed_move_the_next_init_uses_the_recorded_separate_station(scene):
    station.do_init(ask=_script("chuyen", "y"))
    ask = _script()
    res = station.do_init(ask=ask, yes=True)
    assert ask.seen == [] and (res["mode"], res["station"]) == ("separate", scene["oc"])


def test_ctrl_c_at_the_yes_no_question_leaves_embedded_recorded_and_moves_nothing(scene):
    before = _data(scene["st"])
    with pytest.raises(KeyboardInterrupt):
        station.do_init(ask=_script("chuyen", "<CTRL-C>"))
    assert _local(scene)["mode"] == "embedded"
    assert _still_there(before, scene["st"])
    assert not os.path.exists(scene["oc"])


def test_ctrl_c_through_the_cli_edge_is_code_2_one_line_no_traceback(scene, capsys):
    ask = _script("chuyen", "<CTRL-C>")
    rc = contract.run(lambda _a: station.do_init(ask=ask), None, as_json=True)
    cap = capsys.readouterr()
    assert rc == 2 and "đã huỷ" in cap.err and "Traceback" not in cap.err
    assert json.loads(cap.out.strip().splitlines()[-1]) == {
        "ok": False, "code": 2, "error": "đã huỷ (Ctrl+C)"}


def test_ctrl_c_at_the_first_question_writes_nothing(scene, monkeypatch, capsys):
    monkeypatch.setattr(station, "_stdin_is_tty", lambda: True)

    def boom(*_a):
        raise KeyboardInterrupt
    monkeypatch.setattr("builtins.input", boom)
    rc = station.init_main(["--json"])
    cap = capsys.readouterr()
    assert rc == 2 and "đã huỷ" in cap.err and "Traceback" not in cap.err
    assert not (scene["repo"] / "studio.local.json").exists() and not os.path.exists(scene["oc"])


def test_after_a_confirmed_move_the_closing_lines_do_not_offer_an_undo_that_moves_nothing(
        scene, capsys):
    res = station.do_init(ask=_script("chuyen", "y"))
    capsys.readouterr()
    station._print_init(res)
    err = capsys.readouterr().err
    assert "--undo" not in err and scene["oc"] in err


def test_a_plain_embedded_init_still_offers_its_undo(scene, capsys):
    res = station.do_init(yes=True)
    capsys.readouterr()
    station._print_init(res)
    assert "--undo" in capsys.readouterr().err


def test_moving_into_a_variable_that_leads_back_into_the_station_is_code_2_before_the_yes_no_question(
        scene, tmp_path, monkeypatch):
    import subprocess
    link = tmp_path / "lnk"
    inner = scene["st"] / "sub"                              # thư mục con KHÔNG mang dấu trạm
    inner.mkdir()
    try:
        os.symlink(str(inner), str(link), target_is_directory=True)
    except (OSError, NotImplementedError) as e:
        if os.name != "nt" or subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(inner)],
                                             capture_output=True).returncode:
            pytest.skip(f"máy này không tạo được liên kết mềm lẫn điểm nối: {e}")
    monkeypatch.setenv("OPCOS_WORKSPACES", str(link))
    before = _data(scene["st"])
    ask = _script("chuyen")                                  # câu y/N mà bị hỏi ⇒ đỏ
    with pytest.raises(ContractError, match="nằm trong trạm"):
        station.do_init(ask=ask)
    assert len(ask.seen) == 1 and _local(scene)["mode"] == "embedded"
    assert _still_there(before, scene["st"])
