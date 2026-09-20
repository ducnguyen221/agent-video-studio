"""Cổng chống-thoát-`--out`: TÊN FILE không bao giờ được là ĐƯỜNG DẪN.

Ba chỗ đặt tên file ra (`templates/news`, `spec.outputs`, `edit --name`) phải cùng một luật,
và luật đó phải **chạy y hệt nhau trên mọi hệ điều hành**. Đây là bài học đã trả giá: bản
đầu tiên của cổng viết theo `os.sep`, nên trên POSIX (`os.sep == "/"`, `os.altsep is None`)
**nhánh dấu `\\` không bao giờ chạy** — `18\\09\\2026` và `C:\\out\\x` lọt sạch, dù chính test
của cổng đòi phải chặn. Máy Windows không thể thấy lỗi đó; job `pytest (macos-latest)` thì
thấy ngay.

Nên file này kiểm **ba lượt** qua fixture `any_os`: hệ điều hành thật đang chạy, rồi một lượt
giả POSIX và một lượt giả NT — `os.sep`, `os.altsep` và `os.path` bị thay bằng bản của họ
đường dẫn kia. Hàm nào còn hỏi `os` xem dấu ngăn là gì sẽ đỏ ở đúng lượt đó, kể cả khi người
chạy test đang ngồi trên hệ điều hành "đúng". Đo thật trước khi vá: với bản `os.sep`, lượt
`posix` đỏ đúng hai giá trị mà reviewer chỉ ra, ngay trên máy Windows.
"""
import importlib
import ntpath
import os
import posixpath

import pytest

from video_studio import spec as spec_mod
from video_studio.contract import ContractError


# ── giá trị phải chặn ───────────────────────────────────────────────────────────────────
#
# Ba nhóm: dấu ngăn (cả hai họ), đường tuyệt đối (cả hai họ), và dạng có Ổ ĐĨA — nhóm cuối
# là chỗ bản vá đầu tiên bỏ sót: `C:foo.mp4` KHÔNG có dấu ngăn nào và `ntpath.isabs` của nó
# là False, nhưng `ntpath.join("D:\\deliver", "C:foo.mp4")` trả về `'C:foo.mp4'` — thư mục
# `--out` biến mất không một tiếng động.
MUST_REJECT = [
    "18/09/2026",          # sidecar cũ: dd/mm/yyyy
    r"18\09\2026",         # y hệt, họ NT  ← lọt trên POSIX ở bản os.sep
    "/tmp/x",              # tuyệt đối POSIX
    r"C:\out\x",           # tuyệt đối NT  ← lọt trên POSIX ở bản os.sep
    "../../thoat",         # leo cây
    "C:foo.mp4",           # Ổ ĐĨA, KHÔNG dấu ngăn — join reset sang ổ C:
    "c:",                  # chỉ ổ đĩa
    "..",                  # thư mục cha
    ".",                   # chính thư mục
    r"\\srv\share\x",      # UNC
    "a\x00b",              # NUL — cắt tên ở tầng C
    "",                    # rỗng
    "   ",                 # chỉ khoảng trắng
]

MUST_PASS = ["2026-09-18", "deep-dive", "2026-W38", "ban-dai.mp4", "a.mp4", "tin-18.09.2026.mp4"]


# ── mô phỏng họ đường dẫn kia ───────────────────────────────────────────────────────────

def _swap_os_path(monkeypatch, mod, sep, altsep):
    """Biến `os` thành `os` của hệ kia, đúng những thuộc tính mà cổng có thể lỡ hỏi tới."""
    monkeypatch.setattr(os, "path", mod)
    monkeypatch.setattr(os, "sep", sep)
    monkeypatch.setattr(os, "altsep", altsep)
    monkeypatch.setattr(os, "pardir", "..")
    monkeypatch.setattr(os, "curdir", ".")


@pytest.fixture(params=["that", "posix", "nt"])
def any_os(request, monkeypatch):
    """Ba lượt: hệ thật · giả POSIX (sep `/`, KHÔNG altsep) · giả NT (sep `\\`, altsep `/`).

    Lượt "nt" giữ cho bộ test này còn nghĩa khi CI chạy nó trên macOS. Luật phải ra KẾT QUẢ
    GIỐNG NHAU cả ba lượt — đó chính là điều bản `os.sep` không làm được.
    """
    if request.param == "posix":
        _swap_os_path(monkeypatch, posixpath, "/", None)
    elif request.param == "nt":
        _swap_os_path(monkeypatch, ntpath, "\\", "/")
    return request.param


