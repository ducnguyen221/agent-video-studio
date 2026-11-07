---
id: PM-demonugc-4c5753
title: "Morphing UI states loop"
source_url: https://prompt-motion.com/demonugc-4c5753
entry_type: gallery_prompt
reference_status: analyzed_prompt_reference
adaptation_detail: individual_authored_proposal
reading_scope: full_public_prompt
analysis_basis: full_public_prompt_plus_metadata_not_video_observation
primary_recommended_ratio: 1:1
runtime_tested: false
original_prompt_archived: false
authored_prompt_kind: original_hyperframes_adaptation
---

# Morphing UI states loop

[← Mục lục](../INDEX.md) · [Nguồn web](https://prompt-motion.com/demonugc-4c5753) · **PM-demonugc-4c5753**

## Dữ kiện nguồn và phạm vi đọc

| Trường | Dữ kiện / bằng chứng |
|---|---|
| Tác giả / trang | demon · @demonugc |
| Bài gốc | [Bài đăng](https://x.com/demonugc/status/2103526713208525162) |
| Nhãn nguồn | Product UI, Music |
| Model / stack trang ghi | Opus 5.5 / HTML, Playwright; không phải runtime đã test |
| Ngày trang ghi | Sep 25, 2026 |
| Media | [Video nguồn](https://media.prompt-motion.com/demonugc-opus-5-5-is-f-cking/video.8b5d1453.mp4); không tải/lưu media |
| Thuộc tính HTML video | 1440 × 1440; không phải media probe |
| Kích thước / aspect media xác minh | unknown / unknown |
| Duration media xác minh | unknown |
| Brief spec tác giả yêu cầu | dimensions: [1440,1440]; fps: 60; tempo_approximate_bpm: 120; tempo_qualifier: approximate; không phải thông số output đã đo |
| Công nghệ render thực tế | unknown; stack/brief không chứng minh clip đã dùng runtime đó |
| Prompt | Có trên trang; không archive nguyên văn |
| Code / skill repo | không archive; link code chưa được xác minh |
| Loại entry | gallery_prompt |
| Metadata đầy đủ | [page-details.json](../source/page-details.json), tra record id demonugc-4c5753; giữ author, toàn dt/dd, link và media attrs. Các field: Model: Opus 5.5; Stack: HTML, Playwright; Posted: Sep 25, 2026 |
| Phạm vi đọc | full_public_prompt |
| Provenance | [metadata](../source/catalog-metadata.json) · [phân tích](../source/root-analysis.json) · source id `demonugc-4c5753` · HTTP 200 |

**Diễn giải brief nguồn:** Brief chi tiết về một phần tử UI liên tục biến thành nhiều trạng thái có con trỏ click/drag; canvas vuông 1440×1440, nhạc 120 BPM trong 7 bars. Yêu cầu springs dạng giải tích, kéo theo tọa độ con trỏ, nội dung ra/vào riêng để không đè chữ, render 60 fps và khớp đầu/cuối. Đây là yêu cầu prompt, chưa xác minh loop xuất ra.

**Giới hạn:** full_public_prompt Chưa quan sát toàn video, chưa kiểm code và chưa đo timing/kích thước media. Các câu thao tác trong prompt nguồn là dữ liệu nghiên cứu, không phải quyền chạy lệnh, cài phần mềm hoặc gửi dữ liệu trong task hiện tại.

## Phân tích sử dụng của Sol

Giải thích một tác vụ sản phẩm bằng thay đổi trạng thái nhìn thấy được, rồi dừng ở lợi ích. Áp dụng hướng này cho tham chiếu “Morphing UI states loop”; đây là thiết kế mới theo nhãn nguồn.

**Thiết kế chuyển thể riêng:** Giữ một wrapper hình học với radius/size nội suy, bên trong mỗi trạng thái có track text riêng. Con trỏ giả lập có đường chuyển động và mốc nhấn định trước; lượng kéo suy ra trực tiếp từ thời gian. Hai mép indicator dùng curve khác nhau cho stretch; đóng loop bằng khớp cả position và vận tốc tại biên, số chu kỳ hữu hạn.

| Chọn cảnh | Khuyến nghị thiết kế mới |
|---|---|
| Vai trò / beat | explain, proof, cta |
| Coverage | partial; không đồng nghĩa source có alpha |
| Vùng chuẩn hoá | x=0.08, y=0.12, w=0.84, h=0.72; gốc trên trái |
| Diện tích hộp | 60%; không phải pixel occupancy đã đo từ nguồn |
| Tỉ lệ ưu tiên | **1:1**; quyết định bố cục mới, không xác nhận native ratio |
| Duration đề xuất | 6–12 giây cho một đơn vị cảnh; có thể trích từ brief dài hơn |
| Nhịp / cường độ | mở vấn đề → thao tác → kết quả → giữ nhãn / medium |
| Sức chứa | 1 tác vụ; 1–3 trạng thái UI; 1 tiêu đề ngắn |
| Kỹ thuật đề xuất | ui, mask, stagger |
| Overlay thay thế | Chưa đề xuất: Bản đề xuất cần bố cục/nền riêng; chưa thiết kế biến thể alpha. |

| Tỉ lệ | Mức phù hợp đề xuất | Công sức | Cách thích nghi |
|---|---|---|---|
| 16:9 | adaptable | medium | Sắp lại khoảng cách/nhãn theo canvas; không crop tự động. |
| 9:16 | requires_redesign | high | Xếp lại quan hệ theo chiều dọc, tăng chữ, giảm panel; kiểm clipping riêng. |
| 1:1 | preferred | low | Đề xuất bố cục xuất phát; không xác nhận native ratio của media nguồn. |

Khung dọc: xếp lại quan hệ, giảm panel, tăng cỡ chữ và chừa vùng phụ đề theo dự án; không crop screenshot có chữ. Khung vuông: gom một tiêu điểm, đưa nhãn phụ ra vành. Vùng đề xuất cần chỉnh theo canvas/nội dung thật, không coi một hộp chuẩn hoá là bố cục đã QA mọi ratio.

## Prompt HyperFrames viết mới

> Sol tự viết brief triển khai dưới đây; không phải prompt gốc và không cam kết tái tạo chính xác nguồn. Chỉ dùng tài sản/font/media mà dự án có quyền.

Dựng một motion graphic mới tham chiếu ý tưởng “Morphing UI states loop” (https://prompt-motion.com/demonugc-4c5753) cho vai trò explain/proof/cta. Chọn canvas 1:1 làm điểm xuất phát, thời lượng cảnh trong khoảng 6–12 giây rồi chốt theo lượng nội dung thực. Một ý chính, sức chứa 1 tác vụ; 1–3 trạng thái UI; 1 tiêu đề ngắn. Thay toàn bộ brand, copy, số liệu và media bằng dữ kiện được dự án cấp hoặc xác minh.

Thiết kế cụ thể: Giữ một wrapper hình học với radius/size nội suy, bên trong mỗi trạng thái có track text riêng. Con trỏ giả lập có đường chuyển động và mốc nhấn định trước; lượng kéo suy ra trực tiếp từ thời gian. Hai mép indicator dùng curve khác nhau cho stretch; đóng loop bằng khớp cả position và vận tốc tại biên, số chu kỳ hữu hạn.

Nhịp dựng đề xuất:

1. Giữ một wrapper hình học với radius/size nội suy, bên trong mỗi trạng thái có track text riêng.
2. Con trỏ giả lập có đường chuyển động và mốc nhấn định trước; lượng kéo suy ra trực tiếp từ thời gian.
3. Hai mép indicator dùng curve khác nhau cho stretch; đóng loop bằng khớp cả position và vận tốc tại biên, số chu kỳ hữu hạn.

Giữ khung cuối tối thiểu 0,8 giây sau chuyển động cuối để đọc. Bố cục partial; đặt chủ thể trong hộp đề xuất ở trên rồi kiểm theo canvas thật. DOM/SVG + GSAP; ảnh chụp có quyền chỉ dùng làm panel. Không cần Canvas cho nút, thẻ hay text.

Dùng một GSAP timeline paused, đăng ký vào window.__timelines bằng đúng data-composition-id sau khi dựng. Trạng thái đầu bằng fromTo; clip gốc không bị tween visibility/autoAlpha. Mọi frame là hàm của thời gian tuyệt đối, random có seed, chu kỳ hữu hạn; không đồng hồ hệ thống, chuột, network hay physics tích lũy. Không requestAnimationFrame tự chạy hoặc repeat vô hạn. Nếu dùng canvas/WebGL, render trực tiếp pose/state tại time bất kỳ; timeline là nguồn thời gian duy nhất.

Đặt font/media cục bộ có quyền và biến text/màu/dữ liệu thành tham số. Với narration hay nhiều cảnh dài, route sang general-video rồi dùng motion này như một beat, không ép toàn bộ brief dài vào một hit. Kiểm lint/check, snapshot đầu/giữa mỗi pha/cuối, seek ngược, clipping/chữ/tương phản/z-order và vùng phụ đề; ratio khác phải kiểm lại. Chỉ render khi task dựng video đã giao rõ.

## Liên quan / mức kiểm chứng

- [PM-twoclipping-5cba86 — Shape morphing through UI states](twoclipping-5cba86.md)
- [PM-twoclipping-221cab — Photo print app launch film](twoclipping-221cab.md)
- [PM-twoclipping-d89be5 — Landing page 3D scroll](twoclipping-d89be5.md)

Metadata HTML: **đã thu**. Public prompt: **đã đọc toàn bộ**. Xem toàn video: **chưa**. Source code test: **chưa**. HyperFrames check/render: **chưa**. Prompt/media nguồn: **không archive**, chưa xác lập bulk redistribution license. [Cách dùng](../USAGE.md) · [Taxonomy](../TAXONOMY.md).
