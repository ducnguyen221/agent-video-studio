# Dùng Agent Video Studio với Claude Code

Muốn agent cài giúp: dán prompt trong [INSTALL.md](../../INSTALL.md#prompt-copy-dán) vào Claude Code
(terminal, IDE, hoặc tab Code của ứng dụng Claude). Tự cài: [START-HERE.md](../../START-HERE.md).
Cách cài giống nhau trên Windows và macOS — chỉ khác đường gọi `.venv`
(`.\.venv\Scripts\video-studio` hay `.venv/bin/video-studio`).

Claude Code đọc [`CLAUDE.md`](../../CLAUDE.md), file này trỏ sang [`AGENTS.md`](../../AGENTS.md) —
ranh giới mã/dữ liệu và luật dựng video nằm ở đó. Mở **thư mục repo** làm thư mục làm việc.

**Skill:** cách chắc chắn là bảo Claude "đọc `skills/video-routing/SKILL.md` rồi làm theo" — skill
định tuyến chỉ sang skill còn lại. Khi mở thư mục repo, Claude Code còn thấy adapter
`.claude/skills/` ở gốc repo, trỏ về từng skill gốc ([cách hoạt động](../README.md#host-thấy-skill-bằng-cách-nào)). Manifest
`.claude-plugin/` có trong repo nhưng chưa kiểm trên Claude Code thật.

**Kiểm sau khi cài:** nhờ Claude chạy `video-studio doctor` và chép nguyên các dòng. `render` luôn
`NOT_CHECKED` cho tới khi dựng bài mẫu [`samples/news-mini`](../../samples/news-mini/EXPECTED.md).

Bộ cài không sửa cấu hình của Claude Code. Gỡ: `video-studio uninstall` (giữ trạm).
