"""Một số phiên bản cho mọi nơi khai phiên bản, và nhật ký thay đổi nói đúng số đó.

Bump phiên bản phải đổi đủ năm chỗ cùng lúc (`pyproject.toml`, `video_studio/__init__.py`, hai
manifest Claude, một manifest Codex); lệch một chỗ thì marketplace, gói Python và ghi chú phát
hành nói ba phiên bản khác nhau. `docs/CHANGELOG.md` có thể mở đầu bằng mục **Chưa phát hành**;
mục CÓ SỐ đầu tiên phải là bản đang khai.
"""
import json
import re
from pathlib import Path

from video_studio import __version__

ROOT = Path(__file__).resolve().parent.parent
CHANGELOG = ROOT / "docs" / "CHANGELOG.md"
UNRELEASED = "Chưa phát hành"


def _read(rel):
    return (ROOT / rel).read_text(encoding="utf-8")


def manifest_versions():
    found = {}
    m = re.search(r'^version\s*=\s*"([^"]+)"', _read("pyproject.toml"), re.M)
    found["pyproject.toml"] = m.group(1) if m else None
    m = re.search(r'^__version__\s*=\s*"([^"]+)"', _read("video_studio/__init__.py"), re.M)
    found["video_studio/__init__.py"] = m.group(1) if m else None
    found[".claude-plugin/plugin.json"] = json.loads(_read(".claude-plugin/plugin.json")).get("version")
    found[".codex-plugin/plugin.json"] = json.loads(_read(".codex-plugin/plugin.json")).get("version")
    for p in json.loads(_read(".claude-plugin/marketplace.json")).get("plugins", []):
        found[f".claude-plugin/marketplace.json#{p.get('name')}"] = p.get("version")
    return found


def test_every_manifest_states_one_version():
    v = manifest_versions()
    assert None not in v.values(), f"thiếu trường version: {v}"
    assert set(v.values()) == {__version__}, f"phiên bản lệch giữa các nơi khai: {v}"


def test_version_is_a_plain_release_or_a_dev_pre_release():
    assert re.fullmatch(r"\d+\.\d+\.\d+(?:\.dev\d+)?", __version__), __version__


def _headings():
    return re.findall(r"^## (.+)$", CHANGELOG.read_text(encoding="utf-8"), re.M)


def test_changelog_first_numbered_entry_is_the_current_version():
    base = __version__.split(".dev")[0]
    numbered = [h for h in _headings() if re.match(r"\d+\.\d+\.\d+", h)]
    assert numbered, "docs/CHANGELOG.md chưa có mục phiên bản nào"
    assert numbered[0].split()[0] in (__version__, base), (
        f"mục có số đầu tiên của CHANGELOG là {numbered[0]!r}, gói đang là {__version__}")


def test_unreleased_can_only_sit_on_top():
    heads = _headings()
    assert all(h != UNRELEASED for h in heads[1:]), "mục 'Chưa phát hành' chỉ được đứng đầu"
