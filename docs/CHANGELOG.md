# Nhật ký thay đổi

Mỗi bản phát hành một mục, mới nhất ở trên. Mục **Chưa phát hành** gom những gì đã vào nhánh
chính nhưng chưa có tag; khi phát hành, mục đó đổi tên thành số phiên bản, và số đó phải khớp
`pyproject.toml`, `video_studio/__init__.py` cùng ba manifest plugin (`tests/test_version_sync.py`
kiểm).

## 0.2.4 — 2026-10-01

ffmpeg phải **đủ bộ lọc chữ**, không chỉ có lệnh. Trên Mac mini (01/10/2026), `brew install
ffmpeg` theo INSTALL cũ cho bản Homebrew core đã bỏ libfreetype + libass ⇒ không có `drawtext`,
`subtitles`, `ass`; `doctor` vẫn PASS, `edit` đốt phụ đề hỏng, và runner truyện của
marketing-studio (dùng chung ffmpeg) chết ở bước dựng video sau 7 giờ đọc. Render bản tin
(HyperFrames) không đổi.

- **INSTALL**: macOS cài `ffmpeg-full` thay `ffmpeg` (INSTALL.md bảng công cụ + lệnh `brew`,
  docs/INSTALL.md, GUIDE, START-HERE); giải thích keg-only. Bảng ghi rõ "bản có libfreetype +
  libass".
- **Dò ffmpeg**: `FFMPEG_DIR` → (macOS) keg `/opt/homebrew/opt/ffmpeg-full/bin` → `PATH`. Keg thắng
  bản core trên `PATH`, không cần symlink hay sửa `PATH`.
- **`doctor`**: dòng mới `ffmpeg-filters` đọc `ffmpeg -hide_banner -filters`, đòi `drawtext`,
  `subtitles`, `ass`. Thiếu là **WARN** (render bản tin không cần) kèm lệnh cài; mã thoát không
  đổi.
- **`edit`**: cần đốt phụ đề mà ffmpeg không có `subtitles` ⇒ **mã 3 ngay**, trước khi cắt/ghép
  đoạn nào (`edit/render.py: require_filters`); `--no-subtitles` vẫn chạy.
- **CI job `ffmpeg`** (Windows + macOS): cài đúng bản INSTALL dạy (keg KHÔNG thêm vào `PATH`), rồi
  kiểm bộ lọc + đốt phụ đề thật; `VIDEO_STUDIO_REQUIRE_FFMPEG=1` biến skip thành đỏ.
- **Nâng cấp máy Mac đang chạy**: `brew install ffmpeg-full`; gỡ symlink tạm
  `~/.local/bin/ffmpeg`/`ffprobe` nếu đã tạo; `video-studio doctor` phải có
  `[PASS] ffmpeg-filters`.

## 0.2.3 — 2026-09-30

Bản dọn theo báo cáo review repo 30/09, chỉ các mục rủi ro không/thấp. **Hành vi render, init và
trạm không đổi** trên Windows lẫn Mac; mã thoát của mọi lệnh giữ nguyên.

- **Tài liệu `init`:** `GUIDE.md`/`GUIDE.vi.md` và skill `video-routing` còn nói `init` tự nhận
  trạm có sẵn — sai từ 0.2.2. Viết lại đúng mã: trạm đã chọn (`VIDEO_STATION`,
  `studio.local.json` ghi `separate`) dùng luôn; `~/.video` chỉ tình cờ có mặt thì `init` hỏi,
  `--yes`/không người là mã 2, nhận bằng `--mode separate`/`--station`/`--migrate`. Cổng
  `tests/test_docs_drift.py` thêm danh sách câu đã sai, cấm quay lại. `START-HERE.md` thêm hai
  dòng dưới `init --yes`: báo "máy đã có trạm video ở …" thì dùng `init --mode separate`.
- **Telemetry HyperFrames:** bước tắt telemetry dời lên **trước** `doctor` (`INSTALL.md` mục 7,
  trước là 7b) vì `doctor` gọi `npx hyperframes doctor`; các mục sau đánh lại số (doctor 8, bài
  mẫu 9, báo cáo 10, gỡ vướng 11). `doctor` thêm một dòng `[NOT_CHECKED] telemetry` in đúng lệnh
  `npx --yes hyperframes@<bản ghim> telemetry disable` — không gọi thêm lệnh nào, không đổi mã thoát.
- **Lời khuyên khi thiếu phụ thuộc render** (mã 3, không đổi): bỏ `pip install -e ".[voice]"` (hỏng
  khi chưa có bản clone repo giọng); nay trỏ `INSTALL.md` mục 5b, `pip install -e "<repo giọng>[engine]"`,
  và in đường thật khi thấy bản clone repo giọng cạnh repo này (như `doctor`).
- **CI:** `actions/checkout` v5.1.0 và `actions/setup-python` v6.3.0 (chạy Node 24), vẫn ghim SHA.
- **`.gitignore`:** thêm `.coverage`, `htmlcov/`, `.mypy_cache/`, `.ruff_cache/`,
  `templates/_seed/package-lock.json`.

