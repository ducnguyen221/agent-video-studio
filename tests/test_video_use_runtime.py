"""Venv của video-use: máy có OpcOS đặt nó ngoài trạm, máy không có OpcOS giữ hành vi cũ.

Luật đích (hợp đồng `system/workshop/planning/contracts/runtime-resource-v1.json`, OpcOS commit
d5c62b76, khối vectors): `R = $OPCOS_RUNTIME` → `$OPCOS_ROOT/runtime` → (`~/OpcOS/paths.json` có
mặt thì `~/OpcOS/runtime`) → không có. Tài nguyên riêng nằm ở `R/<category>/<repoKey>/<resourceKey>`.

Mọi test dùng cây giả trong `tmp_path` và môi trường sạch (conftest xoá `OPCOS_*`, trỏ HOME giả):
không test nào tạo venv thật, gọi mạng hay đụng `~/OpcOS` thật.
"""
import json
import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

import pytest

from video_studio import _env, station

ROOT = Path(__file__).resolve().parent.parent
PS1 = ROOT / "scripts" / "install-video-use.ps1"
SH = ROOT / "scripts" / "install-video-use.sh"
IS_WIN = os.name == "nt"


def _posix(p):
    return Path(p).as_posix()


# ── bộ giải Python: bốn véc-tơ của hợp đồng ────────────────────────────────────────────

def _vec(environ, has_paths_json):
    return _env.runtime_resource(
        "venvs", "video-use", environ=environ, home="/h",
        isfile=lambda p: has_paths_json and _posix(p) == "/h/OpcOS/paths.json")


@pytest.mark.parametrize("name, environ, paths_json, want", [
    ("VT1", {"OPCOS_RUNTIME": "/r", "OPCOS_ROOT": "/o"}, True, "/r/venvs/agent-video-studio/video-use"),
    ("VT2", {"OPCOS_ROOT": "/o"}, False, "/o/runtime/venvs/agent-video-studio/video-use"),
    ("VT3", {}, True, "/h/OpcOS/runtime/venvs/agent-video-studio/video-use"),
    ("VT4", {}, False, None),
])
def test_vectors(name, environ, paths_json, want):
    got = _vec(environ, paths_json)
    assert (got if got is None else _posix(got)) == want, name


def test_blank_env_counts_as_unset():
    assert _vec({"OPCOS_RUNTIME": "  ", "OPCOS_ROOT": ""}, False) is None


def test_runtime_root_is_the_category_parent():
    r = _env.runtime_root(environ={"OPCOS_RUNTIME": "/r"}, home="/h", isfile=lambda p: False)
    assert _posix(r) == "/r"


@pytest.mark.parametrize("category, key", [
    ("", "video-use"), ("venvs", ""), ("venvs", "../x"), ("venvs", "a/b"), ("ve nvs", "k"),
    ("venvs", "a\\b"), ("venvs", ".."), ("../venvs", "k"),
])
def test_bad_keys_raise(category, key):
    with pytest.raises(ValueError):
        _env.runtime_resource(category, key, environ={"OPCOS_RUNTIME": "/r"}, home="/h")


def test_runtime_resource_reads_the_real_environment(tmp_path, monkeypatch):
    monkeypatch.setenv("OPCOS_RUNTIME", str(tmp_path / "rt"))
    assert Path(_env.runtime_resource("venvs", "video-use")) == (
        tmp_path / "rt" / "venvs" / "agent-video-studio" / "video-use")


def test_clean_env_does_not_see_the_real_opcos(monkeypatch):
    """conftest cô lập: máy dev có `~/OpcOS/paths.json` thật cũng không làm test đổi kết quả."""
    assert _env.runtime_resource("venvs", "video-use") is None


# ── tệp khai nhu cầu ───────────────────────────────────────────────────────────────────

