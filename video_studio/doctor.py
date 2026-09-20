"""doctor.py — `video-studio doctor`: kiểm máy + trạm đủ để dựng video chưa, thiếu thì chỉ bước cài.

    video-studio doctor                    # bảng người đọc (stderr) + tóm tắt
    video-studio doctor --json             # một dòng JSON cuối stdout cho bên gọi
    video-studio doctor --hf 0.8.51        # kiểm với một bản HyperFrames khác bản đang ghim
    video-studio doctor --check-updates    # hỏi npm bản mới nhất — CHỈ BÁO, không nâng gì
    video-studio doctor --offline          # không gọi npx/npm (không mạng, không tải)

Kiểm: python · node ≥ 22 · npx · `npx hyperframes@<bản> doctor` · Chromium của HyperFrames
(`~/.cache/hyperframes`) · ffmpeg + ffprobe · font Inter · trạm (`VIDEO_STATION`, tên cũ
`VIDEO_ROOT` bị nhắc đổi) · `station.json` · hai nguồn sự thật (F17) · repo giọng (tuỳ chọn,
cho narrate) · video-use (tuỳ chọn, cho edit).

Mã thoát: 0 dùng được (có thể kèm cảnh báo) · 2 bản HyperFrames không hợp lệ · 3 thiếu thứ bắt
buộc (node, npx, ffmpeg, trạm) — kèm hướng dẫn cài phần còn thiếu.
"""
import argparse
import importlib.util
import os
import re
import shutil
import subprocess
import sys

from . import API_VERSION, _env, contract

MIN_NODE = 22
# Chromium mà từng bản HyperFrames ghim (đọc từ mã nguồn upstream). Bản không có trong bảng:
# chỉ kiểm "có ít nhất một bản", để `hyperframes doctor` nói phần còn lại.
KNOWN_CHROMIUM = {"0.7.94": "152.0.7928.2", "0.8.51": "152.0.7977.30"}

HINT_NODE = ("cài Node ≥ 22 — Windows: `winget install OpenJS.NodeJS.LTS`; macOS: `brew install node`; "
             "hoặc nodejs.org. Không nằm trên PATH thì đặt NODE_DIR")
HINT_FFMPEG = ("cài ffmpeg — Windows: `winget install Gyan.FFmpeg`; macOS: `brew install ffmpeg`. "
               "Không nằm trên PATH thì đặt FFMPEG_DIR")
HINT_FONT = ("cài font Inter — macOS: `brew install --cask font-inter`; Windows: tải từ rsms.me/inter "
             "rồi Install; hoặc đặt VIDEO_FONT cho font khác")
INSTALL_HINT = ("Cài trạm video: Node ≥ 22 + ffmpeg → `pip install -e <repo agent-video-studio>` → "
                "`video-studio init` → `video-studio doctor`. Trạm có sẵn từ trước: "
                "`video-studio init --station <trạm> --migrate --dry-run`.")
CLOUD_MARKERS = ("onedrive", "google drive", "googledrive", "my drive", "icloud", "dropbox",
                 "mobile documents", "cloudstorage")


def _check(name, ok, detail="", level="error", hint=""):
    return {"name": name, "ok": bool(ok), "level": "ok" if ok else level,
            "detail": detail, "hint": "" if ok else hint}


def _skip(name, detail):
    return {"name": name, "ok": True, "level": "skip", "detail": detail, "hint": ""}


def _run(argv, timeout=60):
    """Chạy lệnh ngoài: argv là LIST, không shell, stdin đóng, có timeout."""
    return subprocess.run(argv, capture_output=True, text=True, encoding="utf-8", errors="replace",
                          stdin=subprocess.DEVNULL, timeout=timeout)


def _vtuple(v):
    return tuple(int(x) for x in re.findall(r"\d+", str(v))[:3])


def _major(v):
    t = _vtuple(v)
    return t[0] if t else None


# ── từng nhóm kiểm ─────────────────────────────────────────────────────────────────────

