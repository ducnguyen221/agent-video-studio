"""`video-studio edit` — bộ chỉnh footage chưng cất từ video-use.

Không có ffmpeg thật, không có model ASR, không có mạng: `_ff.run` và `_ff._probe_raw` là hàm
giả, và cái được kiểm là **lệnh ffmpeg ĐƯỢC DỰNG RA** — vì mọi bài học của bộ này nằm ở đúng
thứ tự các cờ (phụ đề sau cùng, nối bằng -c copy, giữ fps nguồn, chọn đúng track tiếng).
"""
import json
import os

import pytest

from conftest import last_json
from video_studio import edit
from video_studio.contract import ContractError, StationMissing
from video_studio.edit import _ff, edl as edl_mod, grade, pack
from video_studio.edit import render as edit_render


# ── dụng cụ giả ─────────────────────────────────────────────────────────────────────────

@pytest.fixture
def ff(monkeypatch, tmp_path):
    """ffmpeg/ffprobe "có mặt"; mọi lần gọi được ghi lại thay vì chạy."""
    calls = []

    def fake_run(args, quiet=True, timeout=None):
        calls.append(list(args))
        # ffmpeg thật tạo ra file ở tham số cuối — bước sau còn kiểm sự tồn tại của nó
        last = str(args[-1])
        if last.endswith((".mp4", ".srt")):
            os.makedirs(os.path.dirname(os.path.abspath(last)) or ".", exist_ok=True)
            with open(last, "w", encoding="utf-8") as f:
                f.write("x")
        return ""

    monkeypatch.setattr(_ff, "run", fake_run)
    monkeypatch.setattr(_ff, "exe", lambda: "ffmpeg")
    monkeypatch.setattr(_ff, "probe_exe", lambda: "ffprobe")
    monkeypatch.setenv("FFMPEG_DIR", str(_fake_bin(tmp_path)))
    return calls


def _fake_bin(tmp_path):
    d = tmp_path / "ffbin"
    d.mkdir(exist_ok=True)
    for base in ("ffmpeg", "ffprobe"):
        p = d / (base + ".cmd" if os.name == "nt" else base)
        p.write_text("", encoding="utf-8")
        if os.name != "nt":
            p.chmod(0o755)
    return d


def _streams(width=1920, height=1080, fps="30000/1001", rotation=None, transfer="bt709",
             audio=((2, 0),)):
    v = {"codec_type": "video", "width": width, "height": height, "avg_frame_rate": fps,
         "color_transfer": transfer}
    if rotation is not None:
        v["side_data_list"] = [{"rotation": rotation}]
    streams = [v] + [{"codec_type": "audio", "channels": ch, "index": idx}
                     for ch, idx in audio]
    return {"streams": streams, "format": {"duration": "60.0"}}


@pytest.fixture
def probe(monkeypatch):
    """Cho mỗi file nguồn một mô tả; mặc định 1080p ngang 29.97 fps, một track stereo."""
    table = {}
    monkeypatch.setattr(_ff, "_probe_raw", lambda p: table.get(os.path.basename(str(p)),
                                                               _streams()))
    return table


# ── EDL: sai thì đỏ TRƯỚC khi chạm ffmpeg ───────────────────────────────────────────────

def _edl(**over):
    base = {"sources": {"a": "a.mp4"},
            "ranges": [{"source": "a", "start": 1.0, "end": 3.0}]}
    base.update(over)
    return base


@pytest.mark.parametrize("data,phrase", [
    ({}, "sources"),
    ({"sources": {}}, "sources"),
    ({"sources": {"a": "a.mp4"}}, "ranges"),
    (_edl(ranges=[{"source": "b", "start": 0, "end": 1}]), "không có trong"),
    (_edl(ranges=[{"source": "a", "start": 5, "end": 5}]), "lớn hơn"),
    (_edl(ranges=[{"source": "a", "start": -1, "end": 2}]), "âm"),
    (_edl(ranges=[{"source": "a", "start": "x", "end": 2}]), "phải là số"),
    (_edl(ranges=[{"source": "a", "start": 0, "end": 2, "grade_": "x"}]), "khoá lạ"),
    (_edl(overlays=[{"file": "o.mov"}]), "start_in_output"),
    (_edl(overlays=[{"file": "", "start_in_output": 0, "duration": 1}]), "file"),
    (_edl(subtitles=5), "subtitles"),
])
def test_bad_edl_is_contract_error_naming_the_place(data, phrase):
    with pytest.raises(ContractError) as e:
        edl_mod.validate(data)
    assert phrase in str(e.value)


