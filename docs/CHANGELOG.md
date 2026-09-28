# Nhật ký thay đổi

Mỗi bản phát hành một mục, mới nhất ở trên. Mục **Chưa phát hành** gom những gì đã vào nhánh
chính nhưng chưa có tag; khi phát hành, mục đó đổi tên thành số phiên bản, và số đó phải khớp
`pyproject.toml`, `video_studio/__init__.py` cùng ba manifest plugin (`tests/test_version_sync.py`
kiểm).

## Chưa phát hành

Đích: `0.2.0` — chuẩn hóa để chạy như nhau trên Windows và macOS, cài được bằng một lời nhờ agent.

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
- **`video-studio uninstall`** — chỉ gỡ thứ bộ cài đã đặt (skill đã chép nếu chưa sửa, liên kết
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
