---
name: hyperframes-creative
description: Non-animation creative direction for HyperFrames videos - design spec handling (frame.md / design.md), palettes, typography, narration, beat planning, audio-reactive visuals, composition patterns, and brand or style decisions. Use before writing HTML, to decide how the piece should look and sound. For atomic motion patterns and scene blueprints use hyperframes-animation instead.
---

# Hướng sáng tạo: chốt cái nhìn trước khi gõ HTML

> **Nguồn:** `heygen-com/hyperframes` · `skills/hyperframes-creative/SKILL.md` @ **v0.8.51** ·
> Apache-2.0 · hash manifest `0803c90800fda4ce` (79 file upstream: ~13 preset khung hình, 9 bảng
> màu, ~17 tài liệu tham chiếu).
> Bản này **đã dịch, rút gọn và biên tập lại** (Apache-2.0 §4(b)); preset và bảng màu của upstream
> **không** chép vào repo — repo này có thư viện riêng ở `docs/THEME-LIBRARY.md`.

## Thứ tự làm việc

1. **Spine của câu chuyện** — ba tới năm nhịp, mỗi nhịp một việc. Viết bằng câu tiếng Việt bình
   thường trước khi nghĩ tới hình.
2. **Spec thiết kế** (`design.md` / `frame.md`) — bảng màu, bộ chữ, cách chia khung, tông. Một file,
   viết một lần, mọi cảnh sau đó bám theo.
3. **Lời đọc trước, hình sau.** Nhịp hình cắt theo lời, không phải ngược lại — nếu không thì chữ
   chạy xong mà người đọc vẫn đang nói dở câu.
4. **Bảng phân cảnh** — mỗi cảnh: làm gì, dài bao lâu, chữ gì trên màn hình, hình gì.
5. Chỉ sau đó mới sang `hyperframes-core` để viết HTML và `hyperframes-animation` để chọn chuyển động.

## Bảng màu và chữ

- **Một hệ màu cho cả video.** Trộn hai hệ là cách nhanh nhất làm video trông như ghép từ hai chỗ.
- Upstream có sẵn chín họ bảng màu (rực rỡ, doanh nghiệp sạch, tối sang, ngọc quý, đơn sắc, đất,
  neon, pastel, biên tập ấm). Repo này có hệ màu riêng theo thương hiệu, khai qua spec — **màu
  không bao giờ ghi cứng trong template**.
- Chữ: tối đa hai bộ chữ, một cho tiêu đề một cho thân. Cỡ chữ nhỏ nhất trên khung 9:16 phải đọc
  được trên màn hình điện thoại cầm tay, không phải trên màn hình bạn đang ngồi.
- Font có tên trong CSS **phải** có `@font-face` trỏ tới file đi kèm project, nếu không `lint` đỏ
  và máy khác render ra chữ khác.

## Nhịp và hình phản ứng theo âm thanh

Khi có nhạc nền, lấy lưới nhịp làm mốc cắt: điểm cắt rơi vào nhịp thì video "có nhịp" mà không cần
hiệu ứng gì thêm. Hình phản ứng theo âm thanh phải tính từ **dữ liệu phân tích đã lưu sẵn**, không
phân tích lúc render — render phải tái lập được.

## Ranh giới

Skill này **không** quyết định luật chuyển động (đó là `hyperframes-animation`), không tìm tài sản
media (`media-use`), và không thay thế thư viện template của repo: bản tin hằng ngày chọn layout
theo `video-theme-library` + `docs/THEME-LIBRARY.md` **trước**, chỉ sáng tác mới khi không có gì khớp.
