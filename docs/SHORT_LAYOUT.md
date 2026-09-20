---
title: Vertical short — layout library and assets
status: reference
applies_to: video_studio/templates/news
---

# Bản SHORT dọc 9:16 — thư viện bố cục + asset

Bộ **layout template + asset chuẩn** cho bản short dọc (`top_story_video.make_short` và
`news_video.make_weekly_short`). Mục tiêu của mỗi khung hình: **đầy, đều, đa dạng, đúng
thương hiệu** — không ô trống, không đơn điệu.

## 1. Khung chuẩn một section (1080×1920)

```
 ┌─ thương hiệu (góc trái) ──── ngày/tuần (góc phải) ─┐   y≈64
 │ CHIP "PHẦN n / TOP n"                              │   y≈210
 │ TIÊU ĐỀ section (.hl)                              │   y≈300
 │ ┌── .content (flex column, gap ĐỀU 34px) ───────┐  │   y≈466
 │ │  SmartArt fill-bullet (.salist)               │  │
 │ │  ẢNH lấp khung (.heroimg, object-fit: cover)   │  │
 │ └───────────────────────────────────────────────┘  │   tới y≈1504
 │ PHỤ ĐỀ mức-từ (.cap, 40px)                         │   bottom:150
 │ brand.site                                          │   bottom:54
 └─────────────────────────────────────────────────────┘
```

`.content` là flex column, nên **khoảng cách giữa các khối luôn đều** (card ↔ ảnh); ảnh để
`flex:1` tự lấp phần còn lại. Dòng cuối khung là `brand.site` của spec — không có địa chỉ nào
viết cứng trong template.

## 2. Bộ template bố cục (xoay tự động theo `sec_i % 3`)

| Template | Bố cục | Dùng khi |
|---|---|---|
| **tpl-a** | card TRÊN · ảnh DƯỚI (ảnh `flex:1`) | mặc định; ý chính cần đọc trước |
| **tpl-b** | ảnh TRÊN · card DƯỚI | ảnh mạnh, đại diện rõ |
| **tpl-c** | ảnh TRÊN lớn (`flex:1.7`) · card gọn dưới | ảnh hero đẹp, ít ý |
| (noimg) | card căn giữa, giãn đều | khi không có ảnh nào |

**Thêm template mới:** thêm class `.sec .content.tpl-x` / `.story .content.tpl-x` (đảo `order`,
đổi `flex`) trong `_SHORT_HEAD` của cả hai module, rồi mở rộng vòng xoay `("a","b","c", …)`.

## 3. SmartArt thay cho gạch đầu dòng

Có sẵn: `bullets` (thẻ số — mặc định cho short) · `flow` (quy trình) · `stats` (số liệu to) ·
`versus` (so sánh) · `stack` (tầng). Định nghĩa ở `diagram_html` / `_wk_diagram_html`.

## 4. Ảnh lấp khung — thứ tự ưu tiên

1. **Ảnh nghiên cứu** (`media` trong spec) — đúng chủ đề nhất.
2. **Filler on-brand** trong `<trạm>/projects/<tên>/assets/fillers/` (mục 5).
3. **B-roll Openverse** (tech trừu tượng chung) — chỉ khi hai nguồn trên trống.

## 5. Asset người dùng tự chuẩn bị

* **`assets/fillers/`** — ảnh nền / filler đúng tông thương hiệu (ngang ~16:9 hoặc dọc,
  ≥1280 px, `.jpg` / `.png` / `.webp`). Pipeline **xoay vòng** dùng khi một section thiếu ảnh
  nghiên cứu. Nên là ảnh trừu tượng / đồ hoạ tech hợp tông tối: không chữ to, không watermark.
* **`assets/fillers/<pool>/`** — pool riêng cho một kênh; chọn bằng `brand.filler_pool` trong
  spec. Không có pool đó thì rơi về `assets/fillers/` chung. (Bản tiền thân chọn pool bằng một
  biến môi trường riêng của một pipeline — nay là một khoá của spec như mọi thứ khác.)

