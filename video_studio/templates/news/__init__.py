"""templates.news — họ template bản tin: recap ngày / recap tuần / deep-dive một tin / repo.

Bốn hàm dưới đây là chỗ `video-studio render` gọi vào. Chúng nhận SPEC đã kiểm (`spec.py`,
`schema_version=1`) và thư mục ra, rồi trả danh sách file đã dựng:

    [{"kind": "long"|"short", "path": "<file>", "duration": <giây|None>}, …]

Chưng cất từ bộ script bản tin chạy thật trong pipeline `.tts`. Ba khác biệt có chủ đích so
với bản gốc:

* **Thương hiệu đến từ spec.** Bản gốc mang sẵn tên thương hiệu và tên miền trong mã, nên
  quên khai vẫn ra video — mang danh tính người khác. Ở đây thiếu `brand` là mã 2.
* **Đường dẫn đến từ trạm.** `projects.ensure()` thay cho đường cứng tới một ổ đĩa Windows.
* **Không chạy tiến trình con qua shell.** Mọi lần gọi HyperFrames đi qua
  `render.render_project`: argv list, bản ghim, có thử lại, stderr luôn vào log.
"""
import os

from ... import _paths
from ...contract import ContractError

#: Lời khuyên riêng của họ template bản tin, nối vào cuối lỗi của `_paths`.
_HINT = ("Dùng dạng ISO \"2026-01-02\" cho \"date\" (dạng đọc cho người để ở "
         "\"display_date\"), và tên file trần cho \"outputs\".")

__all__ = ["render_daily", "render_weekly", "render_topstory", "render_repo_today",
           "video_obj_of", "out_name"]


def _duration(path):
    """Thời lượng video (giây) — None nếu không đo được (thiếu ffprobe chẳng hạn)."""
    try:
        from voice_studio import av
        return round(float(av.video_duration(path)), 2)
    except Exception:          # noqa: BLE001 — đo được thì tốt, không đo được không chặn render
        return None


def _result(kind, path):
    return {"kind": kind, "path": path, "duration": _duration(path)}


def video_obj_of(spec):
    """Object nội dung của bản tin: `daily_video` → `weekly_video` → chính spec (có `segments`)."""
    vo = spec.get("daily_video") or spec.get("weekly_video")
    if not vo and spec.get("segments"):
        vo = spec
    if not vo or not vo.get("segments"):
        raise ContractError(
            "spec không có đoạn tin nào: cần \"daily_video\"/\"weekly_video\" có \"segments\", "
            "hoặc \"segments\" ngay ở cấp cao nhất.")
    return vo


def _plain_name(value, field):
    """Một mảnh TÊN FILE, không phải một đường dẫn.

    `os.path.join(out_dir, "18/09/2026-top.mp4")` không báo lỗi: nó lặng lẽ đẻ ra
    `<out>/18/09/` rồi đặt file ở đó. `--out` khi ấy không còn nghĩa "file nằm ở đây", và
    bên gọi (runner, pipeline) đi tìm ở đúng chỗ mình khai thì không thấy gì. Ngày dạng
    `dd/mm/yyyy` của sidecar cũ rơi đúng vào bẫy này — nên chặn ngay tại chỗ đặt tên.

    Luật nằm ở `_paths.plain_name` (dùng chung với `spec.outputs` và `edit --name`) vì nó
    **phải giống hệt nhau trên mọi hệ điều hành**; ở đây chỉ thêm lời khuyên riêng của
    template bản tin.
    """
    return _paths.plain_name(value, field, _HINT)


def _out_path(out_dir, value, field):
    """Ghép tên đã kiểm vào `--out`, chốt hậu bằng `realpath`."""
    return _paths.join_out(out_dir, value, field, _HINT)


def out_name(spec, kind, default):
    """Tên file cho một đầu ra: `outputs.<kind>` nếu là chuỗi, không thì tên mặc định."""
    v = (spec.get("outputs") or {}).get(kind, True)
    return _plain_name(v, f"outputs.{kind}") if isinstance(v, str) else default


def _wants(spec, kind):
    return bool((spec.get("outputs") or {}).get(kind, True))


def _voice(spec):
    """-> (tên profile hoặc None, prompt clone hoặc None, model). Ghim seed nếu spec có."""
    from voice_studio import engine, profiles
    v = spec.get("voice") or {}
    model = engine.load()
    if v.get("seed") is not None:
        engine.seed_all(v["seed"])
    name = (v.get("profile") or "").strip() or None
    prompt = (profiles.get_clone_prompt(model, name)
              or profiles.get_clone_prompt(model, profiles.ensure_default(model)))
    return name, prompt, model


