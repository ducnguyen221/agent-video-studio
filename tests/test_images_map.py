"""`video-studio render --images <images.json>`: ghép ảnh người dùng vào đúng cảnh.

Không cần Node/HyperFrames: `_template` bị thay bằng hàm giả giữ lại spec đã được ghép.
Định dạng: {"schema_version": 1, "scenes": {"1": "anh/a.png", "3": "anh/b.jpg"}} — khoá là số
cảnh 1-based, đường tương đối neo vào thư mục chứa images.json. Bốn project (`repo-today`, `news`,
`news-weekly`, `topstory`), MỘT ảnh mỗi cảnh (chuỗi hoặc danh sách một phần tử; URL được, trừ `repo-today`).
"""
import json
import os

import pytest

from conftest import last_json
from video_studio import contract, render, spec as spec_mod


def _spec(tmp_path, project_scenes=3, segments=None, sections=None, weekly=False):
    p = tmp_path / "spec.json"
    doc = {
        "schema_version": 1, "date": "2026-01-02",
        "brand": {"a": "A", "b": "B", "site": "s.example"},
        "scenes": [{"title": f"c{i}", "narration": "x"} for i in range(1, project_scenes + 1)],
        "top_story": {"sections": [{"title": "x"}] if sections is None else sections},
    }
    if segments is not None:
        doc["weekly_video" if weekly else "daily_video"] = {"segments": segments}
    p.write_text(json.dumps(doc), encoding="utf-8")
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
    assert "cảnh 4 vượt" in last_json(capsys.readouterr().out)["error"]


def test_spec_without_the_projects_scene_list_is_code_2(tmp_path, monkeypatch, capsys):
    _png(tmp_path / "a.png")
    img_p = _images(tmp_path, {"1": "a.png"})
    rc, _seen = _run(tmp_path, monkeypatch, "news", _spec(tmp_path), img_p)
    assert rc == contract.CONTRACT_ERROR
    assert "đoạn tin" in last_json(capsys.readouterr().out)["error"]


def test_relative_path_is_anchored_to_the_images_file_not_cwd_or_spec(tmp_path, monkeypatch):
    sub = tmp_path / "ban-do"
    _png(sub / "anh" / "a.png")           # chỉ tồn tại cạnh images.json
    img_p = _images(sub, {"2": "anh/a.png"})
    rc, seen = _run(tmp_path, monkeypatch, "repo-today", _spec(tmp_path), img_p)
    assert rc == contract.OK
    assert seen["spec"]["_image_files"]["img/s2_a.png"] == str(sub / "anh" / "a.png")
    assert seen["spec"]["scenes"][1]["hero_image"] == "img/s2_a.png"


# ── vòng sửa theo review (RF-1…RF-7) ─────────────────────────────────────────────────────

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


def test_copy_image_files_puts_planned_images_into_project_img(tmp_path):
    """RF-7: `apply_images` chỉ ghi kế hoạch; việc chép nằm ở `copy_image_files`."""
    src = _png(tmp_path / "anh" / "a.png")
    proj = tmp_path / "proj"
    proj.mkdir()
    spec_mod.copy_image_files(str(proj), {"img/s1_a.png": str(src)})
    assert (proj / "img" / "s1_a.png").read_bytes() == src.read_bytes()

def test_duplicate_scene_key_in_images_file_is_code_2(tmp_path, monkeypatch, capsys):
    """RF-r2-2: `json.load` thường để khoá sau đè khoá trước — im lặng bỏ một ảnh."""
    _png(tmp_path / "a.png")
    _png(tmp_path / "b.png")
    img_p = _raw(tmp_path, '{"schema_version": 1, "scenes": {"1": "a.png", "1": "b.png"}}')
    rc, _ = _run(tmp_path, monkeypatch, "repo-today", _spec(tmp_path), img_p)
    assert rc == contract.CONTRACT_ERROR
    assert "trùng" in last_json(capsys.readouterr().out)["error"]


def test_bad_images_file_leaves_no_empty_out_dir(tmp_path, monkeypatch, capsys):
    """RF-lo-5: kiểm images.json TRƯỚC khi tạo --out, để lỗi mã 2 không để lại thư mục rỗng."""
    monkeypatch.setattr(render, "_template", lambda p: lambda spec, out: [])
    out = tmp_path / "o"
    rc = render.main(["--project", "repo-today", "--input", str(_spec(tmp_path)),
                      "--images", str(_raw(tmp_path, "{hong")), "--out", str(out), "--json"])
    assert rc == contract.CONTRACT_ERROR
    assert last_json(capsys.readouterr().out)["code"] == 2
    assert not out.exists()



