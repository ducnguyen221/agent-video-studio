"""Nhóm lệnh `video-studio reference`: đọc video mẫu thành bằng chứng và giữ hồ sơ quyền cho bản chuyển thể.

Ý tưởng tham khảo hypit (idea_reference), mã tự viết. Lõi chỉ thư viện chuẩn; `gate.py` thuần
(không tiến trình con, không mạng).

    video-studio reference init --name demo [--url U | --file F]     # dựng project + provenance.json
    video-studio reference frames --input V --at 1,5.5 --out DIR     # khung có PTS thật
    video-studio reference tiles --input V --every 2 --out DIR       # lưới khung
    video-studio reference transcribe --input V --project P          # phụ đề gốc, rồi ASR tại máy
    video-studio reference fetch --url U --allow-url U --project P   # tải có cổng (mặc định chỉ in kế hoạch)
    video-studio reference audit --project P                         # kiểm tài sản với hồ sơ
"""
import argparse
import datetime
import json
import os
import shutil

from .. import _env, _paths, contract
from ..contract import ContractError
from . import gate, media, subs

ACTIONS = ("init", "frames", "tiles", "transcribe", "fetch", "audit", "lyric-audit")

TEMPLATE_FILES = ("reference-map.md", "brief.md", "treatment.md")
PROJECT_DIRS = ("source", os.path.join("evidence", "frames"), os.path.join("evidence", "tiles"),
                "transcripts", "assets")

__all__ = ["ACTIONS", "build_parser", "do_reference", "main"]


def _marks(text):
    try:
        return [float(p) for p in text.split(",") if p.strip()]
    except ValueError:
        raise ContractError(f"--at phải là danh sách số giây cách nhau bằng dấu phẩy, nhận {text!r}") from None


def build_parser(prog="video-studio reference"):
    ap = argparse.ArgumentParser(
        prog=prog,
        description="Video mẫu → khung có PTS thật, lưới khung, transcript, hồ sơ quyền và kiểm tài sản. "
                    "Tải (`fetch`) có cổng: mặc định chỉ in kế hoạch.")
    sub = ap.add_subparsers(dest="action", required=True, metavar="{" + ",".join(ACTIONS) + "}")
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--json", action="store_true", help="dòng cuối stdout là một object JSON")

    p = sub.add_parser("init", parents=[common], help="dựng project tham chiếu + provenance.json")
    p.add_argument("--name", required=True, help="tên project (tên trần, không dấu ngăn thư mục)")
    p.add_argument("--dir", help="thư mục gốc chứa project (mặc định <trạm>/reference)")
    p.add_argument("--url", help="URL video mẫu (chỉ ghi vào hồ sơ, không tải)")
    p.add_argument("--file", help="tệp video mẫu có sẵn (ghi đường + sha256, không chép)")

    p = sub.add_parser(
        "frames", parents=[common],
        help="trích khung tại các mốc giây",
        description="Trích khung tại các mốc giây (tính từ đầu stream video). Lỗi giữa chừng ở mốc "
                    "thứ k để lại k-1 ảnh và không có frames.json; lượt sau không --force sẽ báo "
                    "«đã có» — dọn ảnh cũ hoặc thêm --force.")
    p.add_argument("--input", required=True, help="video")
    p.add_argument("--at", required=True, help="mốc giây, cách nhau bằng dấu phẩy (tối đa 60)")
    p.add_argument("--out", required=True, help="thư mục nhận ảnh + frames.json")
    p.add_argument("--force", action="store_true", help="ghi đè ảnh đã có")

    p = sub.add_parser("tiles", parents=[common], help="lưới khung (contact sheet)")
    p.add_argument("--input", required=True, help="video")
    p.add_argument("--every", required=True, type=float, help="một ô mỗi bao nhiêu giây (> 0)")
    p.add_argument("--out", required=True, help="thư mục nhận tiles_<nnn>.png + tiles.json")
    p.add_argument("--cols", type=int, default=4)
    p.add_argument("--rows", type=int, default=4)
    p.add_argument("--width", type=int, default=320, help="bề rộng mỗi ô (px)")
    p.add_argument("--label", action="store_true", help="in thời điểm lên ô (cần drawtext)")
    p.add_argument("--force", action="store_true", help="ghi đè lưới đã có")

    p = sub.add_parser("transcribe", parents=[common],
                       help="transcript từ phụ đề gốc, không có thì bóc lời tại máy")
    p.add_argument("--input", required=True, help="video")
    p.add_argument("--project", required=True, help="thư mục project (ghi transcripts/<stem>.json)")
    p.add_argument("--subs", help="tệp phụ đề .srt/.vtt đưa tay")
    p.add_argument("--language", default="vi", help="`auto` hoặc mã ngôn ngữ (mặc định vi)")
    p.add_argument("--force", action="store_true", help="ghi đè transcript đã có")

    p = sub.add_parser("fetch", parents=[common], help="tải video mẫu có cổng (mặc định chỉ in kế hoạch)")
    p.add_argument("--url", required=True, help="URL cần tải")
    p.add_argument("--allow-url", help="lặp lại đúng URL — xác nhận phép đích danh")
    p.add_argument("--project", required=True, help="thư mục project")
    p.add_argument("--go", action="store_true", help="tải thật (không có cờ này chỉ in kế hoạch)")
    p.add_argument("--max-mb", type=int, default=500, help="trần dung lượng (MB)")
    p.add_argument("--sub-langs", default="vi,en", help="ngôn ngữ phụ đề, cách nhau bằng dấu phẩy")

    p = sub.add_parser("audit", parents=[common], help="kiểm thư mục tài sản với hồ sơ")
    p.add_argument("--project", required=True, help="thư mục project")
    p.add_argument("--assets", help="thư mục tài sản (mặc định <project>/assets)")

    p = sub.add_parser("lyric-audit", parents=[common], help="kiểm tài sản lyric khai báo; không kiểm runtime")
    p.add_argument("--project", required=True, help="thư mục project tham chiếu")
    p.add_argument("--manifest", required=True, help="JSON khai audio và assets")
    return ap


