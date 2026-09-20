---
title: Workspace
summary: What the video station holds, the two install modes (embedded vs separate), which folders are safe to delete, and what goes into a backup.
audience: anyone who has to answer "where does my stuff live?"
---

# Trạm video — từng thư mục là gì

Repo `agent-video-studio` chỉ chứa **mã**. Mọi thứ của riêng bạn — project đang dựng, footage,
spec, nháp, cache — nằm ở **trạm video**.

Repo này là một **năng lực thêm**, đứng một mình: cài khi bạn cần dựng video. Quy trình sản xuất
nội dung nào gọi nó thì gọi qua hợp đồng mã thoát + dòng JSON cuối stdout, và chạy bình thường
khi máy chưa cài nó. Trạm **giọng** cũng là một năng lực riêng: thiếu nó thì render câm vẫn
chạy. Không có "bộ" nào phải cài đủ.

## Hai chế độ đặt trạm

| Chế độ | Trạm | Biến cấu hình | Dành cho |
|---|---|---|---|
| **`embedded`** — gọn trong repo (**mặc định, khuyến nghị cho người mới**) | `<repo>/workspace/` | `<repo>/.env` | một máy, "mở một folder là thấy hết" |
| **`separate`** — trạm ngoài repo | `~/.video` (hoặc nơi bạn chọn) | cấp user; bí mật ở `~/.secret/video-studio/` | nhiều máy, repo public của chính bạn, nhiều repo dùng chung một trạm |

`video-studio init` hỏi bạn chọn (Enter = `embedded`) và ghi lựa chọn vào
`<repo>/studio.local.json`. **Không hỏi** trong ba trường hợp:

- `--station DIR` — bạn chỉ thẳng trạm ⇒ `separate`.
- Máy **đã có trạm ngoài**: biến `VIDEO_STATION` (hoặc tên cũ `VIDEO_ROOT`) đã đặt, hoặc
  `~/.video` đã có `station.json`, `projects/`, hay seed `demo/` đời cũ ⇒ tự `separate`, và
  **không bao giờ** tạo `workspace/`. Hai trạm cho một repo là hai nguồn sự thật, và cái sai chỉ
  lộ ra khi bạn "mất" một project.
- `--mode embedded|separate`, hoặc `--yes` (= nhận khuyến nghị `embedded`).

Chạy không có người trả lời (agent, script, lịch) mà chưa chọn ⇒ `init` in bảng lựa chọn rồi
thoát **mã 2**, chưa ghi byte nào. **Agent cài phải trình bảng đó cho người dùng và chờ họ
chọn** — không tự chọn im lặng. Tự khai `--non-interactive` cũng vậy: nó nói "không có ai ngồi
đây", KHÔNG nói "đoán hộ tôi", nên thiếu `--yes`/`--mode`/`--station` thì vẫn là mã 2.

Agent cài nên **phân tích rồi khuyến nghị**, không hỏi trống: người không rành kỹ thuật, một
máy ⇒ `embedded`; người nhiều máy, rành hơn, hoặc repo này là bản public của chính họ ⇒
`separate`.

Xem trước, không ghi gì: `video-studio init --dry-run`.

### Biến cấu hình ở chế độ `embedded` — `<repo>/.env`

`init` chép `.env.example` (khuôn tên biến, không có giá trị) thành `<repo>/.env` và khoá quyền
600 trên POSIX. Chạy lại **không đè** file bạn đã điền — và ngược lại, chạy lại là đường **sửa**
khi `.env` hay `studio.local.json` bị xoá nhầm, kể cả lúc trạm đã đúng chuẩn và kế hoạch rỗng.

Thứ tự đọc một biến: **biến môi trường thật → `<repo>/.env` (chỉ khi `mode = embedded`) → chưa
đặt**. Biến thật luôn thắng file: máy đã đặt biến (máy chạy lịch) không được để một file lạc vào
repo cướp cấu hình. Chế độ `separate` **không bao giờ** nạp `.env` — ở đó repo có thể là bản
public của chính bạn, và tự nạp một file nằm trong repo là mở cửa cho nó; vì thế
`migrate --to separate` **mang `.env` theo** sang `~/.secret/video-studio/` thay vì bỏ nó lại
thành một file còn đó mà không ai đọc.

