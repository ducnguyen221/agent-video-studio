---
title: Agent guide
summary: How an agent drives this studio end to end - check the machine, lay out a station, render from a spec, narrate, preview, and cut real footage - with the failure modes that matter.
audience: agents (and humans reading over their shoulder)
---

# Hướng dẫn cho agent — dựng video bằng `video-studio`

Hai mảnh ghép:

- **HyperFrames** (gọi qua `npx hyperframes@<bản ghim>`) — viết HTML/CSS/GSAP → render **MP4 câm**.
- **Trạm giọng** (`agent-voice-studio`, cài trong cùng venv) — đọc lời dẫn tiếng Việt rồi ghép
  vào video.

Repo này là lớp ở giữa: nó biết trạm nằm đâu, bản engine nào, template nào, và biến mọi thứ hỏng
thành **mã thoát có nghĩa** thay vì traceback.

## A. Hợp đồng chung của mọi lệnh

| Mã thoát | Nghĩa | Việc phải làm |
|---|---|---|
| 0 | xong | — |
| 1 | engine/render hỏng giữa chừng | chạy lại có thể qua; đọc log stderr |
| 2 | gọi sai / cấu hình sai | **sửa rồi mới chạy lại** — chạy lại y nguyên là vô ích |
| 3 | thiếu trạm hoặc công cụ | cài tiếp; `video-studio doctor` chỉ đúng thứ còn thiếu |

Có `--json` thì **dòng cuối stdout** là một dòng JSON; mọi log người đọc nằm ở stderr. Gọi từ
PowerShell thì đọc `$LASTEXITCODE`, **đừng** `2>&1` (PS 5.1 biến mỗi dòng stderr thành lỗi và
`$?` thành `False` dù mã thoát là 0).

## B. Thứ tự an toàn

```
video-studio doctor --json          # máy đủ chưa (node ≥ 22, ffmpeg, Chromium, font, trạm)
video-studio init --station <trạm>  # dựng trạm (xem docs/WORKSPACE.md cho hai chế độ)
video-studio render …               # spec JSON → video theo template
video-studio narrate …              # video câm + lời dẫn → video có giọng
video-studio preview --project …    # soi trên trình duyệt (chạy tới khi Ctrl+C)
video-studio edit …                 # cắt footage quay thật
```

## C. Dựng video từ dữ liệu: `render`

```
video-studio render --project topstory --input spec.json --out <thư mục> --json
```

`--project` chọn **template** (`news` · `news-weekly` · `topstory` · `repo-today`), `--input` là
**spec** `schema_version: 1` — xem `docs/CONTRACT.md`. Bốn khối hợp đồng của spec: `brand`,
`voice`, `bgm`, `outputs`; phần còn lại là nội dung.

**`brand` là bắt buộc.** Thiếu nó là mã 2 chứ không phải một mặc định âm thầm: engine không mang
sẵn tên hay tên miền của ai, nên "quên khai brand" không bao giờ ra một video mang danh tính của
người khác.

Ảnh và clip khai bằng đường **tương đối so với file spec**. `--brand brand.json` để tách phần
thương hiệu ra dùng lại cho nhiều số báo.

## D. Lồng tiếng: `narrate`

```
video-studio narrate --video silent.mp4 --file loi-dan.txt --out final.mp4 --profile <tên> --json
video-studio narrate --project demo --text "Xin chào…" --out final.mp4        # render rồi lồng tiếng
```

- `--mode fit` (mặc định): giọng dài hơn thì **giữ khung hình cuối**; video dài hơn thì **đệm im
  lặng**. `--mode shortest` cắt theo cái ngắn hơn.
- `--profile` ghim một giọng cho cả video. Đừng dùng `--instruct` cho bản giao: nó thiết kế lại
  giọng theo từ khoá và cho ra **một giọng khác cho mỗi câu**.
- `--bgm <style|none>` trộn nhạc nền dưới giọng; thư viện nhạc nằm ở trạm giọng.
- Với `--project`, bản render câm trung gian nằm trong `<trạm>/scratch/` và bị dọn sau khi xong
  (giữ lại bằng `--keep-silent`) — không bao giờ rơi vào thư mục bạn giao cho người khác.

## E. Xem trước: `preview`

```
video-studio preview --project demo [--port 5173]
```

Chạy tới khi Ctrl+C; **đừng gọi trong lịch chạy tự động**. Nó dùng **đúng bản engine đã ghim** —
soi bằng một bản khác là soi một video khác.

## F. Cắt footage quay thật: `edit`

```
video-studio edit --footage <thư mục quay> --out <thư mục ra>            # bóc lời + gom cụm
video-studio edit --footage … --out … --edl edl.json --build-subtitles   # dựng bản cắt
```

Không có `edl.json` thì lệnh **dừng ở bước gom cụm** và in bước tiếp theo: đọc `takes_packed.md`,
chọn đoạn, viết EDL. Quy trình đầy đủ + luật cứng: skill `video-edit`.

## G. Biến môi trường

| Biến | Nghĩa |
|---|---|
| `VIDEO_STATION` | gốc trạm video (tên cũ `VIDEO_ROOT` còn đọc được, kèm cảnh báo) |
| `HYPERFRAMES_VERSION` | bản engine — **phải là `x.y.z`**; `latest`/`^`/`~` bị từ chối bằng mã 2 |
| `HYPERFRAMES_WORKDIR` | thư mục chứa project render |
| `NODE_DIR`, `FFMPEG_DIR` | nơi có node/npx và ffmpeg/ffprobe nếu chúng không trên PATH |
| `VIDEO_FONT` | font đứng đầu stack chữ |
| `CHROME_BIN` | Chrome cho công cụ chụp ảnh ngoài HyperFrames |
| `VOICE_STATION` | trạm giọng (lồng tiếng, filler); tên cũ `OMNIVOICE_DIR` trỏ thư mục engine |
| `VIDEO_STUDIO_REPO` | chỉ thẳng bản clone repo (khi không cài `-e`) |

## H. Bốn chỗ hay hỏng

1. **Bản engine trôi.** `latest` làm lượt render đêm nay khác lượt tuần sau mà không ai đổi gì.
   Ở đây bản trôi bị từ chối ngay ở tầng cấu hình; nâng bản là việc có chủ đích: render hồi quy
   rồi mới đổi `HYPERFRAMES_VERSION`. `doctor --check-updates` chỉ **báo**.
2. **Hai nguồn sự thật.** Vừa có `workspace/` trong repo vừa có trạm ngoài ⇒ `doctor` trả mã 3.
   Giữ MỘT trạm.
3. **Đường tuyệt đối trong composition.** Không chạy được trên máy khác, và dấu `:` của ổ đĩa
   Windows còn làm vỡ filtergraph của ffmpeg.
4. **Quên `brand` trong spec.** Mã 2 — đúng như thiết kế.

## I. Nâng bản engine

```
video-studio doctor --check-updates --json     # chỉ báo, không bao giờ tự nâng
video-studio doctor --hf <bản mới>             # thử máy với bản mới
HYPERFRAMES_VERSION=<bản mới> video-studio render …   # render hồi quy rồi so
```

Chỉ khi bản mới ra video tương đương (so khung hình + thời lượng ± 1 s) mới đổi bản ghim trong
`station.json`. Hoàn tác: đổi `HYPERFRAMES_VERSION` về bản cũ.
