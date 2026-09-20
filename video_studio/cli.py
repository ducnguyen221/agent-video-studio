"""cli.py — lệnh `video-studio` (và `python -m video_studio`): một cửa cho mọi công cụ của trạm video.

Mỗi lệnh con nằm trong module riêng và chỉ được import khi được gọi — `video-studio --help`
chạy được trên máy chưa có Node, ffmpeg hay repo giọng. Tham số sau tên lệnh chuyển nguyên cho
lệnh con. Lệnh chưa có trong bản này trả mã 2 kèm lời báo, không giả vờ chạy.
"""
import importlib
import sys
import traceback

from . import API_VERSION, __version__, contract

# tên lệnh -> (module[:hàm] hoặc None nếu chưa có, mô tả một dòng)
COMMANDS = {
    "init":    ("video_studio.station:init_main",
                "dựng trạm (embedded | separate) + station.json; --migrate nhận trạm cũ; --undo"),
    "doctor":  ("video_studio.doctor", "kiểm node, HyperFrames, Chromium, ffmpeg, font, trạm"),
    "render":  ("video_studio.render",
                "spec JSON → video theo template (news | news-weekly | topstory | repo-today)"),
    "edit":    ("video_studio.edit", "chỉnh footage thật theo transcript"),
    "preview": ("video_studio.preview", "xem trước một project HyperFrames"),
    "narrate": ("video_studio.narrate", "video câm + lời dẫn → MP4 có giọng (qua voice-studio)"),
    "export":  ("video_studio.station:export_main",
                "đóng gói trạm (hoặc --personal: tài sản project) để chuyển máy"),
    "import":  ("video_studio.station:import_main", "bung gói export vào trạm (mặc định không đè)"),
    "backup":  ("video_studio.station:backup_main", "zip cả trạm (không nháp, không cache)"),
    "migrate": ("video_studio.station:migrate_main",
                "chuyển trạm embedded ra ngoài repo (--to separate)"),
    "update":  ("video_studio.station:update_main", "cập nhật repo (git pull --ff-only)"),
}


def _console_utf8():
    # Console Windows mặc định cp1252 sẽ sập khi in tiếng Việt.
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8")
        except Exception:
            pass


def usage():
    lines = [f"video-studio {__version__} (hợp đồng API {API_VERSION})", "",
             "Cách dùng: video-studio <lệnh> [tham số…]   ·   video-studio <lệnh> --help", "",
             "Lệnh:"]
    for name, (target, desc) in COMMANDS.items():
        lines.append(f"  {name:<9} {desc}" + ("" if target else "  [chưa có trong bản này]"))
    lines += ["", "Mã thoát chung: 0 ok · 1 lỗi engine/render · 2 gọi/cấu hình sai · "
                  "3 trạm/công cụ chưa cài."]
    return "\n".join(lines)


def _call(target, argv):
    """Nạp module của lệnh rồi gọi `main(argv)`.

    `import_module` chạy TRƯỚC `contract.run` của lệnh, nên một module hỏng (thiếu phụ thuộc
    tuỳ chọn, lỗi cú pháp sau một lần sửa) cho traceback trần — kể cả khi người gọi xin
    `--json`. Bên gọi theo `docs/CONTRACT.md` §2 đọc dòng cuối stdout thì vỡ. Nên lớp nạp
    cũng phải nằm trong hợp đồng.
    """
    module, _, func = target.partition(":")
    try:
        mod = importlib.import_module(module)
        entry = getattr(mod, func or "main")
    except Exception as exc:    # noqa: BLE001 — biên của CLI: nạp hỏng cũng phải thành mã + JSON
        code = contract.classify(exc)
        msg = f"không nạp được lệnh '{module}': {exc.__class__.__name__}: {exc}"
        contract.log(f"[video-studio] LỖI ({code}): {msg}")
        if code == contract.ENGINE_ERROR:
            contract.log(traceback.format_exc().rstrip())
        if "--json" in argv:
            contract.emit({"ok": False, "code": code, "error": msg})
        return code
    rc = entry(argv)
    return contract.OK if rc is None else int(rc)


def main(argv=None):
    _console_utf8()
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help", "help"):
        print(usage())
        return contract.OK
    if argv[0] in ("-V", "--version"):
        print(f"video-studio {__version__} (API {API_VERSION})")
        return contract.OK
    cmd, rest = argv[0], argv[1:]
    if cmd not in COMMANDS:
        contract.log(f"lệnh lạ: '{cmd}'\n\n{usage()}")
        return contract.CONTRACT_ERROR
    target = COMMANDS[cmd][0]
    if target is None:
        msg = f"lệnh '{cmd}' chưa có trong video-studio {__version__}"
        contract.log(f"[video-studio] {msg}")
        if "--json" in rest:
            contract.emit({"ok": False, "code": contract.CONTRACT_ERROR, "error": msg})
        return contract.CONTRACT_ERROR
    return _call(target, rest)


if __name__ == "__main__":
    sys.exit(main())
