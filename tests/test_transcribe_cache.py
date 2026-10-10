"""Transcript cache behavior, without loading ASR or invoking FFmpeg."""
import json
import os
import shutil
import subprocess
import sys
import threading
from types import SimpleNamespace

import pytest

from video_studio.edit import transcribe as tr


class _Word:
    word = " hello "
    start = 0.1
    end = 0.5


class _Segment:
    text = " hello"
    words = [_Word()]


class _Info:
    language = "en"


class _Model:
    def __init__(self, text=" hello"):
        self.text = text
        self.calls = 0
        self.model_size_or_path = "large-v3"
        self.device = "cpu"
        self.compute_type = "int8"
        self.last_wav_bytes = None

    def transcribe(self, wav, **kwargs):
        self.calls += 1
        assert os.path.isfile(wav)
        self.last_wav_bytes = open(wav, "rb").read()
        self.last_kwargs = kwargs
        segment = _Segment()
        segment.text = self.text
        return [segment], _Info()


def _configure(monkeypatch, model):
    runtime_version = {"value": "test-runtime-1"}
    monkeypatch.setattr(tr, "load_model", lambda: model)
    monkeypatch.setattr(tr.importlib.metadata, "version",
                        lambda package: runtime_version["value"] if package == "faster-whisper"
                        else "unknown")

    def extract_audio(_video, dest):
        with open(dest, "wb") as stream:
            stream.write(b"fake wav")
        return dest

    monkeypatch.setattr(tr, "extract_audio", extract_audio)
    return runtime_version


def _payload(work_dir):
    return json.loads((work_dir / "transcripts" / "clip.json").read_text(encoding="utf-8"))


def test_reuses_only_matching_source_model_language_settings_and_schema(tmp_path, monkeypatch):
    source = tmp_path / "clip.mp4"
    source.write_bytes(b"source-1")
    model = _Model()
    runtime_version = _configure(monkeypatch, model)

    out = tr.transcribe_one(str(source), str(tmp_path / "work"), language="en")
    assert model.calls == 1
    assert tr.transcribe_one(str(source), str(tmp_path / "work"), language="en") == out
    assert model.calls == 1

    assert tr.transcribe_one(str(source), str(tmp_path / "work"), language="fr") == out
    assert model.calls == 2
    model.model_size_or_path = "small"
    tr.transcribe_one(str(source), str(tmp_path / "work"), language="fr")
    assert model.calls == 3
    runtime_version["value"] = "test-runtime-2"
    tr.transcribe_one(str(source), str(tmp_path / "work"), language="fr")
    assert model.calls == 4
    model.device = "cuda"
    tr.transcribe_one(str(source), str(tmp_path / "work"), language="fr")
    assert model.calls == 5
    model.compute_type = "float16"
    tr.transcribe_one(str(source), str(tmp_path / "work"), language="fr")
    assert model.calls == 6
    monkeypatch.setattr(tr, "ASR_SETTINGS", {**tr.ASR_SETTINGS, "vad_filter": False})
    tr.transcribe_one(str(source), str(tmp_path / "work"), language="fr")
    assert model.calls == 7
    monkeypatch.setattr(tr, "TRANSCRIPT_SCHEMA", tr.TRANSCRIPT_SCHEMA + 1)
    tr.transcribe_one(str(source), str(tmp_path / "work"), language="fr")
    assert model.calls == 8
    assert _payload(tmp_path / "work")["text"] == "hello"


def test_source_bytes_change_with_same_size_and_mtime_is_a_miss(tmp_path, monkeypatch):
    source = tmp_path / "clip.mp4"
    source.write_bytes(b"source-A")
    stamp = source.stat().st_mtime_ns
    model = _Model()
    _configure(monkeypatch, model)
    work = tmp_path / "work"

    tr.transcribe_one(str(source), str(work), language="en")
    source.write_bytes(b"source-B")
    os.utime(source, ns=(stamp, stamp))
    tr.transcribe_one(str(source), str(work), language="en")

    assert source.stat().st_size == len(b"source-A")
    assert source.stat().st_mtime_ns == stamp
    assert model.calls == 2


