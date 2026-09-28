"""uninstall.py — `video-studio uninstall`: gỡ đúng phần bộ cài đã đặt vào máy, GIỮ trạm.

    video-studio uninstall                 gỡ trên trạm đang phân giải + bản clone đang chạy
    video-studio uninstall --station DIR   gỡ trên một trạm khác
    video-studio uninstall --dry-run       chỉ in kế hoạch, không ghi gì

Thứ bị gỡ — chỉ những thứ `init` tạo ra và dựng lại được bằng `init`:

  * skill đã chép vào `<trạm>/.claude/skills/` và `<trạm>/.agents/skills/`, CHỈ bản còn khớp
    hash trong `skills-lock.json` (người dùng đã sửa thì giữ, báo tên), rồi chính file khoá;
  * `<repo>/studio.local.json` — lựa chọn chế độ + đường trạm (liên kết repo → trạm);
  * `<repo>/.env` CHỈ khi nó còn y hệt `.env.example` (chưa ai điền) — đã điền là cấu hình của
    người dùng, giữ;
  * hook `pre-commit` CHỈ khi đó là hook do `init` cài (nhận bằng dòng dấu) — hook của người
    khác không bao giờ bị đụng.

Thứ KHÔNG BAO GIỜ bị đụng: `projects/`, `demo/`, `templates/`, `station.json`, nháp, cache, cả
thư mục trạm (kể cả `<repo>/workspace/`), bản cài Python. Gỡ package là bước riêng
(`pip uninstall agent-video-studio`) mà lệnh này in ra ở cuối.

Không xoá thẳng: mọi thứ bị gỡ được DỜI vào `<trạm>/.video-studio/runs/<id>/prev/` kèm nhật ký,
nên lỡ tay vẫn lấy lại được bằng tay; cài lại thì chỉ cần `video-studio init`. Nhật ký mang
trạng thái `uninstalled` để `init --undo` không nhầm nó với một lần init.
"""
import argparse
import os
import shutil

from . import _env, contract, station as st_mod

HOOK_MARK = "# video-studio: chan commit du lieu tram"
STATUS = "uninstalled"


def _same_bytes(a, b):
    return os.path.isfile(a) and os.path.isfile(b) and st_mod._sha256(a) == st_mod._sha256(b)


def _is_our_hook(path):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return HOOK_MARK in f.read(2048)
    except OSError:
        return False


def _station_part(st):
    """-> (ops, kept, notes) cho phần TRẠM. Không ghi gì."""
    ops, kept, notes = [], [], []
    if not st:
        notes.append("chưa chọn trạm nào (không repo, không VIDEO_STATION) — bỏ qua phần trạm")
        return ops, kept, notes
    if not os.path.isdir(st):
        notes.append(f"không có trạm ở {st} — bỏ qua phần trạm")
        return ops, kept, notes
    lock_path = st_mod._p(st, st_mod.LOCK_FILE)
    lock, err = _env.read_json(lock_path)
    if not os.path.isfile(lock_path):
        notes.append("trạm không có skills-lock.json — không có skill nào do bộ cài chép")
        return ops, kept, notes
    if err or lock.get("source") != st_mod.LOCK_SOURCE:
        kept.append(f"{st_mod.LOCK_FILE} (do công cụ khác ghi — giữ, không gỡ skill nào)")
        return ops, kept, notes
    skills = lock.get("skills") or {}
    for tool in st_mod.SKILL_TOOLS:
        for name in sorted(skills):
            rel = f"{tool}/{name}"
            path = st_mod._p(st, rel)
            if not os.path.isdir(path):
                continue
            if st_mod._tree_hash(path) != (skills[name] or {}).get("sha256"):
                kept.append(f"{rel} (đã sửa sau khi cài — giữ)")
                continue
            ops.append({"op": "remove-skill", "path": rel})
    ops.append({"op": "remove-lock", "path": st_mod.LOCK_FILE})
    return ops, kept, notes


def _repo_part(repo):
    """-> (ops, kept) cho phần REPO. Không ghi gì."""
    ops, kept = [], []
    if not repo:
        return ops, kept
    local = os.path.join(repo, _env.LOCAL_CONFIG)
    if os.path.isfile(local):
        ops.append({"op": "remove-repo-file", "path": _env.LOCAL_CONFIG})
    env_file = os.path.join(repo, _env.ENV_FILE)
    if os.path.isfile(env_file):
        if _same_bytes(env_file, os.path.join(repo, _env.ENV_EXAMPLE)):
            ops.append({"op": "remove-repo-file", "path": _env.ENV_FILE})
        else:
            kept.append(".env (đã điền cấu hình — giữ)")
    hook = os.path.join(repo, ".git", "hooks", "pre-commit")
    if os.path.isfile(hook):
        if _is_our_hook(hook):
            ops.append({"op": "remove-repo-file", "path": ".git/hooks/pre-commit"})
        else:
            kept.append(".git/hooks/pre-commit (hook không do video-studio cài — giữ)")
    return ops, kept


