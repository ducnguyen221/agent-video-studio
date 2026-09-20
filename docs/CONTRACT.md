---
title: video-studio calling contract
status: stable
api_version: "1.0.0"
schema_version: 1
audience: pipelines, schedulers, agents
---

# Hợp đồng gọi `video-studio`

Tài liệu này là thứ bên gọi cần đọc — pipeline marketing, lịch chạy nền, hay một agent khác.
Hợp đồng gồm **bốn điều**: mã thoát · một dòng JSON cuối stdout · biến môi trường · spec dữ
liệu. Giữ nguyên bốn điều đó thì bên trong engine đổi thế nào cũng không làm hỏng bên gọi.

Cùng một hợp đồng với `voice-studio`, cố ý: một người viết script chỉ phải học một lần.

## 1. Mã thoát

| Mã | Nghĩa | Bên gọi nên làm gì |
|---|---|---|
| `0` | xong | đọc dòng JSON cuối, lấy danh sách file |
| `1` | lỗi engine / render | **chạy lại được** — render sập, hết bộ nhớ, worker chết |
| `2` | hợp đồng sai | **sửa cấu hình rồi mới chạy lại** — thiếu tham số, spec thiếu `brand`, bản HyperFrames không phải bản cụ thể |
| `3` | trạm / công cụ thiếu | **cài tiếp** — chưa có trạm video, thiếu Node hay ffmpeg; chạy `video-studio doctor` |

Phân biệt 1 với 2–3 là để lịch chạy biết **khi nào thử lại là vô ích**. Retry một lỗi hợp đồng
chỉ tạo ra ba lần hỏng thay vì một.

> **Bẫy PowerShell 5.1:** đừng `2>&1` khi gọi lệnh native — mỗi dòng stderr bị bọc thành
> ErrorRecord và `$?` thành `False` dù mã thoát là 0. Đọc `$LASTEXITCODE`.

## 2. Một dòng JSON cuối stdout

Với `--json`, **dòng cuối không rỗng của stdout** là JSON; mọi log cho người đọc đi ra stderr.
Bên gọi lấy dòng cuối — log lạc vào stdout phía trước vẫn không làm hỏng việc parse.

Thành công:

```json
{"ok": true,
 "project": "topstory",
 "out": "<thư mục ra>",
 "outputs": [{"kind": "long",  "path": "…/2026-01-02-top.mp4",       "duration": 372.4},
             {"kind": "short", "path": "…/2026-01-02-top-short.mp4", "duration": 78.1}],
 "timings": {"total": 812.5},
 "engine": {"hyperframes": "0.8.54", "voice_studio": "0.2.0", "video_studio": "0.1.0.dev0",
            "contract": "1.0.0"}}
```

Hỏng:

```json
{"ok": false, "code": 2, "error": "spec.json: brand thiếu khoá bắt buộc: site"}
```

`duration` là `null` khi không đo được (thiếu `ffprobe`) — đó không phải lỗi render.

## 3. Biến môi trường

| Biến | Vai trò |
|---|---|
| `VIDEO_STATION` | gốc trạm video (mặc định `~/.video`). Tên cũ `VIDEO_ROOT` còn đọc được, kèm cảnh báo |
| `HYPERFRAMES_VERSION` | bản HyperFrames gọi qua npx — **phải là `x.y.z`**; một dải bản không xác định bị từ chối với mã 2 |
| `HYPERFRAMES_WORKDIR` | thư mục chứa project render (mặc định `<trạm>/projects`) |
| `NODE_DIR`, `FFMPEG_DIR` | thư mục chứa `node`/`npx`, `ffmpeg`/`ffprobe` (rỗng = tìm trên PATH) |
| `VIDEO_FONT` | font đứng đầu stack chữ (mặc định stack bắt đầu bằng Inter) |
| `CHROME_BIN` | Chrome cho công cụ chụp ảnh ngoài HyperFrames (tuỳ chọn) |
| `VOICE_STATION` | trạm giọng (lồng tiếng, filler). Tên cũ `OMNIVOICE_DIR` = thư mục engine |

Vì sao bản HyperFrames phải là bản cụ thể: một lịch chạy lúc 18h không được đổi engine giữa
đêm. Nâng bản là việc **có chủ đích** — `video-studio doctor --check-updates` chỉ báo, không tự
nâng.

## 4. Spec dữ liệu (`schema_version: 1`)

