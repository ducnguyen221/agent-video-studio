import hashlib
import json
import os
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(os.name != 'nt', reason='Windows native materialization')

@pytest.fixture
def repo(tmp_path, monkeypatch):
    from video_studio.effect_library import resources
    root = tmp_path / 'repo'; root.mkdir()
    index = root / 'skills/video-theme-library/assets/effect-library/entries.json'
    index.parent.mkdir(parents=True)
    content = b'export const test = 1;'
    asset = root / 'assets/test.js'; asset.parent.mkdir(); asset.write_bytes(content)
    checks = dict.fromkeys(('static_check','preview','render','audio','ratio_test','reuse_evidence'), 'not_run')
    item = dict(id='VE-fixture', name='fixture', kind='component', maturity='candidate', rights='owned',
                source='synthetic', runtime='browser', tags=[], roles=[], techniques=[], ratios=[], checks=checks,
                asset={'path':'assets/test.js','sha256':hashlib.sha256(content).hexdigest()})
    index.write_text(json.dumps([item]), encoding='utf-8')
    project=tmp_path/'project'; project.mkdir()
    monkeypatch.setattr(resources, 'resource_root', lambda: root)
    return root,index,item,project,content

def test_repo_materialize_reads_verified_asset(repo):
    from video_studio.effect_library import materialize_repo
    root,index,item,project,content=repo
    materialize_repo(item['id'],project,'reused.js')
    assert (project/'reused.js').read_bytes()==content

def test_repo_materialize_refuses_changed_and_existing(repo):
    from video_studio.effect_library import materialize_repo
    root,index,item,project,content=repo
    (root/'assets/test.js').write_bytes(b'tampered')
    with pytest.raises(ValueError,match='hash'):
        materialize_repo(item['id'],project,'reused.js')
    assert not (project/'reused.js').exists()
    (root/'assets/test.js').write_bytes(content)
    (project/'reused.js').write_bytes(b'existing')
    with pytest.raises(OSError):
        materialize_repo(item['id'],project,'reused.js')
    assert (project/'reused.js').read_bytes()==b'existing'

@pytest.mark.parametrize('change', ['reference','unknown','bundle','missing','duplicate','traversal'])
def test_repo_materialize_rejects_unusable_catalog(repo, change):
    from video_studio.effect_library import materialize_repo
    from video_studio.contract import ContractError
    root,index,item,project,content=repo
    records=[item]
    if change=='reference':
        item.update(kind='reference',maturity='reference_only',asset=None)
    elif change=='unknown':
        item['rights']='unknown'
    elif change=='bundle':
        item.pop('asset'); item['assets']=[{'path':'assets/test.js','sha256':hashlib.sha256(content).hexdigest(),'rights':'owned'}, {'path':'assets/other.js','sha256':hashlib.sha256(b'other').hexdigest(),'rights':'owned'}]
    elif change=='duplicate':
        records.append(dict(item))
    elif change=='traversal':
        item['asset']['path']='../outside'
    index.write_text(json.dumps(records),encoding='utf-8')
    with pytest.raises((ValueError, ContractError)):
        materialize_repo('VE-absent' if change=='missing' else item['id'],project,'reused.js')
    assert list(project.iterdir())==[]

def test_repo_materialize_actual_seed(tmp_path):
    from video_studio.effect_library import materialize_repo
    from video_studio.effect_library.resources import resource_root
    output=tmp_path/'flare.js'
    materialize_repo('VE-lens-flare',tmp_path,output.name)
    assert output.read_bytes()==(resource_root()/'skills/photo-ambient-effects/assets/lens-flare.js').read_bytes()

def test_cli_materialize_repo_actual_seed(tmp_path):
    import subprocess,sys
    result=subprocess.run([sys.executable,'-m','video_studio.effect_library','materialize-repo','--id','VE-lens-flare','--project',str(tmp_path),'--name','flare.js'],capture_output=True,text=True)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)['id']=='VE-lens-flare'
    assert (tmp_path/'flare.js').is_file()

def test_repo_source_close_fails_before_publish(repo, monkeypatch):
    from video_studio.effect_library import materialize_repo
    from video_studio.effect_library import _native_windows as native
    root,index,item,project,content=repo
    original=native.close
    count=0
    def fail_first(handle):
        nonlocal count
        count+=1
        original(handle)
        if count==1: raise OSError('close failure')
    monkeypatch.setattr(native,'close',fail_first)
    with pytest.raises(OSError,match='close failure'):
        materialize_repo(item['id'],project,'reused.js')
    assert not (project/'reused.js').exists()

def test_repo_publish_close_failure_reports_published(repo,monkeypatch):
    from video_studio.effect_library import materialize_repo
    from video_studio.effect_library import _native_windows as native
    root,index,item,project,content=repo
    original=native.rename_no_replace
    def after_rename(handle, destination, name):
        original(handle,destination,name)
        old=native.close
        def fail_once(h):
            monkeypatch.setattr(native,'close',old)
            old(h)
            raise OSError('injected close')
        monkeypatch.setattr(native,'close',fail_once)
    monkeypatch.setattr(native,'rename_no_replace',after_rename)
    with pytest.raises(native.PublishedButCloseFailed):
        materialize_repo(item['id'],project,'reused.js')
    assert (project/'reused.js').read_bytes()==content

