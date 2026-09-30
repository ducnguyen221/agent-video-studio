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

def test_no_variable_means_the_repo_workspace_even_before_init(tmp_path, monkeypatch):
    """Đ4: người dùng không đặt gì ⇒ trạm là `<repo>/workspace/` — kể cả khi `init` chưa tạo nó.

    Trước đây tầng cuối là `~/.video`: một thư mục ẩn ở home mà người dùng public không hề biết
    là có, và máy nào tình cờ có nó thì mọi bản clone đều dùng chung mà không ai chọn.
    """
    repo = _repo(tmp_path, monkeypatch)
    assert not (repo / "workspace").exists()
    assert _env.resolve_station() == (str(repo / "workspace"), "workspace")


def test_home_dot_video_is_never_guessed(tmp_path, monkeypatch):
    """`~/.video` có đủ dấu trạm vẫn KHÔNG được chọn khi không ai chọn nó (biến / init)."""
    repo = _repo(tmp_path, monkeypatch)
    legacy = tmp_path / "home" / ".video"
    legacy.mkdir()
    (legacy / "station.json").write_text("{}", encoding="utf-8")
    assert _env.resolve_station() == (str(repo / "workspace"), "workspace")


def test_without_a_repo_there_is_no_default_station(tmp_path):
    """Bản cài wheel (không repo, không biến): không có gì để đoán ⇒ đòi chọn trạm, mã 3."""
    from video_studio.contract import STATION_MISSING, StationMissing
    assert _env.resolve_station() == (None, "unset")
    with pytest.raises(StationMissing) as e:
        _env.station_dir()
    assert e.value.code == STATION_MISSING
    assert "VIDEO_STATION" in str(e.value) and "--station" in str(e.value)
    assert _env.station_info() == {}              # đọc cấu hình trạm không được sập theo
    assert _env.hyperframes_version() == _env.DEFAULT_HYPERFRAMES_VERSION


def test_init_command_matches_the_station_kind(tmp_path, monkeypatch):
    repo = _repo(tmp_path, monkeypatch)
    assert _env.init_command(str(repo / "workspace")) == "video-studio init"
    ext = str(tmp_path / "ext")
    assert _env.init_command(ext) == f'video-studio init --station "{ext}"'


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
    assert _env.resolve_station()[1] == "unset"


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


# ── đường tương đối giữa hai cây có thể KHÔNG cùng gốc ──────────────────────────────────

def test_rel_path_gives_posix_relative_when_both_under_one_root(tmp_path):
    src = tmp_path / "repo" / "skills" / "video-routing"
    assert _env.rel_path(str(src), str(tmp_path / "repo")) == "skills/video-routing"


def test_rel_path_falls_back_to_absolute_when_no_relative_route_exists(tmp_path, monkeypatch):
    """Hai đường KHÁC GỐC là hợp lệ, không phải lỗi — trả đường tuyệt đối, đừng ném.

    Trên Windows `os.path.relpath` ném `ValueError` khi hai đường nằm trên hai ổ đĩa khác
    nhau. Máy phát triển để mọi thứ trên một ổ nên không bao giờ thấy nhánh đó; ở đây nó
    được dựng lại đúng như runner CI (checkout `D:\\a\\…`, thư mục tạm `C:\\…`) bằng cách
    cho chính `os.path.relpath` ném — nên phép thử chạy y hệt trên macOS.
    """
    def boom(path, start=os.curdir):
        raise ValueError(f"path is on mount {path!r}, start on mount {start!r}")

    monkeypatch.setattr(os.path, "relpath", boom)
    got = _env.rel_path(str(tmp_path / "a" / "b"), str(tmp_path / "khác-gốc"))
    assert got == str(tmp_path / "a" / "b").replace(os.sep, "/")
    assert not got.startswith(".."), "không có đường tương đối thì phải là đường TUYỆT ĐỐI"


@pytest.mark.skipif(os.name != "nt", reason="ổ đĩa riêng biệt là khái niệm của Windows")
def test_rel_path_survives_two_windows_drives():
    """Không cần máy có ổ `D:` thật: `ntpath.relpath` so mặt chữ nên vẫn ném đúng chỗ đó."""
    assert _env.rel_path(r"C:\Temp\skills\hf-core", r"D:\a\repo") == "C:/Temp/skills/hf-core"


# ── HyperFrames ─────────────────────────────────────────────────────────────────────────

def test_hyperframes_default_version():
    # Bản ghi thẳng ở đây CỐ Ý: đổi mặc định là quyết định phải qua render hồi quy
    # (PVi-T13), nên nó phải làm đỏ một test chứ không lặng lẽ trôi theo hằng số.
    assert _env.hyperframes_version() == _env.DEFAULT_HYPERFRAMES_VERSION == "0.8.54"


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


