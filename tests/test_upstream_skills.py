"""Cổng cho bộ skill HyperFrames đã chưng cất (`skills/hyperframes/`) và sổ nguồn `upstream.json`.

Ba thứ được canh ở đây, vì cả ba đều hỏng **im lặng**:

1. **Sổ khớp đĩa.** Thêm một skill mà quên ghi nguồn (hoặc ngược lại) thì `doctor --check-updates`
   sau này so với một danh sách không có thật.
2. **Nghĩa vụ giấy phép.** Apache-2.0 §4(b) đòi file đã sửa phải nói ra là đã sửa; thiếu dòng đó
   thì repo public đang phát hành lại tác phẩm của người khác mà không ghi.
3. **Không chép nhị phân.** Bộ skill upstream mang 142 file font/nhạc/ảnh mà giấy phép từng file
   chưa kiểm được — không một file nào trong số đó được vào repo này.
"""
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills" / "hyperframes"
UPSTREAM = ROOT / "upstream.json"
SOURCE_KEY = "hyperframes-skills"


def _sok():
    return json.loads(UPSTREAM.read_text(encoding="utf-8"))["sources"][SOURCE_KEY]


def _names():
    return sorted(p.parent.name for p in SKILLS.glob("*/SKILL.md"))


def test_upstream_json_and_tree_agree():
    src = _sok()
    assert sorted(src["skills"]) == _names(), "upstream.json lệch với cây skills/hyperframes/"
    assert src["distilled"] == len(_names())
    assert src["upstream_total"] == len(_names()), \
        "distill một tập con thì phải ghi rõ tổng upstream là bao nhiêu"


def test_source_pins_an_exact_version_not_a_moving_ref():
    src = _sok()
    assert re.fullmatch(r"v\d+\.\d+\.\d+", src["ref"]), src["ref"]
    assert src["license"] == "Apache-2.0"
    assert (ROOT / src["license_file"]).is_file()
    assert src["binaries_copied"] == 0


@pytest.mark.parametrize("name", _names())
def test_every_skill_records_its_source_version_and_hash(name):
    src = _sok()["skills"][name]
    text = (SKILLS / name / "SKILL.md").read_text(encoding="utf-8")
    body = text.partition("\n---\n")[2]
    assert "heygen-com/hyperframes" in body, f"{name}: thiếu tên repo nguồn"
    assert _sok()["ref"].lstrip("v") in body, f"{name}: thiếu phiên bản nguồn"
    assert src["upstream_hash"] in body, f"{name}: thiếu hash manifest của bản gốc"
    assert "Apache-2.0" in body, f"{name}: thiếu giấy phép nguồn"
    # Nghĩa vụ §4(b): nói rõ đây là bản đã sửa, không phải bản sao.
    assert "đã dịch" in body and "biên tập lại" in body, f"{name}: thiếu ghi chú 'đã sửa'"


def test_no_binary_or_reference_tree_was_copied():
    """Chỉ `SKILL.md`, không gì khác: không font, không nhạc, không ảnh, không references/."""
    extra = sorted(p.relative_to(ROOT).as_posix() for p in SKILLS.rglob("*")
                   if p.is_file() and p.name != "SKILL.md")
    assert extra == [], f"thư mục skill distill chỉ được chứa SKILL.md: {extra}"


def test_license_apache_is_the_real_text():
    text = (ROOT / "LICENSE-APACHE").read_text(encoding="utf-8")
    assert "Apache License" in text and "Version 2.0, January 2004" in text
    assert "END OF TERMS AND CONDITIONS" in text
    assert len(text) > 9000, "bản Apache-2.0 đầy đủ dài hơn thế — đừng để bản rút gọn"


def test_notice_covers_every_distilled_source():
    notice = (ROOT / "NOTICE").read_text(encoding="utf-8")
    for must in ("Apache-2.0", "LICENSE-APACHE", "heygen-com/hyperframes",
                 "notedit/vtake-skills", "leeoxiang", "browser-use/video-use"):
        assert must in notice, f"NOTICE thiếu: {must}"


def test_doctor_sees_the_drift(tmp_path, monkeypatch):
    """Đột biến: bỏ một skill khỏi sổ thì `doctor` phải kêu, không được im."""
    from video_studio import doctor
    assert doctor.skills_check()["level"] == "ok"

    real = json.loads(UPSTREAM.read_text(encoding="utf-8"))
    real["sources"][SOURCE_KEY]["skills"].pop(sorted(real["sources"][SOURCE_KEY]["skills"])[0])
    fake_repo = tmp_path / "repo"
    (fake_repo / "skills" / "hyperframes").mkdir(parents=True)
    for n in _names():
        d = fake_repo / "skills" / "hyperframes" / n
        d.mkdir()
        (d / "SKILL.md").write_text("x", encoding="utf-8")
    (fake_repo / "upstream.json").write_text(json.dumps(real), encoding="utf-8")
    monkeypatch.setattr(doctor._env, "package_repo", lambda: str(fake_repo))
    c = doctor.skills_check()
    assert c["level"] == "warn" and "chưa ghi nguồn" in c["detail"]
