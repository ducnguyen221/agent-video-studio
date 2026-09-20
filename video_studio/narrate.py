"""narrate.py — `video-studio narrate`: video câm + lời dẫn → MP4 có giọng.

    video-studio narrate --video silent.mp4 --text "Xin chào…" --out final.mp4
    video-studio narrate --project demo --file loi-dan.txt --out final.mp4 --profile <tên>
    video-studio narrate --video in.mp4 --file loi.txt --out final.mp4 --mode shortest --bgm lofi

Thay cho `render_and_narrate.ps1` đời cũ. Bốn thứ đổi, mỗi thứ là một lần đã trả giá:

1. **`--project` render rồi lồng tiếng trong MỘT lệnh** — giữ đúng tiện ích của script cũ,
   nhưng bản câm trung gian nằm trong `<trạm>/scratch/` (script cũ ghi cạnh file ra, và khi
   lệnh hỏng giữa chừng thì `_silent_render.mp4` nằm lại trong thư mục giao cho người khác).
   `--keep-silent` để giữ lại khi cần soi.
2. **Không còn đường máy cứng.** Script cũ ghim đường tuyệt đối tới python của trạm giọng, tới
   thư mục cài Node, và một bản HyperFrames trôi theo `latest`: chạy được trên đúng một máy, và
   nâng bản sau lưng lịch chạy. Ở đây engine giọng là `voice_studio` trong CÙNG venv,
   node/ffmpeg qua `_env`, bản HyperFrames là bản ghim.
3. **Giọng đi qua profile, không qua `--instruct`.** `instruct` bốc một giọng khác mỗi câu —
   dùng để THỬ thì được, để dựng cả video thì không. Mặc định là profile của trạm giọng.
4. **Hợp đồng chung**: mã thoát 0/1/2/3 và một dòng JSON cuối stdout với `--json`.
"""
import argparse
import os
import time

from . import _env, contract, projects, render, voice
from .contract import ContractError, StationMissing

MODES = ("fit", "shortest")
SILENT_SUFFIX = ".__silent.mp4"

__all__ = ["resolve_project", "do_narrate", "main"]


def resolve_project(name):
    """`--project`: một đường dẫn có thật, hoặc tên project trong trạm. -> thư mục project."""
    name = (name or "").strip()
    if not name:
        raise ContractError("--project rỗng")
    if os.path.isdir(name):
        return os.path.abspath(name)
    if os.path.sep in name or "/" in name:
        raise StationMissing(f"không có thư mục project: {name}")
    proj = projects.project_dir(name)
    if not os.path.isdir(proj):
        raise StationMissing(
            f"trạm chưa có project {name!r} ({proj}) — dựng trạm bằng "
            f"`video-studio init --station \"{_env.station_dir()}\"`, hoặc truyền --project "
            "<đường dẫn thư mục project>")
    return proj


def _silent_path(out):
    """Chỗ để bản render câm: `<trạm>/scratch/narrate/…` nếu có trạm, không thì cạnh file ra."""
    base = os.path.basename(out) + SILENT_SUFFIX
    try:
        return projects.scratch_file("narrate", base)
    except OSError:
        return os.path.join(os.path.dirname(os.path.abspath(out)) or ".", base)


def do_narrate(args):
    t0 = time.time()
    out = os.path.abspath(args.out)
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    silent, rendered = args.video, None
    timings = {}

    if args.project:
        proj = resolve_project(args.project)
        silent = rendered = _silent_path(out)
        t = time.time()
        render.render_project(proj, silent, label="narrate")
        timings["render"] = round(time.time() - t, 2)
    if not silent:
        raise ContractError("cần --video <file câm> hoặc --project <project HyperFrames>")
    if not os.path.isfile(silent):
        raise ContractError(f"không thấy video: {silent}")

    try:
        res = voice.narrate(silent, out, text=args.text, file=args.file, profile=args.profile,
                            instruct=args.instruct, lang=args.lang, speed=args.speed,
                            seed=args.seed, normalize=args.normalize, mode=args.mode,
                            bgm=args.bgm, bgm_volume=args.bgm_volume)
    finally:
        # Bản câm trung gian là của lệnh này, không phải sản phẩm: dọn kể cả khi lồng tiếng hỏng.
        if rendered and not args.keep_silent and os.path.isfile(rendered):
            try:
                os.remove(rendered)
            except OSError:
                pass

    res = dict(res or {})
    res.setdefault("outputs", [{"kind": "video", "path": out, "duration": None}])
    if rendered and args.keep_silent:
        res["silent"] = rendered
    res["timings"] = {**timings, **(res.get("timings") or {}),
                      "total": round(time.time() - t0, 2)}
    res["engine"] = {**render.engine_versions(), **(res.get("engine") or {})}
    return res


def build_parser(prog="video-studio narrate"):
    ap = argparse.ArgumentParser(
        prog=prog,
        description="Lồng giọng đọc vào một video câm; với --project thì render project rồi "
                    "lồng tiếng trong một lệnh. Engine giọng là `voice_studio` trong cùng venv.")
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--video", help="video câm đầu vào (.mp4)")
    src.add_argument("--project", help="project HyperFrames (tên trong trạm hoặc đường dẫn) — "
                                       "render câm trước rồi lồng tiếng")
    txt = ap.add_mutually_exclusive_group(required=True)
    txt.add_argument("--text", help="lời dẫn")
    txt.add_argument("--file", "--text-file", dest="file", help="file UTF-8 chứa lời dẫn")
    ap.add_argument("--out", required=True, help="video hoàn chỉnh (.mp4)")
    ap.add_argument("--profile", help="tên profile giọng (mặc định: profile mặc định của trạm giọng)")
    ap.add_argument("--instruct", help="thiết kế giọng bằng từ khoá — mỗi lần một giọng khác, "
                                       "CHỈ để thử")
    ap.add_argument("--lang", help="tên ngôn ngữ (mặc định của repo giọng: Vietnamese)")
    ap.add_argument("--speed", type=float, help="hệ số tốc độ đọc (1.0 = bình thường)")
    ap.add_argument("--seed", type=int, help="seed ghim để tái lập được")
    ap.add_argument("--normalize", action="store_true", help="chuẩn RMS cả bài")
    ap.add_argument("--mode", choices=MODES, default="fit",
                    help="fit = giữ khung cuối / đệm im lặng (mặc định) · shortest = cắt theo "
                         "cái ngắn hơn")
    ap.add_argument("--bgm", help="nhạc nền: tên style, đường dẫn file, hoặc 'none'")
    ap.add_argument("--bgm-volume", type=float, help="âm lượng nhạc nền (0.10 = 10%%)")
    ap.add_argument("--keep-silent", action="store_true",
                    help="giữ lại bản render câm trung gian (chỉ có nghĩa với --project)")
    ap.add_argument("--json", action="store_true", help="in một dòng JSON kết quả ra stdout")
    return ap


def main(argv=None):
    args, code = contract.parse(build_parser(), argv)
    if args is None:
        return code

    def fn(a):
        res = do_narrate(a)
        for o in res.get("outputs") or []:
            contract.log(f"[narrate] {o['kind']} -> {o['path']}")
        return res
    return contract.run(fn, args, args.json)


if __name__ == "__main__":
    import sys
    sys.exit(main())
