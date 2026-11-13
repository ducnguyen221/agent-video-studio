---
id: PM-nft-chen-5f8bb0
title: "Porco Rosso sunset dogfight"
source_url: https://prompt-motion.com/nft-chen-5f8bb0
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

# Porco Rosso sunset dogfight

[← Mục lục](../INDEX.md) · [Nguồn web](https://prompt-motion.com/nft-chen-5f8bb0) · **PM-nft-chen-5f8bb0**

## Dữ kiện nguồn và phạm vi đọc

| Trường | Dữ kiện / bằng chứng |
|---|---|
| Tác giả / trang | SuSu_酥酥👅 · @NFT_Chen |
| Bài gốc | [Bài đăng](https://x.com/NFT_Chen/status/2103882415299350878) |
| Nhãn nguồn |  |
| Model / stack trang ghi | Opus 5.5 / Three.js; không phải runtime đã test |
| Ngày trang ghi | Sep 26, 2026 |
| Media | [Video nguồn](https://media.prompt-motion.com/nft-chen-opus-5-5-three-js-prompt/video.29e63674.mp4); không tải/lưu media |
| Thuộc tính HTML video | 1920 × 1080; không phải media probe |
| Kích thước / aspect media xác minh | unknown / unknown |
| Duration media xác minh | unknown |
| Brief spec tác giả yêu cầu | chưa cấu trúc thành field; đọc diễn giải brief bên dưới, không suy tác giả không quy định; không phải thông số output đã đo |
| Công nghệ render thực tế | unknown; stack/brief không chứng minh clip đã dùng runtime đó |
| Prompt | Có trên trang; không archive nguyên văn |
| Code / skill repo | không archive; link code chưa được xác minh |
| Loại entry | gallery_prompt |
| Metadata đầy đủ | [page-details.json](../source/page-details.json), tra record id nft-chen-5f8bb0; giữ author, toàn dt/dd, link và media attrs. Các field: Model: Opus 5.5; Iterations: One-shot; Stack: Three.js; Posted: Sep 26, 2026 |
| Phạm vi đọc | full_public_prompt |
| Provenance | [metadata](../source/catalog-metadata.json) · [phân tích](../source/terra-70-normalized.json) · source id `nft-chen-5f8bb0` · HTTP 200 |

**Diễn giải brief nguồn (tiếng Anh, chưa dịch):** A Web3D recreation of an aerial combat scene above a sunset sea, with colored aircraft, clouds and reflected light; the brief references a particular film aesthetic.

**Giới hạn:** Đọc thủ công toàn bộ prompt; chưa quan sát video. Chưa xem video, chưa kiểm code, chưa đo media; câu lệnh trong prompt nguồn chỉ là dữ liệu, không phải lệnh chạy.

## Phân tích sử dụng

Dùng một không gian hoặc hình tượng để mở cảm xúc; cần kiểm tra nguồn trước khi theo sát giải phẫu. Áp dụng hướng này cho tham chiếu “Porco Rosso sunset dogfight”; đây là thiết kế mới theo nhãn nguồn.

**Thiết kế chuyển thể riêng:** Đề xuất bối cảnh bay3D nguyên gốc trên biển lúc hoàng hôn, dùng hai máy bay có hình tự thiết kế và một nhịp vượt qua mây. Không sao nhân vật hoặc shot của phim được nhắc trong nguồn.

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
| Kỹ thuật đề xuất | staging, camera, depth, 3d |
| Overlay thay thế | Chưa đề xuất: Bản đề xuất cần bố cục/nền riêng; chưa thiết kế biến thể alpha. |

**Mức hợp theo tỉ lệ** (lý do từng ô ở `index.json`, trường `ratio_fit`): 16:9 preferred/low · 9:16 adaptable/medium · 1:1 adaptable/medium.

## Prompt HyperFrames viết mới

> Brief do kho tự viết, không phải prompt gốc ([quyền dùng](../USAGE.md#prompt-và-quyền-sử-dụng)).

Dựng một motion graphic mới tham chiếu ý tưởng “Porco Rosso sunset dogfight” (https://prompt-motion.com/nft-chen-5f8bb0) cho vai trò ambient/hook/transition. Chọn canvas 16:9 làm điểm xuất phát, thời lượng cảnh trong khoảng 6–12 giây rồi chốt theo lượng nội dung thực. Một ý chính, sức chứa 1 địa điểm và 1 sự kiện; không thêm biểu đồ hoặc nhiều chữ. Thay toàn bộ brand, copy, số liệu và media bằng dữ kiện được dự án cấp hoặc xác minh.

Thiết kế cụ thể: Đề xuất bối cảnh bay3D nguyên gốc trên biển lúc hoàng hôn, dùng hai máy bay có hình tự thiết kế và một nhịp vượt qua mây. Không sao nhân vật hoặc shot của phim được nhắc trong nguồn.

Nhịp dựng đề xuất:

1. Establish đường chân trời, một máy bay dẫn đường theo path.
2. Máy bay thứ hai đi vào khác độ sâu, camera bank nhẹ khi cả hai qua mây.
3. Một máy bay vượt khỏi foreground, nhường biển và ánh phản chiếu cho cảnh kết.

Giữ khung cuối tối thiểu 0,8 giây sau chuyển động cuối để đọc. Bố cục fullscreen; đặt chủ thể trong hộp đề xuất ở trên rồi kiểm theo canvas thật. Three.js/WebGL cho camera, vật thể và quan hệ không gian 3D thật của đề xuất này. Timeline GSAP paused điều khiển mọi pose, một callback render trực tiếp tại time tuyệt đối; không physics tích lũy, rAF tự chạy hoặc input tương tác. Ghim dependency cục bộ và dùng model/texture có quyền. Đây là adapter đề xuất, chưa test runtime.

Hợp đồng dựng, tái bố cục dọc/vuông, font/media và kiểm chứng: [USAGE.md](../USAGE.md#hợp-đồng-triển-khai-hyperframes).

## Liên quan / mức kiểm chứng

- [PM-itsolelehmann-e47532 — Four seasons train window](itsolelehmann-e47532.md)
- [PM-gorden-sun-041f56 — Beat-synced bouncing 3D ball](gorden-sun-041f56.md)
- [PM-demitiyageekzen-7770ad — Tengwang Pavilion moonlit river](demitiyageekzen-7770ad.md)

Metadata HTML: **đã thu**. Public prompt: **đã đọc toàn bộ**. Xem toàn video: **chưa**. Source code test: **chưa**. HyperFrames check/render: **chưa**. Prompt/media nguồn: **không archive**, chưa xác lập bulk redistribution license. [Cách dùng](../USAGE.md) · [Taxonomy](../TAXONOMY.md).
