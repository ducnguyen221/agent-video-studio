"""Effect preview uses the real render entrypoint without network dependencies."""
import json
import hashlib
from pathlib import Path

from video_studio import render


def test_effect_preview_cli_builds_a_seekable_offline_project(tmp_path, monkeypatch):
    monkeypatch.setattr(render, "PREVIEW_GSAP_SHA256", hashlib.sha256(b"fixture").hexdigest())
    source = tmp_path / "spec.json"
    source.write_text(json.dumps({"schema_version": 1, "brand": {"a": "Example", "b": "Studio", "site": "example.invalid"}, "outputs": {"long": "preview.mp4", "short": False}}), encoding="utf-8")
    gsap = tmp_path / "gsap.min.js"
    gsap.write_text("fixture", encoding="utf-8")
    seen = {}

    def fake_render(project, output, **kwargs):
        from pathlib import Path
        p = Path(project)
        seen["html"] = (p / "index.html").read_text(encoding="utf-8")
        seen["asset"] = (p / "sun-rays.js").read_text(encoding="utf-8")
        seen["offline"] = kwargs.get("offline")
        Path(output).write_bytes(b"video")
        return output

    monkeypatch.setattr(render, "render_project", fake_render)
    assert render.main(["--project", "effect-preview", "--input", str(source), "--out", str(tmp_path / "out"), "--gsap-file", str(gsap)]) == 0
    assert "createSunRayPainter" in seen["asset"]
    assert "gsap.timeline({paused:true" in seen["html"]
    assert "paint(clock.t);paintFlare(clock.t)" in seen["html"]
    assert "https://" not in seen["html"]
    assert seen["offline"] is True
    assert (tmp_path / "out" / "preview.mp4").exists()


def test_effect_preview_requires_explicit_local_gsap(tmp_path, capsys):
    source = tmp_path / "spec.json"
    source.write_text(json.dumps({"schema_version": 1, "brand": {"a": "Example", "b": "Studio", "site": "example.invalid"}, "outputs": {"long": True, "short": False}}), encoding="utf-8")
    assert render.main(["--project", "effect-preview", "--input", str(source), "--out", str(tmp_path / "out")]) == 2
    assert "--gsap-file" in capsys.readouterr().err
    assert not (tmp_path / "out").exists()


def test_effect_preview_rejects_untrusted_gsap_before_render(tmp_path, capsys, monkeypatch):
    def unexpected_render(*args, **kwargs):
        raise AssertionError("untrusted script reached renderer")
    monkeypatch.setattr(render, "render_project", unexpected_render)
    source = tmp_path / "spec.json"
    source.write_text(json.dumps({"schema_version": 1, "brand": {"a": "Example", "b": "Studio", "site": "example.invalid"}, "outputs": {"long": True, "short": False}}), encoding="utf-8")
    gsap = tmp_path / "untrusted.js"
    gsap.write_text("arbitrary script", encoding="utf-8")
    assert render.main(["--project", "effect-preview", "--input", str(source), "--out", str(tmp_path / "out"), "--gsap-file", str(gsap)]) == 2
    assert "SHA-256" in capsys.readouterr().err
    assert not (tmp_path / "out").exists()


def test_effect_preview_uses_installed_bundle_assets(tmp_path, monkeypatch):
    from video_studio.effect_library import resources
    from video_studio.templates import effect_preview
    monkeypatch.setattr(render, "PREVIEW_GSAP_SHA256", hashlib.sha256(b"gsap").hexdigest())
    monkeypatch.setattr(effect_preview, "PREVIEW_ASSET_HASHES", {
        name: hashlib.sha256(("bundled " + name).encode()).hexdigest()
        for name in ("sun-rays.js", "lens-flare.js")
    })

    package = tmp_path / "site-packages" / "video_studio"
    bundle = package / "_bundled"
    for name in ("skills/video-theme-library/assets/effect-library/entries.json",
                 "skills/video-theme-library/assets/prompt-motion/index.json",
                 "skills/photo-ambient-effects/assets/sun-rays.js",
                 "skills/photo-ambient-effects/assets/lens-flare.js"):
        path = bundle / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("bundled " + Path(name).name, encoding="utf-8")
    monkeypatch.setattr(resources, "__file__", str(package / "effect_library" / "resources.py"))
    gsap = tmp_path / "gsap.js"
    gsap.write_text("gsap", encoding="utf-8")
    seen = {}
    def fake_render(project, output, **kwargs):
        seen["sun"] = (Path(project) / "sun-rays.js").read_text(encoding="utf-8")
        seen["flare"] = (Path(project) / "lens-flare.js").read_text(encoding="utf-8")
        return output
    monkeypatch.setattr(render, "render_project", fake_render)
    effect_preview.render_preview({"outputs": {"long": True, "short": False}, "_gsap_bytes": b"gsap"}, str(tmp_path))
    assert seen == {"sun": "bundled sun-rays.js", "flare": "bundled lens-flare.js"}


