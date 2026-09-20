# agent-video-studio

*[English](README.md)*

Engine dựng video cho agent: composition HTML/CSS/GSAP được
[HyperFrames](https://github.com/heygen-com/hyperframes) render ra MP4, bọc trong một package
Python cài được với một lệnh duy nhất, `video-studio`.

> **Trạng thái: bản thử (0.1.0.dev0).** Bản này có bố cục trạm, lệnh kiểm máy, công cụ di trú,
> họ template bản tin, lồng tiếng, xem trước, chỉnh footage, và `export` / `import` để mang dữ
> liệu trạm sang máy khác. Mọi lệnh trong bảng dưới đều đã có mã thật.

## Bản này có gì

| Lệnh | Làm gì |
|---|---|
| `video-studio doctor` | Kiểm Node ≥ 22, npx, bản HyperFrames đang ghim, Chromium headless của nó, ffmpeg/ffprobe, font Inter, trạm và `station.json`. `--check-updates` chỉ *báo* bản HyperFrames mới. |
| `video-studio init` | Dựng trạm (`embedded` trong repo, hoặc `separate` ngoài repo), ghi `station.json`, chép skill cho agent. `--migrate` nhận một trạm bố cục cũ, `--dry-run` in kế hoạch không ghi gì, `--undo` đảo lần chạy gần nhất theo nhật ký. |
| `video-studio render` | spec JSON (`schema_version: 1`) → MP4 theo template: `news`, `news-weekly`, `topstory`, `repo-today`. Cần phần phụ `[voice]`. |
| `video-studio narrate` | video câm (hoặc cả một project, render trước) + lời dẫn → một MP4 hoàn chỉnh có giọng và nhạc nền tuỳ chọn, qua trạm giọng. |
| `video-studio preview` | Mở studio xem trước của HyperFrames cho một project — bằng **đúng bản đã ghim**, nên thứ bạn soi chính là thứ sẽ render. |
| `video-studio edit` | Cắt footage quay thật: bóc lời tại máy, gom cụm thành markdown đọc được, rồi dựng theo EDL kèm chỉnh màu, overlay, phụ đề và chuẩn âm lượng. Helper chưng cất từ `video-use` (MIT); cũng gọi được bản upstream đã cài ở trạm. |
| `video-studio export` / `import` | Đóng gói trạm thành zip và bung vào máy khác. `--personal` chỉ lấy tài sản của project (`projects/*/assets`) cộng đúng những thư mục bạn kể tên bằng `--include`; nháp, cache, venv và cây git không bao giờ vào gói. `import` mặc định **không đè**, có `--dry-run` và `--overwrite`. |
| `video-studio backup` / `migrate` / `update` | Zip cả trạm; chuyển trạm `embedded` ra ngoài repo; cập nhật bản clone (không bao giờ xoá gì). |

Mọi lệnh theo một hợp đồng: mã `0` ok · `1` lỗi render/engine (chạy lại được) · `2` gọi hoặc
cấu hình sai · `3` thiếu trạm/công cụ; có `--json` thì dòng cuối stdout là một object JSON, log
người đọc ra stderr. Hợp đồng đầy đủ cho bên gọi: [docs/CONTRACT.md](docs/CONTRACT.md).

**Engine không có thương hiệu mặc định.** Spec phải khai `brand.a`, `brand.b`, `brand.site`;
thiếu là mã 2. Một mặc định im lặng ở chỗ này nghĩa là video của bạn mang tên người khác.

## Cài

```bash
git clone https://github.com/ducnguyen221/agent-video-studio
cd agent-video-studio
python -m venv .venv && . .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -e ".[test]"
video-studio doctor
video-studio init            # hỏi embedded hay separate; --station DIR = separate
```

HyperFrames không phải phụ thuộc Python: nó chạy qua `npx hyperframes@$HYPERFRAMES_VERSION`,
luôn là một bản cụ thể (không bao giờ `latest`).

Hướng dẫn từng bước cho người dùng: [GUIDE.vi.md](GUIDE.vi.md).

## Tài liệu

- [docs/INSTALL.md](docs/INSTALL.md) — Node, ffmpeg, font, và **cài vào venv nào**.
- [docs/WORKSPACE.md](docs/WORKSPACE.md) — trạm, hai chế độ cài, thứ gì xoá được.
- [docs/AGENT_VIDEO_GUIDE.md](docs/AGENT_VIDEO_GUIDE.md) — agent lái trọn quy trình thế nào.
- [docs/CONTRACT.md](docs/CONTRACT.md) — khuôn spec và hợp đồng gọi.
- [docs/THEME-LIBRARY.md](docs/THEME-LIBRARY.md) — thư viện layout + luật cứng khi render.

## Skill cho agent

`skills/` có **24 skill**: ba skill của chính repo này (`video-routing`, `video-edit`,
`video-theme-library`) và **21 skill chưng cất từ bộ skill hiện hành của HyperFrames**
(`skills/hyperframes/`). Bộ 21 này là bản **đã dịch sang tiếng Việt, rút gọn và biên tập lại** từ
`skills/<tên>/SKILL.md` của upstream tại một tag cụ thể — frontmatter giữ tiếng Anh vì đó là thứ
harness đọc để định tuyến. Không file nhị phân nào của upstream (font, nhạc, ảnh) được chép vào
đây, và thư mục `references/` của upstream cũng không. Bản nguồn đã ghim của từng skill nằm ở
[`upstream.json`](upstream.json); `video-studio doctor` đối chiếu sổ đó với cây trên đĩa.

`video-studio init` chép cả 24 skill vào `<trạm>/.claude/skills` và `<trạm>/.agents/skills`, và
ghi `skills-lock.json`. Trạm còn skill đời cũ do công cụ khác cài thì `init --migrate` **gỡ**
chúng đi — bản cũ được lưu vào nhật ký của lần init nên `init --undo` trả lại được.

## Giấy phép

MIT cho mã của repo này (xem `LICENSE`). Thành phần bên thứ ba được gọi lúc chạy giữ giấy phép
của chính chúng — xem `NOTICE`.

## Ghi công

- [HyperFrames](https://github.com/heygen-com/hyperframes) (Apache-2.0) — engine render.
- [video-use](https://github.com/browser-use/video-use) (MIT) — phương pháp cắt footage mà bộ
  helper của `edit` chưng cất từ đó.
