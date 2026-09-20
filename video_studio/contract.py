"""contract.py — hợp đồng gọi từ pipeline khác: mã thoát, lỗi có tên, một dòng JSON cuối stdout.

Mọi lệnh `video-studio …` mà một chương trình khác gọi (marketing, lịch chạy, agent) tuân
cùng một hợp đồng với `voice-studio`, để bên gọi chỉ cần đọc MÃ THOÁT và DÒNG JSON CUỐI:

    0  ok
    1  lỗi engine / render — chạy lại có thể được (render sập, hết bộ nhớ…)
    2  hợp đồng sai — thiếu tham số, spec thiếu `brand`, bản HyperFrames không hợp lệ,
       xung đột khi di trú: phải SỬA CẤU HÌNH, chạy lại vô ích
    3  trạm thiếu — chưa có trạm video, thiếu node/ffmpeg: phải CÀI TIẾP (`video-studio doctor`)

Với `--json`: stdout kết thúc bằng ĐÚNG MỘT dòng JSON (`{"ok": true, …}` hoặc
`{"ok": false, "code": N, "error": "…"}`); mọi log người đọc đi ra stderr. Bên gọi lấy dòng
cuối không rỗng của stdout — log lạc vào stdout phía trước vẫn không làm hỏng việc parse.

Bẫy PowerShell 5.1: đừng `2>&1` khi gọi lệnh native — mỗi dòng stderr bị bọc thành lỗi và
`$?` thành False dù mã thoát là 0. Đọc `$LASTEXITCODE`.
"""
import json
import sys
import traceback

OK, ENGINE_ERROR, CONTRACT_ERROR, STATION_MISSING = 0, 1, 2, 3

__all__ = [
    "OK", "ENGINE_ERROR", "CONTRACT_ERROR", "STATION_MISSING",
    "VideoStudioError", "EngineError", "ContractError", "StationMissing",
    "log", "emit", "run", "parse",
]


class VideoStudioError(Exception):
    code = ENGINE_ERROR


class EngineError(VideoStudioError):
    """Render / engine hỏng giữa chừng — thử lại có thể qua."""
    code = ENGINE_ERROR


class ContractError(VideoStudioError):
    """Bên gọi truyền sai hoặc trạm ở trạng thái không cho phép làm tiếp."""
    code = CONTRACT_ERROR


class StationMissing(VideoStudioError):
    """Trạm video hoặc công cụ bắt buộc chưa có — `video-studio doctor` chỉ bước còn thiếu."""
    code = STATION_MISSING


def log(*parts):
    """Log cho người đọc: LUÔN ra stderr, để stdout chỉ còn kết quả."""
    print(*parts, file=sys.stderr, flush=True)


def emit(payload):
    """In một dòng JSON (UTF-8, không escape tiếng Việt) ra stdout."""
    sys.stdout.write(json.dumps(payload, ensure_ascii=False) + "\n")
    sys.stdout.flush()


def classify(exc):
    """Map một exception về mã thoát của hợp đồng."""
    if isinstance(exc, VideoStudioError):
        return exc.code
    return ENGINE_ERROR


def run(fn, args, as_json=False):
    """Chạy `fn(args) -> dict`, trả mã thoát; `as_json` ⇒ in dòng JSON cuối stdout."""
    try:
        result = fn(args) or {}
    except KeyboardInterrupt:
        raise
    except Exception as exc:        # noqa: BLE001 — biên của CLI: mọi lỗi phải thành mã thoát
        code = classify(exc)
        msg = str(exc) or exc.__class__.__name__
        log(f"[video-studio] LỖI ({code}): {msg}")
        if code == ENGINE_ERROR:
            log(traceback.format_exc().rstrip())
        if as_json:
            emit({"ok": False, "code": code, "error": msg})
        return code
    if as_json:
        emit({"ok": True, **result})
    return OK


def parse(ap, argv=None):
    """argparse theo hợp đồng: -> (args, None) hoặc (None, mã thoát).

    `--help` ⇒ mã 0; tham số sai ⇒ mã 2 (và dòng JSON lỗi nếu người gọi xin `--json`),
    thay vì để SystemExit của argparse lọt ra ngoài.
    """
    try:
        return ap.parse_args(argv), None
    except SystemExit as e:
        if e.code in (0, None):
            return None, OK
        raw = sys.argv[1:] if argv is None else list(argv)
        if "--json" in raw:
            emit({"ok": False, "code": CONTRACT_ERROR, "error": "tham số không hợp lệ (xem stderr)"})
        return None, CONTRACT_ERROR
