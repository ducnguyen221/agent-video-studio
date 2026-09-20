"""Cổng chống rò danh tính: repo public không được mang tên profile giọng thật, tên thương hiệu
hay khách hàng của một máy cụ thể, tên người viết ngoài chỗ ghi công, hay đường dẫn máy.

Mọi chuỗi cấm dựng bằng chr() để chính file này không tự khớp. Chạy được CẢ KHI repo chưa
`git init` (quét cây thư mục, bỏ venv/cache) — cổng phải xanh TRƯỚC commit đầu, không phải sau.

MIỄN TRỪ THEO SỐ ĐẾM, không miễn cả file: mỗi mục ghi số lần KỲ VỌNG hiện tại. Vượt số đó là
đỏ — nhét thêm một chỗ vào file đã được miễn cũng bị bắt. Sửa nội dung làm số đổi thì phải sửa
con số ở đây, tức người sửa buộc phải nhìn thấy mình đang đổi gì.
"""
import re
import shutil
import subprocess
from collections import Counter
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SELF = "tests/test_no_identity_leak.py"
SKIP_DIRS = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", "build", "dist",
             "node_modules", ".tmp"}
# Trạm chế độ `embedded` là dữ liệu người dùng — bỏ qua. Nhưng CHỈ ở gốc repo: bỏ theo tên ở mọi
# cấp thì `templates/workspace/` (cây mẫu, là nội dung repo) lọt khỏi cổng mà không ai thấy.
SKIP_TOP = {"workspace"}
# `.example` có trong danh sách vì `.env.example` là đúng loại file hay rò nhất: người ta
# điền thử đường dẫn máy mình vào rồi quên gỡ.
TEXT_EXT = {".py", ".md", ".json", ".toml", ".yml", ".yaml", ".txt", ".cfg", ".ini", ".sh",
            ".ps1", ".html", ".css", ".js", ".svg", ".example", ".gitignore",
            ".gitattributes", ""}


def s(*codes):
    return "".join(map(chr, codes))


# khoá → regex (không phân biệt hoa thường, trừ mục ghi rõ)
PATTERNS = {
    "profile-a": re.escape(s(109, 121, 45, 118, 111, 105, 99, 101)),                  # profile giọng thật 1
    "profile-b": r"\b" + re.escape(s(97, 45, 116, 117, 110)) + r"\b",                 # profile giọng thật 2
    "brand-a": r"\b" + re.escape(s(116, 111, 98, 105)) + r"\b",                       # thương hiệu riêng 1
    "brand-b": r"\b" + re.escape(s(107, 112, 105, 109)) + r"\b",                       # thương hiệu riêng 2
    "khach-hang": re.escape(s(97, 103, 114, 105, 98, 97, 110, 107)),                   # tên khách hàng
    "ten-nguoi": r"(?-i:\b" + re.escape(s(0x110, 0x1EE9, 0x63)) + r"\b)",             # tên riêng (viết hoa)
    "tac-gia": re.escape(s(100, 117, 99, 110, 103, 117, 121, 101, 110)) + "|" +
               re.escape(s(100, 117, 99, 32, 110, 103, 117, 121, 101, 110)),         # chỉ ở chỗ ghi công
    # Tên MIỀN riêng: template đời cũ nhét thẳng vào regex phát âm và vào brand mặc định.
    "mien": re.escape(s(100, 117, 99, 110, 103, 117, 121, 101, 110, 46, 118, 110)),
    "duong-may-win": re.escape(s(67, 58, 92, 85, 115, 101, 114, 115, 92)),             # ổ C + thư mục người dùng
    "duong-may-env": re.escape(s(37, 85, 83, 69, 82, 80, 82, 79, 70, 73, 76, 69, 37)),  # %USERPROFILE%
    "duong-may-posix": r"/(?:home|Users)/[a-z][a-z0-9_-]+/",
}

# (file, khoá) → số lần tối đa được phép. Lý do bên cạnh.
ALLOW = {
    # Ghi công tác giả + địa chỉ repo công khai: đúng chỗ, là điều kiện của license.
    (".claude-plugin/marketplace.json", "tac-gia"): 4,
    (".claude-plugin/plugin.json", "tac-gia"): 3,
    (".codex-plugin/plugin.json", "tac-gia"): 3,
    # `author.url` của manifest — cùng loại với ghi công ở trên, và CHỈ ở đó.
    (".claude-plugin/marketplace.json", "mien"): 2,
    (".claude-plugin/plugin.json", "mien"): 1,
    (".codex-plugin/plugin.json", "mien"): 1,
    ("LICENSE", "tac-gia"): 1,
    ("NOTICE", "tac-gia"): 1,
    ("README.md", "tac-gia"): 1,
    ("README.vi.md", "tac-gia"): 1,
}