def node_checks(version, offline):
    out = []
    node = _env.node_exe()
    if not node:
        out.append(_check("node", False, "không thấy node", hint=HINT_NODE))
    else:
        try:
            r = _run([node, "--version"], timeout=30)
            v = (r.stdout or "").strip()
        except (OSError, subprocess.SubprocessError) as e:
            v = f"lỗi: {e}"
        maj = _major(v)
        out.append(_check("node", maj is not None and maj >= MIN_NODE, f"{node} {v}",
                          hint=f"HyperFrames cần Node ≥ {MIN_NODE} — {HINT_NODE}"))
    npx = _env.npx_exe()
    out.append(_check("npx", bool(npx), npx or "không thấy npx", hint=HINT_NODE))
    spec = _env.hyperframes_spec(version)
    if offline:
        out.append(_skip("hyperframes-doctor", "--offline: không gọi npx"))
    elif not npx:
        out.append(_skip("hyperframes-doctor", "thiếu npx"))
    else:
        try:
            r = _run([npx, "--yes", spec, "doctor"], timeout=300)
            ok, tail = r.returncode == 0, ((r.stderr or "") + (r.stdout or "")).strip()[-300:]
        except (OSError, subprocess.SubprocessError) as e:
            ok, tail = False, str(e)
        out.append(_check("hyperframes-doctor", ok, spec if ok else f"{spec}: {tail}", level="warn",
                          hint=f"đọc kết quả `npx --yes {spec} doctor` để biết thiếu gì"))
    return out


def chromium_check(version):
    cache = _env.hyperframes_cache()
    roots = [os.path.join(cache, "chrome", "chrome-headless-shell"),
             os.path.join(cache, "chrome-headless-shell")]
    found = sorted({n for r in roots if os.path.isdir(r) for n in os.listdir(r)
                    if os.path.isdir(os.path.join(r, n))})
    ensure = f"`npx --yes hyperframes@{version} browser ensure`"
    need = KNOWN_CHROMIUM.get(version)
    if not found:
        return _check("chromium", False, cache, level="warn",
                      hint=f"chưa có Chromium của HyperFrames — {ensure}")
    if need and not any(n.endswith(need) for n in found):
        return _check("chromium", False, ", ".join(found), level="warn",
                      hint=f"bản {version} cần Chromium {need} — {ensure}")
    return _check("chromium", True, ", ".join(found))


def _font_dirs():
    home = os.path.expanduser("~")
    dirs = [os.path.join(_env.hyperframes_cache(), "fonts")]
    if os.name == "nt":
        dirs += [os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts"),
                 os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "Windows", "Fonts")]
    elif sys.platform == "darwin":
        dirs += [os.path.join(home, "Library", "Fonts"), "/Library/Fonts", "/System/Library/Fonts"]
    else:
        dirs += [os.path.join(home, ".local", "share", "fonts"), os.path.join(home, ".fonts"),
                 "/usr/share/fonts", "/usr/local/share/fonts"]
    return dirs


def font_check():
    want = (_env.env("VIDEO_FONT") or "Inter").lower().replace(" ", "")
    for d in _font_dirs():
        if not os.path.isdir(d):
            continue
        for dp, dn, fn in os.walk(d):
            if dp.count(os.sep) - d.count(os.sep) >= 2:
                dn[:] = []                  # đủ sâu cho bố cục thư mục font thông dụng
            for n in dn + fn:
                if n.lower().replace(" ", "").startswith(want):
                    return _check("font", True, os.path.join(dp, n))
    return _check("font", False, f"không thấy font '{want}'", level="warn", hint=HINT_FONT)


def tool_checks():
    ff, fp = _env.ffmpeg_exe(), _env.ffprobe_exe()
    return [_check("ffmpeg", bool(ff), ff or "không thấy ffmpeg", hint=HINT_FFMPEG),
            _check("ffprobe", bool(fp), fp or "không thấy ffprobe", hint=HINT_FFMPEG)]


