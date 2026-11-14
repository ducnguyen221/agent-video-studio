"""`_check_final` và `_stage_project` với liên kết GIẢ (`lstat` giả) — chạy được cả khi máy không tạo được symlink
(Windows không có quyền). Bổ sung cho các ca symlink thật trong `test_render_project_dir_hardening.py` (RQ-033, TK5)."""
import os
import stat
import subprocess
import sys

import pytest

from video_studio import render
from video_studio.contract import ContractError


class FakeStat:
    def __init__(self, mode, attrs=0, size=3, mtime=1):
        self.st_mode, self.st_file_attributes, self.st_size, self.st_mtime_ns = mode, attrs, size, mtime


REG = stat.S_IFREG | 0o644
LNK = stat.S_IFLNK | 0o777
DIR = stat.S_IFDIR | 0o755
REPARSE = 0x400


def _lstat_returning(monkeypatch, st, only="victim"):
    real = os.lstat

    def fake(p, *a, **k):
        return st if only in str(p) else real(p, *a, **k)
    monkeypatch.setattr(render.os, "lstat", fake)


@pytest.mark.parametrize("st", [FakeStat(LNK), FakeStat(REG, REPARSE), FakeStat(DIR), FakeStat(DIR, REPARSE)])
def test_check_final_refuses_links_junctions_and_directories(monkeypatch, st):
    _lstat_returning(monkeypatch, st)
    with pytest.raises(ContractError):
        render._check_final("/out/victim.mp4")


def test_check_final_missing_is_fine_and_regular_warns(monkeypatch, capsys):
    render._check_final(os.path.join(os.sep, "khong", "co", "victim.mp4"))       # chưa có: im lặng
    _lstat_returning(monkeypatch, FakeStat(REG))
    render._check_final("/out/victim.mp4")
    assert "ghi đè" in capsys.readouterr().err


def test_check_final_refuses_non_regular_file(monkeypatch):
    _lstat_returning(monkeypatch, FakeStat(stat.S_IFCHR | 0o600))
    with pytest.raises(ContractError):
        render._check_final("/out/victim.mp4")


def test_stage_refuses_a_file_that_became_a_link_after_scan(tmp_path, monkeypatch):
    d = tmp_path / "p"
    (d / "assets").mkdir(parents=True)
    (d / "index.html").write_text("<html></html>", encoding="utf-8")
    files = render._scan_project(str(d))
    real = os.lstat

    def fake(p, *a, **k):
        st = real(p, *a, **k)
        if str(p).endswith("index.html") and str(d) in str(p):
            return FakeStat(LNK, 0, st.st_size, st.st_mtime_ns)                 # đã bị thay bằng liên kết
        return st
    monkeypatch.setattr(render.os, "lstat", fake)
    with pytest.raises(ContractError):
        render._stage_project(files, str(tmp_path / "stage"))
    assert not (tmp_path / "stage" / "index.html").exists()


@pytest.mark.skipif(sys.platform != "win32", reason="junction chỉ có trên Windows")
def test_final_junction_is_refused_on_windows(tmp_path):
    out = tmp_path / "out"
    out.mkdir()
    victim_dir = tmp_path / "victim_dir"
    victim_dir.mkdir()
    r = subprocess.run(["cmd", "/c", "mklink", "/J", str(out / "myproj.mp4"), str(victim_dir)],
                       capture_output=True)
    if r.returncode:
        pytest.skip("không tạo được junction trên máy này")
    with pytest.raises(ContractError):
        render._check_final(str(out / "myproj.mp4"))
    assert list(victim_dir.iterdir()) == []


def test_stage_refuses_a_file_that_changes_during_the_copy(tmp_path, monkeypatch):
    d = tmp_path / "p"
    (d / "assets").mkdir(parents=True)
    (d / "index.html").write_text("<html></html>", encoding="utf-8")
    files = render._scan_project(str(d))
    real_copy = render.shutil.copyfile

    def copy_then_grow(src, dst, **kw):
        out = real_copy(src, dst, **kw)
        with open(src, "ab") as f:                                              # nguồn phình NGAY sau khi chép
            f.write(b"x" * 50)
        return out
    monkeypatch.setattr(render.shutil, "copyfile", copy_then_grow)
    with pytest.raises(ContractError):
        render._stage_project(files, str(tmp_path / "stage"))


def test_bad_project_name_stops_before_anything_is_created(monkeypatch, tmp_path, capsys):
    """Nối dây: `plain_name` chạy trước khi tạo `--out`/thư mục tạm và trước mọi lời gọi tiến trình."""
    d = tmp_path / "myproj"
    (d / "assets").mkdir(parents=True)
    (d / "index.html").write_text("<html></html>", encoding="utf-8")

    def refuse(*a, **k):
        raise ContractError("tên không hợp lệ")
    monkeypatch.setattr(render._paths, "plain_name", refuse)
    monkeypatch.setattr(render.subprocess, "run", lambda *a, **k: pytest.fail("không được gọi tiến trình"))
    rc = render.main(["--project-dir", str(d), "--out", str(tmp_path / "out"), "--json"])
    assert rc == 2 and not (tmp_path / "out").exists()