def plan(station=None):
    """-> dict kế hoạch gỡ. Không ghi gì."""
    st = _env._expand(station) if station else _env.resolve_station()[0]
    repo = _env.existing_repo()
    s_ops, s_kept, notes = _station_part(st)
    r_ops, r_kept = _repo_part(repo)
    return {"station": st, "repo": repo, "station_ops": s_ops, "repo_ops": r_ops,
            "kept": s_kept + r_kept, "notes": notes}


def _rmdir_empty(st, rel):
    path = st_mod._p(st, rel)
    if os.path.isdir(path) and not os.listdir(path):
        os.rmdir(path)
        return True
    return False


def _execute(pl):
    """Thi hành kế hoạch. Mọi thứ bị gỡ được DỜI vào nhật ký, không xoá thẳng."""
    st, repo = pl["station"], pl["repo"]
    removed = []
    run = None
    if pl["station_ops"] or pl["repo_ops"]:
        if st and os.path.isdir(st):
            run = st_mod._Run(st)
    for op in pl["station_ops"]:
        b = run.backup(op["path"])
        run.record({"op": "move", "src": op["path"], "dst": b})
        removed.append(op["path"])
    if run:
        for tool in st_mod.SKILL_TOOLS:            # `.claude/skills` rồi `.claude`, nếu đã rỗng
            parts = tool.split("/")
            for i in range(len(parts), 0, -1):
                rel = "/".join(parts[:i])
                if _rmdir_empty(st, rel):
                    run.record({"op": "rmdir", "path": rel})
    for op in pl["repo_ops"]:
        src = os.path.join(repo, *op["path"].split("/"))
        if run:
            dst = os.path.join(run.dir, "prev-repo", *op["path"].split("/"))
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
            run.record({"op": "repo-remove", "path": op["path"],
                        "backup": os.path.relpath(dst, st).replace(os.sep, "/")})
        os.remove(src)
        removed.append(f"<repo>/{op['path']}")
    if run:
        run.finish(STATUS)
    return removed, (run.id if run else None)


def do_uninstall(station=None, dry_run=False):
    pl = plan(station)
    res = {"station": pl["station"], "repo": pl["repo"], "dry_run": bool(dry_run),
           "plan": [op["path"] for op in pl["station_ops"]] +
                   [f"<repo>/{op['path']}" for op in pl["repo_ops"]],
           "kept": pl["kept"], "notes": pl["notes"],
           "station_kept": True,
           "next": "pip uninstall agent-video-studio"}
    if not dry_run:
        res["removed"], res["run_id"] = _execute(pl)
    return res


def _print(res):
    log = contract.log
    tag = "(xem trước — chưa ghi gì) " if res["dry_run"] else ""
    log(f"[uninstall] {tag}trạm: {res['station'] or '(chưa chọn)'} · repo: {res['repo'] or '(không)'}")
    if not res["plan"]:
        log("[uninstall] không có gì do bộ cài đặt vào — không phải gỡ gì")
    for p in res["plan"]:
        log(("  • gỡ " if res["dry_run"] else "  - đã gỡ ") + p)
    for k in res["kept"]:
        log(f"  = giữ: {k}")
    for n in res["notes"]:
        log(f"  ! {n}")
    if res["station"]:
        log(f"[uninstall] trạm và mọi project GIỮ NGUYÊN ở {res['station']}")
    if not res["dry_run"] and res.get("run_id"):
        log(f"[uninstall] bản đã gỡ nằm trong nhật ký {st_mod.RUNS_DIR}/{res['run_id']}/ của trạm; "
            "cài lại: video-studio init")
    log(f"Bước cuối (tuỳ bạn): {res['next']}")


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="video-studio uninstall",
        description="Gỡ phần bộ cài đã đặt (skill đã chép, liên kết repo → trạm, .env chưa điền, "
                    "hook pre-commit của video-studio). GIỮ trạm, project và cấu hình đã điền.")
    ap.add_argument("--station", help="trạm khác trạm đang phân giải")
    ap.add_argument("--dry-run", action="store_true", help="chỉ in kế hoạch, không ghi")
    ap.add_argument("--json", action="store_true")
    args, code = contract.parse(ap, argv)
    if args is None:
        return code

    def fn(a):
        res = do_uninstall(a.station, dry_run=a.dry_run)
        _print(res)
        return res
    return contract.run(fn, args, args.json)
