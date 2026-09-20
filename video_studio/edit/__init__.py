"""edit — chỉnh footage quay thật: bóc lời → gom cụm → (agent chọn đoạn) → cắt & dựng.

    video-studio edit --footage <thư mục quay> --out <thư mục ra>            # bóc lời + gom cụm
    video-studio edit --footage … --out … --edl edl.json                     # dựng theo EDL
    video-studio edit --footage … --out … --plan plan.md --edl edl.json --build-subtitles

Bộ này **chưng cất** từ `browser-use/video-use` (MIT, © 2026 Browser Use), đọc tại bản vendored
`92c2b34` và mang theo ba bản sửa upstream sau mốc đó (#55 giữ fps nguồn, #137 tôn trọng góc
xoay, #134 chọn đúng track tiếng). Từng module ghi rõ nó đến từ file nào; `NOTICE` ghi giấy phép.

**Quy trình là một cuộc hội thoại, không phải một nút bấm.** Máy bóc lời và gom cụm; việc CHỌN
đoạn nào, bỏ đoạn nào là việc của người (hoặc agent đọc `takes_packed.md`) và kết quả của việc
đó là file `edl.json`. Vì vậy lệnh chạy không có EDL sẽ dừng lại ở bước gom cụm và **nói bước
tiếp theo**, chứ không tự bịa ra một bản dựng.

**Hai đường thi hành** (`--backend`):

* `distill` — mã trong chính repo này. Cần ffmpeg; bóc lời cần thêm `pip install -e ".[edit]"`.
* `vendored` — gọi bản `video-use` đã cài ở trạm (khai trong `station.json: video_use`), cho
  ai muốn bám sát upstream hoặc cần đường ASR có phân biệt người nói.
* `auto` (mặc định) — dùng `distill` nếu chạy được, không thì `vendored`; không có đường nào
  thì **mã 3** kèm cả hai cách cài.
"""
import argparse
import os
import shutil
import subprocess

from .. import _env, contract
from ..contract import ContractError, EngineError, StationMissing, log

BACKENDS = ("auto", "distill", "vendored")
STEPS = ("all", "transcribe", "pack", "render")
WORK_NAME = "edit"
PACKED = "takes_packed.md"
DEFAULT_OUT_NAME = "final.mp4"

INSTALL_DISTILL = "`pip install -e \".[edit]\"` (bóc lời tại máy) + cài ffmpeg"
INSTALL_VENDORED = ("cài bản video-use vào trạm: `scripts/install-video-use.ps1` (Windows) "
                    "hoặc `scripts/install-video-use.sh` (macOS/Linux), rồi chạy "
                    "`video-studio init --station <trạm>` để ghi lại vào station.json")

__all__ = ["work_dir_for", "vendored_info", "choose_backend", "do_edit", "main"]


# ── nơi làm việc ────────────────────────────────────────────────────────────────────────

def _writable(path):
    try:
        os.makedirs(path, exist_ok=True)
        probe = os.path.join(path, ".video-studio-write-test")
        with open(probe, "w", encoding="utf-8") as f:
            f.write("")
        os.remove(probe)
        return True
    except OSError:
        return False


def work_dir_for(footage, work=None):
    """Thư mục làm việc: `--work` → `<footage>/edit` → `<trạm>/scratch/edit/<tên>`.

    Để cạnh footage vì transcript là CACHE: chạy lại lần sau không phải bóc lời lại. Footage
    nằm trên ổ chỉ-đọc (thẻ nhớ, thư mục đồng bộ) thì lùi về nháp của trạm thay vì đổ lỗi.
    """
    if work:
        return os.path.abspath(work)
    footage = os.path.abspath(footage)
    base = footage if os.path.isdir(footage) else os.path.dirname(footage)
    cand = os.path.join(base, WORK_NAME)
    if _writable(cand):
        return cand
    name = os.path.basename(base.rstrip(os.sep)) or "footage"
    alt = os.path.join(_env.station_dir(), "scratch", WORK_NAME, name)
    log(f"[edit] {base} không ghi được — dùng nơi làm việc {alt}")
    os.makedirs(alt, exist_ok=True)
    return alt


