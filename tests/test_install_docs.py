"""Tài liệu cài đặt agent-first: một prompt, một nguồn, không lệnh nguy hiểm, không lệnh ma.

`INSTALL.md` ở gốc repo là bản GỐC của prompt copy-dán. README, START-HERE (và trang cài của
website khi có) chỉ chép lại; test này bắt mọi chỗ chép lệch. Nó cũng khoá luật an toàn của
runbook — không tải-rồi-chạy, không đổi chính sách máy — và đối chiếu mọi lệnh, cờ, tên dòng
`doctor` mà runbook nhắc với MÃ thật, vì agent làm theo từng chữ: một lệnh đã đổi tên trong tài
liệu là một bước cài hỏng mà không ai thấy trước.
"""
import html
import re
from pathlib import Path

import pytest

from video_studio import cli

ROOT = Path(__file__).resolve().parent.parent
OFFICIAL_REPO = "https://github.com/ducnguyen221/agent-video-studio"
RAW_INSTALL_URL = "https://raw.githubusercontent.com/ducnguyen221/agent-video-studio/main/INSTALL.md"
PROMPT_START = {
    "vi": "Hãy cài Agent Video Studio lên máy này",
    "en": "Install Agent Video Studio on this machine",
}
# Nơi chép prompt: file Markdown (khối ```text) hoặc trang web (<pre id="prompt-<lang>">).
COPIES = {
    "vi": ["README.vi.md", "START-HERE.md"],
    "en": ["README.md"],
}
PAGE = "docs/install/index.html"
MAX_PROMPT_LINES = 12
USER_DOCS = ["INSTALL.md", "START-HERE.md", "README.md", "README.vi.md", "hosts/README.md",
             "hosts/claude/README.md", "hosts/codex/README.md", "hosts/antigravity/README.md",
             "hosts/claude-desktop/README.md", "AGENTS.md"]


def read(rel):
    return (ROOT / rel).read_text(encoding="utf-8").replace("\r\n", "\n")


def normalize(text):
    return "\n".join(line.rstrip() for line in text.strip("\n").split("\n"))


def fenced_blocks(markdown, lang=r"[\w-]*"):
    return re.findall(rf"^```{lang}\n(.*?)^```", markdown, flags=re.M | re.S)


def html_pre_blocks(page):
    blocks = {}
    for i, m in enumerate(re.finditer(r"<pre([^>]*)>(.*?)</pre>", page, flags=re.S)):
        ident = re.search(r'id="([^"]+)"', m.group(1))
        blocks[ident.group(1) if ident else f"#{i}"] = html.unescape(re.sub(r"<[^>]+>", "", m.group(2)))
    return blocks


def prompt_in(rel, lang):
    text = read(rel)
    if rel.endswith(".html"):
        found = html_pre_blocks(text).get(f"prompt-{lang}")
        assert found is not None, f"{rel}: thiếu <pre id=\"prompt-{lang}\">"
        return normalize(found)
    hits = [b for b in fenced_blocks(text) if b.startswith(PROMPT_START[lang])]
    assert len(hits) == 1, f"{rel}: cần đúng 1 khối prompt {lang}, thấy {len(hits)}"
    return normalize(hits[0])


def canonical(lang):
    return prompt_in("INSTALL.md", lang)


def _copies():
    out = [(lang, rel) for lang, rels in COPIES.items() for rel in rels]
    if (ROOT / PAGE).is_file():
        out += [("vi", PAGE), ("en", PAGE)]
    return out


# ── một prompt, một nguồn ──────────────────────────────────────────────────────────────

@pytest.mark.parametrize("lang,rel", _copies())
def test_prompt_copies_match_install_md(lang, rel):
    assert prompt_in(rel, lang) == canonical(lang), (
        f"Prompt {lang} trong {rel} lệch bản gốc INSTALL.md — chép lại nguyên văn khối trong INSTALL.md.")


@pytest.mark.parametrize("lang", sorted(PROMPT_START))
def test_prompt_points_to_the_single_official_source(lang):
    prompt = canonical(lang)
    urls = set(re.findall(r"https?://\S+", prompt))
    assert urls == {OFFICIAL_REPO, RAW_INSTALL_URL}, f"prompt chỉ được trỏ repo chính thức: {sorted(urls)}"
    assert (ROOT / RAW_INSTALL_URL.rsplit("/main/", 1)[1]).is_file(), "raw URL phải trỏ file có thật"
    assert len(prompt.splitlines()) <= MAX_PROMPT_LINES, "prompt quá dài để dán vào ô chat hẹp"


@pytest.mark.parametrize("lang", sorted(PROMPT_START))
def test_prompt_names_both_operating_systems(lang):
    prompt = canonical(lang)
    assert "Windows" in prompt and "macOS" in prompt


# ── luật an toàn ───────────────────────────────────────────────────────────────────────

def _command_blocks(rel):
    text = read(rel)
    return list(html_pre_blocks(text).values()) if rel.endswith(".html") else fenced_blocks(text)


