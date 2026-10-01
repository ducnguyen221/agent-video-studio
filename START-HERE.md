# Bắt đầu với Agent Video Studio

Repo này dựng video cho agent: từ một file spec JSON ra video bản tin 16:9 và short 9:16 bằng
HyperFrames, có lồng tiếng qua repo giọng `agent-voice-studio`. Chạy trên Windows và macOS; bộ
khung (lệnh, trạm, test) đã kiểm trên cả hai, render thật mới có số đo trên Windows.

## Nhờ AI cài giúp

Mở ứng dụng AI bạn đang dùng (Claude Code, Codex hoặc Antigravity) và dán nguyên văn yêu cầu dưới đây. Agent tự đọc [hướng dẫn cài dành cho agent](INSTALL.md), kiểm tra máy, **hỏi bạn trước** khi cài thêm phần mềm, rồi cài, kiểm tra và báo lại từng bước.

```text
Hãy cài Agent Video Studio lên máy này (Windows hoặc macOS) cho chính ứng dụng AI bạn đang chạy.
Nguồn duy nhất: https://github.com/ducnguyen221/agent-video-studio
Đọc trước hướng dẫn dành cho agent tại
https://raw.githubusercontent.com/ducnguyen221/agent-video-studio/main/INSTALL.md
(không mở được link thì clone repo rồi đọc INSTALL.md trong đó) và làm đúng, đủ các bước:
kiểm máy, hỏi tôi trước khi cài phần mềm hoặc cần quyền admin, clone vào thư mục an toàn
(không OneDrive/iCloud/Desktop), cài vào .venv của repo, dựng trạm, chạy doctor, thử bài mẫu.
Quy tắc: chỉ chạy lệnh có trong repo hoặc INSTALL.md; không đổi chính sách hệ thống; không đọc
hay ghi mật khẩu/khóa; gặp lỗi thì dừng và giải thích bằng lời thường.
Kết thúc bằng bản tóm tắt: đường dẫn repo, trạm, từng dòng doctor, phần mềm đã cài thêm, việc tôi
cần làm tiếp.
```

Tab chat của Claude Desktop không chạy được lệnh — dùng tab Code của ứng dụng, hoặc tự cài theo mục dưới ([vì sao](hosts/claude-desktop/README.md)).

## Cài tay

Cần **Git**, **Python ≥ 3.10**, **Node ≥ 22** và **ffmpeg** — bảng lệnh cài từng thứ cho từng
hệ điều hành ở [docs/INSTALL.md](docs/INSTALL.md#1-thứ-phải-có-trước).

Windows (PowerShell):

```powershell
$Parent = $HOME          # thư mục cha bạn chọn cho các repo studio (tên gì cũng được)
git clone https://github.com/ducnguyen221/agent-video-studio (Join-Path $Parent 'agent-video-studio')
cd (Join-Path $Parent 'agent-video-studio')
py -3 -m venv .venv
.\.venv\Scripts\python -m pip install -e .
.\.venv\Scripts\video-studio init --yes
# Báo "máy đã có trạm video ở …" (mã 2) mà bạn muốn dùng trạm cũ đó? Chạy thay dòng trên:
#   .\.venv\Scripts\video-studio init --mode separate
.\.venv\Scripts\video-studio doctor
```

macOS (Terminal) — cần trước Xcode Command Line Tools (`xcode-select --install`) và Homebrew
(bạn tự cài theo brew.sh), rồi `brew install python@3.12 node ffmpeg-full git` (`ffmpeg-full`, không phải `ffmpeg`: bản core thiếu `drawtext`/`subtitles`). Gọi đích danh
`python3.12`: `python3` của Mac mới là 3.9, dưới mức tối thiểu.

```sh
PARENT="$HOME"           # thư mục cha bạn chọn cho các repo studio (tên gì cũng được)
git clone https://github.com/ducnguyen221/agent-video-studio "$PARENT/agent-video-studio"
cd "$PARENT/agent-video-studio"
python3.12 -m venv .venv
.venv/bin/python -m pip install -e .
.venv/bin/video-studio init --yes
# Báo "máy đã có trạm video ở …" (mã 2) mà bạn muốn dùng trạm cũ đó? Chạy thay dòng trên:
#   .venv/bin/video-studio init --mode separate
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

Chromium của HyperFrames tải về lần đầu render; máy không có mạng lúc render thì chạy trước
`npx --yes hyperframes@<bản ghim> browser ensure` — đúng lệnh `doctor` in ra. Muốn tắt telemetry
của HyperFrames (mặc định bật): `npx --yes hyperframes@<bản ghim> telemetry disable`, một lần mỗi
máy, nên làm trước lần `doctor` đầu tiên (INSTALL.md mục 7).

## Bài mẫu đầu tiên

Lồng tiếng cần repo giọng `agent-voice-studio` clone **cạnh** repo này, cài `[engine]` vào
**chính `.venv` của repo này**, cộng một giọng mặc định — lệnh cho từng hệ điều hành ở
[INSTALL.md mục 5b](INSTALL.md#5b-lồng-tiếng-tuỳ-chọn-nặng--hỏi-trước). Có rồi thì dựng bản tin
mẫu hai cảnh:

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
