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
| **Python ≥ 3.10** | chính package này | `winget install Python.Python.3.12` | `brew install python@3.12` — rồi gọi đích danh `python3.12` |
| **Font Inter** | stack chữ mặc định của template | tải từ rsms.me/inter → Install | `brew install --cask font-inter` |

**Mac mới tinh** cần hai thứ trước cả bảng trên: Xcode Command Line Tools
(`xcode-select --install`, người dùng bấm Install trong hộp thoại) và Homebrew (người dùng tự cài
theo brew.sh — agent không chạy lệnh cài đó thay họ). Homebrew trên Apple Silicon nằm ở
`/opt/homebrew/bin`, thư mục này phải có trên `PATH`. `python3` sẵn có của Mac là 3.9 (đi kèm
Command Line Tools), không đủ.

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
python3.12 -m venv .venv           # Windows: py -3 -m venv .venv
.venv/bin/python -m pip install -e .   # Windows: .\.venv\Scripts\python -m pip install -e .
.venv/bin/video-studio --version
```

### Cài vào venv nào — câu hỏi quan trọng nhất của phần này

| Bạn định làm gì | Cài vào đâu |
|---|---|
| Render **có lồng tiếng** (mọi template bản tin đều đọc lời dẫn) | **`.venv` của repo này** — clone `agent-voice-studio` cạnh repo này rồi `pip install -e "../agent-voice-studio[engine]"` vào chính `.venv` đó |
| Chỉ render **câm**, hoặc chỉ dùng `init`/`doctor`/`edit` | `.venv` của repo này, không cần repo giọng |

Lồng tiếng đi qua `import voice_studio` **trong cùng tiến trình**: model giọng nặng hàng GB, nạp
một lần cho cả bài. Hai venv khác nhau thì không có đường nào để import, và lỗi sẽ hiện ra ở
giữa lượt render chứ không phải lúc cài. Đây là đường **duy nhất** tài liệu này hướng dẫn cho
người dùng thường (chế độ embedded, không biến môi trường); lệnh đầy đủ cho từng hệ điều hành —
torch đúng phần cứng, `voice-studio init --yes`, tạo giọng mặc định — ở
[INSTALL.md mục 5b](../INSTALL.md#5b-lồng-tiếng-tuỳ-chọn-nặng--hỏi-trước). Cần **`-e`**: repo
giọng tìm trạm của nó (`../agent-voice-studio/workspace/`) qua bản clone.

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
trước (`pip install -e "../agent-voice-studio[engine]"`, như bảng trên), rồi extras chỉ còn kiểm
hộ bạn.

## 3. Dựng trạm

```
video-studio init                            # trình bảng hai lựa chọn rồi chờ bạn chọn
video-studio init --yes                      # nhận khuyến nghị (embedded), không hỏi
video-studio init --mode separate            # chọn thẳng chế độ, không hỏi
video-studio init --station <thư mục trạm>  # hoặc chỉ thẳng một trạm (= separate, không hỏi)
video-studio init --non-interactive --yes    # CI / lịch chạy: không hỏi và không đoán
```

**`embedded` là mặc định và là khuyến nghị**: trạm ở `<repo>/workspace/`, biến cấu hình ở
`<repo>/.env`, bấm Enter là xong, không phải đặt biến môi trường nào. Chọn `separate` khi bạn
dùng nhiều máy, rành kỹ thuật, hoặc repo này là bản public của chính bạn. Agent cài nên **phân
tích rồi khuyến nghị**, không hỏi trống.

`init` **chỉ bỏ qua câu hỏi khi trạm đã được chọn**. Máy đã đặt biến `VIDEO_STATION`/`VIDEO_ROOT`
(hoặc `studio.local.json` đã ghi `separate`) thì bản trần dùng trạm đó và nói rõ lý do. `~/.video`
chỉ tình cờ mang dấu trạm thì **không** tự nhận: `init` hỏi; với `--yes` hay khi không có người trả
lời, nó in đường trạm cũ rồi thoát **mã 2** — nhận trạm đó phải bằng `--mode separate`,
`--station <thư mục>` hoặc `--migrate`. Xin `embedded` khi máy đã có trạm ngoài là **lỗi mã 2**
("hai nguồn sự thật") chứ không phải một cảnh báo — muốn dựng trạm trong repo thì gỡ biến hoặc
dời trạm cũ trước.

Không có ai trả lời (CI, scheduled task) mà chưa chọn ⇒ `init` in bảng lựa chọn rồi thoát
**mã 2, chưa ghi byte nào**. Cờ `--non-interactive` tự khai "không có ai ngồi đây"; nó **không**
có nghĩa "đoán hộ tôi", nên thiếu `--yes`/`--mode`/`--station` thì vẫn là mã 2.

### `.env` ở chế độ embedded

`init` chép `.env.example` (khuôn tên biến, không có giá trị) thành `<repo>/.env`, quyền 600
trên POSIX; chạy lại **không đè** file bạn đã điền. Thứ tự đọc một biến: **biến môi trường thật
→ `<repo>/.env` (chỉ khi `mode = embedded`) → chưa đặt**.

Ba biến trỏ trạm này (`VIDEO_STATION`, `VIDEO_ROOT`, `VIDEO_STUDIO_REPO`) và mấy biến mã đọc
thẳng từ `os.environ` **không** đọc được từ `.env` — chúng được đánh dấu `[MÔI TRƯỜNG THẬT]`
ngay trong khuôn, kèm lý do. `VOICE_STATION` thì đọc được: nó trỏ sang trạm của repo khác.

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

Mỗi dòng mang một trong bốn nhãn: `PASS` (đã kiểm, đạt) · `WARN` (thiếu phần tuỳ chọn, không
chặn) · `FAIL` (hỏng, mã ≠ 0) · `NOT_CHECKED` (**chưa kiểm được** — không mạng, thiếu thứ đứng
trước, hoặc việc doctor không bao giờ tự làm). `NOT_CHECKED` không phải lỗi cài, nhưng cũng
không phải xác nhận: dòng `render` luôn ở mức này, vì chỉ một lần dựng bài mẫu
([samples/news-mini](../samples/news-mini/EXPECTED.md)) mới chứng minh được cả chuỗi. Trong
JSON, các dòng đó nằm ở danh sách `not_checked`.

## 5. Tuỳ chọn: bản `video-use` gốc cho việc chỉnh footage

`video-studio edit` đã có bộ helper chưng cất sẵn trong repo — **không cần** bước này. Chỉ cài
khi muốn bám bản upstream hoặc cần đường ASR có phân biệt người nói:

```
pwsh -File scripts/install-video-use.ps1        # Windows
sh scripts/install-video-use.sh                 # macOS / Linux
video-studio init --station <trạm>              # ghi lại vào station.json
video-studio edit --footage <dir> --out <dir> --backend vendored
```

## 6. macOS: những chỗ khác Windows

1. **`python3` là 3.9** trên Mac mới — tạo venv bằng `python3.12`, không bằng `python3`.
2. **Shell của agent không nạp `~/.zshrc`/`~/.zprofile`.** Biến môi trường hay `PATH` người dùng
   đặt ở đó có thể vô hình với agent; kiểm bằng `zsh -lic 'echo $TÊN_BIẾN'` (hoặc `$PATH`) thay vì
   `echo` trong shell của agent. Người dùng embedded không cần biến nào — `workspace/` tự phân giải.
3. **Không có PowerShell mặc định** — ba file `scripts/*.ps1` là vỏ tiện cho Windows; trên
   macOS gọi thẳng `video-studio …` (bản cài video-use dùng `scripts/install-video-use.sh`).
4. **Chromium ghim theo bản engine** chưa có sẵn trong cache ⇒ chạy
   `npx --yes hyperframes@<bản ghim> browser ensure` một lần (cần mạng). Repo không có lệnh
   con `browser` nào; `doctor` in đúng lệnh `npx` với bản đang ghim.
5. **Bóc lời tại máy chạy CPU** (không có CUDA): chậm hơn nhiều. Dùng model nhỏ hơn bằng biến
   `VIDEO_WHISPER_MODEL=medium` nếu chỉ cần mốc thời gian để cắt.

## 7. Nền tảng: cái gì đã chạy thật, cái gì chưa

| Nền tảng | Bộ khung (CLI, trạm, test) | Render thật |
|---|---|---|
| Windows | đã chạy thật | đã chạy thật |
| macOS (Apple Silicon) | CI chạy mỗi lần đẩy mã: cài gói + toàn bộ test | **bài mẫu `news-mini` đã chạy thật** (Mac mini M1, 30/09/2026, số đo ở `samples/news-mini/EXPECTED.md`). CI **cố ý** không cài Node, HyperFrames, ffmpeg hay model. Bản HyperFrames đang ghim (0.8.54) chưa dựng bài `topstory` thật nào |
| Linux | CI chạy cổng đối chiếu skill với `upstream.json` | **chưa kiểm** |

Thứ đã được chứng minh trên mọi nền tảng là **bộ khung**: lệnh chạy, trạm dựng đúng, hợp đồng gọi
và mã thoát giữ nguyên. Render thật có số đo trên Windows và macOS arm64 (bài mẫu). Trên Mac, các
chỗ ở mục 6 là chỗ dễ vấp nhất — chạy `browser ensure` (dạng `npx` ở trên) một lần rồi
`doctor --json` trước khi tin vào bất cứ lịch chạy nào.

## 8. Gỡ

```
video-studio uninstall --dry-run     # xem trước sẽ gỡ gì
video-studio uninstall               # gỡ phần bộ cài đã đặt
pip uninstall agent-video-studio     # rồi mới gỡ package
```

`uninstall` chỉ gỡ thứ `init` đã đặt vào: `studio.local.json`, skill mà bản trước 0.2.0 đã chép
vào trạm (bản bạn đã sửa thì giữ), `.env` nếu còn y hệt `.env.example`, và hook `pre-commit` do chính nó cài.
Thứ bị gỡ được **dời** vào `<trạm>/.video-studio/runs/<id>/prev/`, không xoá thẳng; cài lại chỉ
cần `video-studio init`.

Trạm **không bị đụng tới**: nó là dữ liệu của bạn. Muốn xoá thì xoá thư mục trạm — sau khi đã
`video-studio backup --out <file>.zip`.