def test_preview_rejects_tampered_seed_before_renderer(tmp_path, monkeypatch):
    import pytest
    from video_studio.templates import effect_preview
    root = tmp_path / "root"
    assets = root / "skills" / "photo-ambient-effects" / "assets"
    assets.mkdir(parents=True)
    (assets / "sun-rays.js").write_text("malicious replacement", encoding="utf-8")
    (assets / "lens-flare.js").write_text("other", encoding="utf-8")
    monkeypatch.setattr(effect_preview.resources, "resource_root", lambda: root)
    monkeypatch.setattr(render, "PREVIEW_GSAP_SHA256", hashlib.sha256(b"gsap").hexdigest())
    monkeypatch.setattr(render, "render_project", lambda *a, **k: pytest.fail("tampered seed reached renderer"))
    with pytest.raises(render.ContractError, match="SHA-256"):
        effect_preview.render_preview({"outputs": {"long": True, "short": False}, "_gsap_bytes": b"gsap"}, str(tmp_path))


def test_preview_rejects_junction_assets_directory(tmp_path, monkeypatch):
    import os
    import subprocess
    import pytest
    if os.name != "nt":
        pytest.skip("Windows native handle verification")
    from video_studio.templates import effect_preview
    root = tmp_path / "root"
    parent = root / "skills" / "photo-ambient-effects"
    parent.mkdir(parents=True)
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "sun-rays.js").write_text("not a local seed", encoding="utf-8")
    (outside / "lens-flare.js").write_text("not a local seed", encoding="utf-8")
    link = parent / "assets"
    env = dict(os.environ, EFFECT_TEST_LINK=str(link), EFFECT_TEST_TARGET=str(outside))
    result = subprocess.run(["powershell", "-NoProfile", "-Command", "New-Item -ItemType Junction -Path $env:EFFECT_TEST_LINK -Target $env:EFFECT_TEST_TARGET | Out-Null"], env=env, capture_output=True, timeout=20)
    if result.returncode:
        pytest.skip("Windows junction setup unavailable")
    monkeypatch.setattr(effect_preview.resources, "resource_root", lambda: root)
    monkeypatch.setattr(render, "PREVIEW_GSAP_SHA256", hashlib.sha256(b"gsap").hexdigest())
    monkeypatch.setattr(render, "render_project", lambda *a, **k: pytest.fail("junction reached renderer"))
    try:
        with pytest.raises(render.ContractError, match="c000050b"):
            effect_preview.render_preview({"outputs": {"long": True, "short": False}, "_gsap_bytes": b"gsap"}, str(tmp_path))
    finally:
        os.rmdir(link)


def test_seed_file_cannot_be_replaced_during_read(tmp_path, monkeypatch):
    import os
    import pytest
    if os.name != "nt":
        pytest.skip("Windows native handle verification")
    from video_studio.effect_library import _native_windows as native
    from video_studio.templates import effect_preview
    root = tmp_path / "root"
    assets = root / "skills" / "photo-ambient-effects" / "assets"
    assets.mkdir(parents=True)
    for name in ("sun-rays.js", "lens-flare.js"):
        (assets / name).write_bytes(name.encode())
    replacement = assets / "replacement.js"
    replacement.write_bytes(b"replacement")
    monkeypatch.setattr(effect_preview.resources, "resource_root", lambda: root)
    monkeypatch.setattr(effect_preview, "PREVIEW_ASSET_HASHES", {
        name: hashlib.sha256(name.encode()).hexdigest()
        for name in ("sun-rays.js", "lens-flare.js")
    })
    original_read = native.read_all
    attempted = []
    def read_while_replacing(handle, limit):
        payload = original_read(handle, limit)
        if not attempted:
            with pytest.raises(PermissionError):
                os.replace(replacement, assets / "sun-rays.js")
            attempted.append(True)
        return payload
    monkeypatch.setattr(native, "read_all", read_while_replacing)
    assert effect_preview._read_preview_assets()["sun-rays.js"] == b"sun-rays.js"
    assert attempted == [True]


