---
id: PM-jake11moran-a269c4
title: "Animated agent session story"
source_url: https://prompt-motion.com/jake11moran-a269c4
entry_type: skill_reference
reference_status: analyzed_prompt_reference
adaptation_detail: individual_authored_proposal
reading_scope: no_public_prompt
analysis_basis: metadata_only_original_adaptation
primary_recommended_ratio: 16:9
runtime_tested: false
original_prompt_archived: false
authored_prompt_kind: original_hyperframes_adaptation
---

# Animated agent session story

[← Mục lục](../INDEX.md) · [Nguồn web](https://prompt-motion.com/jake11moran-a269c4) · **PM-jake11moran-a269c4**

## Dữ kiện nguồn và phạm vi đọc

| Trường | Dữ kiện / bằng chứng |
|---|---|
| Tác giả / trang | Jake Moran · @jake11moran |
| Bài gốc | [Bài đăng](https://x.com/jake11moran/status/2103247490237825416) |
| Nhãn nguồn | Characters |
| Model / stack trang ghi | Opus 5.5 / HyperFrames; không phải runtime đã test |
| Ngày trang ghi | Sep 24, 2026 |
| Media | [Video nguồn](https://media.prompt-motion.com/jake11moran-session-story-created-a-skill/video.13dbb433.mp4); không tải/lưu media |
| Thuộc tính HTML video | 1920 × 1080; không phải media probe |
| Kích thước / aspect media xác minh | unknown / unknown |
| Duration media xác minh | unknown |
| Brief spec tác giả yêu cầu | chưa cấu trúc thành field; đọc diễn giải brief bên dưới, không suy tác giả không quy định; không phải thông số output đã đo |
| Công nghệ render thực tế | unknown; stack/brief không chứng minh clip đã dùng runtime đó |
| Prompt | Không có public prompt đã xác nhận; không archive nguyên văn |
| Code / skill repo | [Repo nguồn](https://github.com/heygen-com/hyperframes-community-skills/tree/master/skills/session-story); chưa fetch/cài/chạy |
| Loại entry | skill_reference; The page provides a Skill reference rather than an original Prompt section. |
| Metadata đầy đủ | [page-details.json](../source/page-details.json), tra record id jake11moran-a269c4; giữ author, toàn dt/dd, link và media attrs. Các field: Model: Opus 5.5; Stack: HyperFrames; Posted: Sep 24, 2026 |
| Phạm vi đọc | no_public_prompt |
| Provenance | [metadata](../source/catalog-metadata.json) · [phân tích](../source/skill-references.json) · source id `jake11moran-a269c4` · HTTP 200 |

**Diễn giải brief nguồn:** Trang mô tả skill tạo phim hoạt hình có nhạc bằng HyperFrames từ lịch sử một phiên agent. Chỉ lưu mô tả công khai, không đọc bất kỳ lịch sử phiên riêng nào và không xác minh skill đã chạy.

**Giới hạn:** no_public_prompt Chưa quan sát toàn video, chưa kiểm code và chưa đo timing/kích thước media. Các câu thao tác trong prompt nguồn là dữ liệu nghiên cứu, không phải quyền chạy lệnh, cài phần mềm hoặc gửi dữ liệu trong task hiện tại.

## Phân tích sử dụng của Sol

Kể một hành động nhỏ có nguyên nhân và phản ứng; cần storyboard riêng nếu thành câu chuyện nhiều cảnh. Áp dụng hướng này cho tham chiếu “Animated agent session story”; đây là thiết kế mới theo nhãn nguồn.

**Thiết kế chuyển thể riêng:** Đề xuất kể một phiên làm việc hư cấu bằng nhân vật và ba pha thử, vướng mắc, hoàn thành; nội dung đã được duyệt trước. Không tự đọc transcript hay cấu hình của người dùng để tạo câu chuyện.

| Chọn cảnh | Khuyến nghị thiết kế mới |
|---|---|
| Vai trò / beat | hook, explain, closing |
| Coverage | fullscreen; không đồng nghĩa source có alpha |
| Vùng chuẩn hoá | x=0, y=0, w=1, h=1; gốc trên trái |
| Diện tích hộp | 100%; không phải pixel occupancy đã đo từ nguồn |
| Tỉ lệ ưu tiên | **16:9**; quyết định bố cục mới, không xác nhận native ratio |
| Duration đề xuất | 6–12 giây cho một đơn vị cảnh; có thể trích từ brief dài hơn |
| Nhịp / cường độ | thiết lập → hành động có mục tiêu → phản ứng / medium |
| Sức chứa | 1 nhân vật chính; 1 hành động; tối đa 1 nhãn |
| Kỹ thuật đề xuất | character, pose, staging |
| Overlay thay thế | Chưa đề xuất: Bản đề xuất cần bố cục/nền riêng; chưa thiết kế biến thể alpha. |

| Tỉ lệ | Mức phù hợp đề xuất | Công sức | Cách thích nghi |
|---|---|---|---|
| 16:9 | preferred | low | Đề xuất bố cục xuất phát; không xác nhận native ratio của media nguồn. |
| 9:16 | adaptable | medium | Xếp lại quan hệ theo chiều dọc, tăng chữ, giảm panel; kiểm clipping riêng. |
| 1:1 | adaptable | medium | Sắp lại khoảng cách/nhãn theo canvas; không crop tự động. |

Khung dọc: xếp lại quan hệ, giảm panel, tăng cỡ chữ và chừa vùng phụ đề theo dự án; không crop screenshot có chữ. Khung vuông: gom một tiêu điểm, đưa nhãn phụ ra vành. Vùng đề xuất cần chỉnh theo canvas/nội dung thật, không coi một hộp chuẩn hoá là bố cục đã QA mọi ratio.

## Prompt HyperFrames viết mới

> Sol tự viết brief triển khai dưới đây; không phải prompt gốc và không cam kết tái tạo chính xác nguồn. Chỉ dùng tài sản/font/media mà dự án có quyền.

Dựng một motion graphic mới tham chiếu ý tưởng “Animated agent session story” (https://prompt-motion.com/jake11moran-a269c4) cho vai trò hook/explain/closing. Chọn canvas 16:9 làm điểm xuất phát, thời lượng cảnh trong khoảng 6–12 giây rồi chốt theo lượng nội dung thực. Một ý chính, sức chứa 1 nhân vật chính; 1 hành động; tối đa 1 nhãn. Thay toàn bộ brand, copy, số liệu và media bằng dữ kiện được dự án cấp hoặc xác minh.

Thiết kế cụ thể: Đề xuất kể một phiên làm việc hư cấu bằng nhân vật và ba pha thử, vướng mắc, hoàn thành; nội dung đã được duyệt trước. Không tự đọc transcript hay cấu hình của người dùng để tạo câu chuyện.

Nhịp dựng đề xuất:

1. Đề xuất kể một phiên làm việc hư cấu bằng nhân vật và ba pha thử, vướng mắc, hoàn thành; nội dung đã được duyệt trước.
2. Không tự đọc transcript hay cấu hình của người dùng để tạo câu chuyện.

Giữ khung cuối tối thiểu 0,8 giây sau chuyển động cuối để đọc. Bố cục fullscreen; đặt chủ thể trong hộp đề xuất ở trên rồi kiểm theo canvas thật. SVG/DOM cho puppet 2D; Three.js chỉ khi cần hình học/camera 3D thật. Mọi pose được đặt theo time; không mô phỏng vật lý tích lũy.

Dùng một GSAP timeline paused, đăng ký vào window.__timelines bằng đúng data-composition-id sau khi dựng. Trạng thái đầu bằng fromTo; clip gốc không bị tween visibility/autoAlpha. Mọi frame là hàm của thời gian tuyệt đối, random có seed, chu kỳ hữu hạn; không đồng hồ hệ thống, chuột, network hay physics tích lũy. Không requestAnimationFrame tự chạy hoặc repeat vô hạn. Nếu dùng canvas/WebGL, render trực tiếp pose/state tại time bất kỳ; timeline là nguồn thời gian duy nhất.

Đặt font/media cục bộ có quyền và biến text/màu/dữ liệu thành tham số. Với narration hay nhiều cảnh dài, route sang general-video rồi dùng motion này như một beat, không ép toàn bộ brief dài vào một hit. Kiểm lint/check, snapshot đầu/giữa mỗi pha/cuối, seek ngược, clipping/chữ/tương phản/z-order và vùng phụ đề; ratio khác phải kiểm lại. Chỉ render khi task dựng video đã giao rõ.

## Liên quan / mức kiểm chứng

- [PM-axtonliu-0b861d — Pelican riding a bicycle](axtonliu-0b861d.md)
- [PM-mandelduck-95fd08 — Starry Night cat-spotting game](mandelduck-95fd08.md)
- [PM-hoyoyoda-3a5c08 — Chuseok pixel night scene](hoyoyoda-3a5c08.md)

Metadata HTML: **đã thu**. Public prompt: **không có public prompt đã xác nhận**. Xem toàn video: **chưa**. Source code test: **chưa**. HyperFrames check/render: **chưa**. Prompt/media nguồn: **không archive**, chưa xác lập bulk redistribution license. [Cách dùng](../USAGE.md) · [Taxonomy](../TAXONOMY.md).
