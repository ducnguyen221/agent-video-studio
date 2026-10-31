"""spec.py — hợp đồng DỮ LIỆU của `video-studio render`: một file JSON tả trọn một số báo.

`schema_version` = 1. Thân nội dung GIỮ NGUYÊN khuôn sidecar cũ (`*-top.json`) để bản cũ chỉ
cần thêm bốn khối là chạy được:

    {
      "schema_version": 1,
      "brand":   {"a", "b", "site", "accent"?, "logo"?, "pronounce"?, …},
      "voice":   {"profile"?, "speed"?, "seed"?},
      "bgm":     {"style"} | {"style": null} | "none",
      "outputs": {"long": true|"<tên file>", "short": true|false|"<tên file>"},

      // … phần nội dung y như sidecar cũ:
      "top_story": {...} | "daily_video": {...} | "weekly_video": {...} | "segments": [...],
      "date", "display_date", "week", "range", "verdict", "repo", "scenes", "epi"
    }

Vì sao `brand` BẮT BUỘC: bản pipeline cũ có sẵn tên thương hiệu và tên miền ngay trong mã, nên
quên khai brand vẫn ra video — mang danh tính của người khác. Ở đây thiếu `brand` là **mã 2**
(hợp đồng sai), không có đường lùi im lặng.

`brand.pronounce` = bảng {mẫu regex: cách đọc} cho bước chuẩn hoá trước TTS — chỗ trước đây
là một `re.sub` đường cứng cho đúng một tên miền.
"""
import json
import os
import re

from . import _paths
from .contract import ContractError

SCHEMA_VERSION = 1
REQUIRED_BRAND = ("a", "b", "site")
BRAND_KEYS_TEXT = ("a", "b", "site", "logo", "kicker", "tagline", "tagline_short", "welcome",
                   "rank_suffix", "cover_period", "epi", "outro_big", "outro_sub",
                   "outro_big_short", "outro_sub_short")
VOICE_KEYS = ("profile", "speed", "seed")
OUTPUT_KINDS = ("long", "short")

__all__ = ["SCHEMA_VERSION", "REQUIRED_BRAND", "OUTPUT_KINDS", "load", "validate",
           "brand_of", "voice_of", "bgm_of", "outputs_of", "content_of", "apply_images",
           "copy_image_files", "video_obj_of", "scene_list_of"]


def load(path, brand_file=None):
    """Đọc + kiểm một file spec. Lỗi đọc/định dạng/thiếu khoá đều là ContractError (mã 2).

    `brand_file` được trộn vào TRƯỚC khi kiểm, nên một file brand riêng có thể cấp đủ khối
    `brand` cho một spec chưa có — đúng cảnh dùng lại một spec cho nhiều kênh.
    """
    if not path:
        raise ContractError("thiếu --input <spec.json>")
    if not os.path.isfile(path):
        raise ContractError(f"không có file spec: {path}")
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
    except ValueError as e:
        raise ContractError(f"{path}: JSON hỏng — {e}") from e
    if not isinstance(data, dict):
        raise ContractError(f"{path}: spec phải là một object JSON")
    return validate(data, origin=path, brand_file=brand_file)


def _merge_brand_file(data, brand_file):
    if not brand_file:
        return data
    if not os.path.isfile(brand_file):
        raise ContractError(f"không có file brand: {brand_file}")
    try:
        with open(brand_file, "r", encoding="utf-8-sig") as f:
            extra = json.load(f)
    except ValueError as e:
        raise ContractError(f"{brand_file}: JSON hỏng — {e}") from e
    if not isinstance(extra, dict):
        raise ContractError(f"{brand_file}: brand phải là một object JSON")
    data = dict(data)
    data["brand"] = {**(data.get("brand") or {}), **extra}
    return data


def validate(data, origin="spec", brand_file=None):
    """-> spec đã kiểm (bản sao). Ném ContractError kèm tên khoá sai."""
    data = _merge_brand_file(data, brand_file)
    ver = data.get("schema_version")
    if ver is None:
        raise ContractError(
            f"{origin}: thiếu \"schema_version\" — spec của video-studio phải khai "
            f"\"schema_version\": {SCHEMA_VERSION}")
    if ver != SCHEMA_VERSION:
        raise ContractError(f"{origin}: schema_version={ver!r}, bản này chỉ đọc "
                            f"{SCHEMA_VERSION}")
    out = dict(data)
    out["brand"] = _validate_brand(data.get("brand"), origin)
    out["voice"] = _validate_voice(data.get("voice"), origin)
    out["bgm"] = _validate_bgm(data.get("bgm"), origin)
    out["outputs"] = _validate_outputs(data.get("outputs"), origin)
    return out


