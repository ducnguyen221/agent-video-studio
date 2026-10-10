"""Tests for local cleanup validation, filter selection, and manifest freshness."""
import hashlib
import json
from pathlib import Path
import subprocess
from types import SimpleNamespace

import pytest

from video_studio import contract
from video_studio.cleanup import (
    apply_cleanup,
    build_filter,
    parse_roi,
    validate_media,
    validate_range,
    verify_cleanup,
)
from video_studio.contract import ContractError, EngineError, StationMissing


def test_roi_uses_integer_pixels_and_rejects_nonfinite_values():
    assert parse_roi("12,24,80,44") == (12, 24, 80, 44)
    for value in ("1,2,3", "NaN,2,3,4", "1,2,0,4", "-1,2,3,4"):
        with pytest.raises(ContractError):
            parse_roi(value)


def test_roi_must_fit_the_displayed_frame():
    from video_studio.cleanup import validate_roi

    validate_roi((12, 24, 80, 44), 640, 360)
    with pytest.raises(ContractError, match="ngoài khung"):
        validate_roi((600, 24, 80, 44), 640, 360)
    with pytest.raises(ContractError, match="số chẵn"):
        validate_roi((11, 24, 80, 44), 640, 360)


def test_delogo_requires_safe_margin_from_frame_edges():
    from video_studio.cleanup import validate_method_roi

    with pytest.raises(ContractError, match="mép khung"):
        validate_method_roi("delogo", (0, 0, 20, 20), 640, 360)
    validate_method_roi("delogo", (2, 2, 20, 20), 640, 360)


def test_time_range_rejects_nan_infinity_and_out_of_bounds():
    assert validate_range(1.0, 2.0, 4.0) == (1.0, 2.0)
    for start, end in ((float("nan"), 2), (1, float("inf")), (-1, 2), (2, 2), (1, 5)):
        with pytest.raises(ContractError):
            validate_range(start, end, 4.0)


def test_pts_scan_classifies_constant_rate_and_variable_rate():
    from video_studio.cleanup import classify_timestamps

    assert classify_timestamps([0, 1 / 24, 2 / 24, 3 / 24])["cfr"] is True
    assert classify_timestamps([0, 1 / 24, 2 / 24, 3 / 24 + 0.004])["cfr"] is False
    assert classify_timestamps([0])["cfr"] is False


@pytest.mark.parametrize("method,fragment", [
    ("delogo", "delogo=x=12:y=24:w=80:h=44:show=0:enable='between(t,1,2)'") ,
    ("blur", "boxblur=12:2:10:2"),
    ("cover", "drawbox=x=12:y=24:w=80:h=44:color=0x112233:t=fill"),
    ("crop", "crop=w=80:h=44:x=12:y=24"),
])
def test_filter_graph_uses_only_validated_geometry_and_time(method, fragment):
    graph, label = build_filter(method, (12, 24, 80, 44), 1.0, 2.0, "#112233")
    assert fragment in graph
    assert label == "vout"


def test_cover_color_rejects_filter_syntax():
    with pytest.raises(ContractError, match="#RRGGBB"):
        build_filter("cover", (0, 0, 2, 2), 0, 1, "red:enable=1")


@pytest.mark.parametrize("size,luma_radius,chroma_radius", [(20, 9, 4), (28, 12, 6), (40, 12, 9)])
def test_blur_radius_fits_small_chroma_planes(size, luma_radius, chroma_radius):
    graph, _ = build_filter("blur", (0, 0, size, size), 0, 1)
    assert f"boxblur={luma_radius}:2:{chroma_radius}:2" in graph


def test_media_policy_rejects_hdr_rotation_and_unhandled_pixel_format():
    base = SimpleNamespace(width=640, height=360, duration=4.0, rotation=0, hdr=False,
                           pix_fmt="yuv420p", video_codec="h264", avg_frame_rate="30/1",
                           r_frame_rate="30/1", fps=30, audio=[], color_range="tv",
                           color_transfer="bt709", color_primaries="bt709",
                           color_space="bt709", video_start_time=0.0,
                           audio_start_times=[])
    assert validate_media(base)["vfr_check"] == "NOT_CHECKED"
    for changes, phrase in (({"rotation": 90}, "rotation"), ({"hdr": True}, "HDR"),
                            ({"pix_fmt": "yuv420p10le"}, "pixel format")):
        with pytest.raises(ContractError, match=phrase):
            validate_media(SimpleNamespace(**{**vars(base), **changes}))


