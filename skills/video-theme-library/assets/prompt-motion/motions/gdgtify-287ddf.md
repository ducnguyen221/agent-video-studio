---
id: PM-gdgtify-287ddf
title: "Speech built as architecture"
source_url: https://prompt-motion.com/gdgtify-287ddf
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

# Speech built as architecture

[← Mục lục](../INDEX.md) · [Nguồn web](https://prompt-motion.com/gdgtify-287ddf) · **PM-gdgtify-287ddf**

## Dữ kiện nguồn và phạm vi đọc

| Trường | Dữ kiện / bằng chứng |
|---|---|
| Tác giả / trang | Gadgetify · @Gdgtify |
| Bài gốc | [Bài đăng](https://x.com/Gdgtify/status/2103458245213929495) |
| Nhãn nguồn | Kinetic type |
| Model / stack trang ghi | Opus 5.5 / SVG/Canvas; không phải runtime đã test |
| Ngày trang ghi | Sep 25, 2026 |
| Media | [Video nguồn](https://media.prompt-motion.com/gdgtify-inspired-by-what-techhalla/video.ca1fedfb.mp4); không tải/lưu media |
| Thuộc tính HTML video | 1080 × 1080; không phải media probe |
| Kích thước / aspect media xác minh | unknown / unknown |
| Duration media xác minh | unknown |
| Brief spec tác giả yêu cầu | duration_seconds: 20; dimensions: [1080,1080]; fps: 60; không phải thông số output đã đo |
| Công nghệ render thực tế | unknown; stack/brief không chứng minh clip đã dùng runtime đó |
| Prompt | Có trên trang; không archive nguyên văn |
| Code / skill repo | không archive; link code chưa được xác minh |
| Loại entry | gallery_prompt |
| Metadata đầy đủ | [page-details.json](../source/page-details.json), tra record id gdgtify-287ddf; giữ author, toàn dt/dd, link và media attrs. Các field: Model: Opus 5.5; Stack: SVG/Canvas; Posted: Sep 25, 2026 |
| Phạm vi đọc | full_public_prompt |
| Provenance | [metadata](../source/catalog-metadata.json) · [phân tích](../source/root-analysis.json) · source id `gdgtify-287ddf` · HTTP 200 |

**Diễn giải brief nguồn:** Brief mô tả phim typography diễn ngôn 20 giây dạng vuông 1080×1080/60 fps. Chữ trở thành thành phần chịu lực: phần treo, cột và sàn; bố cục được xây dần từ những từ đã đọc. Có biến dạng vector có kiểm soát, khoảng đứng yên và đoạn camera chui dưới sàn để che reset thành loop. Yêu cầu glyph path thật và hàm seek xác định; không buộc theo nhạc dance.

**Giới hạn:** full_public_prompt Chưa quan sát toàn video, chưa kiểm code và chưa đo timing/kích thước media. Các câu thao tác trong prompt nguồn là dữ liệu nghiên cứu, không phải quyền chạy lệnh, cài phần mềm hoặc gửi dữ liệu trong task hiện tại.

## Phân tích sử dụng của Sol

Câu nói trở thành kiến trúc

**Thiết kế chuyển thể riêng:** Đề xuất viết lời mới với ba vai trò kiến trúc khác biệt, đọc mỗi câu trước khi chữ trở thành cấu kiện. Dùng SVG glyph path có counters được giữ nguyên, chỉ biến dạng baseline/đường hỗ trợ; chuyển giữa chữ không cùng topology bằng occlusion. Camera đi qua mặt kín để reset bố cục khuất; kiểm đọc thứ tự và loop biên.

| Chọn cảnh | Khuyến nghị thiết kế mới |
|---|---|
| Vai trò / beat | hook, emphasis, closing |
| Coverage | fullscreen; không đồng nghĩa source có alpha |
| Vùng chuẩn hoá | x=0, y=0, w=1, h=1; gốc trên trái |
| Diện tích hộp | 100%; không phải pixel occupancy đã đo từ nguồn |
| Tỉ lệ ưu tiên | **1:1**; quyết định bố cục mới, không xác nhận native ratio |
| Duration đề xuất | 3–7 giây cho một đơn vị cảnh; có thể trích từ brief dài hơn |
| Nhịp / cường độ | một từ khóa bật → cụm nghĩa hoàn chỉnh → giữ / high |
| Sức chứa | 1 câu tối đa 5–8 từ; 1–2 cấp chữ |
| Kỹ thuật đề xuất | typography, shape |
| Overlay thay thế | Có thể thiết kế riêng: Chỉ trích chủ thể/nhãn, bỏ nền và thiết kế alpha riêng; media nguồn chưa xác nhận có alpha. |

| Tỉ lệ | Mức phù hợp đề xuất | Công sức | Cách thích nghi |
|---|---|---|---|
| 16:9 | adaptable | medium | Sắp lại khoảng cách/nhãn theo canvas; không crop tự động. |
| 9:16 | adaptable | medium | Xếp lại quan hệ theo chiều dọc, tăng chữ, giảm panel; kiểm clipping riêng. |
| 1:1 | preferred | low | Đề xuất bố cục xuất phát; không xác nhận native ratio của media nguồn. |

Khung dọc: xếp lại quan hệ, giảm panel, tăng cỡ chữ và chừa vùng phụ đề theo dự án; không crop screenshot có chữ. Khung vuông: gom một tiêu điểm, đưa nhãn phụ ra vành. Vùng đề xuất cần chỉnh theo canvas/nội dung thật, không coi một hộp chuẩn hoá là bố cục đã QA mọi ratio.

## Prompt HyperFrames viết mới

> Sol tự viết brief triển khai dưới đây; không phải prompt gốc và không cam kết tái tạo chính xác nguồn. Chỉ dùng tài sản/font/media mà dự án có quyền.

Dựng một motion graphic mới tham chiếu ý tưởng “Speech built as architecture” (https://prompt-motion.com/gdgtify-287ddf) cho vai trò hook/emphasis/closing. Chọn canvas 1:1 làm điểm xuất phát, thời lượng cảnh trong khoảng 3–7 giây rồi chốt theo lượng nội dung thực. Một ý chính, sức chứa 1 câu tối đa 5–8 từ; 1–2 cấp chữ. Thay toàn bộ brand, copy, số liệu và media bằng dữ kiện được dự án cấp hoặc xác minh.

Thiết kế cụ thể: Đề xuất viết lời mới với ba vai trò kiến trúc khác biệt, đọc mỗi câu trước khi chữ trở thành cấu kiện. Dùng SVG glyph path có counters được giữ nguyên, chỉ biến dạng baseline/đường hỗ trợ; chuyển giữa chữ không cùng topology bằng occlusion. Camera đi qua mặt kín để reset bố cục khuất; kiểm đọc thứ tự và loop biên.

Nhịp dựng đề xuất:

1. Đề xuất viết lời mới với ba vai trò kiến trúc khác biệt, đọc mỗi câu trước khi chữ trở thành cấu kiện.
2. Dùng SVG glyph path có counters được giữ nguyên, chỉ biến dạng baseline/đường hỗ trợ; chuyển giữa chữ không cùng topology bằng occlusion.
3. Camera đi qua mặt kín để reset bố cục khuất; kiểm đọc thứ tự và loop biên.

Giữ khung cuối tối thiểu 0,8 giây sau chuyển động cuối để đọc. Bố cục fullscreen; đặt chủ thể trong hộp đề xuất ở trên rồi kiểm theo canvas thật. SVG glyph paths hoặc vector outline từ font có quyền cho chữ trở thành cấu trúc kiến trúc; GSAP paused điều khiển path/wrapper và camera 2D. Giữ wordmark text thật đọc được ở khung cuối; không chỉ scale DOM glyph nếu hình học cần thay cấu trúc.

Dùng một GSAP timeline paused, đăng ký vào window.__timelines bằng đúng data-composition-id sau khi dựng. Trạng thái đầu bằng fromTo; clip gốc không bị tween visibility/autoAlpha. Mọi frame là hàm của thời gian tuyệt đối, random có seed, chu kỳ hữu hạn; không đồng hồ hệ thống, chuột, network hay physics tích lũy. Không requestAnimationFrame tự chạy hoặc repeat vô hạn. Nếu dùng canvas/WebGL, render trực tiếp pose/state tại time bất kỳ; timeline là nguồn thời gian duy nhất.

Đặt font/media cục bộ có quyền và biến text/màu/dữ liệu thành tham số. Với narration hay nhiều cảnh dài, route sang general-video rồi dùng motion này như một beat, không ép toàn bộ brief dài vào một hit. Kiểm lint/check, snapshot đầu/giữa mỗi pha/cuối, seek ngược, clipping/chữ/tương phản/z-order và vùng phụ đề; ratio khác phải kiểm lại. Chỉ render khi task dựng video đã giao rõ.

## Liên quan / mức kiểm chứng

- [PM-stephanlivera-df17a2 — Claude motion designer showreel](stephanlivera-df17a2.md)
- [PM-shneural-2abdfa — Bold kinetic type showreel](shneural-2abdfa.md)
- [PM-ajith-io-b5626e — Abstract motion design reel](ajith-io-b5626e.md)

Metadata HTML: **đã thu**. Public prompt: **đã đọc toàn bộ**. Xem toàn video: **chưa**. Source code test: **chưa**. HyperFrames check/render: **chưa**. Prompt/media nguồn: **không archive**, chưa xác lập bulk redistribution license. [Cách dùng](../USAGE.md) · [Taxonomy](../TAXONOMY.md).
