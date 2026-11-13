# Bước «tìm ảnh» cho video tin và repo

Đặt sau dossier (hồ sơ nguồn của tin), trước storyboard. Mục đích: video dựng bằng chữ và motion
cần thêm 1–2 ảnh thật của chủ thể tin để người xem nhận ra ngay đó là gì.

## Việc cần làm

1. Chọn **1–2 ảnh chính chủ**: ảnh trong README của repo, trang chủ sản phẩm hoặc press kit. Không
   lấy ảnh của báo khác.
2. Với từng ảnh, ghi một dòng vào `assets/ATTRIBUTION` của project: **URL nguồn, tác giả, giấy phép**.
   Không ghi đường dẫn máy. Chưa rõ giấy phép thì ghi «chưa rõ» và hỏi người dùng trước khi dùng.
3. Giao cho agent tư vấn motion (skill `video-theme-library`) cảnh nào dùng ảnh: Ken Burns, khung
   thiết bị hoặc cắt nền. Ghi vào storyboard ở cột «Hình / asset ID».
4. Thumbnail ghép ảnh thật với tiêu đề.

## Giới hạn an toàn khi lấy ảnh

- Chỉ nhận URL `https` tên miền công khai.
- Chặn IP nội bộ, `localhost` và `file:`.
- Tải ảnh từ web luôn cần người dùng cho phép đúng URL; tài liệu này không tự tải gì.
- Ảnh cục bộ khai qua `images.json` của `render` (xem `docs/CONTRACT.md`).

## Mẫu `assets/ATTRIBUTION`

```
assets/hero.png | https://example.org/press/hero.png | Tên tác giả | CC-BY-4.0
```
