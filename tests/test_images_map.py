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
    assert sc[0]["hero_image"] == "img/s1_a.png" and sc[2]["hero_image"] == "img/s3_b.jpg"
    assert "hero_image" not in sc[1]
    files = seen["spec"]["_image_files"]
    assert files["img/s1_a.png"] == str(tmp_path / "anh" / "a.png")


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
    assert seen["spec"]["_image_files"]["img/s2_a.png"] == str(sub / "anh" / "a.png")
    assert seen["spec"]["scenes"][1]["hero_image"] == "img/s2_a.png"


# ── vòng sửa theo review (RF-1…RF-7) ─────────────────────────────────────────────────────

import pytest


def _raw(folder, text, name="images.json"):
    folder.mkdir(parents=True, exist_ok=True)
    p = folder / name
    p.write_text(text, encoding="utf-8")
    return p


def test_destination_names_are_unique_even_with_the_collision_prefix(tmp_path, monkeypatch):
    """RF-1: `c/s2_x.png` + hai `x.png` không được dồn hai cảnh vào cùng `img/s2_x.png`."""
    for rel in ("c/s2_x.png", "a/x.png", "b/x.png"):
        _png(tmp_path / rel)
    img_p = _images(tmp_path, {"1": "c/s2_x.png", "3": "a/x.png", "2": "b/x.png"})
    rc, seen = _run(tmp_path, monkeypatch, "repo-today", _spec(tmp_path), img_p)
    assert rc == contract.OK
    dsts = [s["hero_image"] for s in seen["spec"]["scenes"]]
    assert len({d.casefold() for d in dsts}) == 3
    files = seen["spec"]["_image_files"]
    assert len(files) == 3 and set(files) == set(dsts)


def test_destination_names_differing_only_by_case_do_not_collide(tmp_path, monkeypatch):
    """RF-2: `A.png` và `a.png` là CÙNG file trên NTFS/APFS."""
    _png(tmp_path / "u" / "A.png")
    _png(tmp_path / "v" / "a.png")
    img_p = _images(tmp_path, {"1": "u/A.png", "2": "v/a.png"})
    rc, seen = _run(tmp_path, monkeypatch, "repo-today", _spec(tmp_path), img_p)
    assert rc == contract.OK
    dsts = [s["hero_image"] for s in seen["spec"]["scenes"][:2]]
    assert len({d.casefold() for d in dsts}) == 2


@pytest.mark.parametrize("body", [
    '{"scenes": {"1": "a.png"}}',                                   # thiếu schema_version
    '{"schema_version": 2, "scenes": {"1": "a.png"}}',              # sai bản
    '{"schema_version": 1, "scenes": {"1": "a.png"}, "extra": 1}',  # khoá lạ cấp trên
])
def test_images_file_schema_is_strict(tmp_path, monkeypatch, capsys, body):
    """RF-3."""
    _png(tmp_path / "a.png")
    rc, _ = _run(tmp_path, monkeypatch, "repo-today", _spec(tmp_path), _raw(tmp_path, body))
    assert rc == contract.CONTRACT_ERROR
    assert last_json(capsys.readouterr().out)["code"] == 2


@pytest.mark.parametrize("key", ["01", "0", "\u00b2", "x", "-1", "1.0", " 1"])
def test_scene_keys_must_be_plain_positive_integers(tmp_path, monkeypatch, capsys, key):
    """RF-4: `str.isdigit` nhận cả `²`, và `01` là khoá thứ hai của cảnh 1."""
    _png(tmp_path / "a.png")
    img_p = _images(tmp_path, {key: "a.png"})
    rc, _ = _run(tmp_path, monkeypatch, "repo-today", _spec(tmp_path), img_p)
    assert rc == contract.CONTRACT_ERROR
    assert last_json(capsys.readouterr().out)["code"] == 2


def test_unreadable_or_broken_images_file_is_code_2(tmp_path, monkeypatch, capsys):
    """RF-5: file thiếu, là thư mục, hoặc JSON hỏng — không bao giờ traceback/mã 1."""
    spec_p = _spec(tmp_path)
    (tmp_path / "la-thu-muc").mkdir()
    for p in (tmp_path / "khong-co.json", tmp_path / "la-thu-muc", _raw(tmp_path, "{hong")):
        rc, _ = _run(tmp_path, monkeypatch, "repo-today", spec_p, p)
        assert rc == contract.CONTRACT_ERROR, p.name
        assert last_json(capsys.readouterr().out)["code"] == 2


def test_wrong_extension_is_code_2(tmp_path, monkeypatch, capsys):
    """RF-7."""
    (tmp_path / "a.gif").write_bytes(b"GIF89a")
    img_p = _images(tmp_path, {"1": "a.gif"})
    rc, _ = _run(tmp_path, monkeypatch, "repo-today", _spec(tmp_path), img_p)
    assert rc == contract.CONTRACT_ERROR
    assert ".png" in last_json(capsys.readouterr().out)["error"]


def test_deepdive_copies_planned_images_into_project_img(tmp_path):
    """RF-7: `apply_images` chỉ ghi kế hoạch; việc chép nằm ở `copy_image_files`."""
    from video_studio import spec as news_v2
    src = _png(tmp_path / "anh" / "a.png")
    proj = tmp_path / "proj"
    proj.mkdir()
    news_v2.copy_image_files(str(proj), {"img/s1_a.png": str(src)})
    assert (proj / "img" / "s1_a.png").read_bytes() == src.read_bytes()