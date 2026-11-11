import json
import os
import subprocess
import sys

import pytest

from video_studio.effect_library import capture, search

CHECKS = dict.fromkeys(('static_check', 'preview', 'render', 'audio', 'ratio_test', 'reuse_evidence'), 'not_run')


def reference(identifier, name, **kwargs):
    result = {'id': identifier, 'name': name, 'kind': 'reference', 'maturity': 'reference_only',
              'rights': 'unknown', 'source': 'https://example.invalid/' + identifier,
              'runtime': 'browser', 'tags': [], 'roles': [], 'techniques': [],
              'ratios': [], 'asset': None, 'checks': CHECKS.copy()}
    result.update(kwargs)
    return result


def catalog(path):
    records = [reference('VE-aaa', 'Other', description='VE-react-bits'),
               reference('VE-react-bits', 'React Bits')]
    path.write_text(json.dumps(records), encoding='utf-8')
    return path


def test_exact_id_ranks_above_description_and_preserves_other_order(tmp_path):
    entries = catalog(tmp_path / 'catalog.json')
    assert [e['id'] for e in search('VE-react-bits', repo_entries=entries, limit=1)] == ['VE-react-bits']
    assert [e['id'] for e in search('ve-REACT-bits', repo_entries=entries, limit=1)] == ['VE-react-bits']
    assert [e['id'] for e in search('react bits', repo_entries=entries)] == ['VE-aaa', 'VE-react-bits']


def test_exact_id_still_respects_filters(tmp_path):
    entries = catalog(tmp_path / 'catalog.json')
    assert search('VE-react-bits', {'rights': 'owned'}, repo_entries=entries) == []
    assert search('VE-react-bits', {'check.render': 'pass'}, repo_entries=entries) == []


def test_filtered_exact_id_does_not_bypass_filter(tmp_path):
    entries = tmp_path / 'catalog.json'
    entries.write_text(json.dumps([
        reference('VE-aaa', 'Other', description='VE-react-bits'),
        reference('VE-react-bits', 'Target', rights='owned'),
    ]), encoding='utf-8')
    assert [e['id'] for e in search('VE-react-bits', {'rights': 'unknown'}, repo_entries=entries)] == ['VE-aaa']


def test_prompt_motion_exact_id_ranks_first(tmp_path):
    index = tmp_path / 'index.json'
    index.write_text(json.dumps({'entries': [
        {'id': 'PM-aaa', 'name': 'Other', 'sol_analysis': {'description': 'PM-target'}},
        {'id': 'PM-target', 'name': 'Target'},
    ]}), encoding='utf-8')
    assert [e['id'] for e in search('PM-target', pm_index=index, limit=1)] == ['PM-target']


def test_exact_id_uses_canonical_unicode_but_does_not_drop_accents(tmp_path):
    index = tmp_path / 'index.json'
    index.write_text(json.dumps({'entries': [
        {'id': 'PM-aaa', 'name': 'Other', 'sol_analysis': {'description': 'PM-café'}},
        {'id': 'PM-café', 'name': 'Target'},
        {'id': 'PM-cafe', 'name': 'Unaccented'},
    ]}), encoding='utf-8')
    assert search('pm-cafe\u0301', pm_index=index, limit=1)[0]['id'] == 'PM-café'
    assert search('PM-cafe', pm_index=index, limit=1)[0]['id'] == 'PM-cafe'


def test_exact_id_casefold_expansion_is_not_rejected_by_keyword_matching(tmp_path):
    index = tmp_path / 'index.json'
    index.write_text(json.dumps({'entries': [
        {'id': 'PM-aaa', 'name': 'Other', 'sol_analysis': {'description': 'PM-SS'}},
        {'id': 'PM-ß', 'name': 'Target'},
    ]}), encoding='utf-8')
    assert search('PM-SS', pm_index=index, limit=1)[0]['id'] == 'PM-ß'


@pytest.mark.skipif(os.name != 'nt', reason='station capture is available only on Windows')
def test_station_exact_id_ranks_first(tmp_path):
    station, project = tmp_path / 'station', tmp_path / 'project'
    (station / 'effect-library' / 'entries').mkdir(parents=True)
    project.mkdir()
    capture(project, station, reference('VE-aaa', 'Other', description='VE-station-target'))
    capture(project, station, reference('VE-station-target', 'Target'))
    assert [e['id'] for e in search('VE-station-target', station=station, limit=1)] == ['VE-station-target']


def test_cli_exact_id_limit_one(tmp_path):
    entries = catalog(tmp_path / 'catalog.json')
    p = subprocess.run([sys.executable, '-m', 'video_studio.effect_library', '--q', 'VE-react-bits',
                        '--repo-entries', str(entries), '--no-distilled', '--limit', '1', '--full-record'],
                       text=True, encoding='utf-8', capture_output=True, timeout=30)
    assert p.returncode == 0, p.stderr
    assert json.loads(p.stdout)[0]['entry']['id'] == 'VE-react-bits'
