from pathlib import Path

import pytest

from video_studio.effect_library import search


@pytest.mark.parametrize(('query', 'identifier'), [
    ('earshot', 'VE-earshot-sound'),
    ('vtake', 'VE-vtake-cards'),
    ('video-use', 'VE-video-use-editing'),
])
def test_existing_upstream_references_are_searchable(query, identifier):
    catalog = Path(__file__).resolve().parents[1] / 'skills/video-theme-library/assets/effect-library/entries.json'
    results = search(query, {'kind': 'reference'}, repo_entries=catalog, limit=50)
    row = next(item for item in results if item['id'] == identifier)
    assert row['maturity'] == 'reference_only'
    assert row['rights'] == 'unknown'
    assert row['asset'] is None
    assert all(value == 'not_run' for value in row['checks'].values())
