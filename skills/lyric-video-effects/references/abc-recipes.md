# Ba preset chữ

| Mã | Hình chữ và vào | Giữ/ra | Tình huống |
|---|---|---|---|
| A | Handprint/brush; từ nảy nhẹ 18 px, xoay ±3°, scale .94→1 | Jitter một nhịp ±.7°; từ đã hát trôi lên rồi mờ | Kỷ niệm vui, câu ngắn, doodle |
| B | Script nối nét; mask trái→phải tối đa .3 s; mask về none | Pulse 1.08×1.035; zoom/fade sau khi hát | Câu vui, thân mật, tên gọi; kiểm ink bắt buộc |
| C | Script mềm; grapheme bay theo một trong bốn đường cong rồi về baseline | Từ đã hát bay cong ra; từ cuối giữ tới sung_end | Chủ đạo tình cảm, điệp khúc, đoạn kết |

Dùng font do project cung cấp hợp lệ, có đủ glyph. Ba font mẫu là vai trò hình dáng,
không phải font được phân phối. Khi người dùng chỉ duyệt A/B/C, cả tiêu đề và câu có dấu cũng
phải thuộc bộ này. Không dùng font sans dự phòng âm thầm.

C có bốn hướng: từ dưới phải, từ trên trái, lượn hình sin, lượn xoè nhẹ.
Đổi biến thể sau 2–3 câu; điệp khúc có thể tăng amplitude từ 1 lên 1.15, cuối bài giảm .45.
Đây là gợi ý theo cấu trúc nhạc, không thay mốc hát thực. Không đổi font giữa một từ.

Runtime: nạp GSAP local và `lyric-presets.js`; caller truyền timeline paused và target DOM.
`animateWord(tl, {style, word, glyph, chars, start, duration, index, variant, amplitude})`.
`duration` là thời gian từ được hát; với C truyền phần tử theo grapheme của `Intl.Segmenter`.
`safeScriptReveal` chỉ tạo mask tween; phải áp CSS padding lên word trước đó.
Markup chuẩn: container `.lyric-style-B` (đổi A/C theo preset), bên trong `.line` chứa
`.word > .glyph`; riêng C thêm `.char` bên trong glyph. CSS đi kèm áp inline-block lên
word/glyph/char để GSAP scale/translate có tác dụng, không cần alias lớp khác.
Các hàm ném lỗi khi thời gian/style sai; không tự tìm DOM hoặc tự thêm timeline.

Icon: module `line-icons.mjs` xuất `ICON_IDS`, `iconShapes`, `iconSVG`; chọn key có thật,
animate dashoffset 1→0 trong .28–.4 s, sau đó pulse tối đa 1.045. SVG không được che chữ.
Màu highlight đổi theo từ bắt đầu hát, chuyển trong .045–.06 s; chỉ giữ màu từ khoá sau hát.
Không đổi màu mọi từ liên tục vì giảm khả năng đọc.