def _validate_brand(brand, origin):
    if brand is None:
        raise ContractError(
            f"{origin}: thiếu khối \"brand\". Engine KHÔNG có thương hiệu mặc định — khai "
            "brand.a, brand.b, brand.site (tên hai phần + nơi đọc/hiện ở outro).")
    if not isinstance(brand, dict):
        raise ContractError(f"{origin}: \"brand\" phải là object")
    missing = [k for k in REQUIRED_BRAND if not str(brand.get(k) or "").strip()]
    if missing:
        raise ContractError(f"{origin}: brand thiếu khoá bắt buộc: {', '.join(missing)}")
    for k in BRAND_KEYS_TEXT:
        if k in brand and brand[k] is not None and not isinstance(brand[k], str):
            raise ContractError(f"{origin}: brand.{k} phải là chuỗi")
    acc = brand.get("accent")
    if acc is not None and not isinstance(acc, (str, list)):
        raise ContractError(f"{origin}: brand.accent phải là chuỗi màu hoặc danh sách màu")
    pron = brand.get("pronounce")
    if pron is not None:
        if not isinstance(pron, dict):
            raise ContractError(f"{origin}: brand.pronounce phải là object {{mẫu: cách đọc}}")
        for pat, rep in pron.items():
            if not isinstance(pat, str) or not isinstance(rep, str):
                raise ContractError(f"{origin}: brand.pronounce chỉ nhận chuỗi → chuỗi")
            try:
                re.compile(pat)
            except re.error as e:
                raise ContractError(f"{origin}: brand.pronounce mẫu {pat!r} không phải regex: {e}") from e
    return dict(brand)


def _validate_voice(voice, origin):
    if voice is None:
        return {}
    if not isinstance(voice, dict):
        raise ContractError(f"{origin}: \"voice\" phải là object {{profile, speed, seed}}")
    unknown = [k for k in voice if k not in VOICE_KEYS]
    if unknown:
        raise ContractError(f"{origin}: voice có khoá lạ: {', '.join(sorted(unknown))}")
    if voice.get("profile") is not None and not isinstance(voice["profile"], str):
        raise ContractError(f"{origin}: voice.profile phải là tên profile (chuỗi)")
    if voice.get("speed") is not None:
        try:
            sp = float(voice["speed"])
        except (TypeError, ValueError):
            raise ContractError(f"{origin}: voice.speed phải là số") from None
        if not 0.5 <= sp <= 2.0:
            raise ContractError(f"{origin}: voice.speed={sp} ngoài khoảng 0.5–2.0")
    if voice.get("seed") is not None and not isinstance(voice["seed"], int):
        raise ContractError(f"{origin}: voice.seed phải là số nguyên (engine giọng KHÔNG tái "
                            "lập nếu không ghim seed)")
    return dict(voice)


def _validate_bgm(bgm, origin):
    if bgm is None or bgm == "none":
        return {"style": None}
    if isinstance(bgm, str):
        return {"style": bgm}
    if not isinstance(bgm, dict):
        raise ContractError(f"{origin}: \"bgm\" phải là {{\"style\": …}} hoặc \"none\"")
    style = bgm.get("style")
    if style is not None and not isinstance(style, str):
        raise ContractError(f"{origin}: bgm.style phải là chuỗi hoặc null")
    if isinstance(style, str) and style.strip().lower() == "none":
        style = None
    out = dict(bgm)
    out["style"] = style
    return out


def _validate_outputs(outputs, origin):
    if outputs is None:
        return {"long": True, "short": True}
    if not isinstance(outputs, dict):
        raise ContractError(f"{origin}: \"outputs\" phải là object {{long, short}}")
    unknown = [k for k in outputs if k not in OUTPUT_KINDS]
    if unknown:
        raise ContractError(f"{origin}: outputs có khoá lạ: {', '.join(sorted(unknown))} "
                            f"(chỉ nhận {', '.join(OUTPUT_KINDS)})")
    out = {}
    for k in OUTPUT_KINDS:
        v = outputs.get(k, True)
        if v is None or v is False:
            out[k] = False
        elif v is True:
            out[k] = True
        elif isinstance(v, str) and v.strip():
            # Luật dùng chung với `templates/news` và `edit --name` — và quan trọng hơn: luật
            # KHÔNG phụ thuộc hệ điều hành. `C:ten.mp4` (ổ đĩa, không dấu ngăn) lọt cả ba
            # phép kiểm hiển nhiên ở đây, rồi `join` vứt luôn `--out`.
            _paths.plain_name(v.strip(), f"{origin}: outputs.{k}",
                              "(thư mục đích do --out quyết định)")
            out[k] = v.strip()
        else:
            raise ContractError(f"{origin}: outputs.{k} phải là true/false hoặc tên file")
    if not any(out.values()):
        raise ContractError(f"{origin}: outputs tắt hết — không có gì để render")
    return out


