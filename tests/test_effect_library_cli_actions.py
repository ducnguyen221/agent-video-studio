import hashlib
import json
import os
import subprocess
import sys

import pytest


windows_only = pytest.mark.skipif(os.name != "nt", reason="secure station writes are Windows-only")


def run_cli(*args):
    return subprocess.run([sys.executable, "-m", "video_studio.effect_library", *map(str, args)],
                          capture_output=True, text=True, encoding="utf-8", timeout=30)


def test_root_help_lists_station_actions_and_published_status():
    result = run_cli("--help")
    assert result.returncode == 0
    assert all(text in result.stdout for text in ("capture", "materialize", "status 3"))


@windows_only
def test_cli_capture_and_materialize_without_overwrite(tmp_path):
    project = tmp_path / "project"
    destination = tmp_path / "destination"
    station = tmp_path / "station"
    project.mkdir()
    destination.mkdir()
    (station / "effect-library" / "entries").mkdir(parents=True)
    data = b"synthetic effect for cli"
    (project / "effect.js").write_bytes(data)
    checks = dict.fromkeys(("static_check", "preview", "render", "audio", "ratio_test", "reuse_evidence"), "not_run")
    manifest = {"id": "VE-cli-synthetic", "name": "CLI synthetic effect", "kind": "component",
                "maturity": "candidate", "rights": "owned", "source": "synthetic example", "runtime": "js",
                "tags": ["cli-synthetic"], "roles": [], "techniques": [], "ratios": [], "checks": checks,
                "asset": {"path": "effect.js", "sha256": hashlib.sha256(data).hexdigest()}}
    (project / "entry.json").write_text(json.dumps(manifest), encoding="utf-8-sig")
    captured = run_cli("capture", "--project", project, "--station", station, "--manifest", "entry.json")
    assert captured.returncode == 0, captured.stderr
    assert json.loads(captured.stdout)["id"] == "VE-cli-synthetic"
    found = run_cli("--q", "cli synthetic", "--station", station)
    assert found.returncode == 0
    assert any(row["entry"]["id"] == "VE-cli-synthetic" for row in json.loads(found.stdout))
    restored = run_cli("materialize", "--station", station, "--id", "VE-cli-synthetic",
                       "--project", destination, "--name", "effect.js")
    assert restored.returncode == 0, restored.stderr
    assert (destination / "effect.js").read_bytes() == data
    duplicate = run_cli("materialize", "--station", station, "--id", "VE-cli-synthetic",
                        "--project", destination, "--name", "effect.js")
    assert duplicate.returncode != 0
    assert (destination / "effect.js").read_bytes() == data
    process = subprocess.Popen([sys.executable, "-m", "video_studio.effect_library", "materialize",
                                "--station", str(station), "--id", "VE-cli-synthetic",
                                "--project", str(destination), "--name", "second.js"],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    process.stdout.close()
    code = process.wait(timeout=30)
    error = process.stderr.read().decode("utf-8")
    process.stderr.close()
    assert code == 3, error
    assert "completed" in error
    assert (destination / "second.js").read_bytes() == data


@windows_only
def test_cli_main_capture_and_materialize_roundtrip(tmp_path, capsys):
    from video_studio.effect_library import __main__ as cli

    project, destination, station = tmp_path / "project", tmp_path / "destination", tmp_path / "station"
    project.mkdir()
    destination.mkdir()
    (station / "effect-library" / "entries").mkdir(parents=True)
    payload = b"another synthetic effect"
    (project / "effect.js").write_bytes(payload)
    checks = dict.fromkeys(("static_check", "preview", "render", "audio", "ratio_test", "reuse_evidence"), "not_run")
    manifest = {"id": "VE-cli-main-synthetic", "name": "CLI main synthetic", "kind": "component",
                "maturity": "candidate", "rights": "owned", "source": "synthetic test", "runtime": "js",
                "tags": [], "roles": [], "techniques": [], "ratios": [], "checks": checks,
                "asset": {"path": "effect.js", "sha256": hashlib.sha256(payload).hexdigest()}}
    (project / "entry.json").write_text(json.dumps(manifest), encoding="utf-8-sig")
    assert cli.main(["capture", "--project", str(project), "--station", str(station), "--manifest", "entry.json"]) == 0
    assert json.loads(capsys.readouterr().out) == {"operation": "capture", "id": manifest["id"]}
    assert cli.main(["materialize", "--project", str(destination), "--station", str(station),
                     "--id", manifest["id"], "--name", "effect.js"]) == 0
    assert json.loads(capsys.readouterr().out) == {"operation": "materialize", "id": manifest["id"]}
    assert (destination / "effect.js").read_bytes() == payload


@windows_only
def test_manifest_reader_rejects_duplicate_keys_and_nan(tmp_path):
    from video_studio.effect_library.__main__ import _manifest_in_project

    manifest = tmp_path / "entry.json"
    for contents, message in ((b'{"nested":{"x":1,"x":2}}', "duplicate JSON field"),
                              (b'{"value":NaN}', "invalid JSON constant")):
        manifest.write_bytes(contents)
        with pytest.raises(ValueError, match=message):
            _manifest_in_project(str(tmp_path), "entry.json")


@windows_only
def test_cli_capture_rejects_manifest_traversal_without_writing(tmp_path):
    project = tmp_path / "project"
    station = tmp_path / "station"
    project.mkdir()
    entries = station / "effect-library" / "entries"
    entries.mkdir(parents=True)
    (tmp_path / "manifest.json").write_text("{}", encoding="utf-8")
    result = run_cli("capture", "--project", project, "--station", station, "--manifest", "../manifest.json")
    assert result.returncode == 2
    assert "Unsafe relative path" in result.stderr
    assert not list(entries.iterdir())


@windows_only
def test_cli_bundle_materialize_fails_closed(tmp_path):
    project = tmp_path / "project"
    destination = tmp_path / "destination"
    station = tmp_path / "station"
    project.mkdir()
    destination.mkdir()
    (station / "effect-library" / "entries").mkdir(parents=True)
    assets = []
    for name, content in (("index.html", b"synthetic html"), ("style.css", b"synthetic css")):
        (project / name).write_bytes(content)
        assets.append({"path": name, "sha256": hashlib.sha256(content).hexdigest(), "rights": "owned"})
    checks = dict.fromkeys(("static_check", "preview", "render", "audio", "ratio_test", "reuse_evidence"), "not_run")
    manifest = {"id": "VE-cli-bundle", "name": "Synthetic CLI bundle", "kind": "component",
                "maturity": "candidate", "rights": "owned", "source": "synthetic example", "runtime": "html",
                "tags": [], "roles": [], "techniques": [], "ratios": [], "checks": checks, "assets": assets}
    (project / "entry.json").write_text(json.dumps(manifest), encoding="utf-8")
    captured = run_cli("capture", "--project", project, "--station", station, "--manifest", "entry.json")
    assert captured.returncode == 0, captured.stderr
    result = run_cli("materialize", "--station", station, "--id", "VE-cli-bundle",
                     "--project", destination, "--name", "bundle")
    assert result.returncode == 2
    assert not list(destination.iterdir())


@windows_only
def test_cli_capture_rejects_duplicate_manifest_fields(tmp_path):
    project = tmp_path / "project"
    station = tmp_path / "station"
    project.mkdir()
    entries = station / "effect-library" / "entries"
    entries.mkdir(parents=True)
    field = "synthetic-private-key-" + "x" * 10000
    (project / "entry.json").write_text(json.dumps({field: 1})[:-1] + "," + json.dumps(field) + ":2}", encoding="utf-8")
    result = run_cli("capture", "--project", project, "--station", station, "--manifest", "entry.json")
    assert result.returncode == 2
    assert "duplicate JSON field" in result.stderr
    assert "synthetic-private-key" not in result.stderr
    assert not list(entries.iterdir())


@pytest.mark.parametrize("invalid", ["[]", '{"x":NaN}', "[" * 100000 + "]" * 100000], ids=["array", "nan", "deep"])
@windows_only
def test_cli_capture_rejects_invalid_json_without_traceback(tmp_path, invalid):
    project = tmp_path / "project"
    station = tmp_path / "station"
    project.mkdir()
    entries = station / "effect-library" / "entries"
    entries.mkdir(parents=True)
    (project / "entry.json").write_text(invalid, encoding="utf-8")
    result = run_cli("capture", "--project", project, "--station", station, "--manifest", "entry.json")
    assert result.returncode == 2
    assert "Traceback" not in result.stderr
    assert not list(entries.iterdir())


@windows_only
def test_cli_capture_rejects_oversized_manifest(tmp_path):
    project = tmp_path / "project"
    station = tmp_path / "station"
    project.mkdir()
    entries = station / "effect-library" / "entries"
    entries.mkdir(parents=True)
    (project / "entry.json").write_bytes(b" " * (1024 * 1024 + 1))
    result = run_cli("capture", "--project", project, "--station", station, "--manifest", "entry.json")
    assert result.returncode == 2
    assert "size limit" in result.stderr
    assert not list(entries.iterdir())


@pytest.mark.parametrize("action", ["capture", "materialize"])
def test_cli_reports_published_close_failure(monkeypatch, capsys, action):
    from video_studio.effect_library import __main__ as cli
    from video_studio.effect_library._native_windows import PublishedButCloseFailed

    def fail(*args):
        raise PublishedButCloseFailed("entry published; closing handle failed")

    monkeypatch.setattr(cli, "_manifest_in_project", lambda *args: {"id": "VE-test"})
    monkeypatch.setattr(cli, action, fail)
    arguments = (["capture", "--project", "p", "--station", "s", "--manifest", "x"] if action == "capture"
                 else ["materialize", "--project", "p", "--station", "s", "--id", "VE-test", "--name", "x"])
    assert cli.main(arguments) == 3
    captured = capsys.readouterr()
    assert "published" in captured.err
    assert not captured.out


def test_cli_reports_broken_pipe_after_operation(monkeypatch):
    import builtins
    from video_studio.effect_library import __main__ as cli

    messages = []
    def print_or_break(*args, **kwargs):
        if kwargs.get("file") is None:
            raise BrokenPipeError()
        messages.append(args[0])

    monkeypatch.setattr(builtins, "print", print_or_break)
    monkeypatch.setattr(cli.os, "dup2", lambda *args: None)
    assert cli._write_result({"operation": "capture", "id": "VE-test"}) == 3
    assert "completed" in messages[0]


def test_cli_closed_output_streams_preserves_published_state(monkeypatch):
    import io
    from video_studio.effect_library import __main__ as cli

    calls = []
    monkeypatch.setattr(cli, "_manifest_in_project", lambda *args: {"id": "VE-test"})
    monkeypatch.setattr(cli, "capture", lambda *args: calls.append("published") or "VE-test")
    output, errors = io.StringIO(), io.StringIO()
    output.close()
    errors.close()
    with monkeypatch.context() as scope:
        scope.setattr(cli.sys, "stdout", output)
        scope.setattr(cli.sys, "stderr", errors)
        result = cli._action(["capture", "--project", "p", "--station", "s", "--manifest", "entry.json"])
    assert result == 3
    assert calls == ["published"]


@pytest.mark.parametrize("action", ["capture", "materialize"])
def test_cli_no_stdout_reports_published_status(monkeypatch, capsys, action):
    from video_studio.effect_library import __main__ as cli

    calls = []
    monkeypatch.setattr(cli, "_manifest_in_project", lambda *args: {"id": "VE-test"})
    monkeypatch.setattr(cli, action, lambda *args: calls.append("published") or "VE-test")
    arguments = (["capture", "--project", "p", "--station", "s", "--manifest", "x"] if action == "capture"
                 else ["materialize", "--project", "p", "--station", "s", "--id", "VE-test", "--name", "x"])
    with monkeypatch.context() as scope:
        scope.setattr(cli.sys, "stdout", None)
        result = cli.main(arguments)
    assert result == 3
    assert calls == ["published"]
    assert "completed" in capsys.readouterr().err


def test_cli_stream_reconfigure_failure_prevents_writes(monkeypatch, capsys):
    from video_studio.effect_library import __main__ as cli

    class BadStream:
        def reconfigure(self, **kwargs):
            raise OSError("synthetic stream failure")

    calls = []
    monkeypatch.setattr(cli, "capture", lambda *args: calls.append("published"))
    with monkeypatch.context() as scope:
        scope.setattr(cli.sys, "stdout", BadStream())
        result = cli.main(["capture", "--project", "p", "--station", "s", "--manifest", "x"])
    assert result == 2
    assert not calls
    assert "output" in capsys.readouterr().err.lower()


@windows_only
def test_cli_rejects_manifest_junction_without_reading_target(tmp_path):
    project = tmp_path / "project"
    station = tmp_path / "station"
    outside = tmp_path / "outside"
    project.mkdir()
    outside.mkdir()
    entries = station / "effect-library" / "entries"
    entries.mkdir(parents=True)
    (outside / "entry.json").write_text("{}", encoding="utf-8")
    junction = project / "link"
    env = dict(os.environ, EFFECT_CLI_LINK=str(junction), EFFECT_CLI_TARGET=str(outside))
    proc = subprocess.run(["powershell", "-NoProfile", "-Command",
                           "New-Item -ItemType Junction -Path $env:EFFECT_CLI_LINK -Target $env:EFFECT_CLI_TARGET | Out-Null"],
                          env=env, capture_output=True, timeout=20)
    if proc.returncode:
        pytest.skip("Windows junction setup unavailable")
    try:
        result = run_cli("capture", "--project", project, "--station", station, "--manifest", "link/entry.json")
        assert result.returncode == 2
        assert "c000050b" in result.stderr
        assert not list(entries.iterdir())
    finally:
        os.rmdir(junction)


def test_cli_capture_fails_closed_on_unverified_platform(monkeypatch, tmp_path, capsys):
    from types import SimpleNamespace
    from video_studio.effect_library import __main__ as cli

    initial = sorted(path.name for path in tmp_path.iterdir())
    monkeypatch.setattr(cli, "os", SimpleNamespace(name="posix"))
    result = cli._action(["capture", "--project", str(tmp_path), "--station", str(tmp_path),
                          "--manifest", "entry.json"])
    assert result == 2
    assert "not verified" in capsys.readouterr().err
    assert sorted(path.name for path in tmp_path.iterdir()) == initial
