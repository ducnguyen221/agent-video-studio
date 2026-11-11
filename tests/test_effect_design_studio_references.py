from pathlib import Path

import pytest

from video_studio.effect_library import search


@pytest.mark.parametrize(('query', 'identifier'), [
    ('design studio', 'VE-design-studio-motion-patterns'),
    ('MP01', 'VE-design-studio-motion-patterns'),
    ('MP02', 'VE-design-studio-motion-patterns'),
    ('MP03', 'VE-design-studio-motion-patterns'),
    ('MP04', 'VE-design-studio-motion-patterns'),
    ('MP05', 'VE-design-studio-motion-patterns'),
    ('MP06', 'VE-design-studio-motion-patterns'),
    ('pausable ambient texture', 'VE-design-studio-motion-patterns'),
    ('motion spec', 'VE-design-studio-motion-spec'),
])
def test_design_studio_reference_is_searchable_without_claiming_video_asset(query, identifier):
    catalog = Path(__file__).resolve().parents[1] / 'skills/video-theme-library/assets/effect-library/entries.json'
    rows = search(query, {'kind': 'reference'}, repo_entries=catalog, limit=100)
    entry = next(row for row in rows if row['id'] == identifier)
    assert entry['rights'] == 'unknown'
    assert entry['maturity'] == 'reference_only'
    assert entry['asset'] is None
    assert all(value == 'not_run' for value in entry['checks'].values())
    assert entry['source'] == 'skills/video-theme-library/references/effect-sources.md'