# ── danh sách cảnh theo project (`scene_list_of`) ───────────────────────────────────────

@pytest.mark.parametrize("project,spec_dict,expect_len", [
    ("repo-today", {"scenes": [{}, {}]}, 2),
    ("news", {"daily_video": {"segments": [{}, {}, {}]}}, 3),
    ("news-weekly", {"weekly_video": {"segments": [{}]}}, 1),
    ("news", {"segments": [{}]}, 1),
    ("topstory", {"top_story": {"sections": [{}, {}]}}, 2),
    ("topstory", {"story": {"sections": [{}]}}, 1),
])
def test_scene_list_of_picks_the_list_each_template_reads(project, spec_dict, expect_len):
    assert len(spec_mod.scene_list_of(spec_dict, project)) == expect_len


@pytest.mark.parametrize("project,spec_dict,needle", [
    ("repo-today", {}, "scenes"),
    ("repo-today", {"scenes": "x"}, "scenes"),
    ("news", {}, "đoạn tin"),
    ("news", {"daily_video": {"segments": {"a": 1}}}, "segments"),
    ("news", {"daily_video": "x"}, "object"),
    ("topstory", {}, "top_story"),
    ("topstory", {"top_story": "x"}, "object"),
    ("topstory", {"top_story": {"sections": "x"}}, "sections"),
    ("lạ", {}, "lạ"),
])
def test_scene_list_of_names_the_missing_field(project, spec_dict, needle):
    with pytest.raises(contract.ContractError) as e:
        spec_mod.scene_list_of(spec_dict, project)
    assert needle in str(e.value)


# ── bốn project, một ảnh mỗi cảnh, thay ảnh/clip có sẵn ─────────────────────────────────

def _norm(path):
    return os.path.normpath(str(path))


def test_news_user_image_replaces_the_segment_images(tmp_path, monkeypatch):
    _png(tmp_path / "anh" / "a.png")
    segs = [{"images": ["https://cu.example/z.jpg"]}, {"images": "https://one.example/o.png"}, {"title": "c"}]
    img_p = _images(tmp_path, {"1": "anh/a.png", "2": ["https://x/y.png"]})
    rc, seen = _run(tmp_path, monkeypatch, "news", _spec(tmp_path, segments=segs), img_p)
    assert rc == contract.OK
    seg = seen["spec"]["daily_video"]["segments"]
    assert seg[0]["images"] == [_norm(tmp_path / "anh" / "a.png")]
    assert seg[1]["images"] == ["https://x/y.png"]
    assert seg[2] == {"title": "c"}
    assert "_image_files" not in seen["spec"]


def test_news_weekly_maps_like_news(tmp_path, monkeypatch):
    _png(tmp_path / "anh" / "a.png")
    segs = [{"images": ["https://cu.example/z.jpg"]}, {"title": "b"}]
    img_p = _images(tmp_path, {"1": "anh/a.png"})
    rc, seen = _run(tmp_path, monkeypatch, "news-weekly", _spec(tmp_path, segments=segs, weekly=True), img_p)
    assert rc == contract.OK
    seg = seen["spec"]["weekly_video"]["segments"]
    assert seg[0]["images"] == [_norm(tmp_path / "anh" / "a.png")]
    assert seg[1] == {"title": "b"}
    assert "_image_files" not in seen["spec"]


def test_topstory_user_image_replaces_the_section_media_even_a_clip(tmp_path, monkeypatch):
    _png(tmp_path / "anh" / "a.png")
    secs = [{"title": "a", "media": [{"type": "clip", "src": "c.mp4"}]},
            {"title": "b", "media": "https://old.example/o.png"}, {"title": "c"}]
    img_p = _images(tmp_path, {"1": "anh/a.png", "2": ["https://x/y.png"]})
    rc, seen = _run(tmp_path, monkeypatch, "topstory", _spec(tmp_path, sections=secs), img_p)
    assert rc == contract.OK
    sec = seen["spec"]["top_story"]["sections"]
    assert sec[0]["media"] == [{"type": "image", "src": _norm(tmp_path / "anh" / "a.png")}]
    assert sec[1]["media"] == [{"type": "image", "src": "https://x/y.png"}]
    assert sec[2] == {"title": "c"}
    assert "_image_files" not in seen["spec"]


