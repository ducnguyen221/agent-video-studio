"""`reference audit --spec FILE` (RQ-012): mọi chuỗi trong spec/EDL là đường tệp có thật phải nằm trong
`assets/` của project hoặc template của repo.

Chỉ đọc: không test nào mở tệp đích; `open` bị chặn trên mọi đường không phải chính spec.
"""
import builtins
import json
import os

import pytest

from video_studio import cli
from video_studio.contract import ContractError
from video_studio.reference import gate, spec_audit


def _project(tmp_path):
    proj = tmp_path / "proj"
    (proj / "assets").mkdir(parents=True)
    (proj / "source").mkdir()
    (proj / "assets" / "hero.png").write_bytes(b"png")
    (proj / "source" / "reference.mp4").write_bytes(b"mp4")
    return proj


def _spec(tmp_path, data, name="spec.json"):
    p = tmp_path / name
    p.write_text(json.dumps(data), encoding="utf-8")
    return str(p)


def _audit(tmp_path, data, proj=None):
    proj = proj or _project(tmp_path)
    return spec_audit.audit_spec(_spec(tmp_path, data), str(proj))


def test_file_inside_assets_is_clean(tmp_path):
    proj = _project(tmp_path)
    res = _audit(tmp_path, {"scenes": [{"image": str(proj / "assets" / "hero.png")}]}, proj)
    assert res == {"ok": True, "checked": 1, "findings": []}


def test_relative_path_resolves_against_project_and_spec_dir(tmp_path):
    proj = _project(tmp_path)
    res = _audit(tmp_path, {"a": "assets/hero.png", "b": "proj/assets/hero.png"}, proj)
    assert res["ok"] and res["checked"] == 2


def test_source_reference_is_a_finding(tmp_path):
    res = _audit(tmp_path, {"clip": {"src": "proj/source/reference.mp4"}})
    assert res["ok"] is False and res["checked"] == 1
    [f] = res["findings"]
    assert f["path"] == "proj/source/reference.mp4" and "ngoài" in f["problem"]
    assert "/clip/src" in f["problem"]            # chỉ ra vị trí trong spec


def test_dotdot_escape_is_a_finding(tmp_path):
    proj = _project(tmp_path)
    res = _audit(tmp_path, {"x": "proj/assets/../source/reference.mp4"}, proj)
    assert [f["path"] for f in res["findings"]] == ["proj/assets/../source/reference.mp4"]


def test_absolute_path_outside_is_a_finding(tmp_path):
    proj = _project(tmp_path)
    outside = tmp_path / "other.mp4"
    outside.write_bytes(b"x")
    res = _audit(tmp_path, ["a", str(outside)], proj)
    assert [f["path"] for f in res["findings"]] == [str(outside)]


def test_symlink_in_assets_pointing_out_is_a_finding(tmp_path):
    proj = _project(tmp_path)
    link = proj / "assets" / "sneaky.mp4"
    try:
        os.symlink(proj / "source" / "reference.mp4", link)
    except (OSError, NotImplementedError):
        pytest.skip("không tạo được symlink trên máy này")
    res = _audit(tmp_path, {"x": str(link)}, proj)
    assert res["ok"] is False and "liên kết" in res["findings"][0]["problem"]


def test_symlink_inside_assets_to_assets_is_clean(tmp_path):
    proj = _project(tmp_path)
    link = proj / "assets" / "alias.png"
    try:
        os.symlink(proj / "assets" / "hero.png", link)
    except (OSError, NotImplementedError):
        pytest.skip("không tạo được symlink trên máy này")
    assert _audit(tmp_path, {"x": str(link)}, proj)["ok"] is True


def test_repo_template_file_is_allowed(tmp_path):
    tpl = os.path.join(spec_audit.REPO_TEMPLATE_DIRS[0], "__init__.py")
    assert os.path.isfile(tpl)
    assert _audit(tmp_path, {"x": tpl})["ok"] is True


def test_non_paths_urls_and_missing_files_are_ignored(tmp_path):
    res = _audit(tmp_path, {"title": "Tin nóng", "u": "https://example.com/a.mp4", "n": 5, "t": True,
                            "m": "assets/khong-co.png", "e": "", "d": "data:image/png;base64,AAAA",
                            "nul": "a\x00b", "long": "x" * 5000, "dir": "proj/source"})
    assert res == {"ok": True, "checked": 0, "findings": []}


def test_nested_lists_and_dict_keys_are_walked(tmp_path):
    res = _audit(tmp_path, {"edl": {"clips": [[{"file": "proj/source/reference.mp4"}]]}})
    assert len(res["findings"]) == 1 and "/edl/clips/0/0/file" in res["findings"][0]["problem"]


