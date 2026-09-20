---
title: Theme library
summary: Reusable layout patterns for news, deep-dive, short-form and teaching videos, with the hard rendering rules that make a render correct rather than merely pretty.
audience: agents and humans composing a new video or slide
---

# Thư viện template — chọn layout trước khi sáng tác

> **Cách dùng (bắt buộc đọc trước khi dựng một video/slide mới):**
> 1. Xác định TỪNG đoạn nội dung làm việc gì → tra **bảng chọn nhanh** (§1) → lấy template của
>    nhóm tương ứng, đúng tỉ lệ khung.
> 2. **Chọn từ thư viện TRƯỚC, sáng tác SAU.** Buộc phải chế cái mới thì làm xong phải thêm vào
>    file này (kèm nguồn code) — cùng lượt việc, không để nợ.
> 3. Tier: **S** = đã dựng, đã chạy thật, ưu tiên · **A** = đã dựng, ổn định · **B** = đời cũ,
>    cân nhắc · **NEW** = mới có mô tả giải phẫu, **chưa có code**.
> 4. §6 là **luật cứng**: vi phạm là video hỏng, không phải video xấu.
>
> Nguồn: chưng cất từ bộ template bản tin của chính repo này (`video_studio/templates/news/`) và
> từ các đợt dựng video thật. Tên thương hiệu, tên miền, profile giọng **không nằm ở đây** —
> chúng là dữ liệu của spec, xem `docs/CONTRACT.md`.

## 1. Bảng chọn nhanh (việc → nhóm → template)

| Đoạn nội dung là… | Nhóm | Chọn (16:9) | Chọn (9:16) |
|---|---|---|---|
| Mở màn / hook | §2 | `cover-long` (S) | `hook-orb-badge` (S) · `cover-short` (A) |
| Con số chủ đạo (giá, %, tốc độ) | §3 | `stat-callout` (S) · `stats-grid` (S) | `bignum` (S) · `arc-gauge` (NEW) |
| N điểm / tính năng / lý do | §4 | `pillars` (S) · `bullets-cards` (S) | `bullets-cards` (S) · `tags-pills` (A) |
| Quy trình / lộ trình / chuỗi sự kiện | §4 | `flow` (S) · `timeline` (A) | `process-chips` (S) · `orbit-loop` (NEW) |
| A đối đầu B | §5 | `versus` (S) | `versus` (S) · `racing-dots` (NEW) · `screenshot-vs` (NEW) |
| Xếp hạng / điểm số | §3 | `bars` (S) | `bars` (S) |
| Phát ngôn / nhận định | §4 | `quote` (S) | `quote` (S) |
| Demo sản phẩm / clip nguồn | §7 | `clip-embed` (S) · `hero` Ken-Burns (S) | `hero-fill` + clip (S) |
| Mặt trái / lưu ý / rủi ro | §8 | thẻ số màu cảnh báo | `warning-chips` (S) |
| Chốt hạ / đánh giá cuối | §8 | outro + câu chốt | `verdict-stamp` (S) |
| Kết + kêu gọi | §2 | `outro-long` (S) | `outro-short` (S) |

## 2. Mở màn / hook / kết

| ID · Tier | Giải phẫu | Chuyển động |
|---|---|---|
| **cover-long · S** | pill nhãn + tiêu đề ~150px + dòng phụ (ngày/nguồn); nền lưới trôi + 2 quầng sáng mờ | tiêu đề `fromTo` y:40→0, `power3.out` |
| **cover-weekly · A** | tên số báo khổng lồ ~192px (hai màu nhấn) + tagline + khoảng thời gian | fade theo đoạn |
| **cover-short · A** | khung dọc, chữ lớn ~108px + thanh tiến độ | fade + trượt |
| **hook-orb-badge · S** | ảnh đại diện chủ đề trong quầng sáng + vòng tròn, kèm **huy hiệu nổi** mang một con số ấn tượng | quầng `scale-in` `power2`, huy hiệu `pop` `back.out(2)` |
| **outro-long / short · S** | dòng kết lớn + dòng phụ + địa chỉ trang | fade |

## 3. Số liệu