def test_source_change_during_model_load_cannot_hit_old_snapshot(tmp_path, monkeypatch):
    source = tmp_path / "clip.mp4"
    source.write_bytes(b"AAAA")
    work = tmp_path / "work"
    model = _Model(" old")
    _configure(monkeypatch, model)
    out = tr.transcribe_one(str(source), str(work), language="en")
    old_payload = open(out, encoding="utf-8").read()

    def change_during_load():
        source.write_bytes(b"BBBB")
        return model

    monkeypatch.setattr(tr, "load_model", change_during_load)
    with pytest.raises(tr.ContractError, match="nguồn đổi"):
        tr.transcribe_one(str(source), str(work), language="en")

    assert open(out, encoding="utf-8").read() == old_payload
    assert model.calls == 1


def test_aba_during_extraction_uses_the_verified_snapshot(tmp_path, monkeypatch):
    source = tmp_path / "clip.mp4"
    source.write_bytes(b"AAAA")
    work = tmp_path / "work"
    model = _Model()
    _configure(monkeypatch, model)

    def mutate_live_source_then_extract_snapshot(video, dest):
        source.write_bytes(b"BBBB")
        extracted = open(video, "rb").read()
        source.write_bytes(b"AAAA")
        with open(dest, "wb") as stream:
            stream.write(extracted)

    def transcript_from_wav(wav, **_kwargs):
        model.calls += 1
        segment = _Segment()
        segment.text = " " + open(wav, "rb").read().decode("ascii")
        return [segment], _Info()

    monkeypatch.setattr(tr, "extract_audio", mutate_live_source_then_extract_snapshot)
    monkeypatch.setattr(model, "transcribe", transcript_from_wav)
    out = tr.transcribe_one(str(source), str(work), language="en")

    assert source.read_bytes() == b"AAAA"
    assert json.loads(open(out, encoding="utf-8").read())["text"] == "AAAA"
    assert tr.transcribe_one(str(source), str(work), language="en") == out
    assert model.calls == 1


def test_unknown_model_metadata_never_accepts_existing_cache(tmp_path, monkeypatch, capsys):
    source = tmp_path / "clip.mp4"
    source.write_bytes(b"source")
    model = _Model()
    _configure(monkeypatch, model)
    work = tmp_path / "work"
    tr.transcribe_one(str(source), str(work), language="en")

    model.compute_type = None
    tr.transcribe_one(str(source), str(work), language="en")

    assert model.calls == 2
    assert "model" in capsys.readouterr().err.lower()


@pytest.mark.parametrize("field", ["model_size_or_path", "device", "compute_type"])
def test_missing_effective_model_attribute_forces_a_cache_miss(tmp_path, monkeypatch, field):
    source = tmp_path / "clip.mp4"
    source.write_bytes(b"source")
    work = tmp_path / "work"
    model = _Model()
    _configure(monkeypatch, model)
    tr.transcribe_one(str(source), str(work), language="en")
    setattr(model, field, None)

    tr.transcribe_one(str(source), str(work), language="en")

    assert model.calls == 2


def test_unknown_runtime_version_forces_a_cache_miss(tmp_path, monkeypatch):
    source = tmp_path / "clip.mp4"
    source.write_bytes(b"source")
    work = tmp_path / "work"
    model = _Model()
    _configure(monkeypatch, model)
    tr.transcribe_one(str(source), str(work), language="en")

    def missing_runtime(_package):
        raise tr.importlib.metadata.PackageNotFoundError

    monkeypatch.setattr(tr.importlib.metadata, "version", missing_runtime)
    tr.transcribe_one(str(source), str(work), language="en")

    assert model.calls == 2


