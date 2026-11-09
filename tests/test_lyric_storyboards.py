import json
from pathlib import Path


def test_storyboard_options_resolve_from_different_cwd(tmp_path, monkeypatch):
    root = Path(__file__).resolve().parent / 'fixtures' / 'lyric-project'
    data = json.loads((root / 'storyboards.json').read_text(encoding='utf-8-sig'))
    monkeypatch.chdir(tmp_path)
    assets = {item['id']: item for item in data['assets']}
    cues = {item['id']: item for item in data['cues']}
    assert len(assets) == len(data['assets']) and len(cues) == len(data['cues'])
    assert data['missing_before_render']
    for relative in [data['audio']['path'], data['runtime'], *data['compositions'].values()]:
        path = (root / relative).resolve()
        assert path.is_relative_to(root.resolve()) and path.is_file()
    for name, relative in data['compositions'].items():
        html = (root / relative).read_text(encoding='utf-8')
        assert 'data-composition-id="master"' in html and 'window.__timelines.master' in html
        assert 'media/still.svg' in html
        assert ('media/second.svg' in html) == (name == 'multishot')
    for asset in assets.values():
        path = (root / asset['path']).resolve()
        assert path.is_relative_to(root.resolve()) and path.is_file()
    for cue in cues.values():
        assert 0 <= cue['start'] <= cue['sung_end'] <= cue['end']
        assert cue['text_status'] == cue['timing_status'] == 'unverified'
    for rows in data['options'].values():
        assert {row['cue'] for row in rows} == set(cues)
        for row in rows:
            assert row['asset'] in assets and cues[row['cue']]['segment'] == row['segment']
    assert [cue['text'] for cue in cues.values()] == ['Ánh sáng', 'Ánh sáng']
