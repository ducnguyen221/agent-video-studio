---
name: hyperframes
description: Mandatory entry point for any request to make, create, edit, animate or render a video, animation or motion graphic with HyperFrames - promo, explainer, captioned clip, title card, overlay, slideshow, Remotion port or any HyperFrames HTML composition. Also use to inspect, diagnose, validate, preview, publish or batch-render an existing project. Reads project state first, captures intent, then routes to exactly one owning workflow skill and leaves. Not for editing real footage by transcript (use video-edit) and not for picking a news layout (use video-theme-library).
---

# HyperFrames — cửa vào duy nhất

> **Nguồn:** `heygen-com/hyperframes` · `skills/hyperframes/SKILL.md` @ **v0.8.51** · Apache-2.0 ·
> hash manifest `05525e9c53582e4b` (26 file upstream).
> Bản này **đã dịch, rút gọn và biên tập lại** (Apache-2.0 §4(b) — ghi chú "đã sửa"), không phải
> bản sao nguyên văn. Thư mục `references/` của upstream **không** chép vào repo này; cần chi tiết
> thì đọc thẳng upstream đúng bản ghi trong `upstream.json`.

## Skill này làm gì

Nó **không dựng video**. Nó làm ba việc rồi đứng sang một bên:

1. **Đọc trạng thái project trước đã.** Có `hyperframes.json` trong thư mục làm việc không? Có
   `index.html`, có sub-composition nào đang dở không? Dựng lại từ đầu một project đang có là cách
   xoá việc của người khác nhanh nhất.
2. **Chốt ý định** khi yêu cầu còn mơ hồ — đầu vào là gì (URL trang web, pull request, file nhạc,
   footage có sẵn, một đoạn văn bản), đầu ra là gì (MP4, overlay trong suốt, deck bấm được).
3. **Định tuyến đúng MỘT workflow** rồi giao việc cho nó. Định tuyến xong thì rời đi, không vừa
   định tuyến vừa tự làm.

## Bảng định tuyến

| Đầu vào / yêu cầu | Đi tới |
|---|---|
| Video có mặt người nói, cần **phụ đề** | `embedded-captions` |
| Video có mặt người nói, cần **card đồ hoạ chồng lên** (lower-third, trích dẫn, số liệu) | `talking-head-recut` |
| Một đoạn văn bản / bài viết / chủ đề, **không có footage** | `faceless-explainer` |
| URL sản phẩm hoặc trang marketing | `product-launch-video` |
| Một pull request trên GitHub | `pr-to-video` |
| Một bản nhạc, cần cắt theo nhịp | `music-to-video` |
| Đơn vị motion ngắn (< 10 s), không lời đọc | `motion-graphics` |
| Deck bấm được, có slide rời | `slideshow` |
| Có sẵn mã nguồn Remotion, muốn chuyển sang HTML | `remotion-to-hyperframes` |
| Không khớp cái nào, hoặc nhiều cảnh tự do | `general-video` |

Bản tin hằng ngày của repo này **không** đi qua bảng trên: nó đã có template cố định, xem
`video-theme-library` và `docs/NEWS_V2_DESIGN.md`.

## Kỹ năng theo chủ đề (nạp khi cần, không nạp sẵn)

- `hyperframes-core` — hợp đồng composition: `data-*`, `class="clip"`, track, sub-composition.
  **Đọc trước khi viết dòng HTML đầu tiên.**
- `hyperframes-animation` — mọi thứ về chuyển động, bảy runtime (GSAP là mặc định).
- `hyperframes-creative` — hướng sáng tạo: bảng màu, chữ, nhịp, spec thiết kế.
- `hyperframes-keyframes` — punch-in, zoom, camera move, keyframe an toàn khi tua.
- `hyperframes-audio` — trộn âm thanh đã đặt trong composition.
- `hyperframes-registry` — tìm và cài block/component có sẵn **trước khi** tự viết hiệu ứng.
- `hyperframes-cli` — vòng lặp lệnh: `init → catalog → lint → check → preview → render`.
- `hyperframes-studio` — quy ước timeline để người mở Studio đọc được.
- `media-use` — tìm/sinh nhạc nền, SFX, ảnh, giọng đọc, LUT.
- `figma` — kéo tài sản, token, component từ Figma vào.

## Ba luật của bước định tuyến

1. **Một yêu cầu, một workflow.** Chọn xong thì giao trọn; đừng trộn hai quy trình vào một lượt.
2. **Ghim bản engine.** Mọi lệnh trong cùng một lượt phải chạy cùng một bản HyperFrames — xem
   trước một bản, render một bản khác thì thứ duyệt không phải thứ giao.
3. **Không render khi chưa có người duyệt.** `check` xanh chỉ nói file không sai luật, không nói
   video đúng ý ai.
