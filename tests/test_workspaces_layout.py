"""Bố cục `workspaces`: thư mục gốc luôn tên `workspaces`.

* Cài riêng lẻ ⇒ trạm nhúng là chính `<repo>/workspaces` (thay cho `<repo>/workspace`); cài cùng
  OpcOS ⇒ `<OPCOS_WORKSPACES>/video`. Cùng thư mục gốc `workspaces`, chỉ khác nơi nằm.
* KHÔNG phá trạm nhúng cũ: `<repo>/workspace` mang dấu trạm mà `workspaces` chưa có ⇒ nhận
  nó và in MỘT dòng khuyến nghị đổi tên; cả hai cùng có ⇒ `workspaces` thắng + dòng nhắc.
  `init` mới không bao giờ tạo `workspace` số ít.
* Không còn tên thư mục ẩn ở thư mục cá nhân ở bất cứ đâu (mã, help, docs, test).
"""
import json
import os
import re
import subprocess
from pathlib import Path

import pytest

from video_studio import _env, precommit, station

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def repo(tmp_path, monkeypatch):
    r = tmp_path / "repo"
    (r / "video_studio").mkdir(parents=True)
    (r / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
    (r / ".env.example").write_text("# khuon\n", encoding="utf-8")
    monkeypatch.setenv("VIDEO_STUDIO_REPO", str(r))
    return r


def _old(repo):
    d = repo / "workspace"
    (d / "projects").mkdir(parents=True)
    (d / "station.json").write_text("{}", encoding="utf-8")
    return d


def test_init_embedded_builds_workspaces_and_never_the_singular_dir(repo):
    res = station.do_init(mode="embedded")
    st = repo / "workspaces"
    assert res["station"] == str(st) and (st / "station.json").is_file()
    assert not (repo / "workspace").exists()
    local = json.loads((repo / "studio.local.json").read_text(encoding="utf-8"))
    assert local["station_path"] == "workspaces"
    assert not (repo / "workspaces" / "video").exists()
    assert _env.resolve_station() == (str(st), "studio.local.json")      # init ghi lựa chọn


def test_resolution_prefers_the_new_layout_and_still_finds_the_old_one(repo):
    assert _env.resolve_station() == (str(repo / "workspaces"), "workspaces")
    old = _old(repo)
    assert _env.resolve_station() == (str(old), "workspace")        # tương thích: nhận trạm cũ
    new = repo / "workspaces"
    new.mkdir(parents=True)
    assert _env.resolve_station() == (str(new), "workspaces")       # cả hai: bản mới thắng


def test_an_unmarked_singular_dir_is_not_a_station(repo):
    (repo / "workspace").mkdir()
    assert _env.resolve_station() == (str(repo / "workspaces"), "workspaces")


def test_init_adopts_an_existing_old_embedded_station_and_says_so_once(repo, capsys):
    old = _old(repo)
    mode, path, _why = station.choose_mode(mode="embedded")
    assert (mode, path) == ("embedded", str(old))
    lines = [ln for ln in capsys.readouterr().err.splitlines() if "workspaces" in ln]
    assert len(lines) == 1 and "workspace" in lines[0]
    res = station.do_init(mode="embedded")
    assert res["station"] == str(old) and not (repo / "workspaces").exists()


def test_when_both_exist_the_new_one_wins_with_a_reminder(repo, capsys):
    _old(repo)
    new = repo / "workspaces"
    new.mkdir(parents=True)
    mode, path, _why = station.choose_mode(mode="embedded")
    assert path == str(new)
    assert len([ln for ln in capsys.readouterr().err.splitlines() if "workspaces" in ln]) == 1


def test_a_fresh_init_prints_no_reminder(repo, capsys):
    station.choose_mode(mode="embedded")
    assert "bố cục cũ" not in capsys.readouterr().err


def test_the_gitignore_and_the_precommit_hook_cover_both_layouts():
    text = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert "/workspaces/" in text and "/workspace/" in text
    assert "workspaces/" in precommit.BLOCKED_PREFIXES and "workspace/" in precommit.BLOCKED_PREFIXES


def test_migrate_moves_the_old_singular_station_too(repo, tmp_path):
    old = _old(repo)
    (old / "projects" / "p.txt").write_text("x", encoding="utf-8")
    target = tmp_path / "ngoai"
    res = station.migrate_to_separate(str(target))
    assert res["station"] == str(target) and (target / "projects" / "p.txt").is_file()
    assert not old.exists()


def test_migrate_moves_the_new_layout(repo, tmp_path):
    station.do_init(mode="embedded")
    target = tmp_path / "ngoai"
    station.migrate_to_separate(str(target))
    assert (target / "station.json").is_file()
    assert not (repo / "workspaces").exists()


# ── không còn thư mục ẩn ở thư mục cá nhân ────────────────────────────────────────────────

HIDDEN = re.compile(r"(?<![\w])\.video(?![\w-])")


def _tracked_text_files():
    out = subprocess.run(["git", "-C", str(ROOT), "ls-files"], capture_output=True, text=True,
                         encoding="utf-8").stdout.split("\n")
    for rel in out:
        if not rel or rel.endswith((".png", ".jpg", ".woff2", ".mp4", ".zip")):
            continue
        p = ROOT / rel
        if p.is_file() and rel != "tests/test_workspaces_layout.py":
            yield rel, p.read_text(encoding="utf-8", errors="replace")


def _unreleased(text):
    m = re.search(r"## Chưa phát hành\n(.*?)(?=\n## )", text, re.S)
    return m.group(1) if m else ""


def test_no_tracked_file_names_the_hidden_home_folder():
    bad = []
    for rel, text in _tracked_text_files():
        if rel == "docs/CHANGELOG.md":
            text = _unreleased(text)            # bản đã phát hành giữ nguyên chữ
        for n, line in enumerate(text.splitlines(), 1):
            if HIDDEN.search(line):
                bad.append(f"{rel}:{n}")
    assert not bad, bad[:20]


def test_the_helper_for_the_hidden_folder_is_gone():
    assert not hasattr(_env, "legacy_station") and not hasattr(_env, "default_station")


def test_the_changelog_says_the_change_in_one_clean_sentence():
    text = _unreleased((ROOT / "docs" / "CHANGELOG.md").read_text(encoding="utf-8"))
    assert "thư mục trạm cũ ẩn trong thư mục cá nhân không còn được tự nhận" in text.lower()
    assert "--station <đường>" in text
    assert "<biến>/video" in text and "<repo>/workspaces" in text and "OPCOS_WORKSPACES" in text
