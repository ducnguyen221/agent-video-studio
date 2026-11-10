"""CLI exposes only the declared-asset check, never runtime verification."""
import json

from video_studio.reference import gate
from video_studio.reference import main


def test_lyric_audit_cli_checks_audio_and_fails_on_unlisted_file(tmp_path, capsys):
    media = tmp_path / "composition" / "media"
    media.mkdir(parents=True)
    (tmp_path / "source").mkdir()
    (tmp_path / "source" / "sample.mp4").write_bytes(b"sample")
    (media / "audio.wav").write_bytes(b"audio")
    provenance = gate.new_provenance("example", None, None, gate.sha256_file(str(tmp_path / "source" / "sample.mp4")), "2026-01-01")
    provenance["assets"] = [{"path": "composition/media/audio.wav", "origin": "user", "owner": "owner"}]
    gate.save_provenance(str(tmp_path), provenance)
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"audio": "composition/media/audio.wav", "assets": []}), encoding="utf-8")
    args = ["lyric-audit", "--project", str(tmp_path), "--manifest", str(manifest), "--json"]
    assert main(args) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["coverage"] == "declared_only"
    (media / "unlisted.png").write_bytes(b"unlisted")
    assert main(args) == 2


def test_lyric_audit_bad_manifest_is_contract_error(tmp_path, capsys):
    manifest = tmp_path / "bad.json"
    manifest.write_text("{", encoding="utf-8")
    assert main(["lyric-audit", "--project", str(tmp_path), "--manifest", str(manifest), "--json"]) == 2
    assert json.loads(capsys.readouterr().out)["ok"] is False
