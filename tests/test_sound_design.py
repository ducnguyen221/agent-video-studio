import hashlib
from pathlib import Path
import pytest
from video_studio.sound_design import approved_cues, search_openverse, asset_revision


def fixture(tmp_path):
    raw = b"RIFF" + b"\x04\x00\x00\x00" + b"WAVE"
    (tmp_path / "fx.wav").write_bytes(raw)
    asset = dict(id="a", path="fx.wav", sha256=hashlib.sha256(raw).hexdigest(), purpose="video", source_evidence="https://example.org/source", creator="  Test Creator  ", license="cc-by", license_version="4.0", license_url="https://example.org/license", rights_status="attributed", attribution_required=True, attribution="creator")
    cue = dict(id="c", asset_id="a", status="approved", timeline_seconds=1, in_seconds=0, duration_seconds=.2)
    cue["asset_revision"] = asset_revision(asset)
    return cue, asset


def test_approval_and_changed_file(tmp_path):
    cue, asset = fixture(tmp_path)
    assert len(approved_cues(tmp_path, [cue], [asset])) == 1
    (tmp_path / "fx.wav").write_bytes(b"RIFFxxxxWAVEchanged")
    with pytest.raises(ValueError, match="changed"):
        approved_cues(tmp_path, [cue], [asset])


def test_missing_attribution_and_fake_wav(tmp_path):
    cue, asset = fixture(tmp_path)
    asset["attribution"] = ""
    cue["asset_revision"] = asset_revision(asset)
    with pytest.raises(ValueError, match="attribution"):
        approved_cues(tmp_path, [cue], [asset])
    asset["attribution"] = "creator"
    cue["asset_revision"] = asset_revision(asset)
    (tmp_path / "fx.wav").write_text("#EXTM3U\nhttps://example.org/a")
    with pytest.raises(ValueError, match="RIFF"):
        approved_cues(tmp_path, [cue], [asset])


def test_rejected_cue_is_not_mixed(tmp_path):
    cue, asset = fixture(tmp_path)
    cue["status"] = "rejected"
    assert approved_cues(tmp_path, [cue], [asset]) == []


def test_search_rejects_unbounded_input():
    with pytest.raises(ValueError):
        search_openverse("sound", page=6)


def test_search_metadata_and_oversize(monkeypatch):
    import json
    import video_studio.sound_design as sound
    class Response:
        def __init__(self, raw): self.raw = raw
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def read(self, limit): return self.raw[:limit]
    class Opener:
        raw = json.dumps({"results": [{"title": "<script>x</script>", "id": "1"}]}).encode()
        def open(self, request, timeout):
            assert request.full_url.startswith(sound.ENDPOINT)
            return Response(self.raw)
    opener = Opener()
    monkeypatch.setattr(sound.urllib.request, "build_opener", lambda *a: opener)
    assert sound.search_openverse("wind")[0]["title"] == "<script>x</script>"
    opener.raw = b"x" * (sound.MAX_BODY + 1)
    with pytest.raises(ValueError, match="too large"):
        sound.search_openverse("wind")


def test_redirect_is_refused():
    import video_studio.sound_design as sound
    with pytest.raises(ValueError, match="redirect"):
        sound._NoRedirect().redirect_request(None, None, 302, "", {}, "http://localhost/")


def test_provider_markup_escaped():
    from video_studio.sound_design import escape_provider_text
    result = escape_provider_text('<script>[x](https://bad)</script>')
    assert '<script>' not in result and '[x]' not in result and '(https' not in result


