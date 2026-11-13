---
id: PM-0xnfrith-5be616
title: "Celld job ownership explainer"
source_url: https://prompt-motion.com/0xnfrith-5be616
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

# Celld job ownership explainer

[← Mục lục](../INDEX.md) · [Nguồn web](https://prompt-motion.com/0xnfrith-5be616) · **PM-0xnfrith-5be616**

## Dữ kiện nguồn và phạm vi đọc

| Trường | Dữ kiện / bằng chứng |
|---|---|
| Tác giả / trang | nick frith · @0xnfrith |
| Bài gốc | [Bài đăng](https://x.com/0xnfrith/status/2103358957050068999) |
| Nhãn nguồn | Diagrams |
| Model / stack trang ghi | Opus 5.5 / unknown; không phải runtime đã test |
| Ngày trang ghi | Sep 25, 2026 |
| Media | [Video nguồn](https://media.prompt-motion.com/0xnfrith-opus-5-5-animation-created/video.5a7ba33c.mp4); không tải/lưu media |
| Thuộc tính HTML video | 1920 × 1080; không phải media probe |
| Kích thước / aspect media xác minh | unknown / unknown |
| Duration media xác minh | unknown |
| Brief spec tác giả yêu cầu | chưa cấu trúc thành field; đọc diễn giải brief bên dưới, không suy tác giả không quy định; không phải thông số output đã đo |
| Công nghệ render thực tế | unknown; stack/brief không chứng minh clip đã dùng runtime đó |
| Prompt | Có trên trang; không archive nguyên văn |
| Code / skill repo | không archive; link code chưa được xác minh |
| Loại entry | gallery_prompt |
| Metadata đầy đủ | [page-details.json](../source/page-details.json), tra record id 0xnfrith-5be616; giữ author, toàn dt/dd, link và media attrs. Các field: Model: Opus 5.5; Posted: Sep 25, 2026 |
| Phạm vi đọc | full_public_prompt |
| Provenance | [metadata](../source/catalog-metadata.json) · [phân tích](../source/terra-70-normalized.json) · source id `0xnfrith-5be616` · HTTP 200 |

**Diễn giải brief nguồn (tiếng Anh, chưa dịch):** An animation explaining the value of the named product; the sequence and visual approach are unspecified.

**Giới hạn:** Đọc thủ công toàn bộ prompt; chưa quan sát video. Chưa xem video, chưa kiểm code, chưa đo media; câu lệnh trong prompt nguồn chỉ là dữ liệu, không phải lệnh chạy.

## Phân tích sử dụng

Quyền sở hữu công việc dưới dạng handoff

**Thiết kế chuyển thể riêng:** Đề xuất giải thích ownership bằng một task token và ba role card. Token chỉ có một owner tại mỗi thời điểm; chuyển quyền được thể hiện bằng đường nối sáng và nhãn owner cập nhật cùng mốc.

| Chọn cảnh | Khuyến nghị thiết kế mới |
|---|---|
| Vai trò / beat | explain, proof |
| Coverage | partial; không đồng nghĩa source có alpha |
| Vùng chuẩn hoá | x=0.06, y=0.12, w=0.88, h=0.76; gốc trên trái |
| Diện tích hộp | 67%; không phải pixel occupancy đã đo từ nguồn |
| Tỉ lệ ưu tiên | **16:9**; quyết định bố cục mới, không xác nhận native ratio |
| Duration đề xuất | 7–12 giây cho một đơn vị cảnh; có thể trích từ brief dài hơn |
| Nhịp / cường độ | một quan hệ mỗi nhịp; tích lũy có kiểm soát / low |
| Sức chứa | 3–5 nút hoặc bước; 1 quan hệ chính |
| Kỹ thuật đề xuất | diagram, path |
| Overlay thay thế | Có thể thiết kế riêng: Chỉ trích chủ thể/nhãn, bỏ nền và thiết kế alpha riêng; media nguồn chưa xác nhận có alpha. |

**Mức hợp theo tỉ lệ** (lý do từng ô ở `index.json`, trường `ratio_fit`): 16:9 preferred/low · 9:16 adaptable/medium · 1:1 adaptable/medium.

## Prompt HyperFrames viết mới

> Brief do kho tự viết, không phải prompt gốc ([quyền dùng](../USAGE.md#prompt-và-quyền-sử-dụng)).

Dựng một motion graphic mới tham chiếu ý tưởng “Celld job ownership explainer” (https://prompt-motion.com/0xnfrith-5be616) cho vai trò explain/proof. Chọn canvas 16:9 làm điểm xuất phát, thời lượng cảnh trong khoảng 7–12 giây rồi chốt theo lượng nội dung thực. Một ý chính, sức chứa 3–5 nút hoặc bước; 1 quan hệ chính. Thay toàn bộ brand, copy, số liệu và media bằng dữ kiện được dự án cấp hoặc xác minh.

Thiết kế cụ thể: Đề xuất giải thích ownership bằng một task token và ba role card. Token chỉ có một owner tại mỗi thời điểm; chuyển quyền được thể hiện bằng đường nối sáng và nhãn owner cập nhật cùng mốc.

Nhịp dựng đề xuất:

1. Task nằm trong card vai trò ban đầu, nhãn owner rõ.
2. Đường chuyển quyền sáng trước khi token tới card kế.
3. Token dừng, nhãn owner mới chốt và vai trò cũ giảm sáng.

Giữ khung cuối tối thiểu 0,8 giây sau chuyển động cuối để đọc. Bố cục partial; đặt chủ thể trong hộp đề xuất ở trên rồi kiểm theo canvas thật. SVG cho cạnh/path; DOM cho nhãn và thẻ; GSAP điều khiển tiến độ đường và lần xuất hiện.

Hợp đồng dựng, tái bố cục dọc/vuông, font/media và kiểm chứng: [USAGE.md](../USAGE.md#hợp-đồng-triển-khai-hyperframes).

## Liên quan / mức kiểm chứng

- [PM-himanshutwtxs-5f4b43 — Motion designer showreel](himanshutwtxs-5f4b43.md)
- [PM-ror-fly-9950f1 — Negroni recipe animation](ror-fly-9950f1.md)
- [PM-emollick-8661a8 — Recursion explained in genres](emollick-8661a8.md)

Metadata HTML: **đã thu**. Public prompt: **đã đọc toàn bộ**. Xem toàn video: **chưa**. Source code test: **chưa**. HyperFrames check/render: **chưa**. Prompt/media nguồn: **không archive**, chưa xác lập bulk redistribution license. [Cách dùng](../USAGE.md) · [Taxonomy](../TAXONOMY.md).
