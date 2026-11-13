---
id: PM-twoclipping-221cab
title: "Photo print app launch film"
source_url: https://prompt-motion.com/twoclipping-221cab
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

# Photo print app launch film

[← Mục lục](../INDEX.md) · [Nguồn web](https://prompt-motion.com/twoclipping-221cab) · **PM-twoclipping-221cab**

## Dữ kiện nguồn và phạm vi đọc

| Trường | Dữ kiện / bằng chứng |
|---|---|
| Tác giả / trang | zero · @twoclipping |
| Bài gốc | [Bài đăng](https://x.com/twoclipping/status/2103835273813496100) |
| Nhãn nguồn | Product UI, Phone, Photos, Music |
| Model / stack trang ghi | Opus 5.5 / HTML + Playwright; không phải runtime đã test |
| Ngày trang ghi | Sep 26, 2026 |
| Media | [Video nguồn](https://media.prompt-motion.com/twoclipping-opus-5-5-is-the/video.7b6c0f2a.mp4); không tải/lưu media |
| Thuộc tính HTML video | 1440 × 1440; không phải media probe |
| Kích thước / aspect media xác minh | unknown / unknown |
| Duration media xác minh | unknown |
| Brief spec tác giả yêu cầu | chưa cấu trúc thành field; đọc diễn giải brief bên dưới, không suy tác giả không quy định; không phải thông số output đã đo |
| Công nghệ render thực tế | unknown; stack/brief không chứng minh clip đã dùng runtime đó |
| Prompt | Có trên trang; không archive nguyên văn |
| Code / skill repo | không archive; link code chưa được xác minh |
| Loại entry | gallery_prompt |
| Metadata đầy đủ | [page-details.json](../source/page-details.json), tra record id twoclipping-221cab; giữ author, toàn dt/dd, link và media attrs. Các field: Model: Opus 5.5; Stack: HTML + Playwright; Posted: Sep 26, 2026 |
| Phạm vi đọc | full_public_prompt |
| Provenance | [metadata](../source/catalog-metadata.json) · [phân tích](../source/terra-70-normalized.json) · source id `twoclipping-221cab` · HTTP 200 |

**Diễn giải brief nguồn (tiếng Anh, chưa dịch):** A continuous 2D photo-print launch connects wordmark, gallery grid, glass UI, phone, ordering sequence and a real-wall reveal through shared shapes; it requests seekable motion, beat review and a loop.

**Giới hạn:** Đọc thủ công toàn bộ prompt; chưa quan sát video. Chưa xem video, chưa kiểm code, chưa đo media; câu lệnh trong prompt nguồn chỉ là dữ liệu, không phải lệnh chạy.

## Phân tích sử dụng

Từ ảnh số tới sản phẩm in

**Thiết kế chuyển thể riêng:** Đề xuất theo một ảnh duy nhất qua lưới ảnh, điện thoại, thao tác đặt in và khung ảnh trên tường. Shared rectangle của ảnh là cầu nối; giữ aspect ảnh và thay đổi môi trường bao quanh, không đổi ảnh giữa cut.

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
| Kỹ thuật đề xuất | image, ui |
| Overlay thay thế | Chưa đề xuất: Bản đề xuất cần bố cục/nền riêng; chưa thiết kế biến thể alpha. |

**Mức hợp theo tỉ lệ** (lý do từng ô ở `index.json`, trường `ratio_fit`): 16:9 adaptable/medium · 9:16 requires_redesign/high · 1:1 preferred/low.

## Prompt HyperFrames viết mới

> Brief do kho tự viết, không phải prompt gốc ([quyền dùng](../USAGE.md#prompt-và-quyền-sử-dụng)).

Dựng một motion graphic mới tham chiếu ý tưởng “Photo print app launch film” (https://prompt-motion.com/twoclipping-221cab) cho vai trò explain/proof/cta. Chọn canvas 1:1 làm điểm xuất phát, thời lượng cảnh trong khoảng 6–12 giây rồi chốt theo lượng nội dung thực. Một ý chính, sức chứa 1 tác vụ; 1–3 trạng thái UI; 1 tiêu đề ngắn. Thay toàn bộ brand, copy, số liệu và media bằng dữ kiện được dự án cấp hoặc xác minh.

Thiết kế cụ thể: Đề xuất theo một ảnh duy nhất qua lưới ảnh, điện thoại, thao tác đặt in và khung ảnh trên tường. Shared rectangle của ảnh là cầu nối; giữ aspect ảnh và thay đổi môi trường bao quanh, không đổi ảnh giữa cut.

Nhịp dựng đề xuất:

1. Một ô trong gallery được chọn và nâng lên thành màn hình điện thoại.
2. Ảnh trượt vào thẻ đơn đặt hàng rồi ra mép giấy như một bản in.
3. Bản in đặt vào khung trên tường; camera dừng để đọc lợi ích.

Giữ khung cuối tối thiểu 0,8 giây sau chuyển động cuối để đọc. Bố cục partial; đặt chủ thể trong hộp đề xuất ở trên rồi kiểm theo canvas thật. DOM/SVG + GSAP; ảnh chụp có quyền chỉ dùng làm panel. Không cần Canvas cho nút, thẻ hay text.

Hợp đồng dựng, tái bố cục dọc/vuông, font/media và kiểm chứng: [USAGE.md](../USAGE.md#hợp-đồng-triển-khai-hyperframes).

## Liên quan / mức kiểm chứng

- [PM-twoclipping-5cba86 — Shape morphing through UI states](twoclipping-5cba86.md)
- [PM-twoclipping-d89be5 — Landing page 3D scroll](twoclipping-d89be5.md)
- [PM-gabrielbuzziv-4ff0c6 — Enxovaly baby app promo](gabrielbuzziv-4ff0c6.md)

Metadata HTML: **đã thu**. Public prompt: **đã đọc toàn bộ**. Xem toàn video: **chưa**. Source code test: **chưa**. HyperFrames check/render: **chưa**. Prompt/media nguồn: **không archive**, chưa xác lập bulk redistribution license. [Cách dùng](../USAGE.md) · [Taxonomy](../TAXONOMY.md).