def station_checks(st, src):
    out = [_check("station", os.path.isdir(st), f"{st} ({src})",
                  hint="chưa có trạm video — `video-studio init` (hoặc đặt VIDEO_STATION)")]
    if _env.env("VIDEO_ROOT") and not _env.env("VIDEO_STATION"):
        out.append(_check("env-name", False, "VIDEO_ROOT", level="warn",
                          hint="tên biến cũ — đặt VIDEO_STATION=<gốc trạm> (VIDEO_ROOT vẫn đọc được)"))
    if os.path.isdir(st):
        sj = os.path.join(st, _env.STATION_FILE)
        info, err = _env.read_json(sj)
        if err:
            out.append(_check("station-json", False, err,
                              hint="sửa tay hoặc xoá station.json rồi `video-studio init`"))
        elif not os.path.isfile(sj):
            legacy = _env.has_marker(st)
            out.append(_check("station-json", False, sj, level="warn", hint=(
                f"trạm đời cũ chưa có station.json — xem kế hoạch: `video-studio init --station \"{st}\" "
                "--migrate --dry-run`, đọc kỹ rồi bỏ --dry-run" if legacy else
                f"`video-studio init --station \"{st}\"`")))
        elif _major(info.get("contract")) != _major(API_VERSION):
            out.append(_check("station-json", False, f"contract {info.get('contract')} ≠ {API_VERSION}",
                              level="warn", hint="trạm dựng bởi bản hợp đồng khác — kiểm lại rồi chạy init"))
        else:
            out.append(_check("station-json", True, f"{sj} (contract {info.get('contract')})"))
        vu = (info.get("video_use") or {}) if isinstance(info.get("video_use"), dict) else {}
        vdir = os.path.join(st, vu["dir"]) if vu.get("dir") else None
        vpy = os.path.join(st, *vu["python"].split("/")) if vu.get("python") else None
        out.append(_check("video-use", bool(vdir and os.path.isdir(vdir) and vpy and os.path.isfile(vpy)),
                          vdir or "(chưa khai trong station.json)", level="warn",
                          hint="tuỳ chọn — chỉ cần cho `video-studio edit` bằng bản vendored"))
    return out


def two_sources_check():
    repo = _env.repo_root()
    if not repo or not os.path.isdir(os.path.join(repo, _env.WORKSPACE)):
        return []
    ws = os.path.join(repo, _env.WORKSPACE)
    others = [n for n in ("VIDEO_STATION", "VIDEO_ROOT") if _env.env(n)]
    if _env.local_config(repo).get("mode") == "separate":
        others.append("studio.local.json=separate")
    if _env.has_marker(_env.default_station()):
        others.append("~/.video")
    out = [_check("two-sources", not others, f"{ws} + {', '.join(others)}" if others else ws,
                  hint="hai nguồn sự thật cho một repo: giữ MỘT trạm — gộp dữ liệu rồi xoá "
                       "workspace/ hoặc gỡ biến/trạm ngoài")]
    low = repo.lower()
    cloud = [m for m in CLOUD_MARKERS if m in low]
    out.append(_check("cloud-sync", not cloud, repo, level="warn",
                      hint="repo nằm trong thư mục đồng bộ đám mây — project và nháp sẽ lên cloud; "
                           "dời repo ra ngoài"))
    return out


IGNORE_MUST = ("workspace", ".env", "studio.local.json")


