---
id: PM-itsolelehmann-e47532
title: "Four seasons train window"
source_url: https://prompt-motion.com/itsolelehmann-e47532
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

# Four seasons train window

[← Mục lục](../INDEX.md) · [Nguồn web](https://prompt-motion.com/itsolelehmann-e47532) · **PM-itsolelehmann-e47532**

## Dữ kiện nguồn và phạm vi đọc

| Trường | Dữ kiện / bằng chứng |
|---|---|
| Tác giả / trang | Ole Lehmann · @itsolelehmann |
| Bài gốc | [Bài đăng](https://x.com/itsolelehmann/status/2103124033365762215) |
| Nhãn nguồn |  |
| Model / stack trang ghi | Opus 5.5 / unknown; không phải runtime đã test |
| Ngày trang ghi | Sep 24, 2026 |
| Media | [Video nguồn](https://media.prompt-motion.com/itsolelehmann-anthropic-has-no-image/video.5bd8c36f.mp4); không tải/lưu media |
| Thuộc tính HTML video | 1920 × 1080; không phải media probe |
| Kích thước / aspect media xác minh | unknown / unknown |
| Duration media xác minh | unknown |
| Brief spec tác giả yêu cầu | chưa cấu trúc thành field; đọc diễn giải brief bên dưới, không suy tác giả không quy định; không phải thông số output đã đo |
| Công nghệ render thực tế | unknown; stack/brief không chứng minh clip đã dùng runtime đó |
| Prompt | Có trên trang; không archive nguyên văn |
| Code / skill repo | không archive; link code chưa được xác minh |
| Loại entry | gallery_prompt |
| Metadata đầy đủ | [page-details.json](../source/page-details.json), tra record id itsolelehmann-e47532; giữ author, toàn dt/dd, link và media attrs. Các field: Model: Opus 5.5; Iterations: One-shot; Posted: Sep 24, 2026 |
| Phạm vi đọc | full_public_prompt |
| Provenance | [metadata](../source/catalog-metadata.json) · [phân tích](../source/terra-70-normalized.json) · source id `itsolelehmann-e47532` · HTTP 200 |

**Diễn giải brief nguồn (tiếng Anh, chưa dịch):** Four seasons pass outside a train window while a cozy carriage and coffee remain foreground context; timing and build method are unspecified.

**Giới hạn:** Đọc thủ công toàn bộ prompt; chưa quan sát video. Chưa xem video, chưa kiểm code, chưa đo media; câu lệnh trong prompt nguồn chỉ là dữ liệu, không phải lệnh chạy.

## Phân tích sử dụng

Cửa sổ giữ nguyên, cảnh thay mùa

**Thiết kế chuyển thể riêng:** Đề xuất giữ khung cửa tàu và cốc cà phê ở tiền cảnh làm hệ quy chiếu; chỉ môi trường ngoài cửa thay mùa và chạy parallax. Cảnh interior không trôi cùng background.

| Chọn cảnh | Khuyến nghị thiết kế mới |
|---|---|
| Vai trò / beat | ambient, hook, transition |
| Coverage | fullscreen; không đồng nghĩa source có alpha |
| Vùng chuẩn hoá | x=0, y=0, w=1, h=1; gốc trên trái |
| Diện tích hộp | 100%; không phải pixel occupancy đã đo từ nguồn |
| Tỉ lệ ưu tiên | **16:9**; quyết định bố cục mới, không xác nhận native ratio |
| Duration đề xuất | 6–12 giây cho một đơn vị cảnh; có thể trích từ brief dài hơn |
| Nhịp / cường độ | thiết lập không gian → một chuyển động chủ đạo → giữ / low |
| Sức chứa | 1 địa điểm và 1 sự kiện; không thêm biểu đồ hoặc nhiều chữ |
| Kỹ thuật đề xuất | image, mask |
| Overlay thay thế | Chưa đề xuất: Bản đề xuất cần bố cục/nền riêng; chưa thiết kế biến thể alpha. |

**Mức hợp theo tỉ lệ** (lý do từng ô ở `index.json`, trường `ratio_fit`): 16:9 preferred/low · 9:16 adaptable/medium · 1:1 adaptable/medium.

## Prompt HyperFrames viết mới

> Brief do kho tự viết, không phải prompt gốc ([quyền dùng](../USAGE.md#prompt-và-quyền-sử-dụng)).

Dựng một motion graphic mới tham chiếu ý tưởng “Four seasons train window” (https://prompt-motion.com/itsolelehmann-e47532) cho vai trò ambient/hook/transition. Chọn canvas 16:9 làm điểm xuất phát, thời lượng cảnh trong khoảng 6–12 giây rồi chốt theo lượng nội dung thực. Một ý chính, sức chứa 1 địa điểm và 1 sự kiện; không thêm biểu đồ hoặc nhiều chữ. Thay toàn bộ brand, copy, số liệu và media bằng dữ kiện được dự án cấp hoặc xác minh.

Thiết kế cụ thể: Đề xuất giữ khung cửa tàu và cốc cà phê ở tiền cảnh làm hệ quy chiếu; chỉ môi trường ngoài cửa thay mùa và chạy parallax. Cảnh interior không trôi cùng background.

Nhịp dựng đề xuất:

1. Đặt khung cửa và cốc tĩnh; lớp xa/chính/lân cận chạy tốc độ khác nhau.
2. Màu cây, thời tiết và ánh sáng chuyển qua các mùa bằng mask/parameter có nhịp.
3. Giảm tốc ở một mùa được chọn và giữ cảnh yên.

Giữ khung cuối tối thiểu 0,8 giây sau chuyển động cuối để đọc. Bố cục fullscreen; đặt chủ thể trong hộp đề xuất ở trên rồi kiểm theo canvas thật. DOM/SVG cho nhiều lớp 2D; Three.js nếu cần không gian 3D thật. Camera lấy từ time tuyệt đối, không điều khiển bằng chuột.

Hợp đồng dựng, tái bố cục dọc/vuông, font/media và kiểm chứng: [USAGE.md](../USAGE.md#hợp-đồng-triển-khai-hyperframes).

## Liên quan / mức kiểm chứng

- [PM-nft-chen-5f8bb0 — Porco Rosso sunset dogfight](nft-chen-5f8bb0.md)
- [PM-gorden-sun-041f56 — Beat-synced bouncing 3D ball](gorden-sun-041f56.md)
- [PM-demitiyageekzen-7770ad — Tengwang Pavilion moonlit river](demitiyageekzen-7770ad.md)

Metadata HTML: **đã thu**. Public prompt: **đã đọc toàn bộ**. Xem toàn video: **chưa**. Source code test: **chưa**. HyperFrames check/render: **chưa**. Prompt/media nguồn: **không archive**, chưa xác lập bulk redistribution license. [Cách dùng](../USAGE.md) · [Taxonomy](../TAXONOMY.md).
