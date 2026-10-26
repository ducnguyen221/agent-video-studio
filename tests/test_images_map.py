"""`video-studio render --images <images.json>`: ghép ảnh người dùng vào đúng cảnh.

Không cần Node/HyperFrames: `_template` bị thay bằng hàm giả giữ lại spec đã được ghép.
Định dạng: {"schema_version": 1, "scenes": {"1": "anh/a.png", "3": "anh/b.jpg"}} — khoá là số
cảnh 1-based, đường tương đối neo vào thư mục chứa images.json. Chỉ project `repo-today`.
"""
import json

from conftest import last_json
from video_studio import contract, render


def _spec(tmp_path, project_scenes=3):
    p = tmp_path / "spec.json"
    p.write_text(json.dumps({
        "schema_version": 1, "date": "2026-01-02",
        "brand": {"a": "A", "b": "B", "site": "s.example"},
        "scenes": [{"title": f"c{i}", "narration": "x"} for i in range(1, project_scenes + 1)],
        "top_story": {"sections": [{"title": "x"}]},
    }), encoding="utf-8")
    return p


def _images(folder, mapping, name="images.json"):
    folder.mkdir(parents=True, exist_ok=True)
    p = folder / name
    p.write_text(json.dumps({"schema_version": 1, "scenes": mapping}), encoding="utf-8")
    return p


def _png(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"\x89PNG\r\n\x1a\n")
    return path


def _run(tmp_path, monkeypatch, project, spec_p, images_p):
    seen = {}
    monkeypatch.setattr(render, "_template",
                        lambda p: lambda spec, out: seen.update(spec=spec) or [])
    rc = render.main(["--project", project, "--input", str(spec_p), "--images", str(images_p),
                      "--out", str(tmp_path / "o"), "--json"])
    return rc, seen


def test_images_land_on_the_numbered_scenes_and_others_are_kept(tmp_path, monkeypatch):
    _png(tmp_path / "anh" / "a.png")
    _png(tmp_path / "anh" / "b.jpg")
    img_p = _images(tmp_path, {"1": "anh/a.png", "3": "anh/b.jpg"})
    rc, seen = _run(tmp_path, monkeypatch, "repo-today", _spec(tmp_path), img_p)
    assert rc == contract.OK
    sc = seen["spec"]["scenes"]
    assert sc[0]["hero_image"] == "img/a.png" and sc[2]["hero_image"] == "img/b.jpg"
    assert "hero_image" not in sc[1]
    files = seen["spec"]["_image_files"]
    assert files["img/a.png"] == str(tmp_path / "anh" / "a.png")


def test_missing_image_file_is_code_2(tmp_path, monkeypatch, capsys):
    img_p = _images(tmp_path, {"1": "anh/khong-co.png"})
    rc, _seen = _run(tmp_path, monkeypatch, "repo-today", _spec(tmp_path), img_p)
    assert rc == contract.CONTRACT_ERROR
    payload = last_json(capsys.readouterr().out)
    assert payload["ok"] is False and payload["code"] == 2 and "khong-co.png" in payload["error"]


def test_scene_number_beyond_the_scenes_is_code_2(tmp_path, monkeypatch, capsys):
    _png(tmp_path / "a.png")
    img_p = _images(tmp_path, {"4": "a.png"})
    rc, _seen = _run(tmp_path, monkeypatch, "repo-today", _spec(tmp_path, 3), img_p)
    assert rc == contract.CONTRACT_ERROR
    assert "4" in last_json(capsys.readouterr().out)["error"]


def test_project_without_scenes_is_code_2(tmp_path, monkeypatch, capsys):
    _png(tmp_path / "a.png")
    img_p = _images(tmp_path, {"1": "a.png"})
    rc, _seen = _run(tmp_path, monkeypatch, "news", _spec(tmp_path), img_p)
    assert rc == contract.CONTRACT_ERROR
    assert "repo-today" in last_json(capsys.readouterr().out)["error"]


def test_relative_path_is_anchored_to_the_images_file_not_cwd_or_spec(tmp_path, monkeypatch):
    sub = tmp_path / "ban-do"
    _png(sub / "anh" / "a.png")           # chỉ tồn tại cạnh images.json
    img_p = _images(sub, {"2": "anh/a.png"})
    rc, seen = _run(tmp_path, monkeypatch, "repo-today", _spec(tmp_path), img_p)
    assert rc == contract.OK
    assert seen["spec"]["_image_files"]["img/a.png"] == str(sub / "anh" / "a.png")
    assert seen["spec"]["scenes"][1]["hero_image"] == "img/a.png"
