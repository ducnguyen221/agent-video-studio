"""Bài mẫu `samples/news-mini/`: spec hợp lệ, và kết quả kỳ vọng khớp đúng thứ engine sẽ ghi.

Bài mẫu là thứ người cài chạy ĐẦU TIÊN trên máy mới (và là đầu vào chung để so Windows với
macOS). Nó chỉ có giá trị nếu ba thứ khớp nhau: spec, lệnh in trong `EXPECTED.md`, và tên file
mà `render` thật sự đặt. Test này không cần Node, HyperFrames, mạng hay repo giọng — template
được thay bằng hàm giả; cái được kiểm là hợp đồng dữ liệu và đường đi của lệnh.
"""
import json
import re
import shlex
from pathlib import Path

import pytest

from conftest import last_json
from video_studio import render, spec as spec_mod
from video_studio.cli import main as cli_main
from video_studio.templates.news import out_name, video_obj_of

ROOT = Path(__file__).resolve().parent.parent
SAMPLE = ROOT / "samples" / "news-mini"
SPEC, BRAND, EXPECTED = SAMPLE / "spec.json", SAMPLE / "brand.json", SAMPLE / "EXPECTED.md"


def _expected_text():
    return EXPECTED.read_text(encoding="utf-8")


def _expected_row(label):
    """Ô kỳ vọng của một dòng bảng `| <label> | <giá trị> |` trong EXPECTED.md."""
    for line in _expected_text().splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 2 and cells[0].startswith(label):
            return cells[1]
    raise AssertionError(f"EXPECTED.md thiếu dòng '{label}'")


def _expected_command():
    blocks = re.findall(r"^```text\n(.*?)^```", _expected_text(), flags=re.M | re.S)
    cmds = [ln for b in blocks for ln in b.splitlines() if ln.startswith("video-studio render")]
    assert len(cmds) == 1, "EXPECTED.md phải in đúng một lệnh render"
    return shlex.split(cmds[0])


@pytest.fixture(scope="module")
def loaded():
    return spec_mod.load(str(SPEC), brand_file=str(BRAND))


def test_sample_spec_and_brand_are_valid(loaded):
    assert loaded["schema_version"] == spec_mod.SCHEMA_VERSION
    for key in spec_mod.REQUIRED_BRAND:
        assert loaded["brand"][key].strip(), f"brand mẫu thiếu {key}"


def test_sample_spec_alone_has_no_brand_so_the_brand_file_is_required():
    """Spec mẫu CỐ Ý không mang brand: bài mẫu dạy luôn luật "không có thương hiệu mặc định"."""
    raw = json.loads(SPEC.read_text(encoding="utf-8"))
    assert "brand" not in raw
    with pytest.raises(spec_mod.ContractError):
        spec_mod.load(str(SPEC))


def test_sample_is_reproducible_and_quiet(loaded):
    assert loaded["voice"].get("seed") == 1234, "giọng phải ghim hạt giống để chạy lại ra cùng nhịp"
    assert loaded["bgm"] == {"style": None}, "bài mẫu không phụ thuộc thư viện nhạc nền"


def test_sample_points_to_nothing_on_the_network():
    urls = re.findall(r"https?://", SPEC.read_text(encoding="utf-8"))
    assert not urls, "spec mẫu không được trỏ ảnh/clip trên mạng — kết quả phải tái lập"


def test_sample_has_the_scene_count_it_promises(loaded):
    n = len(video_obj_of(loaded)["segments"])
    assert _expected_row("Số cảnh tin") == str(n)
    assert 2 <= n <= 3, "bài mẫu phải nhỏ: 2–3 cảnh"


def test_expected_file_names_are_what_render_will_write(loaded):
    date = loaded["date"]
    assert _expected_row("File dài") == f"`{out_name(loaded, 'long', f'{date}.mp4')}`"
    assert _expected_row("File ngắn") == f"`{out_name(loaded, 'short', f'{date}-short.mp4')}`"


def test_expected_command_runs_through_the_real_cli(tmp_path, monkeypatch, capsys):
    """Chạy ĐÚNG lệnh in trong EXPECTED.md qua CLI thật; chỉ template là giả.

    Bắt hai kiểu trôi: tài liệu dùng một cờ mà `render` không còn nhận, và tên file kỳ vọng
    lệch với tên template đặt theo `date` + `outputs` của spec.
    """
    argv = _expected_command()
    assert argv[:2] == ["video-studio", "render"]
    args = argv[2:]
    # Đường trong lệnh tương đối với gốc repo; ghi ra thư mục tạm thay cho `out/`.
    for flag, repl in (("--input", str(SPEC)), ("--brand", str(BRAND)),
                       ("--out", str(tmp_path / "out"))):
        i = args.index(flag)
        assert (ROOT / args[i + 1]).exists() or flag == "--out", f"{flag} trỏ file không có"
        args[i + 1] = repl

    def fake_daily(spec, out_dir):
        date = spec["date"]
        return [{"kind": k, "path": str(Path(out_dir) / out_name(spec, k, n)), "duration": None}
                for k, n in (("long", f"{date}.mp4"), ("short", f"{date}-short.mp4"))]

    monkeypatch.setattr(render, "_template", lambda project: fake_daily)
    monkeypatch.setattr(render, "engine_versions", lambda: {})
    rc = cli_main(["render", *args])
    res = last_json(capsys.readouterr().out)
    assert rc == 0 and res["ok"] is True and res["project"] == "news"
    names = [Path(o["path"]).name for o in res["outputs"]]
    assert [f"`{n}`" for n in names] == [_expected_row("File dài"), _expected_row("File ngắn")]
    assert "2 phần tử" in _expected_row("Dòng JSON cuối") and len(names) == 2


def test_measurement_table_never_invents_numbers():
    """Ô số đo chưa chạy phải ghi "chưa đo" — không một con số ước lượng nào."""
    rows = [ln for ln in _expected_text().splitlines()
            if ln.startswith("| Windows") or ln.startswith("| macOS")]
    assert len(rows) == 2, "bảng số đo phải có một dòng Windows và một dòng macOS"
    for row in rows:
        cells = [c.strip() for c in row.strip("|").split("|")]
        if cells[1] == "chưa đo":
            assert set(cells[3:6]) == {"—"}, f"dòng chưa đo mà có số: {row}"
