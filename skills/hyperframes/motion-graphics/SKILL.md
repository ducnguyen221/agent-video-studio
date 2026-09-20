---
name: motion-graphics
description: A short design-led motion graphic where motion is the message - kinetic typography, stat count-up, chart or data-viz hit, logo sting and brand lockup, lower-third, callout or social overlay, animated map, animated tweet or headline, webpage and UI animation, or fusing a real image's geometry into a chart. Usually under 10 seconds and up to about 30, no narration and no live-action subject; renders to MP4 or to a transparent overlay. Longer, narrated or multi-scene pieces belong to general-video.
---

# Motion graphic ngắn: chuyển động chính là nội dung

> **Nguồn:** `heygen-com/hyperframes` · `skills/motion-graphics/SKILL.md` @ **v0.8.51** ·
> Apache-2.0 · hash manifest `32641ae2b94c4a8f` (23 file upstream).
> Bản này **đã dịch, rút gọn và biên tập lại** (Apache-2.0 §4(b)); các module theo thể loại của
> upstream không chép vào repo.

Đơn vị ngắn, thường dưới 10 giây (tối đa khoảng 30), **không lời đọc**, không người thật. Đầu ra là
MP4 hoặc lớp phủ trong suốt để chồng lên video khác.

## Mười thể loại

chữ động · số đếm tăng · biểu đồ · logo sting và khoá thương hiệu · lower-third và chú thích ·
bản đồ động · tweet hoặc tiêu đề báo · hoạt hoá giao diện web · hợp nhất hình học của một bức ảnh
thật vào biểu đồ · lớp phủ mạng xã hội.

Mỗi thể loại có một hình dạng riêng — chọn thể loại **trước**, đừng chọn hiệu ứng trước.

## Bảy bước

0. **Dựng project**, chốt khung hình và định dạng đầu ra (MP4 hay lớp trong suốt — quyết ngay, vì
   nền trong suốt cần đường render khác).
1. **Kế hoạch** — nói bằng lời: khung này làm gì, chuyển động nào mang nghĩa.
2. **Nguồn media** (nếu cần) qua `media-use`.
3. **Thiết kế** — màu, chữ, bố cục.
4. **Dựng**, ưu tiên dùng lại: tra kho (`hyperframes-registry`) trước khi tự viết.
5. **Nghiệm thu bằng `check`**, hỏng thì sửa rồi chạy lại.
6. **Duyệt rồi render.** Lớp trong suốt dùng định dạng hỗ trợ kênh alpha, không phải MP4 thường.

## Luật của đơn vị ngắn

- **Một ý, một đơn vị.** Dưới 10 giây không đủ chỗ cho hai ý; hai ý thì làm hai clip.
- **Chuyển động phải có nghĩa.** Số đếm tăng vì con số là thông điệp; chữ trượt vào vì nó dẫn mắt.
  Chuyển động chỉ để "cho đỡ tĩnh" làm loãng thứ duy nhất cần nhìn.
- **Đọc được khi tắt tiếng.** Không lời đọc nghĩa là chữ trên màn hình gánh toàn bộ nghĩa.
- **Dừng ở khung cuối đủ lâu** để đọc hết — ít nhất 0,8 giây sau khi chuyển động cuối kết thúc.
- **Cấm `repeat: -1`** ngay cả khi đầu ra là một vòng lặp: làm vòng lặp bằng số lần hữu hạn khớp với
  `data-duration`.
