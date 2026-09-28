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

Cần: Node ≥ 22, ffmpeg, Chromium của HyperFrames (`video-studio doctor` chỉ cách cài), và repo
giọng cài **cùng venv** (`pip install -e ".[voice]"` + bản clone `agent-voice-studio`). Không có
repo giọng thì lệnh dừng với **mã 3** kèm lệnh cài — đó là kết quả đúng, không phải lỗi mẫu.

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
| Windows 11 x64 | chưa đo | HyperFrames 0.8.54 | — | — | — |
| macOS arm64 | chưa đo | HyperFrames 0.8.54 | — | — | — |

Điền một dòng sau mỗi lần chạy thật; để ô "chưa đo" khi chưa chạy, không ước lượng.
