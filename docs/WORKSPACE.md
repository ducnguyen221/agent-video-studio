---
title: Workspace
summary: What the video station holds, the two install modes (embedded vs separate), which folders are safe to delete, and what goes into a backup.
audience: anyone who has to answer "where does my stuff live?"
---

# Trạm video — từng thư mục là gì

Repo `agent-video-studio` chỉ chứa **mã**. Mọi thứ của riêng bạn — project đang dựng, footage,
spec, nháp, cache — nằm ở **trạm video**.

## Hai chế độ đặt trạm

| Chế độ | Trạm | Dành cho |
|---|---|---|
| **`embedded`** — gọn trong repo (**mặc định, khuyến nghị cho người mới**) | `<repo>/workspace/` | một máy, "mở một folder là thấy hết" |
| **`separate`** — trạm ngoài repo | `~/.video` (hoặc nơi bạn chọn) | nhiều máy, repo public của chính bạn, nhiều repo dùng chung một trạm |

`video-studio init` hỏi bạn chọn (Enter = `embedded`) và ghi lựa chọn vào
`<repo>/studio.local.json`. **Không hỏi** trong ba trường hợp:

- `--station DIR` — bạn chỉ thẳng trạm ⇒ `separate`.
- Máy **đã có trạm ngoài**: biến `VIDEO_STATION` (hoặc tên cũ `VIDEO_ROOT`) đã đặt, hoặc
  `~/.video` đã có `station.json`, `projects/`, hay seed `demo/` đời cũ ⇒ tự `separate`, và
  **không bao giờ** tạo `workspace/`. Hai trạm cho một repo là hai nguồn sự thật, và cái sai chỉ
  lộ ra khi bạn "mất" một project.
- `--mode embedded|separate`, hoặc `--yes` (= nhận khuyến nghị `embedded`).

Chạy không có người trả lời (agent, script, lịch) mà chưa chọn ⇒ `init` in bảng lựa chọn rồi
thoát **mã 2**. **Agent cài phải trình bảng đó cho người dùng và chờ họ chọn** — không tự chọn
im lặng.

Xem trước, không ghi gì: `video-studio init --dry-run`.

### Thứ tự tìm trạm (mọi lệnh dùng chung một hàm)

```
--station  →  VIDEO_STATION  →  VIDEO_ROOT (tên cũ)  →
<repo>/studio.local.json  →  <repo>/workspace/ nếu có  →  ~/.video
```

`<repo>` là bản clone đã `pip install -e` (hoặc đặt `VIDEO_STUDIO_REPO`). Bản cài wheel không có
repo — chỉ dùng được `separate`.

## Cây trạm

```
<trạm>/
├── station.json            QUẢN LÝ  cấu hình trạm: bản engine đã ghim, projects_dir, video-use, trạm giọng
├── demo/                   MẪU      project seed để thử và để chép cấu hình cho project mới
├── projects/               CONTENT  mỗi thư mục con là một project render
│   └── <tên>/assets/       CONTENT  ảnh, clip, filler của project đó
├── templates/              CONTENT  brand.json, spec mẫu của riêng bạn
├── .claude/skills/         QUẢN LÝ  skill cho agent, chép từ repo
├── .agents/skills/         QUẢN LÝ  bản song sinh cho harness khác
├── skills-lock.json        QUẢN LÝ  hash từng skill đã chép (để biết bản trong trạm còn khớp repo không)
├── .video-studio/runs/     QUẢN LÝ  nhật ký từng lần `init` + bản cũ của thứ bị thay (cho `--undo`)
├── scratch/                NHÁP     bản render câm trung gian, dữ liệu tạm
├── cache/                  NHÁP     cache công cụ
└── video-use/              TUỲ CHỌN bản upstream cho `edit --backend vendored`
```

Thư mục KHÁC ở gốc trạm (dự án riêng, bản vendored, nhạc, log cũ) **engine không bao giờ chạm
tới** — `init` có một danh sách cho phép và một rào chắn trong mã để chặn cả lỗi lập trình.

| Thư mục | Xoá được? | Vào backup? | Nhạy cảm? |
|---|---|---|---|
| `station.json` | dựng lại bằng `init` | có | không |
| `demo/` | dựng lại bằng `init` | có | không |
| `projects/` | **KHÔNG** — việc của bạn | có | có thể (footage, ảnh chưa công bố) |
| `templates/` | **KHÔNG** | có | có (brand là danh tính của bạn) |
| `.claude/skills`, `.agents/skills`, `skills-lock.json` | dựng lại bằng `init` | có | không |
| `.video-studio/` | xoá được, mất khả năng `--undo` | không | không |
| `scratch/`, `cache/` | xoá thoải mái | không | không |
| `video-use/` | cài lại bằng script | không (có venv riêng, nặng) | không |

## Chế độ `embedded`: hai lớp rào

Trạm nằm TRONG repo, nên trước khi có byte dữ liệu nào ở đó phải có đủ:

1. **`.gitignore`** chặn `workspace/`, `.env`, `.env.*` (trừ `.env.example`), `studio.local.json`,
   và mọi họ file media/model. `video-studio doctor` kiểm bằng `git check-ignore` chứ không bằng
   cách đọc file — một dòng `!` ở dưới có thể mở lại cả thư mục đã chặn phía trên, và chỉ git
   mới biết luật nào thắng.
2. **Hook `pre-commit`** (`init` cài, không bao giờ đè hook sẵn có): chặn file dưới `workspace/`,
   `.env`, `studio.local.json`, file media, và dòng thêm mới trông giống token. Bỏ qua có chủ ý:
   `git commit --no-verify`.

Gỡ một trong hai lớp đó là tự tháo rào cho dữ liệu của chính mình.

## Lệnh liên quan

```
video-studio init [--station DIR] [--mode embedded|separate] [--migrate] [--dry-run] [--undo]
video-studio backup --out <file>.zip          # zip cả trạm, trừ scratch/cache/venv/cây git
video-studio migrate --to separate [--station DIR]   # chuyển workspace/ ra ngoài repo
video-studio update                           # git pull --ff-only trên bản clone, không bao giờ xoá gì
video-studio doctor --json                    # trong đó có kiểm hai nguồn sự thật + hai lớp rào
```

`migrate --to separate` kiểm **mọi** điều kiện trước khi dời byte nào (đích phải trống, repo phải
đang ở chế độ embedded); cùng ổ đĩa thì dời bằng `rename` (hỏng thì hỏng sạch), khác ổ thì chép →
đối chiếu sha256 từng file → mới xoá nguồn.
