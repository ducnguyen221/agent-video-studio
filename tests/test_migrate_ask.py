"""`video-studio migrate --to separate` phải HỎI nơi dời, không tự dời vào một thư mục ẩn ở thư mục cá nhân.

Luật: không có `--station` ⇒ hỏi (gợi ý `<OPCOS_WORKSPACES>/video` nếu biến có), hiện đường
tuyệt đối + số file/dung lượng rồi xin xác nhận y/N; không có người ⇒ dừng mã 2. Biến chỉ đọc
từ môi trường thật. Không còn đường mặc định ngầm vào thư mục ẩn ở home.
"""
import os
import errno
import builtins
import hashlib
import json

import pytest

from video_studio import station
from video_studio.cli import main as cli_main
from video_studio.contract import ContractError


@pytest.fixture
def repo(tmp_path, monkeypatch):
    r = tmp_path / "repo"
    (r / "video_studio").mkdir(parents=True)
    (r / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
    (r / ".env.example").write_text("# khuon\nVIDEO_FONT=\n", encoding="utf-8")
    monkeypatch.setenv("VIDEO_STUDIO_REPO", str(r))
    station.do_init(mode="embedded")
    (r / "workspaces" / "projects" / "news").mkdir(parents=True)
    (r / "workspaces" / "projects" / "news" / "meta.json").write_text("{}", encoding="utf-8")
    return r


def _script(*answers):
    """Trả lời lần lượt; ghi lại các câu hỏi để kiểm nội dung."""
    seen, it = [], iter(answers)

    def ask(prompt):
        seen.append(prompt)
        return next(it)
    ask.seen = seen
    return ask


def test_no_station_asks_and_takes_the_typed_destination(repo, tmp_path):
    target = tmp_path / "ngoai"
    ask = _script(str(target), "y")
    res = station.migrate_to_separate(ask=ask)
    assert res["station"] == str(target)
    assert (target / "projects" / "news" / "meta.json").is_file()
    assert not (repo / "workspaces").exists()


def test_the_question_suggests_workspaces_video_and_shows_absolute_path_and_size(
        repo, tmp_path, monkeypatch):
    base = tmp_path / "ws"
    monkeypatch.setenv("OPCOS_WORKSPACES", str(base))
    ask = _script("", "y")                      # Enter = nhận gợi ý
    res = station.migrate_to_separate(ask=ask)
    expect = os.path.abspath(str(base / "video"))
    assert res["station"] == expect
    assert expect in ask.seen[0] and "gợi ý" in ask.seen[0].lower()
    # lượt xác nhận nêu đích tuyệt đối + số file + dung lượng sẽ dời
    assert expect in ask.seen[1] and "file" in ask.seen[1] and "y/N" in ask.seen[1]


def test_a_relative_opcos_workspaces_is_shown_and_used_as_absolute(repo, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("OPCOS_WORKSPACES", "rel-ws")
    ask = _script("", "y")
    res = station.migrate_to_separate(ask=ask)
    assert os.path.isabs(res["station"])
    assert res["station"] == os.path.abspath(os.path.join("rel-ws", "video"))


def test_no_suggestion_and_empty_answer_stops_without_moving(repo, tmp_path):
    with pytest.raises(ContractError):
        station.migrate_to_separate(ask=_script(""))
    assert (repo / "workspaces").is_dir()


@pytest.mark.parametrize("no", ["", "n", "N", "no", "khong"])
def test_anything_but_yes_cancels_and_moves_nothing(repo, tmp_path, no):
    target = tmp_path / "ngoai"
    with pytest.raises(ContractError, match="huỷ"):
        station.migrate_to_separate(ask=_script(str(target), no))
    assert (repo / "workspaces" / "projects" / "news" / "meta.json").is_file()
    assert not target.exists()


def test_never_defaults_to_the_hidden_home_station(repo, tmp_path, monkeypatch):
    """Gợi ý nơi dời không bao giờ là một thư mục ẩn ở thư mục cá nhân."""
    monkeypatch.setenv("OPCOS_WORKSPACES", str(tmp_path / "ws"))
    ask = _script("", "n")
    with pytest.raises(ContractError):
        station.migrate_to_separate(ask=ask)
    assert all(os.path.expanduser("~") not in p for p in ask.seen)


def test_an_explicit_target_does_not_ask(repo, tmp_path):
    def boom(prompt):
        pytest.fail("đã có --station thì không hỏi")

    res = station.migrate_to_separate(str(tmp_path / "ngoai"), ask=boom)
    assert res["station"] == str(tmp_path / "ngoai")


def test_a_target_inside_the_workspace_is_refused(repo):
    with pytest.raises(ContractError, match="nằm trong trạm đang dời"):
        station.migrate_to_separate(str(repo / "workspaces" / "con"))
    assert (repo / "workspaces").is_dir()


def test_cli_non_interactive_without_station_is_exit_2_and_names_the_flag(repo, capsys):
    code = cli_main(["migrate", "--to", "separate", "--non-interactive"])
    err = capsys.readouterr().err
    assert code == 2 and "--station" in err and "bắt buộc" in err
    assert (repo / "workspaces").is_dir()


def test_cli_without_a_tty_and_without_station_is_exit_2(repo, capsys, monkeypatch):
    monkeypatch.setattr(station, "_stdin_is_tty", lambda: False)
    code = cli_main(["migrate", "--to", "separate"])
    err = capsys.readouterr().err
    assert code == 2 and "--station" in err and "bắt buộc" in err
    assert (repo / "workspaces").is_dir()


def test_cli_with_station_moves_without_asking(repo, tmp_path):
    target = tmp_path / "ngoai"
    code = cli_main(["migrate", "--to", "separate", "--station", str(target),
                     "--non-interactive"])
    assert code == 0
    assert (target / "projects" / "news" / "meta.json").is_file()


def test_the_help_does_not_promise_the_hidden_default(capsys):
    assert station.migrate_main(["--help"]) == 0
    assert os.path.expanduser("~") not in capsys.readouterr().out


def test_a_destination_that_is_a_file_is_a_clear_error_not_a_traceback(repo, tmp_path):
    f = tmp_path / "la-file"
    f.write_text("x", encoding="utf-8")
    with pytest.raises(ContractError, match="không phải thư mục"):
        station.migrate_to_separate(str(f))
    ask = _script(str(f), "y")
    with pytest.raises(ContractError, match="không phải thư mục"):
        station.migrate_to_separate(ask=ask)
    assert len(ask.seen) == 1 and f.read_text(encoding="utf-8") == "x"
    assert (repo / "workspaces").is_dir()
    assert cli_main(["migrate", "--to", "separate", "--station", str(f)]) == 2


def test_a_pasted_quoted_destination_is_unquoted(repo, tmp_path):
    target = tmp_path / "co dau cach"
    res = station.migrate_to_separate(ask=_script(f'"{target}"', "y"))
    assert res["station"] == str(target) and (target / "projects" / "news" / "meta.json").is_file()


def test_an_existing_secret_env_is_reported_before_the_y_n_question(repo, tmp_path, monkeypatch):
    """Không để người dùng trả lời y rồi mới nghe ".env đã có": kiểm xong trước khi xin y/N."""
    home = tmp_path / "home"
    (home / ".secret" / station.SECRET_DIR_NAME).mkdir(parents=True)
    (home / ".secret" / station.SECRET_DIR_NAME / ".env").write_text("x=1\n", encoding="utf-8")
    monkeypatch.setenv("USERPROFILE", str(home))
    monkeypatch.setenv("HOME", str(home))
    (repo / ".env").write_text("A=1\n", encoding="utf-8")
    ask = _script(str(tmp_path / "ngoai"), "y")
    with pytest.raises(ContractError, match="đã có"):
        station.migrate_to_separate(ask=ask)
    assert len(ask.seen) == 1                    # chỉ câu hỏi đường; chưa tới câu y/N
    assert (repo / "workspaces").is_dir()


def _tree_snapshot(root):
    """Exact directory/file snapshot for migration failure assertions."""
    result = {}
    for current, dirs, files in os.walk(root):
        rel = os.path.relpath(current, root)
        for name in dirs:
            result[os.path.normpath(os.path.join(rel, name))] = "<dir>"
        for name in files:
            path = os.path.join(current, name)
            with builtins.open(path, "rb") as stream:
                result[os.path.normpath(os.path.join(rel, name))] = hashlib.sha256(
                    stream.read()).hexdigest()
    return result


def test_config_write_failure_after_tree_move_restores_all_migration_state(
        repo, tmp_path, monkeypatch):
    home = tmp_path / "fake-home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    source = repo / "workspaces"
    target = tmp_path / "separate-station"
    env = repo / ".env"
    env.write_text("TEST_ONLY=not-a-secret\n", encoding="utf-8")
    env_bytes = env.read_bytes()
    config = repo / station._env.LOCAL_CONFIG
    config.write_bytes(b'{"mode":"embedded","station_path":"old"}\n')
    config_state = (config.exists(), config.read_bytes() if config.exists() else None)
    source_before = _tree_snapshot(source)
    marker = source / station._env.STATION_FILE
    marker_state = (marker.exists(), marker.read_bytes() if marker.exists() else None)
    secret_env = home / ".secret" / station.SECRET_DIR_NAME / ".env"
    assert not target.exists() and not secret_env.exists()

    real_move_tree = station._move_tree
    moved = {"done": False}

    def move_then_mark(src, dst):
        real_move_tree(src, dst)
        moved["done"] = True

    real_open = builtins.open
    injected = {"count": 0, "path": None, "stage": None}

    class FailAfterPartialWrite:
        def __init__(self, stream):
            self.stream = stream

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return self.stream.__exit__(*exc)

        def write(self, data):
            assert moved["done"], "local config injection must follow the completed workspace move"
            written = self.stream.write(data[:3])
            self.stream.flush()
            injected.update(count=1, path=str(config), stage="after-move-config-known-short-write")
            return written

        def __getattr__(self, name):
            return getattr(self.stream, name)

    def fail_after_partial_config_write(path, mode="r", *args, **kwargs):
        if (os.path.normcase(os.fspath(path)) == os.path.normcase(str(config)) and
                mode == "r+b" and injected["count"] == 0):
            return FailAfterPartialWrite(real_open(path, mode, *args, **kwargs))
        return real_open(path, mode, *args, **kwargs)

    monkeypatch.setattr(station, "_move_tree", move_then_mark)
    monkeypatch.setattr(station, "open", fail_after_partial_config_write, raising=False)
    with pytest.raises(OSError, match="metadata short write"):
        station.migrate_to_separate(str(target))

    assert moved["done"] and injected == {
        "count": 1, "path": str(config), "stage": "after-move-config-known-short-write"}
    expected = {
        "source_tree": source_before,
        "marker": marker_state,
        "config": config_state,
        "source_env": env_bytes,
        "destination_exists": False,
        "secret_dir_exists": False,
        "secret_env_exists": False,
    }
    actual = {
        "source_tree": _tree_snapshot(source) if source.is_dir() else None,
        "marker": (marker.exists(), marker.read_bytes() if marker.exists() else None),
        "config": (config.exists(), config.read_bytes() if config.exists() else None),
        "source_env": env.read_bytes() if env.is_file() else None,
        "destination_exists": target.exists(),
        "secret_dir_exists": secret_env.parent.exists(),
        "secret_env_exists": secret_env.exists(),
    }
    assert actual == expected


def test_opaque_config_write_failure_retains_uncertain_artifacts(repo, tmp_path, monkeypatch):
    home = tmp_path / "fake-home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    source = repo / "workspaces"
    target = tmp_path / "separate-station"
    env = repo / ".env"
    env.write_text("TEST_ONLY=not-a-secret\n", encoding="utf-8")
    config = repo / station._env.LOCAL_CONFIG
    config.write_bytes(b'{"mode":"embedded","station_path":"old"}\n')
    config_id = (config.stat().st_dev, config.stat().st_ino)
    secret_env = home / ".secret" / station.SECRET_DIR_NAME / ".env"
    assert not target.exists() and not secret_env.exists()

    real_open = builtins.open
    injected = {"count": 0, "foreign_bytes": None}

    class OpaqueWriteThenRaise:
        def __init__(self, stream):
            self.stream = stream

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return self.stream.__exit__(*exc)

        def write(self, data):
            self.stream.seek(0)
            self.stream.write(data[:1])
            self.stream.flush()
            # Same-inode foreign content extends the prefix-shaped state after the write call
            # began. Since write() never returned, its byte count is unknown to the transaction.
            self.stream.seek(1)
            self.stream.write(data[1:2])
            self.stream.flush()
            self.stream.seek(1)
            self.stream.seek(0)
            injected["foreign_bytes"] = self.stream.read()
            injected["count"] += 1
            raise OSError("injected opaque config write failure")

        def __getattr__(self, name):
            return getattr(self.stream, name)

    def fail_opaquely_once(path, mode="r", *args, **kwargs):
        if (os.path.normcase(os.fspath(path)) == os.path.normcase(str(config)) and
                mode == "r+b" and injected["count"] == 0):
            return OpaqueWriteThenRaise(real_open(path, mode, *args, **kwargs))
        return real_open(path, mode, *args, **kwargs)

    monkeypatch.setattr(station, "open", fail_opaquely_once, raising=False)
    with pytest.raises(station.ContractError, match="rollback incomplete") as exc:
        station.migrate_to_separate(str(target))

    assert "injected opaque config write failure" in str(exc.value)
    assert injected["count"] == 1
    assert (config.stat().st_dev, config.stat().st_ino) == config_id
    assert config.read_bytes() == injected["foreign_bytes"]
    assert not source.exists() and target.is_dir()
    assert not env.exists() and secret_env.read_text(encoding="utf-8") == "TEST_ONLY=not-a-secret\n"


def test_absent_config_created_by_migration_is_retained_as_recovery_incomplete(
        repo, tmp_path, monkeypatch):
    home = tmp_path / "fake-home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    source = repo / "workspaces"
    target = tmp_path / "separate-station"
    env = repo / ".env"
    env.write_text("TEST_ONLY=not-a-secret\n", encoding="utf-8")
    config = repo / station._env.LOCAL_CONFIG
    config.unlink(missing_ok=True)
    marker = source / station._env.STATION_FILE
    assert marker.is_file()
    secret_env = home / ".secret" / station.SECRET_DIR_NAME / ".env"
    real_open = builtins.open

    def fail_before_marker_write(path, mode="r", *args, **kwargs):
        if (os.path.normcase(os.fspath(path)) == os.path.normcase(
                str(target / station._env.STATION_FILE)) and mode == "r+b"):
            raise OSError("injected marker open failure")
        return real_open(path, mode, *args, **kwargs)

    monkeypatch.setattr(station, "open", fail_before_marker_write, raising=False)
    with pytest.raises(station.ContractError, match="rollback incomplete") as exc:
        station.migrate_to_separate(str(target))

    assert "injected marker open failure" in str(exc.value)
    assert "created during migration and is retained" in str(exc.value)
    assert config.is_file() and json.loads(config.read_text(encoding="utf-8"))["mode"] == "separate"
    assert not source.exists() and target.is_dir()
    assert not env.exists() and secret_env.read_text(encoding="utf-8") == "TEST_ONLY=not-a-secret\n"


@pytest.mark.parametrize("restore_case", ["collision", "exdev", "posix", "posix_unlink_fails"])
def test_env_restore_refuses_collision_cross_device_and_restores_posix_by_link(
        repo, tmp_path, monkeypatch, restore_case):
    home = tmp_path / "fake-home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    source = repo / "workspaces"
    target = tmp_path / "separate-station"
    env = repo / ".env"
    env.write_text("TEST_ONLY=not-a-secret\n", encoding="utf-8")
    config = repo / station._env.LOCAL_CONFIG
    config.write_bytes(b'{"mode":"embedded","station_path":"old"}\n')
    config_before = config.read_bytes()
    secret_env = home / ".secret" / station.SECRET_DIR_NAME / ".env"
    moved = {"done": False}
    real_move = station._move_tree
    real_open = builtins.open
    injected = {"write": 0, "restore_attempt": 0}

    def move_then_mark(src, dst):
        real_move(src, dst)
        moved["done"] = True

    class KnownShortWrite:
        def __init__(self, stream):
            self.stream = stream

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return self.stream.__exit__(*exc)

        def write(self, data):
            assert moved["done"]
            count = self.stream.write(data[:3])
            self.stream.flush()
            injected["write"] += 1
            return count

        def __getattr__(self, name):
            return getattr(self.stream, name)

    def fail_config_write(path, mode="r", *args, **kwargs):
        if (os.path.normcase(os.fspath(path)) == os.path.normcase(str(config)) and
                mode == "r+b" and injected["write"] == 0):
            return KnownShortWrite(real_open(path, mode, *args, **kwargs))
        return real_open(path, mode, *args, **kwargs)

    real_rename = os.rename
    real_link = os.link
    moved_env = home / ".secret" / station.SECRET_DIR_NAME / ".env"

    def is_env_restore(src, dst):
        return (os.path.normcase(os.fspath(src)) == os.path.normcase(str(moved_env)) and
                os.path.normcase(os.fspath(dst)) == os.path.normcase(str(env)))

    def race_at_no_clobber_restore(primitive):
        # The restore primitive is os.rename on Windows and os.link on POSIX; inject the
        # same race into whichever one the platform uses.
        def restore(src, dst):
            if is_env_restore(src, dst) and injected["restore_attempt"] == 0:
                if restore_case.startswith("posix"):
                    if primitive is real_rename:
                        raise AssertionError("POSIX restore must never call overwriting os.rename")
                    injected["restore_attempt"] += 1
                    return primitive(src, dst)
                injected["restore_attempt"] += 1
                if restore_case == "collision":
                    env.write_bytes(b"FOREIGN-SOURCE")
                    raise FileExistsError("destination appeared at rename boundary")
                raise OSError(errno.EXDEV, "cross-device restore")
            return primitive(src, dst)
        return restore

    monkeypatch.setattr(station, "_move_tree", move_then_mark)
    monkeypatch.setattr(station, "open", fail_config_write, raising=False)
    monkeypatch.setattr(os, "rename", race_at_no_clobber_restore(real_rename))
    monkeypatch.setattr(os, "link", race_at_no_clobber_restore(real_link))
    real_unlink = os.unlink

    def fail_unlink_of_moved_env(path, *args, **kwargs):
        if os.path.normcase(os.fspath(path)) == os.path.normcase(str(moved_env)):
            raise PermissionError(errno.EACCES, "injected unlink failure", str(path))
        return real_unlink(path, *args, **kwargs)

    if restore_case == "posix_unlink_fails":
        monkeypatch.setattr(os, "unlink", fail_unlink_of_moved_env)
    if restore_case.startswith("posix"):
        expected = OSError if restore_case == "posix" else station.ContractError
        with monkeypatch.context() as platform_patch:
            platform_patch.setattr(os, "name", "posix")
            with pytest.raises(expected, match="metadata short write") as exc:
                station.migrate_to_separate(str(target))
    else:
        with pytest.raises(station.ContractError, match="rollback incomplete") as exc:
            station.migrate_to_separate(str(target))

    assert "metadata short write" in str(exc.value)
    if restore_case == "collision":
        assert "destination appeared at rename boundary" in str(exc.value)
        assert env.read_bytes() == b"FOREIGN-SOURCE"
    elif restore_case == "exdev":
        assert "cross-device restore" in str(exc.value)
        assert not env.exists()
    elif restore_case == "posix_unlink_fails":
        assert "rollback incomplete" in str(exc.value)
        assert "injected unlink failure" in str(exc.value)
        assert "two names for the SAME file" in str(exc.value)
        assert str(env) in str(exc.value) and str(moved_env) in str(exc.value)
    else:
        assert "rollback incomplete" not in str(exc.value)
    assert injected["write"] == 1
    assert config.read_bytes() == config_before
    assert injected["restore_attempt"] == 1
    if restore_case == "posix":
        # Hard-link restore is no-clobber, so POSIX completes the whole rollback.
        assert env.read_text(encoding="utf-8") == "TEST_ONLY=not-a-secret\n"
        assert not secret_env.exists()
        assert source.is_dir() and not target.exists()
    elif restore_case == "posix_unlink_fails":
        # Both names now refer to the one restored file; later steps stay where they are.
        assert os.path.samefile(env, secret_env)
        assert env.read_text(encoding="utf-8") == "TEST_ONLY=not-a-secret\n"
        assert not source.exists() and target.is_dir()
    else:
        assert secret_env.read_text(encoding="utf-8") == "TEST_ONLY=not-a-secret\n"
        assert not source.exists() and target.is_dir()


def test_dangling_source_symlink_is_retained_and_tree_move_back_is_skipped(
        repo, tmp_path, monkeypatch):
    home = tmp_path / "fake-home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    source = repo / "workspaces"
    target = tmp_path / "separate-station"
    config = repo / station._env.LOCAL_CONFIG
    config.write_bytes(b'{"mode":"embedded","station_path":"old"}\n')
    config_before = config.read_bytes()
    referent = tmp_path / "link-referent"
    referent.mkdir()
    displaced_referent = tmp_path / "link-referent-displaced"
    calls = []
    real_move = station._move_tree
    real_open = builtins.open
    injected = {"count": 0}

    def count_moves(src, dst):
        calls.append((os.path.normcase(os.fspath(src)), os.path.normcase(os.fspath(dst))))
        return real_move(src, dst)

    class CreateDanglingSourceAfterKnownWrite:
        def __init__(self, stream):
            self.stream = stream

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return self.stream.__exit__(*exc)

        def write(self, data):
            count = self.stream.write(data[:3])
            self.stream.flush()
            _junction(source, referent)
            referent.rename(displaced_referent)
            injected["count"] += 1
            return count

        def __getattr__(self, name):
            return getattr(self.stream, name)

    def inject_source_link(path, mode="r", *args, **kwargs):
        if (os.path.normcase(os.fspath(path)) == os.path.normcase(str(config)) and
                mode == "r+b" and injected["count"] == 0):
            return CreateDanglingSourceAfterKnownWrite(real_open(path, mode, *args, **kwargs))
        return real_open(path, mode, *args, **kwargs)

    monkeypatch.setattr(station, "_move_tree", count_moves)
    monkeypatch.setattr(station, "open", inject_source_link, raising=False)
    with pytest.raises(station.ContractError, match="rollback incomplete") as exc:
        station.migrate_to_separate(str(target))

    assert "source station path was recreated" in str(exc.value)
    assert injected["count"] == 1
    assert calls == [(os.path.normcase(str(source)), os.path.normcase(str(target)))]
    source_stat = os.lstat(source)
    assert os.path.lexists(source) and not os.path.exists(source)
    assert (os.path.islink(source) or
            bool(getattr(source_stat, "st_file_attributes", 0) & 0x400))
    assert displaced_referent.is_dir()
    assert config.read_bytes() == config_before
    assert target.is_dir()


def test_rollback_failure_preserves_known_partial_metadata_and_moved_artifacts(
        repo, tmp_path, monkeypatch):
    home = tmp_path / "fake-home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    source = repo / "workspaces"
    target = tmp_path / "separate-station"
    env = repo / ".env"
    env.write_text("TEST_ONLY=not-a-secret\n", encoding="utf-8")
    config = repo / station._env.LOCAL_CONFIG
    config.write_bytes(b'{"mode":"embedded","station_path":"old"}\n')
    secret_env = home / ".secret" / station.SECRET_DIR_NAME / ".env"
    real_open = builtins.open
    injected = {"write": 0, "restore": 0}

    class KnownShortWrite:
        def __init__(self, stream):
            self.stream = stream

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return self.stream.__exit__(*exc)

        def write(self, data):
            count = self.stream.write(data[:3])
            self.stream.flush()
            injected["write"] += 1
            return count

        def __getattr__(self, name):
            return getattr(self.stream, name)

    def inject_write_and_rollback_failure(path, mode="r", *args, **kwargs):
        if os.path.normcase(os.fspath(path)) == os.path.normcase(str(config)) and mode == "r+b":
            if injected["write"] == 0:
                return KnownShortWrite(real_open(path, mode, *args, **kwargs))
            injected["restore"] += 1
            raise OSError("injected rollback open failure")
        return real_open(path, mode, *args, **kwargs)

    monkeypatch.setattr(station, "open", inject_write_and_rollback_failure, raising=False)
    with pytest.raises(station.ContractError, match="rollback incomplete") as exc:
        station.migrate_to_separate(str(target))

    assert "metadata short write" in str(exc.value)
    assert "injected rollback open failure" in str(exc.value)
    assert injected == {"write": 1, "restore": 1}
    assert config.read_bytes() != b'{"mode":"embedded","station_path":"old"}\n'
    assert not source.exists() and target.is_dir()
    assert not env.exists() and secret_env.is_file()


def test_directory_symlink_inside_station_is_rejected_before_move(repo, tmp_path, monkeypatch):
    external = tmp_path / "external"
    external.mkdir()
    (external / "outside.txt").write_text("outside", encoding="utf-8")
    link = repo / "workspaces" / "linked-dir"
    _junction(link, external)
    target = tmp_path / "separate-station"
    called = {"move": 0}

    def unexpected_move(_src, _dst):
        called["move"] += 1
        raise AssertionError("tree move must not run for a station containing a link")

    monkeypatch.setattr(station, "_move_tree", unexpected_move)
    with pytest.raises(station.ContractError, match="symlink/junction/reparse"):
        station.migrate_to_separate(str(target))

    assert called["move"] == 0
    assert link.exists() and (external / "outside.txt").read_text(encoding="utf-8") == "outside"
    assert not target.exists()


# ── đích đi qua điểm nối (junction) vào chính trạm đang dời ─────────────────────────────────────

def _junction(link, target):
    """Tạo điểm nối `link → target` (Windows `mklink /J`, không cần quyền nâng); symlink ở nơi khác."""
    import subprocess
    try:
        os.symlink(str(target), str(link), target_is_directory=True)
        return
    except (OSError, NotImplementedError) as e:
        if os.name != "nt" or subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(target)],
                                             capture_output=True).returncode:
            pytest.skip(f"máy này không tạo được liên kết mềm lẫn điểm nối: {e}")