def test_good_edl_is_normalised():
    data = edl_mod.validate(_edl(ranges=[{"source": "a", "start": "1", "end": "4.5"}]))
    assert data["ranges"][0]["start"] == 1.0 and data["ranges"][0]["end"] == 4.5
    assert data["overlays"] == [] and data["grade"] == "auto"
    assert edl_mod.total_duration(data) == 3.5


def test_relative_paths_resolve_against_the_edl_not_the_cwd(tmp_path):
    got = edl_mod.resolve("clips/a.mp4", str(tmp_path))
    assert got == os.path.join(str(tmp_path), "clips", "a.mp4")


def test_load_reports_broken_json(tmp_path):
    p = tmp_path / "edl.json"
    p.write_text("{nope", encoding="utf-8")
    with pytest.raises(ContractError) as e:
        edl_mod.load(str(p))
    assert "JSON hỏng" in str(e.value)


# ── chỉnh màu ───────────────────────────────────────────────────────────────────────────

def test_grade_resolves_presets_auto_and_raw_filters():
    assert grade.resolve_filter("auto") == grade.AUTO
    assert grade.resolve_filter("subtle") == grade.PRESETS["subtle"]
    assert grade.resolve_filter("eq=contrast=1.2") == "eq=contrast=1.2"
    assert grade.resolve_filter("") == ""
    with pytest.raises(KeyError):
        grade.resolve_filter("khong_co_preset")


@pytest.mark.parametrize("stats,expect", [
    ({"y_mean": 0.33, "y_range": 0.72, "sat_mean": 0.25}, "gamma"),      # tối → kéo sáng
    ({"y_mean": 0.48, "y_range": 0.52, "sat_mean": 0.25}, "contrast"),   # bẹt → nâng tương phản
    ({"y_mean": 0.48, "y_range": 0.72, "sat_mean": 0.10}, "saturation"),  # nhạt → thêm màu
])
def test_auto_grade_fixes_what_it_measures(stats, expect):
    assert expect in grade.auto_filter(stats)


def test_auto_grade_never_moves_more_than_eight_percent():
    for y in (0.0, 0.2, 0.5, 0.9, 1.0):
        for r in (0.1, 0.5, 0.9):
            for s in (0.0, 0.2, 0.5):
                flt = grade.auto_filter({"y_mean": y, "y_range": r, "sat_mean": s})
                for part in flt.replace("eq=", "").split(":"):
                    if "=" in part:
                        assert 0.92 <= float(part.split("=")[1]) <= 1.10, flt


def test_signalstats_are_normalised_by_bit_depth():
    """Nguồn 10 bit: quên chia theo YBITDEPTH thì clip sáng bình thường bị coi là tối đen."""
    text = ("lavfi.signalstats.YBITDEPTH=10\nlavfi.signalstats.YAVG=512\n"
            "lavfi.signalstats.YMIN=0\nlavfi.signalstats.YMAX=1023\n"
            "lavfi.signalstats.SATAVG=256\n")
    stats = grade._parse_stats(text)
    assert 0.49 < stats["y_mean"] < 0.51
    assert stats["y_range"] > 0.99
    assert grade.auto_filter(stats).count("gamma") == 0


def test_unreadable_stats_fall_back_to_neutral():
    assert grade._parse_stats("rac ra ri") == grade.NEUTRAL_STATS


# ── gom cụm ─────────────────────────────────────────────────────────────────────────────

def _w(text, start, end, **kw):
    return {"type": "word", "text": text, "start": start, "end": end, **kw}


def test_phrases_break_on_long_silence():
    words = [_w("một", 0.0, 0.3), _w("hai", 0.3, 0.6),
             _w("ba", 2.0, 2.3)]                       # cách 1,4 s
    phrases = pack.group_into_phrases(words)
    assert [p["text"] for p in phrases] == ["một hai", "ba"]


def test_phrases_break_on_speaker_change():
    words = [_w("a", 0.0, 0.2, speaker_id="speaker_0"),
             _w("b", 0.2, 0.4, speaker_id="speaker_1")]
    assert len(pack.group_into_phrases(words)) == 2


