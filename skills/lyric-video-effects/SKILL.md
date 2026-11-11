---
name: lyric-video-effects
description: "Design and verify kinetic lyric typography, word highlights and line-art icons. Use when a lyric video needs varied entrances, exits, font changes or script-font clipping fixes; supports music-to-video rather than replacing its workflow."
---

# Chuyển động chữ cho lyric video

Đầu vào: nhạc đã chọn, lời chuẩn và cue theo từ/cụm, vùng chữ, bộ style được duyệt.
Đầu ra: bảng phân cảnh có mã motion, composition dùng cùng đồng hồ với nhạc, bằng chứng kiểm chữ
trên MP4. Skill này bổ trợ workflow `music-to-video`; không thay bước phân tích nhạc hay duyệt storyboard.
Không dùng cho phụ đề người nói hoặc chép lời từ âm thanh chưa được căn thời gian.

Trước khi tạo motion mới, tra `video-theme-library` để tìm component, prompt, asset hoặc nguồn
tham khảo phù hợp. Khi dựng trong project có trạm đã được phép ghi, chủ động lưu và lập chỉ mục
component, prompt, asset hoặc liên kết hữu ích có thể tái dùng theo skill đó, kèm provenance,
quyền và mức kiểm; kiểm tìm lại sau khi lưu.
Nguồn chưa rõ quyền chỉ lưu metadata/liên kết `reference_only`, không chép nội dung. Chưa có trạm
hoặc quyền ghi thì báo chưa lưu, không tự chọn đường; chỉ tra cứu thì không ghi. Không coi bundle
nhiều file đã materialize được.

Ba style tương thích hiện có là **A — Brush + Doodles, B — Wedding Script,
C — Flowing Letters**; chọn font và motion theo bài và brief, không ép font viết tay.
Các họ motion mở rộng là mã dùng lại, không mặc định đã được render kiểm.
Với B, luôn dùng đệm ink trên mask, pulse trên glyph con và `clipPath:'none'` sau reveal;
kiểm cả nét nhô và dấu ở scale lớn nhất trước khi render full.

## Quy trình

1. Khoá lời và tên riêng, nguồn audio, cue và các font/style được phép. Đọc
   [references/abc-recipes.md](references/abc-recipes.md) để chọn A/B/C và cách đổi sau 2–3 câu.
   Xong khi mỗi cụm có start, sung_end, end, style, icon; thiếu cue thì quay lại căn lời.
2. Kiểm glyph thực của font trước khi dựng. Không âm thầm dùng font thẳng khi thiếu dấu.
   Đọc [references/fonts-and-glyphs.md](references/fonts-and-glyphs.md) để chọn nguồn,
   kiểm license và phát hiện fallback trên runtime thực.
   Đọc [references/ink-and-timing.md](references/ink-and-timing.md) khi dùng script, pulse,
   mask hoặc chữ có dấu. Xong khi các từ dài và có dấu hiển thị đầy đủ; lỗi thì đổi sang font
   trong bộ đã duyệt hoặc xin đổi font nếu không font nào đáp ứng.
3. Dùng [assets/lyric-presets.js](assets/lyric-presets.js) cho A/B/C;
   [assets/script-ink.css](assets/script-ink.css) là khoảng đệm khởi đầu cho B, cần đo lại theo font.
   [assets/soft-presets.js](assets/soft-presets.js) bổ sung `soft-rise` và `focus-in`;
   đây là mã dùng lại chưa chứng minh render cho từng font/tỉ lệ.
   Dùng [assets/line-icons.mjs](assets/line-icons.mjs) để lấy một icon nét vẽ mỗi cụm khi brief yêu cầu.
   Đọc [references/motion-families.md](references/motion-families.md) khi cần mở rộng cách vào/ra;
   chỉ dùng họ mở rộng nếu brief cho phép, không trộn vào video bị giới hạn A/B/C.
   Xong khi seek cùng thời điểm cho cùng hình; lỗi thì bỏ timer riêng, dùng timeline composition.
4. Kiểm khung ở lúc vào, giữ và ra của từng cụm; đo vùng chữ/icon và so screenshot B với bản bỏ
   mask ở pulse lớn nhất. Nghe các điểm nối trên MP4, giữ nguyên từ cuối trong nguyên âm dài.
   Xong khi không cắt nét, không đổi font ngoài bộ cho phép, không che mặt; lỗi quay lại bước 2/3.
5. Bàn giao video, cue, storyboard, phiên bản runtime và báo cáo phần đã/chưa nghe kiểm.
   Đọc [references/provenance-and-coverage.md](references/provenance-and-coverage.md) trước khi
   mô tả mức đã kiểm. Model A/B eval chưa chạy phải ghi `not_run`, không suy từ static check.

## Gotchas

- `clip-path: inset(0)` vẫn cắt nét script nhô ra; padding nằm trên mask, glyph nằm bên trong,
  và đặt mask về `none` sau reveal. `overflow: visible` một mình không gỡ clip-path.
- B mô phỏng viết bằng mask, không phải vẽ lại nét bút thật. C chuyển động theo grapheme;
  tách code point có thể làm dấu rơi khỏi chữ.
- Pulse thay đổi ink bounds. Đo ở scale lớn nhất; khoảng đệm CSS mẫu không bảo đảm mọi font.
- Không đóng gói font hệ điều hành, ảnh, nhạc, lời hoặc tên riêng của project vào skill.
