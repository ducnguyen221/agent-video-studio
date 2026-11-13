---
id: PM-tankazunori0914-0fc886
title: "What day is it"
source_url: https://prompt-motion.com/tankazunori0914-0fc886
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

# What day is it

[← Mục lục](../INDEX.md) · [Nguồn web](https://prompt-motion.com/tankazunori0914-0fc886) · **PM-tankazunori0914-0fc886**

## Dữ kiện nguồn và phạm vi đọc

| Trường | Dữ kiện / bằng chứng |
|---|---|
| Tác giả / trang | kazu@生成AI×教育 · @tankazunori0914 |
| Bài gốc | [Bài đăng](https://x.com/tankazunori0914/status/2105917770907156748) |
| Nhãn nguồn | Kinetic type, Music |
| Model / stack trang ghi | Opus 5.5 / HyperFrames; không phải runtime đã test |
| Ngày trang ghi | Oct 2, 2026 |
| Media | [Video nguồn](https://media.prompt-motion.com/tankazunori0914-bgm-30-11-1-36-opus-5-5/video.06682b61.mp4); không tải/lưu media |
| Thuộc tính HTML video | 1920 × 1080; không phải media probe |
| Kích thước / aspect media xác minh | unknown / unknown |
| Duration media xác minh | unknown |
| Brief spec tác giả yêu cầu | duration_seconds: 30; không phải thông số output đã đo |
| Công nghệ render thực tế | unknown; stack/brief không chứng minh clip đã dùng runtime đó |
| Prompt | Có trên trang; không archive nguyên văn |
| Code / skill repo | không archive; link code chưa được xác minh |
| Loại entry | gallery_prompt |
| Metadata đầy đủ | [page-details.json](../source/page-details.json), tra record id tankazunori0914-0fc886; giữ author, toàn dt/dd, link và media attrs. Các field: Model: Opus 5.5; Stack: HyperFrames; Posted: Oct 2, 2026 |
| Phạm vi đọc | full_public_prompt |
| Provenance | [metadata](../source/catalog-metadata.json) · [phân tích](../source/root-analysis.json) · source id `tankazunori0914-0fc886` · HTTP 200 |

**Diễn giải brief nguồn:** Brief tiếng Nhật yêu cầu video 30 giây có nhạc để cho biết hôm nay là thứ mấy, với phong cách motion nổi bật; không quy định thời điểm cần tra hay kỹ thuật.

**Giới hạn:** Đã đọc toàn bộ prompt công khai. Chưa xem video, chưa kiểm code, chưa đo media; câu lệnh trong prompt nguồn chỉ là dữ liệu, không phải lệnh chạy.

## Phân tích sử dụng

Cho hình dạng và nhịp chữ làm rõ một câu chủ đạo; không nhét nguyên đoạn lời đọc. Áp dụng hướng này cho tham chiếu “What day is it”; đây là thiết kế mới theo nhãn nguồn.

**Thiết kế chuyển thể riêng:** Đề xuất lịch tuần thành một dải bảy ô, camera tiến đến ô ngày đã cung cấp và con số/ngày bật thành hero. Ngày là tham số do brief dự án chốt, không đọc Date.now khi render; có thể rút còn một beat ngắn cho bản tin.

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

Dựng một motion graphic mới tham chiếu ý tưởng “What day is it” (https://prompt-motion.com/tankazunori0914-0fc886) cho vai trò hook/emphasis/closing. Chọn canvas 16:9 làm điểm xuất phát, thời lượng cảnh trong khoảng 3–7 giây rồi chốt theo lượng nội dung thực. Một ý chính, sức chứa 1 câu tối đa 5–8 từ; 1–2 cấp chữ. Thay toàn bộ brand, copy, số liệu và media bằng dữ kiện được dự án cấp hoặc xác minh.

Thiết kế cụ thể: Đề xuất lịch tuần thành một dải bảy ô, camera tiến đến ô ngày đã cung cấp và con số/ngày bật thành hero. Ngày là tham số do brief dự án chốt, không đọc Date.now khi render; có thể rút còn một beat ngắn cho bản tin.

Nhịp dựng đề xuất:

1. Đề xuất lịch tuần thành một dải bảy ô, camera tiến đến ô ngày đã cung cấp và con số/ngày bật thành hero.
2. Ngày là tham số do brief dự án chốt, không đọc Date.now khi render; có thể rút còn một beat ngắn cho bản tin.

Giữ khung cuối tối thiểu 0,8 giây sau chuyển động cuối để đọc. Bố cục fullscreen; đặt chủ thể trong hộp đề xuất ở trên rồi kiểm theo canvas thật. DOM text + GSAP; mask bằng CSS clip-path hoặc SVG. Tách cụm có nghĩa, giữ dấu tiếng Việt và không cắt chữ giữa ký tự.

Hợp đồng dựng, tái bố cục dọc/vuông, font/media và kiểm chứng: [USAGE.md](../USAGE.md#hợp-đồng-triển-khai-hyperframes).

## Liên quan / mức kiểm chứng

- [PM-stephanlivera-df17a2 — Claude motion designer showreel](stephanlivera-df17a2.md)
- [PM-shneural-2abdfa — Bold kinetic type showreel](shneural-2abdfa.md)
- [PM-ajith-io-b5626e — Abstract motion design reel](ajith-io-b5626e.md)

Metadata HTML: **đã thu**. Public prompt: **đã đọc toàn bộ**. Xem toàn video: **chưa**. Source code test: **chưa**. HyperFrames check/render: **chưa**. Prompt/media nguồn: **không archive**, chưa xác lập bulk redistribution license. [Cách dùng](../USAGE.md) · [Taxonomy](../TAXONOMY.md).