def test_media_policy_rejects_unknown_stream_origins():
    base = SimpleNamespace(width=640, height=360, duration=4.0, rotation=0, hdr=False,
                           pix_fmt="yuv420p", video_codec="h264", avg_frame_rate="24/1",
                           r_frame_rate="24/1", fps=24, audio=[], color_range="tv",
                           color_transfer="bt709", color_primaries="bt709",
                           color_space="bt709", video_start_time=None,
                           audio_start_times=[])
    with pytest.raises(ContractError, match="mốc thời gian"):
        validate_media(base)


@pytest.mark.parametrize("field,phrase", [
    ("frame_rate", "frame rate"),
    ("av_sync_origin", "AV start offset"),
    ("color_metadata", "color metadata"),
    ("duration", "thời lượng"),
])
def test_render_pair_rejects_timing_or_color_drift_before_publish(field, phrase):
    from video_studio.cleanup import _validate_render_pair

    source = SimpleNamespace(duration=4.0, fps=24.0, video_start_time=0.0,
                             audio_start_times=[0.0], pix_fmt="yuv420p",
                             color_range="tv", color_transfer="bt709",
                             color_primaries="bt709", color_space="bt709")
    output = SimpleNamespace(duration=4.0, video_start_time=0.0,
                             audio_start_times=[0.0], pix_fmt="yuv420p",
                             color_range="tv", color_transfer="bt709",
                             color_primaries="bt709", color_space="bt709")
    input_timing = {"fps": 24.0, "cfr": True, "frames": 96}
    output_timing = {"fps": 24.0, "cfr": True, "frames": 96}
    if field == "frame_rate":
        output_timing["fps"] = 25.0
    elif field == "av_sync_origin":
        output.audio_start_times = [0.1]
    elif field == "color_metadata":
        output.color_transfer = "smpte2084"
    else:
        output.duration = 3.0
    with pytest.raises(EngineError, match=phrase):
        _validate_render_pair(source, output, input_timing, output_timing, expected_duration=4.0)


def _write_manifest(path, source, output):
    def digest(file_path):
        return hashlib.sha256(file_path.read_bytes()).hexdigest()

    path.write_text(json.dumps({
        "schema_version": 1,
        "input": str(source),
        "input_sha256": digest(source),
        "output": str(output),
        "output_sha256": digest(output),
        "source_media": {"width": 640, "height": 360, "duration": 4.0,
                         "audio_streams": 1, "frame_count": 96, "measured_fps": 24.0,
                         "video_start_time": 0.0, "audio_start_times": [0.0],
                         "pix_fmt": "yuv420p", "color_range": "tv",
                         "color_transfer": "bt709", "color_primaries": "bt709",
                         "color_space": "bt709", "vfr_check": "PASS"},
        "output_media": {"width": 640, "height": 360, "duration": 4.0,
                         "fps": 24.0, "audio_streams": 1, "frame_count": 96,
                         "video_start_time": 0.0, "audio_start_times": [0.0],
                         "pix_fmt": "yuv420p", "color_range": "tv",
                         "color_transfer": "bt709", "color_primaries": "bt709",
                         "color_space": "bt709", "vfr_check": "PASS"},
        "operation": {"method": "delogo", "roi": {"x": 12, "y": 24,
                      "width": 80, "height": 44}, "start": 0.0, "end": 4.0,
                      "color": None},
        "audio_fingerprints": {"source": [{"packets": 100, "sha256": "a" * 64}],
                               "output": [{"packets": 100, "sha256": "a" * 64}]},
        "audio_signature": {
            "source": [{"codec": "aac", "sample_rate": "48000", "channels": 1,
                        "channel_layout": "mono"}],
            "output": [{"codec": "aac", "sample_rate": "48000", "channels": 1,
                        "channel_layout": "mono"}],
        },
        "technical_checks": {"source_hash": "PASS", "output_probe": "PASS"},
        "visual_review": "NOT_CHECKED",
    }), encoding="utf-8")