def test_custom_model_weights_without_trusted_revision_force_a_cache_miss(
        tmp_path, monkeypatch):
    source = tmp_path / "clip.mp4"
    source.write_bytes(b"source")
    work = tmp_path / "work"
    model = _Model()
    _configure(monkeypatch, model)
    tr.transcribe_one(str(source), str(work), language="en")
    model.model_size_or_path = str(tmp_path / "mutable-custom-weights")

    tr.transcribe_one(str(source), str(work), language="en")

    assert model.calls == 2


def test_corrupt_payload_or_sidecar_is_a_reasoned_miss(tmp_path, monkeypatch, capsys):
    source = tmp_path / "clip.mp4"
    source.write_bytes(b"source")
    model = _Model()
    _configure(monkeypatch, model)
    work = tmp_path / "work"
    out = tr.transcribe_one(str(source), str(work), language="en")
    sidecar = tmp_path / "work" / "transcripts" / "clip.json.meta"

    with open(out, "w", encoding="utf-8") as stream:
        stream.write("{")
    tr.transcribe_one(str(source), str(work), language="en")
    assert model.calls == 2
    assert "payload" in capsys.readouterr().err.lower()

    sidecar.write_text("not metadata", encoding="utf-8")
    tr.transcribe_one(str(source), str(work), language="en")
    assert model.calls == 3
    assert "metadata" in capsys.readouterr().err.lower()


def test_non_finite_timestamp_in_cached_payload_is_a_reasoned_miss(
        tmp_path, monkeypatch, capsys):
    source = tmp_path / "clip.mp4"
    source.write_bytes(b"source")
    work = tmp_path / "work"
    model = _Model()
    _configure(monkeypatch, model)
    out = tr.transcribe_one(str(source), str(work), language="en")
    payload = json.loads(open(out, encoding="utf-8").read())
    payload["words"][0]["start"] = float("nan")
    open(out, "w", encoding="utf-8").write(json.dumps(payload))

    tr.transcribe_one(str(source), str(work), language="en")

    assert model.calls == 2
    assert "payload is invalid" in capsys.readouterr().err.lower()


def test_overflowing_integer_timestamp_in_cache_is_a_reasoned_miss(
        tmp_path, monkeypatch, capsys):
    source = tmp_path / "clip.mp4"
    source.write_bytes(b"source")
    work = tmp_path / "work"
    model = _Model()
    _configure(monkeypatch, model)
    out = tr.transcribe_one(str(source), str(work), language="en")
    metadata_path = out + ".meta"

    payload_bytes = open(out, "rb").read()
    payload = json.loads(payload_bytes)
    payload["words"][0]["start"] = 10 ** 400
    payload_bytes = (json.dumps(payload, ensure_ascii=False, indent=2,
                                allow_nan=False) + "\n").encode("utf-8")
    open(out, "wb").write(payload_bytes)
    metadata = json.loads(open(metadata_path, "r", encoding="utf-8").read())
    metadata["output_sha256"] = tr._sha256_bytes(payload_bytes)
    open(metadata_path, "w", encoding="utf-8").write(
        json.dumps(metadata, ensure_ascii=False, sort_keys=True, indent=2) + "\n")

    tr.transcribe_one(str(source), str(work), language="en")

    assert model.calls == 2
    assert "payload is invalid" in capsys.readouterr().err.lower()


def test_overflowing_integer_asr_timestamp_fails_and_preserves_old_cache(
        tmp_path, monkeypatch):
    source = tmp_path / "clip.mp4"
    source.write_bytes(b"source")
    work = tmp_path / "work"
    model = _Model()
    _configure(monkeypatch, model)
    out = tr.transcribe_one(str(source), str(work), language="en")
    old_payload = open(out, "rb").read()
    old_metadata = open(out + ".meta", "rb").read()

    def invalid_result(_wav, **_kwargs):
        word = _Word()
        word.start = 10 ** 400
        word.end = 10 ** 400
        segment = _Segment()
        segment.words = [word]
        return [segment], _Info()

    monkeypatch.setattr(model, "transcribe", invalid_result)
    with pytest.raises(tr.ContractError, match="timestamp|thời gian|không hợp lệ"):
        tr.transcribe_one(str(source), str(work), language="en", force=True)

    assert open(out, "rb").read() == old_payload
    assert open(out + ".meta", "rb").read() == old_metadata


