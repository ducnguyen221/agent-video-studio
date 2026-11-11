import json

from video_studio.effect_library import __main__ as cli


def test_cli_long_prompt_is_marked_and_full_prompt_is_recoverable(monkeypatch, capsys):
    prompt = 'Tiếng Việt 🎬 ' * 300
    rows = [{'id': 'VE-prompt', 'prompt_text': prompt, 'meta': {'keep': 1}}, {'id': 'VE-reference', 'name': 'Reference'}]
    monkeypatch.setattr(cli, 'search', lambda *a, **k: rows)
    assert cli.main(['--q', 'video']) == 0
    summary = json.loads(capsys.readouterr().out)
    assert summary[0]['entry']['prompt_text'] == prompt[:240]
    assert summary[0]['prompt_text_truncated'] is True
    assert summary[0]['prompt_text_chars'] == len(prompt)
    assert '--full-prompt' in summary[0]['retrieve']
    assert summary[1]['entry'] == rows[1]
    assert summary[1]['prompt_text_truncated'] is False
    assert rows[0]['prompt_text'] == prompt
    assert cli.main(['--q', 'video', '--full-prompt']) == 0
    full = json.loads(capsys.readouterr().out)
    assert full[0]['entry']['prompt_text'] == prompt
    assert 'meta' in full[0]['omitted_fields']
    assert cli.main(['--q', 'video', '--full-record']) == 0
    assert [row['entry'] for row in json.loads(capsys.readouterr().out)] == rows
    assert all(not row['prompt_text_truncated'] for row in full)


