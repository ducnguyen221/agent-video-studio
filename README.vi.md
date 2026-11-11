# agent-video-studio

Reference tái dùng: [chữ lyrics A/B/C, chống cắt nét script và icon nét vẽ](skills/lyric-video-effects/SKILL.md),
và [lớp phủ cho ảnh tĩnh, có tia nắng từ góc](skills/photo-ambient-effects/SKILL.md).
Hai bộ bổ trợ workflow nhạc; không kèm font hay media riêng. Phạm vi đã kiểm và giới hạn nằm trong
từng skill. Bổ sung mã nguồn cục bộ chưa đồng nghĩa đã cài bản plugin mới.

*[English](README.md)* · [Trang giới thiệu](https://ducnguyen.vn/agent-video-studio/)

Engine dựng video cho agent: composition HTML/CSS/GSAP được
[HyperFrames](https://github.com/heygen-com/hyperframes) render ra MP4, bọc trong một package
Python cài được với một lệnh duy nhất, `video-studio`.

> **Trạng thái: v0.8.2.** Bản này có bố cục trạm, lệnh kiểm máy, công cụ di trú,
> họ template bản tin, lồng tiếng, xem trước, chỉnh footage, và `export` / `import` để mang dữ
> liệu trạm sang máy khác, cùng tính năng cleanup video local. Mọi lệnh trong bảng dưới đều đã có mã thật.

**Đây là một năng lực thêm, không phải một mảnh của bộ nào phải cài đủ.** Repo này đứng một
mình: cài khi bạn cần dựng video, và chỉ khi đó. Một quy trình sản xuất nội dung (ví dụ
`agent-marketing-team`) *gọi được* nó qua hợp đồng mã thoát + dòng JSON cuối stdout nếu nó có
mặt — nhưng quy trình đó chạy bình thường khi bạn chưa cài, và nói rõ là đang thiếu năng lực
video thay vì nổ giữa chừng. Trạm **giọng** (`agent-voice-studio`) cũng vậy: thiếu nó thì render
câm vẫn chạy, chỉ là không lồng tiếng được. Không có thứ tự cài bắt buộc, không có "bộ ba".

## Bản này có gì

Thư viện hiệu ứng local có thể tra cứu reference và, trên Windows, lưu hoặc đưa lại một file vào
project qua `python -m video_studio.effect_library` với trạm được chọn tường minh. Trên Windows,
`materialize-repo --id <VE-id> --project <project-đích> --name <tên-file-mới>` lấy một
component hoặc preset một file từ repo có quyền khai báo `owned`/`licensed`, kiểm hash và không
ghi đè file có sẵn; lệnh không tự chuyển sang trạm. Mã 3 nghĩa là file có thể đã được công bố
nhưng bước kết thúc hoặc báo kết quả thất bại: kiểm đích trước khi thử lại. Xem
[hướng dẫn nguồn hiệu ứng](skills/video-theme-library/references/effect-sources.md) để biết
manifest, quyền và mã thoát. Bundle nhiều file đã lưu và đọc được, nhưng chưa đưa lại được thành
thư mục project.

CLI tìm kiếm trả danh sách JSON gồm các envelope: đọc thẻ qua `row["entry"]` (ví dụ
`row["entry"]["id"]`); `truncated_fields` và `omitted_fields` báo phần bị rút hoặc ẩn,
`retrieve` hướng dẫn lấy đầy đủ. Đây là thay đổi so với JSON CLI cũ đặt thẻ trực tiếp
trong row. `--full-prompt` trả nguyên `prompt_text` nhưng vẫn tóm tắt trường khác;
`--full-record` trả đầy đủ mọi trường. Khi lấy một mục, tìm theo ID với `--limit 1` và
kiểm ID trả về vì tìm kiếm dựa trên từ khóa. Bản tóm tắt giới hạn 8.192 byte mỗi envelope
theo phép tính JSON escape bảo thủ. ID dài hơn 240 ký tự làm tìm tóm tắt trả mã 2; dùng
`--full-record`. Hai cờ lấy đủ có thể tạo output lớn. API Python `search()` vẫn trả record gốc.
Trên Windows, CLI còn tìm từng tên tham khảo FFmpeg và kỹ thuật lấy ý tưởng từ Hypit ngay từ tài
liệu gốc; không suy các công cụ đó đã cài. Hệ khác cảnh báo hai nguồn này bị bỏ khỏi kết quả cho
đến khi đường đọc an toàn được kiểm chứng.

| Lệnh | Làm gì |
|---|---|
| `video-studio doctor` | Kiểm Node ≥ 22, npx, bản HyperFrames đang ghim, Chromium headless của nó, ffmpeg/ffprobe, font Inter, trạm và `station.json`. `--check-updates` chỉ *báo* bản HyperFrames mới. |
| `video-studio init` | Dựng trạm (`embedded` trong repo, hoặc `separate` ngoài repo), ghi `station.json`. `--migrate` nhận một trạm bố cục cũ (và gỡ bản skill bản cũ đã chép vào đó), `--dry-run` in kế hoạch không ghi gì, `--undo` đảo lần chạy gần nhất theo nhật ký. |
| `video-studio render` | spec JSON (`schema_version: 1`) → MP4 theo template: `news`, `news-weekly`, `topstory`, `repo-today`, hoặc `effect-preview`. Template tin cần phần phụ `[voice]`; `effect-preview` hiện cần Windows và file `dist/gsap.min.js` của GSAP 3.15.0 có SHA-256 đã ghim qua `--gsap-file`, dựng lớp hiệu ứng tổng hợp 16:9 không âm thanh. Preview đặt npm ở chế độ offline; đây không phải sandbox mạng cho engine. |
| `video-studio probe` | Render thử một trang 320×180 dài 0,5 s, không tài nguyên ngoài (vài giây trên máy khoẻ). Môi trường render kẹt (quá giờ hoặc `Navigation timeout`) ⇒ mã 1, lỗi mở đầu `RENDER_STUCK:` — khởi động lại máy. `--heal` chụp gói chẩn đoán, giết Chrome/HyperFrames mồ côi, xoá profile tạm cũ rồi thử lại (60 s, rồi 600 s) trước khi chịu thua. Pipeline chạy lệnh này trước các bước tốn kém. |
| `video-studio narrate` | video câm (hoặc cả một project, render trước) + lời dẫn → một MP4 hoàn chỉnh có giọng và nhạc nền tuỳ chọn, qua trạm giọng. |
| `video-studio preview` | Mở studio xem trước của HyperFrames cho một project — bằng **đúng bản đã ghim**, nên thứ bạn soi chính là thứ sẽ render. |
| `video-studio edit` | Cắt footage quay thật: bóc lời tại máy, gom cụm thành markdown đọc được, rồi dựng theo EDL kèm chỉnh màu, overlay, phụ đề và chuẩn âm lượng. Cache kiểm tra snapshot tạm của bytes nguồn và cài đặt ASR; mỗi lượt đều chép source vào ổ tạm, kể cả cache hit, nên vẫn tốn I/O. Nếu source lớn hơn một nửa dung lượng trống của ổ tạm, lệnh dừng với lỗi rõ ràng. Model/đường dẫn weights tùy biến được xem là chưa rõ và không dùng cache; batch có tên transcript bị trùng sẽ bị từ chối trước khi đổi output. Transcript cũ chưa có metadata cache sẽ được bóc lại. Helper chưng cất từ `video-use` (MIT); cũng gọi được bản upstream đã cài ở trạm. |
| `video-studio cleanup` | Đọc metadata video local, xem trước và áp dụng chỉnh sửa ROI theo thời gian (`delogo`, blur, che màu đặc hoặc crop cả khung); sau đó kiểm hash, timing, audio và geometry qua manifest. Dùng FFmpeg độc lập, không cần HyperFrames hay trạm. |
| `video-studio reference` | video mẫu → khung có PTS thật, lưới khung, transcript từ phụ đề gốc hoặc bóc lời tại máy, hồ sơ quyền `provenance.json`, kiểm tài sản; tải có cổng (mặc định chỉ in kế hoạch). |
| `video-studio export` / `import` | Đóng gói trạm thành zip và bung vào máy khác. `--personal` chỉ lấy tài sản của project (`projects/*/assets`) cộng đúng những thư mục bạn kể tên bằng `--include`; nháp, cache, venv và cây git không bao giờ vào gói. `import` mặc định **không đè**, có `--dry-run` và `--overwrite`. |
| `video-studio backup` / `migrate` / `update` | Zip cả trạm; chuyển trạm `embedded` ra ngoài repo; cập nhật bản clone (không bao giờ xoá gì). |
| `video-studio uninstall` | Chỉ gỡ thứ bộ cài đã đặt — liên kết repo → trạm, skill bản cũ đã chép (nếu chưa sửa), `.env` chưa điền, hook pre-commit của chính nó — và dời chúng vào nhật ký của trạm thay vì xoá. Trạm và mọi project giữ nguyên. `--dry-run` in kế hoạch. |

Mọi lệnh theo một hợp đồng: mã `0` ok · `1` lỗi render/engine (chạy lại được) · `2` gọi hoặc
cấu hình sai · `3` thiếu trạm/công cụ; có `--json` thì dòng cuối stdout là một object JSON, log
người đọc ra stderr. Hợp đồng đầy đủ cho bên gọi: [docs/CONTRACT.md](docs/CONTRACT.md).

**Engine không có thương hiệu mặc định.** Spec phải khai `brand.a`, `brand.b`, `brand.site`;
thiếu là mã 2. Một mặc định im lặng ở chỗ này nghĩa là video của bạn mang tên người khác.

## Cài

**Nhờ agent cài giúp.** Dán nguyên văn yêu cầu dưới đây vào Claude Code, Codex hoặc Antigravity trên Windows hay macOS; agent làm theo [INSTALL.md](INSTALL.md) (hướng dẫn dành cho agent), hỏi bạn trước khi cài thêm gì, và báo lại từng dòng `doctor`:

```text
Hãy cài Agent Video Studio lên máy này (Windows hoặc macOS) cho chính ứng dụng AI bạn đang chạy.
Nguồn duy nhất: https://github.com/ducnguyen221/agent-video-studio
Đọc trước hướng dẫn dành cho agent tại
https://raw.githubusercontent.com/ducnguyen221/agent-video-studio/main/INSTALL.md
(không mở được link thì clone repo rồi đọc INSTALL.md trong đó) và làm đúng, đủ các bước:
kiểm máy, hỏi tôi trước khi cài phần mềm hoặc cần quyền admin, clone vào thư mục an toàn
(không OneDrive/iCloud/Desktop), cài vào .venv của repo, dựng trạm, chạy doctor, thử bài mẫu.
Quy tắc: chỉ chạy lệnh có trong repo hoặc INSTALL.md; không đổi chính sách hệ thống; không đọc
hay ghi mật khẩu/khóa; gặp lỗi thì dừng và giải thích bằng lời thường.
Kết thúc bằng bản tóm tắt: đường dẫn repo, trạm, từng dòng doctor, phần mềm đã cài thêm, việc tôi
cần làm tiếp.
```

Hoặc tự cài ([START-HERE.md](START-HERE.md) có lệnh đúng cho Windows và macOS):

```bash
git clone https://github.com/ducnguyen221/agent-video-studio
cd agent-video-studio
python3.12 -m venv .venv && . .venv/bin/activate   # Windows: py -3 -m venv .venv; .venv\Scripts\activate
pip install -e ".[test]"
video-studio init            # trình bảng hai lựa chọn rồi chờ bạn chọn; --station DIR = separate
video-studio doctor          # sau init: chưa có trạm thì doctor mã 3, đúng thiết kế
```

Khi cần người chọn, `init` **trình bảng lựa chọn**, chứ không hỏi trống: `embedded` (trạm ở `<repo>/workspaces/`,
biến cấu hình ở `<repo>/.env`) là **khuyến nghị** — khi máy chưa đặt `OPCOS_WORKSPACES`, bấm Enter là
xong, không phải đặt biến môi trường nào, và `init` chép sẵn `.env.example` thành `.env` cho bạn điền.
Chọn `separate` khi bạn dùng nhiều máy, rành kỹ thuật, hoặc repo này là bản public của chính bạn.
Không có ai trả lời (CI, lịch chạy) và máy chưa đặt `OPCOS_WORKSPACES` thì `init` in bảng đó ra rồi
**thoát mã 2 mà chưa ghi byte nào** — agent cài phải đưa bảng cho người dùng xem, không tự chọn im
lặng. Máy đã đặt `OPCOS_WORKSPACES` thì chỗ đặt đã biết: `--yes` hay chạy không người dựng trạm
`<biến>/video`.

HyperFrames không phải phụ thuộc Python: nó chạy qua `npx hyperframes@$HYPERFRAMES_VERSION`,
luôn là một bản cụ thể (không bao giờ `latest`).

Hướng dẫn từng bước cho người dùng: [GUIDE.vi.md](GUIDE.vi.md).

## Tài liệu

- [Trang giới thiệu](https://ducnguyen.vn/agent-video-studio/) — nó làm gì, cài thế nào, quy tắc.
- [START-HERE.md](START-HERE.md) — bước đầu trên Windows hoặc macOS, và bài mẫu nên dựng trước.
- [docs/INSTALL.md](docs/INSTALL.md) — Node, ffmpeg, font, và **cài vào venv nào**.
- [docs/WORKSPACE.md](docs/WORKSPACE.md) — trạm, hai chế độ cài, thứ gì xoá được.
- [docs/AGENT_VIDEO_GUIDE.md](docs/AGENT_VIDEO_GUIDE.md) — agent lái trọn quy trình thế nào.
- [docs/CONTRACT.md](docs/CONTRACT.md) — khuôn spec và hợp đồng gọi.
- [docs/THEME-LIBRARY.md](docs/THEME-LIBRARY.md) — thư viện layout + luật cứng khi render.
- [docs/CHANGELOG.md](docs/CHANGELOG.md) — mỗi bản phát hành đổi gì.

## Skill cho agent

`skills/` có **27 skill**: sáu skill của chính repo này (`video-routing`, `video-edit`,
`video-cleanup`, `video-theme-library`, `video-reference-analysis`,
`video-remix-brief`) và **21 skill chưng cất từ bộ skill hiện hành của HyperFrames**
(`skills/hyperframes/`). Bộ 21 này là bản **đã dịch sang tiếng Việt, rút gọn và biên tập lại** từ
`skills/<tên>/SKILL.md` của upstream tại một tag cụ thể — frontmatter giữ tiếng Anh vì đó là thứ
harness đọc để định tuyến. Không file nhị phân nào của upstream (font, nhạc, ảnh) được chép vào
đây, và thư mục `references/` của upstream cũng không. Bản nguồn đã ghim của từng skill nằm ở
[`upstream.json`](upstream.json); `video-studio doctor` đối chiếu sổ đó với cây trên đĩa.

Skill **không** được chép vào trạm. Gốc repo có một adapter nhỏ cho mỗi skill ở `.claude/skills/`
(Claude Code) và `.agents/skills/` (Codex, Antigravity): adapter chỉ mang `name` + `description`
của skill và trỏ agent về bản gốc trong `skills/`. Mở thư mục repo trong host là thấy đủ 27 skill;
`git pull` là có nội dung skill mới. Thêm, xoá hay đổi mô tả skill thì chạy
`python scripts/build_host_adapters.py`; `tests/test_host_adapters.py` đỏ khi adapter lệch nguồn.
Trạm dựng bằng bản cũ còn bản chép cùng `skills-lock.json`: `init --station DIR --migrate` **gỡ**
chúng — bản cũ được lưu vào nhật ký của lần init nên `init --undo` trả lại được.

## Quy tắc

Đây không phải lời khuyên. Chúng là lý do repo này dựng theo cách hiện tại, và là điều kiện để
dùng nó mà không gây rắc rối cho ai.

1. **Ghi công đúng nguồn, đúng giấy phép.** Bộ skill chưng cất từ HyperFrames mang giấy phép
   **Apache-2.0** kèm nghĩa vụ ghi chú "đã sửa" (§4(b)); bộ helper của `edit` chưng cất từ
   `video-use` mang giấy phép **MIT**; một skill của upstream còn kéo theo ghi công **MIT** cho
   `vtake-skills`. Cả ba ghi đầy đủ trong `NOTICE` kèm tag nguồn. **Gỡ ghi công là vi phạm giấy
   phép**, không phải một lựa chọn biên tập.
2. **Không phát hành lại tài sản của người khác.** Không font, không nhạc, không ảnh, không
   video của upstream được chép vào repo này — giấy phép từng file đó chưa kiểm được. Cái gì cần
   thì **gọi lúc chạy** và do người dùng tự cài.
3. **Thương hiệu phải khai, không có mặc định.** Spec thiếu `brand.a` / `brand.b` / `brand.site`
   là **mã thoát 2**. Một mặc định im lặng ở chỗ này nghĩa là video của bạn mang tên người khác,
   và bạn chỉ phát hiện ra sau khi đã đăng.
4. **Ghim bản, và chỉ báo chứ không tự nâng.** Engine luôn gọi qua
   `npx hyperframes@$HYPERFRAMES_VERSION`, không bao giờ `latest`. `doctor --check-updates` chỉ
   **báo** có bản mới; nâng hay không là quyết định của bạn, vì nâng engine là đổi thứ sẽ ra file.

Bộ test có cổng chặn tên khách hàng, tên thương hiệu riêng, tên profile giọng, đường dẫn máy và
biến môi trường trỏ thư mục người dùng — quét cả tài liệu lẫn trang giới thiệu, **miễn trừ theo số
đếm** chứ không miễn cả file.

## Tác giả

**Nguyễn Quang Đức** (Tobi) — nhà sáng lập, CEO KPIM và đồng sáng lập COMPA Class; chuyên gia Data/AI và giảng viên công nghệ tại Việt Nam.

Website: https://ducnguyen.vn · GitHub: [@ducnguyen221](https://github.com/ducnguyen221) · Liên hệ: ducnguyen.ams@gmail.com

## Giấy phép

MIT cho mã của repo này (xem `LICENSE`). Thành phần bên thứ ba được gọi lúc chạy giữ giấy phép
của chính chúng — xem `NOTICE`.

## Ghi công

Snapshot nguồn và trạng thái áp dụng nằm trong [`upstream.json`](upstream.json). Các nguồn ý
tưởng FlowKit/Hypit có [quy trình cập nhật](docs/UPSTREAM-UPDATES.md): so baseline đã ghim với
candidate, map về skill hiện có, review và kiểm trước khi nhận thay đổi. Đây là bảo trì thủ
công; `doctor --check-updates` không theo dõi hai repo này.

- [HyperFrames](https://github.com/heygen-com/hyperframes) (Apache-2.0) — engine render.
- [video-use](https://github.com/browser-use/video-use) (MIT) — phương pháp cắt footage mà bộ
  helper của `edit` chưng cất từ đó.