def test_verify_recomputes_hashes_instead_of_trusting_manifest(tmp_path, monkeypatch):
    source = tmp_path / "source.mp4"
    output = tmp_path / "output.mp4"
    manifest = tmp_path / "output.mp4.cleanup.json"
    source.write_bytes(b"source")
    output.write_bytes(b"output")
    _write_manifest(manifest, source, output)
    monkeypatch.setattr("video_studio.cleanup._probe", lambda _path: SimpleNamespace(
        duration=4.0, width=640, height=360, audio=[{"codec_name": "aac",
        "sample_rate": "48000", "channels": 1, "channel_layout": "mono"}],
        fps=24.0, pix_fmt="yuv420p",
        color_range="tv", color_transfer="bt709", color_primaries="bt709",
        color_space="bt709", video_start_time=0.0, audio_start_times=[0.0]))
    monkeypatch.setattr("video_studio.cleanup.check_constant_frame_rate", lambda _path: {
        "cfr": True, "frames": 96, "fps": 24.0})
    monkeypatch.setattr("video_studio.cleanup.audio_fingerprints", lambda _path: [{
        "packets": 100, "sha256": "a" * 64}])

    result = verify_cleanup(str(source), str(output))
    assert result["ok"] is True
    assert result["visual_review"] == "NOT_CHECKED"

    output.write_bytes(b"changed output")
    stale = verify_cleanup(str(source), str(output))
    assert stale["ok"] is False
    assert stale["technical_checks"]["output_hash"] == "FAIL"
    assert stale["technical_checks"]["output_probe"] == "PASS"


@pytest.mark.parametrize("mutation", [
    lambda data: data["operation"].update(method="unknown"),
    lambda data: data["operation"]["roi"].update(x=10000),
    lambda data: data["operation"]["roi"].update(width=-1),
    lambda data: data["operation"].update(start=float("nan")),
    lambda data: data["operation"].update(end=None),
    lambda data: data.update(source_media="bad"),
    lambda data: data["audio_fingerprints"].update(source="bad"),
])
def test_verify_rejects_malformed_manifest_before_media_scan(tmp_path, monkeypatch, mutation):
    source = tmp_path / "source.mp4"
    output = tmp_path / "output.mp4"
    manifest = tmp_path / "output.mp4.cleanup.json"
    source.write_bytes(b"source")
    output.write_bytes(b"output")
    _write_manifest(manifest, source, output)
    data = json.loads(manifest.read_text(encoding="utf-8"))
    mutation(data)
    manifest.write_text(json.dumps(data), encoding="utf-8")
    monkeypatch.setattr("video_studio.cleanup._probe", lambda _path: pytest.fail("unexpected probe"))
    with pytest.raises(ContractError, match="manifest"):
        verify_cleanup(str(source), str(output))


def test_output_symlink_and_hardlink_collisions_are_rejected(tmp_path):
    from video_studio.cleanup import _check_output_path

    source = tmp_path / "source.mp4"
    source.write_bytes(b"source")
    link = tmp_path / "hardlink.mp4"
    link.hardlink_to(source)
    with pytest.raises(ContractError, match="hard link"):
        _check_output_path(str(source), str(link))

    symlink = tmp_path / "symlink.mp4"
    try:
        symlink.symlink_to(tmp_path / "elsewhere.mp4")
    except (OSError, NotImplementedError):
        pytest.skip("symlink creation is unavailable on this host")
    with pytest.raises(ContractError, match="symbolic link"):
        _check_output_path(str(source), str(symlink))