# ── đường thi hành ──────────────────────────────────────────────────────────────────────

def vendored_info(station=None):
    """-> (thư mục video-use, python của nó) từ station.json; (None, None) nếu chưa khai."""
    st = _env._expand(station) if station else _env.station_dir()
    info = _env.station_info(st).get("video_use")
    if not isinstance(info, dict) or not info.get("dir"):
        return None, None
    d = info["dir"]
    d = d if os.path.isabs(d) else os.path.join(st, *str(d).replace("\\", "/").split("/"))
    py = info.get("python")
    if py:
        py = py if os.path.isabs(py) else os.path.join(st, *str(py).replace("\\", "/").split("/"))
    if not os.path.isdir(d) or not py or not os.path.isfile(py):
        return None, None
    return d, py


def _distill_can(step):
    if step == "transcribe":
        from . import transcribe as tr
        return tr.available() and bool(_env.ffmpeg_exe())
    if step == "render":
        return bool(_env.ffmpeg_exe() and _env.ffprobe_exe())
    return True                        # gom cụm chỉ cần thư viện chuẩn


def choose_backend(step, want="auto", station=None):
    """-> "distill" | "vendored". Không đường nào chạy được ⇒ StationMissing (mã 3)."""
    has_vendored = all(vendored_info(station))
    if want == "distill":
        if not _distill_can(step):
            raise StationMissing(f"bước '{step}' chạy bằng mã trong repo cần: {INSTALL_DISTILL}")
        return "distill"
    if want == "vendored":
        if not has_vendored:
            raise StationMissing("trạm chưa có bản video-use dùng được — " + INSTALL_VENDORED)
        return "vendored"
    if _distill_can(step):
        return "distill"
    if has_vendored:
        log(f"[edit] bước '{step}' dùng bản video-use ở trạm (mã trong repo chưa đủ phụ thuộc)")
        return "vendored"
    raise StationMissing(
        f"bước '{step}' không có đường nào chạy được. Chọn MỘT trong hai:\n"
        f"  1. mã trong repo: {INSTALL_DISTILL}\n"
        f"  2. bản video-use ở trạm: {INSTALL_VENDORED}")


def _vendored_script(helper_dir, *names):
    """Tên script đầu tiên CÓ THẬT trong bản vendored (upstream đổi tên/thêm file theo bản)."""
    for n in names:
        if os.path.isfile(os.path.join(helper_dir, "helpers", n)):
            return n
    raise StationMissing(f"bản video-use ở trạm không có {' hoặc '.join(names)} trong helpers/ — "
                         + INSTALL_VENDORED)


def _run_vendored(py, helper_dir, script, args):
    argv = [py, os.path.join(helper_dir, "helpers", script), *[str(a) for a in args]]
    if not os.path.isfile(argv[1]):
        raise StationMissing(f"bản video-use ở trạm không có {script} ({argv[1]}) — "
                             + INSTALL_VENDORED)
    log("[edit] " + " ".join(os.path.basename(a) for a in argv[:2]))
    r = subprocess.run(argv, cwd=helper_dir)
    if r.returncode != 0:
        raise EngineError(f"{script} (bản video-use ở trạm) thoát mã {r.returncode}")
    return r.returncode


# ── các bước ────────────────────────────────────────────────────────────────────────────

