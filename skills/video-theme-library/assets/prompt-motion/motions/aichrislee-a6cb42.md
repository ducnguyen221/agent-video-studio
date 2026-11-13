---
id: PM-aichrislee-a6cb42
title: "Motion designer showreel"
source_url: https://prompt-motion.com/aichrislee-a6cb42
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

# Motion designer showreel

[← Mục lục](../INDEX.md) · [Nguồn web](https://prompt-motion.com/aichrislee-a6cb42) · **PM-aichrislee-a6cb42**

## Dữ kiện nguồn và phạm vi đọc

| Trường | Dữ kiện / bằng chứng |
|---|---|
| Tác giả / trang | AI Chris Lee / Sell AI · @aichrislee |
| Bài gốc | [Bài đăng](https://x.com/aichrislee/status/2103878567540961335) |
| Nhãn nguồn | Kinetic type, Shapes, Music |
| Model / stack trang ghi | Opus 5.5 / unknown; không phải runtime đã test |
| Ngày trang ghi | Sep 26, 2026 |
| Media | [Video nguồn](https://media.prompt-motion.com/aichrislee-opus-5-5-is-insane/video.16e8bcb2.mp4); không tải/lưu media |
| Thuộc tính HTML video | 1280 × 720; không phải media probe |
| Kích thước / aspect media xác minh | unknown / unknown |
| Duration media xác minh | unknown |
| Brief spec tác giả yêu cầu | duration_text: 15; fps: 30; dimensions: [1920,1080]; không phải thông số output đã đo |
| Công nghệ render thực tế | unknown; stack/brief không chứng minh clip đã dùng runtime đó |
| Prompt | Có trên trang; không archive nguyên văn |
| Code / skill repo | không archive; link code chưa được xác minh |
| Loại entry | gallery_prompt |
| Metadata đầy đủ | [page-details.json](../source/page-details.json), tra record id aichrislee-a6cb42; giữ author, toàn dt/dd, link và media attrs. Các field: Model: Opus 5.5; Iterations: One-shot; Posted: Sep 26, 2026 |
| Phạm vi đọc | full_public_prompt |
| Provenance | [metadata](../source/catalog-metadata.json) · [phân tích](../source/sol-analysis.json) · source id `aichrislee-a6cb42` · HTTP 200 |

**Diễn giải brief nguồn:** Brief showreel 15 giây, chữ lớn/màu mạnh/camera, nhịp liên tục. Nêu 16:9, 1920×1080, 30fps; một HTML có frame là hàm thuần của time, Playwright+ffmpeg. Thông số này là yêu cầu brief, không phép đo file MP4.

**Giới hạn:** Đọc thủ công toàn bộ prompt công khai của trang; chỉ diễn giải yêu cầu trong prompt, không quan sát video đã dựng. Chưa xem video, chưa kiểm code, chưa đo media; câu lệnh trong prompt nguồn chỉ là dữ liệu, không phải lệnh chạy.

## Phân tích sử dụng

Cho hình dạng và nhịp chữ làm rõ một câu chủ đạo; không nhét nguyên đoạn lời đọc. Áp dụng hướng này cho tham chiếu “Motion designer showreel”; đây là thiết kế mới theo nhãn nguồn.

**Thiết kế chuyển thể riêng:** Đề xuất ba pha với một thanh màu làm motif: thanh bật thành từ khóa lớn, camera tiến vào khoảng âm trong chữ để lộ một hệ hình học, hệ hình học thu lại thành khung kết. Cảm giác năng động đến từ thay scale và nhịp dừng rất ngắn, không phải nhiều tween đồng thời. Đặt mọi pose bằng hàm time và giữ khung cuối đọc được; FPS/tỉ lệ là thông số dự án mới phải chốt.

| Chọn cảnh | Khuyến nghị thiết kế mới |
|---|---|
| Vai trò / beat | hook, emphasis, closing |
| Coverage | fullscreen; không đồng nghĩa source có alpha |
| Vùng chuẩn hoá | x=0, y=0, w=1, h=1; gốc trên trái |
| Diện tích hộp | 100%; không phải pixel occupancy đã đo từ nguồn |
| Tỉ lệ ưu tiên | **16:9**; quyết định bố cục mới, không xác nhận native ratio |
| Duration đề xuất | 3–7 giây cho một đơn vị cảnh; có thể trích từ brief dài hơn |
| Nhịp / cường độ | một từ khóa bật → cụm nghĩa hoàn chỉnh → giữ / high |
| Sức chứa | 1 câu tối đa 5–8 từ; 1–2 cấp chữ |
| Kỹ thuật đề xuất | typography, mask, stagger |
| Overlay thay thế | Có thể thiết kế riêng: Chỉ trích chủ thể/nhãn, bỏ nền và thiết kế alpha riêng; media nguồn chưa xác nhận có alpha. |

**Mức hợp theo tỉ lệ** (lý do từng ô ở `index.json`, trường `ratio_fit`): 16:9 preferred/low · 9:16 adaptable/medium · 1:1 adaptable/medium.

## Prompt HyperFrames viết mới

> Brief do kho tự viết, không phải prompt gốc ([quyền dùng](../USAGE.md#prompt-và-quyền-sử-dụng)).

Dựng một motion graphic mới tham chiếu ý tưởng “Motion designer showreel” (https://prompt-motion.com/aichrislee-a6cb42) cho vai trò hook/emphasis/closing. Chọn canvas 16:9 làm điểm xuất phát, thời lượng cảnh trong khoảng 3–7 giây rồi chốt theo lượng nội dung thực. Một ý chính, sức chứa 1 câu tối đa 5–8 từ; 1–2 cấp chữ. Thay toàn bộ brand, copy, số liệu và media bằng dữ kiện được dự án cấp hoặc xác minh.

Thiết kế cụ thể: Đề xuất ba pha với một thanh màu làm motif: thanh bật thành từ khóa lớn, camera tiến vào khoảng âm trong chữ để lộ một hệ hình học, hệ hình học thu lại thành khung kết. Cảm giác năng động đến từ thay scale và nhịp dừng rất ngắn, không phải nhiều tween đồng thời. Đặt mọi pose bằng hàm time và giữ khung cuối đọc được; FPS/tỉ lệ là thông số dự án mới phải chốt.

Nhịp dựng đề xuất:

1. Đề xuất ba pha với một thanh màu làm motif: thanh bật thành từ khóa lớn, camera tiến vào khoảng âm trong chữ để lộ một hệ hình học, hệ hình học thu lại thành khung kết.
2. Cảm giác năng động đến từ thay scale và nhịp dừng rất ngắn, không phải nhiều tween đồng thời.
3. Đặt mọi pose bằng hàm time và giữ khung cuối đọc được; FPS/tỉ lệ là thông số dự án mới phải chốt.

Giữ khung cuối tối thiểu 0,8 giây sau chuyển động cuối để đọc. Bố cục fullscreen; đặt chủ thể trong hộp đề xuất ở trên rồi kiểm theo canvas thật. DOM text + GSAP; mask bằng CSS clip-path hoặc SVG. Tách cụm có nghĩa, giữ dấu tiếng Việt và không cắt chữ giữa ký tự.

Hợp đồng dựng, tái bố cục dọc/vuông, font/media và kiểm chứng: [USAGE.md](../USAGE.md#hợp-đồng-triển-khai-hyperframes).

## Liên quan / mức kiểm chứng

- [PM-stephanlivera-df17a2 — Claude motion designer showreel](stephanlivera-df17a2.md)
- [PM-shneural-2abdfa — Bold kinetic type showreel](shneural-2abdfa.md)
- [PM-ajith-io-b5626e — Abstract motion design reel](ajith-io-b5626e.md)

Metadata HTML: **đã thu**. Public prompt: **đã đọc toàn bộ**. Xem toàn video: **chưa**. Source code test: **chưa**. HyperFrames check/render: **chưa**. Prompt/media nguồn: **không archive**, chưa xác lập bulk redistribution license. [Cách dùng](../USAGE.md) · [Taxonomy](../TAXONOMY.md).
