# Bài mẫu `news-mini` — kết quả kỳ vọng

Bản tin ngày nhỏ nhất còn đi qua trọn chuỗi dựng: **2 cảnh tin**, giọng ghim hạt giống `1234`,
không nhạc nền, spec không trỏ ảnh nào trên mạng. Dùng để kiểm một máy vừa cài (Windows hoặc
macOS) và để so hai máy với nhau bằng cùng một đầu vào.

Hai chỗ vẫn cần mạng lúc dựng, do template chứ không do spec: trang HTML nạp thư viện hoạt ảnh
từ CDN, và bản ngắn thiếu ảnh thì lấp khung bằng filler của trạm giọng nếu có, không thì tải một
ảnh b-roll giấy phép CC (lỗi mạng không chặn render, chỉ để khung trống). Vì thế khung hình bản
ngắn có thể khác giữa hai lượt; thời lượng thì không.

## Chạy

Từ gốc repo, sau `video-studio init` và `video-studio doctor` báo mã 0:

```text
video-studio render --project news --input samples/news-mini/spec.json --brand samples/news-mini/brand.json --out out/news-mini --json
```

Cần: Node ≥ 22, ffmpeg, Chromium của HyperFrames (`video-studio doctor` chỉ cách cài), repo
giọng `agent-voice-studio` clone cạnh repo này và cài `[engine]` vào **chính `.venv` của repo
này**, cùng một giọng mặc định — lệnh ở [INSTALL.md mục 5b](../../INSTALL.md#5b-lồng-tiếng-tuỳ-chọn-nặng--hỏi-trước).
Không có repo giọng thì lệnh dừng với **mã 3** kèm lệnh cài — đó là kết quả đúng, không phải lỗi
mẫu. Có repo giọng mà chưa có giọng mặc định thì lệnh dừng vì chưa có profile: làm nốt mục 5b.

## Kết quả kỳ vọng

Kiểm bằng máy, không cần mạng: `tests/test_samples.py` đọc đúng các dòng dưới đây.

| Mục | Kỳ vọng |
|---|---|
| Mã thoát | `0` |
| Dòng JSON cuối | `"ok": true`, `"project": "news"`, 2 phần tử trong `outputs` |
| File dài (16:9, 1920×1080) | `2026-01-02.mp4` |
| File ngắn (9:16, 1080×1920) | `2026-01-02-short.mp4` |
| File phụ | `2026-01-02.mp4.chapters.json` (mốc chương của bản dài) |
| Số cảnh tin | 2 |
| Nhạc nền | không (`"bgm": "none"`) |

## Số đo theo máy

Đầu ra **không** trùng từng byte giữa hai hệ điều hành: font sẵn có (Segoe UI chỉ có trên
Windows) và bộ giải mã khác nhau làm lệch vài khung hình. So thời lượng theo khoảng, không so
hash mp4. Trên **cùng một máy**, chạy lại cùng spec cho cùng thời lượng.

| Máy | Ngày | Bản engine | Thời gian dựng | Thời lượng dài / ngắn | Người đo |
|---|---|---|---|---|---|
| Windows 11 x64 | 2026-09-29 | HyperFrames 0.8.54 · voice-studio 0.3.0 · torch 2.14.0+cu126 (RTX 4070) | 113 s (`timings.total` 112,6) | 51,05 s / 24,93 s | agent Claude, cài mới theo INSTALL.md mục 5b |
| macOS arm64 | chưa đo | HyperFrames 0.8.54 | — | — | — |

Điền một dòng sau mỗi lần chạy thật; để ô "chưa đo" khi chưa chạy, không ước lượng.

Ghi chú lượt Windows: bản clone mới, `.venv` mới, giọng mặc định tạo bằng `make-profile --instruct`
(19 s), weights lấy từ cache Hugging Face đã có trên máy (máy mới phải tải thêm ~4 GB). Cùng spec
dựng bằng HyperFrames 0.7.94 cho **đúng cùng** thời lượng 51,05 s / 24,93 s (lượt đó mất 209 s). Bản ngắn tải hai ảnh b-roll CC lúc dựng; thiếu `faster-whisper` thì chỉ bỏ phụ đề từng chữ
(log `[asr] word-caption skip`), không làm hỏng lệnh.