def test_spacing_entries_carry_the_silence():
    words = [_w("a", 0.0, 0.2), {"type": "spacing", "start": 0.2, "end": 1.0}, _w("b", 1.0, 1.2)]
    assert len(pack.group_into_phrases(words)) == 2


def test_audio_events_are_kept_in_brackets():
    words = [_w("a", 0.0, 0.2), {"type": "audio_event", "text": "cười", "start": 0.2, "end": 0.5}]
    assert "(cười)" in pack.group_into_phrases(words)[0]["text"]


def test_packed_markdown_has_addressable_timestamps(tmp_path):
    tdir = tmp_path / "transcripts"
    tdir.mkdir()
    (tdir / "take1.json").write_text(json.dumps(
        {"words": [_w("xin", 1.0, 1.4), _w("chào", 1.4, 1.9)]}), encoding="utf-8")
    res = pack.pack_dir(str(tdir), str(tmp_path / "takes_packed.md"))
    text = open(res["path"], encoding="utf-8").read()
    assert "## take1" in text and "[001.00-001.90]" in text
    assert res["phrases"] == 1


def test_packed_markdown_is_utf8_even_on_a_cp1252_machine(tmp_path):
    """Bản gốc đọc/ghi theo locale — trên Windows đó là lỗi giải mã ngay từ file đầu tiên."""
    tdir = tmp_path / "transcripts"
    tdir.mkdir()
    (tdir / "a.json").write_text(json.dumps({"words": [_w("Đường", 0.0, 0.5)]},
                                            ensure_ascii=False), encoding="utf-8")
    res = pack.pack_dir(str(tdir), str(tmp_path / "p.md"))
    assert "Đường" in open(res["path"], encoding="utf-8").read()


# ── thăm dò nguồn ───────────────────────────────────────────────────────────────────────

def test_rotation_metadata_decides_portrait(probe):
    probe["dọc.mp4"] = _streams(width=1920, height=1080, rotation=90)
    p = _ff.probe("dọc.mp4")
    assert p.portrait is True, "quay dọc từ điện thoại khai 1920×1080 + rotation 90"
    assert _ff.probe("ngang.mp4").portrait is False


def test_audio_track_choice_skips_the_silent_one(probe):
    """`-map 0:a:N` đếm trong DANH SÁCH TRACK TIẾNG CỦA FILE: track câm vẫn chiếm một số thứ tự.

    Đếm trong danh sách đã lọc là cái bẫy — nó trỏ nhầm sang track khác, và video ra có tiếng
    nên không ai nghi ngờ gì cho tới khi nghe kỹ.
    """
    probe["hai-track.mp4"] = _streams(audio=((0, 1), (2, 2)))
    assert _ff.probe("hai-track.mp4").audio_map() == "0:a:1"
    probe["ba-track.mp4"] = _streams(audio=((1, 1), (0, 2), (2, 3)))
    assert _ff.probe("ba-track.mp4").audio_map() == "0:a:2"


@pytest.mark.parametrize("audio", [(), ((0, 1),), ((0, 1), (0, 2))])
def test_a_source_with_no_usable_audio_says_so(audio, probe):
    probe["cam.mp4"] = _streams(audio=audio)
    assert _ff.probe("cam.mp4").audio_map() is None


def test_fps_is_read_as_a_number(probe):
    assert abs(_ff.probe("a.mp4").fps - 29.97) < 0.01


# ── dựng: lệnh ffmpeg phải đúng thứ tự ──────────────────────────────────────────────────

def test_segment_keeps_source_fps_and_maps_the_right_audio(ff, probe, tmp_path):
    probe["a.mp4"] = _streams(fps="60/1", audio=((0, 1), (1, 2)))
    edit_render.extract_segment("a.mp4", 1.0, 2.0, str(tmp_path / "seg.mp4"))
    args = ff[0]
    assert args[args.index("-r") + 1] == "60"
    assert args[args.index("-map") + 1] == "0:v:0"
    assert "0:a:1" in args, "track 0 câm ⇒ phải lấy track 1, không phải 0:a:0"
    assert "afade=t=in" in " ".join(args), "thiếu vuốt tiếng 30 ms hai đầu"


def test_hdr_source_is_tone_mapped(ff, probe, tmp_path):
    probe["hdr.mp4"] = _streams(transfer="arib-std-b67")
    edit_render.extract_segment("hdr.mp4", 0, 1, str(tmp_path / "s.mp4"))
    vf = ff[0][ff[0].index("-vf") + 1]
    assert vf.startswith(edit_render.TONEMAP), "tone-map phải đứng TRƯỚC scale"