def test_needs_file_schema():
    doc = json.loads((ROOT / "opcos-runtime.json").read_text(encoding="utf-8"))
    assert doc["schema"] == "opcos-runtime-needs/1"
    assert doc["repoKey"] == "agent-video-studio" == _env.RUNTIME_REPO_KEY
    (need,) = doc["needs"]
    assert (need["scope"], need["category"], need["key"]) == ("own", "venvs", "video-use")
    assert need["paths"] == {"dir_rel": 95, "file_rel": 149}
    assert "package" not in need                       # đến từ --source-dir lúc chạy
    inst = need["install"]
    assert not any(r.startswith("-e") for r in inst["requirements"])
    for rel in inst["requirements"] + inst["constraints"]["windows"]:
        assert (ROOT / rel).is_file(), rel
    req = (ROOT / inst["requirements"][0]).read_text(encoding="utf-8").split()
    assert req == ["faster-whisper"]
    lock = (ROOT / inst["constraints"]["windows"][0]).read_text(encoding="utf-8").splitlines()
    assert len(lock) >= 40 and lock == sorted(lock, key=str.lower)
    assert all("==" in ln and ln == ln.strip() for ln in lock)
    names = {ln.split("==")[0].lower() for ln in lock}
    assert "faster_whisper" in names and not names & {"video_use", "pip", "setuptools"}


# ── trạm: station.json ghi đường nào ───────────────────────────────────────────────────

def _venv_python(venv):
    rel = ("Scripts", "python.exe") if IS_WIN else ("bin", "python")
    return Path(venv).joinpath(*rel)


def _make_file(p):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("", encoding="utf-8")
    return p


@pytest.fixture
def st_with_clone(tmp_path):
    st = tmp_path / "st"
    (st / "video-use").mkdir(parents=True)
    return st


def test_station_info_absolute_python(st_with_clone, tmp_path, monkeypatch):
    rt = tmp_path / "rt"
    monkeypatch.setenv("OPCOS_RUNTIME", str(rt))
    py = _make_file(_venv_python(rt / "venvs" / "agent-video-studio" / "video-use"))
    old = _make_file(_venv_python(st_with_clone / "video-use" / ".venv"))   # venv cũ cũng có
    info = station._video_use_info(str(st_with_clone))
    assert info["dir"] == "video-use"
    assert os.path.isabs(info["python"]) and Path(info["python"]) == py
    assert old.exists()                                                      # không bao giờ xoá venv cũ


def test_station_info_falls_back_when_runtime_venv_missing(st_with_clone, tmp_path, monkeypatch):
    monkeypatch.setenv("OPCOS_RUNTIME", str(tmp_path / "rt"))                # có R nhưng chưa có venv
    _make_file(_venv_python(st_with_clone / "video-use" / ".venv"))
    info = station._video_use_info(str(st_with_clone))
    assert not os.path.isabs(info["python"]) and info["python"].startswith("video-use/.venv/")


def test_station_info_without_opcos_is_unchanged(st_with_clone):
    _make_file(_venv_python(st_with_clone / "video-use" / ".venv"))
    info = station._video_use_info(str(st_with_clone))
    rel = ".venv/Scripts/python.exe" if IS_WIN else ".venv/bin/python"
    assert info == {"dir": "video-use", "python": "video-use/" + rel}
    assert station._video_use_info(str(st_with_clone.parent / "none")) == {"dir": None, "python": None}


def test_station_info_keeps_existing(st_with_clone, tmp_path, monkeypatch):
    rt = tmp_path / "rt"
    monkeypatch.setenv("OPCOS_RUNTIME", str(rt))
    _make_file(_venv_python(rt / "venvs" / "agent-video-studio" / "video-use"))
    mine = {"dir": "video-use", "python": "my/own/python"}
    (st_with_clone / "station.json").write_text(json.dumps({"video_use": mine}), encoding="utf-8")
    data, _ = station._station_json(str(st_with_clone), "separate", "0.8.54", "projects")
    assert data["video_use"] == mine                   # giá trị người dùng đã sửa luôn thắng