def test_preview_seed_no_recall_failure_never_falls_back(tmp_path, monkeypatch):
    import os
    import pytest
    if os.name != "nt":
        pytest.skip("Windows native handle verification")
    from video_studio.effect_library import _native_windows as native
    from video_studio.templates import effect_preview
    monkeypatch.setattr(effect_preview.resources, "resource_root", lambda: tmp_path)
    monkeypatch.setattr(native, "open_root", lambda p: 1)
    monkeypatch.setattr(native, "open_directory", lambda h, n: (_ for _ in ()).throw(OSError("offline or reparse")))
    monkeypatch.setattr(native, "open_file", lambda *a: pytest.fail("must not fall back after no-recall failure"))
    monkeypatch.setattr(native, "close", lambda h: None)
    with pytest.raises(render.ContractError, match="offline or reparse"):
        effect_preview._read_preview_assets()


def test_preview_render_passes_npm_offline_to_child(tmp_path, monkeypatch):
    from video_studio import _env
    seen = {}
    monkeypatch.setattr(_env, "npx_exe", lambda: "npx")
    def fake_subprocess(argv, **kwargs):
        seen.update(kwargs["env"])
    monkeypatch.setattr(render.subprocess, "run", fake_subprocess)
    render.render_project(str(tmp_path), "preview.mp4", offline=True)
    assert seen["npm_config_offline"] == "true"


def test_gsap_is_read_using_no_recall_native_handle(tmp_path, monkeypatch):
    import os
    import pytest
    if os.name != "nt":
        pytest.skip("Windows native handle verification")
    from video_studio.effect_library import _native_windows as native
    gsap = tmp_path / "gsap.js"
    expected = b"fixture"
    monkeypatch.setattr(render, "PREVIEW_GSAP_SHA256", hashlib.sha256(expected).hexdigest())
    opened = []
    monkeypatch.setattr(native, "open_root", lambda p: opened.append(("root", p)) or 1)
    monkeypatch.setattr(native, "open_file", lambda h, n: opened.append(("file", h, n)) or 2)
    monkeypatch.setattr(native, "read_all", lambda h, limit: opened.append(("read", h, limit)) or expected)
    monkeypatch.setattr(native, "close", lambda h: opened.append(("close", h)))
    assert render._read_preview_gsap(str(gsap)) == expected
    assert opened == [("root", str(tmp_path)), ("file", 1, "gsap.js"), ("read", 2, render.PREVIEW_GSAP_MAX_BYTES), ("close", 2), ("close", 1)]


def test_gsap_no_recall_failure_does_not_fallback_to_path(tmp_path, monkeypatch):
    import os
    import pytest
    if os.name != "nt":
        pytest.skip("Windows native handle verification")
    from video_studio.effect_library import _native_windows as native
    monkeypatch.setattr(native, "open_root", lambda p: 1)
    monkeypatch.setattr(native, "open_file", lambda h, n: (_ for _ in ()).throw(OSError("offline or reparse")))
    monkeypatch.setattr(native, "close", lambda h: None)
    with pytest.raises(render.ContractError, match="offline or reparse"):
        render._read_preview_gsap(str(tmp_path / "file.js"))


def test_gsap_file_close_error_is_contract_error_and_root_is_closed(tmp_path, monkeypatch):
    import os
    import pytest
    if os.name != "nt":
        pytest.skip("Windows native handle verification")
    from video_studio.effect_library import _native_windows as native
    closed = []
    monkeypatch.setattr(native, "open_root", lambda p: 1)
    monkeypatch.setattr(native, "open_file", lambda h, n: 2)
    monkeypatch.setattr(native, "read_all", lambda h, limit: b"fixture")
    def close(h):
        closed.append(h)
        if h == 2:
            raise OSError("injected close failure")
    monkeypatch.setattr(native, "close", close)
    with pytest.raises(render.ContractError, match="injected close failure"):
        render._read_preview_gsap(str(tmp_path / "file.js"))
    assert closed == [2, 1]
