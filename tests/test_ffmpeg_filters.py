"""ffmpeg phải ĐỦ bộ lọc chữ, không chỉ "có lệnh" (Mac mini 01/10/2026).

`brew install ffmpeg` (Homebrew core) đã bỏ libfreetype + libass ⇒ không có `drawtext`,
`subtitles`, `ass`. `doctor` cũ chỉ hỏi có lệnh `ffmpeg` nên báo PASS, rồi `edit` đốt phụ đề
và runner truyện của marketing-studio chết ở bước cuối. Ba cổng:

    · `doctor` có dòng `ffmpeg-filters` (WARN khi thiếu — render bản tin không cần);
    · `edit` chặn bằng mã 3 TRƯỚC khi cắt/ghép khi cần `subtitles` mà ffmpeg không có;
    · macOS dò keg-only `ffmpeg-full` TRƯỚC `PATH`.

Smoke cuối file chạy ffmpeg THẬT; thiếu thì skip — trừ khi `VIDEO_STUDIO_REQUIRE_FFMPEG=1`
(CI đặt sau khi cài theo INSTALL), khi đó thiếu là đỏ.
"""
import os
import subprocess

import pytest

from video_studio import _env, doctor
from video_studio.contract import StationMissing
from video_studio.edit import edl as edl_mod, render as edit_render

FILTERS_FULL = """Filters:
  T.. = Timeline support
 ... ass               V->V       Render ASS subtitles onto input video using the libass library.
 T.C drawtext          V->V       Draw text on top of video frames using libfreetype library.
 ... subtitles         V->V       Render text subtitles onto input video using the libass library.
 TSC scale             V->V       Scale the input video size and/or convert the image format.
"""
FILTERS_CORE = " TSC scale             V->V       Scale the input video size.\n"


def _fake(monkeypatch, stdout, rc=0):
    monkeypatch.setattr(_env.subprocess, "run",
                        lambda argv, **kw: subprocess.CompletedProcess(argv, rc, stdout, ""))


def test_ffmpeg_filters_reads_names(monkeypatch):
    _fake(monkeypatch, FILTERS_FULL)
    assert {"ass", "drawtext", "subtitles", "scale"} <= _env.ffmpeg_filters("/x/ffmpeg")


@pytest.mark.parametrize("out,rc", [("", 0), (FILTERS_FULL, 1), ("rác", 0)])
def test_ffmpeg_filters_unreadable_is_none(monkeypatch, out, rc):
    _fake(monkeypatch, out, rc)
    assert _env.ffmpeg_filters("/x/ffmpeg") is None


def test_doctor_filters_pass(monkeypatch):
    _fake(monkeypatch, FILTERS_FULL)
    c = doctor.filter_check("/x/ffmpeg")
    assert c["level"] == "ok" and c["name"] == "ffmpeg-filters"


def test_doctor_core_ffmpeg_is_WARN_with_ffmpeg_full_hint(monkeypatch):
    _fake(monkeypatch, FILTERS_CORE)
    c = doctor.filter_check("/x/ffmpeg")
    assert c["level"] == "warn" and c["ok"] is False
    assert "drawtext" in c["detail"] and "subtitles" in c["detail"] and "edit" in c["detail"]
    assert "ffmpeg-full" in c["hint"]


def test_doctor_filters_skip_without_ffmpeg():
    assert doctor.filter_check(None)["level"] == "skip"


def test_doctor_filter_warn_does_not_change_exit_code(monkeypatch):
    """WARN không chặn: render bản tin (HyperFrames) vẫn chạy được với ffmpeg core."""
    _fake(monkeypatch, FILTERS_CORE)
    c = doctor.filter_check("/x/ffmpeg")
    assert c["level"] != "error"


def test_macos_prefers_keg_ffmpeg_full_over_core_on_PATH(monkeypatch):
    monkeypatch.setattr(_env.sys, "platform", "darwin")
    monkeypatch.delenv("FFMPEG_DIR", raising=False)
    monkeypatch.setattr(_env, "env", lambda name, *a, **k: None)

    def which(name, path=None):
        if path and "ffmpeg-full" in path:
            return f"{path}/{name}"
        return f"/opt/homebrew/bin/{name}"
    monkeypatch.setattr(_env.shutil, "which", which)
    assert _env.ffmpeg_exe() == "/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg"
    assert _env.ffprobe_exe() == "/opt/homebrew/opt/ffmpeg-full/bin/ffprobe"