## 0.2.2 — 2026-09-30

Bản vá sau lượt kiểm trên Mac mini (báo cáo MAC-REVIEW-FOR-WINDOWS). Máy Windows đã đặt
`VIDEO_STATION` không đổi hành vi.

- **`init` không còn tự nhận `~/.video` có sẵn** (sự cố lượt Mac 29/09). `~/.video` chỉ tình cờ
  mang dấu trạm thì `init` hỏi người dùng; với `--yes` hay khi không có người trả lời, nó in đường
  trạm cũ rồi thoát mã 2 và không ghi gì. Nhận trạm đó phải bằng `--mode separate`,
  `--station <thư mục>` hoặc `--migrate`. `--yes` giữ đúng nghĩa: embedded, `<repo>/workspace/`.
  Trạm đã chọn (biến `VIDEO_STATION`/`VIDEO_ROOT`, hoặc `studio.local.json` ghi `separate`) vẫn
  dùng luôn không hỏi; `studio.local.json` ghi `separate` nay thắng một `~/.video` tình cờ có mặt.
- **Khối `engine` của JSON kết quả (P2-17):** `engine.voice_studio` nay là bản **hợp đồng** của
  repo giọng (`API_VERSION`) ở cả `render` lẫn `narrate`, đúng nghĩa repo giọng tự trả; bản phát
  hành của gói giọng đi khoá mới `engine.voice_studio_version`. Trước đây `render` trả bản phát hành
  dưới cùng khoá. Bảng nghĩa từng khoá ở `docs/CONTRACT.md` §2.
- **`scripts/install-video-use.{ps1,sh}`** không còn đoán trạm là `$HOME/.video`: trạm do package
  phân giải (biến → `studio.local.json` → `<repo>/workspace/`), và lệnh gợi ý cuối cùng khớp chế độ
  cài. Cổng `tests/test_ps1_portable.py` thêm luật chặn mọi script đoán trạm ở home.
- **`doctor`:** chưa cài repo giọng mà bản clone của nó nằm cạnh repo này (cùng thư mục cha, tên gì
  cũng được, nhận bằng nội dung) thì dòng `voice-studio` in sẵn lệnh `pip install -e "<đường>[engine]"`.