def embedded_guard_checks():
    """Chế độ `embedded` đặt trạm TRONG repo ⇒ kiểm hai lớp rào còn nguyên: `.gitignore` thật
    sự chặn, và hook `pre-commit` đã cài.

    Kiểm bằng `git check-ignore` chứ không bằng cách đọc `.gitignore`: một dòng `!` ở dưới có
    thể mở lại cả thư mục đã chặn phía trên, và chỉ git mới biết luật nào thắng.
    """
    repo = _env.repo_root()
    if not repo or not os.path.isdir(os.path.join(repo, _env.WORKSPACE)):
        return []
    if not os.path.isdir(os.path.join(repo, ".git")):
        return [_skip("gitignore", "repo chưa `git init` — chưa có gì để chặn")]
    git = shutil.which("git")
    if not git:
        return [_skip("gitignore", "không có git trên PATH")]
    leaked = []
    for rel in IGNORE_MUST:
        r = _run([git, "-C", repo, "check-ignore", "-q", "--no-index", rel], timeout=30)
        if r.returncode != 0:
            leaked.append(rel)
    out = [_check("gitignore", not leaked,
                  ("git KHÔNG chặn: " + ", ".join(leaked)) if leaked else
                  "git chặn " + ", ".join(IGNORE_MUST),
                  hint="chế độ embedded để dữ liệu trạm trong repo — khôi phục các dòng "
                       "workspace/, .env, studio.local.json trong .gitignore trước khi commit")]
    hook = os.path.join(repo, ".git", "hooks", "pre-commit")
    out.append(_check("pre-commit", os.path.isfile(hook), hook, level="warn",
                      hint="lớp rào thứ hai chưa có — chạy lại `video-studio init` để cài "
                           "(hook sẵn có không bao giờ bị đè)"))
    return out


def voice_check():
    ok = importlib.util.find_spec("voice_studio") is not None
    return _check("voice-studio", ok, "voice_studio importable" if ok else "chưa cài", level="warn",
                  hint="tuỳ chọn — chỉ cần cho lồng tiếng: `pip install -e <repo agent-voice-studio>` "
                       "vào CÙNG venv")


UPSTREAM_FILE = "upstream.json"
SKILLS_SOURCE = "hyperframes-skills"


def skills_check():
    """Đối chiếu `upstream.json` (bản đã ghim của từng skill distill) với cây `skills/` trên đĩa.

    Đây là cổng chống DRIFT, không phải cổng mạng: thêm một thư mục skill mà quên ghi nguồn, hay
    ghi nguồn cho một skill đã xoá, đều là sổ sách sai — và sổ sai thì `--check-updates` sau này
    so với một danh sách không có thật.
    """
    repo = _env.package_repo()
    path = os.path.join(repo, UPSTREAM_FILE) if repo else None
    if not path or not os.path.isfile(path):
        return _skip("skills-upstream", f"không thấy {UPSTREAM_FILE} (bản cài wheel)")
    data, err = _env.read_json(path)
    if err:
        return _check("skills-upstream", False, f"{UPSTREAM_FILE} hỏng: {err}", level="warn",
                      hint="sửa tay rồi chạy lại")
    src = (data.get("sources") or {}).get(SKILLS_SOURCE) or {}
    listed = set(src.get("skills") or {})
    root = os.path.join(repo, "skills", "hyperframes")
    on_disk = {n for n in (os.listdir(root) if os.path.isdir(root) else [])
               if os.path.isfile(os.path.join(root, n, "SKILL.md"))}
    ref = src.get("ref") or "?"
    missing, extra = sorted(listed - on_disk), sorted(on_disk - listed)
    if missing or extra:
        return _check("skills-upstream", False,
                      f"lệch sổ: thiếu trên đĩa {missing} · chưa ghi nguồn {extra}", level="warn",
                      hint=f"cập nhật {UPSTREAM_FILE} hoặc cây skills/hyperframes/ cho khớp")
    return _check("skills-upstream", True, f"{len(on_disk)} skill distill @ {ref}",
                  hint="")


