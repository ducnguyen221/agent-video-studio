"""`video_studio.reference.media`: khung có PTS thật và lưới khung.

Không ffmpeg thật: `_ff.run` / `_ff._probe_raw` là hàm giả; cái được kiểm là lệnh ffmpeg ĐƯỢC DỰNG RA
và cách đọc `pts_time` từ stderr giả.
"""
import json
import os

import pytest

from video_studio import _env
from video_studio.contract import ContractError, EngineError, StationMissing
from video_studio.edit import _ff
from video_studio.reference import media


def _raw(start="10.0", duration="40.0"):
    v = {"codec_type": "video", "width": 640, "height": 360, "avg_frame_rate": "30/1"}
    if start is not None:
        v["start_time"] = start
    fmt = {} if duration is None else {"duration": duration}
    return {"streams": [v], "format": fmt}


@pytest.fixture
def ff(monkeypatch):
    """ffmpeg "có mặt"; ghi lại mọi lệnh. Dict trả về chỉnh được stderr, probe, bộ lọc."""
    state = {"raw": _raw(), "stderr": "pts_time:11.0333", "filters": {"drawtext", "tile"},
             "calls": []}

    def fake_run(args, quiet=True, timeout=None):
        state["calls"].append({"args": list(args), "quiet": quiet})
        return state["stderr"]

    monkeypatch.setattr(_ff, "run", fake_run)
    monkeypatch.setattr(_ff, "exe", lambda: "ffmpeg")
    monkeypatch.setattr(_ff, "probe_exe", lambda: "ffprobe")
    monkeypatch.setattr(_ff, "_probe_raw", lambda p: state["raw"])
    monkeypatch.setattr(_env, "ffmpeg_filters", lambda exe=None: state["filters"])
    return state


def _vf(call):
    args = call["args"]
    return args[args.index("-vf") + 1]


def test_parse_showinfo_reads_pts_time():
    line = "[Parsed_showinfo_2 @ 0x1] n:   0 pts:  45045 pts_time:1.5015 duration:1001"
    assert media.parse_showinfo(line) == [1.5015]
    assert media.parse_showinfo("không có gì") == []
    assert media.parse_showinfo("pts_time:nan") == []
    assert media.parse_showinfo("pts_time:inf") == []
    assert media.parse_showinfo("pts_time:1.0 x\npts_time:2.5") == [1.0, 2.5]


def test_frames_use_absolute_pts_from_stream_start(ff, tmp_path):
    out = media.extract_frames("v.mp4", str(tmp_path), [1.0])
    assert out == [{"requested": 1.0, "pts_abs": 11.0333, "pts_time": 1.0333,
                    "file": "frame_001000.png"}]
    call = ff["calls"][0]
    args = call["args"]
    assert "-copyts" in args and "-ss" not in args
    assert _vf(call) == "select='gte(t,11.000000)',trim=end_frame=1,showinfo"
    i = args.index("-frames:v")
    assert args[i:i + 6] == ["-frames:v", "1", "-fps_mode", "passthrough", "-update", "1"]
    assert args[-1] == os.path.join(str(tmp_path), "frame_001000.png")
    assert call["quiet"] is False
    saved = json.loads((tmp_path / "frames.json").read_text(encoding="utf-8"))
    assert saved == out


def test_frames_refuse_unknown_origin(ff, tmp_path):
    ff["raw"] = _raw(start=None)
    with pytest.raises(ContractError, match="origin chưa xác định"):
        media.extract_frames("v.mp4", str(tmp_path), [1.0])
    assert ff["calls"] == []


@pytest.mark.parametrize("at", [[], [-1.0], [float("nan")], [float("inf")], ["x"],
                                [float(i) for i in range(61)], [1.0, 1.0]])
def test_frames_refuse_bad_or_too_many_marks(ff, tmp_path, at):
    ff["raw"] = _raw(duration="100.0")
    with pytest.raises(ContractError):
        media.extract_frames("v.mp4", str(tmp_path), at)
    assert ff["calls"] == []


def test_frames_refuse_past_duration(ff, tmp_path):
    with pytest.raises(ContractError, match="thời lượng"):
        media.extract_frames("v.mp4", str(tmp_path), [41.0])
    assert ff["calls"] == []


def test_frames_unknown_duration_warns_and_continues(ff, tmp_path, capsys):
    ff["raw"] = _raw(duration=None)
    out = media.extract_frames("v.mp4", str(tmp_path), [999.0])
    assert len(out) == 1
    assert "không rõ thời lượng" in capsys.readouterr().err


def test_tiles_unknown_duration_is_contract_error(ff, tmp_path):
    ff["raw"] = _raw(duration=None)
    with pytest.raises(ContractError, match="không rõ thời lượng"):
        media.contact_sheets("v.mp4", str(tmp_path), 2)
    assert ff["calls"] == []


