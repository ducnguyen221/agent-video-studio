---
id: PM-tdinh-me-815acb
title: "TypingMind logo reveal"
source_url: https://prompt-motion.com/tdinh-me-815acb
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

# TypingMind logo reveal

[← Mục lục](../INDEX.md) · [Nguồn web](https://prompt-motion.com/tdinh-me-815acb) · **PM-tdinh-me-815acb**

## Dữ kiện nguồn và phạm vi đọc

| Trường | Dữ kiện / bằng chứng |
|---|---|
| Tác giả / trang | Tony Dinh · @tdinh_me |
| Bài gốc | [Bài đăng](https://x.com/tdinh_me/status/2103704250329301409) |
| Nhãn nguồn | Shapes |
| Model / stack trang ghi | Opus 5.5 / unknown; không phải runtime đã test |
| Ngày trang ghi | Sep 26, 2026 |
| Media | [Video nguồn](https://media.prompt-motion.com/tdinh-me-use-this-prompt-and/video.f19334df.mp4); không tải/lưu media |
| Thuộc tính HTML video | 1920 × 1080; không phải media probe |
| Kích thước / aspect media xác minh | unknown / unknown |
| Duration media xác minh | unknown |
| Brief spec tác giả yêu cầu | chưa cấu trúc thành field; đọc diễn giải brief bên dưới, không suy tác giả không quy định; không phải thông số output đã đo |
| Công nghệ render thực tế | unknown; stack/brief không chứng minh clip đã dùng runtime đó |
| Prompt | Có trên trang; không archive nguyên văn |
| Code / skill repo | không archive; link code chưa được xác minh |
| Loại entry | gallery_prompt |
| Metadata đầy đủ | [page-details.json](../source/page-details.json), tra record id tdinh-me-815acb; giữ author, toàn dt/dd, link và media attrs. Các field: Model: Opus 5.5; Posted: Sep 26, 2026 |
| Phạm vi đọc | full_public_prompt |
| Provenance | [metadata](../source/catalog-metadata.json) · [phân tích](../source/terra-70-normalized.json) · source id `tdinh-me-815acb` · HTTP 200 |

**Diễn giải brief nguồn (tiếng Anh, chưa dịch):** A slow reveal assembles the named product logo; further sequence and technique are unspecified.

**Giới hạn:** Đọc thủ công toàn bộ prompt; chưa quan sát video. Chưa xem video, chưa kiểm code, chưa đo media; câu lệnh trong prompt nguồn chỉ là dữ liệu, không phải lệnh chạy.

## Phân tích sử dụng

Logo được khám phá bằng hình học

**Thiết kế chuyển thể riêng:** Đề xuất reveal chậm dựa trên đường bao logo do dự án cấp. Dùng một stroke chạy theo contour rồi tăng phần tô; logo không méo thành hình khác trong đoạn cần nhận diện.

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
| Kỹ thuật đề xuất | shape, mask |
| Overlay thay thế | Chưa đề xuất: Bản đề xuất cần bố cục/nền riêng; chưa thiết kế biến thể alpha. |

**Mức hợp theo tỉ lệ** (lý do từng ô ở `index.json`, trường `ratio_fit`): 16:9 preferred/low · 9:16 adaptable/medium · 1:1 adaptable/medium.

## Prompt HyperFrames viết mới

> Brief do kho tự viết, không phải prompt gốc ([quyền dùng](../USAGE.md#prompt-và-quyền-sử-dụng)).

Dựng một motion graphic mới tham chiếu ý tưởng “TypingMind logo reveal” (https://prompt-motion.com/tdinh-me-815acb) cho vai trò hook/transition/emphasis. Chọn canvas 16:9 làm điểm xuất phát, thời lượng cảnh trong khoảng 3–6 giây rồi chốt theo lượng nội dung thực. Một ý chính, sức chứa 1 hình chủ đạo, 2–4 hình phụ; tối đa 1 nhãn. Thay toàn bộ brand, copy, số liệu và media bằng dữ kiện được dự án cấp hoặc xác minh.

Thiết kế cụ thể: Đề xuất reveal chậm dựa trên đường bao logo do dự án cấp. Dùng một stroke chạy theo contour rồi tăng phần tô; logo không méo thành hình khác trong đoạn cần nhận diện.

Nhịp dựng đề xuất:

1. Một đoạn contour nhỏ dẫn mắt tới đặc điểm nhận dạng.
2. Stroke hoàn thành đường bao, các mảng tô xuất hiện có lệch nhịp nhẹ.
3. Wordmark đặt cạnh mark, giữ khoảng cách và dừng.

Giữ khung cuối tối thiểu 0,8 giây sau chuyển động cuối để đọc. Bố cục fullscreen; đặt chủ thể trong hộp đề xuất ở trên rồi kiểm theo canvas thật. SVG/DOM + GSAP cho số lượng hình nhỏ. Nếu morph path, giữ cấu trúc điểm tương thích hoặc dùng crossfade có chủ đích.

Hợp đồng dựng, tái bố cục dọc/vuông, font/media và kiểm chứng: [USAGE.md](../USAGE.md#hợp-đồng-triển-khai-hyperframes).

## Liên quan / mức kiểm chứng

- [PM-monokern-ade5b6 — Psychedelic hypnotic eye showreel](monokern-ade5b6.md)
- [PM-kantamk-61f410 — Ball escaping twelve rings](kantamk-61f410.md)

Metadata HTML: **đã thu**. Public prompt: **đã đọc toàn bộ**. Xem toàn video: **chưa**. Source code test: **chưa**. HyperFrames check/render: **chưa**. Prompt/media nguồn: **không archive**, chưa xác lập bulk redistribution license. [Cách dùng](../USAGE.md) · [Taxonomy](../TAXONOMY.md).
