# AGENTS.md — Agent Video Studio

> File hướng dẫn CHUẨN cho mọi AI agent (Claude Code · Codex · Google Antigravity · bất kỳ công cụ
> nào đọc AGENTS.md). `CLAUDE.md` và `GEMINI.md` chỉ là con trỏ về file này — sửa Ở ĐÂY.

## 0. Ranh giới mã nguồn và dữ liệu

**Engine, template, skill và script chạy từ repo này. Dữ liệu riêng nằm ở trạm:** `workspace/`
ngay trong repo (mặc định; Git bỏ qua cả thư mục), hoặc thư mục ngoài repo được chọn tường minh
bằng biến `VIDEO_STATION` hay `video-studio init --station DIR`. Không có trạm nào được đoán.

`workspace/` là dữ liệu riêng dù nằm trong checkout: không commit, không đóng gói, không chia sẻ.
`.gitignore` không ngăn được `git add -f`; chế độ trạm trong repo còn có hook `pre-commit` chặn lần
nữa. Không đưa tên thương hiệu hay khách hàng thật, profile giọng thật, đường dẫn máy hoặc token
vào phần mã được Git theo dõi — `tests/test_no_identity_leak.py` bắt những thứ đó.

**Agent chỉ ghi vào phần mã được Git theo dõi khi sửa code / tài liệu / test của chính repo.**
Mọi thứ khác đi vào trạm: project đang dựng, spec và `brand.json` thật, footage, nháp, file render.

Skill: nguồn DUY NHẤT để sửa là `skills/` trong repo. `video-studio init` hiện chép một bản vào
`<trạm>/.claude/skills` và `<trạm>/.agents/skills` (khoá bằng `skills-lock.json`); bản chép đó
không phải chỗ để sửa — sửa ở repo rồi chạy lại `init`.

## 1. Repo này là gì