def _fake_voice_repo(monkeypatch, resolve):
    """Repo giọng GIẢ trong sys.modules, chỉ đủ `voice_studio._env.resolve_station()`."""
    import importlib.machinery
    import sys
    import types
    pkg = types.ModuleType("voice_studio")
    pkg.__path__ = []
    # `find_spec` trả `__spec__` của module đã nạp — không có spec thì nó ném ValueError.
    pkg.__spec__ = importlib.machinery.ModuleSpec("voice_studio", None, is_package=True)
    mod = types.ModuleType("voice_studio._env")
    mod.resolve_station = resolve
    pkg._env = mod
    monkeypatch.setitem(sys.modules, "voice_studio", pkg)
    monkeypatch.setitem(sys.modules, "voice_studio._env", mod)


def test_voice_station_takes_what_the_voice_repo_was_told(tmp_path, monkeypatch):
    """Không biến ⇒ hỏi repo giọng; nhận trạm nó ĐÃ ĐƯỢC CHỌN (workspace/, studio.local.json)."""
    ws = tmp_path / "voice-repo" / "workspace"
    ws.mkdir(parents=True)
    _fake_voice_repo(monkeypatch, lambda: (str(ws), "workspace"))
    assert _env.voice_station() == str(ws)


@pytest.mark.parametrize("answer", [
    ("~/.voice", "default"),                 # nó tự đoán ở home — không phải lựa chọn của ai
    ("/nowhere/workspace", "workspace"),     # repo giọng chưa init
    (None, "unset"),
])
def test_voice_station_never_takes_a_guess(tmp_path, monkeypatch, answer):
    _fake_voice_repo(monkeypatch, lambda: answer)
    assert _env.voice_station() is None


def test_voice_station_survives_a_voice_repo_that_changed_shape(monkeypatch):
    def boom():
        raise AttributeError("bề mặt khác")
    _fake_voice_repo(monkeypatch, boom)
    assert _env.voice_station() is None


def test_voice_variable_beats_the_voice_repo(tmp_path, monkeypatch):
    _fake_voice_repo(monkeypatch, lambda: (str(tmp_path), "workspace"))
    monkeypatch.setenv("VOICE_STATION", str(tmp_path / "chosen"))
    assert _env.voice_station() == str(tmp_path / "chosen")


# ── repo anh em (thư mục cha tên gì cũng được, nhận bằng nội dung) ───────────────────────

def _clone(root, name, package):
    d = root / name
    (d / package).mkdir(parents=True)
    (d / package / "__init__.py").write_text("", encoding="utf-8")
    (d / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
    return d


@pytest.mark.parametrize("parent", ["Code", "Repo", "bat ky"])
def test_sibling_repo_is_found_by_content_under_any_parent(parent, tmp_path, monkeypatch):
    video = _clone(tmp_path / parent, "agent-video-studio", "video_studio")
    voice = _clone(tmp_path / parent, "ten-thu-muc-khac", "voice_studio")
    (tmp_path / parent / "khong-phai-repo").mkdir()
    monkeypatch.setenv("VIDEO_STUDIO_REPO", str(video))
    assert _env.sibling_repo("voice_studio") == str(voice)


def test_sibling_repo_never_guesses_between_two_clones(tmp_path, monkeypatch):
    video = _clone(tmp_path, "agent-video-studio", "video_studio")
    _clone(tmp_path, "voice-a", "voice_studio")
    _clone(tmp_path, "voice-b", "voice_studio")
    monkeypatch.setenv("VIDEO_STUDIO_REPO", str(video))
    assert _env.sibling_repo("voice_studio") is None


def test_sibling_repo_needs_a_repo(tmp_path, monkeypatch):
    monkeypatch.setenv("VIDEO_STUDIO_REPO", str(tmp_path / "khong-co"))
    assert _env.sibling_repo("voice_studio") is None


def test_sibling_repo_is_not_a_voice_station(tmp_path, monkeypatch):
    """Repo anh em chỉ để gợi ý lệnh cài: trạm giọng vẫn do chính repo giọng quyết."""
    video = _clone(tmp_path, "agent-video-studio", "video_studio")
    voice = _clone(tmp_path, "agent-voice-studio", "voice_studio")
    (voice / "workspace").mkdir()
    monkeypatch.setenv("VIDEO_STUDIO_REPO", str(video))
    monkeypatch.setitem(__import__("sys").modules, "voice_studio", None)
    assert _env.voice_station() is None