def test_portrait_source_is_scaled_by_height(ff, probe, tmp_path):
    probe["p.mp4"] = _streams(width=1080, height=1920)
    edit_render.extract_segment("p.mp4", 0, 1, str(tmp_path / "s.mp4"))
    assert "scale=-2:1920" in ff[0][ff[0].index("-vf") + 1]


def test_draft_quality_is_smaller_and_faster(ff, probe, tmp_path):
    edit_render.extract_segment("a.mp4", 0, 1, str(tmp_path / "s.mp4"), quality="draft")
    args = ff[0]
    assert "scale=1280:-2" in args[args.index("-vf") + 1]
    assert args[args.index("-crf") + 1] == "28"


def test_concat_is_lossless(ff, tmp_path):
    segs = []
    for n in ("a", "b"):
        p = tmp_path / f"{n}.mp4"
        p.write_text("x", encoding="utf-8")
        segs.append(str(p))
    edit_render.concat(segs, str(tmp_path / "base.mp4"), str(tmp_path))
    args = ff[-1]
    assert args[args.index("-c") + 1] == "copy"
    assert "concat" in args
    assert not (tmp_path / "_concat.txt").exists(), "file danh sách tạm phải được dọn"


def test_composite_puts_subtitles_last(ff, tmp_path):
    base = tmp_path / "base.mp4"
    base.write_text("x", encoding="utf-8")
    subs = tmp_path / "m.srt"
    subs.write_text("1\n", encoding="utf-8")
    overlay = tmp_path / "ov.mov"
    overlay.write_text("x", encoding="utf-8")
    edit_render.composite(str(base), [{"file": "ov.mov", "start_in_output": 2.0,
                                       "duration": 1.0}],
                          str(subs), str(tmp_path / "out.mp4"), str(tmp_path))
    graph = ff[-1][ff[-1].index("-filter_complex") + 1]
    assert graph.index("overlay=") < graph.index("subtitles="), "phụ đề phải ở BƯỚC CUỐI"
    assert "setpts=PTS-STARTPTS+2.0/TB" in graph, "overlay phải dịch PTS về mốc của video ra"
    assert "MarginV=90" in graph


def test_composite_without_anything_just_copies(ff, tmp_path):
    base = tmp_path / "base.mp4"
    base.write_text("x", encoding="utf-8")
    edit_render.composite(str(base), [], None, str(tmp_path / "o.mp4"), str(tmp_path))
    assert "-filter_complex" not in ff[-1] and "copy" in ff[-1]


def test_master_srt_uses_output_timeline(ff, tmp_path):
    work = tmp_path / "work"
    (work / "transcripts").mkdir(parents=True)
    (work / "transcripts" / "a.json").write_text(json.dumps(
        {"words": [_w("MỘT", 10.0, 10.4), _w("HAI", 10.4, 10.8)]}), encoding="utf-8")
    data = edl_mod.validate({"sources": {"a": "a.mp4"},
                             "ranges": [{"source": "a", "start": 5.0, "end": 8.0},
                                        {"source": "a", "start": 10.0, "end": 11.0}]})
    out = edit_render.build_master_srt(data, str(work), str(work / "master.srt"))
    text = open(out, encoding="utf-8").read()
    # đoạn 2 bắt đầu ở giây 3 của video ra (đoạn 1 dài 3 s) ⇒ từ ở 10.0 rơi vào 00:00:03,000
    assert "00:00:03,000 --> 00:00:03,800" in text
    assert "MỘT HAI" in text


def test_loudnorm_second_pass_uses_the_measurement(ff, tmp_path, monkeypatch):
    monkeypatch.setattr(edit_render, "_measure", lambda p: {
        "input_i": "-21.0", "input_tp": "-3.0", "input_lra": "5.0", "input_thresh": "-31.0",
        "target_offset": "0.5"})
    src = tmp_path / "a.mp4"
    src.write_text("x", encoding="utf-8")
    assert edit_render.loudnorm(str(src), str(tmp_path / "b.mp4")) is True
    flt = ff[-1][ff[-1].index("-af") + 1]
    assert "measured_I=-21.0" in flt and "linear=true" in flt and "I=-14.0" in flt


