---
name: hyperframes-audio
description: Mix audio that is already placed inside a HyperFrames composition - fade in and out, crossfade, track gain, volume automation, ducking, a music bed fighting a voiceover (voiceover carve), effects on a track (EQ, compressor, limiter, gate, saturation, delay, reverb, chorus, phaser, bitcrush), automation envelopes, and one submix bus carrying a chain for several tracks at once. Not for sourcing or generating audio (media-use) and not for clip timing or track layout (hyperframes-core).
---

# Trộn âm thanh trong composition

> **Nguồn:** `heygen-com/hyperframes` · `skills/hyperframes-audio/SKILL.md` @ **v0.8.51** ·
> Apache-2.0 · hash manifest `b39bac771e873eae` (7 file upstream).
> Bản này **đã dịch, rút gọn và biên tập lại** (Apache-2.0 §4(b)); `references/*` không chép vào repo.

Skill này chỉ áp cho âm thanh **đã nằm trong** composition. Tìm hay sinh ra nhạc, tiếng động, giọng
đọc là việc của `media-use`. Đặt clip vào đâu, dài bao lâu là việc của `hyperframes-core`.

> **Trong pipeline tin của repo này, HyperFrames render CÂM** rồi ffmpeg mới mux tiếng vào
> (`video_studio/render.py`, `voice.py`). Nghĩa là mọi thứ dưới đây **không ảnh hưởng** bản tin —
> chỉ dùng khi bạn cố ý đưa audio vào trong composition.

## Bắt đầu từ triệu chứng, không bắt đầu từ tên hiệu ứng

| Nghe thấy gì | Nhìn vào đâu trước |
|---|---|
| Nhạc át lời đọc | *voiceover carve* (khoét dải tần giọng khỏi nhạc), rồi mới tới giảm âm lượng |
| Chuyển cảnh nghe "cụp" | thiếu fade 20–40 ms ở hai đầu clip |
| To nhỏ thất thường giữa các cảnh | chưa chuẩn hoá mức, hoặc mỗi clip một gain riêng |
| Giọng đục, nghe xa | EQ cắt trầm rồi mới nén, đừng nén trước |
| Đỉnh vượt ngưỡng lúc giao | thiếu limiter ở bus cuối |

Chẩn đoán trước, chọn hiệu ứng sau. Chọn hiệu ứng theo tên vì "nghe có vẻ hợp" là cách chồng năm
tầng xử lý lên một vấn đề vốn chỉ cần một tầng.

## Bốn thứ đáng nhớ

1. **`<audio>` nào cũng phải có `id`.** Thiếu id thì bộ trộn không thấy nó, và bản render **câm**
   mà không báo lỗi gì.
2. **Voiceover carve** là cách đúng để nhạc nền không nuốt giọng: khoét đúng dải tần của giọng
   trong nhạc, thay vì hạ cả bản nhạc xuống cho tới khi nó thành vô nghĩa. Từ bản 0.8.35 mức khoét
   mặc định **mạnh hơn** trước.
3. **Một bus cho nhiều track.** Khi nhiều track cần chung một chuỗi hiệu ứng, một fader và một đồng
   hồ tự động hoá, gom vào một nhóm thay vì chép cấu hình ra từng track — chép ra là bảo đảm chúng
   sẽ lệch nhau sau vài lần sửa.
4. **Đường bao tự động hoá (automation) vẽ được trên âm lượng và trên tham số của hiệu ứng.** Dùng
   nó thay cho việc cắt clip ra làm nhiều mảnh chỉ để đổi mức.

## Nghiệm thu

Nghe lại **bản render**, không nghe bản xem trước: đường trộn của xem trước và của render không
nhất thiết giống nhau. Kiểm mức đỉnh và mức trung bình của file cuối bằng công cụ đo, đừng kết
luận bằng tai trên một cặp loa.
