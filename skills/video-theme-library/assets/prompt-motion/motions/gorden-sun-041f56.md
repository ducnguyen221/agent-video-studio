---
id: PM-gorden-sun-041f56
title: "Beat-synced bouncing 3D ball"
source_url: https://prompt-motion.com/gorden-sun-041f56
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

# Beat-synced bouncing 3D ball

[← Mục lục](../INDEX.md) · [Nguồn web](https://prompt-motion.com/gorden-sun-041f56) · **PM-gorden-sun-041f56**

## Dữ kiện nguồn và phạm vi đọc

| Trường | Dữ kiện / bằng chứng |
|---|---|
| Tác giả / trang | Gorden Sun · @Gorden_Sun |
| Bài gốc | [Bài đăng](https://x.com/Gorden_Sun/status/2105302007896797351) |
| Nhãn nguồn | Music |
| Model / stack trang ghi | Opus 5.5 / Three.js; không phải runtime đã test |
| Ngày trang ghi | Sep 30, 2026 |
| Media | [Video nguồn](https://media.prompt-motion.com/gorden-sun-opus-5-5-3d-blender-3d-3d-three-js/video.89882cc3.mp4); không tải/lưu media |
| Thuộc tính HTML video | 1280 × 720; không phải media probe |
| Kích thước / aspect media xác minh | unknown / unknown |
| Duration media xác minh | unknown |
| Brief spec tác giả yêu cầu | chưa cấu trúc thành field; đọc diễn giải brief bên dưới, không suy tác giả không quy định; không phải thông số output đã đo |
| Công nghệ render thực tế | unknown; stack/brief không chứng minh clip đã dùng runtime đó |
| Prompt | Có trên trang; không archive nguyên văn |
| Code / skill repo | không archive; link code chưa được xác minh |
| Loại entry | gallery_prompt |
| Metadata đầy đủ | [page-details.json](../source/page-details.json), tra record id gorden-sun-041f56; giữ author, toàn dt/dd, link và media attrs. Các field: Model: Opus 5.5; Stack: Three.js; Posted: Sep 30, 2026 |
| Phạm vi đọc | full_public_prompt |
| Provenance | [metadata](../source/catalog-metadata.json) · [phân tích](../source/terra-70-normalized.json) · source id `gorden-sun-041f56` · HTTP 200 |

**Diễn giải brief nguồn (tiếng Anh, chưa dịch):** Three.js animation of a falling ball bouncing through 3D environments and illuminating objects on musical beats; scenes change with music and include humor.

**Giới hạn:** Đọc thủ công toàn bộ prompt; chưa quan sát video. Chưa xem video, chưa kiểm code, chưa đo media; câu lệnh trong prompt nguồn chỉ là dữ liệu, không phải lệnh chạy.

## Phân tích sử dụng

Nảy có nhịp và trọng lượng

**Thiết kế chuyển thể riêng:** Đề xuất quả bóng3D đi qua vài môi trường bằng các lần chạm trúng beat; mỗi lần chạm làm sáng một vật thể có liên hệ. Quỹ đạo bóng dùng các đoạn analytic có contact time cố định, không physics tích lũy.

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
| Kỹ thuật đề xuất | 3d, shape, camera |
| Overlay thay thế | Chưa đề xuất: Bản đề xuất cần bố cục/nền riêng; chưa thiết kế biến thể alpha. |

**Mức hợp theo tỉ lệ** (lý do từng ô ở `index.json`, trường `ratio_fit`): 16:9 preferred/low · 9:16 adaptable/medium · 1:1 adaptable/medium.

## Prompt HyperFrames viết mới

> Brief do kho tự viết, không phải prompt gốc ([quyền dùng](../USAGE.md#prompt-và-quyền-sử-dụng)).

Dựng một motion graphic mới tham chiếu ý tưởng “Beat-synced bouncing 3D ball” (https://prompt-motion.com/gorden-sun-041f56) cho vai trò ambient/hook/transition. Chọn canvas 16:9 làm điểm xuất phát, thời lượng cảnh trong khoảng 6–12 giây rồi chốt theo lượng nội dung thực. Một ý chính, sức chứa 1 địa điểm và 1 sự kiện; không thêm biểu đồ hoặc nhiều chữ. Thay toàn bộ brand, copy, số liệu và media bằng dữ kiện được dự án cấp hoặc xác minh.

Thiết kế cụ thể: Đề xuất quả bóng3D đi qua vài môi trường bằng các lần chạm trúng beat; mỗi lần chạm làm sáng một vật thể có liên hệ. Quỹ đạo bóng dùng các đoạn analytic có contact time cố định, không physics tích lũy.

Nhịp dựng đề xuất:

1. Bóng rơi vào một mặt phẳng; mặt được chạm sáng cùng cue âm thanh.
2. Một bounce đưa bóng sang môi trường tiếp; camera và ánh sáng đổi trong đoạn có che khuất.
3. Bóng đáp lên vị trí chốt và giảm chuyển động để lộ câu kết.

Giữ khung cuối tối thiểu 0,8 giây sau chuyển động cuối để đọc. Bố cục fullscreen; đặt chủ thể trong hộp đề xuất ở trên rồi kiểm theo canvas thật. Three.js/WebGL cho camera, vật thể và quan hệ không gian 3D thật của đề xuất này. Timeline GSAP paused điều khiển mọi pose, một callback render trực tiếp tại time tuyệt đối; không physics tích lũy, rAF tự chạy hoặc input tương tác. Ghim dependency cục bộ và dùng model/texture có quyền. Đây là adapter đề xuất, chưa test runtime.

Hợp đồng dựng, tái bố cục dọc/vuông, font/media và kiểm chứng: [USAGE.md](../USAGE.md#hợp-đồng-triển-khai-hyperframes).

## Liên quan / mức kiểm chứng

- [PM-itsolelehmann-e47532 — Four seasons train window](itsolelehmann-e47532.md)
- [PM-nft-chen-5f8bb0 — Porco Rosso sunset dogfight](nft-chen-5f8bb0.md)
- [PM-demitiyageekzen-7770ad — Tengwang Pavilion moonlit river](demitiyageekzen-7770ad.md)

Metadata HTML: **đã thu**. Public prompt: **đã đọc toàn bộ**. Xem toàn video: **chưa**. Source code test: **chưa**. HyperFrames check/render: **chưa**. Prompt/media nguồn: **không archive**, chưa xác lập bulk redistribution license. [Cách dùng](../USAGE.md) · [Taxonomy](../TAXONOMY.md).