def _date(spec):
    d = str(spec.get("date") or "").strip()
    if not d:
        raise ContractError("spec thiếu \"date\" (dùng để đặt tên file ra)")
    return _plain_name(d, "date")


# ── bản tin ngày / bản tin tuần ─────────────────────────────────────────────────────────

def _render_recap(spec, out_dir, wording):
    from . import news_video
    vo = video_obj_of(spec)
    date = _date(spec)
    brand = {**wording, **(spec.get("brand") or {})}
    display = spec.get("display_date") or spec.get("range") or ""
    if display:
        brand.setdefault("epi", display)
    week = str(spec.get("week") or "")
    _name, prompt, model = _voice(spec)
    out = []
    if _wants(spec, "long"):
        p = _out_path(out_dir, out_name(spec, "long", f"{date}.mp4"), "outputs.long")
        news_video.make_weekly(vo, p, date, week=week, range_=display, model=model,
                               prompt=prompt, brand=brand)
        out.append(_result("long", p))
    if _wants(spec, "short"):
        p = _out_path(out_dir, out_name(spec, "short", f"{date}-short.mp4"), "outputs.short")
        news_video.make_weekly_short(vo, p, date, week=week, range_=display, model=model,
                                     prompt=prompt, brand=brand)
        out.append(_result("short", p))
    return out


def render_daily(spec, out_dir):
    """Bản tin NGÀY: recap 16:9 + short 9:16.

    `DAILY_WORDING` chỉ đổi cách diễn đạt mốc thời gian ("HÔM NAY" thay "TUẦN NÀY") — không
    mang danh tính, nên nằm trong template chứ không phải trong spec.
    """
    from .daily_hot_video import DAILY_WORDING
    return _render_recap(spec, out_dir, DAILY_WORDING)


def render_weekly(spec, out_dir):
    """Bản tin TUẦN: recap 16:9 + short 9:16 (giữ nguyên cách diễn đạt tuần)."""
    return _render_recap(spec, out_dir, {})


# ── deep-dive một tin ───────────────────────────────────────────────────────────────────

def render_topstory(spec, out_dir):
    """Deep-dive MỘT tin: long 16:9 + short 9:16, lời dẫn bám nhịp từng khối chữ trên màn."""
    from . import top_story_video as ts
    date = _date(spec)
    story = spec.get("top_story") or spec.get("story")
    if not story or not story.get("sections"):
        raise ContractError("spec thiếu \"top_story.sections\"")
    story = dict(story)
    story["_display"] = spec.get("display_date") or ts._vn_display(date)
    if spec.get("verdict") and not story.get("verdict"):
        story["verdict"] = spec["verdict"]
    if spec.get("repo"):
        story["_repo"] = spec["repo"]
    ts._apply_branding(spec.get("brand"))
    _name, prompt, model = _voice(spec)
    # Ảnh/clip tương đối trong spec neo vào THƯ MỤC CHỨA SPEC (như sidecar cũ vẫn làm).
    json_dir = os.path.dirname(os.path.abspath(spec.get("_spec_path") or out_dir))
    out = []
    if _wants(spec, "long"):
        p = _out_path(out_dir, out_name(spec, "long", f"{date}-top.mp4"), "outputs.long")
        ts.make_long(story, p, model, prompt, json_dir)
        out.append(_result("long", p))
    if _wants(spec, "short"):
        p = _out_path(out_dir, out_name(spec, "short", f"{date}-top-short.mp4"), "outputs.short")
        ts.make_short(story, p, model, prompt, json_dir)
        out.append(_result("short", p))
    return out


# ── deep-dive nhiều cảnh (news v2) ──────────────────────────────────────────────────────

def render_repo_today(spec, out_dir):
    """Deep-dive nhiều cảnh từ kịch bản `scenes` (chỉ bản 16:9)."""
    from . import news_v2
    scenes = spec.get("scenes")
    if not scenes:
        raise ContractError("spec thiếu \"scenes\" (danh sách cảnh của bản deep-dive)")
    name, _prompt, _model = _voice(spec)
    epi = spec.get("epi") or spec.get("display_date") or ""
    stem = _plain_name(spec.get("date") or "deep-dive", "date")
    default = out_name(spec, "long", f"{stem}.mp4")
    p = _out_path(out_dir, default, "outputs.long")
    news_v2.render_deepdive(scenes, p, epi=epi, voice_profile=name,
                            brand=spec.get("brand"))
    return [_result("long", p)]
