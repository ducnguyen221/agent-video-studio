"""`render --project-dir` gia cố (RQ-033, TK5): TOCTOU quét→chép, đích ghi an toàn, đủ dòng lỗi, khoá npm.

Dùng lại fixture của `test_render_project_dir.py` (tiến trình giả, không cần Node).
"""
import os
import subprocess
import sys

import pytest

from conftest import last_json
from test_render_project_dir import FAKE_NPX, proj, rec, run  # noqa: F401 — fixture dùng chung
from video_studio import _env, render
from video_studio.contract import ContractError


def _symlink_or_skip(target, link):
    try:
        os.symlink(target, link)
    except (OSError, NotImplementedError):
        pytest.skip("symlink không tạo được trên máy này")


# ── TOCTOU giữa quét và chép ──────────────────────────────────────────────────────────────

def test_stage_detects_file_grown_after_scan(proj, tmp_path):
    files = render._scan_project(str(proj))
    (proj / "assets" / "a.png").write_bytes(b"png" + b"x" * 100)       # phình sau khi quét
    with pytest.raises(ContractError):
        render._stage_project(files, str(tmp_path / "stage"))


def test_stage_detects_same_size_rewrite_after_scan(proj, tmp_path):
    files = render._scan_project(str(proj))
    target = proj / "assets" / "a.png"
    st = target.stat()
    target.write_bytes(b"PNG")                                          # cùng kích thước, nội dung khác
    os.utime(target, ns=(st.st_atime_ns, st.st_mtime_ns + 5_000_000_000))
    with pytest.raises(ContractError):
        render._stage_project(files, str(tmp_path / "stage"))


def test_stage_detects_swap_to_symlink_after_scan(proj, tmp_path):
    files = render._scan_project(str(proj))
    secret = tmp_path / "secret.txt"
    secret.write_text("s", encoding="utf-8")
    victim = proj / "assets" / "a.png"
    victim.unlink()
    _symlink_or_skip(secret, victim)
    with pytest.raises(ContractError):
        render._stage_project(files, str(tmp_path / "stage"))
    staged = tmp_path / "stage" / "assets" / "a.png"
    assert not staged.exists() and not os.path.islink(staged)


def test_total_cap_is_rechecked_on_what_was_copied(proj, tmp_path, monkeypatch):
    files = render._scan_project(str(proj))
    monkeypatch.setattr(render, "PROJECT_MAX_BYTES", 5)                 # nhỏ hơn index.html (13 byte)
    with pytest.raises(ContractError):
        render._stage_project(files, str(tmp_path / "stage"))


def test_stage_ok_when_nothing_changes(proj, tmp_path):
    files = render._scan_project(str(proj))
    render._stage_project(files, str(tmp_path / "stage"))
    assert sorted(os.listdir(tmp_path / "stage")) == ["assets", "index.html"]


# ── tên project phải là tên tệp trần, kiểm TRƯỚC khi tạo gì ───────────────────────────────

@pytest.mark.parametrize("bad", ["ba:d", "name.", "name ", "con\x00x"])
def test_project_name_must_be_a_plain_file_name(bad):
    with pytest.raises(ContractError):
        render._project_name(os.path.join("x", bad))


def test_project_name_plain_ok_and_root_fallback():
    assert render._project_name(os.path.join("x", "myproj")) == "myproj"
    assert render._project_name(os.path.abspath(os.sep)) == "project"


@pytest.mark.skipif(sys.platform == "win32", reason="Windows cắt dấu chấm cuối tên thư mục nên ca này không tạo được")
def test_trailing_dot_directory_rejected_before_out_created(rec, tmp_path, capsys):
    d = tmp_path / "proj."
    (d / "assets").mkdir(parents=True)
    (d / "index.html").write_text("<html></html>", encoding="utf-8")
    rc, _ = run(d, tmp_path, capsys)
    assert rc == 2 and not rec.calls and not (tmp_path / "out").exists()


# ── đích ghi ──────────────────────────────────────────────────────────────────────────────

def test_final_symlink_is_refused_and_target_untouched(rec, proj, tmp_path, capsys):
    out = tmp_path / "out"
    out.mkdir()
    victim = tmp_path / "victim.mp4"
    victim.write_bytes(b"orig")
    _symlink_or_skip(victim, out / "myproj.mp4")
    rc, _ = run(proj, tmp_path, capsys)
    assert rc == 2 and victim.read_bytes() == b"orig"