# ── vỏ cài: -PrintPlan / -VenvOnly ──────────────────────────────────────────────────────

PS_EXE = shutil.which("pwsh") or shutil.which("powershell")
needs_ps = pytest.mark.skipif(PS_EXE is None, reason="không có pwsh/powershell trên PATH")


def _bash():
    exe = shutil.which("bash") or shutil.which("sh")
    if not exe:
        return None
    try:   # bash của WSL (System32) không thấy đường Windows: chỉ nhận bash đọc được thư mục thật
        r = subprocess.run([exe, "-c", 'cd "$1" && pwd', "_", _posix(ROOT)], capture_output=True,
                           timeout=30, stdin=subprocess.DEVNULL)
    except (OSError, subprocess.SubprocessError):
        return None
    return exe if r.returncode == 0 else None


BASH_EXE = _bash()
needs_sh = pytest.mark.skipif(BASH_EXE is None, reason="không có bash/sh dùng được")


def _env_for(tmp_path, **extra):
    env = dict(os.environ)
    for k in list(env):
        if k.startswith(("OPCOS_", "VIDEO_")):
            del env[k]
    home = tmp_path / "home"
    home.mkdir(exist_ok=True)
    drive, tail = os.path.splitdrive(str(home))
    env.update(HOME=str(home), USERPROFILE=str(home), HOMEDRIVE=drive, HOMEPATH=tail,
               VIDEO_STUDIO_REPO=str(tmp_path / "no-repo"),
               # Rào chống cài thật: pip không có chỉ mục, không cache; python giả chặn -m venv/-m pip.
               PIP_NO_INDEX="1", PIP_NO_CACHE_DIR="1", PIP_INDEX_URL="http://127.0.0.1:9/")
    env.update(extra)
    return env


def _py_marker(tmp_path):
    return tmp_path / "py-called.txt"


def _install_py_shim(env, kind):
    """VIDEO_STUDIO_PY -> python giả: `-m venv`/`-m pip` ghi tệp đánh dấu rồi exit 1; còn lại là python thật."""
    base = Path(env["HOME"]).parent
    marker = _py_marker(base)
    env["PY_MARKER"] = str(marker)
    real = sys.executable
    if kind == "cmd":
        shim = base / "pyshim.cmd"
        lines = ["@echo off",
                 'if "%~1"=="-m" if "%~2"=="venv" (echo called>"%PY_MARKER%"& exit /b 1)',
                 'if "%~1"=="-m" if "%~2"=="pip" (echo called>"%PY_MARKER%"& exit /b 1)',
                 f'"{real}" %*',
                 "exit /b %errorlevel%"]
        shim.write_bytes(("\r\n".join(lines) + "\r\n").encode("ascii"))
        env["VIDEO_STUDIO_PY"] = str(shim)
    else:
        shim = base / "pyshim"
        lines = ["#!/bin/sh",
                 'case "$1$2" in "-mvenv"|"-mpip") echo called > "$PY_MARKER"; exit 1;; esac',
                 f'exec "{_posix(real)}" "$@"']
        shim.write_bytes(("\n".join(lines) + "\n").encode("ascii"))
        shim.chmod(shim.stat().st_mode | stat.S_IEXEC)
        env["VIDEO_STUDIO_PY"] = _posix(shim)
    return env


def _assert_nothing_installed(tmp_path):
    """Không venv/pip thật nào chạy, và không rác (pip/, cache module PowerShell) lọt vào gốc repo."""
    assert not _py_marker(tmp_path).exists(), "python -m venv / -m pip đã bị gọi"
    assert not (ROOT / "pip").exists() and not (ROOT / "Microsoft").exists()


