"""Cổng của repo: `.gitignore` khoá đúng họ file, `pyproject` khai đúng entry point và không kéo
engine nặng vào lõi, manifest plugin đồng bộ, mã không có `shell=True` / bản HyperFrames trôi,
và trong cây không có file nhị phân media/model.
"""
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from video_studio import API_VERSION, __version__
from test_no_identity_leak import repo_files

ROOT = Path(__file__).resolve().parent.parent
GITIGNORE = ROOT / ".gitignore"


def _lines():
    return {ln.strip() for ln in GITIGNORE.read_text(encoding="utf-8").splitlines()}


# Xoá BẤT KỲ dòng nào dưới đây là test đỏ — kể cả khi một mẫu rộng hơn tình cờ vẫn chặn.
REQUIRED = ["*.mp4", "*.mov", "*.mp3", "*.wav", "*.png", "*.jpg", "*.woff2", "*.pt", "*.onnx",
            "out/", "work/", "scratch/", "cache/", "/workspace/", ".env", ".env.*",
            "!.env.example", "studio.local.json", "node_modules/"]


@pytest.mark.parametrize("line", REQUIRED)
def test_gitignore_keeps_required_line(line):
    assert line in _lines(), f".gitignore thiếu dòng bắt buộc: {line}"


@pytest.mark.skipif(not (shutil.which("git") and (ROOT / ".git").exists()),
                    reason="repo chưa git init (cổng này chạy từ PVi-G4)")
@pytest.mark.parametrize("path,ignored", [
    ("workspace/projects/news/index.html", True),
    (".env", True),
    (".env.example", False),
    ("studio.local.json", True),
    ("video_studio/out.mp4", True),
    ("templates/_seed/assets/grid.svg", False),
    ("templates/workspace/README.md", False),
    # Template mang theo HTML/JSON mẫu: tường chặn rò KHÔNG được nuốt chúng, nếu không bản
    # cài wheel thiếu file và `render` hỏng đúng lúc chạy thật.
    ("video_studio/templates/news/news_v2_components.html", False),
    ("video_studio/templates/news/repo_today_scenes.json", False),
    ("video_studio/templates/news/repo_today_input.json", False),
])
def test_git_really_ignores(path, ignored):
    r = subprocess.run(["git", "-C", str(ROOT), "check-ignore", "-q", "--no-index", path])
    assert (r.returncode == 0) is ignored, path


def test_no_media_or_model_binaries_in_tree():
    bad = [rel for rel, p in repo_files()
           if p.suffix.lower() in {".mp4", ".mov", ".mp3", ".wav", ".png", ".jpg", ".jpeg",
                                   ".gif", ".webp", ".woff", ".woff2", ".ttf", ".otf", ".pt"}]
    assert bad == [], f"file nhị phân media/model trong cây repo: {bad}"


# ── kỷ luật gọi tiến trình con và ghim bản ──────────────────────────────────────────────

def _code_files():
    return [(rel, p) for rel, p in repo_files()
            if p.suffix in (".py", ".ps1", ".sh", ".md", ".json", ".toml")
            and not rel.startswith("tests/")]


@pytest.mark.parametrize("pattern,why", [
    (r"shell\s*=\s*True", "POSIX chỉ chạy phần tử đầu của list khi shell=True — luôn dùng argv list"),
    (r"hyperframes@latest|@latest", "bản trôi: lịch chạy phải gọi đúng bản đã kiểm"),
    (r"0\.6\.80", "bản HyperFrames đã chết (không có trong cache nào)"),
])
def test_forbidden_pattern_absent(pattern, why):
    hits = [rel for rel, p in _code_files()
            if re.search(pattern, p.read_text(encoding="utf-8", errors="replace"))]
    assert hits == [], f"{why}: {hits}"


# Chuỗi lệnh = ký tự đầu của tham số 1 là dấu nháy (kể cả f"…"/r'…'). Biến hay list thì không.
_CMD_IS_STRING = re.compile(r"""^[fFrRbBuU]*["']""")


def _string_command_hits(text):
    return [m.group(1) for m in re.finditer(r"subprocess\.run\(\s*([^\n)]{0,6})", text)
            if _CMD_IS_STRING.match(m.group(1))]


def test_subprocess_calls_pass_a_list():
    """Mọi `subprocess.run(` trong package nhận biến/list, không nhận chuỗi lệnh."""
    for rel, p in repo_files():
        if not rel.startswith("video_studio/"):
            continue
        bad = _string_command_hits(p.read_text(encoding="utf-8"))
        assert bad == [], f"{rel}: subprocess.run nhận chuỗi lệnh: {bad}"


@pytest.mark.parametrize("snippet,caught", [
    ('subprocess.run("npx hyperframes render")', True),
    ("subprocess.run('ls -la')", True),
    ('subprocess.run(f"{npx} render")', True),
    ('subprocess.run([npx, "render"])', False),
    ("subprocess.run(argv, cwd=d)", False),
    ("subprocess.run(cmd, check=True)", False),
])
def test_string_command_detector(snippet, caught):
    """Đột biến: cổng trên phải bắt đúng thứ nó nhắm — và chỉ thứ đó."""
    assert bool(_string_command_hits(snippet)) is caught


# ── pyproject + manifest ────────────────────────────────────────────────────────────────

tomllib = pytest.importorskip("tomllib") if sys.version_info >= (3, 11) else None


@pytest.mark.skipif(tomllib is None, reason="cần Python ≥ 3.11 để đọc TOML")
def test_pyproject_entry_point_and_light_core():
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    proj = data["project"]
    assert proj["scripts"]["video-studio"] == "video_studio.cli:main"
    assert proj["version"] == __version__
    assert proj["dependencies"] == [], "lõi phải chạy bằng thư viện chuẩn (CI không cài gì nặng)"
    extras = proj["optional-dependencies"]
    for name in ("voice", "edit", "test"):
        assert name in extras
    core_and_test = " ".join(proj["dependencies"] + extras["test"]).lower()
    for heavy in ("torch", "librosa", "matplotlib", "faster-whisper"):
        assert heavy not in core_and_test, f"{heavy} phải ở extras [edit], không ở lõi/test"


def test_plugin_manifests_agree():
    m = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text(encoding="utf-8"))
    c = json.loads((ROOT / ".claude-plugin/plugin.json").read_text(encoding="utf-8"))
    x = json.loads((ROOT / ".codex-plugin/plugin.json").read_text(encoding="utf-8"))
    assert len({m["plugins"][0]["version"], c["version"], x["version"]}) == 1
    assert len({m["name"], m["plugins"][0]["name"], c["name"], x["name"]}) == 1


def test_skill_frontmatter_is_english_body_is_vietnamese():
    """Luật ngôn ngữ: frontmatter (thứ harness đọc để định tuyến) tiếng Anh, thân tiếng Việt."""
    viet = re.compile(r"[àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữự"
                      r"ỳýỷỹỵđ]", re.IGNORECASE)
    skills = list((ROOT / "skills").rglob("SKILL.md"))
    assert skills, "repo phải có ít nhất một skill"
    for sk in skills:
        text = sk.read_text(encoding="utf-8")
        assert text.startswith("---\n"), sk
        fm, _, body = text[4:].partition("\n---\n")
        assert not viet.search(fm), f"{sk}: frontmatter phải là tiếng Anh"
        assert "name:" in fm and "description:" in fm, sk
        assert len(viet.findall(body)) > 50, f"{sk}: thân bài phải là tiếng Việt"


def test_station_contract_version_is_semver():
    assert re.fullmatch(r"\d+\.\d+\.\d+", API_VERSION)