def test_missing_ffmpeg_inspect_emits_contract_json(tmp_path, monkeypatch, capsys):
    from video_studio import cleanup
    from video_studio.contract import StationMissing

    source = tmp_path / "source.mp4"
    source.write_bytes(b"not decoded because ffprobe is missing")
    monkeypatch.setattr(cleanup, "_probe", lambda _path: (_ for _ in ()).throw(
        StationMissing("ffprobe missing")))
    code = cleanup.main(["inspect", "--input", str(source), "--json"])
    assert code == contract.STATION_MISSING
    payload = json.loads(capsys.readouterr().out.splitlines()[-1])
    assert payload["ok"] is False and payload["code"] == 3


def test_apply_removes_partial_temp_when_ffmpeg_fails(tmp_path, monkeypatch):
    from video_studio import cleanup
    from video_studio.contract import EngineError

    source = tmp_path / "source.mp4"
    output_dir = tmp_path / "out"
    output_dir.mkdir()
    source.write_bytes(b"source")
    info = SimpleNamespace(width=640, height=360, duration=4.0, rotation=0, hdr=False,
                           pix_fmt="yuv420p", video_codec="h264", avg_frame_rate="24/1",
                           r_frame_rate="24/1", fps=24, audio=[], color_range="tv",
                           color_transfer="bt709", color_primaries="bt709",
                           color_space="bt709", video_start_time=0.0,
                           audio_start_times=[])
    monkeypatch.setattr(cleanup, "_probe", lambda _path: info)
    monkeypatch.setattr(cleanup, "check_constant_frame_rate", lambda _path: {
        "cfr": True, "frames": 96, "fps": 24.0})
    monkeypatch.setattr(cleanup, "audio_fingerprints", lambda _path: [])

    def failed_ffmpeg(argv):
        Path(argv[-1]).write_bytes(b"partial render")
        raise EngineError("synthetic FFmpeg failure")

    monkeypatch.setattr(cleanup._ff, "run", failed_ffmpeg)
    with pytest.raises(EngineError, match="synthetic FFmpeg failure"):
        apply_cleanup(str(source), str(output_dir / "cleaned.mp4"), "delogo",
                      (10, 10, 20, 20), 0, 4)

    assert list(output_dir.iterdir()) == []


def test_apply_and_preview_publish_only_after_all_render_checks(tmp_path, monkeypatch, capsys):
    from video_studio import cleanup

    source = tmp_path / "source.mp4"
    output_dir = tmp_path / "out"
    output_dir.mkdir()
    source.write_bytes(b"source")
    info = SimpleNamespace(width=640, height=360, duration=4.0, rotation=0, hdr=False,
                           pix_fmt="yuv420p", video_codec="h264", avg_frame_rate="24/1",
                           r_frame_rate="24/1", fps=24.0, audio=[], color_range="tv",
                           color_transfer="bt709", color_primaries="bt709",
                           color_space="bt709", video_start_time=0.0, audio_start_times=[])

    def probe(path):
        if ".preview-" in Path(path).name:
            return SimpleNamespace(**{**vars(info), "duration": 2.0})
        return info

    monkeypatch.setattr(cleanup, "_probe", probe)
    monkeypatch.setattr(cleanup, "check_constant_frame_rate", lambda path: {
        "cfr": True, "frames": 48 if ".preview-" in Path(path).name else 96,
        "fps": 24.0})
    monkeypatch.setattr(cleanup, "audio_fingerprints", lambda _path: [])
    monkeypatch.setattr(cleanup._ff, "run", lambda argv: Path(argv[-1]).write_bytes(b"rendered"))

    apply_args = ["apply", "--input", str(source), "--out", str(output_dir), "--name",
                  "cleaned.mp4", "--method", "cover", "--roi", "12,24,80,44",
                  "--start", "0", "--end", "4", "--json"]
    assert cleanup.main(apply_args) == contract.OK
    applied = json.loads(capsys.readouterr().out)
    result = applied
    assert Path(result["output"]).is_file()
    assert Path(result["manifest"]).is_file()
    assert result["technical_checks"]["frame_timing"] == "PASS"

    verify_args = ["verify", "--input", str(source), "--out", str(output_dir), "--name",
                   "cleaned.mp4", "--json"]
    assert cleanup.main(verify_args) == contract.OK
    verified = json.loads(capsys.readouterr().out)
    assert verified["ok"] is True
    assert verified["technical_checks"]["frame_rate"] == "PASS"

    preview_args = ["preview", "--input", str(source), "--out", str(output_dir), "--name",
                    "preview.mp4", "--method", "blur", "--roi", "12,24,80,44",
                    "--start", "1", "--end", "3", "--json"]
    assert cleanup.main(preview_args) == contract.OK
    preview = json.loads(capsys.readouterr().out)
    assert Path(preview["output"]).is_file()
    assert preview["duration"] == 2.0
    assert preview["frame_count"] == 48


