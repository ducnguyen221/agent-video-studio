"""Cổng cho vỏ PowerShell: MỌI `.ps1` của repo phải chạy được trên MÁY KHÁC, không chỉ máy đã viết.

Sáu thứ bị cấm, mỗi thứ là một lần hỏng đã trả giá:

* `$env:USERPROFILE` — chỉ có trên Windows; và trên máy có known folder đổi chủ (OneDrive
  doanh nghiệp) nó còn trỏ sai chỗ. Đường của người dùng phải đến từ `$HOME` hoặc từ CLI.
* Đường tuyệt đối (`C:\\…`, `/Users/…`, `Program Files`) — một máy duy nhất chạy được.
* `powershell.exe` / `cmd /c` — không có trên macOS; và `cmd /c` còn đưa tham số qua bộ tách
  chuỗi của `cmd`.
* `& python` trần — trên Windows `python3` hay là stub của Microsoft Store: có trên PATH,
  hỏng ở mọi lần gọi thật. Ứng viên phải được CHỨNG MINH bằng một lần chạy thử.
* Bản engine trôi (`latest`) — lịch chạy phải gọi đúng bản đã kiểm.
* Ký tự ngoài ASCII — `.ps1` lưu UTF-8 KHÔNG BOM bị Windows PowerShell 5.1 đọc theo code page
  hệ thống, và lỗi cú pháp nổ ra ở lượt lịch lúc 18h chứ không phải lúc viết.

Cổng có mẫu TỰ KIỂM ở cuối: mỗi luật phải bắt được đúng thứ nó nhắm.

**Phạm vi là CẢ REPO, không phải `scripts/`.** Bản đầu tiên chỉ `glob` trong `scripts/`, nên
một `.ps1` đặt dưới `templates/`, `skills/` hay `.github/` thoát sạch bảy luật mà cổng vẫn
xanh — cổng mù ở đúng chỗ người ta hay quên nhìn. Nay danh sách đến từ `repo_files()` (git
ls-files, có đường lùi quét cây), giống mọi cổng phạm-vi-repo khác.
"""
import re
from pathlib import Path

import pytest

from test_no_identity_leak import repo_files

ROOT = Path(__file__).resolve().parent.parent
#: MỌI `.ps1` mà git biết (hoặc cây thấy) — không giới hạn ở `scripts/`.
SCRIPTS = sorted((p for rel, p in repo_files() if rel.lower().endswith(".ps1")),
                 key=lambda p: p.as_posix())
WRAPPER_DIR = sorted((ROOT / "scripts").glob("*.ps1")) if (ROOT / "scripts").is_dir() else []

RULES = (
    (r"\$env:USERPROFILE", "dùng $HOME (hoặc để CLI tự phân giải), không $env:USERPROFILE"),
    # `[A-Za-z]:\\?[A-Za-z]` cũ chỉ thấy dấu ngăn NGƯỢC, nên `C:/Users/x` — hợp lệ với
    # PowerShell y hệt — lọt. Nay nhận cả hai dấu ngăn; lookbehind loại `https://` (chữ `s:`
    # đứng sau `p`) khỏi bị nhận nhầm là ổ đĩa.
    (r"(?<![A-Za-z0-9_])[A-Za-z]:[\\/]", "đường tuyệt đối theo ổ đĩa — chỉ chạy trên một máy"),
    (r"Program Files", "đường cài cứng — dùng Get-Command / biến NODE_DIR"),
    (r"/Users/[A-Za-z]|/home/[A-Za-z]", "đường nhà của một người cụ thể"),
    (r"powershell\.exe|pwsh\.exe|cmd(\.exe)?\s+/c", "gọi lại shell theo tên file thực thi"),
    (r"&\s*python\b|&\s*py\b", "gọi `python` trần — phải dò rồi chạy thử ứng viên"),
    (r"@latest|latest'|\"latest\"", "bản engine trôi"),
)


def problems(text):
    """Danh sách (luật, lý do) mà đoạn script này vi phạm."""
    out = []
    for pat, why in RULES:
        if re.search(pat, text):
            out.append((pat, why))
    if any(ord(ch) > 127 for ch in text):
        out.append(("ascii", "ký tự ngoài ASCII trong .ps1 (bẫy BOM của PowerShell 5.1)"))
    return out


WRAPPERS = [p for p in SCRIPTS if p.name in ("preview.ps1", "render_and_narrate.ps1")]
SH = sorted((p for rel, p in repo_files() if rel.lower().endswith(".sh")),
            key=lambda p: p.as_posix())


def test_there_are_scripts_to_check():
    """Danh sách rỗng là xanh giả; và ba vỏ trong `scripts/` phải luôn có mặt."""
    names = sorted(p.name for p in SCRIPTS)
    assert names, "không thấy .ps1 nào — cổng đang quét nhầm chỗ"
    for must in ("install-video-use.ps1", "preview.ps1", "render_and_narrate.ps1"):
        assert must in names
    assert sorted(p.name for p in WRAPPER_DIR) == ["install-video-use.ps1", "preview.ps1",
                                                   "render_and_narrate.ps1"]
    assert [p.name for p in SH] == ["install-video-use.sh"]


