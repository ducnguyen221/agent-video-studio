import importlib.util
import base64
from pathlib import Path

import pytest
pytest.importorskip('mutagen')
from mutagen.id3 import APIC, ID3, TIT2, USLT

MODULE = Path(__file__).resolve().parents[1] / 'skills/hyperframes/music-to-video/assets/write_uslt.py'
spec = importlib.util.spec_from_file_location('write_uslt', MODULE)
writer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(writer)


def fixture(path):
    encoded = Path(__file__).parent / 'fixtures/lyric-project/media/synthetic.mp3.b64'
    path.write_bytes(base64.b64decode(encoded.read_bytes(), validate=False))
    tag = ID3()
    tag.add(TIT2(encoding=3, text='Tiêu đề'))
    tag.add(APIC(encoding=3, mime='image/png', type=3, desc='cover', data=b'fake image'))
    tag.add(USLT(encoding=3, lang='vie', desc='main', text='lời cũ'))
    tag.add(USLT(encoding=3, lang='eng', desc='other', text='other'))
    tag.save(path)


def test_roundtrip_preserves_source_payload_and_other_frames(tmp_path):
    source, output = tmp_path / 'source.mp3', tmp_path / 'copy.mp3'
    fixture(source)
    before = source.read_bytes()
    result = writer.write_verified(source, output, 'Mùa xuân\nđã đến', 'vie', 'main')
    assert source.read_bytes() == before
    tag = ID3(output)
    assert tag['USLT:main:vie'].text == 'Mùa xuân\nđã đến'
    assert tag['USLT:other:eng'].text == 'other'
    assert tag['APIC:cover'].data == b'fake image'
    assert writer.payload_digest(source) == writer.payload_digest(output) == result['payload_sha256']


def test_failure_does_not_publish_or_change_source(tmp_path, monkeypatch):
    source, output = tmp_path / 'source.mp3', tmp_path / 'copy.mp3'
    fixture(source)
    before = source.read_bytes()
    monkeypatch.setattr(writer, 'payload_digest', lambda path: str(path))
    with pytest.raises(ValueError, match='payload'):
        writer.write_verified(source, output, 'đúng', 'vie', 'main')
    assert not output.exists()
    assert source.read_bytes() == before
    assert not list(tmp_path.glob('.lyric-*'))
    with pytest.raises(ValueError):
        writer.write_verified(source, source, 'đúng', 'vie', 'main')


def test_rejects_invalid_mp3_and_unknown_id3_without_publishing(tmp_path):
    source, output = tmp_path / 'source.mp3', tmp_path / 'copy.mp3'
    source.write_bytes(b'not an mp3')
    with pytest.raises(ValueError, match='MP3'):
        writer.write_verified(source, output, 'lời', 'vie', 'main')
    assert not output.exists()
    fixture(source)
    # ID3v2.3 unrecognized frame; force a valid raw tag around MPEG bytes.
    raw = source.read_bytes()
    size = sum(raw[6 + i] << (7 * (3 - i)) for i in range(4))
    payload = raw[10 + size:]
    frame = b'ZZZZ' + (4).to_bytes(4, 'big') + b'\x00\x00data'
    source.write_bytes(b'ID3\x03\x00\x00\x00\x00\x00' + bytes([len(frame)]) + frame + payload)
    before = source.read_bytes()
    assert writer.tags(source).unknown_frames
    with pytest.raises(ValueError, match='Unknown ID3'):
        writer.write_verified(source, output, 'lời', 'vie', 'main')
    assert source.read_bytes() == before and not output.exists()