# ── init ────────────────────────────────────────────────────────────────────────────────

def _render(template, project, today):
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates", template)
    with open(path, encoding="utf-8") as f:
        text = f.read()
    return text.replace("{{project}}", project).replace("{{date}}", today)


def _init(args):
    root = os.path.abspath(args.dir) if args.dir else os.path.join(_env.station_dir(), "reference")
    name = _paths.plain_name(args.name, "--name")
    project = os.path.join(root, name)
    if os.path.lexists(project):
        raise ContractError(f"project {project} đã có; chọn tên khác (init không ghi đè)")
    if os.path.exists(root) and not os.path.isdir(root):
        raise ContractError(f"--dir không phải thư mục: {root}" if args.dir
                            else f"thư mục gốc project không phải thư mục: {root}")
    local, digest = None, None
    if args.file:
        if not os.path.isfile(args.file):
            raise ContractError(f"--file không phải tệp: {args.file}")
        try:
            local, digest = os.path.abspath(args.file), gate.sha256_file(args.file)
        except OSError as exc:
            raise ContractError(f"không đọc được --file {args.file}: {exc}") from None
    today = datetime.date.today().isoformat()
    prov = gate.new_provenance(name, args.url, local, digest, today)   # check_url ném trước khi ghi gì

    rendered = [(t, _render(t, name, today)) for t in TEMPLATE_FILES]    # thiếu mẫu ⇒ lỗi trước khi tạo gì
    created = False
    try:
        os.makedirs(root, exist_ok=True)
        os.mkdir(project)
        created = True
        for d in PROJECT_DIRS:
            os.makedirs(os.path.join(project, d))
        for t, text in rendered:
            with open(os.path.join(project, t), "w", encoding="utf-8", newline="\n") as f:
                f.write(text)
        gate.save_provenance(project, prov)
    except FileExistsError as exc:
        if created:     # đua: tiến trình khác chen vào giữa `mkdir` và `makedirs`
            shutil.rmtree(project, ignore_errors=True)
            raise ContractError(f"không tạo được project {project}: {exc}") from None
        raise ContractError(f"project {project} đã có; chọn tên khác (init không ghi đè)") from None
    except OSError as exc:       # quyền, đĩa đầy, tên không hợp lệ: gọi sai/môi trường ⇒ mã 2
        if created:
            shutil.rmtree(project, ignore_errors=True)
        raise ContractError(f"không tạo được project {project}: {exc}") from None
    except BaseException:
        if created:
            shutil.rmtree(project, ignore_errors=True)       # không để project nửa vời
        raise
    return {"project": project,
            "files": [gate.PROVENANCE_FILE, *TEMPLATE_FILES],
            "rights_status": prov["rights_status"],
            "next": "Có tệp mẫu hợp lệ thì chạy `reference transcribe` rồi `reference tiles`; chưa có phép "
                    "tải thì giữ rights_pending và chỉ phân tích tệp của người dùng."}