def test_cli_short_prompt_unmodified(monkeypatch, capsys):
    rows = [{'id': 'VE-prompt', 'prompt_text': 'Mẫu ngắn'}]
    monkeypatch.setattr(cli, 'search', lambda *a, **k: rows)
    assert cli.main([]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result[0]['entry'] == rows[0]
    assert not result[0]['prompt_text_truncated']


def test_cli_metadata_collision_is_preserved_and_filter_is_forwarded(monkeypatch, capsys):
    row = {'id': 'VE-x', 'prompt_text': 'x' * 241, 'prompt_text_truncated': 'source metadata'}
    seen = {}

    def fake_search(query, filters, **kwargs):
        seen.update(query=query, filters=filters)
        return [row]

    monkeypatch.setattr(cli, 'search', fake_search)
    assert cli.main(['--q', 'x', '--rights', 'owned']) == 0
    result = json.loads(capsys.readouterr().out)[0]
    assert 'prompt_text_truncated' in result['omitted_fields']
    assert seen['filters']['rights'] == 'owned'
    assert cli.main(['--full-record']) == 0
    assert json.loads(capsys.readouterr().out)[0]['entry']['prompt_text_truncated'] == 'source metadata'
    assert result['prompt_text_truncated'] is True


def test_cli_invalid_check_still_reports_error(capsys):
    assert cli.main(['--check', 'render=bogus']) == 2
    assert 'evidence filter' in capsys.readouterr().err


def test_real_station_prompt_round_trip_is_compact(tmp_path, capsys):
    import os
    import pytest
    from video_studio.effect_library import capture
    if os.name != 'nt':
        pytest.skip('secure station writes are Windows-only')
    project = tmp_path / 'project'
    project.mkdir()
    station = tmp_path / 'station'
    (station / 'effect-library' / 'entries').mkdir(parents=True)
    prompt = 'đèn lung linh 🎬 ' * 5000
    item = {'id': 'VE-long-prompt-test', 'name': 'synthetic long prompt', 'kind': 'prompt',
            'maturity': 'candidate', 'rights': 'owned', 'source': 'synthetic original',
            'runtime': 'text', 'tags': ['synthetic-prompt-unique'], 'roles': [], 'techniques': [],
            'ratios': [], 'checks': dict.fromkeys(('static_check', 'preview', 'render', 'audio', 'ratio_test', 'reuse_evidence'), 'not_run'),
            'asset': None, 'prompt_text': prompt, 'description': 'd' * 500000,
            'custom': 'real synthetic metadata'}
    capture(project, station, item)
    assert cli.main(['--station', str(station), '--q', 'synthetic-prompt-unique']) == 0
    summarized = json.loads(capsys.readouterr().out)[0]
    assert summarized['entry']['id'] == item['id']
    assert summarized['entry']['prompt_text'] == prompt[:240]
    assert summarized['prompt_text_truncated']
    assert len(summarized['entry']['description']) == 240
    assert 'description' in summarized['truncated_fields']
    assert 'custom' in summarized['omitted_fields']
    assert cli.main(['--station', str(station), '--q', 'synthetic-prompt-unique', '--full-prompt']) == 0
    expanded = json.loads(capsys.readouterr().out)[0]
    assert expanded['entry']['prompt_text'] == prompt
    assert not expanded['prompt_text_truncated']
    assert cli.main(['--station', str(station), '--q', 'synthetic-prompt-unique', '--full-record']) == 0
    complete = json.loads(capsys.readouterr().out)[0]['entry']
    assert complete['description'] == item['description']
    assert complete['custom'] == item['custom']


def test_summary_bounds_description_lists_and_reports_hidden_fields(monkeypatch, capsys):
    row = {'id': 'VE-large', 'kind': 'component', 'rights': 'unknown', 'source': 'synthetic',
           'runtime': 'js', 'checks': {'render': 'not_run'}, 'description': 'D' * 500000,
           'tags': [f'tag-{i}' for i in range(10000)], 'private_extension': 'M' * 500000}
    monkeypatch.setattr(cli, 'search', lambda *a, **k: [row])
    assert cli.main([]) == 0
    output = capsys.readouterr().out
    result = json.loads(output)[0]
    assert len(output) < 10000
    assert result['entry']['id'] == 'VE-large'
    assert result['entry']['rights'] == 'unknown'
    assert result['entry']['checks']['render'] == 'not_run'
    assert len(result['entry']['description']) <= 240
    assert len(result['entry']['tags']) <= 16
    assert 'private_extension' not in result['entry']
    assert any('description' in p for p in result['truncated_fields'])
    assert any('tags' in p for p in result['truncated_fields'])
    assert any('private_extension' in p for p in result['omitted_fields'])
    assert '--full-record' in result['retrieve']
    assert cli.main(['--full-record']) == 0
    assert json.loads(capsys.readouterr().out)[0]['entry'] == row


def test_summary_bounded_for_nested_and_many_unknown_fields(monkeypatch, capsys):
    row = {'id': 'VE-tree', 'source': 'synthetic', 'rights': 'unknown',
           'checks': {'render': 'not_run'},
           'asset': {f'k{i}': {'values': ['v' * 500 for _ in range(100)]} for i in range(100)}}
    row.update({f'extra{i}': 'z' * 1000 for i in range(100)})
    monkeypatch.setattr(cli, 'search', lambda *a, **k: [row])
    assert cli.main([]) == 0
    output = capsys.readouterr().out
    result = json.loads(output)[0]
    assert len(output) < 60000
    assert result['entry']['checks']['render'] == 'not_run'
    assert result['entry']['rights'] == 'unknown'
    assert 'additional fields omitted' in result['omitted_fields']
    assert result['truncated_fields']
    assert cli.main(['--full-record']) == 0
    assert json.loads(capsys.readouterr().out)[0]['entry'] == row


def test_default_search_exposes_prompt_motion_file(capsys):
    from video_studio.effect_library import search
    from video_studio.effect_library.resources import resource_root
    root = resource_root()
    pm = root / 'skills/video-theme-library/assets/prompt-motion/index.json'
    item = search(pm_index=pm, limit=1)[0]
    assert item['file']
    assert cli.main(['--q', item['id'], '--limit', '1']) == 0
    result = json.loads(capsys.readouterr().out)[0]
    assert result['entry']['id'] == item['id']
    assert result['entry']['file'] == item['file']


def test_compact_records_have_eight_kib_json_upper_bound(monkeypatch, capsys):
    rows = []
    for i in range(10):
        rows.append({'id': f'VE-bounded-{i}', 'name': 'x' * 240, 'kind': 'prompt', 'rights': 'unknown',
                     'source': 'synthetic', 'checks': {'render': 'not_run'},
                     'tags': [('🎬' + chr(1)) * 100] * 8,
                     'evidence': {f'key-{j}': [('🎬' + chr(1)) * 100] * 8 for j in range(12)}})
    monkeypatch.setattr(cli, 'search', lambda *a, **k: rows)
    assert cli.main(['--limit', '10']) == 0
    result = json.loads(capsys.readouterr().out)
    assert len(result) == 10
    for row in result:
        assert len(json.dumps(row, ensure_ascii=True).encode('utf-8')) <= 8192
        assert row['entry']['id'].startswith('VE-bounded-')
        assert row['entry']['rights'] == 'unknown'
        assert row['entry']['checks']['render'] == 'not_run'
        assert row['truncated_fields'] or row['omitted_fields']
        assert '--full-record' in row['retrieve']
    assert cli.main(['--limit', '10', '--full-record']) == 0
    assert [x['entry'] for x in json.loads(capsys.readouterr().out)] == rows


def test_long_id_is_never_silently_truncated(monkeypatch, capsys):
    row = {'id': 'VE-' + 'a' * 1000, 'name': 'large id', 'kind': 'reference', 'rights': 'unknown',
           'source': 'synthetic', 'checks': {'render': 'not_run'}}
    monkeypatch.setattr(cli, 'search', lambda *a, **k: [row])
    assert cli.main([]) == 2
    output = capsys.readouterr()
    assert output.out == ''
    assert '--full-record' in output.err
    assert cli.main(['--full-record']) == 0
    assert json.loads(capsys.readouterr().out)[0]['entry']['id'] == row['id']


def test_summary_prioritizes_standard_checks_over_extra_keys(monkeypatch, capsys):
    names = ('static_check', 'preview', 'render', 'audio', 'ratio_test', 'reuse_evidence')
    checks = {f'extra{i}': 'pass' for i in range(30)}
    checks.update(dict.fromkeys(names, 'not_run'))
    row = {'id': 'VE-checks', 'kind': 'component', 'rights': 'owned', 'checks': checks}
    monkeypatch.setattr(cli, 'search', lambda *a, **k: [row])
    assert cli.main([]) == 0
    result = json.loads(capsys.readouterr().out)[0]
    assert result['entry']['checks'] == dict.fromkeys(names, 'not_run')
    assert any('checks' in name for name in result['omitted_fields'])
    assert cli.main(['--full-record']) == 0
    assert json.loads(capsys.readouterr().out)[0]['entry'] == row


def test_long_source_and_file_are_marked_as_truncated(monkeypatch, capsys):
    row = {'id': 'VE-long-path', 'name': 'x', 'kind': 'reference', 'rights': 'unknown',
           'source': 's' * 500, 'file': 'f' * 500, 'checks': {'render': 'not_run'}}
    monkeypatch.setattr(cli, 'search', lambda *a, **k: [row])
    assert cli.main([]) == 0
    result = json.loads(capsys.readouterr().out)[0]
    assert {'source', 'file'} <= set(result['truncated_fields'])
    assert result['entry']['id'] == row['id']
    assert cli.main(['--full-record']) == 0
    assert json.loads(capsys.readouterr().out)[0]['entry'] == row