**Agent Video Studio** = engine dựng video quanh [HyperFrames](https://github.com/heygen-com/hyperframes)
(HTML/CSS/GSAP → MP4) đóng gói thành một package Python với một lệnh, `video-studio`, cộng 24 skill
cho agent. Bản tin 16:9 + short 9:16 từ một spec JSON, lồng tiếng qua repo giọng
`agent-voice-studio` (tuỳ chọn, cùng venv).

```
agent-video-studio/
├─ video_studio/          package: CLI, trạm, doctor, render, edit, narrate, uninstall
│  └─ templates/news/        họ template bản tin (news, news-weekly, topstory, repo-today)
├─ skills/                24 skill (21 chưng cất từ HyperFrames trong skills/hyperframes/)
├─ templates/             seed project HyperFrames + cây mẫu của một trạm mới
├─ samples/news-mini/     bài mẫu + kết quả kỳ vọng (EXPECTED.md)
├─ hosts/                 hướng dẫn riêng từng ứng dụng AI
├─ scripts/               vỏ tiện ích (.ps1 cho Windows, .sh cho macOS)
├─ tests/ · .github/      pytest, CI Windows + macOS
├─ docs/                  tài liệu + trang giới thiệu (GitHub Pages)
├─ .claude-plugin/ · .codex-plugin/   manifest plugin
└─ workspace/             trạm mặc định — Git bỏ qua toàn bộ
```

## 2. Cài đặt và việc đầu tiên

**Cài đặt do AI agent thực hiện:** làm đúng và đủ theo [`INSTALL.md`](INSTALL.md) — hỏi người dùng
trước khi cài phần mềm hoặc cần quyền admin, không đổi chính sách máy, không đọc bí mật. Người tự
cài: [`START-HERE.md`](START-HERE.md). Việc đầu tiên sau khi cài: `video-studio doctor`, rồi bài
mẫu `samples/news-mini/` nếu máy có đủ công cụ render.

## 3. Luật khi dựng video (luật CỨNG)

1. **Chọn skill trước khi làm:** đọc `skills/video-routing/SKILL.md` — nó chỉ việc nào dùng skill
   nào (template bản tin, chỉnh footage, bố cục HyperFrames).
2. **Thương hiệu bắt buộc khai trong spec** (`brand.a`, `brand.b`, `brand.site`). Engine không có
   thương hiệu mặc định; thiếu là mã 2. Đừng bịa brand — hỏi người dùng.
3. **HyperFrames luôn là bản cụ thể** (`x.y.z`), không bao giờ `latest`/`^`/`~`. Nâng bản là việc
   có chủ đích sau render hồi quy; `doctor --check-updates` chỉ báo.
4. **Render qua `video-studio render`**, không gọi `npx hyperframes` tự chế: lệnh đó ghim bản, thử
   lại, và in stderr của engine khi hỏng.
5. **Đọc mã thoát, không đọc chữ:** `0` ok · `1` render/engine hỏng (thử lại được) · `2` gọi hoặc
   cấu hình sai (sửa, đừng thử lại) · `3` thiếu trạm/công cụ (cài tiếp). Với `--json`, dòng cuối
   stdout là một object JSON. Chi tiết: [`docs/CONTRACT.md`](docs/CONTRACT.md).
6. **File ra chỉ nằm trong `--out`;** tên file trong spec là tên trần, không phải đường dẫn.
7. **`NOT_CHECKED` không phải PASS.** Doctor không tự render; chỉ một lần render thật chứng minh
   được cả chuỗi.

## 4. Quy ước khi sửa mã repo này

- Python ≥ 3.10, lõi chỉ dùng thư viện chuẩn. Chạy `python -m pytest -q` trước commit; test không
  cần Node, ffmpeg, mạng hay repo giọng, và tự cô lập `HOME` khỏi trạm thật.
- **Chạy được như nhau trên Windows và macOS:** đường dẫn qua `os.path`/`pathlib`, không đường
  tuyệt đối kiểu `C:\`, không `cmd /c`, không nối `.exe` cứng; tiến trình con luôn là argv list,
  không bao giờ chạy qua shell (`tests/test_repo_gates.py` chặn).
- Mọi đường dẫn trạm / engine đi qua `video_studio/_env.py`; không đọc biến môi trường rải rác.
- `.ps1` giữ UTF-8 **có BOM** + CRLF (PowerShell 5.1 đọc tiếng Việt); mọi file khác LF.
- `README.md` là bản tiếng Anh chuẩn; sửa nó thì sửa `README.vi.md` **trong cùng commit**. Skill:
  frontmatter tiếng Anh (thứ host đọc để định tuyến), thân tiếng Việt.
- Skill chưng cất từ upstream: đổi nội dung thì cập nhật hash trong `upstream.json`; job CI
  `upstream` so với manifest upstream thật.
- Đổi phiên bản: năm chỗ cùng lúc (`pyproject.toml`, `video_studio/__init__.py`, ba manifest
  plugin) và mục tương ứng trong `docs/CHANGELOG.md` — `tests/test_version_sync.py` kiểm.

## 5. File nào host nào đọc

| Host | File hướng dẫn | Skill | Ghi chú |
|---|---|---|---|
| Claude Code | `CLAUDE.md` → trỏ về đây | `<trạm>/.claude/skills/` (do `init` chép) hoặc đọc thẳng `skills/` | [hosts/claude](hosts/claude/README.md) |
| Codex CLI / desktop | `AGENTS.md` (file này) | `<trạm>/.agents/skills/` hoặc đọc thẳng `skills/` | [hosts/codex](hosts/codex/README.md) |
| Antigravity | `GEMINI.md` → trỏ về đây | `<trạm>/.agents/skills/` hoặc đọc thẳng `skills/` | [hosts/antigravity](hosts/antigravity/README.md) |
| Claude Desktop (tab chat) | — | — | Không chạy được lệnh; [hosts/claude-desktop](hosts/claude-desktop/README.md) |