# ── dispatcher ──────────────────────────────────────────────────────────────────────────

def do_reference(args):
    action = args.action
    if action == "init":
        return _init(args)
    if action == "frames":
        out = os.path.abspath(args.out)
        frames = media.extract_frames(args.input, out, _marks(args.at), force=args.force)
        return {"out": out, "frames": frames}
    if action == "tiles":
        out = os.path.abspath(args.out)
        sheets = media.contact_sheets(args.input, out, args.every, cols=args.cols, rows=args.rows,
                                      width=args.width, label=args.label, force=args.force)
        return {"out": out, **sheets}
    if action == "transcribe":
        return subs.transcribe(args.input, args.project, subs=args.subs, language=args.language,
                               force=args.force)
    if action == "audit":
        return gate.audit_assets(args.project, args.assets)
    if action == "lyric-audit":
        from . import lyric_guard
        try:
            with open(args.manifest, encoding="utf-8") as stream:
                manifest = json.load(stream)
        except (OSError, ValueError) as exc:
            raise ContractError(f"không đọc được manifest: {exc}") from None
        snapshot = lyric_guard.prepare(args.project, manifest)
        return {"coverage": "declared_only", "snapshot": snapshot}
    if action == "fetch":
        from . import fetch                      # nhập lười để lõi không cần yt-dlp
        fetch.check_limits(args.max_mb, args.sub_langs)
        project = os.path.abspath(args.project)
        url, _prov = fetch.authorize(args.url, args.allow_url, project)   # cổng 1→5, đúng thứ tự
        if args.go:                              # cổng 6–7 nằm trong plan_fetch / do_fetch
            return fetch.do_fetch(url, project, args.max_mb, args.sub_langs)
        return fetch.plan_fetch(url, project)
    raise ContractError(f"hành động lạ: {action}")


def _audit_main(args):
    """`audit`: phát hiện ⇒ mã 2, mỗi phát hiện một dòng stderr, JSON lỗi mang thêm `findings`."""
    try:
        result = do_reference(args)
    except (Exception, KeyboardInterrupt) as exc:   # noqa: BLE001 - để contract.run đổi thành mã
        def fail(_args):
            raise exc
        return contract.run(fail, args, args.json)
    if not result["findings"]:
        return contract.run(lambda _a: {"checked": result["checked"]}, args, args.json)
    for f in result["findings"]:
        contract.log(f"[reference] {f['path']}: {f['problem']}")
    msg = f"{len(result['findings'])} phát hiện"
    contract.log(f"[video-studio] LỖI ({contract.CONTRACT_ERROR}): {msg}")
    if args.json:
        contract.emit({"ok": False, "code": contract.CONTRACT_ERROR, "error": msg,
                       "findings": result["findings"]})
    return contract.CONTRACT_ERROR


def main(argv=None):
    args, code = contract.parse(build_parser(), argv)
    if args is None:
        return code
    if args.action == "audit":
        return _audit_main(args)
    return contract.run(do_reference, args, args.json)


if __name__ == "__main__":
    import sys
    sys.exit(main())
