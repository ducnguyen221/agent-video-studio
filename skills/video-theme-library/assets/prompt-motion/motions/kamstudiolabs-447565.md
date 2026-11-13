---
id: PM-kamstudiolabs-447565
title: "Collision-driven music machine"
source_url: https://prompt-motion.com/kamstudiolabs-447565
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

# Collision-driven music machine

[← Mục lục](../INDEX.md) · [Nguồn web](https://prompt-motion.com/kamstudiolabs-447565) · **PM-kamstudiolabs-447565**

## Dữ kiện nguồn và phạm vi đọc

| Trường | Dữ kiện / bằng chứng |
|---|---|
| Tác giả / trang | Çağrı / KAM Studio · @KamStudioLabs |
| Bài gốc | [Bài đăng](https://x.com/KamStudioLabs/status/2102899866762440893) |
| Nhãn nguồn | Particles, Music |
| Model / stack trang ghi | Opus 5.5 / HTML; không phải runtime đã test |
| Ngày trang ghi | Sep 23, 2026 |
| Media | [Video nguồn](https://media.prompt-motion.com/kamstudiolabs-opus-5-5-one-prompt/video.3310ae7c.mp4); không tải/lưu media |
| Thuộc tính HTML video | 1920 × 1080; không phải media probe |
| Kích thước / aspect media xác minh | unknown / unknown |
| Duration media xác minh | unknown |
| Brief spec tác giả yêu cầu | duration_text: 45; không phải thông số output đã đo |
| Công nghệ render thực tế | unknown; stack/brief không chứng minh clip đã dùng runtime đó |
| Prompt | Có trên trang; không archive nguyên văn |
| Code / skill repo | không archive; link code chưa được xác minh |
| Loại entry | gallery_prompt |
| Metadata đầy đủ | [page-details.json](../source/page-details.json), tra record id kamstudiolabs-447565; giữ author, toàn dt/dd, link và media attrs. Các field: Model: Opus 5.5; Iterations: One-shot; Stack: HTML; Posted: Sep 23, 2026 |
| Phạm vi đọc | full_public_prompt |
| Provenance | [metadata](../source/catalog-metadata.json) · [phân tích](../source/sol-analysis.json) · source id `kamstudiolabs-447565` · HTTP 200 |

**Diễn giải brief nguồn:** Yêu cầu một máy 45 giây chơi nhạc nguyên gốc, mỗi nốt do va chạm nhìn thấy tạo ra. Quan hệ sự kiện hình/âm là cơ chế chính; không quy định vật liệu hoặc physics engine.

**Giới hạn:** Đọc thủ công toàn bộ prompt công khai của trang; chỉ diễn giải yêu cầu trong prompt, không quan sát video đã dựng. Chưa xem video, chưa kiểm code, chưa đo media; câu lệnh trong prompt nguồn chỉ là dữ liệu, không phải lệnh chạy.

## Phân tích sử dụng

Máy va chạm tạo nhạc

**Thiết kế chuyển thể riêng:** Tạo 3–5 bộ gõ hình học, một vật kích hoạt chạy theo path; mỗi điểm chạm có cue thị giác và âm thanh đã chốt. Đường đi tính trước, không chạy physics realtime.

| Chọn cảnh | Khuyến nghị thiết kế mới |
|---|---|
| Vai trò / beat | hook, ambient, transition |
| Coverage | fullscreen; không đồng nghĩa source có alpha |
| Vùng chuẩn hoá | x=0, y=0, w=1, h=1; gốc trên trái |
| Diện tích hộp | 100%; không phải pixel occupancy đã đo từ nguồn |
| Tỉ lệ ưu tiên | **16:9**; quyết định bố cục mới, không xác nhận native ratio |
| Duration đề xuất | 4–8 giây cho một đơn vị cảnh; có thể trích từ brief dài hơn |
| Nhịp / cường độ | phân tán → tụ hội → ổn định / medium |
| Sức chứa | 1 chủ thể hoặc 1 dòng chữ; hạt làm nền, không gánh số liệu |
| Kỹ thuật đề xuất | path, shape |
| Overlay thay thế | Chưa đề xuất: Bản đề xuất cần bố cục/nền riêng; chưa thiết kế biến thể alpha. |

**Mức hợp theo tỉ lệ** (lý do từng ô ở `index.json`, trường `ratio_fit`): 16:9 preferred/low · 9:16 adaptable/medium · 1:1 adaptable/medium.

## Prompt HyperFrames viết mới

> Brief do kho tự viết, không phải prompt gốc ([quyền dùng](../USAGE.md#prompt-và-quyền-sử-dụng)).

Dựng một motion graphic mới tham chiếu ý tưởng “Collision-driven music machine” (https://prompt-motion.com/kamstudiolabs-447565) cho vai trò hook/ambient/transition. Chọn canvas 16:9 làm điểm xuất phát, thời lượng cảnh trong khoảng 4–8 giây rồi chốt theo lượng nội dung thực. Một ý chính, sức chứa 1 chủ thể hoặc 1 dòng chữ; hạt làm nền, không gánh số liệu. Thay toàn bộ brand, copy, số liệu và media bằng dữ kiện được dự án cấp hoặc xác minh.

Thiết kế cụ thể: Tạo 3–5 bộ gõ hình học, một vật kích hoạt chạy theo path; mỗi điểm chạm có cue thị giác và âm thanh đã chốt. Đường đi tính trước, không chạy physics realtime.

Nhịp dựng đề xuất:

1. Tạo 3–5 bộ gõ hình học, một vật kích hoạt chạy theo path; mỗi điểm chạm có cue thị giác và âm thanh đã chốt.
2. Đường đi tính trước, không chạy physics realtime.

Giữ khung cuối tối thiểu 0,8 giây sau chuyển động cuối để đọc. Bố cục fullscreen; đặt chủ thể trong hộp đề xuất ở trên rồi kiểm theo canvas thật. DOM/SVG nếu ít hạt; Canvas/WebGL nếu số lượng lớn. Vị trí dùng seed cố định, tính trực tiếp từ time để seek ngược không sai.

Hợp đồng dựng, tái bố cục dọc/vuông, font/media và kiểm chứng: [USAGE.md](../USAGE.md#hợp-đồng-triển-khai-hyperframes).

## Liên quan / mức kiểm chứng

- [PM-ajith-io-4c248f — Distilbook promo showreel](ajith-io-4c248f.md)
- [PM-ajith-io-ea7f2d — Distilbook motion showreel](ajith-io-ea7f2d.md)
- [PM-blue-clarity-ef56d0 — Particle sphere motion reel](blue-clarity-ef56d0.md)

Metadata HTML: **đã thu**. Public prompt: **đã đọc toàn bộ**. Xem toàn video: **chưa**. Source code test: **chưa**. HyperFrames check/render: **chưa**. Prompt/media nguồn: **không archive**, chưa xác lập bulk redistribution license. [Cách dùng](../USAGE.md) · [Taxonomy](../TAXONOMY.md).