def test_windows_does_not_look_for_keg(monkeypatch):
    monkeypatch.setattr(_env.sys, "platform", "win32")
    monkeypatch.setattr(_env, "env", lambda name, *a, **k: None)
    seen = []
    monkeypatch.setattr(_env.shutil, "which",
                        lambda name, path=None: seen.append(path) or r"C:\ff\ffmpeg.exe")
    assert _env.ffmpeg_exe() == r"C:\ff\ffmpeg.exe" and seen == [None]


def _edl_with_subs(tmp_path):
    (tmp_path / "a.mp4").write_text("x", encoding="utf-8")
    (tmp_path / "s.srt").write_text("1\n00:00:00,000 --> 00:00:01,000\nhi\n", encoding="utf-8")
    return edl_mod.validate({"sources": {"a": "a.mp4"}, "subtitles": "s.srt",
                             "ranges": [{"source": "a", "start": 0, "end": 1}]})


def test_edit_refuses_BEFORE_cutting_when_subtitles_filter_missing(monkeypatch, tmp_path):
    monkeypatch.setattr(_env, "ffmpeg_filters", lambda exe=None: {"scale"})
    called = []
    monkeypatch.setattr(edit_render, "extract_all", lambda *a, **k: called.append(1) or [])
    with pytest.raises(StationMissing) as e:
        edit_render.render_edl(_edl_with_subs(tmp_path), str(tmp_path), str(tmp_path / "w"),
                               str(tmp_path / "o.mp4"))
    assert "subtitles" in str(e.value) and "ffmpeg-full" in str(e.value)
    assert called == [], "đã cắt đoạn trước khi biết ffmpeg không đốt được phụ đề"


def test_edit_without_subtitles_does_not_need_the_filter(monkeypatch, tmp_path):
    monkeypatch.setattr(_env, "ffmpeg_filters", lambda exe=None: {"scale"})
    monkeypatch.setattr(edit_render, "extract_all", lambda *a, **k: (_ for _ in ()).throw(
        RuntimeError("đi tiếp")))
    with pytest.raises(RuntimeError, match="đi tiếp"):
        edit_render.render_edl(_edl_with_subs(tmp_path), str(tmp_path), str(tmp_path / "w"),
                               str(tmp_path / "o.mp4"), subtitles=False)


# ── smoke: ffmpeg THẬT ───────────────────────────────────────────────────────────────────

REQUIRED = os.environ.get("VIDEO_STUDIO_REQUIRE_FFMPEG") == "1"


def _need(reason):
    if REQUIRED:
        pytest.fail(f"VIDEO_STUDIO_REQUIRE_FFMPEG=1 mà {reason}")
    pytest.skip(reason)


def test_smoke_real_ffmpeg_has_text_filters_and_burns_subtitles(tmp_path):
    ff = _env.ffmpeg_exe()
    if not ff:
        _need("không có ffmpeg")
    have = _env.ffmpeg_filters(ff)
    if have is None:
        _need(f"không đọc được bộ lọc của {ff}")
    missing = [f for f in _env.TEXT_FILTERS if f not in have]
    if missing:
        _need(f"{ff} thiếu {missing} — {doctor.HINT_FFMPEG}")
    base = tmp_path / "base.mp4"
    subprocess.run([ff, "-y", "-hide_banner", "-loglevel", "error", "-f", "lavfi",
                    "-i", "color=c=black:size=320x180:rate=25:duration=2", "-f", "lavfi",
                    "-i", "sine=duration=2", "-shortest", "-c:v", "libx264", "-c:a", "aac",
                    "-pix_fmt", "yuv420p", str(base)], check=True, capture_output=True)
    srt = tmp_path / "s.srt"
    srt.write_text("1\n00:00:00,200 --> 00:00:01,800\nXin chào phụ đề\n", encoding="utf-8")
    out = tmp_path / "out.mp4"
    edit_render.composite(str(base), [], str(srt), str(out), str(tmp_path))
    assert out.is_file() and out.stat().st_size > 1000
