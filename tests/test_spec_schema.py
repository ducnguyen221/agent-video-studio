"""Cổng HỢP ĐỒNG DỮ LIỆU: spec `schema_version=1` của `video-studio render`.

Điều quan trọng nhất ở đây là một câu: **thiếu `brand` thì phải HỎNG**, mã 2, chứ không được
lùi về một thương hiệu mặc định. Bản `.tts` cũ có tên thương hiệu và tên miền ngay trong mã,
nên "quên khai" vẫn ra video — và video đó mang danh tính của người khác. Test dưới đây là chỗ
giữ cho lỗi ấy không quay lại.
"""
import json

import pytest

from video_studio import contract, spec
from video_studio.contract import ContractError

MIN_BRAND = {"a": "Tin", "b": "Ngày", "site": "vi-du.example"}


def s(**kw):
    base = {"schema_version": 1, "brand": dict(MIN_BRAND), "date": "2026-01-02"}
    base.update(kw)
    return base


def err(data, **kw):
    with pytest.raises(ContractError) as e:
        spec.validate(data, **kw)
    assert e.value.code == contract.CONTRACT_ERROR
    return str(e.value)


# ── schema_version ──────────────────────────────────────────────────────────────────────

def test_valid_minimum_spec_passes():
    out = spec.validate(s())
    assert out["brand"]["a"] == "Tin"
    assert out["outputs"] == {"long": True, "short": True}
    assert out["bgm"] == {"style": None} and out["voice"] == {}


def test_missing_schema_version_is_rejected():
    d = s()
    d.pop("schema_version")
    assert "schema_version" in err(d)


@pytest.mark.parametrize("ver", [0, 2, "1", "1.0", [], {}])
def test_wrong_schema_version_is_rejected(ver):
    assert "schema_version" in err(s(schema_version=ver))


# ── brand: khối quyết định ĐẠT/TRƯỢT của việc tẩy danh tính ─────────────────────────────

def test_missing_brand_is_contract_error():
    d = s()
    d.pop("brand")
    msg = err(d)
    assert "brand" in msg and "mặc định" in msg


@pytest.mark.parametrize("key", ["a", "b", "site"])
def test_each_required_brand_key_is_enforced(key):
    d = s()
    d["brand"].pop(key)
    assert key in err(d)


@pytest.mark.parametrize("empty", ["", "   ", None])
def test_blank_brand_value_counts_as_missing(empty):
    d = s()
    d["brand"]["site"] = empty
    assert "site" in err(d)


def test_brand_accepts_optional_accent_logo_pronounce():
    d = s()
    d["brand"].update({"accent": ["#123456", "#abcdef"], "logo": "logo.svg",
                       "pronounce": {r"vi-du\.example": "ví dụ chấm ét xăm pồ"}})
    assert spec.validate(d)["brand"]["pronounce"]


def test_pronounce_must_be_a_regex_table():
    d = s()
    d["brand"]["pronounce"] = {"(chưa đóng": "x"}
    assert "pronounce" in err(d)
    d["brand"]["pronounce"] = ["a", "b"]
    assert "pronounce" in err(d)


def test_brand_file_overrides_spec_and_can_supply_missing_keys(tmp_path):
    d = s()
    d["brand"].pop("site")
    f = tmp_path / "brand.json"
    f.write_text(json.dumps({"site": "kenh.example", "a": "Khác"}), encoding="utf-8")
    out = spec.validate(d, brand_file=str(f))
    assert out["brand"]["site"] == "kenh.example" and out["brand"]["a"] == "Khác"


# ── voice ───────────────────────────────────────────────────────────────────────────────

def test_voice_keys_are_closed():
    assert "khoá lạ" in err(s(voice={"profile": "p", "toc_do": 1.2}))


@pytest.mark.parametrize("bad", [{"speed": 4}, {"speed": "nhanh"}, {"seed": "7"},
                                 {"profile": 12}])
def test_voice_values_are_checked(bad):
    err(s(voice=bad))


def test_voice_seed_must_be_int_because_engine_is_not_reproducible_without_it():
    assert spec.validate(s(voice={"seed": 1234}))["voice"]["seed"] == 1234


# ── bgm ─────────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("given,want", [
    (None, None), ("none", None), ({"style": "none"}, None),
    ("lofi", "lofi"), ({"style": "lofi"}, "lofi"), ({"style": None}, None),
])
def test_bgm_none_and_style(given, want):
    d = s()
    if given is not None:
        d["bgm"] = given
    assert spec.validate(d)["bgm"]["style"] == want


def test_bgm_bad_shape():
    err(s(bgm=["lofi"]))


# ── outputs ─────────────────────────────────────────────────────────────────────────────

def test_outputs_default_to_both():
    assert spec.validate(s())["outputs"] == {"long": True, "short": True}


def test_outputs_can_name_files_and_switch_off():
    out = spec.validate(s(outputs={"long": "ban-dai.mp4", "short": False}))["outputs"]
    assert out == {"long": "ban-dai.mp4", "short": False}


def test_outputs_reject_paths_and_unknown_keys():
    assert "TÊN FILE" in err(s(outputs={"long": "thu-muc/a.mp4"}))
    assert "khoá lạ" in err(s(outputs={"long": True, "medium": True}))


def test_outputs_all_off_is_an_error():
    assert "không có gì để render" in err(s(outputs={"long": False, "short": False}))


# ── đọc từ file ─────────────────────────────────────────────────────────────────────────

def test_load_reads_utf8_bom_and_reports_broken_json(tmp_path):
    good = tmp_path / "g.json"
    good.write_text(json.dumps(s(), ensure_ascii=False), encoding="utf-8-sig")
    assert spec.load(str(good))["brand"]["a"] == "Tin"

    bad = tmp_path / "b.json"
    bad.write_text("{khong phai json", encoding="utf-8")
    with pytest.raises(ContractError) as e:
        spec.load(str(bad))
    assert "JSON hỏng" in str(e.value)

    with pytest.raises(ContractError):
        spec.load(str(tmp_path / "khong-co.json"))


def test_content_keeps_the_old_sidecar_shape():
    """Phần nội dung phải đi qua nguyên vẹn — spec = sidecar cũ + bốn khối hợp đồng."""
    d = s(top_story={"sections": [{"title": "x"}]}, display_date="Thứ Hai", verdict="ổn")
    content = spec.content_of(spec.validate(d))
    assert content["top_story"]["sections"][0]["title"] == "x"
    assert content["display_date"] == "Thứ Hai" and content["verdict"] == "ổn"
    assert "brand" not in content and "schema_version" not in content
