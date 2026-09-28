# Chọn ứng dụng AI để dùng Agent Video Studio

"Host" là ứng dụng chạy AI agent. Repo này **không có MCP server**: mọi việc đi qua lệnh
`video-studio` trong terminal, nên cách cài giống nhau cho mọi host có công cụ chạy lệnh. Cách dễ
nhất: dán prompt trong [INSTALL.md](../INSTALL.md#prompt-copy-dán) vào ứng dụng bạn đang dùng.

| Bạn dùng | Chạy được `video-studio` | Đọc hướng dẫn từ | Hướng dẫn |
|---|---|---|---|
| Claude Code (terminal, IDE, tab Code của ứng dụng Claude) | Có | `CLAUDE.md` → `AGENTS.md` | [Claude Code](claude/README.md) |
| Codex (CLI và desktop) | Có | `AGENTS.md` | [Codex](codex/README.md) |
| Google Antigravity | Có | `GEMINI.md` → `AGENTS.md` | [Antigravity](antigravity/README.md) |
| Claude Desktop, tab chat | **Không** | — | [Claude Desktop](claude-desktop/README.md) |

## Host thấy skill bằng cách nào

Nguồn duy nhất của 24 skill là [`skills/`](../skills/) trong repo; **không** có bản chép nào trong
trạm. Có ba đường, mức kiểm khác nhau — nói thẳng để bạn không tưởng một đường chưa ai thử là đã
chạy:

| Đường | Cách | Trạng thái |
|---|---|---|
| Adapter ở gốc repo | Mở **thư mục repo** trong host. `.claude/skills/<tên>/SKILL.md` (Claude Code) và `.agents/skills/<tên>/SKILL.md` (Codex, Antigravity) chỉ mang `name` + `description` và trỏ agent về skill gốc trong `skills/` | Cùng khuôn đang dùng ở repo dữ liệu anh em; lượt nạp trên từng host thật của repo này chưa được ghi lại |
| Đọc thẳng từ repo | Bảo agent: "đọc `skills/video-routing/SKILL.md` rồi làm theo" | Chạy với mọi host đọc được file — đường dự phòng khi host không tự thấy adapter |
| Manifest plugin | `.claude-plugin/` và `.codex-plugin/` ở gốc repo | **Chưa kiểm** trên host thật |

Adapter do `python scripts/build_host_adapters.py` sinh từ `skills/`; `--check` báo lệch và
`tests/test_host_adapters.py` đỏ khi quên sinh lại. Sau `git pull`, mở lại host để đọc nội dung
skill mới. Trạm dựng bằng bản trước 0.2.0 còn bản chép cũ: `video-studio init --station <trạm>
--migrate` gỡ chúng (có nhật ký, `--undo` trả về).

## Không có cấu hình host nào bị sửa

Bộ cài không ghi vào file cấu hình của host (`~/.claude.json`, `~/.codex/config.toml`,
`~/.gemini/…`). `video-studio uninstall` vì thế cũng không có gì để gỡ ở phía host; nó chỉ gỡ phần
bộ cài đã đặt vào trạm và repo, và giữ nguyên trạm.