Ảnh **mẫu tham khảo** (ảnh chụp giao diện của người khác, dùng để bàn về gu thiết kế) **không
nằm trong repo này**: chúng là tác phẩm của bên thứ ba và không cần cho lúc render. Để chúng
trong trạm của bạn.

## 6. Quy trình khi có ảnh mẫu mới

1. Bỏ ảnh tham khảo vào thư mục tham khảo của trạm, ảnh dùng-thật vào `assets/fillers/`.
2. Agent xem ảnh tham khảo → chỉnh hoặc thêm template cho khớp gu → nếu cần thì tạo thêm
   filler đồ hoạ đúng tông vào `assets/fillers/`.
3. Render thử một short → soi khung → tinh chỉnh gap và tỉ lệ template.

---

## 7. Hướng đi tiếp: storyboard spec + style playbook

Phần này là **thiết kế, chưa phải thứ đã dựng**. Ý tưởng: agent tự lên ý tưởng → chọn bố cục,
asset, slide → xuất ra một spec cho HyperFrames dựng, và nhịp bám tốc độ đọc.

### a) Style playbook (YAML) — "gu khung" để agent chọn

```yaml
identity: {name, mood, pace, best_for}
visual_language:
  color_palette: {primary[], accent[], background, text, muted}   # = --ac1..--ac4
  composition: "flat | depth | glass"
typography:
  headings: {font: Inter, weight: 900}
  body / stat_card / code: {…}
  weight_matrix: {title, heading, body, caption}
motion:
  pacing_rules:                     # KHỚP tốc độ đọc
    min_scene_hold_seconds / max_scene_hold_seconds
    text_card_hold_seconds / stat_card_hold_seconds
    transition_duration_seconds
  transitions: [fade, slide, wipe]
overlays:
  stat_card: {bg, border, radius, shadow}
  key_term:  {bg, text, radius}     # tag pill
  code_block:{bg, text, highlight}
quality_rules: ["≤ 4 màu mỗi khung", "tương phản ≥ 4.5:1", …]
```

Renderer đọc playbook → nhét vào `:root` CSS + nhịp. Đây là cách "đa dạng có kỷ luật": agent
được chọn, nhưng chọn trong một bộ đã duyệt.

### b) Scene plan (storyboard JSON) — agent sinh, renderer diễn giải

```jsonc
{ "version": "1.0", "style_playbook": "<tên playbook>", "scenes": [
  { "id": "s1", "layout": "tpl-b",
    "component": "stat-card|fill-bullet|tags|process|versus|code|image-hero",
    "title": "…", "points": [ … ], "data": [ … ],
    "media": {"src": "…", "relevance": "direct|descriptive"},
    "narration_short": "…", "transition_in": "slide",
    "hero_moment": false, "narrative_role": "deliver_payload" }
] }
```

Renderer map `component` → khối HTML trong `.content` flex + template + beat-sync (mốc ASR) +
karaoke.

### c) Component còn thiếu

| Component | Trạng thái | Nguồn dữ liệu |
|---|---|---|
| fill-bullet (`.sacard`) | có | `points` |
| stat-card (số to) | có | `diagram.stats` |
| key-term tags (pill) | chưa | `points` / từ khoá |
| process-pills (A→B→C) | chưa | `diagram.flow` |
| versus / stack | có (cần scale cho khung dọc) | `diagram` |
| code / terminal mock | chưa | tin về CLI, code |
| image-hero (khung thiết bị) | có ảnh, chưa có khung thiết bị | `media` |

### d) Một ghi chú về nguồn

Kiến trúc "style playbook + scene plan" học từ một dự án cùng dùng HyperFrames nhưng có
license copyleft mạnh: ở đây **chỉ mượn pattern và tự viết lại**, không chép dòng mã nào. Chi
phí thật của hướng này không nằm ở render (vẫn HTML + GSAP) mà ở độ tin cậy của scene plan do
agent sinh — nên phải có schema validate và bước render thử một cảnh trước khi dựng cả bài.
