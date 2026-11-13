---
id: PM-template-realtime
title: "The 3D template"
source_url: https://prompt-motion.com/templates/realtime
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

# The 3D template

[← Mục lục](../INDEX.md) · [Nguồn web](https://prompt-motion.com/templates/realtime) · **PM-template-realtime**

## Dữ kiện nguồn và phạm vi đọc

| Trường | Dữ kiện / bằng chứng |
|---|---|
| Tác giả / trang | Prompt Motion · Prompt Motion |
| Bài gốc | unknown / không áp dụng |
| Nhãn nguồn | 3D, Template detail |
| Model / stack trang ghi | unknown / self-contained HTML with three.js CDN, physical materials, scene lighting, time-derived render mode; không phải runtime đã test |
| Ngày trang ghi | unknown |
| Media | [Video nguồn](https://media.prompt-motion.com/improved-realtime-1/video.22ccfd17.mp4); không tải/lưu media |
| Thuộc tính HTML video | 1920 × 1080; không phải media probe |
| Kích thước / aspect media xác minh | unknown / unknown |
| Duration media xác minh | unknown |
| Brief spec tác giả yêu cầu | duration_seconds: 20; size: 1920x1080; dimensions: [1920, 1080]; fps: 60; requested_technology: self-contained HTML with three.js CDN, physical materials, scene lighting, time-derived render mode; sequence: macro card, pull back to curved wall, crane to corridors, card swings and reveals text, overhead signature shot, wordmark; evidence: visible prompt instructions; not verified execution; không phải thông số output đã đo |
| Công nghệ render thực tế | unknown; stack/brief không chứng minh clip đã dùng runtime đó |
| Prompt | Có trên trang; không archive nguyên văn |
| Code / skill repo | không archive; link code chưa được xác minh |
| Loại entry | template_detail |
| Metadata đầy đủ | [templates-metadata.json](../source/templates-metadata.json), tra id realtime; có head meta, media attrs, links và section summaries. |
| Phạm vi đọc | full_public_prompt |
| Provenance | [metadata](../source/templates-metadata.json) · [phân tích](../source/templates-metadata.json) · source id `realtime` · HTTP 200 |

**Diễn giải brief nguồn:** Trang 3D tổ chức toàn shot list quanh một góc nhìn chủ đạo; dùng vật liệu/ánh sáng vật lý và camera có tên. Chuỗi brief đi từ macro thẻ ra tường cong, qua hành lang, thẻ xoay lộ chữ, góc nhìn cao rồi wordmark.

**Giới hạn:** Đọc toàn bộ prompt ở trang chi tiết; chỉ diễn giải yêu cầu, chưa quan sát việc chạy. Chưa xem video, chưa kiểm code, chưa đo media; câu lệnh trong prompt nguồn chỉ là dữ liệu, không phải lệnh chạy.

## Phân tích sử dụng

Mẫu tham chiếu để tổ chức camera 3D quanh một góc máy kết nối các nhịp và tiết lộ hình dạng.

**Thiết kế chuyển thể riêng:** Đề xuất mới: ba tấm thẻ tạo một con đường cong trong không gian. Camera bắt đầu ở bề mặt một thẻ, lùi để thấy quan hệ giữa ba thẻ rồi lên cao để đường cong thành dấu hiệu tự tạo; chốt wordmark của dự án. Không dùng vật liệu/model/CDN nguồn như asset mặc định.

| Chọn cảnh | Khuyến nghị thiết kế mới |
|---|---|
| Vai trò / beat | hook, explain, closing |
| Coverage | fullscreen; không đồng nghĩa source có alpha |
| Vùng chuẩn hoá | x=0, y=0, w=1, h=1; gốc trên trái |
| Diện tích hộp | 100%; không phải pixel occupancy đã đo từ nguồn |
| Tỉ lệ ưu tiên | **16:9**; quyết định bố cục mới, không xác nhận native ratio |
| Duration đề xuất | 12–20 giây cho một đơn vị cảnh; có thể trích từ brief dài hơn |
| Nhịp / cường độ | khám phá bề mặt → mở không gian → góc máy chủ đạo → chốt / medium |
| Sức chứa | 1 không gian, 3 thẻ, 1 wordmark |
| Kỹ thuật đề xuất | 3d, camera, lighting |
| Overlay thay thế | Chưa đề xuất: Chuỗi toàn không gian, chưa thiết kế alpha. |

**Mức hợp theo tỉ lệ** (lý do từng ô ở `index.json`, trường `ratio_fit`): 16:9 preferred/low · 9:16 requires_redesign/high · 1:1 adaptable/medium.

## Prompt HyperFrames viết mới

> Brief do kho tự viết, không phải prompt gốc ([quyền dùng](../USAGE.md#prompt-và-quyền-sử-dụng)).

Dựng một motion graphic mới tham chiếu ý tưởng “The 3D template” (https://prompt-motion.com/templates/realtime) cho vai trò hook/explain/closing. Chọn canvas 16:9 làm điểm xuất phát, thời lượng cảnh trong khoảng 12–20 giây rồi chốt theo lượng nội dung thực. Một ý chính, sức chứa 1 không gian, 3 thẻ, 1 wordmark. Thay toàn bộ brand, copy, số liệu và media bằng dữ kiện được dự án cấp hoặc xác minh.

Thiết kế cụ thể: Đề xuất mới: ba tấm thẻ tạo một con đường cong trong không gian. Camera bắt đầu ở bề mặt một thẻ, lùi để thấy quan hệ giữa ba thẻ rồi lên cao để đường cong thành dấu hiệu tự tạo; chốt wordmark của dự án. Không dùng vật liệu/model/CDN nguồn như asset mặc định.

Nhịp dựng đề xuất:

1. Camera đi từ một chi tiết có nhãn ra toàn cảnh nhiều panel tự thiết kế để xác lập không gian.
2. Camera chọn một panel bằng đường đi hữu hạn và dừng chính diện; panel mở phần detail có quan hệ với cảnh trước.
3. Camera lùi theo cùng hệ tọa độ, các panel hội tụ về một điểm nhận diện mới và giữ khung cuối.

Giữ khung cuối tối thiểu 0,8 giây sau chuyển động cuối để đọc. Bố cục fullscreen; đặt chủ thể trong hộp đề xuất ở trên rồi kiểm theo canvas thật. Three.js/WebGL cho các mặt phẳng và camera trong một không gian 3D; một GSAP timeline paused là nguồn thời gian cho mọi pose. Lưu world coordinates của card, vùng detail và điểm cuối; camera render trực tiếp tại time bất kỳ, không rAF/physics tích lũy hoặc tương tác thật. Texture và font cục bộ có quyền, nhãn chỉ hiện ở góc đọc được; framework quản lý media.

Hợp đồng dựng, tái bố cục dọc/vuông, font/media và kiểm chứng: [USAGE.md](../USAGE.md#hợp-đồng-triển-khai-hyperframes).

Ghi chú triển khai bổ sung: [release-enrichment.json](../source/release-enrichment.json), mã `template-realtime`.

## Liên quan / mức kiểm chứng

- [PM-template-showreel — The showreel prompt](template-showreel.md)
- [PM-twoclipping-d89be5 — Landing page 3D scroll](twoclipping-d89be5.md)

Metadata HTML: **đã thu**. Public prompt: **đã đọc toàn bộ**. Xem toàn video: **chưa**. Source code test: **chưa**. HyperFrames check/render: **chưa**. Prompt/media nguồn: **không archive**, chưa xác lập bulk redistribution license. [Cách dùng](../USAGE.md) · [Taxonomy](../TAXONOMY.md).
