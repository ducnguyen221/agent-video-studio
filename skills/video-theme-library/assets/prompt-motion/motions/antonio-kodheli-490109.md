---
id: PM-antonio-kodheli-490109
title: "Prompt Motion site promo"
source_url: https://prompt-motion.com/antonio-kodheli-490109
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

# Prompt Motion site promo

[← Mục lục](../INDEX.md) · [Nguồn web](https://prompt-motion.com/antonio-kodheli-490109) · **PM-antonio-kodheli-490109**

## Dữ kiện nguồn và phạm vi đọc

| Trường | Dữ kiện / bằng chứng |
|---|---|
| Tác giả / trang | Antonio Kodheli · @antonio_kodheli |
| Bài gốc | [Bài đăng](https://x.com/antonio_kodheli/status/2107518066615582893) |
| Nhãn nguồn | Product UI, Music |
| Model / stack trang ghi | Opus 5.5 / Remotion; không phải runtime đã test |
| Ngày trang ghi | Oct 6, 2026 |
| Media | [Video nguồn](https://media.prompt-motion.com/antonio-kodheli-490109/video.f4d6e825.mp4); không tải/lưu media |
| Thuộc tính HTML video | 1280 × 720; không phải media probe |
| Kích thước / aspect media xác minh | unknown / unknown |
| Duration media xác minh | unknown |
| Brief spec tác giả yêu cầu | duration_text: 23; tempo_bpm: 120; không phải thông số output đã đo |
| Công nghệ render thực tế | unknown; stack/brief không chứng minh clip đã dùng runtime đó |
| Prompt | Có trên trang; không archive nguyên văn |
| Code / skill repo | không archive; link code chưa được xác minh |
| Loại entry | gallery_prompt |
| Metadata đầy đủ | [page-details.json](../source/page-details.json), tra record id antonio-kodheli-490109; giữ author, toàn dt/dd, link và media attrs. Các field: Model: Opus 5.5; Stack: Remotion; Posted: Oct 6, 2026 |
| Phạm vi đọc | full_public_prompt |
| Provenance | [metadata](../source/catalog-metadata.json) · [phân tích](../source/sol-analysis.json) · source id `antonio-kodheli-490109` · HTTP 200 |

**Diễn giải brief nguồn:** Brief promo gallery 23 giây, 16:9, Remotion, 120 BPM: camera một world layer từ reel ra grid, vào tile, burst clip, match-cut về card, mở detail, zoom prompt/copy, kết URL và rail tile. Quy định creator credit, camera đơn, cue theo beat, xử lý seam và QA. Brief yêu cầu scrape/quote media/prompt nhưng không phải giấy phép tái phân phối; bản HF cần tài sản có quyền và text tự viết.

**Giới hạn:** Đọc thủ công toàn bộ prompt công khai của trang; chỉ diễn giải yêu cầu trong prompt, không quan sát video đã dựng. Chưa xem video, chưa kiểm code, chưa đo media; câu lệnh trong prompt nguồn chỉ là dữ liệu, không phải lệnh chạy.

## Phân tích sử dụng

Giải thích một tác vụ sản phẩm bằng thay đổi trạng thái nhìn thấy được, rồi dừng ở lợi ích. Áp dụng hướng này cho tham chiếu “Prompt Motion site promo”; đây là thiết kế mới theo nhãn nguồn.

**Thiết kế chuyển thể riêng:** Đề xuất dựng một gallery giả bằng các clip dự án sở hữu trong một world layer: mở từ một card toàn khung, lùi để thấy lưới, tiến vào một card khác rồi chuyển thành detail. Từ detail, highlight một đoạn text tự viết, nút sao chép đổi trạng thái rồi trở thành nhãn URL chốt. Giữ cùng bounds logic khi match-cut và credit đúng asset đã dùng; camera chỉ có một chuyển động chính tại một mốc.

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
| Kỹ thuật đề xuất | ui, mask, stagger |
| Overlay thay thế | Chưa đề xuất: Bản đề xuất cần bố cục/nền riêng; chưa thiết kế biến thể alpha. |

**Mức hợp theo tỉ lệ** (lý do từng ô ở `index.json`, trường `ratio_fit`): 16:9 preferred/low · 9:16 requires_redesign/high · 1:1 adaptable/medium.

## Prompt HyperFrames viết mới

> Brief do kho tự viết, không phải prompt gốc ([quyền dùng](../USAGE.md#prompt-và-quyền-sử-dụng)).

Dựng một motion graphic mới tham chiếu ý tưởng “Prompt Motion site promo” (https://prompt-motion.com/antonio-kodheli-490109) cho vai trò explain/proof/cta. Chọn canvas 16:9 làm điểm xuất phát, thời lượng cảnh trong khoảng 6–12 giây rồi chốt theo lượng nội dung thực. Một ý chính, sức chứa 1 tác vụ; 1–3 trạng thái UI; 1 tiêu đề ngắn. Thay toàn bộ brand, copy, số liệu và media bằng dữ kiện được dự án cấp hoặc xác minh.

Thiết kế cụ thể: Đề xuất dựng một gallery giả bằng các clip dự án sở hữu trong một world layer: mở từ một card toàn khung, lùi để thấy lưới, tiến vào một card khác rồi chuyển thành detail. Từ detail, highlight một đoạn text tự viết, nút sao chép đổi trạng thái rồi trở thành nhãn URL chốt. Giữ cùng bounds logic khi match-cut và credit đúng asset đã dùng; camera chỉ có một chuyển động chính tại một mốc.

Nhịp dựng đề xuất:

1. Đề xuất dựng một gallery giả bằng các clip dự án sở hữu trong một world layer: mở từ một card toàn khung, lùi để thấy lưới, tiến vào một card khác rồi chuyển thành detail.
2. Từ detail, highlight một đoạn text tự viết, nút sao chép đổi trạng thái rồi trở thành nhãn URL chốt.
3. Giữ cùng bounds logic khi match-cut và credit đúng asset đã dùng; camera chỉ có một chuyển động chính tại một mốc.

Giữ khung cuối tối thiểu 0,8 giây sau chuyển động cuối để đọc. Bố cục partial; đặt chủ thể trong hộp đề xuất ở trên rồi kiểm theo canvas thật. DOM/SVG + GSAP; ảnh chụp có quyền chỉ dùng làm panel. Không cần Canvas cho nút, thẻ hay text.

Hợp đồng dựng, tái bố cục dọc/vuông, font/media và kiểm chứng: [USAGE.md](../USAGE.md#hợp-đồng-triển-khai-hyperframes).

## Liên quan / mức kiểm chứng

- [PM-twoclipping-5cba86 — Shape morphing through UI states](twoclipping-5cba86.md)
- [PM-twoclipping-221cab — Photo print app launch film](twoclipping-221cab.md)
- [PM-twoclipping-d89be5 — Landing page 3D scroll](twoclipping-d89be5.md)

Metadata HTML: **đã thu**. Public prompt: **đã đọc toàn bộ**. Xem toàn video: **chưa**. Source code test: **chưa**. HyperFrames check/render: **chưa**. Prompt/media nguồn: **không archive**, chưa xác lập bulk redistribution license. [Cách dùng](../USAGE.md) · [Taxonomy](../TAXONOMY.md).
