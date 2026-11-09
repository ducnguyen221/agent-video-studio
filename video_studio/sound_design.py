"""Local sound-design helpers; no provider audio is downloaded."""
from __future__ import annotations

import hashlib
import json
import math
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ENDPOINT = "https://api.openverse.org/v1/audio/"
MAX_BODY = 1_000_000
MAX_ASSET_BYTES = 256 * 1024 * 1024
MAX_CUES = 64
MAX_TEMP_BYTES = 512 * 1024 * 1024


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("Openverse redirect refused")


def search_openverse(query: str, *, page: int = 1, timeout: float = 10):
    """Search public metadata only. Caller must remove private information from query."""
    if not query.strip() or len(query) > 200 or not 1 <= page <= 5 or not 0 < timeout <= 15:
        raise ValueError("invalid query, page or timeout")
    url = ENDPOINT + "?" + urllib.parse.urlencode({"q": query, "page": page, "page_size": 20})
    req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "agent-video-studio/1"})
    try:
        with urllib.request.build_opener(_NoRedirect()).open(req, timeout=timeout) as response:
            data = response.read(MAX_BODY + 1)
    except urllib.error.HTTPError as exc:
        raise ValueError(f"Openverse HTTP {exc.code}") from exc
    except urllib.error.URLError as exc:
        raise ValueError("Openverse network error") from exc
    except TimeoutError as exc:
        raise ValueError("Openverse timeout") from exc
    if len(data) > MAX_BODY:
        raise ValueError("Openverse response too large")
    result = json.loads(data)
    return [{key: item.get(key) for key in ("id", "title", "creator", "foreign_landing_url", "license", "license_version", "license_url", "attribution")} for item in result.get("results", [])]


def asset_revision(asset: dict) -> str:
    """Fingerprint the exact rights and bytes presented when a cue was approved."""
    fields = ("id", "path", "sha256", "purpose", "source_type", "source_evidence", "creator", "license", "license_version", "license_url", "rights_confirmation", "attribution_required", "attribution", "rights_status")
    payload = {key: asset.get(key) for key in fields}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest()


def approved_cues(project: Path, cues: list, assets: list):
    """Return approved cues only after checking local WAV, rights and frozen bytes."""
    if len(cues) > MAX_CUES:
        raise ValueError("too many cues")
    root = Path(project).resolve(strict=True)
    index = {a["id"]: a for a in assets}
    if len(index) != len(assets):
        raise ValueError("duplicate asset id")
    seen = set()
    approved = []
    for cue in cues:
        ident = cue["id"]
        if ident in seen:
            raise ValueError("duplicate cue id")
        seen.add(ident)
        if cue.get("status") != "approved":
            continue
        asset = index[cue["asset_id"]]
        if cue.get("asset_revision") != asset_revision(asset):
            raise ValueError("asset rights or bytes changed since cue approval")
        if asset.get("rights_status") not in ("verified", "attributed"):
            raise ValueError("asset rights not verified")
        if not all(isinstance(asset.get(k), str) and asset[k].strip() for k in ("purpose", "creator", "sha256")):
            raise ValueError("missing rights evidence")
        if not isinstance(asset.get("attribution_required"), bool):
            raise ValueError("attribution requirement unknown")
        if asset.get("source_type", "openverse") == "user_provided":
            if not all(isinstance(asset.get(k), str) and asset[k].strip() for k in ("source_evidence", "rights_confirmation")):
                raise ValueError("missing user-provided rights confirmation")
        elif asset.get("source_type", "openverse") == "openverse":
            if not all(isinstance(asset.get(k), str) and asset[k].strip() for k in ("source_evidence", "license", "license_version", "license_url")):
                raise ValueError("missing rights evidence")
            for key in ("source_evidence", "license_url"):
                parsed = urllib.parse.urlsplit(asset[key].strip())
                if parsed.scheme not in ("http", "https") or not parsed.hostname or parsed.username or parsed.password:
                    raise ValueError("invalid evidence URL")
            license_name = asset["license"].strip().lower()
            if license_name not in ("cc0", "cc-by", "cc-by-sa", "by", "by-sa"):
                raise ValueError("unsupported license; review separately")
            if license_name != "cc0" and not asset["attribution_required"]:
                raise ValueError("license requires attribution")
        else:
            raise ValueError("unsupported source type")
        if asset.get("attribution_required") and (asset.get("rights_status") != "attributed" or not isinstance(asset.get("attribution"), str) or not asset["attribution"].strip()):
            raise ValueError("missing attribution")
        name = asset["path"]
        if not isinstance(name, str) or name.startswith(("/", "\\")) or ":" in name:
            raise ValueError("asset path must be local and relative")
        path = (root / name).resolve(strict=True)
        if not path.is_relative_to(root) or not path.is_file():
            raise ValueError("asset outside project or not regular file")
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            header = stream.read(12)
            if len(header) < 12 or header[:4] != b"RIFF" or header[8:12] != b"WAVE":
                raise ValueError("only local RIFF WAV assets accepted")
            digest.update(header)
            size = len(header)
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                size += len(chunk)
                if size > MAX_ASSET_BYTES:
                    raise ValueError("asset too large")
                digest.update(chunk)
        if digest.hexdigest() != asset["sha256"]:
            raise ValueError("asset changed after approval")
        for key in ("timeline_seconds", "in_seconds", "duration_seconds"):
            value = cue[key]
            if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value) or value < 0:
                raise ValueError("invalid cue timing")
        if cue["duration_seconds"] <= 0:
            raise ValueError("empty cue")
        approved.append((cue, path))
    return approved


