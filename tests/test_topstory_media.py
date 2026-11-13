"""`topstory`: lọc file trong `sec.media` (RQ-004), từ chối media trỏ vào `media/` (RQ-005 cùng lớp),
nhiều ảnh mỗi phần (RQ-003). Không Node/ffmpeg/giọng/mạng (`news_harness.py`)."""
import importlib
import os

import pytest

import news_harness as h
from video_studio.contract import ContractError
from video_studio.spec import USER_IMAGE_KEY


@pytest.fixture
def ts(news, monkeypatch, tmp_path):
    mod = importlib.import_module("video_studio.templates.news.top_story_video")
    proj = tmp_path / "proj"
    cap = h.install(monkeypatch, news, proj, ts=mod)
    mod.BRAND.clear()
    mod._apply_branding(h.MIN_BRAND)
    monkeypatch.setattr(mod, "_fit_clip", lambda src, dst, want: open(dst, "wb").write(b"clip"))
    monkeypatch.setattr(mod, "_render", lambda html, *a, **k: cap.append(html) or "x.mp4")
    monkeypatch.setattr(mod, "_voice_track", lambda *a, **k: [])
    monkeypatch.setattr(mod.nv, "_download_images", lambda *a, **k: [])
    mod.cap = cap
    mod.proj = proj
    return mod


def _spec_dir(tmp_path):
    d = tmp_path / "spec"
    d.mkdir()
    return d


def _prep(ts, sec, json_dir):
    return ts._prep_media(sec, 1, str(json_dir), 5.0, "L")


# ── RQ-004: lọc đuôi, thư mục spec, symlink ──────────────────────────────────────────────

def test_image_with_foreign_extension_is_not_copied(ts, tmp_path, capsys):
    d = _spec_dir(tmp_path)
    (d / "secret.txt").write_text("khong phai anh")
    (d / "a.png").write_bytes(h.PNG)
    out = _prep(ts, {"media": [{"type": "image", "src": "secret.txt"},
                               {"type": "image", "src": "a.png"}]}, d)
    assert [m["src"] for m in out] == ["media/L1_1.png"]
    assert not [f for f in os.listdir(ts.proj / "media") if f.endswith(".txt")]
    assert "[warn]" in capsys.readouterr().out


def test_clip_with_foreign_extension_is_refused(ts, tmp_path):
    d = _spec_dir(tmp_path)
    (d / "notes.txt").write_text("x")
    assert _prep(ts, {"media": [{"type": "clip", "src": "notes.txt"}]}, d) == []


def test_clip_with_clip_extension_is_accepted(ts, tmp_path):
    d = _spec_dir(tmp_path)
    (d / "c.mp4").write_bytes(b"x")
    assert _prep(ts, {"media": [{"type": "clip", "src": "c.mp4"}]}, d) == \
        [{"kind": "clip", "src": "media/L1_0.mp4"}]


def test_relative_path_escaping_the_spec_dir_is_refused(ts, tmp_path):
    d = _spec_dir(tmp_path)
    h.make_png(tmp_path / "outside.png")
    assert _prep(ts, {"media": [{"type": "image", "src": "../outside.png"}]}, d) == []


def test_absolute_path_chosen_by_the_caller_is_accepted(ts, tmp_path):
    d = _spec_dir(tmp_path)
    abs_png = h.make_png(tmp_path / "elsewhere" / "x.png")
    assert [m["kind"] for m in _prep(ts, {"media": [{"type": "image", "src": abs_png}]}, d)] == ["image"]


def test_symlink_media_is_refused(ts, tmp_path, monkeypatch):
    d = _spec_dir(tmp_path)
    (d / "real.png").write_bytes(h.PNG)
    link = os.path.normpath(str(d / "link.png"))
    (d / "link.png").write_bytes(h.PNG)       # tồn tại thật; chỉ "là symlink" theo hệ điều hành
    monkeypatch.setattr(os.path, "islink", lambda p: os.path.normpath(p) == link)
    assert _prep(ts, {"media": [{"type": "image", "src": "link.png"}]}, d) == []
    assert _prep(ts, {"media": [{"type": "image", "src": "real.png"}]}, d) != []