def step_transcribe(args, work, backend):
    if backend == "distill":
        from . import transcribe as tr
        files = tr.transcribe_all(args.footage, work, language=args.language, force=args.force)
        return {"backend": backend, "transcripts": files}
    d, py = vendored_info()
    # Bản vendored có thể đã được áp bản ASR chạy tại máy (`transcribe_whisper.py`) hoặc không;
    # đường còn lại của upstream gọi dịch vụ ASR trả phí và ĐÒI khoá API — nói ra trước khi chạy
    # thay vì để người dùng nhận một lỗi 401 sau mười phút.
    script = _vendored_script(d, "transcribe_whisper.py", "transcribe.py")
    if script == "transcribe.py":
        log("[edit] bản video-use ở trạm chỉ có đường ASR qua dịch vụ (cần khoá API). Muốn bóc "
            "lời tại máy thì dùng --backend distill sau khi `pip install -e \".[edit]\"`.")
    extra = ["--edit-dir", work, "--language", args.language]
    if args.force:
        extra.append("--force")
    _run_vendored(py, d, script, [os.path.abspath(args.footage), *extra])
    tdir = os.path.join(work, "transcripts")
    return {"backend": backend,
            "transcripts": sorted(os.path.join(tdir, n) for n in os.listdir(tdir)
                                  if n.endswith(".json")) if os.path.isdir(tdir) else []}


def step_pack(args, work, backend):
    tdir = os.path.join(work, "transcripts")
    if not os.path.isdir(tdir) or not os.listdir(tdir):
        raise ContractError(f"chưa có bản bóc lời nào ở {tdir} — chạy bước 'transcribe' trước")
    if backend == "distill":
        from . import pack
        res = pack.pack_dir(tdir, os.path.join(work, PACKED), silence=args.silence)
        log(f"[edit] gom cụm → {res['path']} ({res['phrases']} cụm)")
        return {"backend": backend, **res}
    d, py = vendored_info()
    _run_vendored(py, d, "pack_transcripts.py", ["--edit-dir", work,
                                                 "--silence-threshold", args.silence])
    return {"backend": backend, "path": os.path.join(work, PACKED)}


def step_render(args, work, backend, edl_path, out_file):
    if backend == "distill":
        from . import edl as edl_mod, render as edit_render
        data = edl_mod.load(edl_path)
        return {"backend": backend,
                **edit_render.render_edl(data, os.path.dirname(os.path.abspath(edl_path)), work,
                                         out_file, quality=args.quality,
                                         build_subtitles=args.build_subtitles,
                                         subtitles=not args.no_subtitles,
                                         normalize=not args.no_loudnorm, fps=args.fps)}
    d, py = vendored_info()
    extra = ["-o", out_file]
    if args.quality == "preview":
        extra.append("--preview")
    if args.quality == "draft":
        extra.append("--draft")
    if args.build_subtitles:
        extra.append("--build-subtitles")
    if args.no_subtitles:
        extra.append("--no-subtitles")
    if args.no_loudnorm:
        extra.append("--no-loudnorm")
    _run_vendored(py, d, "render.py", [os.path.abspath(edl_path), *extra])
    return {"backend": backend, "outputs": [{"kind": "video", "path": os.path.abspath(out_file),
                                             "duration": None}]}


# ── lệnh ────────────────────────────────────────────────────────────────────────────────

def _find_edl(args, work):
    if args.edl:
        if not os.path.isfile(args.edl):
            raise ContractError(f"không có file EDL: {args.edl}")
        return os.path.abspath(args.edl)
    cand = os.path.join(work, "edl.json")
    return cand if os.path.isfile(cand) else None


