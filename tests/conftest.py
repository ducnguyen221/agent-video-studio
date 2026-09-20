"""Cấu hình chung cho test của package `video_studio`.

Mọi test chạy KHÔNG cần Node, HyperFrames, ffmpeg hay mạng: lệnh ngoài được thay bằng hàm giả.
Hai việc làm chung cho mọi test:

1. Đưa gốc repo vào `sys.path` để `import video_studio` chạy được cả khi chưa cài package.
2. Xoá sạch biến môi trường hợp đồng trước MỖI test và trỏ HOME sang thư mục tạm — máy chạy
   test có thể đang đặt `VIDEO_STATION`, `OMNIVOICE_DIR`… và có trạm thật ở `~/.video`; test
   không bao giờ được đọc hay ghi nhầm vào đó.
"""
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

CONTRACT_VARS = (
    "VIDEO_STATION", "VIDEO_ROOT", "VOICE_STATION", "OMNIVOICE_DIR",
    "HYPERFRAMES_VERSION", "HYPERFRAMES_WORKDIR", "NODE_DIR", "FFMPEG_DIR",
    "VIDEO_FONT", "CHROME_BIN", "VIDEO_STUDIO_REPO",
)


@pytest.fixture(autouse=True)
def _clean_contract_env(monkeypatch, tmp_path):
    for name in CONTRACT_VARS:
        monkeypatch.delenv(name, raising=False)
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    # Bản clone đang chạy test có thể có workspace/ hoặc studio.local.json thật — trỏ "repo"
    # sang một thư mục tạm rỗng; test nào cần repo thì tự dựng.
    monkeypatch.setenv("VIDEO_STUDIO_REPO", str(tmp_path / "no-repo"))
    yield


def fake_voice_studio(monkeypatch, narrate=None, mix_bgm=None, version="9.9.9"):
    """Cài một `voice_studio` GIẢ vào sys.modules. -> module gốc (có `.calls`).

    Repo giọng là phụ thuộc tuỳ chọn và nặng (torch); test của repo này không bao giờ nạp nó.
    Bản giả chỉ cần đủ bề mặt mà `video_studio.voice` chạm tới: `narrate.build_parser()`,
    `narrate.narrate(args)` và `av.mix_bgm(path, bgm=…, volume=…)`.
    """
    import argparse
    import types

    pkg = types.ModuleType("voice_studio")
    pkg.__version__ = version
    pkg.__path__ = []
    pkg.calls = []

    nar = types.ModuleType("voice_studio.narrate")

    def build_parser():
        ap = argparse.ArgumentParser(prog="voice-studio narrate")
        ap.add_argument("--video", required=True)
        ap.add_argument("--out", required=True)
        g = ap.add_mutually_exclusive_group(required=True)
        g.add_argument("--text")
        g.add_argument("--file", "--text-file", dest="file")
        ap.add_argument("--mode", choices=("fit", "shortest"), default="fit")
        ap.add_argument("--bgm")
        ap.add_argument("--bgm-volume", type=float)
        ap.add_argument("--profile")
        ap.add_argument("--instruct")
        ap.add_argument("--lang", default="Vietnamese")
        ap.add_argument("--speed", type=float)
        ap.add_argument("--seed", type=int, default=42)
        ap.add_argument("--normalize", action="store_true")
        ap.add_argument("--json", action="store_true")
        return ap

    def _narrate(args):
        pkg.calls.append(("narrate", vars(args)))
        if narrate is not None:
            return narrate(args)
        with open(args.out, "w", encoding="utf-8") as f:
            f.write("mp4")
        return {"outputs": [{"kind": "video", "path": args.out, "duration": 12.5}],
                "profile": args.profile, "timings": {"synth": 1.0},
                "engine": {"voice_studio": version}}

    nar.build_parser = build_parser
    nar.narrate = _narrate

    av = types.ModuleType("voice_studio.av")

    def _mix(path, bgm=None, volume=None):
        pkg.calls.append(("mix_bgm", {"path": path, "bgm": bgm, "volume": volume}))
        return True if mix_bgm is None else mix_bgm(path, bgm, volume)

    av.mix_bgm = _mix
    pkg.narrate, pkg.av = nar, av
    for name, mod in (("voice_studio", pkg), ("voice_studio.narrate", nar),
                      ("voice_studio.av", av)):
        monkeypatch.setitem(sys.modules, name, mod)
    return pkg


def last_json(text):
    """Dòng JSON cuối (không rỗng) của stdout — đúng cách bên gọi đọc hợp đồng."""
    import json
    lines = [ln for ln in text.splitlines() if ln.strip()]
    assert lines, "stdout rỗng — hợp đồng đòi một dòng JSON cuối"
    return json.loads(lines[-1])