| ID · Tier | Giải phẫu | Chuyển động |
|---|---|---|
| **stat-callout · S** | pill nhãn + tiêu đề gradient ~84px + **một số khổng lồ ~150px** + nhãn + các hàng thông số (icon · nhãn · giá trị, mỗi hàng một màu nhấn) | số `scale-in`, các hàng `stagger` |
| **stats-grid · S** | lưới 2×N thẻ số ~52px (font tabular) + nhãn | `stagger` fade theo nhịp lời dẫn |
| **bignum · S** | đúng một số ~188px + nhãn (khung dọc) | `pop-in` |
| **bars · S** | biểu đồ cột bằng CSS thuần (tên + % + màu) | tween chiều rộng theo nhịp |
| **arc-gauge · NEW** | đồng hồ cung tròn + kim + hai "quầng số" hai bên nối bằng chuỗi chấm chạy | cung quét, chấm chạy **hữu hạn**, số đếm lên |

## 4. Cấu trúc: trụ / quy trình / trích dẫn

| ID · Tier | Giải phẫu | Chuyển động |
|---|---|---|
| **pillars · S** | 3–4 thẻ dọc: icon + tiêu đề + mô tả (thay cho bullet dài) | `stagger` theo `[data-card]` |
| **bullets-cards · S** | thẻ đánh số, badge gradient, bullet có nền | hiện theo nhịp lời dẫn |
| **flow · S** | các bước đánh số theo chiều dọc, mũi tên ▼, thẻ viền trái màu nhấn | từng bước theo nhịp |
| **process-chips · S** | chip ngang nối bằng → (khung dọc) | chip trượt lên, gợn sóng |
| **stack · A** | các tầng xếp chồng, viền trái xen kẽ hai màu nhấn | `stagger` |
| **tags-pills · A** | pill bo tròn xoay vòng ba màu | `pop` `stagger` |
| **quote · S** | trích dẫn lớn, viền trái màu nhấn + tên người nói | fade + trượt |
| **orbit-loop · NEW** | vòng tròn trung tâm (khái niệm lõi) + các node vệ tinh quanh nó + pill kết quả phía dưới | node lần lượt sáng theo nhịp; **quỹ đạo đứng yên** — đừng quay vô hạn |

## 5. So sánh

| ID · Tier | Giải phẫu | Chuyển động |
|---|---|---|
| **versus · S** | hai cột thuộc tính + badge **VS** ở giữa | hai cột trượt vào từ hai phía |
| **racing-dots · NEW** | hai hàng chấm tiến độ chạy đua (A trên, B dưới) + chip mốc thời gian | hàng thắng chạy nhanh hơn **rõ rệt** — trực quan hoá tốc độ thay vì nói bằng chữ |
| **screenshot-vs · NEW** | hai cửa sổ ứng dụng/terminal thật cạnh nhau trong khung thiết bị + tiêu đề đối đầu | ảnh chụp fade vào, viền bên thắng phát sáng |

## 6. LUẬT CỨNG khi render (vi phạm = video hỏng)

1. **Cấm `repeat: -1`** (lặp vô hạn của GSAP) — tiến trình render phình tới khi chết. Mọi vòng
   lặp tính số lần hữu hạn từ tổng thời lượng.
2. **Phải tái lập được:** không `Date.now()`, không `Math.random()`, không `requestAnimationFrame`
   tự chạy, không hiệu ứng theo chuột. Mỗi phần tử định thời có `data-start` / `data-duration` /
   `data-track-index`; timeline `paused` đăng ký vào `window.__timelines["<id>"]`.
3. **ffmpeg:** nền lặp thì nối bằng **concat demuxer + `-c copy`**, KHÔNG `-stream_loop` (lỗi
   ngẫu nhiên); đốt phụ đề libass là một lượt riêng; đường trong filtergraph dùng **đường tương
   đối tính từ cwd** — dấu `:` của ổ đĩa Windows làm vỡ bộ phân tích filtergraph.
