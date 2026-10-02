"""probe.py — `video-studio probe`: render thử một trang tí hon để biết môi trường render còn sống.

## Vì sao có lệnh này

Mac mini 02/10/2026: Hot AI 18:00 hỏng sau 42 phút — `page.goto … Navigation timeout of
60000 ms` ở frame 0, ba lần thử. Mọi project đều hỏng (kể cả mẫu từng dựng được, kể cả bản
HyperFrames mới nhất), trong khi Chromium/puppeteer mở cùng trang bình thường. **Khởi động lại
máy là hết.** Đó là trạng thái kẹt của hệ điều hành, không phải lỗi repo — nhưng pipeline chỉ
biết ra điều đó SAU bước nghiên cứu (agent) và TTS, tức sau 40 phút và một lượt hạn mức.

Lệnh này đi đúng đường render thật (`hyperframes render`: mở trang trong Chrome headless, tua
timeline, chụp khung, ghép mp4) trên một trang 320×180 dài 0,5 s, **không tài nguyên ngoài**
(không font web, không GSAP từ CDN): đo trên Windows 7,2 s cả khởi động npx. Bên gọi đặt nó
TRƯỚC các bước tốn kém.

## Hợp đồng

    video-studio probe [--timeout 30] [--json]

    0  render thử ra file mp4 → môi trường render dùng được
    1  render thử hỏng. Quá `--timeout` hoặc gặp `Navigation timeout` = **kẹt** (lỗi mở đầu
       bằng `RENDER_STUCK:` và gợi ý khởi động lại máy); hỏng kiểu khác thì kèm đuôi log của
       HyperFrames + gợi ý `video-studio doctor --hf`
    2  tham số sai
    3  thiếu `npx` (Node)

Quá giờ thì giết **cả cây** tiến trình (npx → node → các worker Chrome), không chỉ vỏ npx:
để lại Chrome mồ côi đúng lúc máy đang kẹt là làm nó kẹt thêm.

**Làm ấm NGOÀI trần giờ.** Trần `--timeout` chỉ đo phần render. Trước đó `warm_up` bảo đảm npx
đã có gói `hyperframes@<bản ghim>` (`--version`) và Chromium của HyperFrames đã nằm trong cache
(`browser ensure` nếu `doctor` không thấy), mỗi bước trần `WARM_TIMEOUT`. Không làm vậy thì lượt
đầu sau khi nâng bản ghim / xoá cache bị tính là "kẹt" — và vì bị giết giữa lúc tải, cache không
bao giờ đầy, mọi lượt sau cũng "kẹt" (review 02/10). Làm ấm hỏng ⇒ mã 3 (thiếu công cụ), không
phải `RENDER_STUCK`: khởi động lại máy không chữa được mạng hay cache.
"""
import argparse
import os
import shutil
import signal
import subprocess
import tempfile
import time

from . import _env, contract, render
from .contract import EngineError, StationMissing

DEFAULT_TIMEOUT = 30
WARM_TIMEOUT = 600      # giây cho mỗi bước làm ấm (tải gói npx / Chromium lần đầu)
STUCK = render.STUCK_PREFIX
HINT_REBOOT = "khởi động lại máy rồi chạy lại"
NAV_TIMEOUT = "navigation timeout"
OUT = "probe.mp4"