def test_a_target_through_a_junction_into_the_workspace_is_refused_before_touching_anything(
        repo, tmp_path):
    inside = repo / "workspaces" / "sub"
    inside.mkdir()
    (repo / "workspaces" / "data.txt").write_text("du lieu", encoding="utf-8")
    link = tmp_path / "lnk"
    _junction(link, inside)
    local_before = (repo / "studio.local.json").read_text(encoding="utf-8")
    with pytest.raises(ContractError, match="nằm trong trạm"):
        station.migrate_to_separate(str(link / "new"))
    assert (repo / "workspaces" / "data.txt").read_text(encoding="utf-8") == "du lieu"
    assert (repo / "studio.local.json").read_text(encoding="utf-8") == local_before
    assert not (inside / "new").exists() and not (link / "new").exists()


def test_a_junction_that_is_itself_the_target_is_refused_before_the_yes_no_question(repo, tmp_path):
    link = tmp_path / "lnk"
    _junction(link, repo / "workspaces")
    asked = []
    with pytest.raises(ContractError, match="nằm trong trạm"):
        station.migrate_to_separate(str(link), ask=lambda p: asked.append(p) or "y", confirm=True)
    assert asked == []
    assert (repo / "workspaces" / "projects" / "news" / "meta.json").is_file()


def test_a_workspace_that_is_itself_a_junction_still_refuses_a_target_inside_the_real_folder(
        repo, tmp_path):
    real = tmp_path / "that-su"
    os.rename(repo / "workspaces", real)
    _junction(repo / "workspaces", real)
    with pytest.raises(ContractError, match="nằm trong trạm"):
        station.migrate_to_separate(str(real / "new"))
    assert (real / "projects" / "news" / "meta.json").is_file()


def test_is_inside_compares_real_paths_in_both_directions(tmp_path):
    a = tmp_path / "a"
    (a / "b").mkdir(parents=True)
    link = tmp_path / "lnk"
    _junction(link, a)
    assert station._is_inside(str(link / "b"), str(a))
    assert station._is_inside(str(a / "b"), str(link))
    assert station._is_inside(str(a), str(link)) and not station._is_inside(str(tmp_path), str(a))