def test_final_dangling_symlink_is_refused(rec, proj, tmp_path, capsys):
    out = tmp_path / "out"
    out.mkdir()
    ghost = tmp_path / "ghost.mp4"
    _symlink_or_skip(ghost, out / "myproj.mp4")
    rc, _ = run(proj, tmp_path, capsys)
    assert rc == 2 and not ghost.exists()


def test_final_directory_is_refused(rec, proj, tmp_path, capsys):
    (tmp_path / "out" / "myproj.mp4").mkdir(parents=True)
    rc, _ = run(proj, tmp_path, capsys)
    assert rc == 2


def test_part_file_name_is_not_predictable(rec, proj, tmp_path, capsys):
    out = tmp_path / "out"
    out.mkdir()
    victim = tmp_path / "victim.bin"
    victim.write_bytes(b"orig")
    for guess in ("myproj.mp4.tmp", "myproj.mp4.part", "myproj.tmp", "render.mp4"):
        _symlink_or_skip(victim, out / guess)
    rc, _ = run(proj, tmp_path, capsys)
    assert rc == 0 and victim.read_bytes() == b"orig"
    assert (out / "myproj.mp4").read_bytes() == b"mp4"


def test_final_regular_file_is_replaced_with_a_warning(rec, proj, tmp_path, capsys):
    out = tmp_path / "out"
    out.mkdir()
    (out / "myproj.mp4").write_bytes(b"old")
    rc, cap = run(proj, tmp_path, capsys)
    assert rc == 0 and (out / "myproj.mp4").read_bytes() == b"mp4"
    assert "ghi đè" in cap.err


def test_no_part_files_left_after_success_or_failure(rec, proj, tmp_path, capsys):
    run(proj, tmp_path, capsys)
    assert [p for p in os.listdir(tmp_path / "out") if p != "myproj.mp4"] == []


# ── RF26: đủ dòng lỗi ────────────────────────────────────────────────────────────────────

def test_check_failure_message_keeps_60_lines_and_says_what_was_cut(rec, proj, tmp_path, capsys, monkeypatch):
    lines = "\n".join(f"L{i}" for i in range(100)).encode()

    def noisy(argv, **kw):
        return subprocess.CompletedProcess(argv, 1, b"", lines)
    monkeypatch.setattr(render.subprocess, "run", noisy)
    rc, cap = run(proj, tmp_path, capsys)
    msg = last_json(cap.out)["error"]
    assert rc == 2 and "L99" in msg and "L40" in msg and "L39" not in msg and "cắt 40 dòng đầu" in msg


def test_check_tail_short_output_is_not_marked_cut():
    assert render._check_tail("a\nb\nc") == "a\nb\nc"
    assert "cắt" not in render._check_tail("\n".join(str(i) for i in range(60)))


# ── RF28: khoá npm khác hoa/thường ───────────────────────────────────────────────────────

def test_npm_keys_differing_only_by_case_are_removed_in_render_project(monkeypatch, tmp_path):
    seen = {}

    def spy(argv, **kw):
        seen["env"] = kw["env"]
        return subprocess.CompletedProcess(argv, 0, b"", b"")
    monkeypatch.setattr(render.subprocess, "run", spy)
    monkeypatch.setattr(_env, "npx_exe", lambda: FAKE_NPX)
    monkeypatch.setattr(_env, "hyperframes_spec", lambda version=None: "hyperframes@9.9.9")
    monkeypatch.setattr(render, "render_env",
                        lambda *a, **k: {"NPM_CONFIG_USERCONFIG": "/evil", "Npm_Config_Offline": "x", "PATH": "p"})
    render.render_project(str(tmp_path), "o.mp4", env_extra={"npm_config_userconfig": "/good"}, offline=True)
    env = seen["env"]
    keys = [k for k in env if k.lower() == "npm_config_userconfig"]
    assert keys == ["npm_config_userconfig"] and env[keys[0]] == "/good"
    off = [k for k in env if k.lower() == "npm_config_offline"]
    assert off == ["npm_config_offline"] and env[off[0]] == "true"
