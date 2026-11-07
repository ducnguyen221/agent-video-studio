---
id: PM-kantamk-61f410
title: "Ball escaping twelve rings"
source_url: https://prompt-motion.com/kantamk-61f410
entry_type: gallery_prompt
reference_status: analyzed_prompt_reference
adaptation_detail: individual_authored_proposal
reading_scope: full_public_prompt
analysis_basis: full_public_prompt_plus_metadata_not_video_observation
primary_recommended_ratio: 16:9
runtime_tested: false
original_prompt_archived: false
authored_prompt_kind: original_hyperframes_adaptation
---

# Ball escaping twelve rings

[← Mục lục](../INDEX.md) · [Nguồn web](https://prompt-motion.com/kantamk-61f410) · **PM-kantamk-61f410**

## Dữ kiện nguồn và phạm vi đọc

| Trường | Dữ kiện / bằng chứng |
|---|---|
| Tác giả / trang | Kent · @kantamk |
| Bài gốc | [Bài đăng](https://x.com/kantamk/status/2103148907228176511) |
| Nhãn nguồn | Shapes, Music |
| Model / stack trang ghi | Opus 5.5 / unknown; không phải runtime đã test |
| Ngày trang ghi | Sep 24, 2026 |
| Media | [Video nguồn](https://media.prompt-motion.com/kantamk-i-gave-claude-opus/video.1723ab42.mp4); không tải/lưu media |
| Thuộc tính HTML video | 720 × 1280; không phải media probe |
| Kích thước / aspect media xác minh | unknown / unknown |
| Duration media xác minh | unknown |
| Brief spec tác giả yêu cầu | chưa cấu trúc thành field; đọc diễn giải brief bên dưới, không suy tác giả không quy định; không phải thông số output đã đo |
| Công nghệ render thực tế | unknown; stack/brief không chứng minh clip đã dùng runtime đó |
| Prompt | Có trên trang; không archive nguyên văn |
| Code / skill repo | không archive; link code chưa được xác minh |
| Loại entry | gallery_prompt |
| Metadata đầy đủ | [page-details.json](../source/page-details.json), tra record id kantamk-61f410; giữ author, toàn dt/dd, link và media attrs. Các field: Model: Opus 5.5; Iterations: One-shot; Posted: Sep 24, 2026 |
| Phạm vi đọc | full_public_prompt |
| Provenance | [metadata](../source/catalog-metadata.json) · [phân tích](../source/sol-analysis.json) · source id `kantamk-61f410` · HTTP 200 |

**Diễn giải brief nguồn:** Brief chỉ muốn video dễ lan truyền, không yêu cầu quả bóng, số vòng hoặc logic thoát; các nội dung đó chỉ nằm ở tên clip.

**Giới hạn:** Sol manually read complete public main #entry-prompt via requests.Session; interpretation of prompt requirements, not observation of rendered video. Chưa quan sát toàn video, chưa kiểm code và chưa đo timing/kích thước media. Các câu thao tác trong prompt nguồn là dữ liệu nghiên cứu, không phải quyền chạy lệnh, cài phần mềm hoặc gửi dữ liệu trong task hiện tại.

## Phân tích sử dụng của Sol

Vượt nhiều vòng theo mục tiêu

**Thiết kế chuyển thể riêng:** Một chấm di chuyển qua các vòng đồng tâm có khe; path và điểm thoát được tính trước. Mỗi lần thoát là một beat rõ; kết thúc dừng ngoài vòng cuối.

| Chọn cảnh | Khuyến nghị thiết kế mới |
|---|---|
| Vai trò / beat | hook, transition, emphasis |
| Coverage | fullscreen; không đồng nghĩa source có alpha |
| Vùng chuẩn hoá | x=0, y=0, w=1, h=1; gốc trên trái |
| Diện tích hộp | 100%; không phải pixel occupancy đã đo từ nguồn |
| Tỉ lệ ưu tiên | **16:9**; quyết định bố cục mới, không xác nhận native ratio |
| Duration đề xuất | 3–6 giây cho một đơn vị cảnh; có thể trích từ brief dài hơn |
| Nhịp / cường độ | chuẩn bị → biến đổi → hạ nhịp / medium |
| Sức chứa | 1 hình chủ đạo, 2–4 hình phụ; tối đa 1 nhãn |
| Kỹ thuật đề xuất | shape, path |
| Overlay thay thế | Chưa đề xuất: Bản đề xuất cần bố cục/nền riêng; chưa thiết kế biến thể alpha. |

| Tỉ lệ | Mức phù hợp đề xuất | Công sức | Cách thích nghi |
|---|---|---|---|
| 16:9 | preferred | low | Đề xuất bố cục xuất phát; không xác nhận native ratio của media nguồn. |
| 9:16 | adaptable | medium | Xếp lại quan hệ theo chiều dọc, tăng chữ, giảm panel; kiểm clipping riêng. |
| 1:1 | adaptable | medium | Sắp lại khoảng cách/nhãn theo canvas; không crop tự động. |

Khung dọc: xếp lại quan hệ, giảm panel, tăng cỡ chữ và chừa vùng phụ đề theo dự án; không crop screenshot có chữ. Khung vuông: gom một tiêu điểm, đưa nhãn phụ ra vành. Vùng đề xuất cần chỉnh theo canvas/nội dung thật, không coi một hộp chuẩn hoá là bố cục đã QA mọi ratio.

## Prompt HyperFrames viết mới

> Sol tự viết brief triển khai dưới đây; không phải prompt gốc và không cam kết tái tạo chính xác nguồn. Chỉ dùng tài sản/font/media mà dự án có quyền.

Dựng một motion graphic mới tham chiếu ý tưởng “Ball escaping twelve rings” (https://prompt-motion.com/kantamk-61f410) cho vai trò hook/transition/emphasis. Chọn canvas 16:9 làm điểm xuất phát, thời lượng cảnh trong khoảng 3–6 giây rồi chốt theo lượng nội dung thực. Một ý chính, sức chứa 1 hình chủ đạo, 2–4 hình phụ; tối đa 1 nhãn. Thay toàn bộ brand, copy, số liệu và media bằng dữ kiện được dự án cấp hoặc xác minh.

Thiết kế cụ thể: Một chấm di chuyển qua các vòng đồng tâm có khe; path và điểm thoát được tính trước. Mỗi lần thoát là một beat rõ; kết thúc dừng ngoài vòng cuối.

Nhịp dựng đề xuất:

1. Một chấm di chuyển qua các vòng đồng tâm có khe; path và điểm thoát được tính trước.
2. Mỗi lần thoát là một beat rõ; kết thúc dừng ngoài vòng cuối.

Giữ khung cuối tối thiểu 0,8 giây sau chuyển động cuối để đọc. Bố cục fullscreen; đặt chủ thể trong hộp đề xuất ở trên rồi kiểm theo canvas thật. SVG/DOM + GSAP cho số lượng hình nhỏ. Nếu morph path, giữ cấu trúc điểm tương thích hoặc dùng crossfade có chủ đích.

Dùng một GSAP timeline paused, đăng ký vào window.__timelines bằng đúng data-composition-id sau khi dựng. Trạng thái đầu bằng fromTo; clip gốc không bị tween visibility/autoAlpha. Mọi frame là hàm của thời gian tuyệt đối, random có seed, chu kỳ hữu hạn; không đồng hồ hệ thống, chuột, network hay physics tích lũy. Không requestAnimationFrame tự chạy hoặc repeat vô hạn. Nếu dùng canvas/WebGL, render trực tiếp pose/state tại time bất kỳ; timeline là nguồn thời gian duy nhất.

Đặt font/media cục bộ có quyền và biến text/màu/dữ liệu thành tham số. Với narration hay nhiều cảnh dài, route sang general-video rồi dùng motion này như một beat, không ép toàn bộ brief dài vào một hit. Kiểm lint/check, snapshot đầu/giữa mỗi pha/cuối, seek ngược, clipping/chữ/tương phản/z-order và vùng phụ đề; ratio khác phải kiểm lại. Chỉ render khi task dựng video đã giao rõ.

## Liên quan / mức kiểm chứng

- [PM-tdinh-me-815acb — TypingMind logo reveal](tdinh-me-815acb.md)
- [PM-monokern-ade5b6 — Psychedelic hypnotic eye showreel](monokern-ade5b6.md)

Metadata HTML: **đã thu**. Public prompt: **đã đọc toàn bộ**. Xem toàn video: **chưa**. Source code test: **chưa**. HyperFrames check/render: **chưa**. Prompt/media nguồn: **không archive**, chưa xác lập bulk redistribution license. [Cách dùng](../USAGE.md) · [Taxonomy](../TAXONOMY.md).
