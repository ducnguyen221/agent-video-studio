---
id: PM-sab8a-364a5a
title: "Talking-head clip edit"
source_url: https://prompt-motion.com/sab8a-364a5a
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

# Talking-head clip edit

[← Mục lục](../INDEX.md) · [Nguồn web](https://prompt-motion.com/sab8a-364a5a) · **PM-sab8a-364a5a**

## Dữ kiện nguồn và phạm vi đọc

| Trường | Dữ kiện / bằng chứng |
|---|---|
| Tác giả / trang | Sabba Keynejad · @sab8a |
| Bài gốc | [Bài đăng](https://x.com/sab8a/status/2103144778481475686) |
| Nhãn nguồn | Photos |
| Model / stack trang ghi | Opus 5.5 / OpenEdit; không phải runtime đã test |
| Ngày trang ghi | Sep 24, 2026 |
| Media | [Video nguồn](https://media.prompt-motion.com/sab8a-opus-5-5-openedit-prompt/video.f57b6670.mp4); không tải/lưu media |
| Thuộc tính HTML video | 1920 × 1080; không phải media probe |
| Kích thước / aspect media xác minh | unknown / unknown |
| Duration media xác minh | unknown |
| Brief spec tác giả yêu cầu | chưa cấu trúc thành field; đọc diễn giải brief bên dưới, không suy tác giả không quy định; không phải thông số output đã đo |
| Công nghệ render thực tế | unknown; stack/brief không chứng minh clip đã dùng runtime đó |
| Prompt | Có trên trang; không archive nguyên văn |
| Code / skill repo | không archive; link code chưa được xác minh |
| Loại entry | gallery_prompt |
| Metadata đầy đủ | [page-details.json](../source/page-details.json), tra record id sab8a-364a5a; giữ author, toàn dt/dd, link và media attrs. Các field: Model: Opus 5.5; Stack: OpenEdit; Posted: Sep 24, 2026 |
| Phạm vi đọc | full_public_prompt |
| Provenance | [metadata](../source/catalog-metadata.json) · [phân tích](../source/terra-70-normalized.json) · source id `sab8a-364a5a` · HTTP 200 |

**Diễn giải brief nguồn (tiếng Anh, chưa dịch):** Edit an existing talking-head clip with subtitles, graphic overlays and music; sequence and format are unspecified.

**Giới hạn:** Đọc thủ công toàn bộ prompt; chưa quan sát video. Chưa xem video, chưa kiểm code, chưa đo media; câu lệnh trong prompt nguồn chỉ là dữ liệu, không phải lệnh chạy.

## Phân tích sử dụng

Dùng ảnh làm bằng chứng hoặc bối cảnh, chuyển động giúp nhìn đúng chi tiết. Áp dụng hướng này cho tham chiếu “Talking-head clip edit”; đây là thiết kế mới theo nhãn nguồn.

**Thiết kế chuyển thể riêng:** Đề xuất graphic overlay cho talking-head: lower-third lúc giới thiệu, một keyword card tại ý chính và một callout giữ ngắn cạnh người nói. Footage là clip riêng; overlay không ép vào dạng photo pan.

| Chọn cảnh | Khuyến nghị thiết kế mới |
|---|---|
| Vai trò / beat | hook, proof, explain |
| Coverage | partial; không đồng nghĩa source có alpha |
| Vùng chuẩn hoá | x=0.08, y=0.1, w=0.84, h=0.76; gốc trên trái |
| Diện tích hộp | 64%; không phải pixel occupancy đã đo từ nguồn |
| Tỉ lệ ưu tiên | **16:9**; quyết định bố cục mới, không xác nhận native ratio |
| Duration đề xuất | 5–9 giây cho một đơn vị cảnh; có thể trích từ brief dài hơn |
| Nhịp / cường độ | giới thiệu ảnh → chọn chi tiết → giữ bằng chứng / low |
| Sức chứa | 1–2 ảnh có liên quan; 1 câu chú thích |
| Kỹ thuật đề xuất | image, mask, parallax |
| Overlay thay thế | Chưa đề xuất: Bản đề xuất cần bố cục/nền riêng; chưa thiết kế biến thể alpha. |

**Mức hợp theo tỉ lệ** (lý do từng ô ở `index.json`, trường `ratio_fit`): 16:9 preferred/low · 9:16 adaptable/medium · 1:1 adaptable/medium.

## Prompt HyperFrames viết mới

> Brief do kho tự viết, không phải prompt gốc ([quyền dùng](../USAGE.md#prompt-và-quyền-sử-dụng)).

Dựng một motion graphic mới tham chiếu ý tưởng “Talking-head clip edit” (https://prompt-motion.com/sab8a-364a5a) cho vai trò hook/proof/explain. Chọn canvas 16:9 làm điểm xuất phát, thời lượng cảnh trong khoảng 5–9 giây rồi chốt theo lượng nội dung thực. Một ý chính, sức chứa 1–2 ảnh có liên quan; 1 câu chú thích. Thay toàn bộ brand, copy, số liệu và media bằng dữ kiện được dự án cấp hoặc xác minh.

Thiết kế cụ thể: Đề xuất graphic overlay cho talking-head: lower-third lúc giới thiệu, một keyword card tại ý chính và một callout giữ ngắn cạnh người nói. Footage là clip riêng; overlay không ép vào dạng photo pan.

Nhịp dựng đề xuất:

1. Lower-third trượt vào vùng không che mặt rồi rời đi.
2. Keyword hiện đúng mốc lời nói cùng phụ đề.
3. Callout nhấn một bằng chứng, sau đó trả lại hình người nói sạch.

Giữ khung cuối tối thiểu 0,8 giây sau chuyển động cuối để đọc. Bố cục partial; đặt chủ thể trong hộp đề xuất ở trên rồi kiểm theo canvas thật. DOM img + GSAP; object-fit:contain cho screenshot và chữ trong ảnh. Không tự lấy video/ảnh của nguồn để nhúng.

Hợp đồng dựng, tái bố cục dọc/vuông, font/media và kiểm chứng: [USAGE.md](../USAGE.md#hợp-đồng-triển-khai-hyperframes).

## Liên quan / mức kiểm chứng



Metadata HTML: **đã thu**. Public prompt: **đã đọc toàn bộ**. Xem toàn video: **chưa**. Source code test: **chưa**. HyperFrames check/render: **chưa**. Prompt/media nguồn: **không archive**, chưa xác lập bulk redistribution license. [Cách dùng](../USAGE.md) · [Taxonomy](../TAXONOMY.md).