def do_edit(args):
    footage = os.path.abspath(args.footage)
    if not os.path.exists(footage):
        raise StationMissing(f"không có footage: {footage}")
    work = work_dir_for(footage, args.work)
    os.makedirs(work, exist_ok=True)
    out_dir = os.path.abspath(args.out)
    os.makedirs(out_dir, exist_ok=True)
    res = {"footage": footage, "work": work, "out": out_dir, "steps": []}

    if args.plan:
        if not os.path.isfile(args.plan):
            raise ContractError(f"không có file kế hoạch: {args.plan}")
        kept = os.path.join(work, "plan.md")
        if os.path.abspath(args.plan) != kept:
            shutil.copyfile(args.plan, kept)
        res["plan"] = kept

    want = args.step
    if want in ("all", "transcribe"):
        res["transcribe"] = step_transcribe(args, work,
                                            choose_backend("transcribe", args.backend))
        res["steps"].append("transcribe")
    if want in ("all", "pack"):
        res["pack"] = step_pack(args, work, choose_backend("pack", args.backend))
        res["steps"].append("pack")

    edl_path = _find_edl(args, work)
    if want == "render" and not edl_path:
        raise ContractError("bước 'render' cần --edl <edl.json> (hoặc một edl.json trong nơi "
                            "làm việc)")
    if want in ("all", "render") and edl_path:
        out_file = os.path.join(out_dir, args.name or DEFAULT_OUT_NAME)
        res["render"] = step_render(args, work, choose_backend("render", args.backend),
                                    edl_path, out_file)
        res["edl"] = edl_path
        res["outputs"] = res["render"].get("outputs") or []
        res["steps"].append("render")
    elif want == "all":
        res["next"] = (f"đọc {os.path.join(work, PACKED)}, chọn đoạn, viết "
                       f"{os.path.join(work, 'edl.json')} rồi chạy lại lệnh này "
                       "(hoặc thêm --edl <file>)")
        log("[edit] " + res["next"])
    return res


def build_parser(prog="video-studio edit"):
    ap = argparse.ArgumentParser(
        prog=prog,
        description="Chỉnh footage quay thật theo bản ghi lời: bóc lời → gom cụm → dựng theo "
                    "EDL. Không có EDL thì dừng ở bước gom cụm và chỉ bước tiếp theo.")
    ap.add_argument("--footage", required=True, help="thư mục (hoặc một file) quay gốc")
    ap.add_argument("--out", required=True, help="thư mục nhận video ra")
    ap.add_argument("--name", help=f"tên file ra (mặc định {DEFAULT_OUT_NAME})")
    ap.add_argument("--plan", help="file kế hoạch dựng (markdown) — được giữ lại cạnh bản dựng")
    ap.add_argument("--edl", help="EDL mô tả các đoạn cắt (mặc định: <nơi làm việc>/edl.json)")
    ap.add_argument("--work", help="nơi làm việc (mặc định <footage>/edit)")
    ap.add_argument("--step", choices=STEPS, default="all", help="chạy một bước thôi")
    ap.add_argument("--backend", choices=BACKENDS, default="auto",
                    help="mã trong repo (distill) hay bản video-use ở trạm (vendored)")
    ap.add_argument("--language", default="vi", help="ngôn ngữ khi bóc lời ('auto' = tự nhận)")
    ap.add_argument("--force", action="store_true", help="bóc lời lại dù đã có bản cũ")
    ap.add_argument("--silence", type=float, default=0.5,
                    help="ngưỡng khoảng lặng (giây) để ngắt cụm khi gom")
    ap.add_argument("--quality", choices=("final", "preview", "draft"), default="final")
    ap.add_argument("--fps", type=float, help="ép số khung/giây (mặc định: giữ fps của nguồn)")
    ap.add_argument("--build-subtitles", action="store_true",
                    help="dựng phụ đề từ bản bóc lời + mốc của EDL")
    ap.add_argument("--no-subtitles", action="store_true", help="bỏ phụ đề kể cả khi EDL có")
    ap.add_argument("--no-loudnorm", action="store_true", help="bỏ bước chuẩn âm lượng")
    ap.add_argument("--json", action="store_true", help="in một dòng JSON kết quả ra stdout")
    return ap


def main(argv=None):
    args, code = contract.parse(build_parser(), argv)
    if args is None:
        return code
    return contract.run(do_edit, args, args.json)


if __name__ == "__main__":
    import sys
    sys.exit(main())
