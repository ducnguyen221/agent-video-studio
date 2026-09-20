"""precommit.py — hook `pre-commit` của chế độ `embedded`: chặn commit dữ liệu trạm và secret.

Chế độ `embedded` đặt trạm (project đang dựng, footage, nháp) và `.env` NGAY TRONG repo.
`.gitignore` đã chặn chúng, nhưng `git add -f`, một `.gitignore` bị sửa, hay một thư mục được
mở lại bằng dòng `!` là đủ để rò. Hook này là **lớp rào thứ hai**, và nó nhìn vào thứ đã stage
chứ không nhìn vào luật:

    - file dưới `workspace/`, `.env` / `.env.*` (trừ `.env.example`), `studio.local.json`
    - file media/model (mp4, mov, mp3, wav, png, woff2, pt…) — repo này dạy cách dựng video,
      nó không chứa video
    - dòng THÊM MỚI trong diff trông giống token (GitHub, Hugging Face, OpenAI/Anthropic, AWS,
      Slack, Google, khoá riêng PEM, hoặc `token|secret|api_key = "<chuỗi dài>"`)

`video-studio init` (embedded) cài hook gọi `python -m video_studio.precommit`. Bỏ qua một lần
có chủ đích: `git commit --no-verify` — và tự chịu trách nhiệm.
"""
import os
import re
import subprocess
import sys

BLOCKED_PREFIXES = ("workspace/",)
BLOCKED_FILES = ("studio.local.json",)
MEDIA_EXT = {".mp4", ".mov", ".webm", ".mkv", ".mp3", ".wav", ".m4a", ".aac", ".flac", ".ogg",
             ".png", ".jpg", ".jpeg", ".webp", ".gif", ".woff", ".woff2", ".ttf", ".otf",
             ".pt", ".onnx", ".safetensors"}
#: Ngoại lệ media — CỐ Ý rỗng. Mở cả một THƯ MỤC cho file media đi ngược chính giáo lý ghi
#: trong `.gitignore` của repo ("không bao giờ mở cả thư mục"): hôm nay
#: `templates/_seed/assets/` chỉ có `README.md`, nhưng một ngoại lệ theo thư mục thì ai đặt
#: file gì vào đó sau này cũng lọt, và không ai đọc lại dòng này để biết. Cần cho qua một file
#: cụ thể thì thêm ĐÚNG ĐƯỜNG DẪN CỦA NÓ vào đây, không thêm thư mục chứa nó.
MEDIA_ALLOW = ()

TOKEN_PATTERNS = [
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{30,}"),
    re.compile(r"\bhf_[A-Za-z0-9]{30,}"),
    re.compile(r"\bsk-(?:ant-)?[A-Za-z0-9_\-]{20,}"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"\bxox[abpr]-[A-Za-z0-9\-]{10,}"),
    re.compile(r"\bAIza[0-9A-Za-z_\-]{35}"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"(?i)\b(token|secret|api[_-]?key|password)\b\s*[:=]\s*['\"][^'\"\s]{16,}['\"]"),
]

__all__ = ["blocked_path", "token_lines", "check", "main"]


def _git(repo, *args):
    r = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=60)
    if r.returncode != 0:
        raise RuntimeError((r.stderr or r.stdout).strip())
    return r.stdout


def blocked_path(path):
    """-> lý do chặn, hoặc None."""
    p = str(path).replace("\\", "/")
    base = p.rsplit("/", 1)[-1]
    if p.startswith(BLOCKED_PREFIXES) or p in BLOCKED_FILES:
        return "dữ liệu trạm / lựa chọn cài không thuộc repo"
    if base == ".env" or (base.startswith(".env.") and base != ".env.example"):
        return "file secret"
    if os.path.splitext(base)[1].lower() in MEDIA_EXT and not p.startswith(MEDIA_ALLOW):
        return "file media/model (repo không chứa video, ảnh, font hay model)"
    return None


def token_lines(diff):
    """Dòng thêm mới trông giống token. -> [(file, dòng)]."""
    out, current = [], None
    for line in diff.splitlines():
        if line.startswith("+++ "):
            current = line[6:] if line.startswith("+++ b/") else line[4:]
            continue
        if line.startswith("+") and not line.startswith("+++"):
            for pat in TOKEN_PATTERNS:
                if pat.search(line):
                    out.append((current, line[:80]))
                    break
    return out


def check(repo="."):
    """Danh sách vấn đề của phần đã stage (rỗng = cho commit)."""
    problems = []
    names = [n for n in _git(repo, "diff", "--cached", "--name-only", "-z").split("\0") if n]
    for n in names:
        why = blocked_path(n)
        if why:
            problems.append(f"{n}: {why}")
    for path, _line in token_lines(_git(repo, "diff", "--cached", "-U0", "--no-color")):
        problems.append(f"{path}: dòng thêm mới trông giống token/secret")
    return problems


def main(argv=None):
    try:
        problems = check(".")
    except (RuntimeError, OSError) as e:
        print(f"[video-studio pre-commit] không kiểm được: {e}", file=sys.stderr)
        return 1
    if problems:
        print("[video-studio pre-commit] CHẶN commit:", file=sys.stderr)
        for p in problems:
            print("  - " + p, file=sys.stderr)
        print("Gỡ khỏi stage: git restore --staged <file>. Cố ý thì --no-verify.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
