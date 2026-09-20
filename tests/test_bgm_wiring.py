"""`bgm.style` của spec phải THỰC SỰ tới được file ra.

Trước gói này `bgm` chỉ là dữ liệu đi qua: spec kiểm nó, rồi không ai dùng. Một khoá hợp đồng
được kiểm nhưng không nối vào đâu là thứ tệ hơn khoá không có — người dùng khai nhạc nền, lệnh
báo xanh, video ra không có nhạc và không ai biết vì sao.
"""
import os

import pytest

from conftest import fake_voice_studio
from video_studio import render


def _outputs(tmp_path, *names):
    out = []
    for i, n in enumerate(names):
        p = tmp_path / n
        p.write_text("video", encoding="utf-8")
        out.append({"kind": "long" if i == 0 else "short", "path": str(p), "duration": 1.0})
    return out


def test_bgm_style_is_mixed_into_every_output(tmp_path, monkeypatch):
    pkg = fake_voice_studio(monkeypatch)
    outs = _outputs(tmp_path, "a.mp4", "b.mp4")
    mixed = render.apply_bgm(outs, {"bgm": {"style": "lofi", "volume": 0.2}})
    assert mixed == [o["path"] for o in outs]
    assert [c[1]["bgm"] for c in pkg.calls] == ["lofi", "lofi"]
    assert pkg.calls[0][1]["volume"] == 0.2


@pytest.mark.parametrize("spec", [{}, {"bgm": {"style": None}}, {"bgm": "none"}])
def test_no_style_means_no_call_at_all(spec, tmp_path, monkeypatch):
    pkg = fake_voice_studio(monkeypatch)
    assert render.apply_bgm(_outputs(tmp_path, "a.mp4"), spec) == []
    assert pkg.calls == []


def test_a_missing_music_file_does_not_kill_the_render(tmp_path, monkeypatch, capsys):
    fake_voice_studio(monkeypatch, mix_bgm=lambda *a: False)
    outs = _outputs(tmp_path, "a.mp4")
    assert render.apply_bgm(outs, {"bgm": {"style": "khong-co"}}) == []
    assert "giữ nguyên bản không nhạc" in capsys.readouterr().err


def test_a_broken_music_file_does_not_kill_the_render_either(tmp_path, monkeypatch, capsys):
    """Docstring hứa "mất nhạc nền không được giết lượt render" — phải đúng với MỌI lỗi.

    Chỉ cứu `StationMissing` thì một file nhạc hỏng (ffmpeg ném EngineError) làm cả lượt thoát
    MÃ 1 **sau khi mp4 đã nằm trên đĩa**. Bên gọi đọc mã 1 là "render hỏng, thử lại" nên nó
    render lại cả lượt rồi đâm vào đúng file nhạc đó — hỏng mãi mãi, mỗi lần tốn một lượt render.
    """
    from video_studio.contract import EngineError

    def boom(path, bgm, volume):
        raise EngineError("ffmpeg: Invalid data found when processing input")

    fake_voice_studio(monkeypatch, mix_bgm=boom)
    outs = _outputs(tmp_path, "a.mp4", "b.mp4")
    assert render.apply_bgm(outs, {"bgm": {"style": "lofi"}}) == []
    err = capsys.readouterr().err
    assert "giữ nguyên bản không nhạc" in err
    assert "Invalid data" in err                     # lỗi thật vẫn tới được người đọc
    assert err.count("giữ nguyên bản không nhạc") == 2, "lỗi một file không được bỏ file kia"
    for o in outs:
        assert os.path.isfile(o["path"]), "file đã dựng phải còn nguyên trên đĩa"


def test_without_the_voice_repo_bgm_is_skipped_not_fatal(tmp_path, monkeypatch, capsys):
    monkeypatch.setitem(__import__("sys").modules, "voice_studio", None)
    outs = _outputs(tmp_path, "a.mp4")
    assert render.apply_bgm(outs, {"bgm": {"style": "lofi"}}) == []
    assert "bỏ qua nhạc nền" in capsys.readouterr().err


def test_render_result_reports_what_was_mixed(tmp_path, monkeypatch):
    fake_voice_studio(monkeypatch)
    seen = _outputs(tmp_path, "a.mp4")
    monkeypatch.setattr(render, "_template", lambda p: (lambda data, out_dir: seen))
    spec = tmp_path / "spec.json"
    spec.write_text('{"schema_version": 1, "brand": {"a": "A", "b": "B", "site": "s.example"},'
                    ' "bgm": {"style": "lofi"}, "segments": [{"t": "x"}]}', encoding="utf-8")

    class Args:
        project, input, out = "news", str(spec), str(tmp_path / "out")
        brand = voice_profile = ""

    res = render.do_render(Args())
    assert res["bgm"] == {"style": "lofi", "mixed": [seen[0]["path"]]}
