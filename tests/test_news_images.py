"""Ảnh của template `news`: hồi quy HTML cảnh MỘT ảnh, nhiều ảnh mỗi cảnh, từ chối ảnh trỏ vào `img/`,
trần kích thước và symlink (RQ-003, RQ-005, RQ-006).

Mã dựng là mã thật; chỉ giọng/ASR/mạng/HyperFrames bị thay (`news_harness.py`). Bản ghi vàng ở
`tests/fixtures/news_images/` là HTML do mã TRƯỚC khi hỗ trợ nhiều ảnh dựng ra — chạy với
`NEWS_GOLDEN_WRITE=1` chỉ khi cố ý đổi bố cục.
"""
import os

import pytest

import news_harness as h
from video_studio.contract import ContractError
from video_studio.spec import USER_IMAGE_KEY

GOLD = os.path.join(os.path.dirname(__file__), "fixtures", "news_images")


def _golden(name, html):
    path = os.path.join(GOLD, name + ".html")
    if os.environ.get("NEWS_GOLDEN_WRITE"):
        os.makedirs(GOLD, exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(html)
    with open(path, encoding="utf-8", newline="") as f:
        assert html == f.read(), f"HTML cảnh đổi so với bản ghi vàng {name}"


def _segs(tmp_path, n_imgs, marked, diag=False):
    imgs = [h.make_png(tmp_path / "src" / f"p{i}.png") for i in range(n_imgs)]
    seg = {"headline": "Tin A", "narration": "Câu một. Câu hai.", "images": imgs}
    if marked:
        seg[USER_IMAGE_KEY] = True
    if diag:
        seg["diagram"] = {"type": "stats", "items": [{"v": "1", "l": "x"}, {"v": "2", "l": "y"}]}
    return [seg]


@pytest.fixture
def build(news, monkeypatch, tmp_path):
    proj = tmp_path / "proj"
    cap = h.install(monkeypatch, news, proj)

    def run(segments, short=False):
        cap.clear()
        h.weekly(news, segments, tmp_path / "out.mp4", short=short)
        return cap[-1]
    run.proj = proj
    return run


# ── hồi quy: một ảnh -> HTML không đổi ────────────────────────────────────────────────────

@pytest.mark.parametrize("short", [False, True], ids=["long", "short"])
@pytest.mark.parametrize("n_imgs,marked,diag", [(1, True, False), (1, False, False), (2, False, False),
                                                (1, True, True)],
                         ids=["one-marked", "one-plain", "two-unmarked-first-only", "one-with-diagram"])
def test_single_image_scene_html_is_unchanged(build, tmp_path, short, n_imgs, marked, diag):
    if short and diag:
        pytest.skip("short không có SmartArt trong panel ảnh")
    html = build(_segs(tmp_path, n_imgs, marked, diag), short=short)
    _golden(f"{'short' if short else 'long'}-{n_imgs}img-{'m' if marked else 'u'}{'-d' if diag else ''}", html)


# ── nhiều ảnh: hiện đủ, theo thứ tự ───────────────────────────────────────────────────────

def test_long_shows_every_listed_image_in_order(build, tmp_path):
    html = build(_segs(tmp_path, 3, True))
    pos = [html.index(f'id="seg-1-im{j}" src="img/s1_{j}.png"') for j in range(3)]
    assert pos == sorted(pos)
    # ảnh sau chỉ hiện sau khi ảnh trước tắt
    assert html.index('m.to("#seg-1-im0",{opacity:0') < html.index('m.to("#seg-1-im1",{opacity:1')


def test_short_shows_every_listed_image_in_order(build, tmp_path):
    html = build(_segs(tmp_path, 3, True), short=True)
    assert html.count('<div class="heroimg">') == 1
    pos = [html.index(f'id="seg-1-im{j}" src="img/s1_{j}.png"') for j in range(3)]
    assert pos == sorted(pos)
    assert 'id="seg-1-im" ' not in html
    assert html.index('m.to("#seg-1-im1",{opacity:1') > html.index('m.to("#seg-1-im0",{opacity:0')


def test_unmarked_scene_keeps_showing_only_the_first_image(build, tmp_path):
    html = build(_segs(tmp_path, 3, False))
    assert 'id="seg-1-im0"' in html and 'id="seg-1-im1"' not in html


# ── RQ-005: images.json trỏ vào img/ ──────────────────────────────────────────────────────

@pytest.mark.parametrize("short", [False, True], ids=["long", "short"])
def test_image_inside_project_img_dir_is_rejected_and_source_survives(build, news, tmp_path, short):
    src = h.make_png(build.proj / "img" / "mine.png")
    seg = {"headline": "A", "narration": "x.", "images": [src], USER_IMAGE_KEY: True}
    with pytest.raises(ContractError) as e:
        h.weekly(news, [seg], tmp_path / "o.mp4", short=short)
    assert "img/" in str(e.value) and e.value.code == 2
    assert os.path.isfile(src), "file nguồn của người dùng phải còn nguyên"


def test_rejection_happens_before_any_rmtree_even_with_other_files(build, news, tmp_path):
    keep = h.make_png(build.proj / "img" / "other.png")
    src = h.make_png(build.proj / "img" / "sub" / "mine.png")
    seg = {"headline": "A", "narration": "x.", "images": [src]}
    with pytest.raises(ContractError):
        h.weekly(news, [seg], tmp_path / "o.mp4")
    assert os.path.isfile(src) and os.path.isfile(keep)


def test_image_outside_img_dir_is_fine(build, tmp_path):
    html = build(_segs(tmp_path, 1, True))
    assert "img/s1_0.png" in html


# ── RQ-006: trần kích thước và symlink ────────────────────────────────────────────────────

def test_oversize_local_image_warns_but_is_copied(news, tmp_path, capsys, monkeypatch):
    monkeypatch.setattr(news, "IMAGE_MAX_BYTES", 6000)
    big = tmp_path / "big.png"
    big.write_bytes(h.PNG + b"\0" * 2000)
    out = news._download_images([str(big)], str(tmp_path / "d"), 1)
    assert out == ["img/s1_0.png"] and "[warn]" in capsys.readouterr().out
    assert (tmp_path / "d" / "s1_0.png").is_file()


def test_small_local_image_does_not_warn(news, tmp_path, capsys):
    small = h.make_png(tmp_path / "s.png")
    assert news._download_images([small], str(tmp_path / "d"), 1) == ["img/s1_0.png"]
    assert "[warn]" not in capsys.readouterr().out


def test_symlink_image_is_refused(news, tmp_path, capsys, monkeypatch):
    real = h.make_png(tmp_path / "real.png")
    link = str(tmp_path / "link.png")
    monkeypatch.setattr(os.path, "islink", lambda p: os.path.normpath(p) == os.path.normpath(link))
    out = news._download_images([link], str(tmp_path / "d"), 1)
    assert out == [] and "symlink" in capsys.readouterr().out
    assert os.path.isfile(real) and not os.listdir(tmp_path / "d")


def test_real_symlink_is_refused_when_the_os_allows_it(news, tmp_path, capsys):
    real = h.make_png(tmp_path / "real.png")
    link = tmp_path / "link.png"
    try:
        os.symlink(real, link)
    except (OSError, NotImplementedError):
        pytest.skip("máy không tạo được symlink (cần quyền)")
    assert news._download_images([str(link)], str(tmp_path / "d"), 1) == []
    assert "symlink" in capsys.readouterr().out


def test_url_branch_keeps_the_12_megabyte_read_cap(news, tmp_path, monkeypatch):
    seen = {}

    class R:
        headers = {"Content-Type": "image/png"}

        def read(self, n):
            seen["n"] = n
            return h.PNG

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    monkeypatch.setattr(news.urllib.request, "urlopen", lambda req, timeout=0: R())
    assert news._download_images(["https://img.example.invalid/x.png"], str(tmp_path / "d"), 1) == ["img/s1_0.png"]
    assert seen["n"] == 12_000_000
