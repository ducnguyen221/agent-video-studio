# Transcript cho phân tích video mẫu

## Bước 3 — transcript

`reference transcribe --input <video> --project <project>` ghi `transcripts/<stem>.json`.

- Thứ tự nguồn: `--subs` → phụ đề cạnh video hoặc trong `<project>/source/` → luồng phụ đề nhúng
  → ASR cục bộ → mã 3.
- `fetch --go` lưu video vào `<project>/source/reference.<đuôi>` và phụ đề thành
  `reference.<mã>.vtt` (mặc định `--sub-langs vi,en`); dùng tệp video đó làm `--input`. Nếu yt-dlp ghi `reference.unknown_video` (không biết đuôi), đổi tên theo định dạng thật (xem `cleanup inspect`) trước khi phân tích, vì `frames`/`tiles`/`transcribe` chỉ nhận đuôi video/âm thanh; yt-dlp chỉ ra playlist ⇒ mã 1 «không tạo tệp». Video
  mẫu không nhất thiết là tiếng Việt: đặt `--language <mã của phụ đề đã có>` (vd `vi`, `en`) hoặc
  đưa thẳng `--subs <project>/source/reference.<mã>.vtt` **kèm** `--language <mã>` để `language_code` đúng. `--language auto` chỉ thử
  `<stem>.vtt` / `<stem>.srt` cạnh video, nên bỏ sót `reference.<mã>.vtt`.
- Phụ đề nhúng chọn theo ngôn ngữ xin; không khớp thì lấy luồng chữ đầu tiên **mà không cảnh
  báo**. Transcript **không** ghi ngôn ngữ thật của luồng: `language_code` chỉ chép lại ngôn ngữ
  đã xin, `_source_stream` chỉ là chỉ số luồng (chỉ có khi `_source` là `subtitles:embedded`). Đọc vài
  cue để tự xác nhận ngôn ngữ; sai thì chạy lại với `--subs <tệp>` (kèm `--force`), không thì ghi
  vào «Chưa kiểm chứng».
- Độ mịn `cue` là theo cụm phụ đề, **không** gọi là theo từ và không dùng làm mốc chính xác từng chữ.
- Lệnh thoát mã 3 (không có phụ đề, không có ASR): **dừng**, báo người dùng cách bổ sung (đưa tệp
  phụ đề, hoặc cài công cụ ASR). Không đoán lời từ hình hay từ tiêu đề.