# Trang thử: KHÔNG tài nguyên ngoài — mạng chậm không được giả làm "render kẹt". Timeline là một
# vật giả tối thiểu thay GSAP: engine chỉ cần tua được nó; thiếu `window.__timelines` thì engine
# chờ 45 s (`sub_timeline_readiness_timeout`) rồi mới chụp — phép thử rẻ thành phép thử đắt.
INDEX_HTML = """<!doctype html>
<html lang="en">
  <head><meta charset="UTF-8" /><title>video-studio probe</title>
    <style>html,body{margin:0;width:320px;height:180px;overflow:hidden;background:#0b1220;color:#fff}</style>
  </head>
  <body>
    <div id="master-root" data-composition-id="master" data-width="320" data-height="180"
         data-start="0" data-duration="0.5"><div data-start="0" data-duration="0.5">probe</div>
      <script>
        var t = 0;
        var tl = { duration: function () { return 0.5; }, totalDuration: function () { return 0.5; },
                   time: function (v) { if (v === undefined) return t; t = v; return tl; },
                   totalTime: function (v) { return tl.time(v); },
                   seek: function (v) { t = v; return tl; }, pause: function () { return tl; },
                   play: function () { return tl; }, progress: function () { return t / 0.5; },
                   paused: function () { return true; }, isActive: function () { return false; },
                   getChildren: function () { return []; }, eventCallback: function () { return tl; } };
        window.__timelines = window.__timelines || {};
        window.__timelines["master"] = tl;
      </script>
    </div>
  </body>
</html>
"""
CONFIG = {
    "hyperframes.json": '{"paths": {"blocks": "compositions", "components": '
                        '"compositions/components", "assets": "assets"}}\n',
    "meta.json": '{"id": "probe", "name": "probe"}\n',
    "package.json": '{"name": "video-studio-probe", "private": true, "type": "module"}\n',
}


def write_project(d):
    """Dựng project thử trong thư mục `d`. -> d."""
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, render.INDEX), "w", encoding="utf-8") as f:
        f.write(INDEX_HTML)
    for name, text in CONFIG.items():
        with open(os.path.join(d, name), "w", encoding="utf-8") as f:
            f.write(text)
    return d


