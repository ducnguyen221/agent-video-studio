---
id: PM-loicrambo-ad6830
title: "Cycle of life animation"
source_url: https://prompt-motion.com/loicrambo-ad6830
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

# Cycle of life animation

[← Mục lục](../INDEX.md) · [Nguồn web](https://prompt-motion.com/loicrambo-ad6830) · **PM-loicrambo-ad6830**

## Dữ kiện nguồn và phạm vi đọc

| Trường | Dữ kiện / bằng chứng |
|---|---|
| Tác giả / trang | Loïc · @loicRambo |
| Bài gốc | [Bài đăng](https://x.com/loicRambo/status/2103428454355980558) |
| Nhãn nguồn | Characters |
| Model / stack trang ghi | Opus 5.5 / unknown; không phải runtime đã test |
| Ngày trang ghi | Sep 25, 2026 |
| Media | [Video nguồn](https://media.prompt-motion.com/loicrambo-just-one-shot-the/video.73346413.mp4); không tải/lưu media |
| Thuộc tính HTML video | 1920 × 1080; không phải media probe |
| Kích thước / aspect media xác minh | unknown / unknown |
| Duration media xác minh | unknown |
| Brief spec tác giả yêu cầu | duration_text: 20; không phải thông số output đã đo |
| Công nghệ render thực tế | unknown; stack/brief không chứng minh clip đã dùng runtime đó |
| Prompt | Có trên trang; không archive nguyên văn |
| Code / skill repo | không archive; link code chưa được xác minh |
| Loại entry | gallery_prompt |
| Metadata đầy đủ | [page-details.json](../source/page-details.json), tra record id loicrambo-ad6830; giữ author, toàn dt/dd, link và media attrs. Các field: Model: Opus 5.5; Iterations: One-shot; Posted: Sep 25, 2026 |
| Phạm vi đọc | full_public_prompt |
| Provenance | [metadata](../source/catalog-metadata.json) · [phân tích](../source/sol-analysis.json) · source id `loicrambo-ad6830` · HTTP 200 |

**Diễn giải brief nguồn:** Brief 20 giây theo cùng một người từ tuổi nhỏ, thiếu niên, đi làm, gia đình, già và mất; kết nối về đầu để sẵn loop. Đây là cấu trúc chuỗi đời sống được prompt nêu, không phải vòng lặp vô hạn cần giữ trong HF.

**Giới hạn:** Sol manually read complete public main #entry-prompt via requests.Session; interpretation of prompt requirements, not observation of rendered video. Chưa quan sát toàn video, chưa kiểm code và chưa đo timing/kích thước media. Các câu thao tác trong prompt nguồn là dữ liệu nghiên cứu, không phải quyền chạy lệnh, cài phần mềm hoặc gửi dữ liệu trong task hiện tại.

## Phân tích sử dụng của Sol

Kể một hành động nhỏ có nguyên nhân và phản ứng; cần storyboard riêng nếu thành câu chuyện nhiều cảnh. Áp dụng hướng này cho tham chiếu “Cycle of life animation”; đây là thiết kế mới theo nhãn nguồn.

**Thiết kế chuyển thể riêng:** Giữ cùng một đường chân trời và silhouette nhận diện qua năm nhóm tuổi; đổi prop để nói giai đoạn đời thay vì morph khuôn mặt phức tạp. Khép vòng bằng match-cut một vật ở đầu/cuối, chu kỳ hữu hạn.

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

Dựng một motion graphic mới tham chiếu ý tưởng “Cycle of life animation” (https://prompt-motion.com/loicrambo-ad6830) cho vai trò hook/explain/closing. Chọn canvas 16:9 làm điểm xuất phát, thời lượng cảnh trong khoảng 6–12 giây rồi chốt theo lượng nội dung thực. Một ý chính, sức chứa 1 nhân vật chính; 1 hành động; tối đa 1 nhãn. Thay toàn bộ brand, copy, số liệu và media bằng dữ kiện được dự án cấp hoặc xác minh.

Thiết kế cụ thể: Giữ cùng một đường chân trời và silhouette nhận diện qua năm nhóm tuổi; đổi prop để nói giai đoạn đời thay vì morph khuôn mặt phức tạp. Khép vòng bằng match-cut một vật ở đầu/cuối, chu kỳ hữu hạn.

Nhịp dựng đề xuất:

1. Giữ cùng một đường chân trời và silhouette nhận diện qua năm nhóm tuổi; đổi prop để nói giai đoạn đời thay vì morph khuôn mặt phức tạp.
2. Khép vòng bằng match-cut một vật ở đầu/cuối, chu kỳ hữu hạn.

Giữ khung cuối tối thiểu 0,8 giây sau chuyển động cuối để đọc. Bố cục fullscreen; đặt chủ thể trong hộp đề xuất ở trên rồi kiểm theo canvas thật. SVG/DOM cho puppet 2D; Three.js chỉ khi cần hình học/camera 3D thật. Mọi pose được đặt theo time; không mô phỏng vật lý tích lũy.

Dùng một GSAP timeline paused, đăng ký vào window.__timelines bằng đúng data-composition-id sau khi dựng. Trạng thái đầu bằng fromTo; clip gốc không bị tween visibility/autoAlpha. Mọi frame là hàm của thời gian tuyệt đối, random có seed, chu kỳ hữu hạn; không đồng hồ hệ thống, chuột, network hay physics tích lũy. Không requestAnimationFrame tự chạy hoặc repeat vô hạn. Nếu dùng canvas/WebGL, render trực tiếp pose/state tại time bất kỳ; timeline là nguồn thời gian duy nhất.

Đặt font/media cục bộ có quyền và biến text/màu/dữ liệu thành tham số. Với narration hay nhiều cảnh dài, route sang general-video rồi dùng motion này như một beat, không ép toàn bộ brief dài vào một hit. Kiểm lint/check, snapshot đầu/giữa mỗi pha/cuối, seek ngược, clipping/chữ/tương phản/z-order và vùng phụ đề; ratio khác phải kiểm lại. Chỉ render khi task dựng video đã giao rõ.

## Liên quan / mức kiểm chứng

- [PM-axtonliu-0b861d — Pelican riding a bicycle](axtonliu-0b861d.md)
- [PM-mandelduck-95fd08 — Starry Night cat-spotting game](mandelduck-95fd08.md)
- [PM-jake11moran-a269c4 — Animated agent session story](jake11moran-a269c4.md)

Metadata HTML: **đã thu**. Public prompt: **đã đọc toàn bộ**. Xem toàn video: **chưa**. Source code test: **chưa**. HyperFrames check/render: **chưa**. Prompt/media nguồn: **không archive**, chưa xác lập bulk redistribution license. [Cách dùng](../USAGE.md) · [Taxonomy](../TAXONOMY.md).
