"""Khung dựng giả cho test `make_weekly` / `make_weekly_short` / `topstory` — không Node, ffmpeg, giọng hay mạng.

Chỉ thay những thứ chạm ngoài (tổng hợp giọng, ASR, b-roll mạng, HyperFrames, mux); phần dựng HTML là mã thật,
nên HTML cảnh một ảnh có thể so với bản ghi vàng (`tests/fixtures/news_images/*.html`).
"""
import os
import types

from video_studio import render

MIN_BRAND = {"a": "Tin", "b": "Ngay", "site": "vi-du.example"}
PNG = b"\x89PNG\r\n\x1a\n" + b"\0" * 5000


def make_png(path):
    os.makedirs(os.path.dirname(str(path)), exist_ok=True)
    with open(path, "wb") as f:
        f.write(PNG)
    return str(path)


def install(monkeypatch, nv, project_dir, ts=None):
    """Thay phần chạm ngoài; trả `captured` (list HTML đã ghi qua `render.write_index`)."""
    captured = []
    os.makedirs(project_dir, exist_ok=True)
    monkeypatch.setattr(nv, "_proj", lambda: str(project_dir))
    monkeypatch.setattr(nv, "_synth_long", lambda model, text, prompt: [0] * 24000)
    monkeypatch.setattr(nv, "_asr_words", lambda audio, sr, lang="vi": [])
    monkeypatch.setattr(nv, "_words_from_text", lambda audio, sr, spoken: [])
    monkeypatch.setattr(nv, "asr_drift_warn", lambda *a, **k: None)
    monkeypatch.setattr(nv, "_local_filler", lambda *a, **k: None)
    monkeypatch.setattr(nv, "_broll_image", lambda *a, **k: False)   # không bao giờ ra mạng
    monkeypatch.setattr(nv, "av", types.SimpleNamespace(mux=lambda *a, **k: None))
    monkeypatch.setattr(render, "write_index", lambda proj, html: captured.append(html))
    monkeypatch.setattr(render, "render_project", lambda *a, **k: None)
    if ts is not None:
        monkeypatch.setattr(ts, "_proj", lambda: str(project_dir))
    return captured


MODEL = types.SimpleNamespace(sampling_rate=24000)


def weekly(nv, segments, out, short=False):
    fn = nv.make_weekly_short if short else nv.make_weekly
    brand = nv.resolve_brand(MIN_BRAND)
    return fn({"segments": segments}, str(out), "2026-01-02", week="1", range_="r", model=MODEL,
              prompt=None, brand=brand)
