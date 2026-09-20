---
name: pr-to-video
description: Turn a GitHub pull request - a PR URL, owner/repo#N, or "this PR" in a checked-out repo - into a code-change explainer video built from the diff, the commits and the files. Use for changelog videos, feature reveals, fix and refactor walkthroughs. The input is a code change, not a website. Not a product promo (product-launch-video) and not a topic explainer with no PR (faceless-explainer).
---

# Từ pull request thành video giải thích thay đổi

> **Nguồn:** `heygen-com/hyperframes` · `skills/pr-to-video/SKILL.md` @ **v0.8.51** · Apache-2.0 ·
> hash manifest `da3a68c5a2a86f77` (30 file upstream).
> Bản này **đã dịch, rút gọn và biên tập lại** (Apache-2.0 §4(b)); `references/*` không chép vào repo.

Đầu vào là **một thay đổi mã**, không phải một trang web. Kết quả là video kể: trước thế nào, đổi
cái gì, vì sao, và ai đã làm.

## Bảy bước

0. **Dựng project.**
1. **Nạp PR một cách xác định.** Lấy metadata và diff bằng `gh`, **phân trang cho đủ danh sách
   file** — PR lớn bị cắt ở khoảng 100 file nếu không phân trang, và khi đó video kể thiếu mà không
   ai biết. Lỗi xác thực, không tìm thấy, hoặc repo riêng tư phải **hỏng ngay ở bước này**, đừng để
   nó âm thầm thành video rỗng.
   - Biến đổi ngoại tuyến sau khi tải: rút token màu từ mã, rút chữ nhìn thấy được làm brief, rút
     danh sách người đóng góp (lọc bot).
   - Bước mạng duy nhất còn lại: tải ảnh đại diện người đóng góp cho cảnh ghi công. Làm được thì
     làm, không được thì **vẫn đi tiếp** — thiếu ảnh không phải lý do giết cả lượt.
2. **Hệ thiết kế** kiểu biên tập mã: nền tối, chữ đơn cách cho mã, màu nhấn lấy từ token của repo.
3. **Bảng phân cảnh và lời đọc** — vấn đề → thay đổi → đoạn mã then chốt → kết quả → ghi công.
   3.1 **Âm thanh.**
4. **Thiết kế từng khung.** Mã hiện lên phải **đọc được**: chọn 5–12 dòng, không dán cả file.
5. **Dựng khung.**
6. **Chốt:** `check` → `preview` → người duyệt → `render`.

## Luật riêng

- **Không kể sai diff.** Nếu không hiểu một thay đổi thì bỏ nó ra khỏi video, đừng đoán.
- **Ghi công theo dữ liệu thật** của PR, lọc bot, giữ đúng tên đăng nhập.
- **Chỉ dùng thông tin công khai.** PR riêng tư, repo nội bộ: hỏi người dùng trước khi đưa bất cứ
  đoạn mã nào lên video sẽ đăng công khai.
- **Đường dẫn tuyệt đối và tên máy không lên màn hình.** Cắt còn tên file tương đối.

## Cảnh mã

Một cảnh một đoạn mã. Tô sáng **đúng dòng đã đổi**, và để dòng đó ở giữa khung. Cuộn mã trong lúc
lời đọc chạy là cách chắc chắn để người xem không đọc kịp dòng nào.
