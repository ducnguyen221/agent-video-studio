---
title: News video v2 — infographic design direction
status: reference
applies_to: video_studio/templates/news
---

# News video v2 — hướng thiết kế infographic

Đưa template bản tin từ kiểu **"tiêu đề + gạch đầu dòng + 2–3 ảnh web"** sang kiểu
**infographic / SmartArt**: nhiều nhất **1–2 ảnh liên quan trực tiếp**, phần còn lại là đồ hoạ
thông tin dựng bằng HTML/CSS/SVG, kèm **transcript chạy dưới đáy khung**.

Mockup xem được: `video_studio/templates/news/news_v2_components.html` (mở qua HTTP,
1280×720/khung).

---

## 1. Sáu nguyên tắc

1. **Eyebrow pill → tiêu đề đậm → một dòng mô tả.** Mỗi khối một ý; phân cấp rõ.
2. **Một ý = một card.** Thay đoạn văn bằng card "icon + nhãn accent + giá trị". Đoạn văn dài
   trên khung hình là chữ không ai đọc kịp.
3. **Mã màu theo hạng mục** (cyan / violet / pink / blue / green / gold) — dễ phân biệt, sống
   trên nền đen.
4. **Số to làm tâm điểm:** vốn gọi, phần trăm, điểm benchmark, ngày ra mắt.
5. **Card so sánh (versus)** cho tin "A vs B"; **timeline / steps** cho quy trình, lộ trình.
6. **Khoảng trắng rộng, bo góc lớn, viền mảnh + glow nhẹ, lưới nền mờ.** Gradient chỉ dùng
   trên vài từ khoá.

## 2. Design token

| Token | Giá trị |
|---|---|
| Nền | `#0A0A0F` (radial glow ở 78% top) + lưới mờ 64 px |
| Panel / viền | `#1A1A24` / `#2A2A3A` |
| Chữ | `#F0F0F5` · phụ `#A0A0B0` · mờ `#6B6B7B` |
| Accent (xoay vòng) | cyan `#00E5FF`, violet `#A78BFA`, pink `#F472B6`, blue `#60A5FA`, green `#00E676`, gold `#FFC857` |
| Font | **Inter** 400–900, nạp qua Google Fonts CDN |

Bốn accent đầu là `--ac1..--ac4` trong `:root`; `brand.accent` của spec đè lên chúng.

**Font không được viết cứng trong template.** Mọi template ghi chỗ trống `__FONT__`, và
`render.write_index()` thay bằng `_env.font_stack()` lúc ghi `index.html` — vì font sẵn có
khác nhau giữa Windows và macOS, và vì `VIDEO_FONT` phải đổi được mà không sửa mã.

## 3. Thư viện component (mỗi tin chọn ĐÚNG một layout)

| Layout | Dùng khi | Dữ liệu spec phải cấp |
|---|---|---|
| **stat** (số to + hàng thông số) | tin có một con số chủ đạo | `big`, `big_label`, `rows:[{icon,label,value}]` |
| **pillars** (3–4 card icon+title+desc) | "N điểm / tính năng mới" | `items:[{icon,title,desc}]` |
| **process** (bước đánh số + mũi tên) | quy trình, lộ trình, chuỗi sự kiện | `steps:[{title,desc}]` |
| **vs** (hai cột thuộc tính) | so sánh A với B | `a`, `b`, `rows:[{key,a,b}]` |
| **bars** (thanh CSS, không cần thư viện) | xếp hạng, điểm số | `series:[{name,pct,color}]` |
| **quote** (trích dẫn lớn) | phát ngôn, nhận định | `quote`, `who` |
| **cover** (chữ gradient + eyebrow) | mở đầu / kết | sẵn có |

Tất cả dựng bằng HTML/CSS thuần trong HyperFrames — **không thêm thư viện chart**. Icon dùng
emoji hoặc SVG inline.

## 4. Ảnh hưởng lên pipeline

**a) Mỗi đoạn tin trong spec thêm:**

```json
{ "headline": "…", "narration": "…",
  "layout": "stat|pillars|process|vs|bars|quote",
  "data": { "…theo bảng mục 3…" },
  "hero_image": "url-ảnh-liên-quan-nhất",
  "image2": "url-phụ (tuỳ chọn)" }
```

Bước nghiên cứu/tóm tắt phải **phân loại layout**, **xuất data có cấu trúc**, và **chọn một
ảnh liên quan nhất** — xếp theo độ liên quan, không lấy ba ảnh chung chung.

**b) Tải ảnh: tối đa 2.** Chỉ `hero_image` (+ nhiều nhất một ảnh phụ). Ảnh là điểm nhấn ở góc
hoặc phía sau con số, không còn là nội dung chính. Không có ảnh liên quan thì bỏ hẳn — layout
vẫn đầy nhờ infographic.

**c) Dispatcher render:** thay khối "chữ + bullet + ảnh" cố định bằng
`render_block(layout, data, accent)`. Mỗi đoạn xoay một accent.

**d) Transcript dưới đáy khung.** Hai cách:

* (khuyến nghị) burn bằng `ffmpeg` filter `subtitles` từ SRT — cue sinh theo thời lượng từng
  câu trong `_synth_long` — kèm `-filter_complex_threads 1`: thiếu cờ này libass sập.
* hoặc caption-bar HTML animate bằng GSAP theo mốc câu (nặng phần canh thời gian hơn).

**e) Dùng chung cho mọi thương hiệu** qua khối `brand` + token; bản short 9:16 dùng cùng
component, một layout mỗi slide.

## 5. Thứ tự triển khai

1. Thêm token + CSS component vào `_WEEKLY_HEAD` / `_SHORT_HEAD` (giữ nguyên cover, outro).
2. Viết `render_block()` + sáu hàm component, **có đường lùi**: layout sai hoặc thiếu data thì
   quay về `pillars` dựng từ câu narration, để khung không vỡ.
3. Giảm số ảnh + đổi prompt nghiên cứu (xuất `layout` / `data` / `hero_image`).
4. Thêm cue SRT trong `_synth_long` + burn phụ đề ở bước ghép.
5. Render thử một số báo, so v1 với v2, tinh chỉnh khoảng cách (số to đừng đè mô tả; ảnh
   accent đừng đè chữ).
