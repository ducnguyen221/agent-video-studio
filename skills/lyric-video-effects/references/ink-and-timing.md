# Kiểm nét script và thời gian hát

1. Chờ `document.fonts.ready`, kiểm cmap/glyph và nhìn chuỗi có dấu thực.
   `document.fonts.check()` chỉ chứng minh font tải, không chứng minh glyph không fallback.
2. Dùng canvas `actualBoundingBoxLeft/Right/Ascent/Descent` để ước lượng ink;
   `inkPadding()` cho đệm bảo thủ ban đầu. Với font mẫu B ở cỡ lớn, nét nhô khoảng 30 px là có thật.
3. Mask đặt trên word đã có padding, pulse nằm trên glyph con. Bỏ overflow hidden ở cha.
   Không đặt các word quá sát; line-height 1.15 và gap .42em là điểm bắt đầu, không quy tắc mọi font.
4. Khi reveal xong đặt `clipPath:'none'`. Tua đúng peak pulse, chụp bản hiện tại và cùng bản
   bỏ mask. Chờ hai `requestAnimationFrame` trước mỗi lần chụp để GPU ổn định.
5. So pixel crop bao trọn overhang. Bản cũ phải tái hiện thiếu nét; bản sửa phải trùng unmasked
   ở toàn bộ từ được kiểm. Test có mask `none` mà vẫn báo khác cần xem compositing trước khi sửa CSS.

Cue tối thiểu: phrase.start ≤ word.start < word.end ≤ phrase.sung_end ≤ phrase.end.
Không suy word onset từ chia đều số chữ khi đã có căn thời gian tốt hơn.
Hai cụm hát nối nhau: không fade cả card trước sung_end. Có thể cho từ đã hát ra sớm;
`retireSungWord` từ chối ẩn từ cuối. Hết clip mới thay cụm kế tiếp.
Layout tại trạng thái giữ chưa đủ: kiểm glyph đang bay và pulse lớn nhất, không chỉ DOM box.
Screenshot QA không chứng minh sync nhạc; nghe render riêng và ghi đoạn đã nghe.

Với dấu tổ hợp: dùng grapheme segmentation. Nếu buộc ghép dấu bằng SVG, composite phải mang
nguyên ký tự trong dữ liệu/aria-label, dấu cùng màu/cùng transform với chữ, nhìn kiểm từng dấu.
Ưu tiên font đầy đủ glyph trong bộ được duyệt; không coi ghép dấu là giải pháp mọi ngôn ngữ.