def test_legacy_payload_and_failed_asr_are_preserved_until_new_result_is_valid(
        tmp_path, monkeypatch):
    source = tmp_path / "clip.mp4"
    source.write_bytes(b"source")
    work = tmp_path / "work"
    out_dir = work / "transcripts"
    out_dir.mkdir(parents=True)
    out = out_dir / "clip.json"
    old = '{"text": "legacy", "language_code": "en", "words": []}\n'
    out.write_text(old, encoding="utf-8")
    model = _Model()
    _configure(monkeypatch, model)
    monkeypatch.setattr(model, "transcribe", lambda *_a, **_k: (_ for _ in ()).throw(
        RuntimeError("ASR failed")))

    try:
        tr.transcribe_one(str(source), str(work), language="en")
    except RuntimeError as exc:
        assert str(exc) == "ASR failed"
    else:
        raise AssertionError("ASR failure should propagate")

    assert out.read_text(encoding="utf-8") == old


@pytest.mark.parametrize("invalid_time", [float("nan"), float("inf"), float("-inf"),
                                           -0.1, True])
def test_invalid_asr_timestamps_fail_closed_and_preserve_old_cache(
        tmp_path, monkeypatch, invalid_time):
    source = tmp_path / "clip.mp4"
    source.write_bytes(b"source")
    work = tmp_path / "work"
    model = _Model()
    _configure(monkeypatch, model)
    out = tr.transcribe_one(str(source), str(work), language="en")
    old_payload = open(out, "rb").read()
    old_metadata = open(out + ".meta", "rb").read()

    def invalid_result(_wav, **_kwargs):
        word = _Word()
        word.start = invalid_time
        word.end = 0.5
        segment = _Segment()
        segment.words = [word]
        return [segment], _Info()

    monkeypatch.setattr(model, "transcribe", invalid_result)
    with pytest.raises(tr.ContractError, match="timestamp|thời gian|không hợp lệ"):
        tr.transcribe_one(str(source), str(work), language="en", force=True)

    assert open(out, "rb").read() == old_payload
    assert open(out + ".meta", "rb").read() == old_metadata


def test_metadata_sidecar_is_not_a_transcript_for_pack(tmp_path, monkeypatch):
    from video_studio.edit import pack

    source = tmp_path / "clip.mp4"
    source.write_bytes(b"source")
    work = tmp_path / "work"
    _configure(monkeypatch, _Model())
    out = tr.transcribe_one(str(source), str(work), language="en")
    files = [name for name in os.listdir(os.path.dirname(out)) if name.endswith(".json")]

    packed = pack.pack_dir(os.path.dirname(out), str(work / "packed.md"))
    assert files == ["clip.json"]
    assert packed["sources"] == 1


def test_batch_rejects_same_stem_targets_before_replacing_existing_transcript(
        tmp_path, monkeypatch):
    footage = tmp_path / "footage"
    footage.mkdir()
    first = footage / "clip.mov"
    second = footage / "clip.mp4"
    first.write_bytes(b"first")
    second.write_bytes(b"second")
    work = tmp_path / "work"
    transcripts = work / "transcripts"
    transcripts.mkdir(parents=True)
    existing = transcripts / "clip.json"
    existing.write_text("old transcript", encoding="utf-8")
    model = _Model()
    _configure(monkeypatch, model)

    with pytest.raises(tr.ContractError, match="cùng đường dẫn transcript"):
        tr.transcribe_all(str(footage), str(work))

    assert existing.read_text(encoding="utf-8") == "old transcript"
    assert model.calls == 0


