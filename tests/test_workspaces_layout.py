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
    assert _env.resolve_station() == (str(st), "workspaces")             # config embedded không được tin như chuỗi


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

#: Tên thư mục ẩn của CẢ BA trạm (video, voice, marketing) ở các dạng `~/.x`, `/.x/`, biến-thư-mục-cá-nhân kiểu Windows,
#: `$HOME/.x`. Đứng sau một ký tự chữ (vd `args.video`, `module.voice`) thì không tính.
HIDDEN = re.compile(r"(?<![\w])\.(video|voice|marketing)(?![\w-])")
SKIP_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", ".pytest_cache", ".worktrees",
             ".tmp", "workspaces", "workspace", "out", "work", "scratch", "cache"}
SKIP_FILES = {"tests/test_workspaces_layout.py", ".env", "studio.local.json"}
BINARY = (".png", ".jpg", ".jpeg", ".webp", ".gif", ".woff", ".woff2", ".ttf", ".mp4", ".mov", ".mp3",
          ".wav", ".zip", ".pt", ".onnx", ".safetensors", ".pyc")


def _walk_text_files(root):
    """Duyệt bằng `os.walk` (không cần git: bản `git archive`/wheel cũng được quét)."""
    for dp, dn, fn in os.walk(root):
        dn[:] = sorted(d for d in dn if d not in SKIP_DIRS)
        for name in sorted(fn):
            p = Path(dp) / name
            rel = p.relative_to(root).as_posix()
            if rel in SKIP_FILES or name.endswith(BINARY):
                continue
            yield rel, p.read_text(encoding="utf-8", errors="replace")


def _unreleased(text):
    m = re.search(r"## Chưa phát hành\n(.*?)(?=\n## )", text, re.S)
    return m.group(1) if m else ""


def _hidden_hits(root):
    bad, seen = [], 0
    for rel, text in _walk_text_files(root):
        seen += 1
        if rel == "docs/CHANGELOG.md":
            text = _unreleased(text)            # bản đã phát hành giữ nguyên chữ
        for n, line in enumerate(text.splitlines(), 1):
            if HIDDEN.search(line):
                bad.append(f"{rel}:{n}")
    return bad, seen


def test_no_file_names_a_hidden_home_folder_of_any_of_the_three_stations():
    bad, seen = _hidden_hits(ROOT)
    assert seen > 100, f"quét quá ít file ({seen}) — bộ duyệt hỏng thì test này xanh giả"
    assert not bad, bad[:20]


@pytest.mark.parametrize("name", ["video", "voice", "marketing"])
@pytest.mark.parametrize("form", ["~/.{n}", "%USER" + "PROFILE%\\.{n}", "$HOME/.{n}", "x/.{n}/y"])
def test_the_scanner_catches_an_injected_string_without_git(tmp_path, name, form):
    """Đột biến: chèn chuỗi cấm vào một file mã trong một cây KHÔNG có `.git` ⇒ phải đỏ."""
    (tmp_path / "video_studio").mkdir()
    for i in range(3):
        (tmp_path / "video_studio" / f"m{i}.py").write_text("x = 1\n", encoding="utf-8")
    assert _hidden_hits(tmp_path)[0] == []
    (tmp_path / "video_studio" / "m0.py").write_text("# " + form.format(n=name) + "\n", encoding="utf-8")
    assert _hidden_hits(tmp_path)[0] == ["video_studio/m0.py:1"]


def test_attribute_access_is_not_mistaken_for_a_hidden_folder(tmp_path):
    (tmp_path / "a.py").write_text("print(args.video, mod.voice, self.marketing)\n", encoding="utf-8")
    assert _hidden_hits(tmp_path)[0] == []


# ── hành vi: một trạm mồi ở thư mục ẩn của thư mục cá nhân KHÔNG bao giờ được dùng ───────────

@pytest.mark.parametrize("name", ["video", "voice", "marketing"])
def test_a_decoy_station_in_a_hidden_home_folder_is_never_used(repo, tmp_path, monkeypatch, name):
    from video_studio import doctor
    home = tmp_path / "home"
    decoy = home / ("." + name)                   # dựng bằng chuỗi GHÉP — file này không nêu tên nó
    (decoy / "projects").mkdir(parents=True)
    (decoy / "station.json").write_text("{}", encoding="utf-8")
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    st, src = _env.resolve_station()
    assert st == str(repo / "workspaces") and src == "workspaces"
    assert station.choose_mode(yes=True)[1] == str(repo / "workspaces")
    with pytest.raises(Exception):
        station.choose_mode(mode="separate", non_interactive=True)      # không biến ⇒ mã 2, không rơi về home
    texts = [c["detail"] + c.get("hint", "") for c in doctor.station_checks(st, src)]
    assert all(str(decoy) not in t for t in texts)
    before = sorted(p.name for p in decoy.rglob("*"))
    station.do_init(mode="embedded")
    assert sorted(p.name for p in decoy.rglob("*")) == before            # không đụng byte nào


