"""Cổng cho template `news` sau khi chưng cất: thương hiệu fail-closed, đường dẫn từ trạm.

Template cần `numpy`, `soundfile` và repo giọng — CI cài lõi thì không có thứ nào. Ở đây cả ba
được thay bằng module GIẢ trước khi import: cái đang kiểm là LUẬT của template (brand bắt buộc,
bảng phát âm, project lấy từ trạm), không phải chất lượng âm thanh.
"""
import os
import sys
import types

import pytest

from video_studio import contract, projects
from video_studio.contract import ContractError, StationMissing


def _fake(name, **attrs):
    m = types.ModuleType(name)
    for k, v in attrs.items():
        setattr(m, k, v)
    return m


@pytest.fixture
def news(monkeypatch):
    """Import `templates.news.news_video` với numpy / soundfile / voice_studio giả."""
    vs = _fake("voice_studio")
    vs.__path__ = []
    mods = {
        "numpy": _fake("numpy", float32="f4", zeros=lambda *a, **k: [],
                       concatenate=lambda *a, **k: [], asarray=lambda a, **k: a),
        "soundfile": _fake("soundfile", write=lambda *a, **k: None),
        "voice_studio": vs,
        "voice_studio.engine": _fake("voice_studio.engine"),
        "voice_studio.profiles": _fake("voice_studio.profiles"),
        "voice_studio.av": _fake("voice_studio.av"),
    }
    vs.engine, vs.profiles, vs.av = (mods["voice_studio.engine"], mods["voice_studio.profiles"],
                                     mods["voice_studio.av"])
    for name, mod in mods.items():
        monkeypatch.setitem(sys.modules, name, mod)
    for name in list(sys.modules):
        if name.startswith("video_studio.templates"):
            monkeypatch.delitem(sys.modules, name, raising=False)
    import importlib
    return importlib.import_module("video_studio.templates.news.news_video")


MIN = {"a": "Tin", "b": "Ngày", "site": "vi-du.example"}


# ── thương hiệu: không có mặc định nào mang danh tính ───────────────────────────────────

@pytest.mark.parametrize("brand", [None, {}, {"a": "Tin"}, {"a": "Tin", "b": "Ngày"},
                                   {"a": "", "b": "B", "site": "s"}])
def test_brand_is_mandatory(news, brand):
    with pytest.raises(ContractError) as e:
        news.resolve_brand(brand)
    assert e.value.code == contract.CONTRACT_ERROR


def test_brand_defaults_are_derived_from_the_given_name(news):
    b = news.resolve_brand(MIN)
    assert b["welcome"].endswith("Tin Ngày") and "Tin Ngày" in b["tagline"]
    assert b["site"] == "vi-du.example"


def test_brand_defaults_carry_no_name_of_their_own(news):
    """BRAND_DEFAULTS chỉ được chứa cách diễn đạt — không tên, không nơi chốn."""
    assert not ({"a", "b", "site"} & set(news.BRAND_DEFAULTS))


# ── bảng phát âm thay cho một tên miền nằm cứng ─────────────────────────────────────────

def test_pronounce_table_comes_from_the_brand(news):
    news.resolve_brand(MIN)
    assert news._tts_normalize("ghé vi-du.example nhé") == "ghé vi-du.example nhé"
    news.resolve_brand({**MIN, "pronounce": {r"vi-du\.example": "ví dụ chấm ví dụ"}})
    assert news._tts_normalize("ghé vi-du.example nhé") == "ghé ví dụ chấm ví dụ nhé"


def test_week_normalisation_survives(news):
    news.resolve_brand(MIN)
    assert news._tts_normalize("bản tin W24") == "bản tin tuần 24"


def test_resolving_a_new_brand_clears_the_previous_table(news):
    news.resolve_brand({**MIN, "pronounce": {"abc": "a bê xê"}})
    news.resolve_brand(MIN)
    assert news._tts_normalize("abc") == "abc"


# ── project lấy từ trạm, không từ một ổ đĩa cụ thể ──────────────────────────────────────

def test_template_holds_no_machine_path(news):
    src = open(news.__file__, encoding="utf-8").read()
    for token in ("\\.video", "Program Files", 'environ.get("LOCALAPPDATA")', "Gyan.FFmpeg",
                  "OMNIVOICE_DIR", "mcp_server", "voice_profiles"):
        assert token not in src, token


