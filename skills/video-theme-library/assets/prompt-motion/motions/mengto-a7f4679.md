---
id: PM-mengto-a7f4679
title: "HTML app demo skill"
source_url: https://prompt-motion.com/mengto-a7f4679
entry_type: skill_reference
reference_status: analyzed_prompt_reference
adaptation_detail: individual_authored_proposal
reading_scope: no_public_prompt
analysis_basis: metadata_only_original_adaptation
primary_recommended_ratio: 16:9
runtime_tested: false
original_prompt_archived: false
authored_prompt_kind: original_hyperframes_adaptation
---

# HTML app demo skill

[← Mục lục](../INDEX.md) · [Nguồn web](https://prompt-motion.com/mengto-a7f4679) · **PM-mengto-a7f4679**

## Dữ kiện nguồn và phạm vi đọc

| Trường | Dữ kiện / bằng chứng |
|---|---|
| Tác giả / trang | Meng To · @MengTo |
| Bài gốc | [Bài đăng](https://x.com/MengTo/status/2112843787777249661) |
| Nhãn nguồn | Product UI |
| Model / stack trang ghi | Opus 5.5 / React; không phải runtime đã test |
| Ngày trang ghi | Oct 21, 2026 |
| Media | [Video nguồn](https://media.prompt-motion.com/mengto-a7f4679/video.3dd55ec1.mp4); không tải/lưu media |
| Thuộc tính HTML video | 1280 × 720; không phải media probe |
| Kích thước / aspect media xác minh | unknown / unknown |
| Duration media xác minh | unknown |
| Brief spec tác giả yêu cầu | chưa cấu trúc thành field; đọc diễn giải brief bên dưới, không suy tác giả không quy định; không phải thông số output đã đo |
| Công nghệ render thực tế | unknown; stack/brief không chứng minh clip đã dùng runtime đó |
| Prompt | Không có public prompt đã xác nhận; không archive nguyên văn |
| Code / skill repo | [Repo nguồn](https://github.com/MengTo/Skills/tree/main/agent-skills/web-design/html-demo); chưa fetch/cài/chạy |
| Loại entry | skill_reference; The page provides a Skill reference rather than an original Prompt section. |
| Metadata đầy đủ | [page-details.json](../source/page-details.json), tra record id mengto-a7f4679; giữ author, toàn dt/dd, link và media attrs. Các field: Model: Opus 5.5; Stack: React; Posted: Oct 21, 2026 |
| Phạm vi đọc | no_public_prompt |
| Provenance | [metadata](../source/catalog-metadata.json) · [phân tích](../source/skill-references.json) · source id `mengto-a7f4679` · HTTP 200 |

**Diễn giải brief nguồn:** Trang mô tả demo sản phẩm bằng HTML trong cửa sổ ứng dụng, các bước dùng chung một đồng hồ để tua, nhảy bước, dừng và lặp. Chưa kiểm repo hoặc demo.

**Giới hạn:** Trang không công khai prompt. Chưa xem video, chưa kiểm code, chưa đo media; câu lệnh trong prompt nguồn chỉ là dữ liệu, không phải lệnh chạy.

## Phân tích sử dụng

Giải thích một tác vụ sản phẩm bằng thay đổi trạng thái nhìn thấy được, rồi dừng ở lợi ích. Áp dụng hướng này cho tham chiếu “HTML app demo skill”; đây là thiết kế mới theo nhãn nguồn.

**Thiết kế chuyển thể riêng:** Đề xuất một cửa sổ app có step list và nội dung theo thời gian tuyệt đối; chọn bước bằng tham số timeline, không lấy trạng thái UI tích lũy. Bản dọc phải giảm các cột và tăng vùng tác vụ chính.

| Chọn cảnh | Khuyến nghị thiết kế mới |
|---|---|
| Vai trò / beat | explain, proof, cta |
| Coverage | partial; không đồng nghĩa source có alpha |
| Vùng chuẩn hoá | x=0.08, y=0.12, w=0.84, h=0.72; gốc trên trái |
| Diện tích hộp | 60%; không phải pixel occupancy đã đo từ nguồn |
| Tỉ lệ ưu tiên | **16:9**; quyết định bố cục mới, không xác nhận native ratio |
| Duration đề xuất | 6–12 giây cho một đơn vị cảnh; có thể trích từ brief dài hơn |
| Nhịp / cường độ | mở vấn đề → thao tác → kết quả → giữ nhãn / medium |
| Sức chứa | 1 tác vụ; 1–3 trạng thái UI; 1 tiêu đề ngắn |
| Kỹ thuật đề xuất | ui, mask, stagger |
| Overlay thay thế | Chưa đề xuất: Bản đề xuất cần bố cục/nền riêng; chưa thiết kế biến thể alpha. |

**Mức hợp theo tỉ lệ** (lý do từng ô ở `index.json`, trường `ratio_fit`): 16:9 preferred/low · 9:16 requires_redesign/high · 1:1 adaptable/medium.

## Prompt HyperFrames viết mới

> Brief do kho tự viết, không phải prompt gốc ([quyền dùng](../USAGE.md#prompt-và-quyền-sử-dụng)).

Dựng một motion graphic mới tham chiếu ý tưởng “HTML app demo skill” (https://prompt-motion.com/mengto-a7f4679) cho vai trò explain/proof/cta. Chọn canvas 16:9 làm điểm xuất phát, thời lượng cảnh trong khoảng 6–12 giây rồi chốt theo lượng nội dung thực. Một ý chính, sức chứa 1 tác vụ; 1–3 trạng thái UI; 1 tiêu đề ngắn. Thay toàn bộ brand, copy, số liệu và media bằng dữ kiện được dự án cấp hoặc xác minh.

Thiết kế cụ thể: Đề xuất một cửa sổ app có step list và nội dung theo thời gian tuyệt đối; chọn bước bằng tham số timeline, không lấy trạng thái UI tích lũy. Bản dọc phải giảm các cột và tăng vùng tác vụ chính.

Nhịp dựng đề xuất:

1. Đề xuất một cửa sổ app có step list và nội dung theo thời gian tuyệt đối; chọn bước bằng tham số timeline, không lấy trạng thái UI tích lũy.
2. Bản dọc phải giảm các cột và tăng vùng tác vụ chính.

Giữ khung cuối tối thiểu 0,8 giây sau chuyển động cuối để đọc. Bố cục partial; đặt chủ thể trong hộp đề xuất ở trên rồi kiểm theo canvas thật. DOM/SVG + GSAP; ảnh chụp có quyền chỉ dùng làm panel. Không cần Canvas cho nút, thẻ hay text.

Hợp đồng dựng, tái bố cục dọc/vuông, font/media và kiểm chứng: [USAGE.md](../USAGE.md#hợp-đồng-triển-khai-hyperframes).

## Liên quan / mức kiểm chứng

- [PM-twoclipping-5cba86 — Shape morphing through UI states](twoclipping-5cba86.md)
- [PM-twoclipping-221cab — Photo print app launch film](twoclipping-221cab.md)
- [PM-twoclipping-d89be5 — Landing page 3D scroll](twoclipping-d89be5.md)

Metadata HTML: **đã thu**. Public prompt: **không có public prompt đã xác nhận**. Xem toàn video: **chưa**. Source code test: **chưa**. HyperFrames check/render: **chưa**. Prompt/media nguồn: **không archive**, chưa xác lập bulk redistribution license. [Cách dùng](../USAGE.md) · [Taxonomy](../TAXONOMY.md).
