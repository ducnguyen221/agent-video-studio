---
name: video-theme-library
description: Use BEFORE inventing a layout for any video or slide built with this studio - news recaps, deep dives, shorts, teaching decks, review videos. Classify each beat of the script, look the beat up in docs/THEME-LIBRARY.md, take the highest-tier template that matches the job and aspect ratio, and only compose something new when nothing fits (then add it back to the library). Not for rendering, narration or footage editing.
---

# Chọn template trước, sáng tác sau

**Nguồn duy nhất:** `docs/THEME-LIBRARY.md` trong repo này. Đọc file đó — **không làm theo trí
nhớ**, vì thư viện đổi theo từng đợt dựng và trí nhớ thì không.

## Quy trình bốn bước

1. **Phân loại TỪNG đoạn nội dung theo việc nó làm**: mở màn/hook · con số chủ đạo · N điểm ·
   quy trình/chuỗi sự kiện · so sánh A-B · xếp hạng · phát ngôn · demo sản phẩm · mặt trái/cảnh
   báo · chốt hạ · kết + kêu gọi.
2. **Tra bảng chọn nhanh** (§1 của `THEME-LIBRARY.md`) → lấy template **tier cao nhất** khớp
   việc đó VÀ khớp tỉ lệ khung (16:9 hay 9:16 — hai cột khác nhau, đừng lấy nhầm).
3. **Chọn một hệ màu theo thương hiệu** (§9) và **không trộn hai hệ** trong một video.
4. **Tuân luật cứng** (§6). Vi phạm luật cứng là video **hỏng**, không phải video xấu.

## Nghĩa vụ giữ thư viện còn sống

- Chế một pattern chưa có trong thư viện → **thêm entry vào `docs/THEME-LIBRARY.md` ngay trong
  cùng lượt việc** (id · giải phẫu · chuyển động · nguồn code · tier). Không có bước này thì lần
  sau người khác — hoặc chính bạn — lại chế lại từ đầu.
- Dựng xong một pattern đang ở tier `NEW` (mới có mô tả, chưa có code) → đổi tier và trỏ tới
  nguồn code.
- Sửa một template theo yêu cầu riêng của một số báo thì **đừng** sửa vào thư viện: thư viện là
  cái dùng lại được, không phải nhật ký của một số báo.

## Ba luật hay bị quên nhất

- **Cấm lặp vô hạn** (`repeat: -1`): tiến trình render phình tới khi chết, và chết sau vài phút
  chứ không chết ngay.
- **Tái lập được:** mọi phần tử định thời có `data-start`/`data-duration`; timeline `paused`
  đăng ký vào `window.__timelines`; không `Date.now()`, không `Math.random()`.
- **Ghim một bản engine cụ thể.** Xem trước và render thật phải cùng một bản, nếu không thì thứ
  soi trên trình duyệt không phải thứ sẽ ra video.