def _run_ps(args, env, timeout=120):
    # cwd = thư mục tạm: PowerShell ghi cache module vào thư mục hiện hành khi LOCALAPPDATA trống.
    argv = [PS_EXE, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
            "-File", str(PS1), *args]
    env = _install_py_shim(dict(env), "cmd" if IS_WIN else "sh")
    r = subprocess.run(argv, env=env, capture_output=True, text=True, timeout=timeout,
                       stdin=subprocess.DEVNULL, cwd=env["HOME"])
    _assert_nothing_installed(Path(env["HOME"]).parent)
    return r


def _run_sh(args, env, timeout=120):
    env = _install_py_shim(dict(env), "sh")
    r = subprocess.run([BASH_EXE, _posix(SH), *args], env=env, capture_output=True, text=True,
                       timeout=timeout, stdin=subprocess.DEVNULL, cwd=env["HOME"])
    _assert_nothing_installed(Path(env["HOME"]).parent)
    return r


def _plan(stdout):
    out = {}
    for ln in stdout.splitlines():
        if "=" in ln:
            k, _, v = ln.partition("=")
            out[k.strip()] = v.strip()
    return out


def _same(a, b):
    if IS_WIN and len(a) > 2 and a[0] == "/" and a[1].isalpha() and a[2] == "/":
        a = a[1].upper() + ":" + a[2:]               # dạng /c/... của Git Bash
    return os.path.normcase(os.path.normpath(a)) == os.path.normcase(os.path.normpath(str(b)))


RUNNERS = [pytest.param(_run_ps, ["-Station", "{st}", "-PrintPlan", "-VenvOnly"], marks=needs_ps, id="ps1"),
           pytest.param(_run_sh, ["--station", "{st}", "--print-plan", "--venv-only"], marks=needs_sh, id="sh")]


@pytest.mark.parametrize("runner, args", RUNNERS)
@pytest.mark.parametrize("name, envs, want", [
    ("VT1", {"OPCOS_RUNTIME": "{t}/r", "OPCOS_ROOT": "{t}/o"}, "{t}/r/venvs/agent-video-studio/video-use"),
    ("VT2", {"OPCOS_ROOT": "{t}/o"}, "{t}/o/runtime/venvs/agent-video-studio/video-use"),
])
def test_print_plan_runtime(tmp_path, runner, args, name, envs, want):
    st = tmp_path / "st"
    st.mkdir()
    env = _env_for(tmp_path, **{k: v.format(t=_posix(tmp_path)) for k, v in envs.items()})
    if name == "VT2":                                   # VT2: không có paths.json — chỉ OPCOS_ROOT
        assert not (tmp_path / "home" / "OpcOS" / "paths.json").exists()
    r = runner([a.format(st=st) for a in args], env)
    assert r.returncode == 0, r.stderr
    plan = _plan(r.stdout)
    assert _same(plan["venv"], want.format(t=_posix(tmp_path))), r.stdout
    assert plan["clone"] == "skip"
    assert _same(plan["station"], st)
    assert plan["installer"] in ("venv", "opcos-runtime")


@pytest.mark.parametrize("runner, args", RUNNERS)
def test_print_plan_vt3_uses_home_paths_json(tmp_path, runner, args):
    st = tmp_path / "st"
    st.mkdir()
    _make_file(tmp_path / "home" / "OpcOS" / "paths.json")
    r = runner([a.format(st=st) for a in args], _env_for(tmp_path))
    assert r.returncode == 0, r.stderr
    assert _same(_plan(r.stdout)["venv"],
                 tmp_path / "home" / "OpcOS" / "runtime" / "venvs" / "agent-video-studio" / "video-use")


@pytest.mark.parametrize("runner, args", RUNNERS)
def test_print_plan_no_opcos(tmp_path, runner, args):
    st = tmp_path / "st"
    st.mkdir()
    r = runner([a.format(st=st) for a in args], _env_for(tmp_path))     # VT4
    assert r.returncode == 0, r.stderr
    plan = _plan(r.stdout)
    assert _same(plan["venv"], st / "video-use" / ".venv"), r.stdout
    assert plan["installer"] == "venv"


