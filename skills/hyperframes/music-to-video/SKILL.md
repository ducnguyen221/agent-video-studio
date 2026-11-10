---
name: music-to-video
description: Use when turning a music track, extracted audio or mood brief into a lyric video, slideshow or kinetic promo, or when finalizing, handing off or ending a lyric-video session. Narrated pieces belong to the input-matched workflow instead.
---

# Video cắt theo nhịp nhạc

## Nhánh lyric video

Với yêu cầu lyric video, đọc [references/lyric-workflow.md](references/lyric-workflow.md)
và dùng hai mẫu storyboard ở `assets/`. Cue giọng hát lấy từ bản thu, cùng mốc thời gian
với audio; không lượng tử hóa cue theo lưới nhịp cắt cảnh. Lời chưa xác minh phải hiện rõ
trạng thái và không được ghi như lời đã duyệt. Nhịp là công cụ chọn điểm cắt, không phải
điều kiện bắt buộc cho mọi lựa chọn sáng tạo của người dùng.

Khi người dùng chốt bản cuối / yêu cầu finalize, **hoặc trước khi kết thúc phiên lyric video**,
bắt buộc tư vấn năm việc ở mục “Chốt bản cuối và bàn giao” trong workflow; ghi rõ trạng thái
video hiện tại và để người dùng chọn việc thực hiện. Đã có quyết định thì áp dụng, không hỏi lại.

Khi thiết kế chữ, đọc [lyric-video-effects](../../lyric-video-effects/SKILL.md): có A/B/C,
motion mở rộng và preset `soft-rise`/`focus-in`. Với ảnh tĩnh, đọc
[photo-ambient-effects](../../photo-ambient-effects/SKILL.md): có ambient painter, sun rays,
`dust` và envelope. Mỗi skill ghi rõ cách dùng, giới hạn và mức đã kiểm của tài nguyên.

> **Nguồn:** `heygen-com/hyperframes` · `skills/music-to-video/SKILL.md` @ **v0.8.51** ·
> Apache-2.0 · hash manifest `190e9885dab9b11d` (169 file upstream, phần lớn là **ảnh `png` mẫu** —
> **không** chép vào repo này).
> Bản này **đã dịch, rút gọn và biên tập lại** (Apache-2.0 §4(b)); `references/*` không chép vào repo.

## Hai ý chi phối mọi thứ

1. **Nhạc định hướng nhịp, không quyết định nội dung.** Dùng lưới nhịp đã phân tích để
   chọn điểm cắt khi phù hợp; chủ đích sáng tạo và cue giọng hát có thể nằm ngoài lưới.
2. **Không cần tài sản nào cũng ra được video hoàn chỉnh.** Chữ, hình khối, màu và chuyển động là
   đủ. Ảnh và clip người dùng đưa vào là **thêm**, cắt theo kế hoạch và nhạc.

## Sáu bước

0. **Dựng project, nạp nhạc và tài sản** (nếu có).
1. **Phân tích nhạc** → lưới nhịp, mốc chuyển đoạn, cường độ theo thời gian. Kết quả **lưu ra file**;
   render phải tái lập được, nên không phân tích lại lúc render.
2. **Khung xương** — chỉ cấu trúc: đoạn nào từ giây nào tới giây nào, mỗi đoạn làm gì.
3. **Điền kế hoạch** — **có cổng người dùng ở đây.** Người dùng xem kế hoạch trước khi bạn đổ công
   dựng từng khung.
4. **Dựng từng khung theo kế hoạch.**
5. **Lắp lại và render** sau khi duyệt bản xem trước.

## Luật cứng

- **Không dùng nhạc không có quyền.** Đây là chỗ dễ sai nhất của thể loại này và hậu quả rơi vào
  người đăng, không rơi vào người dựng. Ghi nguồn và giấy phép bản nhạc vào sổ media của project.
- **Lời bài hát trên màn hình cũng là tác phẩm có bản quyền.** Video lyric cần quyền riêng, không
  chỉ quyền dùng bản ghi.
- **Cấm `repeat: -1`** — nhạc dài, tween vô hạn ở đây là cách làm tiến trình render chết giữa chừng.
- Dùng lưới nhịp đã lưu để hỗ trợ chọn điểm cắt; ghi các ngoại lệ có chủ đích trong storyboard.

## Nghiệm thu

Nghe và nhìn **bản render**, không nhìn bản xem trước: chỗ lệch nhịp nửa khung chỉ lộ ra ở file
cuối. Kiểm cả điểm nối cuối cùng — video hết trước nhạc, hay nhạc bị cắt cụt, đều là lỗi thấy ngay.
