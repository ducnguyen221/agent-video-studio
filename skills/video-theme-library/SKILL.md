---
name: video-theme-library
description: Use BEFORE inventing a layout for any video or slide built with this studio - news recaps, deep dives, shorts, teaching decks, review videos, infographic video. Mandatory lookup - read the station's theme catalog first (THEME-LIBRARY.md at the station root), else the repo's docs/THEME-LIBRARY.md; classify each beat of the script, take the highest-tier template that matches the job and aspect ratio, and only compose something new when nothing fits (then add it back to the catalog in use). Not for rendering, narration or footage editing.
---

# Chọn template trước, sáng tác sau

## Catalog nào là nguồn sự thật — tìm theo thứ tự

1. **Catalog của trạm:** `THEME-LIBRARY.md` ở gốc trạm video (trạm = `VIDEO_STATION`, hoặc
   `studio.local.json`; `video-studio doctor` in đường trạm đang dùng). Nếu file này có thì
   **đó là nguồn duy nhất** — trạm là nơi thư viện sống và lớn lên theo từng đợt dựng của người
   dùng.
2. **Không có catalog ở trạm** → lùi về `docs/THEME-LIBRARY.md` trong repo này (bản gốc dùng
   chung, chưng cất từ bộ template của repo).

Đọc file đó — **không làm theo trí nhớ**, vì thư viện đổi theo từng đợt dựng và trí nhớ thì không.
Không trộn hai catalog trong cùng một video, và **không sửa nội dung catalog khi chỉ đang tra**.

## Quy trình bốn bước

1. **Phân loại TỪNG đoạn nội dung theo việc nó làm**: mở màn/hook · con số chủ đạo · N điểm ·
   quy trình/chuỗi sự kiện · so sánh A-B · xếp hạng · phát ngôn · demo sản phẩm/clip nguồn · mặt
   trái/cảnh báo · chốt hạ · kết + kêu gọi.
2. **Tra bảng chọn nhanh** (§1 của catalog) → lấy template **tier cao nhất** khớp việc đó VÀ khớp
   tỉ lệ khung (16:9 hay 9:16 — hai cột khác nhau, đừng lấy nhầm). Template tier `NEW` mới có mô
   tả giải phẫu, chưa có code: dựng theo mô tả rồi ghi nguồn code vào catalog.
3. **Chọn một hệ màu theo thương hiệu** (§9 nếu catalog có) và **không trộn hai hệ** trong một
   video.
4. **Tuân luật cứng** (§6). Vi phạm luật cứng là video **hỏng**, không phải video xấu.

## Nghĩa vụ giữ thư viện còn sống

Áp cho catalog **đang dùng** (của trạm nếu có, không thì của repo):

- Chế một pattern chưa có trong thư viện → **thêm entry vào catalog ngay trong cùng lượt việc**
  (id · giải phẫu · chuyển động · nguồn code · tier). Không có bước này thì lần sau người khác —
  hoặc chính bạn — lại chế lại từ đầu.
- Dựng xong một pattern đang ở tier `NEW` → đổi tier (S/A) và trỏ tới nguồn code.
- Học thêm một nguồn ngoài thì chưng cất vào catalog và **ghi rõ nguồn gốc** (provenance).
- Sửa một template theo yêu cầu riêng của một số báo thì **đừng** sửa vào thư viện: thư viện là
  cái dùng lại được, không phải nhật ký của một số báo.

## Ba luật hay bị quên nhất

- **Cấm lặp vô hạn** (`repeat: -1`): tiến trình render phình tới khi chết, và chết sau vài phút
  chứ không chết ngay.
- **Tái lập được:** mọi phần tử định thời có `data-start`/`data-duration`; timeline `paused`
  đăng ký vào `window.__timelines`; không `Date.now()`, không `Math.random()`.
- **Ghim một bản engine cụ thể.** Xem trước và render thật phải cùng một bản, nếu không thì thứ
  soi trên trình duyệt không phải thứ sẽ ra video.

Hai luật nữa thuộc về nội dung và được catalog nêu chi tiết: chữ phụ đề tô **từ khoá**, và bản
công khai **không lộ tên công cụ nội bộ**.
