---
id: PM-twoclipping-d89be5
title: "Landing page 3D scroll"
source_url: https://prompt-motion.com/twoclipping-d89be5
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

# Landing page 3D scroll

[← Mục lục](../INDEX.md) · [Nguồn web](https://prompt-motion.com/twoclipping-d89be5) · **PM-twoclipping-d89be5**

## Dữ kiện nguồn và phạm vi đọc

| Trường | Dữ kiện / bằng chứng |
|---|---|
| Tác giả / trang | zero · @twoclipping |
| Bài gốc | [Bài đăng](https://x.com/twoclipping/status/2110329502676951367) |
| Nhãn nguồn | Product UI, Kinetic type |
| Model / stack trang ghi | Opus 5.5 / WebGL2 + Playwright; không phải runtime đã test |
| Ngày trang ghi | Oct 14, 2026 |
| Media | [Video nguồn](https://media.prompt-motion.com/twoclipping-d89be5/video.c1c2a37f.mp4); không tải/lưu media |
| Thuộc tính HTML video | 1440 × 1152; không phải media probe |
| Kích thước / aspect media xác minh | unknown / unknown |
| Duration media xác minh | unknown |
| Brief spec tác giả yêu cầu | chưa cấu trúc thành field; đọc diễn giải brief bên dưới, không suy tác giả không quy định; không phải thông số output đã đo |
| Công nghệ render thực tế | unknown; stack/brief không chứng minh clip đã dùng runtime đó |
| Prompt | Có trên trang; không archive nguyên văn |
| Code / skill repo | không archive; link code chưa được xác minh |
| Loại entry | gallery_prompt |
| Metadata đầy đủ | [page-details.json](../source/page-details.json), tra record id twoclipping-d89be5; giữ author, toàn dt/dd, link và media attrs. Các field: Model: Opus 5.5; Stack: WebGL2 + Playwright; Posted: Oct 14, 2026 |
| Phạm vi đọc | full_public_prompt |
| Provenance | [metadata](../source/catalog-metadata.json) · [phân tích](../source/terra-70-normalized.json) · source id `twoclipping-d89be5` · HTTP 200 |

**Diễn giải brief nguồn (tiếng Anh, chưa dịch):** A camera glides over a captured landing page, rises overhead, dives into the hero and settles on a title card. The requested build layers captured webpage elements in WebGL2 with depth, time-seeking and frame previews.

**Giới hạn:** Đọc thủ công toàn bộ prompt; chưa quan sát video. Chưa xem video, chưa kiểm code, chưa đo media; câu lệnh trong prompt nguồn chỉ là dữ liệu, không phải lệnh chạy.

## Phân tích sử dụng

Cuộn web như camera kể chuyện

**Thiết kế chuyển thể riêng:** Đề xuất một camera có ba đoạn đường rõ trên các lớp của landing page đã được cấp quyền: lướt sát, nâng lên nhìn tổng thể, rồi dive tới hero. Tách UI thành plane có độ sâu; video không nhận sự kiện scroll thật.

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
| Kỹ thuật đề xuất | camera, ui, 3d |
| Overlay thay thế | Chưa đề xuất: Bản đề xuất cần bố cục/nền riêng; chưa thiết kế biến thể alpha. |

**Mức hợp theo tỉ lệ** (lý do từng ô ở `index.json`, trường `ratio_fit`): 16:9 preferred/low · 9:16 requires_redesign/high · 1:1 adaptable/medium.

## Prompt HyperFrames viết mới

> Brief do kho tự viết, không phải prompt gốc ([quyền dùng](../USAGE.md#prompt-và-quyền-sử-dụng)).

Dựng một motion graphic mới tham chiếu ý tưởng “Landing page 3D scroll” (https://prompt-motion.com/twoclipping-d89be5) cho vai trò explain/proof/cta. Chọn canvas 16:9 làm điểm xuất phát, thời lượng cảnh trong khoảng 6–12 giây rồi chốt theo lượng nội dung thực. Một ý chính, sức chứa 1 tác vụ; 1–3 trạng thái UI; 1 tiêu đề ngắn. Thay toàn bộ brand, copy, số liệu và media bằng dữ kiện được dự án cấp hoặc xác minh.

Thiết kế cụ thể: Đề xuất một camera có ba đoạn đường rõ trên các lớp của landing page đã được cấp quyền: lướt sát, nâng lên nhìn tổng thể, rồi dive tới hero. Tách UI thành plane có độ sâu; video không nhận sự kiện scroll thật.

Nhịp dựng đề xuất:

1. Camera lướt ngang thấp qua vài chi tiết UI đọc được.
2. Nâng góc nhìn để lộ cấu trúc trang, giữ hero là điểm định hướng.
3. Tiến vào hero rồi hạ perspective thành title card phẳng.

Giữ khung cuối tối thiểu 0,8 giây sau chuyển động cuối để đọc. Bố cục partial; đặt chủ thể trong hộp đề xuất ở trên rồi kiểm theo canvas thật. Three.js/WebGL cho camera, vật thể và quan hệ không gian 3D thật của đề xuất này. Timeline GSAP paused điều khiển mọi pose, một callback render trực tiếp tại time tuyệt đối; không physics tích lũy, rAF tự chạy hoặc input tương tác. Ghim dependency cục bộ và dùng model/texture có quyền. Đây là adapter đề xuất, chưa test runtime.

Hợp đồng dựng, tái bố cục dọc/vuông, font/media và kiểm chứng: [USAGE.md](../USAGE.md#hợp-đồng-triển-khai-hyperframes).

## Liên quan / mức kiểm chứng

- [PM-twoclipping-5cba86 — Shape morphing through UI states](twoclipping-5cba86.md)
- [PM-twoclipping-221cab — Photo print app launch film](twoclipping-221cab.md)
- [PM-gabrielbuzziv-4ff0c6 — Enxovaly baby app promo](gabrielbuzziv-4ff0c6.md)

Metadata HTML: **đã thu**. Public prompt: **đã đọc toàn bộ**. Xem toàn video: **chưa**. Source code test: **chưa**. HyperFrames check/render: **chưa**. Prompt/media nguồn: **không archive**, chưa xác lập bulk redistribution license. [Cách dùng](../USAGE.md) · [Taxonomy](../TAXONOMY.md).
