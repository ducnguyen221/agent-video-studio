---
name: music-to-video
description: Turn a music track - an audio file, a video to pull audio from, or a track generated from a mood brief - into a beat-synced video such as a lyric video, a slideshow or a kinetic promo. The music drives all pacing, any user-supplied images or videos are cut onto the same beat grid, and a complete video needs zero assets. Narrated pieces belong to the input-matched workflow instead.
---

# Video cắt theo nhịp nhạc

> **Nguồn:** `heygen-com/hyperframes` · `skills/music-to-video/SKILL.md` @ **v0.8.51** ·
> Apache-2.0 · hash manifest `190e9885dab9b11d` (169 file upstream, phần lớn là **ảnh `png` mẫu** —
> **không** chép vào repo này).
> Bản này **đã dịch, rút gọn và biên tập lại** (Apache-2.0 §4(b)); `references/*` không chép vào repo.

## Hai ý chi phối mọi thứ

1. **Nhạc quyết định nhịp, không phải nội dung.** Mọi điểm cắt rơi vào lưới nhịp đã phân tích. Cắt
   "theo cảm giác" rồi mong nó trùng nhịp là cách làm ra video lệch nhẹ ở mọi chỗ — thứ người xem
   không chỉ ra được nhưng cảm thấy.
2. **Không cần tài sản nào cũng ra được video hoàn chỉnh.** Chữ, hình khối, màu và chuyển động là
   đủ. Ảnh và clip người dùng đưa vào là **thêm**, và chúng cũng phải cắt lên cùng lưới nhịp đó.

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
- Mốc cắt bám **nhịp**, không bám giây tròn. Một video 90 giây có thể có hơn 100 điểm cắt; đừng đặt
  tay từng cái, tính từ lưới nhịp.

## Nghiệm thu

Nghe và nhìn **bản render**, không nhìn bản xem trước: chỗ lệch nhịp nửa khung chỉ lộ ra ở file
cuối. Kiểm cả điểm nối cuối cùng — video hết trước nhạc, hay nhạc bị cắt cụt, đều là lỗi thấy ngay.