@pytest.mark.parametrize("rel", USER_DOCS)
def test_no_download_and_execute(rel):
    bad = [ln.strip() for block in _command_blocks(rel) for ln in block.splitlines()
           if re.search(r"\biex\b|Invoke-Expression|DownloadString|\|\s*(ba)?sh\b", ln, re.I)]
    assert not bad, f"{rel}: lệnh tải-rồi-chạy bị cấm:\n  " + "\n  ".join(bad)


def test_install_md_never_changes_machine_policy():
    text = read("INSTALL.md")
    for bad in ("Set-ExecutionPolicy", "spctl --master-disable", "xattr -d com.apple.quarantine"):
        assert bad not in text, f"INSTALL.md không được đổi chính sách máy: {bad}"


def test_install_md_gives_both_os_their_own_commands():
    """Mỗi bước có lệnh thì có cả khối PowerShell lẫn khối sh — agent trên Mac không được phải
    dịch lệnh Windows trong đầu (và ngược lại)."""
    text = read("INSTALL.md")
    ps, sh = fenced_blocks(text, "powershell"), fenced_blocks(text, "sh")
    assert len(ps) >= 3 and len(sh) >= 3 and abs(len(ps) - len(sh)) <= 1, (len(ps), len(sh))
    assert not any(re.search(r"(?m)^\s*(cmd /c|\S+\.exe\b)", b) for b in sh), "khối macOS có lệnh Windows"


# ── lệnh / cờ / dòng doctor mà runbook nhắc phải có thật ────────────────────────────────

def _mentioned_commands(text):
    # `(?<![\w-])`: "agent-video-studio" (tên repo trong đường dẫn) không phải lệnh.
    # `.\.venv\Scripts\video-studio init` và `.venv/bin/video-studio init` thì có.
    return set(re.findall(r"(?<![\w-])video-studio ([a-z]+)\b", text))


@pytest.mark.parametrize("rel", ["INSTALL.md", "START-HERE.md", "AGENTS.md"])
def test_every_command_the_docs_mention_exists(rel):
    ghost = _mentioned_commands(read(rel)) - set(cli.COMMANDS)
    assert not ghost, f"{rel} nhắc lệnh không có trong video-studio: {sorted(ghost)}"


def test_every_init_flag_in_install_md_exists():
    src = read("video_studio/station.py").split("def init_main(")[1]
    real = set(re.findall(r'ap\.add_argument\("(--[a-z-]+)"', src))
    lines = [ln for ln in read("INSTALL.md").splitlines() if "video-studio init" in ln or "init --" in ln]
    used = set(re.findall(r"(--[a-z][a-z-]+)", "\n".join(lines)))
    assert used and used <= real, f"INSTALL.md dùng cờ init không có: {sorted(used - real)}"


def _doctor_check_names():
    src = read("video_studio/doctor.py")
    return set(re.findall(r'_(?:check|skip|not_checked)\(\s*"([a-z-]+)"', src))


def test_doctor_lines_in_install_md_are_real_checks():
    names = set(re.findall(r"`\[[A-Z_]+\] ([a-z-]+)", read("INSTALL.md")))
    names |= {n for row in re.findall(r"`\[[A-Z_]+\] ([a-z /`-]+)`", read("INSTALL.md"))
              for n in re.split(r"[ /`]+", row) if n}
    assert names, "INSTALL.md phải có bảng đọc dòng doctor"
    ghost = names - _doctor_check_names()
    assert not ghost, f"INSTALL.md giải thích dòng doctor không tồn tại: {sorted(ghost)}"


def test_doctor_labels_in_install_md_are_the_real_labels():
    from video_studio import doctor
    used = set(re.findall(r"`\[([A-Z_]+)\]", read("INSTALL.md")))
    assert used and used <= set(doctor.MARKS.values()), used - set(doctor.MARKS.values())


# ── liên kết ───────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("rel", USER_DOCS + ["CLAUDE.md", "GEMINI.md"])
def test_relative_links_exist(rel):
    doc = ROOT / rel
    missing = []
    for target in re.findall(r"\]\(([^)\s]+)\)", read(rel)):
        if target.startswith(("http://", "https://", "#", "mailto:")):
            continue
        path = target.split("#", 1)[0]
        if path and not (doc.parent / path).exists():
            missing.append(target)
    assert not missing, f"{rel}: link tương đối gãy {missing}"


@pytest.mark.parametrize("rel", ["README.md", "README.vi.md", "START-HERE.md", "AGENTS.md"])
def test_entry_docs_point_to_install_md(rel):
    assert "INSTALL.md" in read(rel), f"{rel} chưa trỏ tới INSTALL.md"


@pytest.mark.parametrize("rel", ["CLAUDE.md", "GEMINI.md"])
def test_host_files_only_point_to_agents_md(rel):
    """CLAUDE.md / GEMINI.md là con trỏ, không phải bản luật thứ hai để trôi."""
    text = read(rel)
    assert "AGENTS.md" in text and len(text.splitlines()) <= 6


@pytest.mark.parametrize("host", ["claude", "codex", "claude-desktop", "antigravity"])
def test_every_host_has_a_page_and_is_listed(host):
    assert (ROOT / "hosts" / host / "README.md").is_file()
    assert f"({host}/README.md)" in read("hosts/README.md")
