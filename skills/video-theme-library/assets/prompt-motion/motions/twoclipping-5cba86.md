---
id: PM-twoclipping-5cba86
title: "Shape morphing through UI states"
source_url: https://prompt-motion.com/twoclipping-5cba86
entry_type: gallery_prompt
reference_status: analyzed_prompt_reference
adaptation_detail: individual_authored_proposal
reading_scope: full_public_prompt
analysis_basis: full_public_prompt_plus_metadata_not_video_observation
primary_recommended_ratio: 1:1
runtime_tested: false
original_prompt_archived: false
authored_prompt_kind: original_hyperframes_adaptation
---

# Shape morphing through UI states

[← Mục lục](../INDEX.md) · [Nguồn web](https://prompt-motion.com/twoclipping-5cba86) · **PM-twoclipping-5cba86**

## Dữ kiện nguồn và phạm vi đọc

| Trường | Dữ kiện / bằng chứng |
|---|---|
| Tác giả / trang | zero · @twoclipping |
| Bài gốc | [Bài đăng](https://x.com/twoclipping/status/2103273003555402193) |
| Nhãn nguồn | Product UI, Charts, Music |
| Model / stack trang ghi | Opus 5.5 / HTML + Playwright; không phải runtime đã test |
| Ngày trang ghi | Sep 24, 2026 |
| Media | [Video nguồn](https://media.prompt-motion.com/twoclipping-opus-5-5-is-f-cking/video.eef090ae.mp4); không tải/lưu media |
| Thuộc tính HTML video | 1440 × 1440; không phải media probe |
| Kích thước / aspect media xác minh | unknown / unknown |
| Duration media xác minh | unknown |
| Brief spec tác giả yêu cầu | chưa cấu trúc thành field; đọc diễn giải brief bên dưới, không suy tác giả không quy định; không phải thông số output đã đo |
| Công nghệ render thực tế | unknown; stack/brief không chứng minh clip đã dùng runtime đó |
| Prompt | Có trên trang; không archive nguyên văn |
| Code / skill repo | không archive; link code chưa được xác minh |
| Loại entry | gallery_prompt |
| Metadata đầy đủ | [page-details.json](../source/page-details.json), tra record id twoclipping-5cba86; giữ author, toàn dt/dd, link và media attrs. Các field: Model: Opus 5.5; Stack: HTML + Playwright; Posted: Sep 24, 2026 |
| Phạm vi đọc | full_public_prompt |
| Provenance | [metadata](../source/catalog-metadata.json) · [phân tích](../source/terra-70-normalized.json) · source id `twoclipping-5cba86` · HTTP 200 |

**Diễn giải brief nguồn:** A single shape morphs through button, loader, player, slider, tabs, chart and command palette under cursor control, returning to its initial state; the brief uses beat-mapped seeking, springs and motion-blur subframes.

**Giới hạn:** manual full prompt reading; not observed video Chưa quan sát toàn video, chưa kiểm code và chưa đo timing/kích thước media. Các câu thao tác trong prompt nguồn là dữ liệu nghiên cứu, không phải quyền chạy lệnh, cài phần mềm hoặc gửi dữ liệu trong task hiện tại.

## Phân tích sử dụng của Sol

Một khối trung tâm thành điều khiển UI

**Thiết kế chuyển thể riêng:** Đề xuất dựng một wrapper liên tục, giữ anchor qua các trạng thái UI và đặt text ở track riêng. Con trỏ click/drag chỉ là keyframe xác định trước. Indicator có hai mép dùng curve khác nhau để stretch mà không đổi tâm đột ngột.

| Chọn cảnh | Khuyến nghị thiết kế mới |
|---|---|
| Vai trò / beat | explain, proof, cta |
| Coverage | partial; không đồng nghĩa source có alpha |
| Vùng chuẩn hoá | x=0.08, y=0.12, w=0.84, h=0.72; gốc trên trái |
| Diện tích hộp | 60%; không phải pixel occupancy đã đo từ nguồn |
| Tỉ lệ ưu tiên | **1:1**; quyết định bố cục mới, không xác nhận native ratio |
| Duration đề xuất | 6–12 giây cho một đơn vị cảnh; có thể trích từ brief dài hơn |
| Nhịp / cường độ | mở vấn đề → thao tác → kết quả → giữ nhãn / medium |
| Sức chứa | 1 tác vụ; 1–3 trạng thái UI; 1 tiêu đề ngắn |
| Kỹ thuật đề xuất | morph, ui |
| Overlay thay thế | Chưa đề xuất: Bản đề xuất cần bố cục/nền riêng; chưa thiết kế biến thể alpha. |

| Tỉ lệ | Mức phù hợp đề xuất | Công sức | Cách thích nghi |
|---|---|---|---|
| 16:9 | adaptable | medium | Sắp lại khoảng cách/nhãn theo canvas; không crop tự động. |
| 9:16 | requires_redesign | high | Xếp lại quan hệ theo chiều dọc, tăng chữ, giảm panel; kiểm clipping riêng. |
| 1:1 | preferred | low | Đề xuất bố cục xuất phát; không xác nhận native ratio của media nguồn. |

Khung dọc: xếp lại quan hệ, giảm panel, tăng cỡ chữ và chừa vùng phụ đề theo dự án; không crop screenshot có chữ. Khung vuông: gom một tiêu điểm, đưa nhãn phụ ra vành. Vùng đề xuất cần chỉnh theo canvas/nội dung thật, không coi một hộp chuẩn hoá là bố cục đã QA mọi ratio.

## Prompt HyperFrames viết mới

> Sol tự viết brief triển khai dưới đây; không phải prompt gốc và không cam kết tái tạo chính xác nguồn. Chỉ dùng tài sản/font/media mà dự án có quyền.

Dựng một motion graphic mới tham chiếu ý tưởng “Shape morphing through UI states” (https://prompt-motion.com/twoclipping-5cba86) cho vai trò explain/proof/cta. Chọn canvas 1:1 làm điểm xuất phát, thời lượng cảnh trong khoảng 6–12 giây rồi chốt theo lượng nội dung thực. Một ý chính, sức chứa 1 tác vụ; 1–3 trạng thái UI; 1 tiêu đề ngắn. Thay toàn bộ brand, copy, số liệu và media bằng dữ kiện được dự án cấp hoặc xác minh.

Thiết kế cụ thể: Đề xuất dựng một wrapper liên tục, giữ anchor qua các trạng thái UI và đặt text ở track riêng. Con trỏ click/drag chỉ là keyframe xác định trước. Indicator có hai mép dùng curve khác nhau để stretch mà không đổi tâm đột ngột.

Nhịp dựng đề xuất:

1. Nút nén thành loader rồi mở thành player; nội dung cũ thoát trước nội dung mới.
2. Thanh player kéo dài thành slider, chuyển thành tabs và chart cùng một vùng anchor.
3. Chart thu vào command field rồi toast; trả cả shape và con trỏ về pose đầu.

Giữ khung cuối tối thiểu 0,8 giây sau chuyển động cuối để đọc. Bố cục partial; đặt chủ thể trong hộp đề xuất ở trên rồi kiểm theo canvas thật. DOM/SVG + GSAP; ảnh chụp có quyền chỉ dùng làm panel. Không cần Canvas cho nút, thẻ hay text.

Dùng một GSAP timeline paused, đăng ký vào window.__timelines bằng đúng data-composition-id sau khi dựng. Trạng thái đầu bằng fromTo; clip gốc không bị tween visibility/autoAlpha. Mọi frame là hàm của thời gian tuyệt đối, random có seed, chu kỳ hữu hạn; không đồng hồ hệ thống, chuột, network hay physics tích lũy. Không requestAnimationFrame tự chạy hoặc repeat vô hạn. Nếu dùng canvas/WebGL, render trực tiếp pose/state tại time bất kỳ; timeline là nguồn thời gian duy nhất.

Đặt font/media cục bộ có quyền và biến text/màu/dữ liệu thành tham số. Với narration hay nhiều cảnh dài, route sang general-video rồi dùng motion này như một beat, không ép toàn bộ brief dài vào một hit. Tiêu chí riêng: Không có cut che lỗi morph; frame biên loop khớp vị trí và vận tốc, không lặp vô hạn. Kiểm lint/check, snapshot đầu/giữa mỗi pha/cuối, seek ngược, clipping/chữ/tương phản/z-order và vùng phụ đề; ratio khác phải kiểm lại. Chỉ render khi task dựng video đã giao rõ.

## Liên quan / mức kiểm chứng

- [PM-twoclipping-221cab — Photo print app launch film](twoclipping-221cab.md)
- [PM-twoclipping-d89be5 — Landing page 3D scroll](twoclipping-d89be5.md)
- [PM-gabrielbuzziv-4ff0c6 — Enxovaly baby app promo](gabrielbuzziv-4ff0c6.md)

Metadata HTML: **đã thu**. Public prompt: **đã đọc toàn bộ**. Xem toàn video: **chưa**. Source code test: **chưa**. HyperFrames check/render: **chưa**. Prompt/media nguồn: **không archive**, chưa xác lập bulk redistribution license. [Cách dùng](../USAGE.md) · [Taxonomy](../TAXONOMY.md).