@pytest.mark.parametrize("runner, args", RUNNERS)
def test_print_plan_clone_mode_without_venv_only(tmp_path, runner, args):
    st = tmp_path / "st"
    st.mkdir()
    flag = {"-VenvOnly": None, "--venv-only": None}
    args = [a.format(st=st) for a in args if a not in flag]
    r = runner(args, _env_for(tmp_path))
    assert r.returncode == 0, r.stderr
    assert _plan(r.stdout)["clone"] == "clone"                           # chưa có clone ⇒ sẽ clone
    (st / "video-use" / ".git").mkdir(parents=True)
    assert _plan(runner(args, _env_for(tmp_path)).stdout)["clone"] == "pull"


def _fake_git(tmp_path, marker):
    """PATH giả có `git` ghi tệp đánh dấu mỗi lần bị gọi."""
    bindir = tmp_path / "fakebin"
    bindir.mkdir()
    if IS_WIN:
        (bindir / "git.cmd").write_text('@echo called>"%GIT_MARKER%"\r\n@exit /b 0\r\n', encoding="ascii")
    else:
        g = bindir / "git"
        g.write_text('#!/bin/sh\necho called > "$GIT_MARKER"\n', encoding="ascii")
        g.chmod(g.stat().st_mode | stat.S_IEXEC)
    return bindir, {"GIT_MARKER": str(marker)}


def _fake_cli_tree(tmp_path, exit_code=0):
    """<cây>/runtime làm R; CLI giả ở R/../system/operations/runtime/. Ghi argv + liệt kê bản sao."""
    tree = tmp_path / "opcos"
    cli_dir = tree / "system" / "operations" / "runtime"
    cli_dir.mkdir(parents=True)
    (tree / "runtime").mkdir()
    ps = cli_dir / "opcos-runtime.ps1"
    ps.write_text(
        "$log = $env:FAKE_CLI_LOG\n"
        "$args | Set-Content -Path $log -Encoding ASCII\n"
        "foreach ($a in $args) { if ($a -like 'venvs/video-use=*') {\n"
        "  $src = $a.Substring('venvs/video-use='.Length)\n"
        "  Add-Content -Path $log -Value ('LISTING:' + ((Get-ChildItem -Force -Name $src) -join ',')) } }\n"
        f"exit {exit_code}\n", encoding="ascii")
    sh = cli_dir / "opcos-runtime.sh"
    sh.write_text(
        '#!/bin/sh\nprintf "%s\\n" "$@" > "$FAKE_CLI_LOG"\n'
        'for a in "$@"; do case "$a" in venvs/video-use=*) src="${a#venvs/video-use=}";\n'
        '  echo "LISTING:$(ls -A "$src" | tr "\\n" ",")" >> "$FAKE_CLI_LOG";; esac; done\n' + f"exit {exit_code}\n",
        encoding="ascii")
    sh.chmod(sh.stat().st_mode | stat.S_IEXEC)
    return tree


CLI_RUNNERS = [pytest.param(_run_ps, ["-Station", "{st}", "-VenvOnly"], marks=needs_ps, id="ps1"),
               pytest.param(_run_sh, ["--station", "{st}", "--venv-only"], marks=needs_sh, id="sh")]