def test_project_dir_follows_the_station(news, tmp_path, monkeypatch):
    st = tmp_path / "tram"
    (st / "demo").mkdir(parents=True)
    for n in projects.CONFIG_FILES:
        (st / "demo" / n).write_text("{}", encoding="utf-8")
    monkeypatch.setenv("VIDEO_STATION", str(st))
    p = news._proj()
    assert p == str(st / "projects" / "news")
    assert os.path.isfile(os.path.join(p, "hyperframes.json"))


def test_missing_station_is_station_missing(news, tmp_path, monkeypatch):
    monkeypatch.setenv("VIDEO_STATION", str(tmp_path / "chua-co"))
    with pytest.raises(StationMissing) as e:
        news._proj()
    assert e.value.code == contract.STATION_MISSING
    # Ghim ĐÚNG lý do: "chưa có trạm", không phải "project thiếu cấu hình" — hai lỗi khác
    # nhau dẫn người dùng tới hai việc khác nhau.
    assert "chưa có trạm video ở" in str(e.value) and "video-studio init" in str(e.value)


def test_filler_dir_moved_into_the_project(news, tmp_path, monkeypatch):
    monkeypatch.setenv("VIDEO_STATION", str(tmp_path / "tram"))
    assert news._filler_dir().endswith(os.path.join("projects", "news", "assets", "fillers"))


# ── seed chỉ chép file CÒN THIẾU, không đè bản người dùng đã sửa ────────────────────────

def test_ensure_never_overwrites_an_existing_config(tmp_path, monkeypatch):
    st = tmp_path / "tram"
    (st / "demo").mkdir(parents=True)
    for n in projects.CONFIG_FILES:
        (st / "demo" / n).write_text('{"seed": true}', encoding="utf-8")
    proj = st / "projects" / "news"
    proj.mkdir(parents=True)
    (proj / "hyperframes.json").write_text('{"cua-toi": true}', encoding="utf-8")
    monkeypatch.setenv("VIDEO_STATION", str(st))
    projects.ensure("news")
    assert (proj / "hyperframes.json").read_text(encoding="utf-8") == '{"cua-toi": true}'
    assert (proj / "meta.json").read_text(encoding="utf-8") == '{"seed": true}'


@pytest.mark.parametrize("name", ["", "..", "a/b", "a\\b", "/abs"])
def test_project_name_must_be_a_single_folder(tmp_path, monkeypatch, name):
    monkeypatch.setenv("VIDEO_STATION", str(tmp_path))
    with pytest.raises(ContractError):
        projects.project_dir(name)


# ── tên file ra phải là TÊN, không phải đường dẫn ───────────────────────────────────────

@pytest.fixture
def tpl(news):
    """Gói `templates.news` (đã có module giả nhờ fixture `news`)."""
    import importlib
    return importlib.import_module("video_studio.templates.news")


@pytest.mark.parametrize("bad", ["18/09/2026", r"18\09\2026", "/tmp/x", r"C:\out\x",
                                 "../../thoat"])
def test_a_date_with_a_separator_is_code_2_not_a_surprise_folder(tpl, bad):
    """`date` dạng dd/mm/yyyy của sidecar cũ từng lặng lẽ đẻ `<out>/18/09/` — nay là mã 2."""
    with pytest.raises(ContractError) as e:
        tpl._date({"date": bad})
    assert "display_date" in str(e.value)


@pytest.mark.parametrize("good", ["2026-09-18", "deep-dive", "2026-W38"])
def test_a_plain_date_passes_through_unchanged(tpl, good):
    assert tpl._date({"date": good}) == good


def test_an_explicit_output_name_may_not_escape_out_dir(tpl):
    with pytest.raises(ContractError):
        tpl.out_name({"outputs": {"long": "sub/dir/a.mp4"}}, "long", "mac-dinh.mp4")
    assert tpl.out_name({"outputs": {"long": "a.mp4"}}, "long", "mac-dinh.mp4") == "a.mp4"
    assert tpl.out_name({}, "long", "mac-dinh.mp4") == "mac-dinh.mp4"
