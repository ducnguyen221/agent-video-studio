---
name: video-routing
description: Use when an agent must set up, check or drive a HyperFrames video station through the video-studio CLI - installing the engine, laying out or migrating a station, diagnosing a machine that cannot render, or choosing which video-studio command fits a request. Not for writing a composition's HTML/CSS/animation itself or for cutting real footage by hand.
---

# Định tuyến việc dựng video qua `video-studio`

Skill này là **cửa vào**: nó nói việc nào đi lệnh nào, thứ tự an toàn, và chỗ phải dừng hỏi
người dùng. Mọi lệnh tuân **một hợp đồng**: mã thoát `0` ok · `1` lỗi render (chạy lại được) ·
`2` gọi/cấu hình sai (sửa rồi mới chạy) · `3` thiếu trạm/công cụ (cài tiếp); có `--json` thì
dòng cuối stdout là một dòng JSON, log người đọc ở stderr.

## Bước 1 — máy đã sẵn chưa: `video-studio doctor`

- Chạy `video-studio doctor --json` trước mọi việc khác. Mã `3` ⇒ đọc `errors` + `hint`, hướng
  dẫn người dùng cài phần thiếu (Node ≥ 22, ffmpeg, trạm). Đừng tự cài thay khi chưa được giao.
- `--offline` khi không được phép gọi mạng (không chạy `npx`/`npm`).
- `--check-updates` chỉ **báo** bản HyperFrames mới; nâng bản là việc có chủ đích (render hồi quy
  trước, đổi `HYPERFRAMES_VERSION` sau). Không bao giờ dùng `latest`.

## Bước 2 — trạm: `video-studio init`

Trạm là nơi chứa project, seed, skill cho agent, nháp, cache — **không** nằm trong git.

1. **Máy đã có trạm ngoài** (biến `VIDEO_STATION`/`VIDEO_ROOT` đã đặt, hoặc `~/.video` đã có
   `station.json`, `projects/` hay seed `demo/` đời cũ): `init` tự chọn `separate`, không hỏi.
   Vẫn nên truyền `--station <đường>` **tường minh** để không bao giờ dựng nhầm `workspace/`.
2. **Người dùng mới**: trình bảng hai lựa chọn (`init` in sẵn khi không có người trả lời) —
   `embedded` (gọn trong repo, **khuyến nghị**) hay `separate` (trạm ngoài, cho người rành kỹ
   thuật / nhiều máy). **Chờ người dùng chọn**, rồi chạy lại với `--mode …`, `--yes` (= embedded)
   hoặc `--station DIR` (= separate).
3. **Trạm đời cũ** (project `news/`, `topstory/` còn nằm ở gốc):
   - `video-studio init --station <trạm> --migrate --dry-run` → đọc kế hoạch cùng người dùng.
   - Được đồng ý mới bỏ `--dry-run`. Làm ngoài giờ lịch render; đóng preview/trình duyệt đang
     mở file trong trạm.
   - Di trú chỉ chạm: `news/`, `topstory/` → `projects/`, ghim bản HyperFrames trong
     `package.json`, filler từ trạm giọng, `demo/`, skill trong `.claude/skills` + `.agents/skills`,
     `skills-lock.json`, `station.json`. Mọi thư mục khác ở gốc trạm để nguyên.
   - Sai thì `video-studio init --station <trạm> --undo` (file người dùng đã sửa sau lần init
     được giữ lại và báo tên).

## Bảng lệnh

| Việc | Lệnh | Trạng thái |
|---|---|---|
| Kiểm máy + trạm | `video-studio doctor [--json] [--hf x.y.z] [--check-updates] [--offline]` | có |
| Dựng / di trú / hoàn tác trạm | `video-studio init [--station DIR] [--migrate] [--dry-run] [--undo]` | có |
| Spec JSON → video theo template | `video-studio render --project <template> --input <spec> --out <thư mục>` | có |
| Lồng tiếng cho video câm | `video-studio narrate --video <mp4>\|--project <tên> --text\|--file … --out <mp4>` | có |
| Xem trước project | `video-studio preview [--project <tên\|thư mục>]` | có |
| Chỉnh footage quay thật | `video-studio edit --footage <dir> --out <dir> [--edl edl.json]` | có |
| Zip cả trạm | `video-studio backup --out <file>.zip` | có |
| Chuyển trạm ra ngoài repo | `video-studio migrate --to separate [--station DIR]` | có |
| Cập nhật bản clone | `video-studio update` | có |
| Đóng gói / nhập dữ liệu cá nhân | `video-studio export` · `import` | chưa có trong bản này |

Lệnh "chưa có" trả mã `2` kèm lời báo — đừng thử lại, báo người dùng.

## Bước 3 — chọn đúng việc

- **Dựng video từ DỮ LIỆU** (bản tin, deep-dive, repo hôm nay): `render` + một spec
  `schema_version: 1`. `brand` bắt buộc; thiếu là mã 2. Khuôn spec: `docs/CONTRACT.md`.
- **Đã có video câm, cần giọng**: `narrate`. Ghim `--profile`, đừng dùng `--instruct` cho bản
  giao (mỗi câu một giọng khác).
- **Có footage quay thật**: `edit` → đọc skill `video-edit` trước khi cắt; quy trình là hỏi →
  chốt → dựng, không phải một nút bấm.
- **Sắp chế một layout mới**: đọc skill `video-theme-library` + `docs/THEME-LIBRARY.md` TRƯỚC —
  chọn từ thư viện rồi mới sáng tác.
- **Người dùng hỏi "đồ của tôi nằm đâu / xoá được không"**: `docs/WORKSPACE.md`.

## Biến môi trường

`VIDEO_STATION` (gốc trạm; tên cũ `VIDEO_ROOT`) · `HYPERFRAMES_VERSION` (bản cụ thể x.y.z) ·
`HYPERFRAMES_WORKDIR` · `NODE_DIR` · `FFMPEG_DIR` · `VIDEO_FONT` · `CHROME_BIN` ·
`VOICE_STATION` (trạm giọng cho lồng tiếng).