def test_loudnorm_falls_back_when_measurement_fails(ff, tmp_path, monkeypatch):
    monkeypatch.setattr(edit_render, "_measure", lambda p: None)
    src = tmp_path / "a.mp4"
    src.write_text("x", encoding="utf-8")
    assert edit_render.loudnorm(str(src), str(tmp_path / "b.mp4")) is False
    assert "measured_I" not in ff[-1][ff[-1].index("-af") + 1]


def test_render_edl_runs_the_four_steps_in_order(ff, probe, tmp_path):
    src = tmp_path / "a.mp4"
    src.write_text("x", encoding="utf-8")
    data = edl_mod.validate({"sources": {"a": "a.mp4"}, "grade": "subtle",
                             "ranges": [{"source": "a", "start": 0, "end": 2},
                                        {"source": "a", "start": 4, "end": 5}]})
    res = edit_render.render_edl(data, str(tmp_path), str(tmp_path / "work"),
                                 str(tmp_path / "out" / "final.mp4"))
    kinds = ["cut" if "-ss" in a else "concat" if "concat" in a else
             "loudnorm" if any("loudnorm" in str(x) for x in a) else "composite" for a in ff]
    # hai lần "loudnorm": lượt ĐO rồi lượt CHỈNH — đó chính là "hai lượt"
    assert kinds == ["cut", "cut", "concat", "composite", "loudnorm", "loudnorm"]
    # ffmpeg giả không in kết quả đo ⇒ lượt hai lùi về một lượt, và nói ra chứ không im lặng
    assert res["segments"] == 2 and res["loudnorm"] == "one-pass"
    assert res["outputs"][0]["duration"] == 3.0


def test_render_edl_refuses_an_unknown_quality(ff, probe, tmp_path):
    data = edl_mod.validate(_edl())
    with pytest.raises(ContractError):
        edit_render.render_edl(data, str(tmp_path), str(tmp_path / "w"),
                               str(tmp_path / "o.mp4"), quality="siêu-nét")


def test_missing_source_file_is_named(ff, probe, tmp_path):
    data = edl_mod.validate(_edl())
    with pytest.raises(ContractError) as e:
        edit_render.extract_all(data, str(tmp_path), str(tmp_path / "w"))
    assert "a.mp4" in str(e.value)


# ── chọn đường thi hành ─────────────────────────────────────────────────────────────────

@pytest.fixture
def station(tmp_path, monkeypatch):
    st = tmp_path / "st"
    st.mkdir()
    monkeypatch.setenv("VIDEO_STATION", str(st))
    return st


def _install_vendored(station, with_helpers=("transcribe_whisper.py", "pack_transcripts.py",
                                             "render.py")):
    vu = station / "video-use"
    (vu / "helpers").mkdir(parents=True)
    for n in with_helpers:
        (vu / "helpers" / n).write_text("# helper", encoding="utf-8")
    rel = ".venv/Scripts/python.exe" if os.name == "nt" else ".venv/bin/python"
    py = vu.joinpath(*rel.split("/"))
    py.parent.mkdir(parents=True, exist_ok=True)
    py.write_text("", encoding="utf-8")
    (station / "station.json").write_text(json.dumps(
        {"contract": "1.0.0", "video_use": {"dir": "video-use", "python": "video-use/" + rel}}),
        encoding="utf-8")
    return vu, str(py)


def test_auto_prefers_the_code_in_this_repo(station, monkeypatch):
    monkeypatch.setattr(edit, "_distill_can", lambda step: True)
    assert edit.choose_backend("transcribe") == "distill"


def test_auto_falls_back_to_the_vendored_tree(station, monkeypatch, capsys):
    _install_vendored(station)
    monkeypatch.setattr(edit, "_distill_can", lambda step: False)
    assert edit.choose_backend("transcribe") == "vendored"
    assert "bản video-use ở trạm" in capsys.readouterr().err


def test_with_neither_backend_it_is_code_3_and_says_both_ways(station, monkeypatch):
    monkeypatch.setattr(edit, "_distill_can", lambda step: False)
    with pytest.raises(StationMissing) as e:
        edit.choose_backend("transcribe")
    msg = str(e.value)
    assert "pip install -e" in msg and "install-video-use" in msg


def test_asking_for_vendored_without_one_is_code_3(station, monkeypatch):
    with pytest.raises(StationMissing) as e:
        edit.choose_backend("render", want="vendored")
    assert "install-video-use" in str(e.value)


