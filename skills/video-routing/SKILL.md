---
name: video-routing
description: Use when an agent must choose a video product approach, clarify a brief, or set up, check or drive a HyperFrames video station through the video-studio CLI. Covers training, explainers, data news and character stories across engines and styles, or adapt a reference or viral video into an original one (routes to video-reference-analysis then video-remix-brief); not for writing a composition's HTML/CSS/animation or cutting footage by hand.
---

# Định tuyến việc dựng video qua `video-studio`

Skill này là **cửa vào**: nó nói việc nào đi lệnh nào, thứ tự an toàn, và chỗ phải dừng hỏi
người dùng. Mọi lệnh tuân **một hợp đồng**: mã thoát `0` ok · `1` lỗi render (chạy lại được) ·
`2` gọi/cấu hình sai (sửa rồi mới chạy) · `3` thiếu trạm/công cụ (cài tiếp); có `--json` thì
dòng cuối stdout là một dòng JSON, log người đọc ở stderr.

## Chọn hướng sản phẩm

Với mọi yêu cầu tạo video, điều phối theo [workflow chung](references/video-workflow.md):
chọn nhánh theo đầu ra, dùng video mẫu nếu có, rồi nối brief → treatment → storyboard → dựng →
kiểm. Nếu chỉ yêu cầu phân tích hoặc thiết kế thì dừng đúng đầu ra được giao. Với lyric video có
mẫu, dùng phân tích mẫu trước rồi chuyển sang `music-to-video`; cue lời luôn lấy từ bản thu mới.
Nếu người dùng muốn tạo template tái sử dụng từ mẫu, dùng nhánh riêng của workflow chung; template
được thiết kế chưa đồng nghĩa có mã chạy hay quyền dùng lại media mẫu.

Khi chỉ nghiên cứu hoặc mở rộng concept, phong cách hay kỹ thuật video, vẫn tra thư viện theo
[workflow chung](references/video-workflow.md) ở bước brief → treatment. Đây là nghiên cứu video;
ý tưởng chiến dịch hay lịch đăng thuộc marketing. Nếu chỉ được giao tra cứu, không ghi catalog
hay tải asset. Trong công việc dựng video có quyền ghi trạm, nguồn mới hữu ích để tái dùng được
lập thẻ liên kết theo `video-theme-library` và kiểm tìm lại qua chỉ mục chung; link không cấp
quyền sao chép nội dung.

Khi cần tìm hiệu ứng hoặc đóng gói pattern dùng lại, chuyển sang `video-theme-library`: phân biệt
thẻ tham chiếu, mã có sẵn và mức kiểm; trong phạm vi đã giao, chủ động lưu dữ liệu đã tách khỏi
project và có quyền vào trạm được chọn. Thao tác tìm không tự ghi và không tự phát hành vào repo.

Khi yêu cầu bắt đầu từ mục tiêu người xem, hãy đọc
[`references/product-profiles.md`](references/product-profiles.md) trước khi chọn cách dựng.
Chọn **một nhóm chính** theo điều người xem cần hiểu hoặc làm; video lai có thể có rubric phụ.
Engine, phong cách, nền tảng, khung hình và thời lượng không tự quyết nhóm. Reference cũng nêu
intake gọn và các điểm quyết định cần hỏi.

Khi brief có lỗi chất lượng cụ thể hoặc cần bàn giao output, đọc đúng thẻ trong
[`references/production-techniques.md`](references/production-techniques.md). Đây là checklist
để chọn bước phù hợp; skill hiện có vẫn sở hữu việc thực thi. Với footage quay thật đọc
skill `video-edit`; với cleanup vùng trong video đọc
skill `video-cleanup`. Không mở mọi thẻ nếu brief không gọi tới.

Khi yêu cầu cần xử lý media bằng FFmpeg, tra danh mục `ffmpeg-tool-index.md` trong skill
`video-edit` để chọn luồng đã có; không suy rằng mọi hiệu ứng đề xuất đã được triển khai.

