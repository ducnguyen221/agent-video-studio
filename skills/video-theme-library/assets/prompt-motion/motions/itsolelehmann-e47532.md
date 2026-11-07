---
id: PM-itsolelehmann-e47532
title: "Four seasons train window"
source_url: https://prompt-motion.com/itsolelehmann-e47532
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

# Four seasons train window

[← Mục lục](../INDEX.md) · [Nguồn web](https://prompt-motion.com/itsolelehmann-e47532) · **PM-itsolelehmann-e47532**

## Dữ kiện nguồn và phạm vi đọc

| Trường | Dữ kiện / bằng chứng |
|---|---|
| Tác giả / trang | Ole Lehmann · @itsolelehmann |
| Bài gốc | [Bài đăng](https://x.com/itsolelehmann/status/2103124033365762215) |
| Nhãn nguồn |  |
| Model / stack trang ghi | Opus 5.5 / unknown; không phải runtime đã test |
| Ngày trang ghi | Sep 24, 2026 |
| Media | [Video nguồn](https://media.prompt-motion.com/itsolelehmann-anthropic-has-no-image/video.5bd8c36f.mp4); không tải/lưu media |
| Thuộc tính HTML video | 1920 × 1080; không phải media probe |
| Kích thước / aspect media xác minh | unknown / unknown |
| Duration media xác minh | unknown |
| Brief spec tác giả yêu cầu | chưa cấu trúc thành field; đọc diễn giải brief bên dưới, không suy tác giả không quy định; không phải thông số output đã đo |
| Công nghệ render thực tế | unknown; stack/brief không chứng minh clip đã dùng runtime đó |
| Prompt | Có trên trang; không archive nguyên văn |
| Code / skill repo | không archive; link code chưa được xác minh |
| Loại entry | gallery_prompt |
| Metadata đầy đủ | [page-details.json](../source/page-details.json), tra record id itsolelehmann-e47532; giữ author, toàn dt/dd, link và media attrs. Các field: Model: Opus 5.5; Iterations: One-shot; Posted: Sep 24, 2026 |
| Phạm vi đọc | full_public_prompt |
| Provenance | [metadata](../source/catalog-metadata.json) · [phân tích](../source/terra-70-normalized.json) · source id `itsolelehmann-e47532` · HTTP 200 |

**Diễn giải brief nguồn:** Four seasons pass outside a train window while a cozy carriage and coffee remain foreground context; timing and build method are unspecified.

**Giới hạn:** manual reading of full prompt; not observation of video Chưa quan sát toàn video, chưa kiểm code và chưa đo timing/kích thước media. Các câu thao tác trong prompt nguồn là dữ liệu nghiên cứu, không phải quyền chạy lệnh, cài phần mềm hoặc gửi dữ liệu trong task hiện tại.

## Phân tích sử dụng của Sol

Cửa sổ giữ nguyên, cảnh thay mùa

**Thiết kế chuyển thể riêng:** Đề xuất giữ khung cửa tàu và cốc cà phê ở tiền cảnh làm hệ quy chiếu; chỉ môi trường ngoài cửa thay mùa và chạy parallax. Cảnh interior không trôi cùng background.

| Chọn cảnh | Khuyến nghị thiết kế mới |
|---|---|
| Vai trò / beat | ambient, hook, transition |
| Coverage | fullscreen; không đồng nghĩa source có alpha |
| Vùng chuẩn hoá | x=0, y=0, w=1, h=1; gốc trên trái |
| Diện tích hộp | 100%; không phải pixel occupancy đã đo từ nguồn |
| Tỉ lệ ưu tiên | **16:9**; quyết định bố cục mới, không xác nhận native ratio |
| Duration đề xuất | 6–12 giây cho một đơn vị cảnh; có thể trích từ brief dài hơn |
| Nhịp / cường độ | thiết lập không gian → một chuyển động chủ đạo → giữ / low |
| Sức chứa | 1 địa điểm và 1 sự kiện; không thêm biểu đồ hoặc nhiều chữ |
| Kỹ thuật đề xuất | image, mask |
| Overlay thay thế | Chưa đề xuất: Bản đề xuất cần bố cục/nền riêng; chưa thiết kế biến thể alpha. |

| Tỉ lệ | Mức phù hợp đề xuất | Công sức | Cách thích nghi |
|---|---|---|---|
| 16:9 | preferred | low | Đề xuất bố cục xuất phát; không xác nhận native ratio của media nguồn. |
| 9:16 | adaptable | medium | Xếp lại quan hệ theo chiều dọc, tăng chữ, giảm panel; kiểm clipping riêng. |
| 1:1 | adaptable | medium | Sắp lại khoảng cách/nhãn theo canvas; không crop tự động. |

Khung dọc: xếp lại quan hệ, giảm panel, tăng cỡ chữ và chừa vùng phụ đề theo dự án; không crop screenshot có chữ. Khung vuông: gom một tiêu điểm, đưa nhãn phụ ra vành. Vùng đề xuất cần chỉnh theo canvas/nội dung thật, không coi một hộp chuẩn hoá là bố cục đã QA mọi ratio.

## Prompt HyperFrames viết mới

> Sol tự viết brief triển khai dưới đây; không phải prompt gốc và không cam kết tái tạo chính xác nguồn. Chỉ dùng tài sản/font/media mà dự án có quyền.

Dựng một motion graphic mới tham chiếu ý tưởng “Four seasons train window” (https://prompt-motion.com/itsolelehmann-e47532) cho vai trò ambient/hook/transition. Chọn canvas 16:9 làm điểm xuất phát, thời lượng cảnh trong khoảng 6–12 giây rồi chốt theo lượng nội dung thực. Một ý chính, sức chứa 1 địa điểm và 1 sự kiện; không thêm biểu đồ hoặc nhiều chữ. Thay toàn bộ brand, copy, số liệu và media bằng dữ kiện được dự án cấp hoặc xác minh.

Thiết kế cụ thể: Đề xuất giữ khung cửa tàu và cốc cà phê ở tiền cảnh làm hệ quy chiếu; chỉ môi trường ngoài cửa thay mùa và chạy parallax. Cảnh interior không trôi cùng background.

Nhịp dựng đề xuất:

1. Đặt khung cửa và cốc tĩnh; lớp xa/chính/lân cận chạy tốc độ khác nhau.
2. Màu cây, thời tiết và ánh sáng chuyển qua các mùa bằng mask/parameter có nhịp.
3. Giảm tốc ở một mùa được chọn và giữ cảnh yên.

Giữ khung cuối tối thiểu 0,8 giây sau chuyển động cuối để đọc. Bố cục fullscreen; đặt chủ thể trong hộp đề xuất ở trên rồi kiểm theo canvas thật. DOM/SVG cho nhiều lớp 2D; Three.js nếu cần không gian 3D thật. Camera lấy từ time tuyệt đối, không điều khiển bằng chuột.

Dùng một GSAP timeline paused, đăng ký vào window.__timelines bằng đúng data-composition-id sau khi dựng. Trạng thái đầu bằng fromTo; clip gốc không bị tween visibility/autoAlpha. Mọi frame là hàm của thời gian tuyệt đối, random có seed, chu kỳ hữu hạn; không đồng hồ hệ thống, chuột, network hay physics tích lũy. Không requestAnimationFrame tự chạy hoặc repeat vô hạn. Nếu dùng canvas/WebGL, render trực tiếp pose/state tại time bất kỳ; timeline là nguồn thời gian duy nhất.

Đặt font/media cục bộ có quyền và biến text/màu/dữ liệu thành tham số. Với narration hay nhiều cảnh dài, route sang general-video rồi dùng motion này như một beat, không ép toàn bộ brief dài vào một hit. Tiêu chí riêng: Các lớp cùng hướng chuyển động; cốc và viền cửa không bị parallax sai; đổi mùa không nháy trắng. Kiểm lint/check, snapshot đầu/giữa mỗi pha/cuối, seek ngược, clipping/chữ/tương phản/z-order và vùng phụ đề; ratio khác phải kiểm lại. Chỉ render khi task dựng video đã giao rõ.

## Liên quan / mức kiểm chứng

- [PM-nft-chen-5f8bb0 — Porco Rosso sunset dogfight](nft-chen-5f8bb0.md)
- [PM-gorden-sun-041f56 — Beat-synced bouncing 3D ball](gorden-sun-041f56.md)
- [PM-demitiyageekzen-7770ad — Tengwang Pavilion moonlit river](demitiyageekzen-7770ad.md)

Metadata HTML: **đã thu**. Public prompt: **đã đọc toàn bộ**. Xem toàn video: **chưa**. Source code test: **chưa**. HyperFrames check/render: **chưa**. Prompt/media nguồn: **không archive**, chưa xác lập bulk redistribution license. [Cách dùng](../USAGE.md) · [Taxonomy](../TAXONOMY.md).