@pytest.fixture
def tpl(news):
    """Gói `templates.news` (numpy/soundfile/voice_studio giả nhờ fixture `news` ở conftest)."""
    return importlib.import_module("video_studio.templates.news")


# ── 1. template bản tin: `date` và `outputs.<kind>` ─────────────────────────────────────

@pytest.mark.parametrize("bad", MUST_REJECT)
def test_date_is_rejected_on_every_os(tpl, any_os, bad):
    with pytest.raises(ContractError):
        tpl._date({"date": bad})


@pytest.mark.parametrize("good", MUST_PASS)
def test_a_plain_name_passes_on_every_os(tpl, any_os, good):
    assert tpl._date({"date": good}) == good


@pytest.mark.parametrize("bad", MUST_REJECT)
def test_output_name_is_rejected_on_every_os(tpl, any_os, bad):
    with pytest.raises(ContractError):
        tpl.out_name({"outputs": {"long": bad}}, "long", "mac-dinh.mp4")


# ── 2. spec: `outputs.long` / `outputs.short` ───────────────────────────────────────────

def _spec(**kw):
    base = {"schema_version": 1, "template": "daily", "date": "2026-09-18",
            "brand": {"a": "A", "b": "B", "site": "x.test"},
            "daily_video": {"segments": [{"title": "t", "text": "x"}]}}
    base.update(kw)
    return base


@pytest.mark.parametrize("bad", [v for v in MUST_REJECT if v.strip()])
def test_spec_outputs_reject_paths_on_every_os(any_os, bad):
    with pytest.raises(ContractError):
        spec_mod.validate(_spec(outputs={"long": bad}))


# ── 3. helper dùng chung: luật mặt chữ, KHÔNG hỏi hệ điều hành ──────────────────────────

@pytest.mark.parametrize("bad", MUST_REJECT)
def test_plain_name_is_os_independent(any_os, bad):
    from video_studio import _paths
    with pytest.raises(ContractError):
        _paths.plain_name(bad, "outputs.long")


@pytest.mark.parametrize("good", MUST_PASS)
def test_plain_name_lets_a_real_name_through(any_os, good):
    from video_studio import _paths
    assert _paths.plain_name(good, "outputs.long") == good


# ── 4. `edit --name` — cổng thứ ba, trước đây KHÔNG có cổng nào ─────────────────────────
#
# Chạy trên hệ THẬT thôi: `edit.do_edit` đụng đĩa (`abspath`, `makedirs`), mà giả `os.path` cho
# một cây thư mục thật là mô phỏng sai chứ không phải mô phỏng chặt. Phần "luật giống nhau
# trên mọi OS" đã do mục 3 gánh — `edit` chỉ cần chứng minh nó ĐI QUA đúng helper đó.

@pytest.mark.parametrize("bad", [r"..\..\evil.mp4", "../../evil.mp4", "C:evil.mp4",
                                 r"C:\evil.mp4", "sub/dir/a.mp4", "..", "/tmp/evil.mp4"])
def test_edit_name_may_not_escape_out(tmp_path, bad):
    from video_studio import edit
    footage = tmp_path / "quay"
    footage.mkdir()
    (footage / "a.mp4").write_text("x", encoding="utf-8")
    edl = tmp_path / "edl.json"
    edl.write_text('{"clips": []}', encoding="utf-8")
    ap = edit.build_parser()
    args = ap.parse_args(["--footage", str(footage), "--out", str(tmp_path / "deliver"),
                          "--name", bad, "--step", "render", "--edl", str(edl)])
    with pytest.raises(ContractError):
        edit.do_edit(args)


# ── 5. chốt hậu: đường đã ghép KHÔNG BAO GIỜ ra ngoài `--out` ───────────────────────────

def test_every_accepted_name_stays_inside_out_dir(tmp_path):
    from video_studio import _paths
    out_dir = str(tmp_path / "deliver")
    root = os.path.realpath(out_dir)
    for good in MUST_PASS:
        p = _paths.join_out(out_dir, good, "outputs.long")
        assert os.path.realpath(p).startswith(root + os.sep)
    for bad in MUST_REJECT:
        with pytest.raises(ContractError):
            _paths.join_out(out_dir, bad, "outputs.long")