def test_real_symlink_is_refused_when_the_os_allows_it(ts, tmp_path):
    d = _spec_dir(tmp_path)
    (d / "real.png").write_bytes(h.PNG)
    try:
        os.symlink(d / "real.png", d / "link.png")
    except (OSError, NotImplementedError):
        pytest.skip("máy không tạo được symlink (cần quyền)")
    assert _prep(ts, {"media": [{"type": "image", "src": "link.png"}]}, d) == []


def test_missing_file_is_still_skipped_quietly(ts, tmp_path):
    assert _prep(ts, {"media": [{"type": "image", "src": "none.png"}]}, _spec_dir(tmp_path)) == []


# ── media trỏ vào media/ → mã 2, nguồn còn nguyên ────────────────────────────────────────

def test_media_inside_project_media_dir_is_rejected_before_rmtree(ts, tmp_path):
    src = h.make_png(ts.proj / "media" / "mine.png")
    story = {"headline": "H", "sections": [{"title": "T", "media": [{"type": "image", "src": src}]}]}
    with pytest.raises(ContractError) as e:
        ts.make_long(story, str(tmp_path / "o.mp4"), h.MODEL, None, str(tmp_path))
    assert "media/" in str(e.value) and os.path.isfile(src)
    with pytest.raises(ContractError):
        ts.make_short(story, str(tmp_path / "o.mp4"), h.MODEL, None, str(tmp_path))
    assert os.path.isfile(src)


# ── RQ-003: nhiều ảnh mỗi phần ───────────────────────────────────────────────────────────

def _story(tmp_path, n, marked):
    media = [{"type": "image", "src": h.make_png(tmp_path / "in" / f"i{j}.png")} for j in range(n)]
    sec = {"title": "T", "lead": "Một. Hai.", "narration": "Một. Hai.", "media": media}
    if marked:
        sec[USER_IMAGE_KEY] = True
    return {"headline": "H", "sections": [sec]}


def test_short_shows_all_images_of_a_marked_section(ts, tmp_path):
    ts.make_short(_story(tmp_path, 3, True), str(tmp_path / "o.mp4"), h.MODEL, None, str(tmp_path))
    html = ts.cap[-1]
    pos = [html.index(f'id="Ssec-1-im{j}" src="media/S1_{j}.png"') for j in range(3)]
    assert pos == sorted(pos)


def test_short_single_image_html_is_the_old_one(ts, tmp_path):
    ts.make_short(_story(tmp_path, 1, False), str(tmp_path / "o.mp4"), h.MODEL, None, str(tmp_path))
    html = ts.cap[-1]
    assert '<div class="heroimg"><img id="Ssec-1-im" src="media/S1_0.png"></div>' in html
    assert 'Ssec-1-im0' not in html


def test_short_unmarked_section_keeps_only_the_first_image(ts, tmp_path):
    ts.make_short(_story(tmp_path, 3, False), str(tmp_path / "o.mp4"), h.MODEL, None, str(tmp_path))
    assert 'id="Ssec-1-im"' in ts.cap[-1] and 'S1_1.png' not in ts.cap[-1]


def test_long_shows_all_images_of_a_marked_section(ts, tmp_path, monkeypatch):
    monkeypatch.setattr(ts, "_synth_section_beats", lambda m, sec, p, sr: ([0] * 24000, 1.0, []))
    ts.make_long(_story(tmp_path, 3, True), str(tmp_path / "o.mp4"), h.MODEL, None, str(tmp_path))
    html = ts.cap[-1]
    assert all(f'src="media/L1_{j}.png"' in html for j in range(3))


def test_long_unmarked_section_keeps_only_the_first_image(ts, tmp_path, monkeypatch):
    monkeypatch.setattr(ts, "_synth_section_beats", lambda m, sec, p, sr: ([0] * 24000, 1.0, []))
    ts.make_long(_story(tmp_path, 3, False), str(tmp_path / "o.mp4"), h.MODEL, None, str(tmp_path))
    assert 'src="media/L1_0.png"' in ts.cap[-1] and 'L1_1.png' not in ts.cap[-1]
