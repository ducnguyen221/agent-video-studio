# Dùng Agent Video Studio với Codex

Muốn agent cài giúp: dán prompt trong [INSTALL.md](../../INSTALL.md#prompt-copy-dán) vào Codex (CLI
hoặc ứng dụng desktop — hai bản dùng chung một cấu hình). Tự cài: [START-HERE.md](../../START-HERE.md).

Codex đọc thẳng [`AGENTS.md`](../../AGENTS.md) ở gốc repo. Mở **thư mục repo** làm project; Codex
desktop sẽ hỏi tin cậy (trust) thư mục — bấm đồng ý để agent chạy được lệnh trong đó.

**Sandbox:** sandbox của Codex có thể chặn `winget`/`brew`, chặn mạng (lúc `pip install`, lúc
HyperFrames tải Chromium) hoặc chặn ghi ra ngoài thư mục project (trạm ngoài repo). Khi bị chặn,
**không** đổi thiết lập sandbox để lách: đưa đúng lệnh cho người dùng tự chạy trong terminal
thường rồi dán kết quả lại. Trạm mặc định `workspace/` nằm trong repo nên không cần ghi ra ngoài.

**Skill:** cách chắc chắn là bảo Codex "đọc `skills/video-routing/SKILL.md` rồi làm theo". Bản chép
trong `<trạm>/.agents/skills` chỉ được tự nạp khi thư mục làm việc là trạm
([vì sao](../README.md#host-thấy-skill-bằng-cách-nào)). Manifest `.codex-plugin/` có trong repo nhưng
chưa kiểm trên Codex thật.

**Kiểm sau khi cài:** `video-studio doctor`, chép nguyên các dòng; bài mẫu
[`samples/news-mini`](../../samples/news-mini/EXPECTED.md) nếu máy đủ công cụ render.

Bộ cài không sửa `~/.codex/config.toml`. Gỡ: `video-studio uninstall` (giữ trạm).
