"""Test cho các sửa sau security review RQ-033: tên thiết bị `NUL:`/chữ số trên, B-ROLL chịu JSON lạ, ghi file ra qua fd."""
import json
import os

import pytest

from test_render_project_dir import proj, rec, run  # noqa: F401 — fixture dùng chung
from video_studio import _paths


@pytest.mark.parametrize("value", [
    "NUL:", "C:" + chr(92) + "a" + chr(92) + "NUL:", "nul:.txt", "COM¹", "lpt².txt", "CON:"])
def test_is_device_name_colon_and_superscript_forms(value):
    assert _paths.is_device_name(value) is True


@pytest.mark.parametrize("value", ["C:NUL", "C:CON", "D:COM1", "c:nul.txt", "C:NUL:"])
def test_is_device_name_drive_relative_forms(value):
    assert _paths.is_device_name(value) is True


@pytest.mark.parametrize("value", ["C:", "D:" + chr(92), "a:b.png"])
def test_is_device_name_does_not_flag_drive_letters(value):
    assert _paths.is_device_name(value) is False


@pytest.mark.parametrize("results", [None, "x", 5, {"a": 1}, [1, "x", None], [[]]])
def test_broll_survives_odd_openverse_results(news, monkeypatch, tmp_path, results):
    body = json.dumps({"results": results}).encode()
    monkeypatch.setattr(news._netfetch, "fetch_public", lambda url, **kw: (url, "application/json", body))
    assert news._broll_image("q", str(tmp_path / "b.jpg")) is None


def test_broll_survives_non_object_json(news, monkeypatch, tmp_path):
    monkeypatch.setattr(news._netfetch, "fetch_public", lambda url, **kw: (url, "application/json", b"[1,2]"))
    assert news._broll_image("q", str(tmp_path / "b.jpg")) is None


def test_output_file_is_written_through_the_descriptor(rec, proj, tmp_path, capsys, monkeypatch):
    """RF6: `.part` được ghi qua fd do `mkstemp` trả về; không mở lại theo tên (không `shutil.copyfile` lên đường `.part`)."""
    from video_studio import render
    calls = []
    real = render.shutil.copyfile
    monkeypatch.setattr(render.shutil, "copyfile", lambda s, d, **k: calls.append(str(d)) or real(s, d, **k))
    rc, _ = run(proj, tmp_path, capsys)
    assert rc == 0 and (tmp_path / "out" / "myproj.mp4").read_bytes() == b"mp4"
    assert calls and not [c for c in calls if c.endswith(".mp4.part")]
