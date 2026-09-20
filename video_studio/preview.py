"""preview.py — `video-studio preview`: mở studio xem trước của HyperFrames cho một project.

    video-studio preview                     # project mặc định của trạm (demo)
    video-studio preview --project news      # tên project trong trạm
    video-studio preview --project ./work    # hoặc một thư mục project bất kỳ
    video-studio preview --dry-run --json    # chỉ in lệnh sẽ chạy, không gọi npx

Thay cho `preview.ps1` đời cũ. Ba thứ đổi:

* **Không ghim `C:\\Program Files\\nodejs` vào PATH.** node/ffmpeg đến từ `_env` (`NODE_DIR`,
  `FFMPEG_DIR`, rồi PATH) nên chạy được trên máy khác và trên macOS.
* **Không nhận bản trôi `latest`.** Bản engine là bản ghim của trạm: xem trước và render thật
  phải là CÙNG một bản, nếu không thì thứ soi trên trình duyệt không phải thứ sẽ ra video.
* **Project mặc định không đoán theo tên riêng.** Bản cũ ưu tiên một project của một dự án cụ
  thể; ở đây mặc định là seed `demo/` của trạm, và không có thì nói ra chứ không đoán tiếp.

Lệnh này chạy **cho tới khi người dùng Ctrl+C** — đừng gọi nó trong lịch chạy tự động.
"""
import argparse
import os
import subprocess

from . import contract, narrate as narrate_mod, projects, render
from .contract import StationMissing

DEFAULT_PROJECT = projects.SEED_PROJECT

__all__ = ["resolve_project", "preview_argv", "do_preview", "main"]


def resolve_project(name=None):
    if name:
        return narrate_mod.resolve_project(name)
    proj = projects.project_dir(DEFAULT_PROJECT)
    if not os.path.isdir(proj):
        raise StationMissing(
            f"trạm chưa có project mặc định {DEFAULT_PROJECT!r} ({proj}) — chạy "
            "`video-studio init` để dựng seed, hoặc truyền --project <tên|thư mục>")
    return proj


def preview_argv(extra=(), version=None):
    """argv list gọi studio xem trước (không bao giờ là một chuỗi lệnh, không bao giờ qua shell)."""
    return render.hyperframes_argv("preview", *extra, version=version)


def do_preview(args):
    proj = resolve_project(args.project)
    extra = list(args.extra or [])
    if args.port:
        extra = ["--port", str(args.port)] + extra
    argv = preview_argv(extra)
    res = {"project": proj, "argv": argv, "dry_run": bool(args.dry_run)}
    if args.dry_run:
        return res
    contract.log(f"[preview] {proj} — Ctrl+C để dừng")
    try:
        code = subprocess.run(argv, cwd=proj, env=render.render_env()).returncode
    except KeyboardInterrupt:
        contract.log("[preview] đã dừng theo yêu cầu")
        code = 0
    if code:
        raise contract.EngineError(
            f"studio xem trước thoát với mã {code} — chạy `video-studio doctor --hf` để kiểm engine")
    return {**res, "code": code}


def build_parser(prog="video-studio preview"):
    ap = argparse.ArgumentParser(
        prog=prog, description="Mở studio xem trước của HyperFrames cho một project (chạy tới "
                               "khi Ctrl+C).")
    ap.add_argument("--project", help="tên project trong trạm hoặc đường dẫn thư mục project")
    ap.add_argument("--port", type=int, help="cổng cho studio (chuyển thẳng cho HyperFrames)")
    ap.add_argument("--dry-run", action="store_true", help="chỉ in lệnh sẽ chạy")
    ap.add_argument("--json", action="store_true", help="in một dòng JSON kết quả ra stdout")
    ap.add_argument("extra", nargs="*", help="tham số thêm chuyển thẳng cho HyperFrames")
    return ap


def main(argv=None):
    args, code = contract.parse(build_parser(), argv)
    if args is None:
        return code
    return contract.run(do_preview, args, args.json)


if __name__ == "__main__":
    import sys
    sys.exit(main())
