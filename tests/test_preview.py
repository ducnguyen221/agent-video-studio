"""`video-studio preview` — studio xem trước, và luật "xem trước bằng ĐÚNG bản sẽ render".

Không gọi npx thật: `--dry-run` trả lại đúng argv sẽ chạy, và test đọc argv đó.
"""
import os

import pytest

from conftest import last_json
from video_studio import preview
from video_studio.contract import StationMissing


@pytest.fixture
def station(tmp_path, monkeypatch):
    st = tmp_path / "st"
    (st / "projects" / "demo").mkdir(parents=True)
    monkeypatch.setenv("VIDEO_STATION", str(st))
    monkeypatch.setenv("NODE_DIR", str(_fake_npx(tmp_path)))
    return st


def _fake_npx(tmp_path):
    """Thư mục có một `npx` giả — `_env.npx_exe()` tìm bằng `shutil.which`, không chạy nó."""
    d = tmp_path / "bin"
    d.mkdir(exist_ok=True)
    for base in ("npx", "node"):
        p = d / (base + ".cmd" if os.name == "nt" else base)
        p.write_text("", encoding="utf-8")
        if os.name != "nt":
            p.chmod(0o755)
    return d


def test_dry_run_prints_the_command_and_runs_nothing(station, monkeypatch, capsys):
    monkeypatch.setenv("HYPERFRAMES_VERSION", "0.7.94")
    monkeypatch.setattr(preview.subprocess, "run",
                        lambda *a, **k: pytest.fail("--dry-run không được gọi tiến trình con"))
    assert preview.main(["--dry-run", "--json"]) == 0
    data = last_json(capsys.readouterr().out)
    assert data["project"] == str(station / "projects" / "demo")
    assert data["argv"][1:3] == ["--yes", "hyperframes@0.7.94"]
    assert data["argv"][3] == "preview"


def test_preview_never_uses_a_floating_version(station, monkeypatch):
    monkeypatch.setenv("HYPERFRAMES_VERSION", "0.8.51")
    argv = preview.preview_argv()
    assert "hyperframes@0.8.51" in argv
    assert not any("latest" in str(a) for a in argv)


def test_port_and_extra_args_go_to_hyperframes(station, monkeypatch, capsys):
    monkeypatch.setattr(preview.subprocess, "run", lambda *a, **k: pytest.fail("không chạy"))
    assert preview.main(["--dry-run", "--json", "--port", "5123", "--", "--open"]) == 0
    argv = last_json(capsys.readouterr().out)["argv"]
    assert argv[-3:] == ["--port", "5123", "--open"]


def test_runs_in_the_project_directory_with_node_on_path(station, monkeypatch):
    seen = {}

    class R:
        returncode = 0

    def fake_run(argv, cwd=None, env=None, **kw):
        seen.update(argv=argv, cwd=cwd, env=env)
        return R()

    monkeypatch.setattr(preview.subprocess, "run", fake_run)
    assert preview.main(["--project", "demo"]) == 0
    assert seen["cwd"] == str(station / "projects" / "demo")
    assert not isinstance(seen["argv"], str), "argv phải là list — không bao giờ chuỗi lệnh"
    assert str(station) not in seen["env"]["PATH"].split(os.pathsep)[0]
    assert seen["env"]["PATH"].split(os.pathsep)[0].endswith("bin")


def test_non_zero_exit_is_engine_error(station, monkeypatch):
    class R:
        returncode = 9

    monkeypatch.setattr(preview.subprocess, "run", lambda *a, **k: R())
    assert preview.main(["--project", "demo"]) == 1


def test_ctrl_c_is_not_an_error(station, monkeypatch):
    def boom(*a, **k):
        raise KeyboardInterrupt

    monkeypatch.setattr(preview.subprocess, "run", boom)
    assert preview.main(["--project", "demo"]) == 0


def test_missing_default_project_is_code_3(tmp_path, monkeypatch):
    monkeypatch.setenv("VIDEO_STATION", str(tmp_path / "trong"))
    with pytest.raises(StationMissing) as e:
        preview.resolve_project()
    assert "video-studio init" in str(e.value)


def test_missing_npx_is_code_3(station, monkeypatch):
    monkeypatch.delenv("NODE_DIR")
    monkeypatch.setattr(preview.render._env, "npx_exe", lambda: None)
    assert preview.main(["--project", "demo"]) == 3
