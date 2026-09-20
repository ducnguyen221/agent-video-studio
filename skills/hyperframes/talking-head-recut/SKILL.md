---
name: talking-head-recut
description: Package an existing talking-head, interview or podcast video with timed graphic overlay cards - kinetic titles, lower-thirds, data callouts, quotes, side panels, picture-in-picture - synced to the transcript on a 16:9, 9:16 or 4:5 canvas, while the clip plays untouched underneath. Trigger on "graphic overlays", "on-screen graphics", "package or dress up my video". Not plain subtitles - that is embedded-captions.
---

# Gắn card đồ hoạ lên video phỏng vấn

> **Nguồn:** `heygen-com/hyperframes` · `skills/talking-head-recut/SKILL.md` @ **v0.8.51** ·
> Apache-2.0 · hash manifest `7018bf017e8606d2` (28 file upstream, gồm 6 file font `woff2` —
> **không** chép vào repo này).
> **Ghi công bắt buộc kèm theo (giữ nguyên văn theo yêu cầu của upstream):** phần hệ thống thiết kế
> của skill gốc phỏng theo `notedit/vtake-skills`, giấy phép **MIT**, © 2026 leeoxiang. Xem `NOTICE`
> của repo này.
> Bản này **đã dịch, rút gọn và biên tập lại** (Apache-2.0 §4(b)).

## Khác gì với phụ đề

Phụ đề là chữ của lời nói. Card đồ hoạ là **thông tin thêm**: tên và chức danh người nói, một con
số, một câu trích, một bảng nhỏ, một khung hình phụ. Clip gốc chạy **nguyên vẹn bên dưới**, không
cắt, không đổi.

## Mười một bước

1. **Kiểm môi trường** — Node ≥ 22, ffmpeg, và bộ tài sản đi kèm skill.
2. **Tạo thư mục làm việc riêng**, đừng làm ngay cạnh file gốc.
3. **Trích tiếng và siêu dữ liệu** — thời lượng, kích thước, fps.
4. **Phiên âm** (whisper chạy tại máy).
5. **Sửa bản chữ.** Tên riêng và số liệu luôn sai; sửa ở đây rẻ hơn sửa sau.
6. **Phác bảng phân cảnh nhẹ** ngay trong hội thoại: mốc nào cần card gì.
7. **Chốt hướng nhìn với người dùng TRƯỚC** khi viết card. Đây là bước hay bị bỏ, và bỏ nó nghĩa
   là làm xong mới biết sai tông.
8. **Viết HTML từng card** theo hợp đồng: mỗi card một khối có `data-start`/`data-duration`, kích
   thước tính theo khung dọc trước (chữ đọc được trên điện thoại), chọn kiểu vào–ra từ bộ có sẵn.
9. **Lắp composition** — và đây là chỗ có một bẫy thật:
   > **Mã hoá lại video nguồn với keyframe dày trước khi đưa vào.** Nguồn có GOP thưa (khoảng cách
   > keyframe > ~1 s) sẽ **đứng hình khi tua**, cho ra một khung chết nằm dưới lớp overlay. Đặt
   > `-g` và `-keyint_min` bằng đúng fps của composition.
10. **Render** sau khi người dùng duyệt bản xem trước.
11. **Báo kết quả**: đường file, thời lượng, và mọi chỗ đã phải tự quyết.

## Luật bố cục

- Card **không che mặt người nói** và không che vùng giao diện nền tảng.
- Một card một ý. Hai con số trên một card là hai card.
- Card vào và ra **trong lúc người nói đang nói tới ý đó**, không vào sau khi ý đã qua.
- Ở khung dọc, thiết kế theo chiều rộng điện thoại trước rồi mới nới ra khung ngang, không làm
  ngược lại.