def test_mix_mux_smoke(tmp_path, monkeypatch):
    import shutil
    import subprocess
    import wave
    import math
    import struct
    from video_studio.sound_design import mix_mux
    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        pytest.skip("ffmpeg not available")
    for name, hz in (("master.wav", 220), ("fx.wav", 1200)):
        with wave.open(str(tmp_path / name), "wb") as f:
            f.setparams((1, 2, 8000, 8000 * 2, "NONE", "not compressed"))
            f.writeframes(b"".join(struct.pack("<h", int(3000 * math.sin(2 * math.pi * hz * n / 8000))) for n in range(16000)))
    video = tmp_path / "video.mp4"
    subprocess.run([ffmpeg, "-v", "error", "-f", "lavfi", "-i", "color=s=64x64:r=25:d=2", "-c:v", "mpeg4", str(video)], check=True)
    cue, asset = fixture(tmp_path)
    # fixture creates the minimal header; restore a real WAV.
    with wave.open(str(tmp_path / "fx.wav"), "wb") as f:
        f.setparams((1, 2, 8000, 8000, "NONE", "not compressed"))
        f.writeframes(b"".join(struct.pack("<h", int(3000 * math.sin(2 * math.pi * 1200 * n / 8000))) for n in range(8000)))
    asset["sha256"] = hashlib.sha256((tmp_path / "fx.wav").read_bytes()).hexdigest()
    source_hash = hashlib.sha256((tmp_path / "master.wav").read_bytes()).hexdigest()
    cue["asset_revision"] = asset_revision(asset)
    cue.update(fade_in=.02, fade_out=.02)
    import video_studio.sound_design as sound
    with monkeypatch.context() as patch:
        patch.setattr(sound, "MAX_TEMP_BYTES", 10)
        with pytest.raises(ValueError, match="temporary total"):
            mix_mux(tmp_path, video, tmp_path / "master.wav", tmp_path / "oversize.mp4", [cue], [asset], ffmpeg=ffmpeg)
    excessive = [dict(cue, id=str(i)) for i in range(sound.MAX_CUES + 1)]
    with pytest.raises(ValueError, match="too many cues"):
        approved_cues(tmp_path, excessive, [asset])
    result = mix_mux(tmp_path, video, tmp_path / "master.wav", tmp_path / "out.mp4", [cue], [asset], ffmpeg=ffmpeg)
    assert result.stat().st_size > 0
    import json
    probe = shutil.which("ffprobe")
    metadata = json.loads(subprocess.check_output([probe, "-v", "error", "-show_entries", "format_tags=comment", "-of", "json", str(result)]))
    assert metadata["format"]["tags"]["comment"].startswith("Test Creator | creator |")
    private_asset = dict(asset, source_type="user_provided", source_evidence="PRIVATE_CONTRACT_123", rights_confirmation="PRIVATE_AUTHORIZATION_456", attribution="Public Credit", rights_status="attributed", attribution_required=True)
    private_cue = dict(cue, asset_revision=asset_revision(private_asset))
    private_out = mix_mux(tmp_path, video, tmp_path / "master.wav", tmp_path / "private.mp4", [private_cue], [private_asset], ffmpeg=ffmpeg)
    private_metadata = json.loads(subprocess.check_output([probe, "-v", "error", "-show_entries", "format_tags=comment", "-of", "json", str(private_out)]))
    comment = private_metadata["format"]["tags"]["comment"]
    assert comment == "Test Creator | Public Credit"
    assert "PRIVATE_CONTRACT_123" not in comment and "PRIVATE_AUTHORIZATION_456" not in comment
    too_long = dict(cue, in_seconds=.9, duration_seconds=.2)
    with pytest.raises(ValueError, match="asset duration"):
        mix_mux(tmp_path, video, tmp_path / "master.wav", tmp_path / "bad.mp4", [too_long], [asset], ffmpeg=ffmpeg)
    too_late = dict(cue, timeline_seconds=1.9, duration_seconds=.2)
    with pytest.raises(ValueError, match="master or video duration"):
        mix_mux(tmp_path, video, tmp_path / "master.wav", tmp_path / "late.mp4", [too_late], [asset], ffmpeg=ffmpeg)
    decoded = subprocess.check_output([ffmpeg, "-v", "error", "-i", str(result), "-map", "0:a:0", "-f", "s16le", "-ac", "1", "-ar", "8000", "-"])
    assert len(decoded) >= 2 * 8000 * 1.98
    bad_master = tmp_path / "truncated.wav"
    bad_master.write_bytes((tmp_path / "master.wav").read_bytes()[:-500])
    with pytest.raises(ValueError, match="truncated PCM"):
        mix_mux(tmp_path, video, bad_master, tmp_path / "truncated.mp4", [cue], [asset], ffmpeg=ffmpeg)
    samples = struct.unpack("<" + "h" * (len(decoded) // 2), decoded)
    def strength(start, end, hz):
        values = samples[int(start * 8000):int(end * 8000)]
        return abs(sum(v * complex(math.cos(2 * math.pi * hz * i / 8000), -math.sin(2 * math.pi * hz * i / 8000)) for i, v in enumerate(values))) / len(values)
    assert strength(1.03, 1.15, 1200) > 5 * strength(.7, .85, 1200)
    assert max(abs(v) for v in samples) < 32767
    assert hashlib.sha256((tmp_path / "master.wav").read_bytes()).hexdigest() == source_hash
    cue["status"] = "rejected"
    control = mix_mux(tmp_path, video, tmp_path / "master.wav", tmp_path / "control.mp4", [cue], [asset], ffmpeg=ffmpeg)
    control_bytes = subprocess.check_output([ffmpeg, "-v", "error", "-i", str(control), "-map", "0:a:0", "-f", "s16le", "-ac", "1", "-ar", "8000", "-"])
    ref = struct.unpack("<" + "h" * (len(control_bytes) // 2), control_bytes)
    assert len(ref) >= 8000 * 1.98 and abs(len(samples) - len(ref)) <= 1
    assert max(abs(v) for v in samples[int(1.9 * 8000):int(1.95 * 8000)]) > 100
    for start, end in ((.2, .7), (1.5, 1.8), (1.9, 1.95)):
        left, right = int(start * 8000), int(end * 8000)
        rms = math.sqrt(sum((a-b)**2 for a,b in zip(samples[left:right], ref[left:right])) / (right-left))
        assert rms < 150
    def control_strength(start, end, hz):
        values = ref[int(start * 8000):int(end * 8000)]
        return abs(sum(v * complex(math.cos(2 * math.pi * hz * i / 8000), -math.sin(2 * math.pi * hz * i / 8000)) for i, v in enumerate(values))) / len(values)
    assert strength(1.03, 1.15, 1200) > 5 * control_strength(1.03, 1.15, 1200)
    # The SFX is absent in the frame before onset and present in the next frame.
    assert strength(.96, 1.0, 1200) < strength(1.0, 1.04, 1200) * .35
    assert strength(1.0, 1.04, 1200) > control_strength(1.0, 1.04, 1200) * 5
    cue.update(status="approved", gain_db=-96, ducking_db=-6.0206, fade_in=0, fade_out=0)
    second = dict(cue, id="c2")
    ducked = mix_mux(tmp_path, video, tmp_path / "master.wav", tmp_path / "ducked.mp4", [cue, second], [asset], ffmpeg=ffmpeg)
    duck_bytes = subprocess.check_output([ffmpeg, "-v", "error", "-i", str(ducked), "-map", "0:a:0", "-f", "s16le", "-ac", "1", "-ar", "8000", "-"])
    duck_samples = struct.unpack("<" + "h" * (len(duck_bytes) // 2), duck_bytes)
    def project(values, start, end, hz):
        values = values[int(start * 8000):int(end * 8000)]
        return abs(sum(v * complex(math.cos(2 * math.pi * hz * i / 8000), -math.sin(2 * math.pi * hz * i / 8000)) for i, v in enumerate(values))) / len(values)
    excessive_duck = [dict(cue, id="x", ducking_db=-40), dict(cue, id="y", ducking_db=-40)]
    with pytest.raises(ValueError, match="overlapping ducking"):
        mix_mux(tmp_path, video, tmp_path / "master.wav", tmp_path / "too-ducked.mp4", excessive_duck, [asset], ffmpeg=ffmpeg)
    ratio = project(duck_samples, 1.07, 1.13, 220) / project(ref, 1.07, 1.13, 220)
    assert .15 < ratio < .4


def test_attribution_cannot_be_silently_waived(tmp_path):
    cue, asset = fixture(tmp_path)
    del asset['attribution_required']
    cue['asset_revision'] = asset_revision(asset)
    with pytest.raises(ValueError, match='unknown'):
        approved_cues(tmp_path, [cue], [asset])
    asset['attribution_required'] = False
    cue['asset_revision'] = asset_revision(asset)
    with pytest.raises(ValueError, match='requires attribution'):
        approved_cues(tmp_path, [cue], [asset])


def test_asset_size_limit(tmp_path, monkeypatch):
    import video_studio.sound_design as sound
    cue, asset = fixture(tmp_path)
    monkeypatch.setattr(sound, 'MAX_ASSET_BYTES', 11)
    # header itself exceeds the cap even with no remaining chunks
    (tmp_path / 'fx.wav').write_bytes(b'RIFFxxxxWAVEextra')
    with pytest.raises(ValueError, match='too large'):
        approved_cues(tmp_path, [cue], [asset])


def test_ledger_change_invalidates_approval(tmp_path):
    cue, asset = fixture(tmp_path)
    asset['source_evidence'] = 'https://example.org/new-source'
    with pytest.raises(ValueError, match='changed since cue approval'):
        approved_cues(tmp_path, [cue], [asset])


def test_search_http_and_offline_errors(monkeypatch):
    import urllib.error
    import video_studio.sound_design as sound
    class Opener:
        def __init__(self, error): self.error = error
        def open(self, request, timeout): raise self.error
    for error, expected in ((urllib.error.HTTPError('https://api.openverse.org', 429, 'limited', {}, None), 'HTTP 429'), (urllib.error.URLError('offline'), 'network error')):
        monkeypatch.setattr(sound.urllib.request, 'build_opener', lambda *a: Opener(error))
        with pytest.raises(ValueError, match=expected):
            search_openverse('wind')


def test_storyboard_approval_and_no_sfx(tmp_path):
    import json
    data = json.loads((Path(__file__).parent / 'fixtures' / 'sound-storyboard.json').read_text(encoding='utf-8-sig'))
    cue, asset = fixture(tmp_path)
    proposed = data['sfx_cues'][0]
    rejected = data['sfx_cues'][1]
    assert proposed['scene_id'] == data['scenes'][0]['id'] and proposed['lyric_cue_id'] == 'lyric-1'
    assert data['no_sfx'][0]['scene_id'] == data['scenes'][1]['id']
    assert approved_cues(tmp_path, [proposed, rejected], [asset]) == []
    proposed.update(status='approved', asset_revision=asset_revision(asset))
    assert len(approved_cues(tmp_path, [proposed, rejected], [asset])) == 1
    proposed['asset_id'] = 'missing'
    with pytest.raises(KeyError):
        approved_cues(tmp_path, [proposed], [asset])


def test_user_provided_rights_without_fabricated_license(tmp_path):
    cue, asset = fixture(tmp_path)
    asset.update(source_type="user_provided", source_evidence="recorded by provider", rights_confirmation="owner authorized video use", rights_status="verified", attribution_required=False)
    for key in ("license", "license_version", "license_url", "attribution"):
        asset.pop(key)
    cue["asset_revision"] = asset_revision(asset)
    assert len(approved_cues(tmp_path, [cue], [asset])) == 1
    asset["rights_confirmation"] = "   "
    cue["asset_revision"] = asset_revision(asset)
    with pytest.raises(ValueError, match="rights confirmation"):
        approved_cues(tmp_path, [cue], [asset])
