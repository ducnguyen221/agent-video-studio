"""Write verified UTF-8 lyrics to a new MP3 copy; requires Mutagen."""
import argparse
import hashlib
import os
from pathlib import Path
import shutil
import tempfile

from mutagen.id3 import ID3, ID3NoHeaderError, USLT
from mutagen.mp3 import MP3, HeaderNotFoundError


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest() if hasattr(hashlib, 'file_digest') else _digest_stream(stream)


def _digest_stream(stream):
    result = hashlib.sha256()
    for block in iter(lambda: stream.read(1024 * 1024), b''):
        result.update(block)
    return result.hexdigest()


def payload_digest(path):
    # Mutagen rewrites only the leading ID3v2 tag. Compare all remaining bytes,
    # including MPEG data and any trailing tags; no decoding or bitrate assumptions.
    with path.open('rb') as stream:
        header = stream.read(10)
        if header[:3] == b'ID3':
            if len(header) != 10 or any(byte & 0x80 for byte in header[6:10]):
                raise ValueError('Invalid ID3 header')
            size = sum(header[6 + i] << (7 * (3 - i)) for i in range(4))
            stream.seek(10 + size + (10 if header[5] & 0x10 else 0))
        else:
            stream.seek(0)
        return _digest_stream(stream)


def tags(path):
    try:
        return ID3(path)
    except ID3NoHeaderError:
        return ID3()


def fingerprint(frames, excluded):
    return sorted((frame.HashKey, repr(frame)) for frame in frames.values() if frame.HashKey != excluded)


def write_verified(source, output, lyrics, lang, description):
    source, output = Path(source).resolve(), Path(output).resolve()
    if source == output or output.exists():
        raise ValueError('Output must be a new file distinct from source')
    if len(lang) != 3 or not lang.isascii() or not lang.isalpha():
        raise ValueError('Language must be three ASCII letters')
    if not lyrics.strip():
        raise ValueError('Lyrics must not be empty')
    try:
        MP3(source)
    except HeaderNotFoundError as error:
        raise ValueError('Source is not a recognized MP3') from error
    before, audio = digest(source), payload_digest(source)
    original = tags(source)
    if original.unknown_frames:
        raise ValueError('Unknown ID3 frames cannot be safely preserved')
    key = USLT(encoding=3, lang=lang, desc=description, text=lyrics).HashKey
    preserved = fingerprint(original, key)
    fd, name = tempfile.mkstemp(prefix='.lyric-', suffix='.mp3', dir=output.parent)
    os.close(fd)
    temporary = Path(name)
    try:
        shutil.copyfile(source, temporary)
        updated = tags(temporary)
        updated.add(USLT(encoding=3, lang=lang, desc=description, text=lyrics))
        updated.save(temporary, v2_version=4)
        reread = tags(temporary)
        if reread.unknown_frames:
            raise ValueError('Unexpected unknown ID3 frames; output not published')
        if key not in reread or str(reread[key].text) != lyrics:
            raise ValueError('USLT read-back failed')
        if fingerprint(reread, key) != preserved:
            raise ValueError('Other ID3 frames changed; output not published')
        if payload_digest(temporary) != audio or digest(source) != before:
            raise ValueError('Source or audio payload changed; output not published')
        # Hard link publishes atomically without overwriting an existing destination.
        os.link(temporary, output)
        return {'source_sha256': before, 'payload_sha256': audio, 'output_sha256': digest(output), 'language': lang, 'description': description}
    finally:
        temporary.unlink(missing_ok=True)


def main():
    import json
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('lyrics', type=Path, help='Verified UTF-8 text file')
    parser.add_argument('--lang', required=True)
    parser.add_argument('--description', default='')
    args = parser.parse_args()
    print(json.dumps(write_verified(args.source, args.output, args.lyrics.read_text(encoding='utf-8'), args.lang, args.description), ensure_ascii=False))


if __name__ == '__main__':
    main()