def test_repo_materialize_rejects_asset_junction(repo, tmp_path):
    import subprocess
    from video_studio.effect_library import materialize_repo
    root,index,item,project,content=repo
    outside=tmp_path/'outside'; outside.mkdir(); (outside/'test.js').write_bytes(content)
    link=root/'linked'
    env=dict(os.environ, EFFECT_TEST_LINK=str(link), EFFECT_TEST_TARGET=str(outside))
    result=subprocess.run(['powershell','-NoProfile','-Command','New-Item -ItemType Junction -Path $env:EFFECT_TEST_LINK -Target $env:EFFECT_TEST_TARGET | Out-Null'],env=env,capture_output=True,timeout=20)
    if result.returncode:
        pytest.skip('Windows junction setup unavailable')
    try:
        item['asset']['path']='linked/test.js'; index.write_text(json.dumps([item]),encoding='utf-8')
        with pytest.raises(OSError):
            materialize_repo(item['id'],project,'reused.js')
        assert list(project.iterdir())==[]
    finally:
        os.rmdir(link)

def test_repo_materialize_write_failure_cleans_stage(repo,monkeypatch):
    from video_studio.effect_library import materialize_repo
    from video_studio.effect_library import _native_windows as native
    root,index,item,project,content=repo
    def fail(*args): raise OSError('injected write failure')
    monkeypatch.setattr(native,'write_all',fail)
    with pytest.raises(OSError,match='write failure'):
        materialize_repo(item['id'],project,'reused.js')
    assert list(project.iterdir())==[]

def test_repo_materialize_denies_posix_before_access(repo,monkeypatch):
    import importlib
    from video_studio.contract import ContractError
    catalog=importlib.import_module('video_studio.effect_library.catalog')
    root,index,item,project,content=repo
    monkeypatch.setattr(catalog.os,'name','posix')
    with pytest.raises(ContractError,match='unavailable'):
        catalog.materialize_repo(item['id'],project,'reused.js')

def test_cli_reports_published_close_failure(monkeypatch,capsys,tmp_path):
    from video_studio.effect_library import __main__ as cli
    from video_studio.effect_library._native_windows import PublishedButCloseFailed
    def fail(*args): raise PublishedButCloseFailed('published')
    monkeypatch.setattr(cli,'materialize_repo',fail)
    assert cli.main(['materialize-repo','--id','VE-fixture','--project',str(tmp_path),'--name','file.js']) == 3
    assert 'published' in capsys.readouterr().err.lower()

def test_cli_repo_entry_missing_has_exit_two(tmp_path):
    import subprocess,sys
    result=subprocess.run([sys.executable,'-m','video_studio.effect_library','materialize-repo','--id','VE-no-such-entry','--project',str(tmp_path),'--name','file.js'],capture_output=True,text=True)
    assert result.returncode==2
    assert not (tmp_path/'file.js').exists()

def test_repo_asset_is_locked_while_read(repo,monkeypatch):
    from video_studio.effect_library import materialize_repo
    from video_studio.effect_library import _native_windows as native
    root,index,item,project,content=repo
    original=native.read_all
    observed=[]
    def inspect(handle,limit=64*1024*1024):
        payload=original(handle,limit)
        if payload == content:
            with pytest.raises(PermissionError):
                (root/'assets/test.js').write_bytes(b'mutated')
            observed.append(True)
        return payload
    monkeypatch.setattr(native,'read_all',inspect)
    materialize_repo(item['id'],project,'reused.js')
    assert observed == [True]
    assert (project/'reused.js').read_bytes()==content

def test_repo_materialize_rename_failure_cleans_stage(repo,monkeypatch):
    from video_studio.effect_library import materialize_repo
    from video_studio.effect_library import _native_windows as native
    root,index,item,project,content=repo
    def fail(*args): raise OSError('injected rename failure')
    monkeypatch.setattr(native,'rename_no_replace',fail)
    with pytest.raises(OSError,match='rename failure'):
        materialize_repo(item['id'],project,'reused.js')
    assert list(project.iterdir())==[]

@pytest.mark.parametrize('duplicate', ['rights','asset','hash','nan','infinity'])
def test_repo_materialize_rejects_ambiguous_or_nonfinite_json(repo, duplicate):
    from video_studio.effect_library import materialize_repo
    root,index,item,project,content=repo
    raw=json.dumps([item])
    if duplicate == 'rights':
        raw=raw.replace('"rights": "owned"', '"rights": "unknown", "rights": "owned"', 1)
    elif duplicate == 'asset':
        raw=raw.replace('"asset": {', '"asset": null, "asset": {', 1)
    elif duplicate == 'hash':
        raw=raw.replace('"sha256": ', '"sha256": "' + '0'*64 + '", "sha256": ', 1)
    else:
        raw=raw.replace('"runtime": "browser"','"runtime": "browser", "extra": '+('NaN' if duplicate=='nan' else 'Infinity'),1)
    index.write_text(raw,encoding='utf-8')
    with pytest.raises(ValueError):
        materialize_repo(item['id'],project,'reused.js')
    assert list(project.iterdir())==[]