def test_frames_never_overwrite_without_force(ff, tmp_path):
    (tmp_path / "frame_001000.png").write_bytes(b"x")
    with pytest.raises(ContractError, match="đã có"):
        media.extract_frames("v.mp4", str(tmp_path), [1.0])
    assert ff["calls"] == []
    assert (tmp_path / "frame_001000.png").read_bytes() == b"x"
    assert media.extract_frames("v.mp4", str(tmp_path), [1.0], force=True)
    assert len(ff["calls"]) == 1


def test_tiles_never_overwrite_without_force(ff, tmp_path):
    (tmp_path / "tiles_001.png").write_bytes(b"x")
    with pytest.raises(ContractError, match="đã có"):
        media.contact_sheets("v.mp4", str(tmp_path), 2)
    assert ff["calls"] == []
    media.contact_sheets("v.mp4", str(tmp_path), 2, force=True)
    assert len(ff["calls"]) == 1


def test_frames_no_pts_is_engine_error(ff, tmp_path):
    ff["stderr"] = "ffmpeg không in gì hữu ích"
    with pytest.raises(EngineError, match="pts_time"):
        media.extract_frames("v.mp4", str(tmp_path), [1.0])
    assert not (tmp_path / "frames.json").exists()


def test_frames_missing_ffmpeg_is_station_missing(monkeypatch, tmp_path):
    monkeypatch.setattr(_ff, "_probe_raw", lambda p: _raw())
    monkeypatch.setattr(_ff, "probe_exe", lambda: "ffprobe")
    monkeypatch.setattr(_ff._env, "ffmpeg_exe", lambda: None)
    with pytest.raises(StationMissing):
        media.extract_frames("v.mp4", str(tmp_path), [1.0])


def test_tiles_index_matches_grid(ff, tmp_path):
    res = media.contact_sheets("v.mp4", str(tmp_path), 2)
    assert (res["every"], res["cols"], res["rows"], res["width"]) == (2, 4, 4, 320)
    assert res["labels"] is False and res["timing"] == "approximate"
    assert [len(s["cells"]) for s in res["sheets"]] == [16, 4]
    s2 = res["sheets"][1]
    assert s2["file"] == "tiles_002.png"
    assert [c["index"] for c in s2["cells"]] == [16, 17, 18, 19]
    assert [c["approx_time"] for c in s2["cells"]] == [32.0, 34.0, 36.0, 38.0]
    call = ff["calls"][0]
    assert _vf(call) == "fps=1/2,scale=320:-2,tile=4x4"
    assert call["args"][-1] == os.path.join(str(tmp_path), "tiles_%03d.png")
    assert json.loads((tmp_path / "tiles.json").read_text(encoding="utf-8")) == res


@pytest.mark.parametrize("kw", [{"every": 0}, {"every": -1}, {"every": float("nan")},
                                {"every": 2, "cols": 0}, {"every": 2, "cols": 11},
                                {"every": 2, "rows": 0}, {"every": 2, "rows": 11},
                                {"every": 2, "width": 63}, {"every": 2, "width": 1921}])
def test_tiles_refuse_bad_params(ff, tmp_path, kw):
    with pytest.raises(ContractError):
        media.contact_sheets("v.mp4", str(tmp_path), **kw)
    assert ff["calls"] == []


def test_tiles_refuse_too_dense(ff, tmp_path):
    ff["raw"] = _raw(duration="1000.0")
    with pytest.raises(ContractError, match="tăng --every"):
        media.contact_sheets("v.mp4", str(tmp_path), 1)
    assert ff["calls"] == []


def test_tiles_label_without_drawtext_warns_and_continues(ff, tmp_path, capsys):
    ff["filters"] = {"tile"}
    res = media.contact_sheets("v.mp4", str(tmp_path), 2, label=True)
    assert res["labels"] is False
    assert "drawtext" in capsys.readouterr().err
    assert "drawtext" not in _vf(ff["calls"][0])


def test_tiles_label_with_drawtext_inserts_before_tile(ff, tmp_path):
    res = media.contact_sheets("v.mp4", str(tmp_path), 2, label=True)
    assert res["labels"] is True
    assert _vf(ff["calls"][0]) == (
        "fps=1/2,scale=320:-2,drawtext=text='%{pts\\:hms}':x=4:y=4:fontsize=18:"
        "fontcolor=white:box=1:boxcolor=black@0.5,tile=4x4")


def test_ffmpeg_args_are_a_list(ff, tmp_path):
    media.extract_frames("v.mp4", str(tmp_path), [1.0])
    media.contact_sheets("v.mp4", str(tmp_path / "t"), 2)
    for c in ff["calls"]:
        assert isinstance(c["args"], list)
        assert all(isinstance(a, str) for a in c["args"])
        assert "-i" in c["args"]
