"""Cổng cho template `news` sau khi chưng cất: thương hiệu fail-closed, đường dẫn từ trạm.

Template cần `numpy`, `soundfile` và repo giọng — CI cài lõi thì không có thứ nào. Ở đây cả ba
được thay bằng module GIẢ trước khi import: cái đang kiểm là LUẬT của template (brand bắt buộc,
bảng phát âm, project lấy từ trạm), không phải chất lượng âm thanh.
"""
import os

import pytest

from video_studio import contract, projects
from video_studio.contract import ContractError, StationMissing


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


def test_generic_pronunciation_respects_token_boundaries(news):
    news.resolve_brand({**MIN, "pronounce": {r"\bXZ\b": "X Z"}})
    assert news._tts_normalize("AXZ XZ2 XZ") == "AXZ XZ2 X Z"


def test_resolving_a_new_brand_clears_the_previous_table(news):
    news.resolve_brand({**MIN, "pronounce": {"abc": "a bê xê"}})
    news.resolve_brand(MIN)
    assert news._tts_normalize("abc") == "abc"


def test_authored_caption_uses_span_of_multiword_pronunciation(news, monkeypatch):
    news.resolve_brand({**MIN, "pronounce": {r"\bXZ\b": "X Z"}})
    asr = [("before", 1.0, 1.2), ("X", 2.3, 2.5), ("Z", 2.6, 2.9),
           ("after", 3.0, 3.2)]
    monkeypatch.setattr(news, "_asr_words", lambda audio, sr: asr)

    words = news._words_from_text([0] * 4000, 1000, "before XZ after")

    assert [word for word, _, _ in words] == ["before", "XZ", "after"]
    assert words == [("before", 1.0, 1.2), ("XZ", 2.3, 2.9), ("after", 3.0, 3.2)]


def test_shared_pronunciation_span_can_overlap_authored_tokens(news, monkeypatch):
    news.resolve_brand({**MIN, "pronounce": {r"\bXZ YZ\b": "term"}})
    monkeypatch.setattr(news, "_asr_words", lambda audio, sr: [("term", 2.0, 2.6)])

    words = news._words_from_text([0] * 4000, 1000, "XZ YZ")

    assert words == [("XZ", 2.0, 2.6), ("YZ", 2.0, 2.6)]


def test_partial_normalized_match_falls_back_to_legacy_interpolation(news, monkeypatch):
    news.resolve_brand({**MIN, "pronounce": {r"\bXZ\b": "X Z"}})
    asr = [("before", 1.0, 1.2), ("X", 2.3, 2.5), ("after", 3.0, 3.2)]
    monkeypatch.setattr(news, "_asr_words", lambda audio, sr: asr)

    words = news._words_from_text([0] * 4000, 1000, "before XZ after")

    assert words[1] == ("XZ", 1.2, 3.0)


@pytest.mark.parametrize("spoken", ["XZ X", "X XZ"])
def test_normalized_and_authored_matches_do_not_reuse_asr_words(news, monkeypatch, spoken):
    news.resolve_brand({**MIN, "pronounce": {r"\bXZ\b": "X Z"}})
    monkeypatch.setattr(news, "_asr_words", lambda audio, sr: [("X", 1.0, 1.2),
                                                                   ("Z", 1.3, 1.5)])

    words = news._words_from_text([0] * 4000, 1000, spoken)

    assert [word for word, _, _ in words] == spoken.split()
    assert words[0][2] <= words[1][1]


def test_number_split_keeps_authored_display_and_legacy_fallback(news, monkeypatch):
    news.resolve_brand(MIN)
    asr = [("up", 1.0, 1.2), ("12", 1.3, 1.5), (".5", 1.5, 1.8),
           ("%", 1.8, 2.0), ("today", 2.1, 2.4)]
    monkeypatch.setattr(news, "_asr_words", lambda audio, sr: asr)

    words = news._words_from_text([0] * 3000, 1000, "up 12.5% today")

    assert [word for word, _, _ in words] == ["up", "12.5%", "today"]
    # 12.5% remains outside the normalization table. Preserve its established gap
    # interpolation until a separate number-alignment requirement is demonstrated.
    assert words[1] == ("12.5%", 1.2, 2.1)


def test_existing_week_normalization_maps_back_to_one_authored_token(news, monkeypatch):
    news.resolve_brand(MIN)
    monkeypatch.setattr(news, "_asr_words", lambda audio, sr: [("tuần", 2.1, 2.4),
                                                                   ("24", 2.45, 2.8)])

    words = news._words_from_text([0] * 4000, 1000, "W24")

    assert words == [("W24", 2.1, 2.8)]


@pytest.mark.parametrize("spoken,number", [("tuần W24", "24"), ("tuan w02", "02")])
def test_week_prefix_keeps_its_own_asr_span(news, monkeypatch, spoken, number):
    news.resolve_brand(MIN)
    monkeypatch.setattr(news, "_asr_words", lambda audio, sr: [("tuần", 1.0, 1.2),
                                                                   (number, 2.0, 2.2)])

    words = news._words_from_text([0] * 4000, 1000, spoken)

    assert words == [(spoken.split()[0], 1.0, 1.2), (spoken.split()[1], 2.0, 2.2)]


