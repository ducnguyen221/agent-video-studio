"""Bounded checks for media explicitly consumed by a declarative lyric renderer."""
import pytest

from video_studio.contract import ContractError
from video_studio.reference import gate


@pytest.fixture
def project(tmp_path):
    media = tmp_path / "composition" / "media"
    media.mkdir(parents=True)
    (tmp_path / "source").mkdir()
    (tmp_path / "source" / "sample.mp4").write_bytes(b"source")
    (media / "audio.wav").write_bytes(b"new audio")
    (media / "cover.png").write_bytes(b"new cover")
    prov = gate.new_provenance("test", None, None, None, "2026-01-01")
    prov["reference"]["sha256"] = gate.sha256_file(str(tmp_path / "source" / "sample.mp4"))
    prov["assets"] = [
        {"path": "composition/media/audio.wav", "origin": "user", "owner": "tester"},
        {"path": "composition/media/cover.png", "origin": "user", "owner": "tester"},
    ]
    gate.save_provenance(str(tmp_path), prov)
    return tmp_path


@pytest.fixture
def manifest():
    return {"audio": "composition/media/audio.wav", "assets": ["composition/media/cover.png"]}


def test_prepare_and_recheck(project, manifest):
    from video_studio.reference import lyric_guard
    snapshot = lyric_guard.prepare(project, manifest)
    assert lyric_guard.verify_snapshot(project, manifest, snapshot) is None
    (project / "composition/media/audio.wav").write_bytes(b"modified")
    with pytest.raises(ContractError):
        lyric_guard.verify_snapshot(project, manifest, snapshot)


@pytest.mark.parametrize("change", [
    {"audio": "../outside.wav", "assets": []},
    {"audio": "composition/media/audio.wav", "assets": []},
    {"audio": "composition/media/audio.wav", "assets": ["composition/media/cover.png", "composition/media/cover.png"]},
    {"audio": "composition/media/audio.wav", "assets": ["composition/media/cover.png"], "script": "x"},
])
def test_manifest_must_be_closed_and_cover_all_assets(project, change):
    from video_studio.reference import lyric_guard
    with pytest.raises(ContractError):
        lyric_guard.prepare(project, change)


def test_reference_duplicate_and_undeclared_file_rejected(project, manifest):
    from video_studio.reference import lyric_guard
    (project / "composition/media/cover.png").write_bytes(b"source")
    with pytest.raises(ContractError):
        lyric_guard.prepare(project, manifest)
    (project / "composition/media/cover.png").write_bytes(b"new cover")
    (project / "composition/media/unlisted.png").write_bytes(b"extra")
    with pytest.raises(ContractError):
        lyric_guard.prepare(project, manifest)


def test_symlink_and_manifest_change_rejected(project, manifest):
    from video_studio.reference import lyric_guard
    snapshot = lyric_guard.prepare(project, manifest)
    with pytest.raises(ContractError):
        lyric_guard.verify_snapshot(project, {"audio": manifest["audio"], "assets": []}, snapshot)
    cover = project / "composition/media/cover.png"
    cover.unlink()
    try:
        cover.symlink_to(project / "composition/media/audio.wav")
    except OSError:
        pytest.skip("symlink creation unavailable")
    with pytest.raises(ContractError):
        lyric_guard.prepare(project, manifest)


def test_missing_and_empty_media_rejected(project, manifest):
    from video_studio.reference import lyric_guard
    (project / "composition/media/cover.png").unlink()
    with pytest.raises(ContractError):
        lyric_guard.prepare(project, manifest)
    (project / "composition/media/audio.wav").unlink()
    with pytest.raises(ContractError):
        lyric_guard.prepare(project, manifest)


def test_provenance_change_invalidates_snapshot(project, manifest):
    from video_studio.reference import lyric_guard
    snapshot = lyric_guard.prepare(project, manifest)
    prov = gate.load_provenance(str(project))
    prov["assets"][0]["owner"] = "different"
    gate.save_provenance(str(project), prov)
    with pytest.raises(ContractError):
        lyric_guard.verify_snapshot(project, manifest, snapshot)


def test_source_file_instead_of_directory_fails_closed(project, manifest):
    from video_studio.reference import lyric_guard
    source = project / "source"
    (source / "sample.mp4").unlink()
    source.rmdir()
    source.write_bytes(b"a hidden source")
    with pytest.raises(ContractError):
        lyric_guard.prepare(project, manifest)


def test_source_walk_error_fails_closed(project, manifest, monkeypatch):
    from video_studio.reference import lyric_guard
    real_walk = gate.os.walk

    def failing_walk(path, *args, **kwargs):
        if str(path) == str(project / "source"):
            callback = kwargs.get("onerror")
            if callback:
                callback(PermissionError("denied"))
            return iter(())
        return real_walk(path, *args, **kwargs)

    monkeypatch.setattr(gate.os, "walk", failing_walk)
    with pytest.raises(ContractError):
        lyric_guard.prepare(project, manifest)


def test_nested_link_in_source_fails_closed(project, manifest, monkeypatch):
    from video_studio.reference import lyric_guard
    nested = project / "source" / "nested"
    nested.mkdir()
    original = gate._is_link
    monkeypatch.setattr(gate, "_is_link", lambda path: str(path) == str(nested) or original(path))
    with pytest.raises(ContractError):
        lyric_guard.prepare(project, manifest)


def test_missing_reference_evidence_cannot_be_audited(project, manifest):
    from video_studio.reference import lyric_guard
    (project / "source" / "sample.mp4").unlink()
    prov = gate.load_provenance(str(project))
    prov["reference"]["sha256"] = None
    gate.save_provenance(str(project), prov)
    with pytest.raises(ContractError):
        lyric_guard.prepare(project, manifest)


def test_recorded_reference_hash_can_supply_reference_evidence(project, manifest):
    from video_studio.reference import lyric_guard
    (project / "source" / "sample.mp4").unlink()
    prov = gate.load_provenance(str(project))
    prov["reference"]["sha256"] = "ab" * 32
    gate.save_provenance(str(project), prov)
    assert lyric_guard.prepare(project, manifest)["scope"] == "declared_only"


def test_unrelated_evidence_cannot_replace_reference_hash(project, manifest):
    from video_studio.reference import lyric_guard
    (project / "source" / "sample.mp4").unlink()
    (project / "evidence").mkdir()
    (project / "evidence" / "unrelated.txt").write_text("not the source video")
    prov = gate.load_provenance(str(project))
    prov["reference"]["sha256"] = None
    gate.save_provenance(str(project), prov)
    with pytest.raises(ContractError):
        lyric_guard.prepare(project, manifest)
