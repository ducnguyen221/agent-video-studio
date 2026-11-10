# Lyric video từ video mẫu

Quy trình nối phân tích mẫu với `music-to-video`. Agent thiết kế và dựng theo bài hát, lời,
media và lựa chọn của người dùng; kiểm chất lượng trên video cuối. Đây là quy trình có bước agent
đối chiếu, không phải pipeline tự động chứng minh mọi file runtime sử dụng.

1. **Mẫu và bài hát.** Dùng `video-reference-analysis` đọc mẫu khi có tệp hoặc quyền tải phù hợp;
   URL cần phép đích danh và hồ sơ quyền theo skill đó. Ghi bản đồ beat có bằng chứng. Thu thập bản
   nhạc, lời và media của người dùng; ghi quyền riêng cho bản thu, sáng tác/lời, ảnh/clip, font và
   nhạc/SFX. Quyền chưa rõ thì ghi `unknown`, không công bố; cần quyền để dùng tài sản nào thì làm
   rõ hoặc thay tài sản đó.
2. **Brief → treatment → storyboard.** Dùng bản đồ mẫu làm tham chiếu cách kể, rồi áp dụng
   `video-remix-brief` và `music-to-video`. Phân tích nhạc; đối chiếu lời, giữ trạng thái text và
   timing độc lập; cue dùng thời điểm của **bản thu mới**. Lập storyboard từ mẫu tĩnh/nhiều media,
   liên kết cue, cover, bố cục, hình, font, màu, chuyển động và âm thanh. Dùng `video-theme-library`,
   `lyric-video-effects` và `photo-ambient-effects` khi phù hợp. Trình phương án và các khung/preview
   cần thiết; giữ quyết định đã được duyệt, không hỏi lại.
3. **Một project, một cây media.** Project do `reference init` tạo cũng có thể là gốc lyric:
   giữ `source/`, `evidence/`, `provenance.json`, `reference-map.md`, brief/treatment, storyboard,
   `lyrics.md`, `cues.json` và `media-ledger.md` tại project. Đặt media dùng dựng trong
   `<project>/composition/media/`; `composition/` là gốc HyperFrames, đường trong composition là
   `media/...`. Khai từng tệp dựng trong `provenance.json` `assets[]` bằng đường tương đối từ project
   và ghi ID, nguồn, chủ, quyền, đường dẫn trong media ledger. Nhạc master và SFX dùng để ghép cũng
   nằm trong cây này. Không đưa hình, lời, giọng, nhạc hay tư liệu lấy từ mẫu vào bản mới; dùng
   tài sản gốc của người dùng hoặc tài sản khác có quyền.
4. **Kiểm gọn trước dựng.** Tạo composition và chuẩn bị lệnh ghép audio theo storyboard, chưa render;
   đối chiếu storyboard, composition và kế hoạch ghép audio với ledger:
   các tệp thực sự định dùng phải có mặt, đúng phiên bản/đường dẫn và có quyền phù hợp. Chạy
   `video-studio reference audit --project <project> --assets <project>/composition/media --json`;
   lỗi hoặc `checked` bằng 0 thì sửa trước dựng. Audit chỉ kiểm cây đã chỉ định, khai báo và trùng
   byte với mẫu; không đọc composition hay chứng minh quyền. Agent tự đối chiếu media trong HTML,
   CSS, JS, font và lệnh ghép audio với ledger; ghi điều chưa kiểm thay vì kết luận máy đã kiểm hết.
   `reference lyric-audit` là lựa chọn bổ sung nếu có trong bản đang chạy, không bắt buộc tạo thêm
   manifest. Nó cũng chỉ kiểm tập khai báo.
5. **Dựng và kiểm chất lượng.** Theo `music-to-video`: dựng preview, xem bố cục và chuyển động, sửa
   rồi render qua wrapper của repo; ghép đúng audio master theo offset đã chọn. Kiểm file cuối có
   audio, thời lượng, điểm vào/ra và nghe/xem theo phạm vi thực tế; kiểm chữ/dấu, vùng an toàn,
   hình, nhịp, cue và việc không dùng tư liệu mẫu. Ghi QA, các phần chưa nghe/kiểm và đường output.
   Nếu chỉ làm đến storyboard hoặc preview, bàn giao đúng mức đó; không tự công bố video.

Đường này kế thừa công cụ và kiểm tra thủ công hiện có; chưa được xác nhận bằng một lượt dựng lyric
từ mẫu đầu-cuối. Dùng bản repo hoặc plugin đã cập nhật đúng phiên bản trong phiên thử.
