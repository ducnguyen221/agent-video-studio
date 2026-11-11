import json
import os
import subprocess
import sys

import pytest

from video_studio.contract import ContractError
from video_studio.effect_library import search


def test_search_rejects_duplicate_repo_rights_before_return(tmp_path):
    catalog = tmp_path / 'entries.json'
    catalog.write_text('[{"id":"VE-example","rights":"unknown","rights":"owned"}]', encoding='utf-8')
    with pytest.raises(ContractError, match='duplicate'):
        search(repo_entries=catalog)


@pytest.mark.parametrize('value', ['NaN', 'Infinity', '-Infinity', '1e999'])
def test_search_rejects_nonfinite_pm_metadata(tmp_path, value):
    catalog = tmp_path / 'index.json'
    catalog.write_text('{"entries":[],"extra":{"score":' + value + '}}', encoding='utf-8')
    with pytest.raises(ContractError, match='finite'):
        search(pm_index=catalog)


def test_search_rejects_duplicate_nested_pm_field(tmp_path):
    catalog = tmp_path / 'index.json'
    catalog.write_text('{"entries":[],"extra":{"x":1,"x":2}}', encoding='utf-8')
    with pytest.raises(ContractError, match='duplicate'):
        search(pm_index=catalog)


@pytest.mark.parametrize('catalog_kind', ['repo', 'pm'])
def test_search_rejects_excessively_nested_json_cleanly(tmp_path, catalog_kind):
    catalog = tmp_path / 'deep.json'
    catalog.write_text('[' * 20000 + '0' + ']' * 20000, encoding='utf-8')
    with pytest.raises(ContractError, match='nesting'):
        search(**{('repo_entries' if catalog_kind == 'repo' else 'pm_index'): catalog})


def test_cli_rejects_excessively_nested_json_without_traceback(tmp_path):
    catalog = tmp_path / 'deep.json'
    catalog.write_text('[' * 20000 + '0' + ']' * 20000, encoding='utf-8')
    proc = subprocess.run([sys.executable, '-m', 'video_studio.effect_library', '--repo-entries', str(catalog), '--no-distilled'], capture_output=True, text=True)
    assert proc.returncode == 2
    assert proc.stdout == ''
    assert 'nesting' in proc.stderr.lower()
    assert 'traceback' not in proc.stderr.lower()


def test_cli_rejects_duplicate_repo_catalog_without_stdout(tmp_path):
    catalog = tmp_path / 'entries.json'
    catalog.write_text('[{"id":"VE-example","rights":"unknown","rights":"owned"}]', encoding='utf-8')
    proc = subprocess.run([sys.executable, '-m', 'video_studio.effect_library', '--repo-entries', str(catalog), '--no-distilled'], capture_output=True, text=True)
    assert proc.returncode == 2
    assert proc.stdout == ''
    assert 'duplicate' in proc.stderr.lower()


@pytest.mark.skipif(os.name != 'nt', reason='station reader is Windows only')
def test_station_rejects_duplicate_entry_before_return(tmp_path):
    entries = tmp_path / 'station/effect-library/entries/VE-example'
    entries.mkdir(parents=True)
    (entries / 'entry.json').write_text('{"format":"ve-metadata-v1","entry":{"rights":"unknown","rights":"owned"}}', encoding='utf-8')
    with pytest.raises(ContractError, match='duplicate'):
        search(station=tmp_path / 'station')


@pytest.mark.skipif(os.name != 'nt', reason='capture is Windows only')
@pytest.mark.parametrize('broken_source', ['repo', 'pm', 'repo_deep', 'pm_deep'])
def test_capture_rejects_duplicate_catalog_before_publishing(tmp_path, monkeypatch, broken_source):
    from video_studio.effect_library import capture, resources, distilled_sources

    repo = tmp_path / 'repo'
    repo_index = repo / 'skills/video-theme-library/assets/effect-library/entries.json'
    pm_index = repo / 'skills/video-theme-library/assets/prompt-motion/index.json'
    repo_index.parent.mkdir(parents=True)
    pm_index.parent.mkdir(parents=True)
    deep = '[' * 20000 + '0' + ']' * 20000
    repo_index.write_text('[{"rights":"unknown","rights":"owned"}]' if broken_source == 'repo' else deep if broken_source == 'repo_deep' else '[]', encoding='utf-8')
    pm_index.write_text('{"entries":[],"extra":{"x":1,"x":2}}' if broken_source == 'pm' else deep if broken_source == 'pm_deep' else '{"entries":[]}', encoding='utf-8')
    monkeypatch.setattr(resources, 'resource_root', lambda: repo)
    monkeypatch.setattr(distilled_sources, 'load_distilled', lambda _: [])
    project = tmp_path / 'project'
    project.mkdir()
    station = tmp_path / 'station'
    entries = station / 'effect-library/entries'
    entries.mkdir(parents=True)
    record = {'id': 'VE-synthetic', 'name': 'Synthetic reference', 'kind': 'reference',
              'maturity': 'reference_only', 'rights': 'unknown', 'source': 'https://example.invalid/source',
              'runtime': 'reference', 'tags': [], 'roles': [], 'techniques': [], 'ratios': [],
              'checks': dict.fromkeys(('static_check', 'preview', 'render', 'audio', 'ratio_test', 'reuse_evidence'), 'not_run')}
    with pytest.raises(ValueError, match='nesting' if broken_source.endswith('_deep') else 'duplicate'):
        capture(project, station, record)
    assert list(entries.iterdir()) == []