def test_same_string_twice_is_reported_per_location(tmp_path):
    res = _audit(tmp_path, {"a": "proj/source/reference.mp4", "b": "proj/source/reference.mp4"})
    assert len(res["findings"]) == 2


def test_never_opens_target_files(tmp_path, monkeypatch):
    proj = _project(tmp_path)
    spec = _spec(tmp_path, {"a": "proj/source/reference.mp4", "b": "assets/hero.png"})
    real_open = builtins.open
    opened = []

    def spy(file, *a, **k):
        opened.append(os.path.realpath(str(file)))
        return real_open(file, *a, **k)

    monkeypatch.setattr(builtins, "open", spy)
    spec_audit.audit_spec(spec, str(proj))
    assert opened == [os.path.realpath(spec)]


@pytest.mark.parametrize("content, msg", [("không phải json", "JSON"), ("[1, 2", "JSON")])
def test_bad_spec_is_contract_error(tmp_path, content, msg):
    p = tmp_path / "bad.json"
    p.write_text(content, encoding="utf-8")
    with pytest.raises(ContractError, match=msg):
        spec_audit.audit_spec(str(p), str(_project(tmp_path)))


def test_missing_spec_is_contract_error(tmp_path):
    with pytest.raises(ContractError, match="--spec"):
        spec_audit.audit_spec(str(tmp_path / "nope.json"), str(_project(tmp_path)))


def test_oversized_spec_is_contract_error(tmp_path, monkeypatch):
    monkeypatch.setattr(spec_audit, "MAX_SPEC_BYTES", 10)
    with pytest.raises(ContractError, match="lớn hơn"):
        _audit(tmp_path, {"a": "b" * 50})


def test_assets_dir_outside_project_is_contract_error(tmp_path):
    proj = _project(tmp_path)
    with pytest.raises(ContractError, match="phải nằm trong project"):
        spec_audit.audit_spec(_spec(tmp_path, {}), str(proj), assets_dir=str(tmp_path))


# ---------------------------------------------------------------- CLI

def _run(argv, capsys):
    rc = cli.main(["reference", *argv])
    out = capsys.readouterr()
    lines = [ln for ln in out.out.splitlines() if ln.strip()]
    return rc, (json.loads(lines[-1]) if lines and lines[-1].startswith("{") else None), out.err


def test_cli_spec_clean_exit_0(tmp_path, capsys):
    proj = _project(tmp_path)
    spec = str(proj / "spec.json")
    (proj / "spec.json").write_text(json.dumps({"a": "assets/hero.png"}), encoding="utf-8")
    rc, payload, _ = _run(["audit", "--spec", spec, "--json"], capsys)
    assert rc == 0 and payload["ok"] is True and payload["checked"] == 1


def test_cli_spec_findings_exit_2(tmp_path, capsys):
    proj = _project(tmp_path)
    spec = str(proj / "spec.json")
    (proj / "spec.json").write_text(json.dumps({"a": "source/reference.mp4"}), encoding="utf-8")
    rc, payload, err = _run(["audit", "--spec", spec, "--json"], capsys)
    assert rc == 2 and payload["code"] == 2 and payload["error"] == "1 phát hiện"
    assert payload["findings"][0]["path"] == "source/reference.mp4"
    assert "source/reference.mp4" in err


def test_cli_spec_defaults_project_to_spec_dir(tmp_path, capsys):
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets" / "a.png").write_bytes(b"x")
    spec = _spec(tmp_path, {"a": "assets/a.png"})
    rc, payload, _ = _run(["audit", "--spec", spec, "--json"], capsys)
    assert rc == 0 and payload["checked"] == 1


def test_cli_audit_needs_project_or_spec(tmp_path, capsys):
    rc, payload, _ = _run(["audit", "--json"], capsys)
    assert rc == 2 and payload["code"] == 2


def test_cli_project_and_spec_together_merge_findings(tmp_path, capsys):
    proj = _project(tmp_path)
    gate.save_provenance(str(proj), gate.new_provenance("demo", None, None, None, "2026-11-07"))
    spec = _spec(tmp_path, {"a": "proj/source/reference.mp4"})
    rc, payload, _ = _run(["audit", "--project", str(proj), "--spec", spec, "--json"], capsys)
    paths = [f["path"] for f in payload["findings"]]
    assert rc == 2 and "assets/hero.png" in paths and "proj/source/reference.mp4" in paths