@pytest.mark.parametrize("runner, args", CLI_RUNNERS)
def test_venv_only_never_runs_git(tmp_path, runner, args):
    """-VenvOnly: không git, không clone/pull; bản sao tạm không mang .git/.venv và bị xoá cuối."""
    st = tmp_path / "st"
    clone = st / "video-use"
    (clone / ".git").mkdir(parents=True)
    (clone / ".venv").mkdir()
    (clone / "pyproject.toml").write_text("[project]\nname='video-use'\n", encoding="utf-8")
    (clone / "src").mkdir()
    (clone / "src" / "mod.py").write_text("x = 1\n", encoding="utf-8")
    tree = _fake_cli_tree(tmp_path)
    marker, log = tmp_path / "git-called.txt", tmp_path / "cli.log"
    bindir, git_env = _fake_git(tmp_path, marker)
    env = _env_for(tmp_path, OPCOS_RUNTIME=str(tree / "runtime"), FAKE_CLI_LOG=str(log),
                   PATH=str(bindir) + os.pathsep + os.environ["PATH"], **git_env)
    r = runner([a.format(st=st) for a in args], env)
    assert r.returncode == 0, r.stdout + r.stderr
    assert not marker.exists(), "git đã bị gọi trong -VenvOnly"
    lines = log.read_text(encoding="ascii").splitlines()
    argv = [ln for ln in lines if not ln.startswith("LISTING:")]
    assert argv[0] == "ensure"
    assert _same(argv[argv.index("--repo-dir") + 1], ROOT)
    assert argv[argv.index("--only") + 1] == "venvs/video-use"
    src_arg = argv[argv.index("--source-dir") + 1]
    assert src_arg.startswith("venvs/video-use=")
    copy = src_arg.split("=", 1)[1]
    listing = next(ln for ln in lines if ln.startswith("LISTING:"))[len("LISTING:"):].strip(",").split(",")
    assert "pyproject.toml" in listing and "src" in listing
    assert ".git" not in listing and ".venv" not in listing
    assert not os.path.exists(copy), "bản sao tạm phải bị xoá"
    plan = _plan(r.stdout)                              # venv ở R ⇒ in python tuyệt đối + nhắc station.json
    assert os.path.isabs(plan["python"]) and "agent-video-studio" in plan["python"]
    assert "station.json" in r.stdout
    assert (clone / ".git").is_dir() and (clone / ".venv").is_dir()      # clone nguyên vẹn


@pytest.mark.parametrize("runner, args", CLI_RUNNERS)
def test_venv_only_cli_failure_cleans_copy(tmp_path, runner, args):
    """CLI trả mã lỗi ⇒ script thoát mã khác 0, bản sao tạm vẫn bị xoá, clone nguyên vẹn."""
    st = tmp_path / "st"
    clone = st / "video-use"
    (clone / ".git").mkdir(parents=True)
    (clone / "pyproject.toml").write_text("[project]\nname='video-use'\n", encoding="utf-8")
    tree = _fake_cli_tree(tmp_path, exit_code=1)
    log = tmp_path / "cli.log"
    env = _env_for(tmp_path, OPCOS_RUNTIME=str(tree / "runtime"), FAKE_CLI_LOG=str(log))
    r = runner([a.format(st=st) for a in args], env)
    assert r.returncode != 0
    lines = log.read_text(encoding="ascii").splitlines()
    src_arg = next(ln for ln in lines if ln.startswith("venvs/video-use="))
    assert not os.path.exists(src_arg.split("=", 1)[1]), "bản sao tạm phải bị xoá cả khi lỗi"
    assert (clone / ".git").is_dir() and (clone / "pyproject.toml").is_file()


@pytest.mark.parametrize("runner, args", CLI_RUNNERS)
def test_venv_only_without_clone_fails(tmp_path, runner, args):
    st = tmp_path / "st"
    st.mkdir()
    tree = _fake_cli_tree(tmp_path)
    env = _env_for(tmp_path, OPCOS_RUNTIME=str(tree / "runtime"), FAKE_CLI_LOG=str(tmp_path / "cli.log"))
    r = runner([a.format(st=st) for a in args], env)
    assert r.returncode != 0
    assert "video-use" in (r.stdout + r.stderr)
    assert not (tmp_path / "cli.log").exists()


def test_scripts_stay_portable():
    """.ps1 chỉ ASCII; không `??`/`&&` (Windows PowerShell 5.1)."""
    text = PS1.read_bytes().decode("utf-8-sig")
    assert all(ord(c) < 128 for c in text)
    assert "??" not in text and "&&" not in text
    assert "Resolve-VideoUseVenv" in text and "resolve_video_use_venv" in SH.read_text(encoding="utf-8")