def test_batch_preflight_rejects_same_stem_from_different_directories(
        tmp_path, monkeypatch):
    first = tmp_path / "camera-a" / "clip.mp4"
    second = tmp_path / "camera-b" / "clip.mp4"
    first.parent.mkdir()
    second.parent.mkdir()
    first.write_bytes(b"first")
    second.write_bytes(b"second")
    model = _Model()
    _configure(monkeypatch, model)
    monkeypatch.setattr(tr, "videos_in", lambda _path: [str(first), str(second)])

    with pytest.raises(tr.ContractError, match="cùng đường dẫn transcript"):
        tr.transcribe_all(str(tmp_path), str(tmp_path / "work"))

    assert model.calls == 0


@pytest.mark.skipif(os.name != "nt", reason="Windows paths are case-insensitive")
def test_batch_rejects_windows_casefolded_output_collision(tmp_path, monkeypatch):
    footage = tmp_path / "footage"
    footage.mkdir()
    first = footage / "Clip.mov"
    second = footage / "clip.mp4"
    first.write_bytes(b"first")
    second.write_bytes(b"second")
    model = _Model()
    _configure(monkeypatch, model)

    with pytest.raises(tr.ContractError, match="cùng đường dẫn transcript"):
        tr.transcribe_all(str(footage), str(tmp_path / "work"))

    assert model.calls == 0


def test_output_parent_resolving_outside_work_is_rejected_before_model_load(
        tmp_path, monkeypatch):
    source = tmp_path / "clip.mp4"
    source.write_bytes(b"source")
    work = tmp_path / "work"
    work.mkdir()
    model = _Model()
    _configure(monkeypatch, model)
    real_realpath = os.path.realpath
    output_dir = str(work / "transcripts")
    outside_dir = str(tmp_path / "outside")

    def escape_output_parent(path, *args, **kwargs):
        if os.path.abspath(path) == os.path.abspath(output_dir):
            return outside_dir
        return real_realpath(path, *args, **kwargs)

    monkeypatch.setattr(os.path, "realpath", escape_output_parent)

    with pytest.raises(tr.ContractError, match="symlink/junction"):
        tr.transcribe_one(str(source), str(work), language="en")

    assert model.calls == 0
    assert not (tmp_path / "outside").exists()


@pytest.mark.skipif(os.name != "nt", reason="Windows junction behavior")
def test_real_junction_output_parent_is_rejected_with_bounded_probe(tmp_path):
    powershell = shutil.which("powershell.exe")
    if not powershell:
        pytest.skip("Windows PowerShell is unavailable for the junction fixture")
    work = tmp_path / "work"
    work.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    junction = work / "transcripts"
    junction_literal = str(junction).replace("'", "''")
    outside_literal = str(outside).replace("'", "''")
    command = (f"New-Item -ItemType Junction -Path '{junction_literal}' "
               f"-Target '{outside_literal}' | Out-Null")
    try:
        created = subprocess.run([powershell, "-NoProfile", "-NonInteractive", "-Command", command],
                                 capture_output=True, text=True, timeout=10)
    except subprocess.TimeoutExpired:
        pytest.fail("junction fixture creation exceeded 10 seconds")
    if created.returncode != 0:
        detail = (created.stderr or created.stdout).strip().replace("\r", " ").replace("\n", " ")
        pytest.skip(f"host could not create a temporary junction: {detail[:240]}")
    try:
        probe = """import sys
from video_studio.edit import transcribe as tr
try:
    tr._transcript_dir(sys.argv[1])
except tr.ContractError:
    raise SystemExit(0)
raise SystemExit(4)
"""
        try:
            result = subprocess.run([sys.executable, "-c", probe, str(work)],
                                    capture_output=True, text=True, timeout=10)
        except subprocess.TimeoutExpired:
            pytest.fail("transcript parent junction check exceeded 10 seconds")
        assert result.returncode == 0, result.stderr
    finally:
        os.rmdir(junction)