def _kill_tree(p):
    """Giết cả nhóm tiến trình con. Không ném — dọn dẹp hỏng không được che lỗi chính."""
    try:
        if os.name == "nt":
            subprocess.run(["taskkill", "/T", "/F", "/PID", str(p.pid)],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
        else:
            os.killpg(os.getpgid(p.pid), signal.SIGKILL)
    except (OSError, ValueError, subprocess.SubprocessError):
        pass
    try:
        p.wait(timeout=10)
    except (OSError, subprocess.SubprocessError):
        pass


def _lam_am_mot(argv, ten, run):
    try:
        r = run(argv, env=render.render_env(), capture_output=True, timeout=WARM_TIMEOUT)
    except subprocess.TimeoutExpired as e:
        raise StationMissing(f"làm ấm `{ten}` quá {WARM_TIMEOUT}s (đang tải lần đầu? mạng?) — "
                             f"chạy tay `{' '.join(argv[1:])}` rồi thử lại") from e
    except OSError as e:
        raise StationMissing(f"không chạy được `{ten}`: {e}") from e
    if r.returncode != 0:
        err = r.stderr or r.stdout or b""
        err = err.decode("utf-8", "replace") if isinstance(err, bytes) else str(err)
        raise StationMissing(f"`{ten}` hỏng (mã {r.returncode}) — chạy `video-studio doctor --hf`"
                             f"\n{err.strip()[-600:]}")


def warm_up(run=subprocess.run, chromium=None):
    """Gói npx + Chromium sẵn sàng TRƯỚC khi bấm giờ. Ném StationMissing (mã 3) nếu không được."""
    _lam_am_mot(render.hyperframes_argv("--version"), "hyperframes --version", run)
    if chromium is None:
        from . import doctor
        chromium = doctor.chromium_check(_env.hyperframes_version())["ok"]
    if not chromium:
        contract.log("[probe] chưa thấy Chromium của HyperFrames trong cache — `browser ensure` ...")
        _lam_am_mot(render.hyperframes_argv("browser", "ensure"), "hyperframes browser ensure", run)


def run_probe(timeout=DEFAULT_TIMEOUT, workdir=None, popen=subprocess.Popen, clock=time.monotonic,
              warm=True):
    """Render thử. -> {"seconds", "hyperframes"}; ném EngineError (mã 1) / StationMissing (mã 3).

    `popen`/`clock`/`warm` mở cho test — không gọi Node thật trong bộ test lõi.
    """
    argv = render.hyperframes_argv("render", "-o", OUT, "-q", "draft")
    if warm is True:
        warm_up()            # tra tên lúc GỌI (không đóng băng lúc định nghĩa) — test thay được
    elif warm:
        warm()
    own = workdir is None
    d = write_project(workdir or tempfile.mkdtemp(prefix="video-studio-probe-"))
    kw = {"start_new_session": True} if os.name != "nt" else {
        "creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
    t0 = clock()
    try:
        p = popen(argv, cwd=d, env=render.render_env(), stdout=subprocess.PIPE,
                  stderr=subprocess.STDOUT, **kw)
        try:
            out, _ = p.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            _kill_tree(p)
            raise EngineError(
                f"{STUCK}: môi trường render kẹt — HyperFrames không dựng xong một trang 0,5 s "
                f"trong {timeout}s (bình thường vài giây) — {HINT_REBOOT}")
        secs = round(clock() - t0, 1)
        text = (out or b"").decode("utf-8", "replace") if isinstance(out, bytes) else str(out or "")
        tail = "\n".join(text.strip().splitlines()[-15:])
        mp4 = os.path.join(d, OUT)
        hong = p.returncode != 0 or not os.path.isfile(mp4) or os.path.getsize(mp4) == 0
        # Chỉ tính Navigation timeout khi lượt HỎNG: engine thử lại nội bộ rồi qua thì vẫn đạt.
        if hong and NAV_TIMEOUT in text.lower():
            raise EngineError(
                f"{STUCK}: môi trường render kẹt — HyperFrames không mở được trang "
                f"(Navigation timeout) — {HINT_REBOOT}\n{tail}")
        if hong:
            raise EngineError(
                f"render thử hỏng (mã {p.returncode}) sau {secs}s — chạy `video-studio doctor "
                f"--hf` để kiểm engine; không rõ nguyên nhân thì {HINT_REBOOT}\n{tail}")
        return {"seconds": secs, "hyperframes": _env.hyperframes_version()}
    finally:
        if own:
            shutil.rmtree(d, ignore_errors=True)


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="video-studio probe",
        description="Render thử một trang 320×180 dài 0,5 s (không tài nguyên ngoài) để biết "
                    "môi trường render còn dùng được. Đặt trước các bước tốn kém.")
    ap.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT,
                    help=f"giây; quá giờ = môi trường kẹt (mặc định {DEFAULT_TIMEOUT})")
    ap.add_argument("--json", action="store_true", help="in một dòng JSON kết quả ra stdout")
    args, code = contract.parse(ap, argv)
    if args is None:
        return code
    if args.timeout < 1:
        contract.log("--timeout phải ≥ 1")
        if args.json:
            contract.emit({"ok": False, "code": contract.CONTRACT_ERROR,
                           "error": "--timeout phải ≥ 1"})
        return contract.CONTRACT_ERROR

    try:
        res = run_probe(args.timeout)
    except Exception as e:      # noqa: BLE001 — biên của CLI: mọi lỗi phải thành mã + JSON
        # Hỏng của phép thử là KẾT QUẢ đo, không phải sự cố của chương trình: không in traceback
        # (`contract.run` in nó cho mã 1) — đuôi log runner rồi tin Telegram phải là câu người đọc.
        code = contract.classify(e)
        msg = str(e) or e.__class__.__name__
        contract.log(f"[probe] LỖI ({code}): {msg}")
        if args.json:
            contract.emit({"ok": False, "code": code, "error": msg})
        return code
    return contract.run(lambda _a: _ok(res), args, args.json)


def _ok(res):
    contract.log(f"[probe] render thử OK sau {res['seconds']}s (hyperframes {res['hyperframes']})")
    return res
