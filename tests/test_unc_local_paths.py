"""Đường UNC/thiết bị không bị probe, tên ổ chỉ ASCII, tên thiết bị Windows (RQ-033, TK4; RF23, RF27)."""
import importlib
import os

import pytest

from video_studio import _paths
from video_studio.reference import spec_audit

B = chr(92)


@pytest.mark.parametrize("value", [
    B * 2 + "srv" + B + "share" + B + "a.png", "//srv/share/a.png", B + "/srv/share/a.png",
    B * 2 + "?" + B + "C:" + B + "a.png", B * 2 + "." + B + "NUL", B + "??" + B + "C:" + B + "a.png",
    "é:" + B + "a.png", "1:" + B + "a.png", "ǅ:/a.png"])
def test_is_unc_like_true(value):
    assert _paths.is_unc_like(value) is True


@pytest.mark.parametrize("value", [
    "C:" + B + "a.png", "c:/a.png", "/tmp/a.png", "a.png", "rel/x.png", "D:", "x" + B + "y.png"])
def test_is_unc_like_false(value):
    assert _paths.is_unc_like(value) is False


@pytest.mark.parametrize("value", [
    "NUL", "nul.png", "COM1", "lpt9.txt", "CONIN$", "conout$.x", "C:" + B + "x" + B + "NUL", "NUL.", "con .",
    "assets/CON.png", "AUX", "PRN.txt"])
def test_is_device_name_true(value):
    assert _paths.is_device_name(value) is True


@pytest.mark.parametrize("value", ["null.png", "COM10", "console.png", "a/b.png", "lpt0.txt", "x.nul", ""])
def test_is_device_name_false(value):
    assert _paths.is_device_name(value) is False


def _trap(monkeypatch, tmp_log):
    """Bẫy: ném `AssertionError` nếu hàm hệ tệp nhận đường UNC; còn lại gọi hàm thật."""
    def wrap(mod, name):
        real = getattr(mod, name)

        def f(p, *a, **k):
            if isinstance(p, str) and p.replace("/", B).startswith(B * 2):
                tmp_log.append((name, p))
                raise AssertionError(f"{name} bị gọi trên đường UNC: {p}")
            return real(p, *a, **k)
        monkeypatch.setattr(mod, name, f)
    for n in ("isfile", "realpath", "getsize", "islink", "exists", "isdir"):
        wrap(os.path, n)
    wrap(os, "lstat")
    wrap(os, "stat")


UNC = ["//srv/share/a.png", B * 2 + "srv" + B + "share" + B + "a.png", B * 2 + "?" + B + "C:" + B + "a.png"]


def test_download_images_never_touches_unc_paths(news, monkeypatch, tmp_path, capsys):
    log = []
    _trap(monkeypatch, log)
    got = news._download_images(UNC, str(tmp_path / "d"), 1, max_n=len(UNC))
    assert got == [] and log == []
    assert capsys.readouterr().out.count("[warn] image 1/") == len(UNC)


def test_guard_user_images_never_touches_unc_paths(news, monkeypatch, tmp_path):
    log = []
    _trap(monkeypatch, log)
    news.guard_user_images([{"images": UNC}], str(tmp_path / "img"))
    assert log == []


def test_top_story_local_media_and_guard_never_touch_unc_paths(news, monkeypatch, tmp_path, capsys):
    ts = importlib.import_module("video_studio.templates.news.top_story_video")
    log = []
    _trap(monkeypatch, log)
    for src in UNC:
        assert ts._local_media(src, str(tmp_path), news._LOCAL_EXTS, "ảnh s1/0") is None
    ts.guard_media_sources([{"media": [{"type": "image", "src": s} for s in UNC]}],
                           str(tmp_path), str(tmp_path / "media"))
    assert log == []
    assert capsys.readouterr().out.count("[warn] ảnh s1/0 bỏ") == len(UNC)


def test_device_name_local_image_is_dropped_without_probing(news, monkeypatch, tmp_path, capsys):
    probed = []
    real = os.path.isfile
    monkeypatch.setattr(os.path, "isfile", lambda p: probed.append(p) or real(p))
    got = news._download_images([str(tmp_path / "NUL.png"), "C:" + B + "x" + B + "CON.png"], str(tmp_path / "d"), 1, max_n=2)
    assert got == []
    assert not any("NUL" in str(p).upper() or "CON" in str(p).upper() for p in probed)


def _spec(tmp_path, data):
    import json
    p = tmp_path / "spec.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    return str(p)


def test_spec_audit_reports_device_names_and_non_ascii_drives(tmp_path, monkeypatch):
    proj = tmp_path / "proj"
    (proj / "assets").mkdir(parents=True)
    probed = []
    real = os.path.isfile
    monkeypatch.setattr(os.path, "isfile", lambda p: probed.append(p) or real(p))
    values = ["NUL.png", "assets/CON.png", "é:" + B + "a.png"]
    res = spec_audit.audit_spec(_spec(tmp_path, {"v": values}), str(proj))
    assert res["ok"] is False and len(res["findings"]) == len(values)
    assert not any(str(p).upper().endswith(("NUL.PNG", "CON.PNG")) for p in probed)
    # chữ trần "con" (từ tiếng Việt) không phải phát hiện
    ok = spec_audit.audit_spec(_spec(tmp_path, {"v": ["con", "Con mèo"]}), str(proj))
    assert ok["findings"] == []
