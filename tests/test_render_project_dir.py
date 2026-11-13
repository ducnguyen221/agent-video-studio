"""`render --project-dir`: project HyperFrames tự dựng, chạy cô lập bằng engine ghim.

Không cần Node: `subprocess.run` được thay bằng bản giả ghi lại lời gọi.
"""
import os
import subprocess

import pytest

from conftest import last_json
from video_studio import _env, render

FAKE_NPX = "/fake/bin/npx"


class Rec:
    def __init__(self, check_rc=0, render_rc=0):
        self.calls = []
        self.check_rc, self.render_rc = check_rc, render_rc
        self.staged = None

    def __call__(self, argv, **kw):
        self.calls.append((argv, kw))
        cwd = kw.get("cwd")
        if "check" in argv:
            self.staged = sorted(os.listdir(cwd))
            return subprocess.CompletedProcess(argv, self.check_rc, b"", b"bad composition\n")
        if self.render_rc:
            raise subprocess.CalledProcessError(self.render_rc, argv, output=b"", stderr=b"boom")
        out = argv[argv.index("-o") + 1]
        with open(out if os.path.isabs(out) else os.path.join(cwd, out), "wb") as f:
            f.write(b"mp4")
        return subprocess.CompletedProcess(argv, 0, b"", b"")


@pytest.fixture
def rec(monkeypatch):
    monkeypatch.setattr(_env, "npx_exe", lambda: FAKE_NPX)
    monkeypatch.setattr(_env, "node_exe", lambda: "/fake/bin/node")
    monkeypatch.setattr(_env, "ffmpeg_exe", lambda: "/fake/bin/ffmpeg")
    monkeypatch.setattr(_env, "hyperframes_spec", lambda version=None: "hyperframes@9.9.9")
    r = Rec()
    monkeypatch.setattr(render.subprocess, "run", r)
    monkeypatch.setattr(render, "engine_versions", lambda: {"hyperframes": "9.9.9"})
    return r


@pytest.fixture
def proj(tmp_path):
    d = tmp_path / "myproj"
    (d / "assets").mkdir(parents=True)
    (d / "index.html").write_text("<html></html>", encoding="utf-8")
    (d / "assets" / "a.png").write_bytes(b"png")
    return d


def run(proj, tmp_path, capsys, *extra):
    rc = render.main(["--project-dir", str(proj), "--out", str(tmp_path / "out"), "--json", *extra])
    return rc, capsys.readouterr()


def test_happy_path_check_then_render_in_staged_copy(rec, proj, tmp_path, capsys):
    rc, cap = run(proj, tmp_path, capsys)
    assert rc == 0
    res = last_json(cap.out)
    assert res["ok"] and os.path.isfile(res["outputs"][0]["path"])
    assert res["outputs"][0]["path"] == str(tmp_path / "out" / "myproj.mp4")
    (chk, ckw), (rnd, rkw) = rec.calls
    assert chk == [FAKE_NPX, "--yes", "hyperframes@9.9.9", "check", "--strict"]
    assert rnd[:3] == [FAKE_NPX, "--yes", "hyperframes@9.9.9"] and "render" in rnd
    assert not isinstance(chk, str) and not ckw.get("shell")
    # chạy ở bản chép, không phải thư mục người dùng
    assert os.path.abspath(ckw["cwd"]) != str(proj) and not os.path.exists(ckw["cwd"])
    assert rec.staged == ["assets", "index.html"]


def test_npm_userconfig_pointed_at_empty_file(rec, proj, tmp_path, capsys, monkeypatch):
    monkeypatch.setenv("npm_config_userconfig", "/evil/.npmrc")
    seen = {}
    orig = rec.__call__

    def spy(argv, **kw):
        env = kw["env"]
        # RF21: npm thoát "double-loading config" nếu user và global trỏ cùng một file
        assert env["npm_config_userconfig"] != env["npm_config_globalconfig"]
        assert os.path.getsize(env["npm_config_globalconfig"]) == 0
        seen[argv[3]] = (env["npm_config_userconfig"], os.path.getsize(env["npm_config_userconfig"]))
        return orig(argv, **kw)
    monkeypatch.setattr(render.subprocess, "run", spy)
    rc, _ = run(proj, tmp_path, capsys)
    assert rc == 0
    assert set(seen) == {"check", "render"}
    for path, size in seen.values():
        assert path != "/evil/.npmrc" and size == 0