def keep_in_tree_scan(rel):
    """Đường (posix, tương đối gốc repo) có thuộc phạm vi quét khi repo CHƯA `git init`?"""
    parts = rel.split("/")
    if SKIP_DIRS & set(parts) or any(p.endswith(".egg-info") for p in parts):
        return False
    return parts[0] not in SKIP_TOP or len(parts) == 1


def tree_files():
    for p in ROOT.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(ROOT).as_posix()
        if keep_in_tree_scan(rel):
            yield rel


def repo_files():
    """File của repo: theo git nếu đã có, không thì quét cây (repo chưa `git init`)."""
    if shutil.which("git") and (ROOT / ".git").exists():
        out = subprocess.run(["git", "-C", str(ROOT), "ls-files", "--cached", "--others",
                              "--exclude-standard", "-z"], capture_output=True, text=True,
                             encoding="utf-8", check=True).stdout
        rels = sorted({p for p in out.split("\0") if p})
    else:
        rels = sorted(tree_files())
    for rel in rels:
        p = ROOT / rel
        if rel == SELF or not p.is_file():
            continue
        if p.suffix.lower() in TEXT_EXT or p.name.startswith("."):
            yield rel, p


def count_hits():
    hits = Counter()
    for rel, p in repo_files():
        try:
            text = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for key, pat in PATTERNS.items():
            n = len(re.findall(pat, text, flags=re.IGNORECASE))
            if n:
                hits[(rel, key)] = n
    return hits


def test_scanner_sees_the_repo():
    """Cổng phải thật sự quét được file — danh sách rỗng là xanh giả."""
    seen = {rel for rel, _ in repo_files()}
    for must in ("README.md", "video_studio/station.py", "pyproject.toml",
                 "templates/workspace/README.md", "skills/hyperframes/hyperframes/SKILL.md"):
        assert must in seen, f"cổng không nhìn thấy {must}"


@pytest.mark.parametrize("rel,keep", [
    ("templates/workspace/README.md", True),      # cây mẫu = nội dung repo
    ("workspace/projects/a/x.md", False),         # trạm embedded = dữ liệu người dùng
    ("video_studio/station.py", True),
    (".venv/Lib/x.py", False),
    ("video_studio/__pycache__/a.pyc", False),
    ("agent_video_studio.egg-info/PKG-INFO", False),
])
def test_tree_scan_filter(rel, keep):
    """Đột biến: bỏ theo TÊN ở mọi cấp sẽ giấu mất `templates/workspace/` khỏi cổng."""
    assert keep_in_tree_scan(rel) is keep


def test_no_identity_leak():
    over = {k: n for k, n in count_hits().items() if n > ALLOW.get(k, 0)}
    assert over == {}, "rò danh tính / vượt số miễn trừ: " + ", ".join(
        f"{f} [{k}] {n} > {ALLOW.get((f, k), 0)}" for (f, k), n in sorted(over.items()))


def test_allowlist_is_exact():
    """Miễn trừ phải BẰNG số thật: mục thừa (cửa mở sẵn) cũng đỏ như mục thiếu."""
    hits = count_hits()
    loose = {k: (n, hits.get(k, 0)) for k, n in ALLOW.items() if hits.get(k, 0) != n}
    assert loose == {}, f"ALLOW lệch số thật (cho phép, thật): {loose}"


def test_patterns_catch_their_target():
    """Đột biến: mỗi mẫu phải bắt được chuỗi nó nhắm tới (không để regex hỏng thành xanh giả)."""
    samples = {
        "profile-a": s(109, 121, 45, 118, 111, 105, 99, 101),
        "profile-b": "--profile " + s(97, 45, 116, 117, 110),
        "brand-a": "brand " + s(84, 111, 98, 105) + " site",
        "brand-b": s(75, 80, 73, 77) + " Academy",
        "khach-hang": "gala-" + s(97, 103, 114, 105, 98, 97, 110, 107),
        "ten-nguoi": "anh " + s(0x110, 0x1EE9, 0x63) + " viết",
        "tac-gia": s(68, 117, 99, 32, 78, 103, 117, 121, 101, 110),
        "mien": "site: " + s(100, 117, 99, 110, 103, 117, 121, 101, 110, 46, 118, 110) + "/news",
        "duong-may-win": s(67, 58, 92, 85, 115, 101, 114, 115, 92) + "x",
        "duong-may-env": s(37, 85, 83, 69, 82, 80, 82, 79, 70, 73, 76, 69, 37) + "\\.video",
        "duong-may-posix": "/home/someone/",
    }
    for key, text in samples.items():
        assert re.search(PATTERNS[key], text, flags=re.IGNORECASE), key
    # "đạo đức" (chữ thường) không phải tên người
    assert not re.search(PATTERNS["ten-nguoi"], s(0x111, 0x1EA1, 0x6F, 32, 0x111, 0x1EE9, 0x63),
                         flags=re.IGNORECASE)