def test_repo_today_single_local_image_is_unchanged_from_0_5_0(tmp_path, monkeypatch):
    _png(tmp_path / "anh" / "a.png")
    _png(tmp_path / "anh" / "b.jpg")
    img_p = _images(tmp_path, {"1": ["anh/a.png"], "3": "anh/b.jpg"})
    rc, seen = _run(tmp_path, monkeypatch, "repo-today", _spec(tmp_path), img_p)
    assert rc == contract.OK
    sc = seen["spec"]["scenes"]
    assert sc[0]["hero_image"] == "img/s1_a.png" and sc[2]["hero_image"] == "img/s3_b.jpg"
    assert "hero_image" not in sc[1]
    assert seen["spec"]["_image_files"]["img/s1_a.png"] == _norm(tmp_path / "anh" / "a.png")


@pytest.mark.parametrize("project,segments,sections,mapping,needle", [
    ("repo-today", None, None, {"1": ["a.png", "b.png"]}, "một ảnh mỗi cảnh"),
    ("news", [{}] * 3, None, {"1": ["a.png", "b.png"]}, "một ảnh mỗi cảnh"),
    ("repo-today", None, None, {"1": "https://x/y.png"}, "không nhận URL"),
    ("news", [{}] * 3, None, {"1": []}, "rỗng"),
    ("news", [{}] * 3, None, {"1": [1]}, "chuỗi"),
    ("news", [{}] * 3, None, {"1": ""}, "chuỗi"),
    ("news", [{}] * 3, None, {"1": 7}, "chuỗi hoặc danh sách"),
    ("news", [{}] * 3, None, {"4": "a.png"}, "cảnh 4 vượt"),
    ("topstory", None, [{}] * 2, {"3": "a.png"}, "cảnh 3 vượt"),
    ("news", None, None, {"1": "a.png"}, "đoạn tin"),
    ("topstory", None, "x", {"1": "a.png"}, "sections"),
])
def test_bad_scene_values_are_code_2(tmp_path, monkeypatch, capsys, project, segments, sections, mapping, needle):
    _png(tmp_path / "a.png")
    _png(tmp_path / "b.png")
    spec_p = _spec(tmp_path, segments=segments, sections=sections)
    rc, _seen = _run(tmp_path, monkeypatch, project, spec_p, _images(tmp_path, mapping))
    assert rc == contract.CONTRACT_ERROR
    payload = last_json(capsys.readouterr().out)
    assert payload["code"] == 2 and needle in payload["error"], payload


def test_render_help_describes_images_for_four_projects(capsys):
    assert render.main(["--help"]) == contract.OK
    out = " ".join(capsys.readouterr().out.split())
    assert "chỉ project repo-today" not in out
    for w in ("news-weekly", "topstory", "một ảnh", "URL", "thay ảnh/clip"):
        assert w in out


def test_mapped_news_segments_are_marked_as_user_images_and_others_are_not(tmp_path, monkeypatch):
    segs = [{"title": "a"}, {"title": "b"}, {"title": "c"}]
    img_p = _images(tmp_path, {"1": "https://x/y.png"})
    rc, seen = _run(tmp_path, monkeypatch, "news", _spec(tmp_path, segments=segs), img_p)
    assert rc == contract.OK
    seg = seen["spec"]["daily_video"]["segments"]
    assert seg[0][spec_mod.USER_IMAGE_KEY] is True
    assert spec_mod.USER_IMAGE_KEY not in seg[1] and spec_mod.USER_IMAGE_KEY not in seg[2]


def test_the_segments_error_names_the_real_project(tmp_path):
    with pytest.raises(contract.ContractError) as e:
        spec_mod.scene_list_of({"weekly_video": {"segments": "x"}}, "news-weekly")
    assert "project news-weekly" in str(e.value)


def test_the_many_images_error_does_not_cite_an_internal_ledger_code(tmp_path, monkeypatch, capsys):
    _png(tmp_path / "a.png")
    _png(tmp_path / "b.png")
    rc, _ = _run(tmp_path, monkeypatch, "news", _spec(tmp_path, segments=[{}] * 2),
                 _images(tmp_path, {"1": ["a.png", "b.png"]}))
    assert rc == contract.CONTRACT_ERROR
    err = last_json(capsys.readouterr().out)["error"]
    assert "chưa hỗ trợ nhiều ảnh mỗi cảnh" in err and "RQ-" not in err
