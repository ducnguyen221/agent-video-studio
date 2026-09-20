"""Hợp đồng CLI: `video-studio` chạy như TIẾN TRÌNH THẬT trên máy chưa có Node/ffmpeg/engine —
`--help` phải xong mã 0, lệnh chưa có phải nói thẳng bằng mã 2 (kèm JSON nếu người gọi xin)."""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from video_studio import __version__
from video_studio.cli import COMMANDS, main
from conftest import last_json

ROOT = Path(__file__).resolve().parent.parent


def run_proc(args, env=None):
    e = dict(os.environ, PYTHONPATH=str(ROOT), PYTHONIOENCODING="utf-8", **(env or {}))
    return subprocess.run([sys.executable, "-m", "video_studio", *args], capture_output=True,
                          text=True, encoding="utf-8", errors="replace", env=e, timeout=120)


def test_help_runs_as_a_real_process_without_engine():
    r = run_proc(["--help"])
    assert r.returncode == 0, r.stderr
    assert "video-studio" in r.stdout and "init" in r.stdout and "doctor" in r.stdout
    assert "0 ok" in r.stdout


def test_version_flag():
    r = run_proc(["--version"])
    assert r.returncode == 0 and __version__ in r.stdout


def test_init_dry_run_as_a_real_process_writes_nothing(tmp_path):
    st = tmp_path / "st"
    r = run_proc(["init", "--station", str(st), "--dry-run", "--json"])
    assert r.returncode == 0, r.stderr
    assert not st.exists()
    data = json.loads([ln for ln in r.stdout.splitlines() if ln.strip()][-1])
    assert data["ok"] is True and data["dry_run"] is True


def test_unknown_command_is_code_2():
    r = run_proc(["khong-co-lenh-nay"])
    assert r.returncode == 2 and "lệnh lạ" in r.stderr


def test_no_command_is_still_a_placeholder():
    """Mọi lệnh trong bảng đều đã có mã thật. Bảng rỗng chỗ nào là `--help` nói dối chỗ đó."""
    missing = sorted(c for c, (t, _d) in COMMANDS.items() if t is None)
    assert missing == [], f"lệnh chưa nối vào mã: {missing}"


def test_a_placeholder_would_say_so_and_honour_json(monkeypatch, capsys):
    """Đột biến: nếu sau này có lệnh chưa làm, nó phải nói thẳng mã 2 chứ không giả vờ chạy."""
    monkeypatch.setitem(COMMANDS, "sap-co", (None, "lệnh của bản sau"))
    assert main(["sap-co"]) == 2
    assert "chưa có" in capsys.readouterr().err
    assert main(["sap-co", "--json"]) == 2
    out = capsys.readouterr().out
    assert last_json(out)["ok"] is False and last_json(out)["code"] == 2


def test_bad_arguments_to_a_real_command_still_emit_json(capsys):
    assert main(["render", "--json"]) == 2
    out = capsys.readouterr().out
    assert last_json(out)["ok"] is False and last_json(out)["code"] == 2


def test_a_module_that_fails_to_import_still_ends_in_one_json_line(monkeypatch, capsys):
    """`import_module` chạy TRƯỚC `contract.run` của lệnh con.

    Một module hỏng (thiếu phụ thuộc tuỳ chọn, lỗi cú pháp sau một lần sửa) cho traceback
    TRẦN: `--json` không có dòng JSON nào, và bên gọi theo CONTRACT.md §2 vỡ chứ không đọc
    được lỗi. Lớp NẠP cũng phải nằm trong hợp đồng.
    """
    monkeypatch.setitem(COMMANDS, "hong", ("video_studio._khong_he_ton_tai", "lệnh hỏng"))
    rc = main(["hong", "--json"])
    assert rc in (1, 3)                              # tuỳ ImportError được phân loại thế nào
    payload = last_json(capsys.readouterr().out)     # <- chính là thứ trước đây KHÔNG có
    assert payload["ok"] is False
    assert "không nạp được lệnh" in payload["error"]


def test_a_module_without_the_entry_function_is_not_a_bare_traceback(monkeypatch, capsys):
    monkeypatch.setitem(COMMANDS, "hong2", ("video_studio.contract:khong_co_ham", "lệnh hỏng"))
    rc = main(["hong2", "--json"])
    assert rc != 0
    assert last_json(capsys.readouterr().out)["ok"] is False


def test_every_command_documented_in_help():
    from video_studio.cli import usage
    text = usage()
    for name in COMMANDS:
        assert f"  {name}" in text, name
