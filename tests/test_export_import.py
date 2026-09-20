"""`video-studio export` / `import`: chuyển phần dữ liệu của trạm sang máy khác.

Những thứ được canh, vì mỗi cái đã có tiền lệ hỏng ở đâu đó:

- **Gói cá nhân không được đoán hộ.** Chỉ `projects/*/assets` và đúng thư mục người dùng kể tên;
  gói nhầm một thư mục khách hàng vào zip rồi gửi đi là chuyện không thu hồi được.
- **Nháp, cache, venv, cây git không vào gói.** Chúng dựng lại được và chúng là phần nặng nhất.
- **Bung gói không được đè im lặng**, và không được ghi ra ngoài trạm (zip-slip).
"""
import json
import os
import zipfile

import pytest

from conftest import last_json
from video_studio import API_VERSION, cli, contract, station


def run(argv, capsys):
    rc = cli.main(argv)
    cap = capsys.readouterr()
    return rc, cap.out, cap.err


def _w(path, text="x"):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


@pytest.fixture
def st(tmp_path):
    """Trạm có: tài sản project, nháp, cache, một bản vendored có .git, một thư mục riêng."""
    d = tmp_path / "station"
    _w(d / "station.json", json.dumps({"contract": API_VERSION, "projects_dir": "projects"}))
    _w(d / "projects" / "news" / "assets" / "logo.svg", "<svg/>")
    _w(d / "projects" / "news" / "assets" / "img" / "a.txt", "anh")
    _w(d / "projects" / "news" / "index.html", "<html>")
    _w(d / "projects" / "topstory" / "assets" / "b.txt", "b")
    _w(d / "scratch" / "tmp.mp4", "rac")
    _w(d / "cache" / "c.bin", "rac")
    _w(d / ".video-studio" / "runs" / "1" / "journal.json", "{}")
    _w(d / "vendored" / ".git" / "config", "[core]")
    _w(d / "vendored" / "helper.py", "print()")
    _w(d / "rieng" / "ghi-chu.md", "cua toi")
    return d


# ── export ──────────────────────────────────────────────────────────────────────────────

def test_personal_export_takes_project_assets_and_nothing_else(st, tmp_path, capsys):
    out = tmp_path / "p.zip"
    rc, o, err = run(["export", "--out", str(out), "--personal", "--station", str(st), "--json"],
                     capsys)
    assert rc == 0, err
    files = last_json(o)["files"]
    assert files == ["projects/news/assets/img/a.txt", "projects/news/assets/logo.svg",
                     "projects/topstory/assets/b.txt"]
    for gone in ("projects/news/index.html", "scratch/tmp.mp4", "cache/c.bin",
                 "rieng/ghi-chu.md", "vendored/helper.py"):
        assert gone not in files


def test_include_adds_exactly_the_named_folder_without_its_git(st, tmp_path, capsys):
    out = tmp_path / "p.zip"
    rc, o, err = run(["export", "--out", str(out), "--personal", "--station", str(st),
                      "--include", "rieng", "--include", "vendored", "--json"], capsys)
    assert rc == 0, err
    files = last_json(o)["files"]
    assert "rieng/ghi-chu.md" in files and "vendored/helper.py" in files
    assert not any(f.startswith("vendored/.git") for f in files), "không đóng gói cây git của người khác"


def test_include_of_a_missing_folder_is_a_contract_error(st, tmp_path, capsys):
    rc, _o, err = run(["export", "--out", str(tmp_path / "p.zip"), "--personal",
                       "--station", str(st), "--include", "khong-co"], capsys)
    assert rc == contract.CONTRACT_ERROR
    assert "khong-co" in err


def test_include_without_personal_is_refused(st, tmp_path, capsys):
    rc, _o, err = run(["export", "--out", str(tmp_path / "p.zip"), "--station", str(st),
                       "--include", "rieng"], capsys)
    assert rc == contract.CONTRACT_ERROR and "--personal" in err


def test_include_cannot_escape_the_station(st, tmp_path, capsys):
    rc, _o, err = run(["export", "--out", str(tmp_path / "p.zip"), "--personal",
                       "--station", str(st), "--include", "../.."], capsys)
    assert rc == contract.CONTRACT_ERROR and "bên trong trạm" in err


def test_full_export_skips_scratch_cache_journal_and_git(st, tmp_path, capsys):
    out = tmp_path / "all.zip"
    rc, o, err = run(["export", "--out", str(out), "--station", str(st), "--json"], capsys)
    assert rc == 0, err
    files = last_json(o)["files"]
    assert "projects/news/index.html" in files and "rieng/ghi-chu.md" in files
    for gone in ("scratch/tmp.mp4", "cache/c.bin", ".video-studio/runs/1/journal.json",
                 "vendored/.git/config"):
        assert gone not in files


def test_export_on_a_missing_station_is_code_3(tmp_path, capsys):
    rc, _o, err = run(["export", "--out", str(tmp_path / "p.zip"),
                       "--station", str(tmp_path / "khong-co")], capsys)
    assert rc == contract.STATION_MISSING and "trạm" in err


# ── import ──────────────────────────────────────────────────────────────────────────────

def _pack(st, tmp_path, capsys, *extra):
    out = tmp_path / "p.zip"
    rc, _o, err = run(["export", "--out", str(out), "--personal", "--station", str(st), *extra],
                      capsys)
    assert rc == 0, err
    return out


