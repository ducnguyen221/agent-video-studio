"""A small offline, seekable 16:9 preview of the existing sun-ray painter."""
import os
import hashlib
from contextlib import ExitStack
from pathlib import Path
import tempfile

from .. import render
from ..contract import ContractError
from ..effect_library import resources

PREVIEW_ASSET_HASHES = {
    "sun-rays.js": "8f7a84510161277342da0b5d11b8e6341705bb35d95f5d89a64f40d8de01e3c8",
    "lens-flare.js": "99d91c590ad3d9eea0ef58bdb848a4ca1f5d14843a416cbbd8e20f7fdf43740f",
}

HTML = '''<!doctype html><html lang="en"><head><meta charset="utf-8">
<style>html,body{margin:0;width:100%;height:100%;overflow:hidden;background:#202533}
#master{width:100%;height:100%;position:relative}canvas{position:absolute;inset:0;width:100%;height:100%}</style>
</head><body><div id="master" data-composition-id="master" data-width="1920" data-height="1080" data-start="0" data-duration="2">
<canvas id="rays" width="1920" height="1080"></canvas><canvas id="flare" width="1920" height="1080"></canvas><script src="gsap.min.js"></script><script src="sun-rays.js"></script><script src="lens-flare.js"></script><script>
const paint=PhotoSunRays.createSunRayPainter(document.getElementById('rays'));
const paintFlare=PhotoLensFlare.createLensFlarePainter(document.getElementById('flare'));
const update=()=>{paint(clock.t);paintFlare(clock.t)};
const clock={t:0}; const tl=gsap.timeline({paused:true,onUpdate:update});
tl.to(clock,{t:2,duration:2,ease:'none'});
for(const name of ['time','totalTime','seek']){const original=tl[name];tl[name]=function(...args){const result=original.apply(this,args);if(args.length)update();return result}}
update();window.__timelines={master:tl};</script></div></body></html>'''


def _read_preview_assets():
    """Read only pinned seed bytes via the Windows no-recall handle boundary."""
    if os.name != "nt":
        raise ContractError("effect-preview chưa hỗ trợ đọc asset an toàn trên hệ điều hành này")
    from ..effect_library import _native_windows as native
    try:
        with ExitStack() as roots:
            directory = native.open_root(os.path.abspath(resources.resource_root()))
            roots.callback(native.close, directory)
            for part in ("skills", "photo-ambient-effects", "assets"):
                directory = native.open_directory(directory, part)
                roots.callback(native.close, directory)
            assets = {}
            for name, expected in PREVIEW_ASSET_HASHES.items():
                with ExitStack() as opened:
                    handle = native.open_file(directory, name)
                    opened.callback(native.close, handle)
                    payload = native.read_all(handle, 1024 * 1024)
                if hashlib.sha256(payload).hexdigest() != expected:
                    raise ContractError(f"Asset {name} có SHA-256 không khớp bản đã ghim")
                assets[name] = payload
    except (OSError, ValueError) as exc:
        raise ContractError(f"Không đọc được asset preview cục bộ: {exc}") from exc
    return assets


def render_preview(data, out_dir):
    gsap = data.get("_gsap_bytes")
    if not isinstance(gsap, bytes) or hashlib.sha256(gsap).hexdigest() != render.PREVIEW_GSAP_SHA256:
        raise ContractError("GSAP SHA-256 không khớp bản 3.15.0 đã ghim")
    outputs = data.get("outputs", {})
    if not outputs.get("long") or outputs.get("short"):
        raise ContractError("effect-preview chỉ nhận outputs.long và không nhận outputs.short")
    name = outputs["long"] if isinstance(outputs["long"], str) else "effect-preview.mp4"
    assets = _read_preview_assets()
    output = os.path.abspath(os.path.join(out_dir, name))
    with tempfile.TemporaryDirectory(prefix="video-effect-preview-") as project:
        Path(project, "index.html").write_text(HTML, encoding="utf-8")
        for asset_name, asset_bytes in assets.items():
            Path(project, asset_name).write_bytes(asset_bytes)
        Path(project, "gsap.min.js").write_bytes(gsap)
        render.render_project(project, output, label="effect-preview", offline=True)
    return [{"kind": "long", "path": output, "duration": 2.0}]
