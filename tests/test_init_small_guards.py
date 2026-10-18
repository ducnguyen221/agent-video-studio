"""Hai chỗ nhỏ: `--station` trỏ vào FILE phải là mã 2 (không phải lỗi hệ điều hành), và `migrate`
dời hỏng không được làm mất thư mục đích rỗng mà người dùng đã tạo sẵn."""
import pytest

from video_studio import station
from video_studio.contract import ContractError


@pytest.fixture
def repo(tmp_path, monkeypatch):
    r = tmp_path / "repo"
    (r / "video_studio").mkdir(parents=True)
    (r / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
    (r / ".env.example").write_text("# khuon\n", encoding="utf-8")
    monkeypatch.setenv("VIDEO_STUDIO_REPO", str(r))
    return r


def test_station_pointing_at_a_file_exits_2(repo, tmp_path, capsys):
    f = tmp_path / "la-mot-file"
    f.write_text("x", encoding="utf-8")
    assert station.init_main(["--station", str(f), "--non-interactive"]) == 2
    assert not f.is_dir() and f.read_text(encoding="utf-8") == "x"


def test_a_failed_migrate_gives_back_the_users_empty_target_dir(repo, tmp_path, monkeypatch):
    station.do_init(mode="embedded")
    target = tmp_path / "dich"
    target.mkdir()

    def boom(src, dst):
        raise ContractError("giả lập: file đang bị giữ")

    monkeypatch.setattr(station, "_move_tree", boom)
    with pytest.raises(ContractError):
        station.migrate_to_separate(str(target))
    assert target.is_dir() and not any(target.iterdir())
    assert (repo / "workspace").is_dir()