4. **Giọng đọc: luôn ghim một profile** (`voice.profile` trong spec), cấm lùi về chế độ
   `instruct` — chế độ đó bốc một giọng khác cho mỗi câu. Tốc độ lời dẫn ~3,2 từ/giây; lời dẫn
   **giảng giải**, không đọc nguyên văn bullet đang hiện trên màn.
5. **Bản công khai không nhắc tên công cụ nội bộ.** Người xem cần biết nội dung, không cần biết
   engine nào dựng ra nó.
6. **Phụ đề karaoke mức từ cho CẢ khung ngang lẫn khung dọc**; dòng ~5 từ hiện dần theo lời; tự
   động tô **vàng** các từ khoá (số liệu, %, chữ in hoa, tên công nghệ). Thanh transcript cả đoạn
   chỉ là đường lùi khi bóc lời hỏng.
7. **Ảnh trong khung dọc dùng `object-fit: contain`** trên nền panel — `cover` cắt mất chữ trong
   ảnh chụp màn hình và ảnh OG.
8. **Slide giảng dạy:** một ý lớn mỗi slide, lấp đầy khung (trống nửa dưới là lỗi), sửa đúng slot
   `data-edit` / `data-item`.

## 7. Media / hero / b-roll

- **hero Ken-Burns · S** — ảnh panel fade + phóng 1 → 1.06 rồi nhường chỗ cho sơ đồ.
- **clip-embed · S** — `<video data-start/duration/track-index>` co theo khung của section.
- **b-roll đường lùi · S** — không có ảnh thì dùng filler tại máy theo thương hiệu; đừng để trống.
- **image-split · A** — chữ bên trái + thẻ ảnh 16:10 bên phải + chú thích.
- Quy tắc chung: **tối đa 1–2 ảnh liên quan nhất cho mỗi đoạn**; ảnh là điểm nhấn, phần còn lại
  là đồ hoạ thông tin.

## 8. Kết luận / cảnh báo

| ID · Tier | Giải phẫu | Ghi chú |
|---|---|---|
| **warning-chips · S** | hàng chip màu hổ phách ⚠, mỗi lưu ý ≤ 6 từ | video đánh giá **bắt buộc** có mục này |
| **verdict-stamp · S** | thẻ chốt phát sáng + câu đánh giá + dòng phụ, hiện ở đoạn kết | CSS phải khớp đúng selector của cover, nếu không thẻ hiện ra ngoài khung |

## 9. Bốn hệ màu (chọn MỘT, không trộn)

| Hệ | Nền | Màu nhấn | Font | Dùng cho |
|---|---|---|---|---|
| **v2 (mặc định cho video mới)** | radial `#15203a` → `#070a12` + lưới + quầng sáng | cyan `#00E5FF` · tím `#A78BFA` · lục `#00E676` · vàng `#FFC857` · panel `#161620` | Inter | deep-dive, video mới |
| v1 "dữ liệu" | radial `#101a33` → `#04060a` | `#00f0ff` · `#bd00ff` · `#39ff7a` · `#ffd166` | Inter (trước đây là font hệ thống) | bản tin tuần đã có nhận diện riêng |
| Giảng dạy | nền sáng `#f3f6fb`, bìa navy `#0e1b34` | `#4472C4` · `#ED7D31` · `#FFC000` · `#70AD47` · `#00B0F0` | Calibri/Inter | slide + video bài giảng |
| Kể chuyện | ảnh nền theo chủ đề | lửa `#FF4500`/`#FF9A2A` · chữ vàng `#FFE38A` | font đậm, chân phương | audiobook / kể chuyện |

Màu nhấn của một số báo cụ thể đi qua `brand.accent` trong spec, không sửa vào file này.

## 10. Còn nợ

1. Năm pattern đang ở tier `NEW` cần code: `arc-gauge` → `racing-dots` → `screenshot-vs` →
   `orbit-loop` (thứ tự ưu tiên).
2. Template deep-dive nhiều cảnh còn một chỗ lặp vô hạn trong mã đời cũ — sửa trước khi tái dùng
   bất kỳ đoạn nào từ đó (xem luật §6.1).
3. Bộ bản tin tuần (hệ v1) nâng dần sang hệ v2, giữ riêng màu nhận diện.
