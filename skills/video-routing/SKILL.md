---
name: video-routing
description: Use when an agent must choose a video product approach, clarify a brief, or set up, check or drive a HyperFrames video station through the video-studio CLI. Covers training, explainers, data news and character stories across engines and styles; not for writing a composition's HTML/CSS/animation or cutting footage by hand.
---

# Định tuyến việc dựng video qua `video-studio`

Skill này là **cửa vào**: nó nói việc nào đi lệnh nào, thứ tự an toàn, và chỗ phải dừng hỏi
người dùng. Mọi lệnh tuân **một hợp đồng**: mã thoát `0` ok · `1` lỗi render (chạy lại được) ·
`2` gọi/cấu hình sai (sửa rồi mới chạy) · `3` thiếu trạm/công cụ (cài tiếp); có `--json` thì
dòng cuối stdout là một dòng JSON, log người đọc ở stderr.

## Chọn hướng sản phẩm

Khi yêu cầu bắt đầu từ mục tiêu người xem, hãy đọc
[`references/product-profiles.md`](references/product-profiles.md) trước khi chọn cách dựng.
Chọn **một nhóm chính** theo điều người xem cần hiểu hoặc làm; video lai có thể có rubric phụ.
Engine, phong cách, nền tảng, khung hình và thời lượng không tự quyết nhóm. Reference cũng nêu
intake gọn và các điểm quyết định cần hỏi.

Khi brief có lỗi chất lượng cụ thể hoặc cần bàn giao output, đọc đúng thẻ trong
[`references/production-techniques.md`](references/production-techniques.md). Đây là checklist
để chọn bước phù hợp; skill hiện có vẫn sở hữu việc thực thi. Với footage quay thật đọc
[`../video-edit/SKILL.md`](../video-edit/SKILL.md); với cleanup vùng trong video đọc
[`../video-cleanup/SKILL.md`](../video-cleanup/SKILL.md). Không mở mọi thẻ nếu brief không gọi tới.

## Bước 1 — chọn đúng tiền kiểm

- Các lệnh cần HyperFrames hoặc trạm: chạy `video-studio doctor --json` trước. Mã `3` ⇒ đọc
  `errors` + `hint`, hướng dẫn người dùng cài phần thiếu (Node ≥ 22, ffmpeg, trạm). Đừng tự cài
  thay khi chưa được giao.
- `cleanup` là luồng FFmpeg độc lập; không cần doctor, Node, HyperFrames hay trạm. Nó tự báo mã
  `3` nếu thiếu ffmpeg/ffprobe.
- `--offline` khi không được phép gọi mạng (không chạy `npx`/`npm`).
- `--check-updates` chỉ **báo** bản HyperFrames mới; nâng bản là việc có chủ đích (render hồi quy
  trước, đổi `HYPERFRAMES_VERSION` sau). Không bao giờ dùng `latest`.

## Bước 2 — trạm: `video-studio init`

Trạm là nơi chứa project, seed, skill cho agent, nháp, cache — **không** nằm trong git.

1. **Máy đã chọn trạm ngoài** (biến `VIDEO_STATION`/`VIDEO_ROOT` đã đặt, hoặc
   `studio.local.json` ghi `separate`): `init` dùng trạm đó, không hỏi. Vẫn nên truyền
   `--station <đường>` **tường minh** để không bao giờ dựng nhầm `workspaces/`.
   `--yes` không bao giờ hỏi: máy đặt `OPCOS_WORKSPACES` thì ra `<biến>/video` (chạy không người cũng
   vậy), không đặt thì ra trạm trong repo (`<repo>/workspaces`); muốn trạm trong repo trên máy có biến:
   `--mode embedded --yes`. Không có biến mà `--non-interactive` thiếu `--yes`/`--mode` ⇒ mã 2. Trạm
   trong repo đã có dữ liệu thì được giữ (có người hỏi "giữ hay chuyển").
2. **Người dùng mới**: trình bảng hai lựa chọn (`init` in sẵn khi không có người trả lời) —
   `embedded` (gọn trong repo, **khuyến nghị**) hay `separate` (trạm ngoài, cho người rành kỹ
   thuật / nhiều máy). **Chờ người dùng chọn**, rồi chạy lại với `--mode …`, `--yes` (không biến: trạm
   trong repo) hoặc `--station DIR` (= separate).
3. **Trạm đời cũ** (project `news/`, `topstory/` còn nằm ở gốc):
   - `video-studio init --station <trạm> --migrate --dry-run` → đọc kế hoạch cùng người dùng.
   - Được đồng ý mới bỏ `--dry-run`. Làm ngoài giờ lịch render; đóng preview/trình duyệt đang
     mở file trong trạm.
   - Di trú chỉ chạm: `news/`, `topstory/` → `projects/`, ghim bản HyperFrames trong
     `package.json`, filler từ trạm giọng, `demo/`, `station.json`, và gỡ bản skill đời cũ đã
     chép vào `.claude/skills` + `.agents/skills` cùng `skills-lock.json` (skill đọc từ repo, trạm
     không giữ bản chép). Mọi thư mục khác ở gốc trạm để nguyên.
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
| Chỉnh một vùng trong video local | `video-studio cleanup inspect|preview|apply|verify` | có; đọc skill `video-cleanup` |
| Zip cả trạm | `video-studio backup --out <file>.zip` | có |
| Chuyển trạm ra ngoài repo | `video-studio migrate --to separate [--station DIR]` (thiếu `--station` thì hỏi nơi dời; agent không có terminal phải hỏi người dùng rồi truyền `--station`) | có |
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
- **Cần xử lý một vùng hoặc logo nhìn thấy trong video đã có**: đọc skill `video-cleanup`; chọn
  ROI, thời gian và method rõ ràng, xem preview, rồi apply ra file mới và verify manifest.
- **Sắp chế một layout mới**: đọc skill `video-theme-library` + `docs/THEME-LIBRARY.md` TRƯỚC —
  chọn từ thư viện rồi mới sáng tác.
- **Người dùng hỏi "đồ của tôi nằm đâu / xoá được không"**: `docs/WORKSPACE.md`.

## Biến môi trường

`VIDEO_STATION` (gốc trạm; tên cũ `VIDEO_ROOT`) · `HYPERFRAMES_VERSION` (bản cụ thể x.y.z) ·
`HYPERFRAMES_WORKDIR` · `NODE_DIR` · `FFMPEG_DIR` · `VIDEO_FONT` · `CHROME_BIN` ·
`VOICE_STATION` (trạm giọng cho lồng tiếng).