def test_snapshot_size_limit_fails_before_replacing_old_transcript(tmp_path, monkeypatch):
    source = tmp_path / "clip.mp4"
    source.write_bytes(b"source")
    work = tmp_path / "work"
    output_dir = work / "transcripts"
    output_dir.mkdir(parents=True)
    out = output_dir / "clip.json"
    old_payload = b"old transcript"
    out.write_bytes(old_payload)
    model = _Model()
    _configure(monkeypatch, model)
    monkeypatch.setattr(tr.shutil, "disk_usage", lambda _path: SimpleNamespace(free=4))

    with pytest.raises(tr.ContractError, match="giới hạn.*một nửa"):
        tr.transcribe_one(str(source), str(work), language="en")

    assert out.read_bytes() == old_payload
    assert model.calls == 0


def test_missing_sidecar_is_a_reasoned_legacy_cache_miss(tmp_path, monkeypatch, capsys):
    source = tmp_path / "clip.mp4"
    source.write_bytes(b"source")
    work = tmp_path / "work"
    model = _Model()
    _configure(monkeypatch, model)
    out = tr.transcribe_one(str(source), str(work), language="en")
    os.unlink(out + ".meta")

    tr.transcribe_one(str(source), str(work), language="en")

    assert model.calls == 2
    assert "missing metadata" in capsys.readouterr().err.lower()


def test_source_symlink_fingerprints_target_bytes(tmp_path, monkeypatch):
    target = tmp_path / "real.mp4"
    target.write_bytes(b"target-A")
    source = tmp_path / "clip.mp4"
    try:
        source.symlink_to(target)
    except OSError as exc:
        if os.name == "nt" and getattr(exc, "winerror", None) == 1314:
            pytest.skip("Windows host cannot create symlinks without an elevated privilege")
        raise
    work = tmp_path / "work"
    model = _Model()
    _configure(monkeypatch, model)

    tr.transcribe_one(str(source), str(work), language="en")
    target.write_bytes(b"target-B")
    tr.transcribe_one(str(source), str(work), language="en")

    assert model.calls == 2


def test_symlinked_cache_payload_is_not_followed(tmp_path, monkeypatch):
    source = tmp_path / "clip.mp4"
    source.write_bytes(b"source")
    work = tmp_path / "work"
    _configure(monkeypatch, _Model())
    out_dir = work / "transcripts"
    out_dir.mkdir(parents=True)
    outside = tmp_path / "outside.json"
    outside.write_text('{"text": "outside", "language_code": "en", "words": []}',
                       encoding="utf-8")
    out = out_dir / "clip.json"
    try:
        out.symlink_to(outside)
    except OSError as exc:
        if os.name == "nt" and getattr(exc, "winerror", None) == 1314:
            pytest.skip("Windows host cannot create symlinks without an elevated privilege")
        raise

    tr.transcribe_one(str(source), str(work), language="en")

    assert not out.is_symlink()
    assert json.loads(out.read_text(encoding="utf-8"))["text"] == "hello"
    assert json.loads(outside.read_text(encoding="utf-8"))["text"] == "outside"


def test_cache_path_marked_as_symlink_is_a_miss(tmp_path, monkeypatch):
    source = tmp_path / "clip.mp4"
    source.write_bytes(b"source")
    work = tmp_path / "work"
    model = _Model()
    _configure(monkeypatch, model)
    out = tr.transcribe_one(str(source), str(work), language="en")
    real_islink = os.path.islink
    monkeypatch.setattr(os.path, "islink",
                        lambda path: str(path) == out or real_islink(path))

    tr.transcribe_one(str(source), str(work), language="en")

    assert model.calls == 2


def test_source_change_during_asr_does_not_publish_or_replace_old_output(tmp_path, monkeypatch):
    source = tmp_path / "clip.mp4"
    source.write_bytes(b"source-A")
    work = tmp_path / "work"
    model = _Model()
    _configure(monkeypatch, model)
    out = tr.transcribe_one(str(source), str(work), language="en")
    original_payload = open(out, encoding="utf-8").read()

    def change_source(_wav, **_kwargs):
        source.write_bytes(b"source-B")
        return [_Segment()], _Info()

    monkeypatch.setattr(model, "transcribe", change_source)
    try:
        tr.transcribe_one(str(source), str(work), language="en", force=True)
    except Exception as exc:
        assert "nguồn đổi" in str(exc)
    else:
        raise AssertionError("changed input must not publish a transcript")

    assert open(out, encoding="utf-8").read() == original_payload