`video-studio render --project <tên> --input <spec.json> --out <thư mục>` đọc một file JSON.
Thân nội dung GIỮ NGUYÊN khuôn sidecar cũ, cộng thêm bốn khối hợp đồng:

```jsonc
{
  "schema_version": 1,

  "brand": {                       // BẮT BUỘC — xem mục 5
    "a": "Tên", "b": "Phần sau",   // tên hai phần: a <accent>b</accent>
    "site": "noi-doc-o-outro.example",
    "accent": ["#00E5FF", "#A78BFA"],        // tuỳ chọn
    "logo": "logo.svg",                      // tuỳ chọn
    "pronounce": {"noi-doc\\.example": "cách đọc"}   // tuỳ chọn, {regex: cách đọc}
  },

  "voice":   {"profile": "<tên profile giọng>", "speed": 1.0, "seed": 1234},
  "bgm":     {"style": "lofi"},            // hoặc "none" / {"style": null}
  "outputs": {"long": true, "short": "ten-file.mp4"},   // true | false | tên file

  // … phần nội dung, y như sidecar cũ:
  "date": "2026-01-02", "display_date": "Thứ Sáu · 02/01/2026",
  "week": "", "range": "",
  "top_story": {"sections": [ … ]},        // project topstory
  "daily_video": {"intro": "…", "outro": "…", "segments": [ … ]},   // project news
  "weekly_video": { … },                   // project news-weekly
  "scenes": [ … ]                          // project repo-today
}
```

Bốn `--project` hiện có:

| project | Nội dung đọc từ | Ra |
|---|---|---|
| `news` | `daily_video` / `weekly_video` / `segments` | recap 16:9 + short 9:16, cách diễn đạt bản NGÀY |
| `news-weekly` | như trên | recap 16:9 + short 9:16, cách diễn đạt bản TUẦN |
| `topstory` | `top_story.sections` | deep-dive một tin: long 16:9 + short 9:16 |
| `repo-today` | `scenes` | deep-dive nhiều cảnh (news v2), chỉ 16:9 |

Hai cờ đè lên spec, dùng khi một spec chạy cho nhiều kênh:
`--brand <brand.json>` (trộn lên khối `brand`) và `--voice-profile <tên>`.

Đường dẫn tương đối trong spec (ảnh, clip) neo vào **thư mục chứa spec**, không vào thư mục
hiện hành — để `cd` ở đâu thì kết quả vẫn như nhau.

`voice.seed`: engine giọng **không tái lập nếu không ghim seed**. Và cùng một seed trên hai
loại thiết bị khác nhau (CUDA vs MPS) vẫn cho waveform khác — tái lập chỉ có nghĩa trên cùng
một loại thiết bị.

## 5. `brand` bắt buộc — và vì sao

Engine **không có thương hiệu mặc định**. Thiếu `brand.a`, `brand.b` hay `brand.site` là mã 2,
không có đường lùi im lặng.

Bản tiền thân của template này mang sẵn tên thương hiệu và tên miền của một người ngay trong
mã. Hệ quả không phải là "xấu về mặt thẩm mỹ": ai cài repo về mà quên khai brand vẫn render ra
video, và video đó **mang danh tính của người khác** — đúng chỗ khán giả nhìn và đúng câu mà
giọng đọc lên ở outro. Một mặc định im lặng ở đây là một lỗi phát tán.

Cùng lý do đó, `brand.pronounce` thay cho bảng sửa phát âm nằm cứng trong mã: tên miền, tên
riêng và từ viết tắt của mỗi thương hiệu một khác, engine không đoán hộ.

## 6. Gọi từ đâu

```bash
video-studio render --project topstory --input spec.json --out ./out --json
```

```powershell
$out = video-studio render --project news --input spec.json --out .\out --json
if ($LASTEXITCODE -eq 0) { ($out | Select-Object -Last 1 | ConvertFrom-Json).outputs }
```

```python
import json, subprocess
p = subprocess.run(["video-studio", "render", "--project", "news",
                    "--input", spec, "--out", out_dir, "--json"],
                   capture_output=True, text=True)      # argv list, không qua shell
if p.returncode == 0:
    data = json.loads([ln for ln in p.stdout.splitlines() if ln.strip()][-1])
```

Mọi lệnh đều nhận `--help` và trả mã 0 cho `--help`; tham số sai trả mã 2.