# ── studio.local.json cũ ghi `station_path` tương đối: không tin chuỗi ở chế độ embedded ────

def _config(repo, kind):
    if kind == "none":
        return
    name = "workspace" if kind == "old" else "workspaces"
    (repo / "studio.local.json").write_text(
        json.dumps({"mode": "embedded", "station_path": name}), encoding="utf-8")


def _tier(repo, tier):
    if tier in ("A", "C"):
        _old(repo)
    if tier in ("B", "C"):
        (repo / "workspaces").mkdir(parents=True)


@pytest.mark.parametrize("cfg", ["old", "new", "none"])
@pytest.mark.parametrize("tier,want", [("A", "workspace"), ("B", "workspaces"), ("C", "workspaces")])
def test_a_relative_workspace_station_path_goes_through_the_shared_resolution(
        repo, capsys, monkeypatch, cfg, tier, want):
    """(A) chỉ `workspace` cũ · (B) đã đổi tên sang `workspaces` (config còn ghi tên cũ — ca doctor
    khuyên đổi tên) · (C) có cả hai ⇒ `workspaces` thắng. Config ghi tên nào cũng vậy."""
    monkeypatch.setattr(_env, "_NOTED", set())
    _tier(repo, tier)
    _config(repo, cfg)
    st, _src = _env.resolve_station()
    assert st == str(repo / want)
    lines = [ln for ln in capsys.readouterr().err.splitlines() if "bố cục cũ" in ln]
    assert len(lines) == (1 if tier in ("A", "C") else 0)
    _env.resolve_station()
    assert not [ln for ln in capsys.readouterr().err.splitlines() if "bố cục cũ" in ln]   # một lần


def test_a_separate_config_or_an_other_path_is_still_trusted(repo, tmp_path):
    _old(repo)
    (repo / "studio.local.json").write_text(
        json.dumps({"mode": "separate", "station_path": "workspace"}), encoding="utf-8")
    assert _env.resolve_station()[0] == str(repo / "workspace")
    (repo / "studio.local.json").write_text(
        json.dumps({"mode": "embedded", "station_path": str(tmp_path / "ngoai")}), encoding="utf-8")
    assert _env.resolve_station() == (str(tmp_path / "ngoai"), "studio.local.json")
    (repo / "studio.local.json").write_text(
        json.dumps({"mode": "embedded", "station_path": "sub/dir"}), encoding="utf-8")
    assert _env.resolve_station()[0] == str(repo / "sub" / "dir")


def test_init_rewrites_an_old_station_path_to_the_new_name(repo):
    _old(repo)
    (repo / "studio.local.json").write_text(
        json.dumps({"mode": "embedded", "station_path": "workspace"}), encoding="utf-8")
    station.do_init(mode="embedded")
    local = json.loads((repo / "studio.local.json").read_text(encoding="utf-8"))
    assert local["station_path"] == "workspaces"
    assert _env.resolve_station()[0] == str(repo / "workspace")        # vẫn nhận trạm cũ


def test_migrate_uses_the_resolved_embedded_station_when_both_exist(repo, tmp_path):
    old = _old(repo)
    new = repo / "workspaces"
    new.mkdir()
    (new / "station.json").write_text("{}", encoding="utf-8")
    target = tmp_path / "ngoai"
    station.migrate_to_separate(str(target))
    assert (target / "station.json").is_file() and old.is_dir() and not new.exists()


def test_the_helper_for_the_hidden_folder_is_gone():
    assert not hasattr(_env, "legacy_station") and not hasattr(_env, "default_station")


def test_the_changelog_says_the_change_in_one_clean_sentence():
    text = _unreleased((ROOT / "docs" / "CHANGELOG.md").read_text(encoding="utf-8"))
    assert "thư mục trạm cũ ẩn trong thư mục cá nhân không còn được tự nhận" in text.lower()
    assert "--station <đường>" in text
    assert "<biến>/video" in text and "<repo>/workspaces" in text and "OPCOS_WORKSPACES" in text