def test_empty_pronunciation_and_empty_asr_keep_authored_text(news, monkeypatch):
    news.resolve_brand({**MIN, "pronounce": {r"\bXZ\b": ""}})
    monkeypatch.setattr(news, "_asr_words", lambda audio, sr: [("before", 1.0, 1.2),
                                                                   ("after", 2.0, 2.2)])

    words = news._words_from_text([0] * 3000, 1000, "before XZ after")

    assert [word for word, _, _ in words] == ["before", "XZ", "after"]
    assert words[1] == ("XZ", 1.2, 2.0)

    monkeypatch.setattr(news, "_asr_words", lambda audio, sr: [])
    words = news._words_from_text([0] * 3000, 1000, "before XZ after")
    assert [word for word, _, _ in words] == ["before", "XZ", "after"]
    assert words[0][1] == 0.0 and words[-1][2] == 3.0


# ── project lấy từ trạm, không từ một ổ đĩa cụ thể ──────────────────────────────────────

def test_template_holds_no_machine_path(news):
    src = open(news.__file__, encoding="utf-8").read()
    for token in ("\\." + "video", "Program Files",       # ghép đôi: file này cũng không được nêu tên nó 'environ.get("LOCALAPPDATA")', "Gyan.FFmpeg",
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


# ── thiếu ffmpeg là "cài thêm" (mã 3), không phải "thử lại" (mã 1) ──────────────────────

def test_a_machine_without_ffmpeg_gets_code_3_not_a_retryable_error(news, monkeypatch):
    """`_ffbin` trả chuỗi trần `"ffprobe"` thì `subprocess.run` ném `FileNotFoundError`, mà
    `contract.classify` xếp nó vào ENGINE_ERROR = mã 1 = "thử lại có thể qua". Máy chưa có
    ffmpeg thì thử lại bao nhiêu lần cũng thế — và `subprocess.run` lại nằm NGOÀI `try` nên
    không ai chặn được. `edit/_ff.probe_exe()` đã làm đúng bằng `StationMissing`; chỗ này
    phải giống.
    """
    import importlib
    ts = importlib.import_module("video_studio.templates.news.top_story_video")
    monkeypatch.setattr(ts._env, "ffprobe_exe", lambda: None)
    monkeypatch.setattr(ts._env, "ffmpeg_exe", lambda: None)
    for name in ("ffprobe", "ffmpeg"):
        with pytest.raises(StationMissing) as e:
            ts._ffbin(name)
        assert e.value.code == 3
        assert name in str(e.value) and "FFMPEG_DIR" in str(e.value)


def test_ffbin_returns_the_resolved_path_when_the_tool_is_there(news, monkeypatch):
    import importlib
    ts = importlib.import_module("video_studio.templates.news.top_story_video")
    monkeypatch.setattr(ts._env, "ffprobe_exe", lambda: "/fake/bin/ffprobe")
    assert ts._ffbin("ffprobe") == "/fake/bin/ffprobe"


def test_top_story_short_uses_shared_normalized_caption_mapping(news, monkeypatch, tmp_path):
    import importlib
    nv = news
    ts = importlib.import_module("video_studio.templates.news.top_story_video")
    nv.resolve_brand({**MIN, "pronounce": {r"\bXZ\b": "X Z"}})
    asr = [("X", 2.3, 2.5), ("Z", 2.6, 2.9)]
    monkeypatch.setattr(nv, "_asr_words", lambda audio, sr: asr)
    monkeypatch.setattr(nv, "asr_drift_warn", lambda *args, **kwargs: None)
    monkeypatch.setattr(nv, "_synth_long", lambda model, text, prompt: [0] * 4000)
    monkeypatch.setattr(nv, "_local_filler", lambda *args, **kwargs: None)
    monkeypatch.setattr(nv, "_broll_image", lambda *args, **kwargs: False)
    monkeypatch.setattr(ts, "_proj", lambda: str(tmp_path))
    captured = {}
    def capture_build(story, blocks, *args):
        captured["blocks"] = blocks
        return "html"
    monkeypatch.setattr(ts, "_build", capture_build)
    monkeypatch.setattr(ts, "_voice_track", lambda *args: [])
    monkeypatch.setattr(ts, "_render", lambda *args, **kwargs: "rendered")

    result = ts.make_short(
        {"headline": "XZ", "intro_short": "XZ", "sections": [
            {"title": "XZ", "narration_short": "XZ", "media": [{"type": "image", "src": "fixture.png"}]}],
            "outro_short": "XZ"},
        "out.mp4", type("Model", (), {"sampling_rate": 1000})(), None, str(tmp_path))

    assert result == "rendered"
    section = next(block for block in captured["blocks"] if block["kind"] == "sec")
    assert section["caps_words"] == [("XZ", 2.3, 2.9)]
