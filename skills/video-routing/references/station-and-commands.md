# Trạm và bảng lệnh

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
| Spec JSON → video theo template | `video-studio render --project <template> --input <spec> --out <thư mục> [--images <images.json>]` | có |
| Lồng tiếng cho video câm | `video-studio narrate --video <mp4>\|--project <tên> --text\|--file … --out <mp4>` | có |
| Xem trước project | `video-studio preview [--project <tên\|thư mục>]` | có |
| Chỉnh footage quay thật | `video-studio edit --footage <dir> --out <dir> [--edl edl.json]` | có |
| Chỉnh một vùng trong video local | `video-studio cleanup inspect\|preview\|apply\|verify` | có; đọc skill `video-cleanup` |
| Đọc video mẫu, lập hồ sơ nguồn, kiểm tài sản | `video-studio reference init\|frames\|tiles\|transcribe\|fetch\|audit` | có; đọc skill `video-reference-analysis` rồi `video-remix-brief`; `fetch` chỉ in kế hoạch, tải cần `--go` và phép đích danh |
| Zip cả trạm | `video-studio backup --out <file>.zip` | có |
| Chuyển trạm ra ngoài repo | `video-studio migrate --to separate [--station DIR]` (thiếu `--station` thì hỏi nơi dời; agent không có terminal phải hỏi người dùng rồi truyền `--station`) | có |
| Cập nhật bản clone | `video-studio update` | có |
| Đóng gói / nhập dữ liệu cá nhân | `video-studio export` · `import` | chưa có trong bản này |

Lệnh "chưa có" trả mã `2` kèm lời báo — đừng thử lại, báo người dùng.
