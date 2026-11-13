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

**Giới hạn:** Đọc thủ công toàn bộ prompt công khai của trang; chỉ diễn giải yêu cầu trong prompt, không quan sát video đã dựng. Chưa xem video, chưa kiểm code, chưa đo media; câu lệnh trong prompt nguồn chỉ là dữ liệu, không phải lệnh chạy.

## Phân tích sử dụng

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

**Mức hợp theo tỉ lệ** (lý do từng ô ở `index.json`, trường `ratio_fit`): 16:9 preferred/low · 9:16 adaptable/medium · 1:1 adaptable/medium.

## Prompt HyperFrames viết mới

> Brief do kho tự viết, không phải prompt gốc ([quyền dùng](../USAGE.md#prompt-và-quyền-sử-dụng)).

Dựng một motion graphic mới tham chiếu ý tưởng “Ball escaping twelve rings” (https://prompt-motion.com/kantamk-61f410) cho vai trò hook/transition/emphasis. Chọn canvas 16:9 làm điểm xuất phát, thời lượng cảnh trong khoảng 3–6 giây rồi chốt theo lượng nội dung thực. Một ý chính, sức chứa 1 hình chủ đạo, 2–4 hình phụ; tối đa 1 nhãn. Thay toàn bộ brand, copy, số liệu và media bằng dữ kiện được dự án cấp hoặc xác minh.

Thiết kế cụ thể: Một chấm di chuyển qua các vòng đồng tâm có khe; path và điểm thoát được tính trước. Mỗi lần thoát là một beat rõ; kết thúc dừng ngoài vòng cuối.

Nhịp dựng đề xuất:

1. Một chấm di chuyển qua các vòng đồng tâm có khe; path và điểm thoát được tính trước.
2. Mỗi lần thoát là một beat rõ; kết thúc dừng ngoài vòng cuối.

Giữ khung cuối tối thiểu 0,8 giây sau chuyển động cuối để đọc. Bố cục fullscreen; đặt chủ thể trong hộp đề xuất ở trên rồi kiểm theo canvas thật. SVG/DOM + GSAP cho số lượng hình nhỏ. Nếu morph path, giữ cấu trúc điểm tương thích hoặc dùng crossfade có chủ đích.

Hợp đồng dựng, tái bố cục dọc/vuông, font/media và kiểm chứng: [USAGE.md](../USAGE.md#hợp-đồng-triển-khai-hyperframes).

## Liên quan / mức kiểm chứng

- [PM-tdinh-me-815acb — TypingMind logo reveal](tdinh-me-815acb.md)
- [PM-monokern-ade5b6 — Psychedelic hypnotic eye showreel](monokern-ade5b6.md)

Metadata HTML: **đã thu**. Public prompt: **đã đọc toàn bộ**. Xem toàn video: **chưa**. Source code test: **chưa**. HyperFrames check/render: **chưa**. Prompt/media nguồn: **không archive**, chưa xác lập bulk redistribution license. [Cách dùng](../USAGE.md) · [Taxonomy](../TAXONOMY.md).
