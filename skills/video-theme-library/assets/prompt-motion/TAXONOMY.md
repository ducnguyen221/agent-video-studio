---
title: Prompt Motion reference taxonomy
summary: Independent dimensions for searching scene purpose, technique, pacing, screen area and adaptation requirements.
---

# Bộ lọc thư viện

Các trục độc lập giúp chọn theo công việc. Một motion có thể mang nhiều vai trò hoặc kỹ thuật; tên category của website được giữ riêng ở `source_facts`, không bị đổi thành đánh giá của Sol.

| Trục | Giá trị | Cách hiểu |
|---|---|---|
| `scene_roles` | `hook`, `explain`, `proof`, `emphasis`, `transition`, `closing`, `cta`, `ambient` | Cảnh làm việc gì cho câu chuyện; không chọn chỉ vì cùng màu |
| `coverage` | `fullscreen`, `partial`, `overlay` | Cách **đề xuất** đặt trong video mới: cả khung, vùng riêng có nền/bố cục, lớp phủ cần alpha |
| `techniques` | từ khoá mô tả như `typography`, `mask`, `stagger`, `morph`, `particles`, `3d`, `chart`, `ui`, `camera`, `path`, `glow` | Cơ chế chuyển động theo phân tích; không chứng minh thư viện/runtime nguồn |
| `intensity` | `low`, `medium`, `high` | Độ tranh giành chú ý; high dùng ngắn ở điểm nhấn, low phù hợp phụ trợ |
| `rhythm` | mô tả ngắn | Cấu trúc nhịp: hiện dần, bật rồi giữ, tuần tự, tăng tốc, sóng; không đoán BPM |
| `recommended_ratios` | `16:9`, `9:16`, `1:1` | Khung nên dựng; mỗi entry nói cách tái bố trí, không coi crop tự động là đủ |
| `primary_recommended_ratio` | `16:9`, `9:16`, `1:1` | Điểm xuất phát Sol ưu tiên cho bố cục mới; không xác nhận native aspect của nguồn |
| `ratio_fit` | `preferred`, `adaptable`, `requires_redesign`; effort `low`, `medium`, `high` | Mức thích hợp và công sức bố trí lại ở từng ratio; là đánh giá thiết kế, chưa benchmark |
| `content_capacity` | mô tả giới hạn | Số ý, số đối tượng, độ dài chữ **đề xuất** để đọc được; không phải hard limit nguồn |
| `recommended_region` | `x`, `y`, `width`, `height` trong `[0,1]` | Hộp bố cục đề xuất, gốc trên trái, theo toàn canvas; không phải tọa độ đo từ video nguồn |
| `recommended_occupancy` | `width × height`, hoặc mô tả/`unknown` | Phần diện tích hộp đề xuất; không phải số pixel thực tế có nội dung hoặc alpha |
| `source_dimensions` | số đo có bằng chứng hoặc `unknown` | Kích thước media nguồn, không phải kích thước CSS preview |
| `source_duration` | số đo có bằng chứng hoặc `unknown` | Thời lượng media; duration được nhắc trong brief nguồn phải giữ nhãn riêng |
| `runtime_tested` | `false` mặc định | Kho tham chiếu không chứng minh khả năng chạy/render của bản dựng mới |
| `entry_type` | `gallery_prompt`, `skill_reference`, `template_detail` | Trang gallery có thể giới thiệu skill thay cho prompt; repo link không đồng nghĩa skill đã được cài hoặc thử |
| `reading_scope` | `full_public_prompt`, `no_public_prompt` | Đã đọc toàn prompt công khai hoặc trang cung cấp skill thay cho prompt; không đồng nghĩa đã xem toàn video |

## ID và đường dẫn

ID có dạng `PM-<source-slug>`; file có cùng slug dưới `motions/`. ID dựa vào định danh nguồn, không đánh lại số khi website thay thứ tự. Đổi tiêu đề không tự đổi ID. Nếu URL nguồn đổi, giữ ID và cập nhật alias/provenance có chứng cứ. `related_ids` liên kết lựa chọn thay thế hoặc cảnh ghép được, không có nghĩa tác giả nguồn đã liên kết chúng.

## Độ chắc chắn

Mỗi entry phân biệt dữ kiện thu từ trang, quan sát preview, nội dung tác giả mô tả và đề xuất dựng lại. Một field không kiểm được để `unknown`, `null` hoặc diễn giải hạn chế rõ; không điền số cho đẹp schema. `verified` phải nói **đã kiểm điều gì**, không phải một nhãn PASS bao trùm.
