"""_env: thứ tự phân giải trạm (F17.3), tên cũ VIDEO_ROOT, bản HyperFrames, công cụ ngoài."""
import json
import os
import warnings

import pytest

from video_studio import _env
from video_studio.contract import ContractError


def _repo(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    (repo / "video_studio").mkdir(parents=True)
    (repo / "pyproject.toml").write_text("[project]\n", encoding="utf-8")
    monkeypatch.setenv("VIDEO_STUDIO_REPO", str(repo))
    return repo


# ── trạm ────────────────────────────────────────────────────────────────────────────────

def test_default_station_is_home_dot_video(tmp_path):
    st, src = _env.resolve_station()
    assert src == "default"
    assert st == os.path.join(str(tmp_path / "home"), ".video")


def test_video_station_wins(tmp_path, monkeypatch):
    monkeypatch.setenv("VIDEO_STATION", str(tmp_path / "a"))
    monkeypatch.setenv("VIDEO_ROOT", str(tmp_path / "b"))
    assert _env.resolve_station() == (str(tmp_path / "a"), "VIDEO_STATION")


def test_video_root_is_legacy_alias_with_warning(tmp_path, monkeypatch):
    monkeypatch.setenv("VIDEO_ROOT", str(tmp_path / "old"))
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        st, src = _env.resolve_station()
    assert (st, src) == (str(tmp_path / "old"), "VIDEO_ROOT")
    assert any(issubclass(x.category, DeprecationWarning) and "VIDEO_STATION" in str(x.message)
               for x in w)


def test_blank_env_counts_as_unset(monkeypatch):
    monkeypatch.setenv("VIDEO_STATION", "   ")
    assert _env.resolve_station()[1] == "default"


def test_local_config_then_workspace(tmp_path, monkeypatch):
    repo = _repo(tmp_path, monkeypatch)
    (repo / "workspace").mkdir()
    assert _env.resolve_station() == (str(repo / "workspace"), "workspace")
    (repo / "studio.local.json").write_text(json.dumps({"station_path": str(tmp_path / "ext")}),
                                            encoding="utf-8")
    assert _env.resolve_station() == (str(tmp_path / "ext"), "studio.local.json")


def test_local_config_relative_path_is_relative_to_repo(tmp_path, monkeypatch):
    repo = _repo(tmp_path, monkeypatch)
    (repo / "studio.local.json").write_text(json.dumps({"station_path": "workspace"}),
                                            encoding="utf-8")
    assert _env.resolve_station()[0] == str(repo / "workspace")


def test_env_beats_local_config(tmp_path, monkeypatch):
    repo = _repo(tmp_path, monkeypatch)
    (repo / "studio.local.json").write_text(json.dumps({"station_path": "x"}), encoding="utf-8")
    monkeypatch.setenv("VIDEO_STATION", str(tmp_path / "env"))
    assert _env.resolve_station()[1] == "VIDEO_STATION"


def test_env_read_live_not_frozen_at_import(tmp_path, monkeypatch):
    monkeypatch.setenv("VIDEO_STATION", str(tmp_path / "one"))
    first = _env.station_dir()
    monkeypatch.setenv("VIDEO_STATION", str(tmp_path / "two"))
    assert _env.station_dir() != first


def test_marker_station_json_or_legacy_layout(tmp_path):
    st = tmp_path / "st"
    st.mkdir()
    assert not _env.has_marker(str(st))
    (st / "demo").mkdir()
    (st / "demo" / "hyperframes.json").write_text("{}", encoding="utf-8")
    assert _env.has_marker(str(st))          # trạm đời cũ (trước station.json) vẫn nhận ra
    st2 = tmp_path / "st2"
    st2.mkdir()
    (st2 / "station.json").write_text("{}", encoding="utf-8")
    assert _env.has_marker(str(st2))


def test_projects_dir_env_station_default(tmp_path, monkeypatch):
    st = tmp_path / "st"
    st.mkdir()
    monkeypatch.setenv("VIDEO_STATION", str(st))
    assert _env.projects_dir() == str(st / "projects")
    (st / "station.json").write_text(json.dumps({"projects_dir": "p2"}), encoding="utf-8")
    assert _env.projects_dir() == str(st / "p2")
    monkeypatch.setenv("HYPERFRAMES_WORKDIR", str(tmp_path / "wd"))
    assert _env.projects_dir() == str(tmp_path / "wd")


# ── HyperFrames ─────────────────────────────────────────────────────────────────────────

def test_hyperframes_default_version():
    assert _env.hyperframes_version() == _env.DEFAULT_HYPERFRAMES_VERSION == "0.7.94"


def test_hyperframes_version_env_then_station(tmp_path, monkeypatch):
    st = tmp_path / "st"
    st.mkdir()
    (st / "station.json").write_text(json.dumps({"hyperframes_version": "0.8.51"}),
                                     encoding="utf-8")
    monkeypatch.setenv("VIDEO_STATION", str(st))
    assert _env.hyperframes_version() == "0.8.51"
    monkeypatch.setenv("HYPERFRAMES_VERSION", "0.8.38")
    assert _env.hyperframes_version() == "0.8.38"


@pytest.mark.parametrize("bad", ["latest", "^0.8.51", "~0.8", "0.8", "0.8.51 && echo", "next"])
def test_hyperframes_version_rejects_floating(monkeypatch, bad):
    monkeypatch.setenv("HYPERFRAMES_VERSION", bad)
    with pytest.raises(ContractError):
        _env.hyperframes_version()


def test_hyperframes_spec():
    assert _env.hyperframes_spec("0.8.51") == "hyperframes@0.8.51"


# ── công cụ ngoài ───────────────────────────────────────────────────────────────────────

def test_tool_prefers_dir_env(tmp_path, monkeypatch):
    d = tmp_path / "bin"
    d.mkdir()
    calls = []

    def fake_which(name, path=None):
        calls.append((name, path))
        return os.path.join(path, name) if path else None
    monkeypatch.setattr(_env.shutil, "which", fake_which)
    monkeypatch.setenv("NODE_DIR", str(d))
    assert _env.npx_exe() == os.path.join(str(d), "npx")
    monkeypatch.setenv("FFMPEG_DIR", str(d))
    assert _env.ffmpeg_exe() == os.path.join(str(d), "ffmpeg")


def test_tool_falls_back_to_path(monkeypatch):
    monkeypatch.setattr(_env.shutil, "which",
                        lambda name, path=None: None if path else f"/usr/bin/{name}")
    assert _env.node_exe() == "/usr/bin/node"
    assert _env.ffprobe_exe() == "/usr/bin/ffprobe"


def test_font_stack_inter_first_and_override(monkeypatch):
    assert _env.font_stack().startswith("Inter")
    monkeypatch.setenv("VIDEO_FONT", "Be Vietnam Pro")
    stack = _env.font_stack()
    assert stack.startswith("'Be Vietnam Pro'") and "Inter" in stack


def test_chrome_bin_optional(tmp_path, monkeypatch):
    assert _env.chrome_bin() is None
    monkeypatch.setenv("CHROME_BIN", str(tmp_path / "chrome"))
    assert _env.chrome_bin() == str(tmp_path / "chrome")


# ── trạm giọng (nguồn filler, lồng tiếng) ───────────────────────────────────────────────

def test_voice_station_new_and_legacy(tmp_path, monkeypatch):
    assert _env.voice_station() is None
    monkeypatch.setenv("OMNIVOICE_DIR", str(tmp_path / "vs" / "omnivoice"))
    assert _env.voice_station() == str(tmp_path / "vs")
    assert _env.voice_engine_dir() == str(tmp_path / "vs" / "omnivoice")
    monkeypatch.setenv("VOICE_STATION", str(tmp_path / "voice"))
    assert _env.voice_station() == str(tmp_path / "voice")
    assert _env.voice_engine_dir() == str(tmp_path / "voice" / "omnivoice")


def test_filler_sources_order(tmp_path, monkeypatch):
    monkeypatch.setenv("VOICE_STATION", str(tmp_path / "voice"))
    c = _env.filler_source_candidates()
    assert c[0] == str(tmp_path / "voice" / "omnivoice" / "assets" / "news_short" / "fillers")
    assert str(tmp_path / "voice" / "assets" / "news_short" / "fillers") in c