def test_the_scan_is_not_limited_to_the_scripts_folder():
    """Chống xanh giả kiểu cũ: một `.ps1` ngoài `scripts/` PHẢI lọt vào danh sách.

    Đây chính là chỗ cổng từng mù. Kiểm bằng cách hỏi thẳng cơ chế quét, không phải bằng
    cách tin vào `glob` của một thư mục.
    """
    import subprocess
    import shutil
    if not (shutil.which("git") and (ROOT / ".git").exists()):
        pytest.skip("repo chưa git init")
    listed = subprocess.run(["git", "-C", str(ROOT), "ls-files", "--cached", "--others",
                             "--exclude-standard", "-z", "*.ps1"],
                            capture_output=True, text=True, encoding="utf-8",
                            check=True).stdout
    from_git = sorted(p for p in listed.split("\0") if p)
    assert from_git, "git không thấy .ps1 nào"
    scanned = sorted(p.relative_to(ROOT).as_posix() for p in SCRIPTS)
    assert scanned == from_git, f"cổng bỏ sót: {sorted(set(from_git) - set(scanned))}"


@pytest.mark.parametrize("path", SCRIPTS, ids=lambda p: p.name)
def test_script_is_portable(path):
    bad = problems(path.read_text(encoding="utf-8"))
    assert bad == [], f"{path.name}: " + "; ".join(why for _p, why in bad)


@pytest.mark.parametrize("path", WRAPPERS, ids=lambda p: p.name)
def test_script_forwards_to_the_cli_and_returns_its_exit_code(path):
    """Vỏ mỏng: mọi quyết định ở CLI, và mã thoát của CLI phải đi ra nguyên vẹn."""
    text = path.read_text(encoding="utf-8")
    assert "Find-VideoStudio" in text
    assert "exit $LASTEXITCODE" in text.replace("\r", "")


@pytest.mark.parametrize("path", WRAPPERS, ids=lambda p: p.name)
def test_wrapper_fatal_paths_pick_a_contract_exit_code(path):
    """`throw` trần ⇒ `pwsh -File` thoát MÃ 1, mà mã 1 nghĩa là "thử lại có thể qua".

    Lịch chạy sẽ retry vĩnh viễn "chưa cài video-studio" — đúng cái lỗi mà retry không bao giờ
    chữa được. Mọi đường chết trong vỏ phải chọn 2 (sửa lời gọi) hoặc 3 (cài thêm), theo
    `docs/CONTRACT.md`.
    """
    text = path.read_text(encoding="utf-8")
    # Bỏ dòng chú thích: chính chú thích giải thích vì sao KHÔNG dùng `throw` sẽ tự làm đỏ.
    code = "\n".join(ln for ln in text.splitlines() if not ln.lstrip().startswith("#"))
    assert "throw" not in code, "throw trần = mã 1 = retry vĩnh viễn; dùng Fail 2 / Fail 3"
    assert re.search(r"function Fail\(", text), "vỏ cần helper Fail <code> <message>"
    codes = {int(m) for m in re.findall(r"^\s*Fail (\d)", text, flags=re.M)}
    assert codes, f"{path.name}: không có đường chết nào khai mã"
    assert codes <= {2, 3}, f"{path.name}: mã lạ {codes - {2, 3}}"
    assert 3 in codes, f"{path.name}: 'chưa cài video-studio' phải là mã 3"


@pytest.mark.parametrize("path", SH, ids=lambda p: p.name)
def test_shell_installer_is_posix_and_strict(path):
    text = path.read_text(encoding="utf-8")
    assert text.startswith("#!/usr/bin/env sh"), "vỏ POSIX: đừng đòi bash trên máy không có"
    assert "set -eu" in text, "thiếu set -eu: một bước hỏng mà script vẫn chạy tiếp"
    assert "\r" not in text, "CRLF trong .sh làm `sh` báo lỗi khó hiểu trên macOS/Linux"
    assert not any(ord(ch) > 127 for ch in text)


@pytest.mark.parametrize("snippet,caught", [
    ('$p = "$env:USERPROFILE\\.video"', True),
    ('$py = "C:\\Users\\x\\.venv\\python"', True),
    ('$py = "C:/Users/x/.venv/python"', True),   # dấu ngăn XUÔI cũng là ổ đĩa — từng lọt
    ("Invoke-WebRequest https://example.test/x", False),   # `s:/` không phải ổ đĩa
    ("$u = 'http://localhost:3000'", False),
    ('$env:Path = "C:\\Program Files\\nodejs;" + $env:Path', True),
    ("npx --yes hyperframes@latest render", True),
    ("& python -m video_studio narrate", True),
    ("powershell.exe -File other.ps1", True),
    ("cmd /c npx hyperframes render", True),
    ("# xem truoc mot project", False),          # dấu tiếng Việt bị bỏ -> ASCII, hợp lệ
    ("# xem trước một project", True),           # còn dấu -> đỏ
    ("$argv = @('preview'); & $exe @argv", False),
    ("$c = Get-Command 'python'; & $c.Source -c 'import sys'", False),
])
def test_rules_catch_their_target(snippet, caught):
    assert bool(problems(snippet)) is caught, snippet
