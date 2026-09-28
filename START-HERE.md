# Bắt đầu với Agent Video Studio

Repo này dựng video cho agent: từ một file spec JSON ra video bản tin 16:9 và short 9:16 bằng
HyperFrames, có lồng tiếng qua repo giọng `agent-voice-studio`. Chạy trên Windows và macOS; bộ
khung (lệnh, trạm, test) đã kiểm trên cả hai, render thật mới có số đo trên Windows.

## Cài tay

Cần **Git**, **Python ≥ 3.10**, **Node ≥ 22** và **ffmpeg** — bảng lệnh cài từng thứ cho từng
hệ điều hành ở [docs/INSTALL.md](docs/INSTALL.md#1-thứ-phải-có-trước).

Windows (PowerShell):

```powershell
git clone https://github.com/ducnguyen221/agent-video-studio "$env:USERPROFILE\agent-video-studio"
cd "$env:USERPROFILE\agent-video-studio"
py -3 -m venv .venv
.\.venv\Scripts\python -m pip install -e .
.\.venv\Scripts\video-studio init --yes
.\.venv\Scripts\video-studio doctor
```

macOS (Terminal):

```sh
git clone https://github.com/ducnguyen221/agent-video-studio ~/agent-video-studio
cd ~/agent-video-studio
python3 -m venv .venv
.venv/bin/python -m pip install -e .
.venv/bin/video-studio init --yes
.venv/bin/video-studio doctor
```

Đặt repo ở thư mục cục bộ, **không** trong OneDrive, iCloud Drive, Google Drive hay Dropbox:
đồng bộ đám mây làm hỏng `.venv` và đẩy cả nháp render lên mạng.

`init --yes` tạo **trạm** ở `workspace/` ngay trong repo — nơi chứa project đang dựng, nháp và
cache. Git bỏ qua cả thư mục này, nên dữ liệu của bạn không bao giờ đi vào mã nguồn. Muốn đặt
trạm ở chỗ khác (dùng chung giữa nhiều máy, hoặc repo là bản public của chính bạn): đặt biến
`VIDEO_STATION` trỏ thư mục đó, hoặc `video-studio init --station <thư mục>`. Hai chế độ và cây
thư mục của trạm: [docs/WORKSPACE.md](docs/WORKSPACE.md).

## Đọc kết quả `doctor`

Mỗi dòng là một thứ đã kiểm. Mã thoát nói việc cần làm tiếp:

| Mã | Nghĩa | Làm gì |
|---|---|---|
| `0` | Dùng được (có thể kèm cảnh báo) | Sang bài mẫu |
| `2` | Cấu hình sai | Đọc dòng lỗi, sửa cấu hình — cài thêm không chữa được |
| `3` | Còn thiếu công cụ hoặc trạm | Làm theo dòng `→` dưới mỗi lỗi |

Chromium của HyperFrames tải về lần đầu render; máy không có mạng lúc render thì chạy trước lệnh
`browser ensure` mà `doctor` in ra.

## Bài mẫu đầu tiên

Lồng tiếng cần repo giọng cài **cùng venv** ([docs/INSTALL.md](docs/INSTALL.md#2-cài-package)).
Có rồi thì dựng bản tin mẫu hai cảnh:

```text
video-studio render --project news --input samples/news-mini/spec.json --brand samples/news-mini/brand.json --out out/news-mini --json
```

Kết quả đúng và cách so hai máy: [samples/news-mini/EXPECTED.md](samples/news-mini/EXPECTED.md).
Chưa có repo giọng thì lệnh dừng mã 3 kèm lệnh cài — đó là kết quả đúng.

## Cập nhật và sao lưu

- `video-studio update` — `git pull --ff-only`; không bao giờ xoá thay đổi của bạn.
- `video-studio backup --out <file>.zip` — gói cả trạm (trừ nháp và cache) trước khi làm gì lớn.

## Đọc thêm

[README.vi.md](README.vi.md) · [hướng dẫn dùng](GUIDE.vi.md) · [hợp đồng lệnh và mã
thoát](docs/CONTRACT.md) · [nhật ký thay đổi](docs/CHANGELOG.md)
