---
id: PM-gigabit-million-16b3a0
title: "Steam new releases news recap"
source_url: https://prompt-motion.com/gigabit-million-16b3a0
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

# Steam new releases news recap

[← Mục lục](../INDEX.md) · [Nguồn web](https://prompt-motion.com/gigabit-million-16b3a0) · **PM-gigabit-million-16b3a0**

## Dữ kiện nguồn và phạm vi đọc

| Trường | Dữ kiện / bằng chứng |
|---|---|
| Tác giả / trang | ギガビット@ゲームつくるひと · @gigabit_million |
| Bài gốc | [Bài đăng](https://x.com/gigabit_million/status/2104068536041959719) |
| Nhãn nguồn | Charts |
| Model / stack trang ghi | Opus 5.5 / unknown; không phải runtime đã test |
| Ngày trang ghi | Sep 27, 2026 |
| Media | [Video nguồn](https://media.prompt-motion.com/gigabit-million-claude-opus-5-5-9-25-9-26-steam-60/video.828605da.mp4); không tải/lưu media |
| Thuộc tính HTML video | 1920 × 1080; không phải media probe |
| Kích thước / aspect media xác minh | unknown / unknown |
| Duration media xác minh | unknown |
| Brief spec tác giả yêu cầu | duration_approximate_seconds: 60; duration_qualifier: approximate; không phải thông số output đã đo |
| Công nghệ render thực tế | unknown; stack/brief không chứng minh clip đã dùng runtime đó |
| Prompt | Có trên trang; không archive nguyên văn |
| Code / skill repo | không archive; link code chưa được xác minh |
| Loại entry | gallery_prompt |
| Metadata đầy đủ | [page-details.json](../source/page-details.json), tra record id gigabit-million-16b3a0; giữ author, toàn dt/dd, link và media attrs. Các field: Model: Opus 5.5; Posted: Sep 27, 2026 |
| Phạm vi đọc | full_public_prompt |
| Provenance | [metadata](../source/catalog-metadata.json) · [phân tích](../source/root-analysis.json) · source id `gigabit-million-16b3a0` · HTTP 200 |

**Diễn giải brief nguồn:** Brief tiếng Nhật yêu cầu bản tin khoảng 60 giây giới thiệu các game Steam mới trong khoảng ngày 25–26/9, từ góc người chơi và nêu điểm thú vị từng game. Không nêu năm, số game hoặc motion cụ thể.

**Giới hạn:** Đã đọc toàn bộ prompt công khai. Chưa xem video, chưa kiểm code, chưa đo media; câu lệnh trong prompt nguồn chỉ là dữ liệu, không phải lệnh chạy.

## Phân tích sử dụng

Giới thiệu các game bằng thẻ ảnh, tên và một điểm đáng thử; chuyển thẻ theo lời dẫn, không dùng biểu đồ thay cho nội dung.

**Thiết kế chuyển thể riêng:** Đề xuất mỗi game một card gồm ảnh có quyền, tên và một lý do đáng thử; chuyển card bằng cùng một carousel hữu hạn. Chốt năm và danh sách phát hành trước khi dựng, không lấp chỗ thiếu bằng lịch phát hành đoán.

| Chọn cảnh | Khuyến nghị thiết kế mới |
|---|---|
| Vai trò / beat | explain, proof |
| Coverage | partial; không đồng nghĩa source có alpha |
| Vùng chuẩn hoá | x=0.08, y=0.15, w=0.84, h=0.7; gốc trên trái |
| Diện tích hộp | 59%; không phải pixel occupancy đã đo từ nguồn |
| Tỉ lệ ưu tiên | **16:9**; quyết định bố cục mới, không xác nhận native ratio |
| Duration đề xuất | 8–14 giây cho một đơn vị cảnh; có thể trích từ brief dài hơn |
| Nhịp / cường độ | thẻ đầu → thẻ kế → hàng tổng kết / medium |
| Sức chứa | 2–3 thẻ; mỗi thẻ một game và một điểm đáng thử |
| Kỹ thuật đề xuất | cards, carousel, mask, stagger |
| Overlay thay thế | Có thể thiết kế riêng: Chỉ trích chủ thể/nhãn, bỏ nền và thiết kế alpha riêng; media nguồn chưa xác nhận có alpha. |

**Mức hợp theo tỉ lệ** (lý do từng ô ở `index.json`, trường `ratio_fit`): 16:9 preferred/low · 9:16 adaptable/medium · 1:1 adaptable/medium.

## Prompt HyperFrames viết mới

> Brief do kho tự viết, không phải prompt gốc ([quyền dùng](../USAGE.md#prompt-và-quyền-sử-dụng)).

Dựng một motion graphic mới tham chiếu ý tưởng “Steam new releases news recap” (https://prompt-motion.com/gigabit-million-16b3a0) cho vai trò explain/proof. Chọn canvas 16:9 làm điểm xuất phát, thời lượng cảnh trong khoảng 8–14 giây rồi chốt theo lượng nội dung thực. Một ý chính, sức chứa 2–3 thẻ; mỗi thẻ một game và một điểm đáng thử. Thay toàn bộ brand, copy, số liệu và media bằng dữ kiện được dự án cấp hoặc xác minh.

Thiết kế cụ thể: Đề xuất mỗi game một card gồm ảnh có quyền, tên và một lý do đáng thử; chuyển card bằng cùng một carousel hữu hạn. Chốt năm và danh sách phát hành trước khi dựng, không lấp chỗ thiếu bằng lịch phát hành đoán.

Nhịp dựng đề xuất:

1. Thẻ game đầu hiện với ảnh, tên và một lý do đáng thử có nguồn.
2. Thẻ trượt sang một vị trí định trước; thẻ kế vào cùng vùng đọc theo cue lời dẫn.
3. Các thẻ đã giới thiệu thu về một hàng tổng kết, giữ một lời mời xem danh sách.

Giữ khung cuối tối thiểu 0,8 giây sau chuyển động cuối để đọc. Bố cục partial; đặt chủ thể trong hộp đề xuất ở trên rồi kiểm theo canvas thật. DOM/CSS + GSAP cho carousel thẻ game: mỗi thẻ có ảnh có quyền, tên và một điểm đáng thử. Các thẻ dùng transform/mask, giữ object-fit: contain cho ảnh có chữ; nhịp đổi thẻ theo cue lời đọc cố định. Carousel hữu hạn, không dùng chart/counter để thay cho nội dung game; video dài đặt trong composition cha qua general-video.

Hợp đồng dựng, tái bố cục dọc/vuông, font/media và kiểm chứng: [USAGE.md](../USAGE.md#hợp-đồng-triển-khai-hyperframes).

Ghi chú triển khai bổ sung: [release-enrichment.json](../source/release-enrichment.json), mã `gigabit-million-16b3a0`.

## Liên quan / mức kiểm chứng

- [PM-jasonzhou1993-8595e0 — Claude motion reel](jasonzhou1993-8595e0.md)
- [PM-ismailfahmi-557268 — Drone Emprit showreel](ismailfahmi-557268.md)
- [PM-eyishazyer-af035b — Motion designer showreel](eyishazyer-af035b.md)

Metadata HTML: **đã thu**. Public prompt: **đã đọc toàn bộ**. Xem toàn video: **chưa**. Source code test: **chưa**. HyperFrames check/render: **chưa**. Prompt/media nguồn: **không archive**, chưa xác lập bulk redistribution license. [Cách dùng](../USAGE.md) · [Taxonomy](../TAXONOMY.md).