# ── đọc ra từng phần (bên gọi khỏi lặp `.get`) ──────────────────────────────────────────

def brand_of(spec):
    return dict(spec.get("brand") or {})


def voice_of(spec):
    return dict(spec.get("voice") or {})


def bgm_of(spec):
    """Khối nhạc nền đã chuẩn hoá. Nhận cả spec CHƯA qua `validate` (nơi `bgm` còn là chuỗi):
    bên gọi không phải nhớ mình đang cầm bản nào, và nhầm thì ra mã 2 chứ không phải mã 1."""
    return _validate_bgm(spec.get("bgm"), "bgm")


def outputs_of(spec):
    return dict(spec.get("outputs") or {"long": True, "short": True})


def content_of(spec):
    """Phần nội dung (khuôn sidecar cũ) — mọi khoá không thuộc bốn khối hợp đồng."""
    skip = {"schema_version", "brand", "voice", "bgm", "outputs"}
    return {k: v for k, v in spec.items() if k not in skip}


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


def scene_list_of(data, project):
    """Danh sách cảnh MÀ TEMPLATE của `project` sẽ đọc (cùng đối tượng, để sửa tại chỗ); sai kiểu ⇒ ContractError.

    `repo-today`: `scenes` · `news`/`news-weekly`: `segments` của `daily_video`/`weekly_video`/cấp cao
    nhất · `topstory`: `top_story.sections` (hoặc `story.sections`). Không kiểm từng phần tử.
    """
    if project == "repo-today":
        lst = data.get("scenes")
        if not isinstance(lst, list) or not lst:
            raise ContractError("--images cần spec có danh sách `scenes` (project repo-today)")
    elif project in ("news", "news-weekly"):
        raw = data.get("daily_video") or data.get("weekly_video")
        if raw and not isinstance(raw, dict):
            raise ContractError("spec: `daily_video`/`weekly_video` phải là object")
        vo = video_obj_of(data)
        lst = vo.get("segments")
        if not isinstance(lst, list) or not lst:
            raise ContractError("--images cần spec có danh sách `segments` (project news)")
    elif project == "topstory":
        story = data.get("top_story") or data.get("story")
        if not isinstance(story, dict):
            raise ContractError("spec: `top_story` phải là object có `sections`")
        lst = story.get("sections")
        if not isinstance(lst, list) or not lst:
            raise ContractError("--images cần spec có `top_story.sections` (project topstory)")
    else:
        raise ContractError(f"--images chưa hỗ trợ project {project!r}")
    return lst


# ── ảnh người dùng → cảnh (`render --images`) ───────────────────────────────────────────

IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp")


def _no_dup_keys(pairs):
    """`object_pairs_hook`: khoá trùng trong images.json là lỗi, không để cái sau đè cái trước."""
    out = {}
    for k, v in pairs:
        if k in out:
            raise ValueError(f"khoá trùng {k!r}")
        out[k] = v
    return out


def _read_images_file(images_path):
    try:
        with open(images_path, "r", encoding="utf-8-sig") as f:
            obj = json.load(f, object_pairs_hook=_no_dup_keys)
    except OSError as e:
        raise ContractError(f"không đọc được file ảnh-theo-cảnh {images_path}: {e}") from e
    except ValueError as e:
        raise ContractError(f"{images_path}: JSON hỏng — {e}") from e
    if not isinstance(obj, dict):
        raise ContractError(f"{images_path}: phải là một object JSON")
    if obj.get("schema_version") != SCHEMA_VERSION:
        raise ContractError(f"{images_path}: cần \"schema_version\": {SCHEMA_VERSION} "
                            f"(nhận {obj.get('schema_version')!r})")
    extra = sorted(k for k in obj if k not in ("schema_version", "scenes"))
    if extra:
        raise ContractError(f"{images_path}: khoá lạ: {', '.join(extra)}")
    mapping = obj.get("scenes")
    if not isinstance(mapping, dict) or not mapping:
        raise ContractError(f"{images_path}: cần object {{\"scenes\": {{\"1\": \"anh.png\"}}}}")
    return mapping