@pytest.mark.parametrize("name", [".npmrc", "package.json"])
def test_rejects_npm_files(rec, proj, tmp_path, capsys, name):
    (proj / name).write_text("x", encoding="utf-8")
    rc, cap = run(proj, tmp_path, capsys)
    assert rc == 2 and not rec.calls
    assert not (tmp_path / "out").exists()
    assert last_json(cap.out)["ok"] is False


def test_rejects_node_modules_and_nested_npmrc(rec, proj, tmp_path, capsys):
    (proj / "node_modules" / ".bin").mkdir(parents=True)
    assert run(proj, tmp_path, capsys)[0] == 2
    import shutil
    shutil.rmtree(proj / "node_modules")
    (proj / "assets" / ".npmrc").write_text("x", encoding="utf-8")
    assert run(proj, tmp_path, capsys)[0] == 2
    assert not rec.calls


def test_rejects_symlink(rec, proj, tmp_path, capsys):
    target = tmp_path / "secret.txt"
    target.write_text("s", encoding="utf-8")
    try:
        os.symlink(target, proj / "assets" / "link.txt")
    except (OSError, NotImplementedError):
        pytest.skip("symlink không tạo được trên máy này")
    rc, _ = run(proj, tmp_path, capsys)
    assert rc == 2 and not rec.calls


def test_rejects_junction_like_reparse_point(proj, monkeypatch):
    class St:
        st_mode = 0o100644
        st_file_attributes = 0x400
    assert render._is_link(St())


def test_rejects_unknown_dir_ext_and_missing_index(rec, proj, tmp_path, capsys):
    (proj / "scripts").mkdir()
    assert run(proj, tmp_path, capsys)[0] == 2
    (proj / "scripts").rmdir()
    (proj / "run.cmd").write_text("x", encoding="utf-8")
    assert run(proj, tmp_path, capsys)[0] == 2
    (proj / "run.cmd").unlink()
    (proj / "index.html").unlink()
    assert run(proj, tmp_path, capsys)[0] == 2
    assert not rec.calls


def test_not_a_directory(rec, tmp_path, capsys):
    rc = render.main(["--project-dir", str(tmp_path / "nope"), "--out", str(tmp_path / "o")])
    assert rc == 2


def test_check_failure_is_code_2_and_no_render(rec, proj, tmp_path, capsys):
    rec.check_rc = 1
    rc, cap = run(proj, tmp_path, capsys)
    assert rc == 2 and len(rec.calls) == 1
    assert "check --strict" in last_json(cap.out)["error"]


def test_render_failure_is_code_1(rec, proj, tmp_path, capsys, monkeypatch):
    rec.render_rc = 3
    monkeypatch.setattr(render, "RETRY_SLEEP", 0)
    rc, _ = run(proj, tmp_path, capsys)
    assert rc == 1


def test_check_timeout_is_code_1(rec, proj, tmp_path, capsys, monkeypatch):
    def boom(argv, **kw):
        raise subprocess.TimeoutExpired(argv, 1)
    monkeypatch.setattr(render.subprocess, "run", boom)
    assert run(proj, tmp_path, capsys)[0] == 1


def test_argument_combinations(rec, proj, tmp_path, capsys):
    assert render.main(["--project-dir", str(proj), "--project", "news", "--out", str(tmp_path)]) == 2
    assert render.main(["--out", str(tmp_path)]) == 2
    assert render.main(["--project", "news", "--out", str(tmp_path)]) == 2