def test_inspect_json_reports_runtime_cfr_and_media_support(tmp_path, monkeypatch, capsys):
    from video_studio import cleanup

    source = tmp_path / "source.mp4"
    source.write_bytes(b"synthetic")
    info = SimpleNamespace(width=640, height=360, duration=4.0, rotation=0, hdr=False,
                           pix_fmt="yuv420p", video_codec="h264", avg_frame_rate="24/1",
                           r_frame_rate="24/1", fps=24.0, audio=[], color_range="tv",
                           color_transfer="bt709", color_primaries="bt709",
                           color_space="bt709", video_start_time=0.0, audio_start_times=[])
    monkeypatch.setattr(cleanup, "_probe", lambda _path: info)
    monkeypatch.setattr(cleanup, "check_constant_frame_rate", lambda _path: {
        "status": "PASS", "cfr": True, "frames": 96, "fps": 24.0})
    assert cleanup.main(["inspect", "--input", str(source), "--json"]) == contract.OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["media"]["supported_for_cleanup"] is True
    assert payload["media"]["frame_count"] == 96


def test_inspect_marks_vfr_unsupported_and_verify_requires_current_files(tmp_path, monkeypatch):
    from video_studio import cleanup

    source = tmp_path / "source.mp4"
    output = tmp_path / "output.mp4"
    source.write_bytes(b"source")
    info = SimpleNamespace(width=640, height=360, duration=4.0, rotation=0, hdr=False,
                           pix_fmt="yuv420p", video_codec="h264", avg_frame_rate="24/1",
                           r_frame_rate="24/1", fps=24.0, audio=[], color_range="tv",
                           color_transfer="bt709", color_primaries="bt709",
                           color_space="bt709", video_start_time=0.0, audio_start_times=[])
    monkeypatch.setattr(cleanup, "_probe", lambda _path: info)
    monkeypatch.setattr(cleanup, "check_constant_frame_rate", lambda _path: {
        "status": "VFR_OR_UNVERIFIABLE", "cfr": False, "frames": 96, "fps": 24.0})
    inspected = cleanup.inspect_video(str(source))
    assert inspected["media"]["supported_for_cleanup"] is False
    assert "VFR" in inspected["media"]["support_notes"][-1]

    with pytest.raises(ContractError, match="không có output"):
        cleanup.verify_cleanup(str(source), str(output))
    output.write_bytes(b"output")
    with pytest.raises(ContractError, match="không có manifest"):
        cleanup.verify_cleanup(str(source), str(output))


@pytest.mark.parametrize("failure,error_type,phrase", [
    (subprocess.TimeoutExpired("ffprobe", 2), EngineError, "quá"),
    (OSError("ffprobe unavailable"), StationMissing, "không chạy được ffprobe"),
    (subprocess.CompletedProcess("ffprobe", 1, "", "probe failed"), EngineError, "scan hỏng"),
])
def test_ffprobe_scan_errors_have_typed_contract_failures(monkeypatch, failure, error_type, phrase):
    from video_studio import cleanup

    def fail(*_args, **_kwargs):
        if isinstance(failure, BaseException):
            raise failure
        return failure

    monkeypatch.setattr(cleanup._ff, "probe_exe", lambda: "ffprobe")
    monkeypatch.setattr(cleanup.subprocess, "run", fail)
    with pytest.raises(error_type, match=phrase):
        cleanup._ffprobe_text("input.mp4", "-show_frames")