_URL_RE = re.compile(r"^https?://", re.I)


def _scene_image(images_path, key, value, base, project):
    """Chuẩn hoá giá trị của MỘT cảnh thành đúng một ảnh: đường tuyệt đối hoặc URL `http(s)://`."""
    where = f"{images_path}: cảnh {key}"
    items = [value] if isinstance(value, str) else value
    if not isinstance(items, list):
        raise ContractError(f"{where}: giá trị phải là chuỗi hoặc danh sách một chuỗi")
    if not items:
        raise ContractError(f"{where}: danh sách ảnh rỗng")
    if len(items) > 1:
        raise ContractError(f"{where}: template chỉ hiện một ảnh mỗi cảnh (nhận {len(items)}); "
                            "nhiều ảnh mỗi cảnh là RQ-003")
    rel = items[0]
    if not isinstance(rel, str) or not rel.strip():
        raise ContractError(f"{where}: ảnh phải là chuỗi đường dẫn hoặc URL")
    if _URL_RE.match(rel):
        if project == "repo-today":
            raise ContractError(f"{where}: repo-today chỉ nhận ảnh cục bộ, không nhận URL")
        return rel
    if not rel.lower().endswith(IMAGE_EXTS):
        raise ContractError(f"{where}: ảnh phải là {'/'.join(IMAGE_EXTS)}")
    src = os.path.normpath(rel if os.path.isabs(rel) else os.path.join(base, rel))
    if not os.path.isfile(src):
        raise ContractError(f"{where}: không có ảnh {src}")
    return src


def apply_images(data, images_path, project):
    """Ghép ảnh vào cảnh theo file `images.json`; mọi lỗi là ContractError (mã 2).

    Định dạng: `{"schema_version": 1, "scenes": {"1": "anh/a.png"}}` — khoá là số cảnh 1-based
    (chỉ chữ số ASCII, không số 0 đầu) trong danh sách cảnh của project (`scene_list_of`); giá trị là
    MỘT ảnh, viết dạng chuỗi hoặc danh sách một chuỗi: ảnh cục bộ (đường tương đối neo vào thư mục
    chứa images.json, đường tuyệt đối và `..` được chấp nhận) hoặc URL `http(s)://` (trừ `repo-today`).
    Ảnh người dùng THAY toàn bộ ảnh/clip spec khai cho cảnh đó; cảnh không có trong file giữ nguyên.
    `repo-today`: `scene["hero_image"] = "img/s<n>_<tên>"` + `data["_image_files"]` (bước dựng chép
    bằng `copy_image_files`); `news`/`news-weekly`: `segment["images"] = [ảnh]` (template tải/chép);
    `topstory`: `section["media"] = [{"type": "image", "src": ảnh}]`. Không bỏ qua im lặng điều gì.
    """
    if not os.path.isfile(images_path):
        raise ContractError(f"không có file ảnh-theo-cảnh: {images_path}")
    mapping = _read_images_file(images_path)
    targets = scene_list_of(data, project)
    base = os.path.dirname(os.path.abspath(images_path))
    files = {}
    for key, value in mapping.items():
        if not re.fullmatch(r"[1-9][0-9]*", key):
            raise ContractError(f"{images_path}: khoá cảnh phải là số nguyên >= 1 viết thường "
                                f"(1, 2, 3…), nhận {key!r}")
        n = int(key)
        if n > len(targets):
            raise ContractError(f"{images_path}: cảnh {n} vượt số cảnh của spec ({len(targets)})")
        img = _scene_image(images_path, n, value, base, project)
        if not isinstance(targets[n - 1], dict):
            raise ContractError(f"spec: cảnh {n} phải là object")
        if project == "repo-today":
            dst = f"img/s{n}_{os.path.basename(img)}"
            files[dst] = img
            targets[n - 1]["hero_image"] = dst
        elif project == "topstory":
            targets[n - 1]["media"] = [{"type": "image", "src": img}]
        else:
            targets[n - 1]["images"] = [img]
    if project == "repo-today":
        data["_image_files"] = files
    return data


def copy_image_files(project_dir, image_files):
    """Chép ảnh đã lên kế hoạch bởi `apply_images` vào `<project>/img/`."""
    import shutil
    for dst, src in (image_files or {}).items():
        dst_path = os.path.join(project_dir, *dst.split("/"))
        os.makedirs(os.path.dirname(dst_path), exist_ok=True)
        shutil.copy2(src, dst_path)