## Bước 1 — chọn đúng tiền kiểm

- Các lệnh cần HyperFrames hoặc trạm: chạy `video-studio doctor --json` trước. Mã `3` ⇒ đọc
  `errors` + `hint`, hướng dẫn người dùng cài phần thiếu (Node ≥ 22, ffmpeg, trạm). Đừng tự cài
  thay khi chưa được giao.
- `cleanup` là luồng FFmpeg độc lập; không cần doctor, Node, HyperFrames hay trạm. Nó tự báo mã
  `3` nếu thiếu ffmpeg/ffprobe.
- `--offline` khi không được phép gọi mạng (không chạy `npx`/`npm`).
- `--check-updates` chỉ **báo** bản HyperFrames mới; nâng bản là việc có chủ đích (render hồi quy
  trước, đổi `HYPERFRAMES_VERSION` sau). Không bao giờ dùng `latest`.

## Bước 2 — trạm: `video-studio init`

Trước khi chọn trạm, cài, di trú hoặc tra lệnh, đọc [trạm và bảng lệnh](references/station-and-commands.md).
Trên máy có `OPCOS_WORKSPACES`, `--mode embedded --yes` chọn trạm trong repo.

## Bước 3 — chọn đúng việc

- **Lyric video từ một bản nhạc**: workflow sở hữu là `hyperframes/music-to-video`;
  khi cần chữ theo nhạc đọc thêm skill `lyric-video-effects`.
  Khi cần ảnh tĩnh có sao, đom đóm hoặc tia nắng, đọc thêm
  skill `photo-ambient-effects`. Hai skill bổ trợ không thay workflow chính.
- **Dựng video từ DỮ LIỆU** (bản tin, deep-dive, repo hôm nay): `render` + một spec
  `schema_version: 1`. `brand` bắt buộc; thiếu là mã 2. Khuôn spec: `docs/CONTRACT.md`.
- **Đã có video câm, cần giọng**: `narrate`. Ghim `--profile`, đừng dùng `--instruct` cho bản
  giao (mỗi câu một giọng khác).
- **Có footage quay thật**: `edit` → đọc skill `video-edit` trước khi cắt; quy trình là hỏi →
  chốt → dựng, không phải một nút bấm.
- **Cần xử lý một vùng hoặc logo nhìn thấy trong video đã có**: đọc skill `video-cleanup`; chọn
  ROI, thời gian và method rõ ràng, xem preview, rồi apply ra file mới và verify manifest.
- **"Làm video giống video này" (link hoặc tệp mẫu)**: đọc `video-reference-analysis` → `video-remix-brief` → `render`/`edit`; quy trình ở `docs/reference-to-remix.md`. Chỉ tải khi người dùng nói đúng URL; ý tưởng, hook, lịch đăng thì sang `agent-marketing-team`; nhân bản người trong mẫu thì từ chối.
- **Sắp chế một layout mới**: đọc skill `video-theme-library` + `docs/THEME-LIBRARY.md` TRƯỚC —
  chọn từ thư viện rồi mới sáng tác.
- **Người dùng hỏi "đồ của tôi nằm đâu / xoá được không"**: `docs/WORKSPACE.md`.
- **Deck HTML bài giảng/trình chiếu cần QA bố cục**: ngoài phạm vi video — plugin `agent-design-studio`, skill `design-routing`, mode `static-artifact`.

## Biến môi trường

`VIDEO_STATION` (gốc trạm; tên cũ `VIDEO_ROOT`) · `HYPERFRAMES_VERSION` (bản cụ thể x.y.z) ·
`HYPERFRAMES_WORKDIR` · `NODE_DIR` · `FFMPEG_DIR` · `VIDEO_FONT` · `CHROME_BIN` ·
`VOICE_STATION` (trạm giọng cho lồng tiếng).
