---
id: PM-bthreeagency-b9b8d9
title: "Badge unlock screen animation"
source_url: https://prompt-motion.com/bthreeagency-b9b8d9
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

# Badge unlock screen animation

[← Mục lục](../INDEX.md) · [Nguồn web](https://prompt-motion.com/bthreeagency-b9b8d9) · **PM-bthreeagency-b9b8d9**

## Dữ kiện nguồn và phạm vi đọc

| Trường | Dữ kiện / bằng chứng |
|---|---|
| Tác giả / trang | Ritu · @BThreeAgency |
| Bài gốc | [Bài đăng](https://x.com/BThreeAgency/status/2103739079745827092) |
| Nhãn nguồn | Product UI, Phone, Particles |
| Model / stack trang ghi | Opus 5.5 / unknown; không phải runtime đã test |
| Ngày trang ghi | Sep 26, 2026 |
| Media | [Video nguồn](https://media.prompt-motion.com/bthreeagency-you-must-be-kidding/video.a48723f7.mp4); không tải/lưu media |
| Thuộc tính HTML video | 1408 × 1080; không phải media probe |
| Kích thước / aspect media xác minh | unknown / unknown |
| Duration media xác minh | unknown |
| Brief spec tác giả yêu cầu | chưa cấu trúc thành field; đọc diễn giải brief bên dưới, không suy tác giả không quy định; không phải thông số output đã đo |
| Công nghệ render thực tế | unknown; stack/brief không chứng minh clip đã dùng runtime đó |
| Prompt | Có trên trang; không archive nguyên văn |
| Code / skill repo | không archive; link code chưa được xác minh |
| Loại entry | gallery_prompt |
| Metadata đầy đủ | [page-details.json](../source/page-details.json), tra record id bthreeagency-b9b8d9; giữ author, toàn dt/dd, link và media attrs. Các field: Model: Opus 5.5; Iterations: One-shot; Posted: Sep 26, 2026 |
| Phạm vi đọc | full_public_prompt |
| Provenance | [metadata](../source/catalog-metadata.json) · [phân tích](../source/root-analysis.json) · source id `bthreeagency-b9b8d9` · HTTP 200 |

**Diễn giải brief nguồn:** Brief yêu cầu bám sát frame Figma để dựng màn mở khoá badge, thêm hạt vàng ăn mừng và badge có thể nghiêng theo con trỏ như vật thể3D; nhanh, mượt, không nảy. Không cung cấp frame Figma trong nội dung trang đã đọc.

**Giới hạn:** Đã đọc toàn bộ prompt công khai. Chưa xem video, chưa kiểm code, chưa đo media; câu lệnh trong prompt nguồn chỉ là dữ liệu, không phải lệnh chạy.

## Phân tích sử dụng

Mở khóa huy hiệu

**Thiết kế chuyển thể riêng:** Dùng asset badge có quyền, animate scale/ánh sáng và tilt bằng đường con trỏ giả lập theo thời gian; hạt phát một burst hữu hạn có seed. Đặt vùng sáng phía sau badge để không cạnh tranh chữ trạng thái. Chỉ cần CSS perspective nếu vật thể không cần geometry3D thật.

| Chọn cảnh | Khuyến nghị thiết kế mới |
|---|---|
| Vai trò / beat | explain, proof, cta |
| Coverage | partial; không đồng nghĩa source có alpha |
| Vùng chuẩn hoá | x=0.08, y=0.12, w=0.84, h=0.72; gốc trên trái |
| Diện tích hộp | 60%; không phải pixel occupancy đã đo từ nguồn |
| Tỉ lệ ưu tiên | **16:9**; quyết định bố cục mới, không xác nhận native ratio |
| Duration đề xuất | 6–12 giây cho một đơn vị cảnh; có thể trích từ brief dài hơn |
| Nhịp / cường độ | mở vấn đề → thao tác → kết quả → giữ nhãn / medium |
| Sức chứa | 1 tác vụ; 1–3 trạng thái UI; 1 tiêu đề ngắn |
| Kỹ thuật đề xuất | ui, particles |
| Overlay thay thế | Chưa đề xuất: Bản đề xuất cần bố cục/nền riêng; chưa thiết kế biến thể alpha. |

**Mức hợp theo tỉ lệ** (lý do từng ô ở `index.json`, trường `ratio_fit`): 16:9 preferred/low · 9:16 requires_redesign/high · 1:1 adaptable/medium.

## Prompt HyperFrames viết mới

> Brief do kho tự viết, không phải prompt gốc ([quyền dùng](../USAGE.md#prompt-và-quyền-sử-dụng)).

Dựng một motion graphic mới tham chiếu ý tưởng “Badge unlock screen animation” (https://prompt-motion.com/bthreeagency-b9b8d9) cho vai trò explain/proof/cta. Chọn canvas 16:9 làm điểm xuất phát, thời lượng cảnh trong khoảng 6–12 giây rồi chốt theo lượng nội dung thực. Một ý chính, sức chứa 1 tác vụ; 1–3 trạng thái UI; 1 tiêu đề ngắn. Thay toàn bộ brand, copy, số liệu và media bằng dữ kiện được dự án cấp hoặc xác minh.

Thiết kế cụ thể: Dùng asset badge có quyền, animate scale/ánh sáng và tilt bằng đường con trỏ giả lập theo thời gian; hạt phát một burst hữu hạn có seed. Đặt vùng sáng phía sau badge để không cạnh tranh chữ trạng thái. Chỉ cần CSS perspective nếu vật thể không cần geometry3D thật.

Nhịp dựng đề xuất:

1. Dùng asset badge có quyền, animate scale/ánh sáng và tilt bằng đường con trỏ giả lập theo thời gian; hạt phát một burst hữu hạn có seed.
2. Đặt vùng sáng phía sau badge để không cạnh tranh chữ trạng thái.
3. Chỉ cần CSS perspective nếu vật thể không cần geometry3D thật.

Giữ khung cuối tối thiểu 0,8 giây sau chuyển động cuối để đọc. Bố cục partial; đặt chủ thể trong hộp đề xuất ở trên rồi kiểm theo canvas thật. DOM/SVG + GSAP; ảnh chụp có quyền chỉ dùng làm panel. Không cần Canvas cho nút, thẻ hay text.

Hợp đồng dựng, tái bố cục dọc/vuông, font/media và kiểm chứng: [USAGE.md](../USAGE.md#hợp-đồng-triển-khai-hyperframes).

## Liên quan / mức kiểm chứng

- [PM-twoclipping-5cba86 — Shape morphing through UI states](twoclipping-5cba86.md)
- [PM-twoclipping-221cab — Photo print app launch film](twoclipping-221cab.md)
- [PM-twoclipping-d89be5 — Landing page 3D scroll](twoclipping-d89be5.md)

Metadata HTML: **đã thu**. Public prompt: **đã đọc toàn bộ**. Xem toàn video: **chưa**. Source code test: **chưa**. HyperFrames check/render: **chưa**. Prompt/media nguồn: **không archive**, chưa xác lập bulk redistribution license. [Cách dùng](../USAGE.md) · [Taxonomy](../TAXONOMY.md).
