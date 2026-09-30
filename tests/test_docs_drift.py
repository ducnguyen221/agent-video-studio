"""Cổng chống trôi tài liệu: README và trang giới thiệu phải nói đúng thứ mã đang làm.

Vì sao cần cổng này: tài liệu và trang web là thứ người ngoài đọc TRƯỚC khi chạy lệnh đầu
tiên. Khi mã đổi mà chữ không đổi, người đọc không thấy lỗi — họ chỉ thấy một lệnh không tồn
tại, hoặc không bao giờ biết một lệnh đã có. Cổng rẻ tiền: đọc `cli.COMMANDS` (nguồn duy nhất
mà `--help` cũng đọc) rồi đối chiếu với chữ.

Hai chiều, cố ý:
  · mã → chữ: lệnh nào có trong `COMMANDS` mà không được nhắc tới là đỏ (thêm lệnh, quên kể).
  · chữ → mã: tên nào nằm trong BẢNG LỆNH của trang mà không có trong `COMMANDS` là đỏ
    (bỏ lệnh, quên xoá — kiểu trôi im lặng hơn, vì không ai thử lệnh trong tài liệu cũ).
"""
import re
from pathlib import Path

import pytest

from video_studio import __version__, cli

ROOT = Path(__file__).resolve().parent.parent
PAGE = ROOT / "docs" / "index.html"
READMES = ("README.md", "README.vi.md")
# Tên template mà `render` nhận, theo đúng mô tả một dòng trong `COMMANDS`.
TEMPLATES = ("news", "news-weekly", "topstory", "repo-today")


def _page():
    if not PAGE.is_file():
        pytest.skip("repo chưa có trang giới thiệu")
    return PAGE.read_text(encoding="utf-8")


@pytest.mark.parametrize("name", sorted(cli.COMMANDS))
def test_page_lists_every_command(name):
    assert name in _page(), f"trang giới thiệu không nhắc lệnh `{name}`"


@pytest.mark.parametrize("name", sorted(cli.COMMANDS))
def test_readme_lists_every_command(name):
    for rel in READMES:
        text = (ROOT / rel).read_text(encoding="utf-8")
        assert name in text, f"{rel} không nhắc lệnh `{name}`"


@pytest.mark.parametrize("name", TEMPLATES)
def test_templates_named_in_code_are_documented(name):
    assert name in cli.COMMANDS["render"][1], f"mô tả lệnh render không còn kể template `{name}`"
    assert name in _page(), f"trang giới thiệu không kể template `{name}`"


def _page_command_table():
    """Tên lệnh in trong BẢNG LỆNH của trang (mục #lenh), theo ô `<td class="lbl…">`."""
    text = _page()
    block = re.search(r'<section id="lenh">(.*?)</section>', text, flags=re.S)
    assert block, "trang giới thiệu phải có mục #lenh chứa bảng lệnh"
    return set(re.findall(r'<td class="lbl[^"]*">([a-z][a-z-]*)</td>', block.group(1)))


def test_page_command_table_invents_nothing():
    thua = _page_command_table() - set(cli.COMMANDS)
    assert not thua, f"bảng lệnh của trang kể lệnh không có trong mã: {sorted(thua)}"


def test_page_command_table_is_complete():
    thieu = set(cli.COMMANDS) - _page_command_table()
    assert not thieu, f"bảng lệnh của trang thiếu lệnh: {sorted(thieu)}"


@pytest.mark.parametrize("rel", READMES + ("docs/INSTALL.md", "docs/CONTRACT.md"))
def test_docs_do_not_still_advertise_a_prerelease(rel):
    """Bỏ hậu tố `.dev` khi phát hành thì tài liệu cũng phải bỏ theo.

    Kiểu trôi này im lặng nhất: bản đã tag rồi mà README vẫn tự xưng "bản thử", và người đọc
    quyết định dựa trên một câu không còn đúng.
    """
    if ".dev" in __version__:
        pytest.skip("bản hiện tại vẫn là tiền phát hành")
    text = (ROOT / rel).read_text(encoding="utf-8")
    assert f"{__version__}.dev" not in text, (
        f"{rel} còn quảng cáo bản tiền phát hành trong khi gói đã là {__version__}")


def test_page_states_the_current_version():
    assert __version__ in _page(), (
        f"trang giới thiệu không nói đúng phiên bản {__version__} — "
        "phát hành bản mới thì sửa cả trang")