def test_import_writes_files_into_a_fresh_station(st, tmp_path, capsys):
    pack = _pack(st, tmp_path, capsys)
    dst = tmp_path / "other"
    rc, o, err = run(["import", "--in", str(pack), "--station", str(dst), "--json"], capsys)
    assert rc == 0, err
    assert (dst / "projects" / "news" / "assets" / "logo.svg").read_text(encoding="utf-8") == "<svg/>"
    assert last_json(o)["replaced"] == []


def test_import_never_overwrites_without_the_flag(st, tmp_path, capsys):
    pack = _pack(st, tmp_path, capsys)
    dst = tmp_path / "other"
    _w(dst / "projects" / "news" / "assets" / "logo.svg", "BAN CUA TOI")
    rc, o, err = run(["import", "--in", str(pack), "--station", str(dst), "--json"], capsys)
    assert rc == 0, err
    assert (dst / "projects" / "news" / "assets" / "logo.svg").read_text(encoding="utf-8") == "BAN CUA TOI"
    assert "projects/news/assets/logo.svg" in last_json(o)["skipped"]

    rc, o, err = run(["import", "--in", str(pack), "--station", str(dst), "--overwrite", "--json"],
                     capsys)
    assert rc == 0, err
    assert (dst / "projects" / "news" / "assets" / "logo.svg").read_text(encoding="utf-8") == "<svg/>"
    assert "projects/news/assets/logo.svg" in last_json(o)["replaced"]


def test_import_dry_run_writes_nothing(st, tmp_path, capsys):
    pack = _pack(st, tmp_path, capsys)
    dst = tmp_path / "other"
    rc, o, err = run(["import", "--in", str(pack), "--station", str(dst), "--dry-run", "--json"],
                     capsys)
    assert rc == 0, err
    assert last_json(o)["written"], "xem trước phải nói sẽ ghi gì"
    assert not dst.exists()


def test_import_refuses_a_pack_from_another_major_contract(st, tmp_path, capsys):
    pack = _pack(st, tmp_path, capsys)
    bad = tmp_path / "bad.zip"
    with zipfile.ZipFile(pack) as src, zipfile.ZipFile(bad, "w") as out:
        for n in src.namelist():
            data = src.read(n)
            if n == "manifest.json":
                m = json.loads(data.decode("utf-8"))
                m["contract"] = "99.0.0"
                data = json.dumps(m).encode("utf-8")
            out.writestr(n, data)
    rc, _o, err = run(["import", "--in", str(bad), "--station", str(tmp_path / "x")], capsys)
    assert rc == contract.CONTRACT_ERROR and "hợp đồng" in err


def test_import_refuses_a_zip_that_is_not_ours(tmp_path, capsys):
    bad = tmp_path / "x.zip"
    with zipfile.ZipFile(bad, "w") as z:
        z.writestr("hello.txt", "hi")
    rc, _o, err = run(["import", "--in", str(bad), "--station", str(tmp_path / "x")], capsys)
    assert rc == contract.CONTRACT_ERROR and "manifest" in err


@pytest.mark.parametrize("member", ["station/../escape.txt", "station/C:/escape.txt"])
def test_import_refuses_zip_slip(tmp_path, capsys, member):
    bad = tmp_path / "slip.zip"
    with zipfile.ZipFile(bad, "w") as z:
        z.writestr("manifest.json", json.dumps({"kind": "export", "contract": API_VERSION}))
        z.writestr(member, "x")
    rc, _o, err = run(["import", "--in", str(bad), "--station", str(tmp_path / "st")], capsys)
    assert rc == contract.CONTRACT_ERROR and "không an toàn" in err
    assert not (tmp_path / "escape.txt").exists()


def test_import_ignores_members_outside_the_station_prefix(tmp_path, capsys):
    """`manifest.json` và mọi thứ ngoài `station/` không bao giờ được ghi ra đĩa."""
    pack = tmp_path / "p.zip"
    with zipfile.ZipFile(pack, "w") as z:
        z.writestr("manifest.json", json.dumps({"kind": "export", "contract": API_VERSION}))
        z.writestr("README.md", "khong phai noi dung tram")
        z.writestr("station/projects/a/assets/x.txt", "ok")
    dst = tmp_path / "st"
    rc, o, err = run(["import", "--in", str(pack), "--station", str(dst), "--json"], capsys)
    assert rc == 0, err
    assert last_json(o)["written"] == ["projects/a/assets/x.txt"]
    assert not (dst / "README.md").exists() and not (dst / "manifest.json").exists()


def test_round_trip_keeps_bytes(st, tmp_path, capsys):
    pack = _pack(st, tmp_path, capsys, "--include", "rieng")
    dst = tmp_path / "other"
    assert run(["import", "--in", str(pack), "--station", str(dst)], capsys)[0] == 0
    for rel in ("projects/news/assets/logo.svg", "projects/news/assets/img/a.txt",
                "projects/topstory/assets/b.txt", "rieng/ghi-chu.md"):
        a = (st / rel.replace("/", os.sep)).read_bytes()
        b = (dst / rel.replace("/", os.sep)).read_bytes()
        assert a == b, rel


def test_station_module_is_the_only_place_that_unpacks():
    """`import_pack` phải đi qua `_safe_member` — đừng ai thêm một `extractall()` thứ hai."""
    src = (station.__file__)
    text = open(src, encoding="utf-8").read()
    assert "extractall" not in text, "extractall bỏ qua mọi kiểm tra zip-slip"
