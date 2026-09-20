---
name: media-use
description: The single skill for every media need in a HyperFrames project - resolve BGM, SFX, image, icon, brand logo, voice, color grade or LUT into a frozen local file plus a ledger record; generate through TTS, music or image models when the catalog misses; produce voiceover, transcription, captions and background removal; and operate on media (cut, reframe, transform). Also use for vague visual feedback that footage looks dark, flat or boring, should feel retro or print, or needs privacy. Not for mixing audio already placed in a composition - that is hyperframes-audio.
---

# Tìm, sinh và xử lý media

> **Nguồn:** `heygen-com/hyperframes` · `skills/media-use/SKILL.md` @ **v0.8.51** · Apache-2.0 ·
> hash manifest `8f21655cd07a62ea` (158 file upstream, trong đó **19 file mp3** của bộ SFX và nhiều
> LUT — **không** chép vào repo này vì giấy phép từng file chưa kiểm).
> Bản này **đã dịch, rút gọn và biên tập lại** (Apache-2.0 §4(b)).

## Một động từ duy nhất: `resolve`

Mọi nhu cầu media đi qua một cửa: **hoá giải yêu cầu thành một file cục bộ đã đóng băng, kèm một
dòng sổ ghi nó đến từ đâu.** "Đã đóng băng" nghĩa là: file nằm trong project, không phải một URL
sẽ đổi nội dung vào tuần sau; và lượt render tháng sau ra đúng thứ của tháng này.

Thứ tự thử: **đã có trong project → kho catalog → sinh ra bằng mô hình**. Chỉ tới bước ba khi hai
bước trước trượt, vì bước ba tốn tiền, tốn thời gian và cho kết quả khác nhau mỗi lần.

## Dòng sổ bắt buộc ghi gì

Nguồn (tên kho/mô hình/URL), giấy phép, ngày lấy, và tên file trong project. Thiếu dòng này thì
sáu tháng sau không ai trả lời được câu "ảnh này có được dùng thương mại không" — và câu đó luôn
đến sau khi video đã đăng.

> **Luật của repo này:** không chép font, nhạc, ảnh của bên thứ ba vào repo. Cần thì ghi **hướng
> dẫn tải** trong `docs/`, để người cài tự lấy về trạm của họ. Nhạc nền của trạm nằm ở
> `<trạm>/assets/`, không nằm trong repo.

## Phản hồi mơ hồ về hình ảnh cũng là yêu cầu media

"Trông tối quá", "phẳng quá", "chán quá", "muốn kiểu máy quay cũ", "cần che mặt người đi ngang" —
tất cả đều là yêu cầu xử lý media, không phải yêu cầu đổi animation. Đừng chữa bằng cách thêm
chuyển động; chữa bằng grade, LUT, đổi khung hoặc thay tài sản.

## Giọng đọc, phụ đề, xoá nền

- **Giọng đọc:** trong repo này lồng tiếng **không** đi qua HyperFrames mà đi qua trạm giọng
  (`video_studio/voice.py` → `voice-studio`), vì profile giọng là dữ liệu của người dùng và phải ở
  lại trạm.
- **Phiên âm (transcribe):** đường mặc định của repo là whisper chạy tại máy
  (`video_studio/edit/transcribe.py`) — không cần khoá API, không gửi tiếng của ai ra ngoài.
- **Xoá nền:** chạy tại máy; kiểm bằng mắt ở vài khung, đặc biệt chỗ tóc và chỗ chuyển động nhanh.

## Chủ động rà cơ hội media

Trước khi render, rà một lượt: cảnh nào đang trống có thể mạnh hơn nhờ một tài sản có sẵn? Chỗ nào
đang dùng ảnh tạm mà quên thay? Có tài sản nào đang trỏ ra URL ngoài không? Câu cuối là câu quan
trọng nhất — nó là thứ làm lượt render lúc nửa đêm hỏng mà không ai hiểu vì sao.