Hai nhóm biến **không** tới được qua `.env`, và được đánh dấu `[MÔI TRƯỜNG THẬT]` ngay trong
khuôn:

- `VIDEO_STATION`, `VIDEO_ROOT`, `VIDEO_STUDIO_REPO` — chúng trỏ chính repo và trạm này, tức
  quay ngược lại cái đã quyết định có đọc `.env` hay không. `.env` chỉ được nạp khi chế độ là
  `embedded`, nghĩa là trạm đã chốt ở `<repo>/workspace/`; để một dòng trong đó trỏ trạm đi nơi
  khác là tự tạo ra đúng cái "hai nguồn sự thật" mà cả bộ cài sinh ra để chặn.
- Biến mã đọc thẳng từ `os.environ` (`VIDEO_WHISPER_MODEL`, `VIDEO_BROLL_QUERY`,
  `TOPSTORY_ACCENTS`, `REPO_TODAY_INPUT`).

`VOICE_STATION` thì **đọc được** từ `.env`: nó trỏ sang trạm của một repo khác, và đó chính là
cách người dùng `embedded` nối hai năng lực lại mà không phải đặt biến môi trường nào.

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

Bộ test còn giữ một cổng thứ ba cho chính khuôn biến: **mọi biến mã đọc qua `_env.env("…")` phải
có trong `.env.example`**, và khuôn không được mang giá trị. Thiếu một dòng là người dùng không
biết mình phải điền gì, và chỉ phát hiện ra lúc lệnh nổ giữa chừng.

Gỡ một trong hai lớp đó là tự tháo rào cho dữ liệu của chính mình.

## Trạm KHÔNG BAO GIỜ được có remote

Đặt trạm dưới `git` để có lịch sử cục bộ là việc hợp lý và `video-studio` không cản (mã của
repo này chưa bao giờ chạy `git init` ở trạm — đó là thao tác tay của người dùng). Nhưng nếu
trạm đã là một repo git thì **nó phải mãi mãi không có remote**.

Lý do: trạm là nơi chứa **công việc thật** — project của khách hàng, bản dựng chưa duyệt, nhật
ký di trú, tài sản media. Gắn remote một lần là toàn bộ LỊCH SỬ đi theo, kể cả những thứ đã
xoá khỏi bản làm việc từ lâu. Đây không phải rủi ro giả định: không có gì trong máy chặn
`git remote add`, và không có cổng nào báo sau khi ai đó đã đẩy.

```
git -C <trạm> remote -v        # phải RỖNG, mọi lúc
```

Cần chia sẻ nội dung trạm thì dùng `video-studio export` / `backup` — chúng đóng gói **bản làm
việc hiện tại**, không mang lịch sử theo.

## Lệnh liên quan

```
video-studio init [--station DIR] [--mode embedded|separate] [--yes] [--non-interactive]
                  [--migrate] [--dry-run] [--undo]
video-studio backup --out <file>.zip          # zip cả trạm, trừ scratch/cache/venv/cây git
video-studio migrate --to separate [--station DIR]   # chuyển workspace/ ra ngoài repo
video-studio update                           # git pull --ff-only trên bản clone, không bao giờ xoá gì
video-studio doctor --json                    # trong đó có kiểm hai nguồn sự thật + hai lớp rào
```

`migrate --to separate` kiểm **mọi** điều kiện trước khi dời byte nào (đích phải trống, repo phải
đang ở chế độ embedded, `~/.secret/video-studio/.env` chưa có sẵn một bản khác); cùng ổ đĩa thì
dời bằng `rename` (hỏng thì hỏng sạch), khác ổ thì chép → đối chiếu sha256 từng file → mới xoá
nguồn. `<repo>/.env` đi theo sang kho secret, không bị bỏ lại.
