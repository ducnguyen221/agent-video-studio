"""Chữ nói về `init --yes` / `--non-interactive` phải khớp hành vi: máy đặt `OPCOS_WORKSPACES` thì
`--yes` và chạy không người ra `<biến>/video` (không hỏi), trạm nhúng cũ có dữ liệu được giữ, và muốn
giữ trạm trong repo khi máy có biến thì dùng `--mode embedded --yes`.

Cổng này canh chữ (tài liệu, help, thông báo) — một câu "`--yes` luôn là embedded" còn sót là agent đọc
tài liệu rồi cài sai chỗ. Phần hành vi do `test_init_decision_table.py` / `test_init_old_station.py` canh.
"""
import re
from pathlib import Path

import pytest

from video_studio import station

ROOT = Path(__file__).resolve().parent.parent

# Tài liệu người dùng và agent đọc để chọn lệnh `init`.
DOCS = ["GUIDE.md", "GUIDE.vi.md", "INSTALL.md", "START-HERE.md", "docs/INSTALL.md",
        "docs/WORKSPACE.md", "skills/video-routing/SKILL.md"]

# Câu cũ: nói `--yes` vô điều kiện là embedded (hoặc `init --yes` luôn không hỏi/không mã 2 vì dùng embedded).
OLD_CLAIMS = (
    "luôn là embedded",
    "always means embedded",
    "luôn ra <repo>/workspaces",
    "--yes = embedded",
    "--yes (= embedded)",
    "--yes (= nhận khuyến nghị embedded",
    "nhận khuyến nghị (embedded), không hỏi",
    "nó dùng trạm embedded",
    "tạo trạm ở workspaces/ ngay trong repo",
    "--yes (= embedded, mặc định)",
    "ra <repo>/workspaces và không hỏi gì",
)


def _flat(text):
    """Bỏ định dạng Markdown (`*`, backtick, nháy đơn) và gộp khoảng trắng để so câu."""
    return " ".join(re.sub(r"[`*']", "", text).split())


def _read(rel):
    return _flat((ROOT / rel).read_text(encoding="utf-8"))


def _near_yes(text, phrase, window=160):
    """Các chỗ `phrase` xuất hiện ngay sau một `--yes` trong vòng `window` ký tự."""
    hits = []
    for m in re.finditer(re.escape(phrase), text):
        if "--yes" in text[max(0, m.start() - window):m.start() + len(phrase)]:
            hits.append(text[max(0, m.start() - 60):m.end() + 40])
    return hits


@pytest.mark.parametrize("rel", DOCS)
def test_docs_do_not_say_yes_is_always_embedded(rel):
    text = _read(rel)
    bad = {p: _near_yes(text, p) for p in OLD_CLAIMS if _near_yes(text, p)}
    assert not bad, f"{rel} còn câu cũ về `--yes`: {bad}"


@pytest.mark.parametrize("rel", DOCS)
def test_docs_say_how_to_keep_an_embedded_station_when_the_variable_is_set(rel):
    text = _read(rel)
    assert "--mode embedded --yes" in text, f"{rel} chưa nói cách giữ trạm trong repo: --mode embedded --yes"
    assert "OPCOS_WORKSPACES" in text


def test_the_unreleased_changelog_block_tells_the_whole_story():
    raw = (ROOT / "docs" / "CHANGELOG.md").read_text(encoding="utf-8")
    m = re.search(r"## Chưa phát hành\n(.*?)(?=\n## )", raw, re.S)
    block = _flat(m.group(1)) if m else ""
    for needle in ("--mode embedded --yes",            # cách giữ trạm trong repo
                   "<biến>/video",                      # --yes / không người ra trạm OpcOS
                   "< NUL",                             # EOF khi có biến ⇒ trạm OpcOS
                   "chuyen",                            # trạm cũ có dữ liệu: giữ hoặc chuyển
                   "Ctrl+C",                            # mã 2 một dòng, không traceback
                   "hai trạm",                          # hai trạm cùng mang dấu
                   "station_path"):                     # bản ghi separate hỏng ⇒ mã 2
        assert needle in block, needle
    for old in OLD_CLAIMS:
        assert not _near_yes(block, old), old


def test_the_cli_help_matches_the_behaviour(capsys):
    assert station.init_main(["--help"]) == 0
    blocks = re.split(r"\n  (?=-)", capsys.readouterr().out)          # mỗi khối = một tuỳ chọn
    by_flag = {b.split()[0].rstrip(","): _flat(b) for b in blocks if b.startswith("-")}
    yes_help, ni_help = by_flag["--yes"], by_flag["--non-interactive"]
    assert "OPCOS_WORKSPACES" in yes_help and "(embedded)" not in yes_help
    assert "OPCOS_WORKSPACES" in ni_help


def test_the_error_that_asks_for_a_choice_does_not_promise_yes_means_embedded_everywhere(
        capsys, monkeypatch, tmp_path):
    """Không biến + không người: thông báo mã 2 nhắc `--yes = embedded` là đúng (chỉ khi KHÔNG có
    `OPCOS_WORKSPACES`) — và phải nói rõ điều kiện đó, không nói suông."""
    r = tmp_path / "repo"
    (r / "video_studio").mkdir(parents=True)
    (r / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
    monkeypatch.setenv("VIDEO_STUDIO_REPO", str(r))
    monkeypatch.setattr(station, "_stdin_is_tty", lambda: False)
    assert station.init_main([]) == 2
    err = _flat(capsys.readouterr().err)
    assert "--yes = embedded" not in err or "không đặt OPCOS_WORKSPACES" in err


@pytest.mark.parametrize("rel", ["README.md", "README.vi.md", "docs/index.html"])
def test_entry_pages_do_not_promise_a_table_and_exit_2_on_a_machine_that_sets_the_variable(rel):
    """"Không có ai trả lời ⇒ in bảng rồi mã 2" chỉ đúng khi máy chưa đặt `OPCOS_WORKSPACES`."""
    text = _read(rel)
    assert "OPCOS_WORKSPACES" in text, f"{rel} còn câu 'không ai trả lời ⇒ mã 2' không nêu điều kiện về biến"