@pytest.mark.parametrize("failure,phrase", [
    ("geometry", "kích thước output"),
    ("audio-count", "số track audio"),
    ("audio-config", "cấu hình track audio"),
    ("cfr", "PTS/count khung"),
    ("frame-count", "số khung output"),
    ("audio-payload", "payload audio"),
    ("fps", "frame rate"),
    ("av-offset", "AV start offset"),
    ("color", "color metadata"),
    ("duration", "thời lượng output"),
    ("source-change", "nguồn đã thay đổi"),
])
def test_apply_does_not_publish_when_render_checks_fail(tmp_path, monkeypatch, failure, phrase):
    from video_studio import cleanup

    source = tmp_path / "source.mp4"
    output_dir = tmp_path / "out"
    output_dir.mkdir()
    source.write_bytes(b"source")
    source_audio = [{"codec_name": "aac", "sample_rate": "48000", "channels": 1,
                     "channel_layout": "mono"}]
    info = SimpleNamespace(width=640, height=360, duration=4.0, rotation=0, hdr=False,
                           pix_fmt="yuv420p", video_codec="h264", avg_frame_rate="24/1",
                           r_frame_rate="24/1", fps=24.0, audio=source_audio,
                           color_range="tv", color_transfer="bt709", color_primaries="bt709",
                           color_space="bt709", video_start_time=0.0, audio_start_times=[0.0])
    output_info = SimpleNamespace(**vars(info))
    if failure == "geometry":
        output_info.width = 638
    elif failure == "audio-count":
        output_info.audio = []
        output_info.audio_start_times = []
    elif failure == "audio-config":
        output_info.audio = [{**source_audio[0], "codec_name": "mp3"}]
    elif failure == "av-offset":
        output_info.audio_start_times = [0.1]
    elif failure == "color":
        output_info.color_transfer = "smpte2084"
    elif failure == "duration":
        output_info.duration = 3.0

    def probe(path):
        return output_info if Path(path).name.startswith(".cleaned.render-") else info

    def timing(path):
        frames, fps, cfr = 96, 24.0, True
        if Path(path).name.startswith(".cleaned.render-"):
            if failure == "cfr":
                cfr = False
            elif failure == "frame-count":
                frames = 95
            elif failure == "fps":
                fps = 25.0
        return {"cfr": cfr, "frames": frames, "fps": fps}

    def fingerprints(path):
        digest = "b" * 64 if failure == "audio-payload" and Path(path).name.startswith(
            ".cleaned.render-") else "a" * 64
        return [{"packets": 100, "sha256": digest}]

    def run(argv):
        Path(argv[-1]).write_bytes(b"partial or completed render")
        if failure == "source-change":
            source.write_bytes(b"changed during render")

    monkeypatch.setattr(cleanup, "_probe", probe)
    monkeypatch.setattr(cleanup, "check_constant_frame_rate", timing)
    monkeypatch.setattr(cleanup, "audio_fingerprints", fingerprints)
    monkeypatch.setattr(cleanup._ff, "run", run)
    with pytest.raises(EngineError, match=phrase):
        cleanup.apply_cleanup(str(source), str(output_dir / "cleaned.mp4"),
                              "cover", (12, 24, 80, 44), 0, 4)
    assert list(output_dir.iterdir()) == []


def test_cli_rejects_output_name_that_escapes_output_directory(tmp_path, capsys):
    from video_studio import cleanup

    source = tmp_path / "source.mp4"
    source.write_bytes(b"source")
    code = cleanup.main(["preview", "--input", str(source), "--out", str(tmp_path),
                         "--name", "../escape.mp4", "--method", "cover", "--roi", "0,0,2,2",
                         "--start", "0", "--end", "1", "--json"])
    payload = json.loads(capsys.readouterr().out.splitlines()[-1])
    assert code == contract.CONTRACT_ERROR
    assert payload["ok"] is False and payload["code"] == contract.CONTRACT_ERROR
    assert not (tmp_path.parent / "escape.mp4").exists()
