---
name: general-video
description: Author or edit a custom HyperFrames composition when no specialised workflow fits - longer or multi-scene pieces, brand and sizzle reels, montages, static loops, static title cards, footage remixes and freeform builds. Use motion-graphics instead for a short unnarrated motion unit including an animated title. Route fresh creation through the hyperframes entry point before landing here.
---

# Dựng tự do khi không workflow nào khớp

> **Nguồn:** `heygen-com/hyperframes` · `skills/general-video/SKILL.md` @ **v0.8.51** · Apache-2.0 ·
> hash manifest `079d3479295e27b4` (4 file upstream).
> Bản này **đã dịch, rút gọn và biên tập lại** (Apache-2.0 §4(b)).

Đây là đường **cuối cùng**, không phải đường mặc định. Trước khi vào đây, đi qua `hyperframes` để
chắc rằng không có workflow chuyên biệt nào khớp — workflow chuyên biệt mang theo cả bảng phân cảnh
lẫn bộ luật của thể loại, tự dựng lại là tự bỏ cả hai.

## Sáu bước

1. **Áp bộ chuyển nguồn chung** — có URL, có PR, có nhạc, có footage thì xử lý đầu vào đúng cách
   trước, đừng dán thẳng vào composition.
2. **Bắt đầu từ trạng thái project đang có.** Đọc `hyperframes.json`, `index.html`, danh sách
   sub-composition. Dựng lại từ đầu lên một project đang dở là xoá việc người khác.
3. **Đọc hình dạng của lượt việc** — làm mới hoàn toàn, hay đi kèm một bản thiết kế đã chốt, hay
   sửa một phần.
4. **Nạp tri thức cần cho từng chặng**, không nạp sẵn tất cả: `hyperframes-creative` cho thiết kế,
   `hyperframes-core` cho markup, `hyperframes-animation` cho chuyển động.
5. **Dựng composition.**
6. **Cổng luôn áp**, xem dưới.

## Bốn cổng luôn áp

- **Giữ phạm vi đúng bằng yêu cầu.** Thấy chỗ khác chưa đẹp thì ghi chú, đừng tiện tay sửa: người
  duyệt đang so với bản họ biết.
- **Chốt thiết kế trước khi viết HTML.** Viết HTML rồi mới bàn màu là viết hai lần.
- **Giữ nguyên hợp đồng composition** — id, khoá timeline, `data-*`, đường media của phần không
  liên quan không được đổi.
- **Mượn quy trình khác thì mượn cả bộ luật của nó.** Lấy bảng phân cảnh của một workflow mà bỏ
  phần nghiệm thu của nó là lấy đúng phần dễ.

## Khi nào nên quay lại workflow chuyên biệt

Giữa chừng phát hiện video thật ra là "giải thích một chủ đề", "ra mắt sản phẩm", "cắt theo nhạc"
hay "gắn card lên phỏng vấn" — thì **dừng và chuyển**. Đi tiếp bằng đường tự do chỉ để khỏi làm lại
là cách tự bỏ bộ luật đã có người trả giá viết ra.
