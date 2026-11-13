---
id: PM-pankajstwt-49978ed
title: "Voice agent landing page"
source_url: https://prompt-motion.com/pankajstwt-49978ed
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

# Voice agent landing page

[← Mục lục](../INDEX.md) · [Nguồn web](https://prompt-motion.com/pankajstwt-49978ed) · **PM-pankajstwt-49978ed**

## Dữ kiện nguồn và phạm vi đọc

| Trường | Dữ kiện / bằng chứng |
|---|---|
| Tác giả / trang | Pankaj · @pankajstwt |
| Bài gốc | [Bài đăng](https://x.com/pankajstwt/status/2112540104896241791) |
| Nhãn nguồn | Product UI, Music |
| Model / stack trang ghi | Opus 5.5 / WebGL2; không phải runtime đã test |
| Ngày trang ghi | Oct 20, 2026 |
| Media | [Video nguồn](https://media.prompt-motion.com/pankajstwt-49978ed/video.1313695c.mp4); không tải/lưu media |
| Thuộc tính HTML video | 1440 × 1152; không phải media probe |
| Kích thước / aspect media xác minh | unknown / unknown |
| Duration media xác minh | unknown |
| Brief spec tác giả yêu cầu | duration_seconds: 14.5; fps: 60; không phải thông số output đã đo |
| Công nghệ render thực tế | unknown; stack/brief không chứng minh clip đã dùng runtime đó |
| Prompt | Có trên trang; không archive nguyên văn |
| Code / skill repo | không archive; link code chưa được xác minh |
| Loại entry | gallery_prompt |
| Metadata đầy đủ | [page-details.json](../source/page-details.json), tra record id pankajstwt-49978ed; giữ author, toàn dt/dd, link và media attrs. Các field: Model: Opus 5.5; Stack: WebGL2; Posted: Oct 20, 2026 |
| Phạm vi đọc | full_public_prompt |
| Provenance | [metadata](../source/catalog-metadata.json) · [phân tích](../source/terra-70-normalized.json) · source id `pankajstwt-49978ed` · HTTP 200 |

**Diễn giải brief nguồn (tiếng Anh, chưa dịch):** A 14.5-second camera move glides over a landing page, rises overhead, dives back to the hero and ends on a branded card. The brief requests webpage capture, WebGL2 depth, time-seekable motion, 60fps output and approval of stills before render.

**Giới hạn:** Đọc thủ công toàn bộ prompt; chưa quan sát video. Chưa xem video, chưa kiểm code, chưa đo media; câu lệnh trong prompt nguồn chỉ là dữ liệu, không phải lệnh chạy.

## Phân tích sử dụng

Giải thích một tác vụ sản phẩm bằng thay đổi trạng thái nhìn thấy được, rồi dừng ở lợi ích. Áp dụng hướng này cho tham chiếu “Voice agent landing page”; đây là thiết kế mới theo nhãn nguồn.

**Thiết kế chuyển thể riêng:** Đề xuất chia camera landing page thành low glide, overhead và hero dive, kết bằng một card nhận diện. Geometry/WebGL chỉ là phương án dựng cho các plane webpage; camera tiến theo đường time-derived và không điều khiển scroll thật.

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
| Kỹ thuật đề xuất | ui, mask, stagger, 3d, camera |
| Overlay thay thế | Chưa đề xuất: Bản đề xuất cần bố cục/nền riêng; chưa thiết kế biến thể alpha. |

**Mức hợp theo tỉ lệ** (lý do từng ô ở `index.json`, trường `ratio_fit`): 16:9 preferred/low · 9:16 requires_redesign/high · 1:1 adaptable/medium.

## Prompt HyperFrames viết mới

> Brief do kho tự viết, không phải prompt gốc ([quyền dùng](../USAGE.md#prompt-và-quyền-sử-dụng)).

Dựng một motion graphic mới tham chiếu ý tưởng “Voice agent landing page” (https://prompt-motion.com/pankajstwt-49978ed) cho vai trò explain/proof/cta. Chọn canvas 16:9 làm điểm xuất phát, thời lượng cảnh trong khoảng 6–12 giây rồi chốt theo lượng nội dung thực. Một ý chính, sức chứa 1 tác vụ; 1–3 trạng thái UI; 1 tiêu đề ngắn. Thay toàn bộ brand, copy, số liệu và media bằng dữ kiện được dự án cấp hoặc xác minh.

Thiết kế cụ thể: Đề xuất chia camera landing page thành low glide, overhead và hero dive, kết bằng một card nhận diện. Geometry/WebGL chỉ là phương án dựng cho các plane webpage; camera tiến theo đường time-derived và không điều khiển scroll thật.

Nhịp dựng đề xuất:

1. Lướt sát dọc các chi tiết của trang, hero luôn có marker thị giác.
2. Camera lên cao để thấy bố cục rồi đổi góc nhìn hướng về hero.
3. Dive có giảm tốc vào hero; perspective dần về mặt phẳng cuối để đọc tên.

Giữ khung cuối tối thiểu 0,8 giây sau chuyển động cuối để đọc. Bố cục partial; đặt chủ thể trong hộp đề xuất ở trên rồi kiểm theo canvas thật. Three.js/WebGL cho camera, vật thể và quan hệ không gian 3D thật của đề xuất này. Timeline GSAP paused điều khiển mọi pose, một callback render trực tiếp tại time tuyệt đối; không physics tích lũy, rAF tự chạy hoặc input tương tác. Ghim dependency cục bộ và dùng model/texture có quyền. Đây là adapter đề xuất, chưa test runtime.

Hợp đồng dựng, tái bố cục dọc/vuông, font/media và kiểm chứng: [USAGE.md](../USAGE.md#hợp-đồng-triển-khai-hyperframes).

## Liên quan / mức kiểm chứng

- [PM-twoclipping-5cba86 — Shape morphing through UI states](twoclipping-5cba86.md)
- [PM-twoclipping-221cab — Photo print app launch film](twoclipping-221cab.md)
- [PM-twoclipping-d89be5 — Landing page 3D scroll](twoclipping-d89be5.md)

Metadata HTML: **đã thu**. Public prompt: **đã đọc toàn bộ**. Xem toàn video: **chưa**. Source code test: **chưa**. HyperFrames check/render: **chưa**. Prompt/media nguồn: **không archive**, chưa xác lập bulk redistribution license. [Cách dùng](../USAGE.md) · [Taxonomy](../TAXONOMY.md).
