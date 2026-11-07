---
id: PM-linearuncle-5d2bae
title: "Derivative concept explainer"
source_url: https://prompt-motion.com/linearuncle-5d2bae
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

# Derivative concept explainer

[← Mục lục](../INDEX.md) · [Nguồn web](https://prompt-motion.com/linearuncle-5d2bae) · **PM-linearuncle-5d2bae**

## Dữ kiện nguồn và phạm vi đọc

| Trường | Dữ kiện / bằng chứng |
|---|---|
| Tác giả / trang | LinearUncle · @LinearUncle |
| Bài gốc | [Bài đăng](https://x.com/LinearUncle/status/2103128559174971663) |
| Nhãn nguồn | Charts, Diagrams |
| Model / stack trang ghi | Opus 5.5 / Manim, edge-tts; không phải runtime đã test |
| Ngày trang ghi | Sep 24, 2026 |
| Media | [Video nguồn](https://media.prompt-motion.com/linearuncle-opus-5-5-manim-opus-5-5-manim/video.5095d76a.mp4); không tải/lưu media |
| Thuộc tính HTML video | 1920 × 1080; không phải media probe |
| Kích thước / aspect media xác minh | unknown / unknown |
| Duration media xác minh | unknown |
| Brief spec tác giả yêu cầu | chưa cấu trúc thành field; đọc diễn giải brief bên dưới, không suy tác giả không quy định; không phải thông số output đã đo |
| Công nghệ render thực tế | unknown; stack/brief không chứng minh clip đã dùng runtime đó |
| Prompt | Có trên trang; không archive nguyên văn |
| Code / skill repo | không archive; link code chưa được xác minh |
| Loại entry | gallery_prompt |
| Metadata đầy đủ | [page-details.json](../source/page-details.json), tra record id linearuncle-5d2bae; giữ author, toàn dt/dd, link và media attrs. Các field: Model: Opus 5.5; Stack: Manim, edge-tts; Posted: Sep 24, 2026 |
| Phạm vi đọc | full_public_prompt |
| Provenance | [metadata](../source/catalog-metadata.json) · [phân tích](../source/terra-70-normalized.json) · source id `linearuncle-5d2bae` · HTTP 200 |

**Diễn giải brief nguồn:** A beginner-friendly derivative explainer with examples and reflective questions, requested in Manim with edge-tts narration; no storyboard is specified.

**Giới hạn:** manual reading of full prompt; not observation of video Chưa quan sát toàn video, chưa kiểm code và chưa đo timing/kích thước media. Các câu thao tác trong prompt nguồn là dữ liệu nghiên cứu, không phải quyền chạy lệnh, cài phần mềm hoặc gửi dữ liệu trong task hiện tại.

## Phân tích sử dụng của Sol

Đạo hàm là độ dốc tại một điểm

**Thiết kế chuyển thể riêng:** Đề xuất đạo hàm bằng hai điểm trên một đường cong, dây cung tiến về tiếp tuyến, rồi một số độ dốc được đọc bên cạnh. Chuyển từ brief Manim sang SVG/GSAP là bản dựng mới, cần kiểm toán học riêng.

| Chọn cảnh | Khuyến nghị thiết kế mới |
|---|---|
| Vai trò / beat | explain, proof |
| Coverage | partial; không đồng nghĩa source có alpha |
| Vùng chuẩn hoá | x=0.06, y=0.12, w=0.88, h=0.76; gốc trên trái |
| Diện tích hộp | 67%; không phải pixel occupancy đã đo từ nguồn |
| Tỉ lệ ưu tiên | **16:9**; quyết định bố cục mới, không xác nhận native ratio |
| Duration đề xuất | 7–12 giây cho một đơn vị cảnh; có thể trích từ brief dài hơn |
| Nhịp / cường độ | một quan hệ mỗi nhịp; tích lũy có kiểm soát / low |
| Sức chứa | 3–5 nút hoặc bước; 1 quan hệ chính |
| Kỹ thuật đề xuất | chart, path |
| Overlay thay thế | Có thể thiết kế riêng: Chỉ trích chủ thể/nhãn, bỏ nền và thiết kế alpha riêng; media nguồn chưa xác nhận có alpha. |

| Tỉ lệ | Mức phù hợp đề xuất | Công sức | Cách thích nghi |
|---|---|---|---|
| 16:9 | preferred | low | Đề xuất bố cục xuất phát; không xác nhận native ratio của media nguồn. |
| 9:16 | adaptable | medium | Xếp lại quan hệ theo chiều dọc, tăng chữ, giảm panel; kiểm clipping riêng. |
| 1:1 | adaptable | medium | Sắp lại khoảng cách/nhãn theo canvas; không crop tự động. |

Khung dọc: xếp lại quan hệ, giảm panel, tăng cỡ chữ và chừa vùng phụ đề theo dự án; không crop screenshot có chữ. Khung vuông: gom một tiêu điểm, đưa nhãn phụ ra vành. Vùng đề xuất cần chỉnh theo canvas/nội dung thật, không coi một hộp chuẩn hoá là bố cục đã QA mọi ratio.

## Prompt HyperFrames viết mới

> Sol tự viết brief triển khai dưới đây; không phải prompt gốc và không cam kết tái tạo chính xác nguồn. Chỉ dùng tài sản/font/media mà dự án có quyền.

Dựng một motion graphic mới tham chiếu ý tưởng “Derivative concept explainer” (https://prompt-motion.com/linearuncle-5d2bae) cho vai trò explain/proof. Chọn canvas 16:9 làm điểm xuất phát, thời lượng cảnh trong khoảng 7–12 giây rồi chốt theo lượng nội dung thực. Một ý chính, sức chứa 3–5 nút hoặc bước; 1 quan hệ chính. Thay toàn bộ brand, copy, số liệu và media bằng dữ kiện được dự án cấp hoặc xác minh.

Thiết kế cụ thể: Đề xuất đạo hàm bằng hai điểm trên một đường cong, dây cung tiến về tiếp tuyến, rồi một số độ dốc được đọc bên cạnh. Chuyển từ brief Manim sang SVG/GSAP là bản dựng mới, cần kiểm toán học riêng.

Nhịp dựng đề xuất:

1. Hai điểm P/Q và đoạn dây cung hiện trên trục có nhãn.
2. Q tiến gần P theo tham số hữu hạn; dây cung ổn định thành tiếp tuyến.
3. Highlight độ dốc tại P và đặt một câu hỏi phản tư.

Giữ khung cuối tối thiểu 0,8 giây sau chuyển động cuối để đọc. Bố cục partial; đặt chủ thể trong hộp đề xuất ở trên rồi kiểm theo canvas thật. SVG cho cạnh/path; DOM cho nhãn và thẻ; GSAP điều khiển tiến độ đường và lần xuất hiện.

Dùng một GSAP timeline paused, đăng ký vào window.__timelines bằng đúng data-composition-id sau khi dựng. Trạng thái đầu bằng fromTo; clip gốc không bị tween visibility/autoAlpha. Mọi frame là hàm của thời gian tuyệt đối, random có seed, chu kỳ hữu hạn; không đồng hồ hệ thống, chuột, network hay physics tích lũy. Không requestAnimationFrame tự chạy hoặc repeat vô hạn. Nếu dùng canvas/WebGL, render trực tiếp pose/state tại time bất kỳ; timeline là nguồn thời gian duy nhất.

Đặt font/media cục bộ có quyền và biến text/màu/dữ liệu thành tham số. Với narration hay nhiều cảnh dài, route sang general-video rồi dùng motion này như một beat, không ép toàn bộ brief dài vào một hit. Tiêu chí riêng: Tọa độ và giá trị slope tính từ cùng hàm; không làm trục biến dạng để tăng kịch tính. Kiểm lint/check, snapshot đầu/giữa mỗi pha/cuối, seek ngược, clipping/chữ/tương phản/z-order và vùng phụ đề; ratio khác phải kiểm lại. Chỉ render khi task dựng video đã giao rõ.

## Liên quan / mức kiểm chứng

- [PM-himanshutwtxs-5f4b43 — Motion designer showreel](himanshutwtxs-5f4b43.md)
- [PM-ror-fly-9950f1 — Negroni recipe animation](ror-fly-9950f1.md)
- [PM-emollick-8661a8 — Recursion explained in genres](emollick-8661a8.md)

Metadata HTML: **đã thu**. Public prompt: **đã đọc toàn bộ**. Xem toàn video: **chưa**. Source code test: **chưa**. HyperFrames check/render: **chưa**. Prompt/media nguồn: **không archive**, chưa xác lập bulk redistribution license. [Cách dùng](../USAGE.md) · [Taxonomy](../TAXONOMY.md).