def update_check(version, offline):
    """-> (check|None, updates dict)."""
    if offline:
        return _skip("hyperframes-update", "--offline: không hỏi npm"), {"pinned": version,
                                                                        "latest": None, "behind": None}
    npm = _env.npm_exe()
    if not npm:
        return _check("hyperframes-update", False, "không thấy npm", level="warn",
                      hint=HINT_NODE), {"pinned": version, "latest": None, "behind": None}
    try:
        r = _run([npm, "view", "hyperframes", "version"], timeout=60)
        latest = (r.stdout or "").strip().splitlines()[-1].strip() if r.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError, IndexError):
        latest = ""
    if not _vtuple(latest):
        return _check("hyperframes-update", False, "không đọc được bản mới nhất từ npm", level="warn",
                      hint="kiểm mạng / npm"), {"pinned": version, "latest": None, "behind": None}
    a, b = _vtuple(version), _vtuple(latest)
    behind = None
    if b > a:
        behind = "major" if b[0] != a[0] else "minor" if b[1] != a[1] else "patch"
    upd = {"pinned": version, "latest": latest, "behind": behind}
    # HyperFrames phát hành gần như mỗi ngày: lệch patch chỉ ghi nhận, lệch minor trở lên mới cảnh báo.
    ok = behind in (None, "patch")
    return _check("hyperframes-update", ok, f"ghim {version} · mới nhất {latest}", level="warn",
                  hint=f"có bản {latest} — nâng là việc CÓ CHỦ ĐÍCH: render hồi quy rồi mới đổi "
                       "HYPERFRAMES_VERSION / station.json (doctor không tự nâng)"), upd


# ── ráp lại ────────────────────────────────────────────────────────────────────────────

def run_checks(hf=None, offline=False, check_updates=False):
    st, src = _env.resolve_station()
    version = _env.check_version(hf, "--hf") if hf else _env.hyperframes_version()
    checks = [_check("python", sys.version_info >= (3, 10), sys.version.split()[0],
                     hint="cần Python ≥ 3.10")]
    checks += node_checks(version, offline)
    checks.append(chromium_check(version))
    checks += tool_checks()
    checks.append(font_check())
    checks += station_checks(st, src)
    checks += two_sources_check()
    checks += embedded_guard_checks()
    checks.append(voice_check())
    checks.append(skills_check())
    updates = None
    if check_updates:
        c, updates = update_check(version, offline)
        checks.append(c)
    return st, version, checks, updates


class _DoctorFailed(contract.StationMissing):
    def __init__(self, result):
        super().__init__("trạm video chưa đủ: " + ", ".join(result["errors"]))
        self.result = result


def doctor(args):
    st, version, checks, updates = run_checks(args.hf, args.offline, args.check_updates)
    for c in checks:
        mark = {"ok": "OK  ", "warn": "WARN", "error": "LỖI ", "skip": "BỎ  "}[c["level"]]
        line = f"[{mark}] {c['name']:<18} {c['detail']}"
        if c["hint"]:
            line += f"\n         → {c['hint']}"
        contract.log(line)
    result = {"video_studio": API_VERSION, "station": st, "hyperframes": version, "checks": checks,
              "errors": [c["name"] for c in checks if c["level"] == "error"],
              "warnings": [c["name"] for c in checks if c["level"] == "warn"]}
    if updates is not None:
        result["updates"] = updates
    if result["errors"]:
        contract.log("\n" + INSTALL_HINT)
        raise _DoctorFailed(result)
    return result


def build_parser(prog="video-studio doctor"):
    ap = argparse.ArgumentParser(prog=prog, description="Kiểm máy và trạm video.")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--hf", metavar="VER", help="kiểm với bản HyperFrames này (x.y.z)")
    ap.add_argument("--check-updates", action="store_true",
                    help="hỏi npm bản HyperFrames mới nhất — chỉ báo, không nâng")
    ap.add_argument("--offline", action="store_true", help="không gọi npx/npm")
    return ap


def main(argv=None):
    args, code = contract.parse(build_parser(), argv)
    if args is None:
        return code
    try:
        result = doctor(args)
    except _DoctorFailed as e:
        if args.json:
            contract.emit({"ok": False, "code": contract.STATION_MISSING, "error": str(e), **e.result})
        return contract.STATION_MISSING
    except contract.VideoStudioError as e:
        contract.log(f"[video-studio] LỖI ({e.code}): {e}")
        if args.json:
            contract.emit({"ok": False, "code": e.code, "error": str(e)})
        return e.code
    if args.json:
        contract.emit({"ok": True, **result})
    return contract.OK


if __name__ == "__main__":
    sys.exit(main())