- **Tài liệu:** clone vào `<thư mục cha>` người dùng chọn thay cho đường cứng; repo giọng là anh em
  cùng thư mục cha (`INSTALL.md` mục 4, 5b); bước tắt telemetry của HyperFrames
  `npx --yes hyperframes@<bản ghim> telemetry disable` (mục 7b, P2-18); mọi chỗ nói `browser ensure`
  ghi rõ dạng `npx --yes hyperframes@<bản ghim> browser ensure` — đó là lệnh của HyperFrames, CLI
  repo này không có lệnh con `browser` (P2-2); `package.json` của project không quyết bản render,
  `station.json` mới quyết (P3-2); bảng nền tảng ghi macOS arm64 đã render thật bài mẫu (dòng macOS
  của `samples/news-mini/EXPECTED.md`, PR #3).

## 0.2.1 — 2026-09-29

Bản vá tài liệu để một agent trên Mac Apple Silicon mới tinh tự cài được theo `INSTALL.md`, không
biến môi trường nào (chế độ embedded).

- **macOS trong `INSTALL.md`, `START-HERE.md`, `docs/INSTALL.md`:** tạo venv bằng `python3.12`
  (`python3` của Mac mới là 3.9, dưới mức tối thiểu); điều kiện trước cho Mac mới — Xcode Command
  Line Tools, Homebrew do người dùng tự cài (agent không chạy lệnh tải-rồi-chạy), `/opt/homebrew/bin`
  trên `PATH`, `brew install python@3.12 node ffmpeg git`; kiểm biến và `PATH` bằng
  `zsh -lic 'echo $…'` vì shell của agent không nạp `~/.zshrc`. Lần render đầu cần mạng (HyperFrames,
  Chromium, CDN), và bản HyperFrames đang ghim (0.8.54) chưa render gì trên arm64.
- **Một đường cài lồng tiếng duy nhất** (mục 5b mới của `INSTALL.md`): clone `agent-voice-studio`
  cạnh repo này, `pip install -e "../agent-voice-studio[engine]"` vào chính `.venv` của repo video,
  `voice-studio init --yes`, rồi tạo giọng mặc định bằng `make-profile --instruct … --set-default`.
  Bỏ câu "cài vào venv của trạm giọng" ở `docs/INSTALL.md` và trang web, vốn mâu thuẫn với
  `INSTALL.md`. Thiếu bước giọng mặc định thì bài mẫu dừng vì chưa có profile — trước đây tài liệu
  không nói.
- **Bài mẫu `news-mini`:** dòng Windows trong `EXPECTED.md` có số đo thật (HyperFrames 0.8.54,
  113 s, 51,05 s / 24,93 s), đo bằng một bản cài mới theo đúng mục 5b.
- **`INSTALL.md` mục 6:** máy đã có trạm `~/.video` thì `init --yes` tự nhận trạm đó — agent phải
  đọc dòng `station` của `doctor` và hỏi trước khi render thử vào trạm đang chạy lịch.

## 0.2.0 — 2026-09-29

Chuẩn hóa để chạy như nhau trên Windows và macOS, cài được bằng một lời nhờ agent.

- **Trạm mặc định nằm trong repo.** Không đặt biến nào thì trạm là `<repo>/workspace/` (Git bỏ
  qua cả thư mục), kể cả trước khi `video-studio init` tạo nó. Bỏ tầng đoán `~/.video`: máy dùng
  trạm ngoài chọn tường minh bằng `VIDEO_STATION` hoặc `init --station DIR`. Bản cài wheel không
  có repo thì mọi lệnh cần trạm dừng mã 3 và chỉ cách chọn trạm.
- **Trạm giọng không bị đoán.** `VOICE_STATION` → `OMNIVOICE_DIR` → trạm mà repo giọng cài cùng
  venv đã được chọn; không có gì thì là "chưa có trạm giọng".
- **Bài mẫu `samples/news-mini/`** — bản tin hai cảnh, giọng ghim hạt giống, kèm `EXPECTED.md`
  (lệnh chạy, tên file ra, bảng số đo theo máy) và test không cần mạng.
- **CI** chạy trên mọi nhánh, ma trận Windows + macOS × Python 3.10 / 3.12 / 3.13, action ghim
  theo SHA commit.
- **Skill không còn được chép vào trạm.** `init` thôi chép 24 skill vào `<trạm>/.claude/skills` +
  `.agents/skills` và thôi ghi `skills-lock.json`. Gốc repo có adapter `.claude/skills/` và
  `.agents/skills/` (sinh bằng `scripts/build_host_adapters.py`, `--check` báo lệch) trỏ về skill
  gốc trong `skills/` — một nguồn, `git pull` là có bản mới. Trạm cũ: `init --station DIR --migrate`
  gỡ bản đã chép cùng file khoá (dời vào nhật ký, `--undo` trả về), skill riêng của người dùng giữ.
- **`video-studio uninstall`** — chỉ gỡ thứ bộ cài đã đặt (skill bản cũ đã chép nếu chưa sửa, liên kết
  repo → trạm, `.env` chưa điền, hook pre-commit của chính nó), dời vào nhật ký của trạm thay vì
  xoá; trạm và mọi project giữ nguyên. `--dry-run` in kế hoạch.
- **`doctor` có mức `NOT_CHECKED`** cho thứ chưa kiểm được (chạy `--offline`, thiếu npx) và cho
  `render` — doctor không tự render, nên không để một bảng toàn PASS nói thay. Nhãn người đọc
  đổi thành `PASS` / `WARN` / `FAIL` / `NOT_CHECKED` / `SKIP`; JSON thêm danh sách `not_checked`.
- **Cài bằng một lời nhờ agent:** `INSTALL.md` ở gốc repo là hướng dẫn dành cho agent (Windows và
  macOS, hỏi trước khi cài phần mềm, không tải-rồi-chạy, báo nguyên văn từng dòng `doctor`) kèm
  prompt copy-dán tiếng Việt và tiếng Anh; README và START-HERE chép đúng prompt đó.
- `AGENTS.md` (hướng dẫn chung cho mọi agent) với `CLAUDE.md` / `GEMINI.md` là con trỏ, và
  `hosts/` cho Claude Code, Codex, Antigravity, Claude Desktop — nói rõ đường nạp skill nào đã
  chạy, đường nào chưa kiểm.
- Trang web `/install/`: chọn ứng dụng AI, dán prompt (chép nguyên văn từ `INSTALL.md`), đọc nhãn kiểm tra.
- `START-HERE.md` và nhật ký thay đổi này.

## 0.1.0 — 2026-09-22

Bản công khai đầu tiên.

- Lệnh `video-studio`: `init` (hai chế độ `embedded` / `separate`, `--migrate`, `--undo`,
  `--dry-run`), `doctor`, `render`, `edit`, `preview`, `narrate`, `export`, `import`, `backup`,
  `migrate`, `update`.
- Hợp đồng gọi từ chương trình khác: mã thoát 0 / 1 / 2 / 3 và một dòng JSON cuối stdout
  ([CONTRACT.md](CONTRACT.md)), phủ cả `doctor` và lỗi nạp lệnh.
- `render` theo template bản tin `news`, `news-weekly`, `topstory`, `repo-today` từ một spec JSON;
  thương hiệu bắt buộc khai trong spec (thiếu là mã 2).
- HyperFrames ghim bản `0.8.54`, render khai `-q standard` tường minh; `doctor --check-updates`
  chỉ báo, không tự nâng.
- 21 skill HyperFrames chưng cất (thân tiếng Việt, ghi nguồn và hash đối chiếu upstream) cùng 3
  skill riêng: `video-routing`, `video-edit`, `video-theme-library`.
- Cổng chống ghi thoát khỏi `--out` độc lập hệ điều hành, chịu được hai cây trên hai ổ đĩa khác
  nhau trên Windows.
- CI Windows + macOS, và một job riêng so hash skill với manifest upstream.