def test_interrupted_sidecar_publication_cannot_create_a_false_hit(tmp_path, monkeypatch):
    source = tmp_path / "clip.mp4"
    source.write_bytes(b"source")
    work = tmp_path / "work"
    model = _Model()
    _configure(monkeypatch, model)
    out = tr.transcribe_one(str(source), str(work), language="en")
    old_payload = open(out, encoding="utf-8").read()
    real_replace = os.replace

    def fail_metadata_replace(src, dst):
        if str(dst).endswith(".json.meta"):
            raise OSError("simulated interruption")
        return real_replace(src, dst)

    monkeypatch.setattr(tr.os, "replace", fail_metadata_replace)
    model.text = " changed"
    try:
        tr.transcribe_one(str(source), str(work), language="en", force=True)
    except OSError as exc:
        assert "interruption" in str(exc)
    else:
        raise AssertionError("metadata publication interruption should propagate")
    monkeypatch.setattr(tr.os, "replace", real_replace)

    assert open(out, encoding="utf-8").read() != old_payload
    before = model.calls
    tr.transcribe_one(str(source), str(work), language="en")
    assert model.calls == before + 1


def test_interleaved_writers_with_mixed_generation_force_a_cache_miss(tmp_path, monkeypatch):
    source = tmp_path / "clip.mp4"
    source.write_bytes(b"source")
    work = tmp_path / "work"
    entered = threading.Barrier(2)
    a_payload_done = threading.Event()
    b_payload_done = threading.Event()
    b_metadata_done = threading.Event()
    errors = []

    class ConcurrentModel(_Model):
        def transcribe(self, wav, **kwargs):
            self.calls += 1
            entered.wait(timeout=5)
            segment = _Segment()
            segment.text = " " + threading.current_thread().name
            return [segment], _Info()

    model = ConcurrentModel()
    _configure(monkeypatch, model)
    real_replace = os.replace

    def interleave_replace(src, dst):
        writer = threading.current_thread().name
        is_payload = str(dst).endswith("clip.json")
        if writer == "writer-a" and is_payload:
            real_replace(src, dst)
            a_payload_done.set()
            assert b_metadata_done.wait(timeout=5)
            return
        if writer == "writer-b" and is_payload:
            assert a_payload_done.wait(timeout=5)
            real_replace(src, dst)
            b_payload_done.set()
            return
        if writer == "writer-b" and str(dst).endswith("clip.json.meta"):
            assert b_payload_done.wait(timeout=5)
            real_replace(src, dst)
            b_metadata_done.set()
            return
        if writer == "writer-a" and str(dst).endswith("clip.json.meta"):
            assert b_metadata_done.wait(timeout=5)
        real_replace(src, dst)

    monkeypatch.setattr(tr.os, "replace", interleave_replace)

    def run():
        try:
            tr.transcribe_one(str(source), str(work), language="en")
        except Exception as exc:  # captured so thread failures surface in the test
            errors.append(exc)

    a = threading.Thread(target=run, name="writer-a")
    b = threading.Thread(target=run, name="writer-b")
    a.start()
    b.start()
    b.join(timeout=5)
    a.join(timeout=5)
    assert not a.is_alive() and not b.is_alive()
    assert errors == []

    monkeypatch.setattr(model, "transcribe",
                        lambda wav, **kwargs: _Model.transcribe(model, wav, **kwargs))
    before = model.calls
    tr.transcribe_one(str(source), str(work), language="en")
    # The forced A-payload/B-payload/B-meta/A-meta schedule leaves a torn pair.
    assert model.calls == before + 1
