# Dùng Agent Video Studio với Google Antigravity

Muốn agent cài giúp: dán prompt trong [INSTALL.md](../../INSTALL.md#prompt-copy-dán) vào Antigravity.
Tự cài: [START-HERE.md](../../START-HERE.md).

Antigravity đọc [`GEMINI.md`](../../GEMINI.md), file này trỏ sang [`AGENTS.md`](../../AGENTS.md).
Mở **thư mục repo** làm workspace.

**Skill:** cách chắc chắn là bảo agent "đọc `skills/video-routing/SKILL.md` rồi làm theo". Khi mở
thư mục repo, adapter `.agents/skills/` ở gốc repo trỏ về từng skill gốc
([cách hoạt động](../README.md#host-thấy-skill-bằng-cách-nào)).

**Kiểm sau khi cài:** `video-studio doctor`, chép nguyên các dòng; bài mẫu
[`samples/news-mini`](../../samples/news-mini/EXPECTED.md) nếu máy đủ công cụ render.

Chưa có lượt cài nào trên Antigravity được ghi lại — nếu bạn là người đầu tiên, báo lại những dòng
`doctor` giúp repo cập nhật trang này. Bộ cài không sửa cấu hình của Antigravity. Gỡ:
`video-studio uninstall` (giữ trạm).