def escape_provider_text(value: str) -> str:
    """Escape provider text before embedding in HTML or Markdown containing HTML."""
    import html
    return html.escape(value, quote=True).replace("\\", "&#92;").replace("[", "&#91;").replace("]", "&#93;").replace("(", "&#40;").replace(")", "&#41;").replace("`", "&#96;").replace("*", "&#42;").replace("_", "&#95;")


def mix_mux(project, video, master, output, cues, assets, *, ffmpeg="ffmpeg", ffprobe="ffprobe"):
    """Mux an approved WAV cue mix onto rendered video, without modifying inputs.

    Input video and master must be trusted local files. SFX is copied into a private
    temporary directory and its copied bytes are rechecked before ffmpeg sees them.
    The output must not exist. Listening and rights verification remain manual.
    """
    import os
    import subprocess
    import tempfile
    import wave

    root = Path(project).resolve(strict=True)
    video = Path(video).resolve(strict=True)
    master = Path(master).resolve(strict=True)
    output = Path(output).absolute()
    if not output.parent.resolve(strict=True).is_relative_to(root):
        raise ValueError("output must be within project")
    if not video.is_relative_to(root) or not master.is_relative_to(root) or not video.is_file() or not master.is_file() or output.exists() or output in (video, master):
        raise ValueError("invalid input or existing output")
    with video.open("rb") as stream:
        if stream.read(8)[4:8] != b"ftyp":
            raise ValueError("video must be local MP4")
    with master.open("rb") as stream:
        header = stream.read(12)
        if header[:4] != b"RIFF" or header[8:12] != b"WAVE":
            raise ValueError("master must be local WAV")
    selected = approved_cues(root, cues, assets)
    by_id = {a["id"]: a for a in assets}
    def wav_duration(path):
        try:
            with wave.open(str(path), "rb") as reader:
                frames, rate = reader.getnframes(), reader.getframerate()
                frame_bytes = reader.getnchannels() * reader.getsampwidth()
                remaining = frames
                while remaining:
                    count = min(remaining, 65536)
                    if len(reader.readframes(count)) != count * frame_bytes:
                        raise ValueError("truncated PCM WAV")
                    remaining -= count
                return frames / rate
        except (wave.Error, EOFError, ZeroDivisionError) as exc:
            raise ValueError("invalid PCM WAV") from exc

    master_duration = wav_duration(master)
    probe = subprocess.run([ffprobe, "-v", "error", "-protocol_whitelist", "file,pipe", "-f", "mov", "-select_streams", "v:0", "-show_entries", "stream=duration,avg_frame_rate", "-of", "json", str(video)], check=True, timeout=30, capture_output=True)
    info = json.loads(probe.stdout)["streams"][0]
    video_duration = float(info["duration"])
    numerator, denominator = (int(part) for part in info["avg_frame_rate"].split("/"))
    if numerator <= 0 or denominator <= 0 or not math.isfinite(video_duration):
        raise ValueError("invalid video duration or frame rate")
    frame = denominator / numerator
    if abs(video_duration - master_duration) > frame + 0.001:
        raise ValueError("video and master durations differ by more than one frame")
    for cue, path in selected:
        if cue["in_seconds"] + cue["duration_seconds"] > wav_duration(path) + 1e-6:
            raise ValueError("cue exceeds asset duration")
        if cue["timeline_seconds"] + cue["duration_seconds"] > min(master_duration, video_duration) + 1e-6:
            raise ValueError("cue exceeds master or video duration")
    duck_events = []
    for cue, _ in selected:
        duck = cue.get("ducking_db", 0)
        if not isinstance(duck, (int, float)) or isinstance(duck, bool) or not math.isfinite(duck) or not -60 <= duck <= 0:
            raise ValueError("invalid ducking")
        duck_events.extend(((cue["timeline_seconds"], 1, duck), (cue["timeline_seconds"] + cue["duration_seconds"], 0, -duck)))
    total_duck = 0
    for _, _, change in sorted(duck_events):
        total_duck += change
        if total_duck < -60:
            raise ValueError("overlapping ducking exceeds -60 dB")
    with tempfile.TemporaryDirectory(prefix="video-sfx-") as temp:
        copied = []
        total_size = 0
        for number, (cue, path) in enumerate(selected):
            dest = Path(temp) / f"{number}.wav"
            digest = hashlib.sha256()
            size = 0
            with path.open("rb") as stream, dest.open("xb") as target:
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    size += len(chunk)
                    total_size += len(chunk)
                    if size > MAX_ASSET_BYTES or total_size > MAX_TEMP_BYTES:
                        raise ValueError("asset or temporary total too large")
                    digest.update(chunk)
                    target.write(chunk)
            if digest.hexdigest() != by_id[cue["asset_id"]]["sha256"]:
                raise ValueError("asset changed while copying")
            copied.append((cue, dest))
        args = [ffmpeg, "-nostdin", "-v", "error", "-y", "-protocol_whitelist", "file,pipe", "-f", "mov", "-i", str(video), "-protocol_whitelist", "file,pipe", "-f", "wav", "-i", str(master)]
        for _, path in copied:
            args += ["-protocol_whitelist", "file,pipe", "-f", "wav", "-i", str(path)]
        filters = []
        master_label = "[1:a]"
        for number, (cue, _) in enumerate(copied, 2):
            gain = cue.get("gain_db", 0)
            if not isinstance(gain, (int, float)) or isinstance(gain, bool) or not math.isfinite(gain) or not -96 <= gain <= 12:
                raise ValueError("invalid gain")
            delay = round(cue["timeline_seconds"] * 1000)
            duration = cue['duration_seconds']
            fade_in, fade_out = cue.get('fade_in', 0), cue.get('fade_out', 0)
            if any(not isinstance(v, (int, float)) or isinstance(v, bool) or not math.isfinite(v) or v < 0 or v > duration for v in (fade_in, fade_out)):
                raise ValueError("invalid fade")
            fades = f",afade=t=in:st=0:d={fade_in}" if fade_in else ""
            fades += f",afade=t=out:st={duration-fade_out}:d={fade_out}" if fade_out else ""
            filters.append(f"[{number}:a]atrim=start={cue['in_seconds']}:duration={duration},asetpts=PTS-STARTPTS,volume={gain}dB{fades},adelay={delay}:all=1[s{number}]")
            duck = cue.get('ducking_db', 0)
            if not isinstance(duck, (int, float)) or isinstance(duck, bool) or not math.isfinite(duck) or not -60 <= duck <= 0:
                raise ValueError("invalid ducking")
            if duck:
                start = cue['timeline_seconds']
                end = start + duration
                ramp = min(.05, duration / 2)
                factor = 10 ** (duck / 20)
                expression = f"if(lt(t,{start}),1,if(lt(t,{start+ramp}),1-(1-{factor})*(t-{start})/{ramp},if(lt(t,{end-ramp}),{factor},if(lt(t,{end}),{factor}+(1-{factor})*(t-{end-ramp})/{ramp},1))))"
                filters.append(f"{master_label}volume='{expression}':eval=frame[m{number}]")
                master_label = f"[m{number}]"
        inputs = master_label + "".join(f"[s{n}]" for n in range(2, len(copied) + 2))
        filters.append(f"{inputs}amix=inputs={len(copied)+1}:duration=first:normalize=0[mix]")
        credits = []
        for asset_id in dict.fromkeys(cue["asset_id"] for cue, _ in selected):
            asset = by_id[asset_id]
            if asset["attribution_required"]:
                if asset.get("source_type", "openverse") == "user_provided":
                    parts = (asset['creator'], asset['attribution'])
                else:
                    parts = (asset['creator'], asset['attribution'], asset['source_evidence'], asset.get('license', ''), asset.get('license_version', ''), asset.get('license_url', ''))
                credits.append(" | ".join(str(part).strip() for part in parts if str(part).strip()))
        if sum(len(line) for line in credits) > 16000:
            raise ValueError("credit metadata too large")
        fd, temporary = tempfile.mkstemp(prefix=".sound-mix-", suffix=".mp4", dir=output.parent)
        os.close(fd)
        args += ["-filter_complex", ";".join(filters), "-map", "0:v:0", "-map", "[mix]", "-c:v", "copy", "-c:a", "aac", "-metadata", "comment=" + "\n".join(credits), temporary]
        try:
            subprocess.run(args, check=True, timeout=120, capture_output=True)
            os.link(temporary, output)
        finally:
            os.unlink(temporary)
    return output
