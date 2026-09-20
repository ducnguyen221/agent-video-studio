"""voice.py — MỘT cửa duy nhất của repo này sang repo giọng (`voice_studio`).

Vì sao có file này: `narrate`, `render` và template đều cần giọng, nhưng repo giọng là
**phụ thuộc tuỳ chọn** (extras `[voice]`). Nếu mỗi chỗ tự `import voice_studio` thì máy chưa
cài sẽ ném `ModuleNotFoundError` — một câu đúng sự thật nhưng nói cho sai người: người dùng
đọc traceback không biết phải cài gì. Ở đây mọi lần import đi qua `_mod()`, và cái ném ra là
`StationMissing` (mã 3) kèm đúng câu lệnh phải chạy.

Hai việc:

    narrate(...)   video câm + lời dẫn → MP4 có giọng (và nhạc nền), qua `voice_studio.narrate`
    mix_bgm(...)   trộn một lớp nhạc nền DƯỚI track giọng đã có của một file (tại chỗ)

Không tự tổng hợp, không tự gọi ffmpeg: luật giọng (profile bắt buộc, seed ghim, chuẩn RMS) và
luật ghép (fit/shortest, âm lượng nhạc nền) sống ở repo giọng — chép sang đây là hai bản sao
của cùng một bài học, và bản thứ hai luôn là bản lạc hậu.
"""
import argparse
import importlib

from .contract import StationMissing

INSTALL_HINT = (
    "cài repo giọng vào CÙNG venv: `pip install -e <bản clone agent-voice-studio>` "
    "(rồi `pip install -e \".[voice]\"` ở repo này). Kiểm bằng `video-studio doctor`.")

__all__ = ["available", "module", "narrate", "mix_bgm", "version"]


def _mod(name="voice_studio"):
    try:
        return importlib.import_module(name)
    except ImportError as e:
        raise StationMissing(f"bước này cần `{name}` nhưng venv đang chạy chưa có — "
                             + INSTALL_HINT) from e


def module(name):
    """Import một module con của repo giọng (`av`, `engine`, `profiles`, `narrate`…)."""
    _mod()                                  # gói cha trước: thông báo thiếu nói đúng tên gói
    return _mod("voice_studio." + name)


def available():
    """Repo giọng có trong venv này không (không ném lỗi — dùng cho doctor/JSON kết quả)."""
    try:
        importlib.import_module("voice_studio")
        return True
    except ImportError:
        return False


def version():
    try:
        return getattr(importlib.import_module("voice_studio"), "__version__", None)
    except ImportError:
        return None


def _args(argv, parser_factory):
    """Namespace tham số cho `voice_studio.narrate`.

    Ưu tiên parser CỦA CHÍNH repo giọng: nó biết mặc định của bản đang cài (ngôn ngữ, seed,
    chuẩn RMS), nên bản mới thêm tham số có mặc định vẫn chạy. Bản không có `build_parser`
    thì dựng Namespace tối thiểu.
    """
    if parser_factory is not None:
        return parser_factory().parse_args(argv)
    ns = argparse.Namespace(video=None, out=None, text=None, file=None, mode="fit", bgm=None,
                            bgm_volume=None, profile=None, instruct=None, lang=None, speed=None,
                            seed=None, normalize=False, json=False)
    it = iter(argv)
    for tok in it:
        key = tok.lstrip("-").replace("-", "_")
        if key == "normalize":
            ns.normalize = True
        else:
            setattr(ns, key, next(it))
    return ns


def narrate(video, out, *, text=None, file=None, profile=None, instruct=None, lang=None,
            speed=None, seed=None, normalize=False, mode="fit", bgm=None, bgm_volume=None):
    """Lồng giọng vào `video` → `out`. -> dict kết quả của repo giọng.

    `bgm`: tên style / đường dẫn file / "none" để tắt / None = theo cấu hình trạm giọng.
    """
    vn = module("narrate")
    argv = ["--video", str(video), "--out", str(out)]
    if file:
        argv += ["--file", str(file)]
    else:
        argv += ["--text", text or ""]
    argv += ["--mode", mode]
    for flag, val in (("--profile", profile), ("--instruct", instruct), ("--lang", lang),
                      ("--speed", speed), ("--seed", seed), ("--bgm", bgm),
                      ("--bgm-volume", bgm_volume)):
        if val is not None and val != "":
            argv += [flag, str(val)]
    if normalize:
        argv.append("--normalize")
    return vn.narrate(_args(argv, getattr(vn, "build_parser", None)))


def mix_bgm(path, style=None, volume=None):
    """Trộn nhạc nền dưới track giọng sẵn có của `path` (ghi đè tại chỗ). -> True nếu đã trộn.

    `style` None/"none" ⇒ không trộn gì (khác với repo giọng, nơi None nghĩa là "theo biến môi
    trường"): ở đây nhạc nền là một khoá CỦA SPEC, spec không khai thì không được có nhạc.
    """
    if style is None or str(style).strip().lower() in ("", "none", "off"):
        return False
    av = module("av")
    return bool(av.mix_bgm(str(path), bgm=str(style), volume=volume))