def test_page_states_the_exit_code_contract():
    """Hợp đồng mã thoát là thứ pipeline khác dựa vào; trang không được kể sai hay bỏ sót."""
    text = _page()
    for code in ("0", "1", "2", "3"):
        assert f"<b>{code}</b>" in text, f"trang thiếu mã thoát {code} trong hợp đồng"


def test_page_counts_the_skills_that_really_exist():
    """Con số '24 skill' trên trang phải khớp cây `skills/` trên đĩa, không phải trí nhớ."""
    own = [p for p in (ROOT / "skills").iterdir() if p.is_dir() and p.name != "hyperframes"]
    upstream = [p for p in (ROOT / "skills" / "hyperframes").iterdir() if p.is_dir()]
    tong = len(own) + len(upstream)
    text = _page()
    assert f'data-to="{tong}"' in text, f"trang không nói đúng tổng số skill ({tong})"
    assert f"{len(upstream)} skill chưng cất" in text or \
           f"{len(upstream)} skill còn lại" in text, \
           f"trang không nói đúng số skill chưng cất từ upstream ({len(upstream)})"


# ── START-HERE + CHANGELOG ──────────────────────────────────────────────────────────────

NEW_DOCS = ("START-HERE.md", "docs/CHANGELOG.md")


@pytest.mark.parametrize("rel", NEW_DOCS)
def test_relative_links_resolve(rel):
    """Link tương đối gãy là trang 404 đầu tiên người mới gặp."""
    doc = ROOT / rel
    missing = []
    for target in re.findall(r"\]\(([^)\s]+)\)", doc.read_text(encoding="utf-8")):
        if target.startswith(("http://", "https://", "#", "mailto:")):
            continue
        path = target.split("#", 1)[0]
        if path and not (doc.parent / path).exists():
            missing.append(target)
    assert not missing, f"{rel}: link tương đối gãy {missing}"


def test_start_here_runs_the_sample_the_way_expected_md_does():
    """START-HERE và EXPECTED.md in cùng MỘT lệnh bài mẫu — lệch là người mới chạy lệnh cũ."""
    def cmd(rel):
        text = (ROOT / rel).read_text(encoding="utf-8")
        return [ln for ln in text.splitlines() if ln.startswith("video-studio render")]
    assert cmd("START-HERE.md") == cmd("samples/news-mini/EXPECTED.md") != []



# ── câu đã sai, cấm quay lại ────────────────────────────────────────────────────────────

# Tài liệu người dùng và agent đọc để cài/dùng. CHANGELOG cố ý không nằm đây: nó kể lại hành vi
# CŨ của từng bản, nên có quyền chép câu cũ.
STALE_DOCS = ("README.md", "README.vi.md", "GUIDE.md", "GUIDE.vi.md", "START-HERE.md",
              "INSTALL.md", "docs/INSTALL.md", "docs/WORKSPACE.md", "skills/video-routing/SKILL.md",
              "docs/index.html", "docs/install/index.html")
# (câu sai, vì sao sai). Từ 0.2.2 `init` KHÔNG tự nhận `~/.video` có sẵn: `--yes` = embedded,
# trạm cũ chỉ được nhận qua `--mode separate` / `--station` / `--migrate` hoặc câu trả lời [1];
# không có người thì mã 2 (`station.py::_adopt_or_stop`). Câu cũ dạy agent chờ một lượt nhận
# trạm im lặng không còn tồn tại — đúng kiểu lỗi của lượt cài Mac 29/09.
STALE_CLAIMS = (
    ("detects it and does not ask", "init không tự nhận trạm cũ từ 0.2.2"),
    ("tự nhận ra và không hỏi", "init không tự nhận trạm cũ từ 0.2.2"),
    ("`init` tự chọn `separate`, không hỏi", "~/.video tình cờ có mặt không được tự chọn"),
    ("init --yes` tự nhận", "--yes luôn là embedded"),
)


@pytest.mark.parametrize("rel", STALE_DOCS)
@pytest.mark.parametrize("claim,why", STALE_CLAIMS)
def test_docs_do_not_repeat_a_claim_the_code_no_longer_makes(rel, claim, why):
    path = ROOT / rel
    if not path.is_file():
        pytest.skip(f"{rel} không có trong repo")
    text = " ".join(path.read_text(encoding="utf-8").split())
    assert claim not in text, f"{rel} còn câu đã sai: {claim!r} — {why}"
