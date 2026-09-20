"""Cổng cho vỏ PowerShell: `scripts/*.ps1` phải chạy được trên MÁY KHÁC, không chỉ máy đã viết.

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
"""
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = sorted((ROOT / "scripts").glob("*.ps1")) if (ROOT / "scripts").is_dir() else []

RULES = (
    (r"\$env:USERPROFILE", "dùng $HOME (hoặc để CLI tự phân giải), không $env:USERPROFILE"),
    (r"[A-Za-z]:\\\\?[A-Za-z]", "đường tuyệt đối theo ổ đĩa — chỉ chạy trên một máy"),
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
SH = sorted((ROOT / "scripts").glob("*.sh")) if (ROOT / "scripts").is_dir() else []


def test_there_are_scripts_to_check():
    """Danh sách rỗng là xanh giả."""
    assert [p.name for p in SCRIPTS] == ["install-video-use.ps1", "preview.ps1",
                                         "render_and_narrate.ps1"]
    assert [p.name for p in SH] == ["install-video-use.sh"]


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
