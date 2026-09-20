---
name: product-launch-video
description: Turn a product or marketing URL, a pasted script, or a brief into a product launch or promo video - SaaS promos, feature reveals, product demos, app and company launches. Use when the user wants to market, launch, promote or reveal a product; this is the default for any commercial URL. Site tours and website showcases route here too. Not a topic explainer without a product (faceless-explainer) and not a code-change video (pr-to-video).
---

# Video ra mắt sản phẩm

> **Nguồn:** `heygen-com/hyperframes` · `skills/product-launch-video/SKILL.md` @ **v0.8.51** ·
> Apache-2.0 · hash manifest `ced501f76c52716b` (30 file upstream).
> Bản này **đã dịch, rút gọn và biên tập lại** (Apache-2.0 §4(b)); `references/*` không chép vào repo.

Đầu vào là một **URL sản phẩm**, một kịch bản dán vào, hoặc một brief. Đây là đường mặc định cho
mọi URL thương mại — kể cả khi người dùng chỉ nói "quay lại trang này cho tôi xem".

## Bảy bước

0. **Dựng project**, chốt khung hình và thời lượng mục tiêu.
1. **Chụp tài sản từ trang.** Ảnh chụp giao diện, logo, màu thương hiệu, chữ trên trang. Đây là
   bước duy nhất có gọi mạng — và là bước phải kiểm kỹ: trang tải chậm cho ra ảnh chụp trắng.
2. **Hệ thiết kế** rút từ chính trang đó: màu lấy từ token của trang, chữ chọn cho gần bộ chữ của
   họ. Video không được trông như của một thương hiệu khác.
3. **Bảng phân cảnh và lời đọc** theo cấu trúc quen: vấn đề → sản phẩm → 2–3 điểm mạnh → chứng cứ
   → lời mời hành động.
   3.1 **Âm thanh** chốt ở đây; nhịp cắt bám theo độ dài lời đọc thật.
4. **Thiết kế từng khung.**
5. **Dựng khung** — tra kho trước khi tự viết hiệu ứng.
6. **Chốt:** `check` → `preview` → người duyệt → `render`.

## Luật riêng của thể loại này

- **Không hứa hộ sản phẩm.** Chỉ nói thứ có trên trang hoặc trong brief. Một câu quảng cáo bịa ra
  là một câu người khác phải chịu trách nhiệm.
- **Ảnh chụp giao diện phải là giao diện thật**, không phải bản dựng lại cho đẹp. Dựng lại thì phải
  nói rõ với người dùng.
- **Logo và màu thương hiệu không tự sửa.** Đổi tỉ lệ logo, đổi màu cho "hợp nền" là chỗ bị bắt lỗi
  nhiều nhất khi bàn giao.
- **Lời mời hành động cuối phải đúng đường thật** — tên miền, nút bấm, chữ trên nút. Sai một chữ là
  cả video mất tác dụng.

## Mở màn

Ba giây đầu nói **sản phẩm làm được gì cho người xem**, không nói tên công ty. Tên công ty để ở
cảnh cuối cùng với lời mời hành động.
