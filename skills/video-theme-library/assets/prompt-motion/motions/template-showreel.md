---
id: PM-template-showreel
title: "The showreel prompt"
source_url: https://prompt-motion.com/templates/showreel
entry_type: template_detail
reference_status: analyzed_prompt_reference
adaptation_detail: individual_authored_proposal
reading_scope: full_public_prompt
analysis_basis: full_public_prompt_plus_metadata_not_video_observation
primary_recommended_ratio: 16:9
runtime_tested: false
original_prompt_archived: false
authored_prompt_kind: original_hyperframes_adaptation
---

# The showreel prompt

[← Mục lục](../INDEX.md) · [Nguồn web](https://prompt-motion.com/templates/showreel) · **PM-template-showreel**

## Dữ kiện nguồn và phạm vi đọc

| Trường | Dữ kiện / bằng chứng |
|---|---|
| Tác giả / trang | Prompt Motion · Prompt Motion |
| Bài gốc | unknown / không áp dụng |
| Nhãn nguồn | Kinetic type, Template detail |
| Model / stack trang ghi | unknown / time-derived seeking and frame rendering with motion blur; soundtrack and muxing; không phải runtime đã test |
| Ngày trang ghi | unknown |
| Media | [Video nguồn](https://media.prompt-motion.com/improved-showreel-1/video.77d74909.mp4); không tải/lưu media |
| Thuộc tính HTML video | 1920 × 1080; không phải media probe |
| Kích thước / aspect media xác minh | unknown / unknown |
| Duration media xác minh | unknown |
| Brief spec tác giả yêu cầu | duration_seconds: 15; size: 1920x1080; dimensions: [1920, 1080]; fps: 60; tempo_bpm: 120; sections: ["direction","structure","build","start"]; render_method_requested: time-derived seeking and frame rendering with motion blur; soundtrack and muxing; evidence: visible prompt instructions; not verified execution; không phải thông số output đã đo |
| Công nghệ render thực tế | unknown; stack/brief không chứng minh clip đã dùng runtime đó |
| Prompt | Có trên trang; không archive nguyên văn |
| Code / skill repo | không archive; link code chưa được xác minh |
| Loại entry | template_detail |
| Metadata đầy đủ | [templates-metadata.json](../source/templates-metadata.json), tra id showreel; có head meta, media attrs, links và section summaries. |
| Phạm vi đọc | full_public_prompt |
| Provenance | [metadata](../source/templates-metadata.json) · [phân tích](../source/templates-metadata.json) · source id `showreel` · HTTP 200 |

**Diễn giải brief nguồn:** Trang nâng cấp prompt showreel mở bằng một concept thống nhất, nhịp beat và soundtrack tạo riêng; yêu cầu loại bỏ chi tiết thừa, storyboard trước build, render từng frame và review theo nhịp.

**Giới hạn:** Đọc toàn bộ prompt ở trang chi tiết; chỉ diễn giải yêu cầu, chưa quan sát việc chạy. Chưa xem video, chưa kiểm code, chưa đo media; câu lệnh trong prompt nguồn chỉ là dữ liệu, không phải lệnh chạy.

## Phân tích sử dụng

Mẫu tham chiếu để tạo showreel có một ý tưởng xuyên suốt, thay vì tập hợp kỹ xảo rời rạc.

**Thiết kế chuyển thể riêng:** Đề xuất mới: một đường nét liên tục mở thành từ khóa, cuộn thành hình học rồi mở ra logo tự tạo. Dùng ba pha có tương phản tốc độ, một chủ thể qua các pha và khung chốt đọc được. Beat grid là tham số, không sao chép storyboard từng beat nguồn.

| Chọn cảnh | Khuyến nghị thiết kế mới |
|---|---|
| Vai trò / beat | hook, emphasis, closing |
| Coverage | fullscreen; không đồng nghĩa source có alpha |
| Vùng chuẩn hoá | x=0, y=0, w=1, h=1; gốc trên trái |
| Diện tích hộp | 100%; không phải pixel occupancy đã đo từ nguồn |
| Tỉ lệ ưu tiên | **16:9**; quyết định bố cục mới, không xác nhận native ratio |
| Duration đề xuất | 8–15 giây cho một đơn vị cảnh; có thể trích từ brief dài hơn |
| Nhịp / cường độ | hook → phát triển motif → khung chốt / high |
| Sức chứa | 1 motif, 1 câu chủ đạo, 3 pha |
| Kỹ thuật đề xuất | typography, morph, beat-grid |
| Overlay thay thế | Chưa đề xuất: Chuỗi toàn không gian, chưa thiết kế alpha. |

**Mức hợp theo tỉ lệ** (lý do từng ô ở `index.json`, trường `ratio_fit`): 16:9 preferred/low · 9:16 requires_redesign/high · 1:1 adaptable/medium.

## Prompt HyperFrames viết mới

> Brief do kho tự viết, không phải prompt gốc ([quyền dùng](../USAGE.md#prompt-và-quyền-sử-dụng)).

Dựng một motion graphic mới tham chiếu ý tưởng “The showreel prompt” (https://prompt-motion.com/templates/showreel) cho vai trò hook/emphasis/closing. Chọn canvas 16:9 làm điểm xuất phát, thời lượng cảnh trong khoảng 8–15 giây rồi chốt theo lượng nội dung thực. Một ý chính, sức chứa 1 motif, 1 câu chủ đạo, 3 pha. Thay toàn bộ brand, copy, số liệu và media bằng dữ kiện được dự án cấp hoặc xác minh.

Thiết kế cụ thể: Đề xuất mới: một đường nét liên tục mở thành từ khóa, cuộn thành hình học rồi mở ra logo tự tạo. Dùng ba pha có tương phản tốc độ, một chủ thể qua các pha và khung chốt đọc được. Beat grid là tham số, không sao chép storyboard từng beat nguồn.

Nhịp dựng đề xuất:

1. Một đường nét mở ra từ khóa tự viết rồi giữ đủ để đọc.
2. Cùng đường nét cuộn thành hình học, đổi vai nhưng giữ anchor và màu nhận dạng.
3. Hình mở thành logo tự tạo cùng câu chốt; âm thanh kết ở cue đã chốt và hình giữ yên.

Giữ khung cuối tối thiểu 0,8 giây sau chuyển động cuối để đọc. Bố cục fullscreen; đặt chủ thể trong hộp đề xuất ở trên rồi kiểm theo canvas thật. Một composition cha và các clip con cho ba pha motif; GSAP paused điều khiển đường nét SVG, wrapper chữ và hình học. Dùng SVG paths/mask cho đường nối hoặc reveal, không ép toàn showreel thành một tween chữ. Cue nhạc được chuẩn bị trước và đặt cùng timeline; framework quản lý audio/video, không render hoặc mux bằng lệnh trong prompt nguồn. Đây là adapter đề xuất chưa chạy kiểm.

Hợp đồng dựng, tái bố cục dọc/vuông, font/media và kiểm chứng: [USAGE.md](../USAGE.md#hợp-đồng-triển-khai-hyperframes).

Ghi chú triển khai bổ sung: [release-enrichment.json](../source/release-enrichment.json), mã `template-showreel`.

## Liên quan / mức kiểm chứng

- [PM-template-realtime — The 3D template](template-realtime.md)
- [PM-antonio-kodheli-490109 — Prompt Motion site promo](antonio-kodheli-490109.md)

Metadata HTML: **đã thu**. Public prompt: **đã đọc toàn bộ**. Xem toàn video: **chưa**. Source code test: **chưa**. HyperFrames check/render: **chưa**. Prompt/media nguồn: **không archive**, chưa xác lập bulk redistribution license. [Cách dùng](../USAGE.md) · [Taxonomy](../TAXONOMY.md).
