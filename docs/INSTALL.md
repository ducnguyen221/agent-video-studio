---
title: Install
summary: Install video-studio on Windows and macOS - Node, ffmpeg, fonts, which venv to install into, and the optional extras for narration and footage editing.
audience: anyone setting the studio up on a new machine
---

# Cài `video-studio` (Windows · macOS · Linux)

Repo chứa **mã**; project, footage và nháp sống ở **trạm** (xem `docs/WORKSPACE.md`). Cài xong
thì `video-studio doctor` phải xanh.

## 1. Thứ phải có trước

| Thứ | Vì sao | Windows | macOS |
|---|---|---|---|
| **Node ≥ 22** | HyperFrames chạy trên Node; mọi bản đang dùng đều khai `engines.node >= 22` | `winget install OpenJS.NodeJS.LTS` | `brew install node` |
| **ffmpeg + ffprobe** | ghép tiếng, chuẩn âm lượng, cắt đoạn — thiếu `ffprobe` là hỏng ở giữa chừng chứ không hỏng lúc bắt đầu | `winget install Gyan.FFmpeg` | `brew install ffmpeg` |
| **Python ≥ 3.10** | chính package này | `winget install Python.Python.3.12` | `brew install python@3.12` |
| **Font Inter** | stack chữ mặc định của template | tải từ rsms.me/inter → Install | `brew install --cask font-inter` |

`doctor` nhận font Inter ở **font hệ thống hoặc kho font của HyperFrames**
(`~/.cache/hyperframes/fonts/`) — máy đã render bằng HyperFrames một lần thì thường có sẵn,
không phải cài lại.

Không nằm trên PATH thì đặt `NODE_DIR` / `FFMPEG_DIR` trỏ thư mục chứa chúng; font khác thì đặt
`VIDEO_FONT`.

Chromium headless của HyperFrames **tự tải về cache người dùng** ở lần chạy đầu
(`~/.cache/hyperframes`). Máy không có mạng lúc render thì chạy trước một lần:
`npx --yes hyperframes@<bản ghim> browser ensure`.

## 2. Cài package

```
git clone <repo> agent-video-studio
cd agent-video-studio
pip install -e .
video-studio --version
```

### Cài vào venv nào — câu hỏi quan trọng nhất của phần này

| Bạn định làm gì | Cài vào đâu |
|---|---|
| Render **có lồng tiếng** (mọi template bản tin đều đọc lời dẫn) | **venv của trạm giọng** — cùng chỗ đã cài `agent-voice-studio` |
| Chỉ render **câm**, hoặc chỉ dùng `init`/`doctor`/`edit` | venv riêng nào cũng được |

Lồng tiếng đi qua `import voice_studio` **trong cùng tiến trình**: model giọng nặng hàng GB, nạp
một lần cho cả bài. Hai venv khác nhau thì không có đường nào để import, và lỗi sẽ hiện ra ở
giữa lượt render chứ không phải lúc cài.

> **Ngoại lệ có chủ đích:** luật đẻ repo của hệ này nói "không dùng `pip install -e`". Ở đây
> dùng, vì trạm giọng và trạm video là **hai bản clone sống động** phải cùng venv và còn được
> sửa qua lại; cài bản wheel là mỗi lần sửa một lần đóng gói lại. Đổi lại: `video-studio update`
> chỉ là `git pull --ff-only`, không bao giờ `clean`.

### Phần phụ

```
pip install -e ".[voice]"   # lồng tiếng + render theo template (cần agent-voice-studio cùng venv)
pip install -e ".[edit]"    # chỉnh footage: faster-whisper, pillow, numpy… (nặng)
pip install -e ".[test]"    # chạy test
```

`[voice]` khai phụ thuộc `agent-voice-studio` **chưa có trên PyPI**: cài bản clone của repo giọng
trước (`pip install -e <clone agent-voice-studio>`), rồi extras chỉ còn kiểm hộ bạn.

## 3. Dựng trạm

```
video-studio init                      # hỏi bạn chọn embedded hay separate
video-studio init --yes                # nhận khuyến nghị (embedded), không hỏi
video-studio init --mode separate      # chọn thẳng chế độ, không hỏi
video-studio init --station ~/.video   # hoặc chỉ thẳng một trạm (= separate, không hỏi)
```

`init` **chỉ hỏi khi không tự nhận ra được**. Máy đã có trạm (biến `VIDEO_STATION`/`VIDEO_ROOT`,
hoặc `~/.video` mang dấu trạm) thì bản trần tự chọn `separate` và nói rõ lý do; xin `embedded`
trong tình huống đó là **lỗi mã 2** ("hai nguồn sự thật") chứ không phải một cảnh báo — muốn
dựng trạm trong repo thì gỡ biến/trạm cũ trước. Không có terminal (CI, scheduled task) thì
truyền `--mode` hoặc `--station` tường minh thay vì để lệnh chờ câu trả lời.

Máy **đã có trạm cũ** (thư mục `news/`, `topstory/` nằm ngay ở gốc trạm):

```
video-studio init --station <trạm> --migrate --dry-run   # đọc kế hoạch
video-studio init --station <trạm> --migrate             # rồi mới chạy thật
video-studio init --station <trạm> --undo                # sai thì hoàn tác theo nhật ký
```

Làm việc này **ngoài giờ lịch render**, và đóng preview/trình duyệt đang mở file trong trạm
(Windows không cho dời thư mục đang bị giữ).

## 4. Kiểm

```
video-studio doctor --json
```

Mã 3 ⇒ đọc `errors` + `hint`, cài phần thiếu. `--offline` khi không được gọi mạng.

## 5. Tuỳ chọn: bản `video-use` gốc cho việc chỉnh footage

`video-studio edit` đã có bộ helper chưng cất sẵn trong repo — **không cần** bước này. Chỉ cài
khi muốn bám bản upstream hoặc cần đường ASR có phân biệt người nói:

```
pwsh -File scripts/install-video-use.ps1        # Windows
sh scripts/install-video-use.sh                 # macOS / Linux
video-studio init --station <trạm>              # ghi lại vào station.json
video-studio edit --footage <dir> --out <dir> --backend vendored
```

## 6. macOS: ba chỗ khác Windows

1. **Không có PowerShell mặc định** — ba file `scripts/*.ps1` là vỏ tiện cho Windows; trên
   macOS gọi thẳng `video-studio …` (bản cài video-use dùng `scripts/install-video-use.sh`).
2. **Chromium ghim theo bản engine** chưa có sẵn trong cache ⇒ chạy `browser ensure` một lần.
3. **Bóc lời tại máy chạy CPU** (không có CUDA): chậm hơn nhiều. Dùng model nhỏ hơn bằng biến
   `VIDEO_WHISPER_MODEL=medium` nếu chỉ cần mốc thời gian để cắt.

## 7. Gỡ

```
pip uninstall agent-video-studio
```

Trạm **không bị đụng tới**: nó là dữ liệu của bạn. Muốn xoá thì xoá thư mục trạm — sau khi đã
`video-studio backup --out <file>.zip`.