def test_vendored_info_ignores_a_half_installed_tree(station):
    (station / "station.json").write_text(json.dumps(
        {"video_use": {"dir": "video-use", "python": None}}), encoding="utf-8")
    assert edit.vendored_info() == (None, None)


def test_vendored_transcribe_warns_when_only_the_paid_path_exists(station, monkeypatch, capsys,
                                                                  tmp_path):
    vu, py = _install_vendored(station, with_helpers=("transcribe.py",))
    seen = {}

    class R:
        returncode = 0

    def fake_run(argv, **kw):
        seen["argv"] = argv
        return R()

    monkeypatch.setattr(edit.subprocess, "run", fake_run)

    class Args:
        footage, language, force = str(tmp_path), "vi", False

    edit.step_transcribe(Args(), str(tmp_path / "w"), "vendored")
    assert seen["argv"][1].endswith("transcribe.py")
    assert "khoá API" in capsys.readouterr().err


def test_vendored_step_reports_a_failing_helper(station, monkeypatch, tmp_path):
    _install_vendored(station)

    class R:
        returncode = 3

    monkeypatch.setattr(edit.subprocess, "run", lambda argv, **kw: R())

    class Args:
        footage, language, force = str(tmp_path), "vi", False

    with pytest.raises(Exception) as e:
        edit.step_transcribe(Args(), str(tmp_path / "w"), "vendored")
    assert "mã 3" in str(e.value)


# ── nơi làm việc + CLI ──────────────────────────────────────────────────────────────────

def test_work_dir_sits_next_to_the_footage(tmp_path):
    f = tmp_path / "quay"
    f.mkdir()
    assert edit.work_dir_for(str(f)) == str(f / "edit")


def test_work_dir_falls_back_to_station_scratch_when_footage_is_read_only(
        tmp_path, station, monkeypatch):
    f = tmp_path / "the-nho"
    f.mkdir()
    monkeypatch.setattr(edit, "_writable", lambda p: False)
    got = edit.work_dir_for(str(f))
    assert got.startswith(str(station / "scratch"))


def test_missing_footage_is_code_3(tmp_path):
    assert edit.main(["--footage", str(tmp_path / "khong-co"), "--out", str(tmp_path)]) == 3


def test_render_step_without_an_edl_is_code_2(tmp_path, station):
    f = tmp_path / "quay"
    f.mkdir()
    assert edit.main(["--footage", str(f), "--out", str(tmp_path / "o"), "--step", "render"]) == 2


def test_run_without_an_edl_stops_after_packing_and_says_the_next_step(
        tmp_path, station, monkeypatch, capsys):
    f = tmp_path / "quay"
    f.mkdir()
    monkeypatch.setattr(edit, "choose_backend", lambda step, want="auto", station=None: "distill")
    monkeypatch.setattr(edit, "step_transcribe", lambda a, w, b: {"transcripts": []})

    def fake_pack(a, w, b):
        os.makedirs(w, exist_ok=True)
        return {"path": os.path.join(w, edit.PACKED)}

    monkeypatch.setattr(edit, "step_pack", fake_pack)
    assert edit.main(["--footage", str(f), "--out", str(tmp_path / "o"), "--json"]) == 0
    data = last_json(capsys.readouterr().out)
    assert data["steps"] == ["transcribe", "pack"]
    assert "edl.json" in data["next"] and "outputs" not in data


def test_plan_is_kept_beside_the_edit(tmp_path, station, monkeypatch):
    f = tmp_path / "quay"
    f.mkdir()
    plan = tmp_path / "plan.md"
    plan.write_text("# kế hoạch dựng", encoding="utf-8")
    monkeypatch.setattr(edit, "choose_backend", lambda step, want="auto", station=None: "distill")
    monkeypatch.setattr(edit, "step_transcribe", lambda a, w, b: {})
    monkeypatch.setattr(edit, "step_pack", lambda a, w, b: {})
    assert edit.main(["--footage", str(f), "--out", str(tmp_path / "o"),
                      "--plan", str(plan)]) == 0
    assert (f / "edit" / "plan.md").read_text(encoding="utf-8") == "# kế hoạch dựng"


def test_a_missing_plan_file_is_code_2(tmp_path, station):
    f = tmp_path / "quay"
    f.mkdir()
    assert edit.main(["--footage", str(f), "--out", str(tmp_path / "o"),
                      "--plan", str(tmp_path / "khong-co.md")]) == 2
