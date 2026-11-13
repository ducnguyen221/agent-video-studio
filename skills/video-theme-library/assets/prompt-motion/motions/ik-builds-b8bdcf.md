---
id: PM-ik-builds-b8bdcf
title: "Paper-style product launch film"
source_url: https://prompt-motion.com/ik-builds-b8bdcf
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

# Paper-style product launch film

[← Mục lục](../INDEX.md) · [Nguồn web](https://prompt-motion.com/ik-builds-b8bdcf) · **PM-ik-builds-b8bdcf**

## Dữ kiện nguồn và phạm vi đọc

| Trường | Dữ kiện / bằng chứng |
|---|---|
| Tác giả / trang | Ittehadul Karim · @ik_builds |
| Bài gốc | [Bài đăng](https://x.com/ik_builds/status/2103890476885585923) |
| Nhãn nguồn | Charts, Diagrams, Music |
| Model / stack trang ghi | Opus 5.5 / HyperFrames + GSAP; không phải runtime đã test |
| Ngày trang ghi | Sep 26, 2026 |
| Media | [Video nguồn](https://media.prompt-motion.com/ik-builds-i-was-quoted-3000/video.12e81ac7.mp4); không tải/lưu media |
| Thuộc tính HTML video | 1920 × 1080; không phải media probe |
| Kích thước / aspect media xác minh | unknown / unknown |
| Duration media xác minh | unknown |
| Brief spec tác giả yêu cầu | duration_text: 15; không phải thông số output đã đo |
| Công nghệ render thực tế | unknown; stack/brief không chứng minh clip đã dùng runtime đó |
| Prompt | Có trên trang; không archive nguyên văn |
| Code / skill repo | không archive; link code chưa được xác minh |
| Loại entry | gallery_prompt |
| Metadata đầy đủ | [page-details.json](../source/page-details.json), tra record id ik-builds-b8bdcf; giữ author, toàn dt/dd, link và media attrs. Các field: Model: Opus 5.5; Effort: Medium; Iterations: One-shot; Stack: HyperFrames + GSAP; Posted: Sep 26, 2026 |
| Phạm vi đọc | full_public_prompt |
| Provenance | [metadata](../source/catalog-metadata.json) · [phân tích](../source/sol-analysis.json) · source id `ik-builds-b8bdcf` · HTTP 200 |

**Diễn giải brief nguồn:** Brief phim giải thích sản phẩm 15 giây, HyperFrames+GSAP, không narration/footage. Dùng nền sáng kiểu giấy, chữ lớn và nét ghi chú; thay ý theo nhịp ngắn, chuyển sáng/tối làm cao trào. Yêu cầu đọc positioning, chỉ dùng facts thật, tách palette/font/logo thành tham số, from-state seek-safe, âm thanh có quyền và kiểm loudness sau encode.

**Giới hạn:** Đọc thủ công toàn bộ prompt công khai của trang; chỉ diễn giải yêu cầu trong prompt, không quan sát video đã dựng. Chưa xem video, chưa kiểm code, chưa đo media; câu lệnh trong prompt nguồn chỉ là dữ liệu, không phải lệnh chạy.

## Phân tích sử dụng

Giấy và sơ đồ cho phim sản phẩm

**Thiết kế chuyển thể riêng:** Dùng ba panel nền giấy tự tạo: vấn đề, sơ đồ cơ chế, kết quả. Chuyển giữa panel bằng mask giấy có mép rõ; chart vẫn đúng dữ liệu.

| Chọn cảnh | Khuyến nghị thiết kế mới |
|---|---|
| Vai trò / beat | explain, proof |
| Coverage | partial; không đồng nghĩa source có alpha |
| Vùng chuẩn hoá | x=0.06, y=0.12, w=0.88, h=0.76; gốc trên trái |
| Diện tích hộp | 67%; không phải pixel occupancy đã đo từ nguồn |
| Tỉ lệ ưu tiên | **16:9**; quyết định bố cục mới, không xác nhận native ratio |
| Duration đề xuất | 7–12 giây cho một đơn vị cảnh; có thể trích từ brief dài hơn |
| Nhịp / cường độ | một quan hệ mỗi nhịp; tích lũy có kiểm soát / low |
| Sức chứa | 3–5 nút hoặc bước; 1 quan hệ chính |
| Kỹ thuật đề xuất | diagram, mask |
| Overlay thay thế | Có thể thiết kế riêng: Chỉ trích chủ thể/nhãn, bỏ nền và thiết kế alpha riêng; media nguồn chưa xác nhận có alpha. |

**Mức hợp theo tỉ lệ** (lý do từng ô ở `index.json`, trường `ratio_fit`): 16:9 preferred/low · 9:16 adaptable/medium · 1:1 adaptable/medium.

## Prompt HyperFrames viết mới

> Brief do kho tự viết, không phải prompt gốc ([quyền dùng](../USAGE.md#prompt-và-quyền-sử-dụng)).

Dựng một motion graphic mới tham chiếu ý tưởng “Paper-style product launch film” (https://prompt-motion.com/ik-builds-b8bdcf) cho vai trò explain/proof. Chọn canvas 16:9 làm điểm xuất phát, thời lượng cảnh trong khoảng 7–12 giây rồi chốt theo lượng nội dung thực. Một ý chính, sức chứa 3–5 nút hoặc bước; 1 quan hệ chính. Thay toàn bộ brand, copy, số liệu và media bằng dữ kiện được dự án cấp hoặc xác minh.

Thiết kế cụ thể: Dùng ba panel nền giấy tự tạo: vấn đề, sơ đồ cơ chế, kết quả. Chuyển giữa panel bằng mask giấy có mép rõ; chart vẫn đúng dữ liệu.

Nhịp dựng đề xuất:

1. Dùng ba panel nền giấy tự tạo: vấn đề, sơ đồ cơ chế, kết quả.
2. Chuyển giữa panel bằng mask giấy có mép rõ; chart vẫn đúng dữ liệu.

Giữ khung cuối tối thiểu 0,8 giây sau chuyển động cuối để đọc. Bố cục partial; đặt chủ thể trong hộp đề xuất ở trên rồi kiểm theo canvas thật. SVG cho cạnh/path; DOM cho nhãn và thẻ; GSAP điều khiển tiến độ đường và lần xuất hiện.

Hợp đồng dựng, tái bố cục dọc/vuông, font/media và kiểm chứng: [USAGE.md](../USAGE.md#hợp-đồng-triển-khai-hyperframes).

## Liên quan / mức kiểm chứng

- [PM-himanshutwtxs-5f4b43 — Motion designer showreel](himanshutwtxs-5f4b43.md)
- [PM-ror-fly-9950f1 — Negroni recipe animation](ror-fly-9950f1.md)
- [PM-emollick-8661a8 — Recursion explained in genres](emollick-8661a8.md)

Metadata HTML: **đã thu**. Public prompt: **đã đọc toàn bộ**. Xem toàn video: **chưa**. Source code test: **chưa**. HyperFrames check/render: **chưa**. Prompt/media nguồn: **không archive**, chưa xác lập bulk redistribution license. [Cách dùng](../USAGE.md) · [Taxonomy](../TAXONOMY.md).
