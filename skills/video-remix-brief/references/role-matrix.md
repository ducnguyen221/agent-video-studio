# Bảng vai trò × biểu hiện

Dùng khi viết `treatment.md`. Mỗi hàng là một **vai trò** trong video mẫu; mỗi cột là một chỗ
vai trò đó **hiện ra**. Điền ô bằng «giữ: …» hoặc «đổi sang: …» kèm tài sản thay thế có trong
`assets/`. Ô để trống nghĩa là chưa quyết, và chưa được dựng. Ô ghi «—» nghĩa là không áp dụng cho vai đó.

## Luật

**Đổi một vai trò phải đổi đủ hàng.** Đã đổi vai trò thì mọi cột của hàng đó đều phải có câu trả
lời: thay hẳn, hoặc ghi lý do giữ vì nó không thuộc về vai trò cũ (ví dụ nền chung của bản mới).
Đổi người dẫn mà vẫn nghe giọng cũ, hay vẫn xen cảnh B-roll quay riêng cho người cũ, là hàng bị
đổi nửa vời.

Cột **giọng**, **ảnh/footage**, **B-roll**, **đồ hoạ** và **nhạc** chỉ nhận tài sản của người
dùng, sinh mới hoặc template; không cột nào được trỏ vào `source/` hay `evidence/`.

## Bảng

| Vai trò | Giọng | Ảnh / footage | B-roll gắn với vai | Đồ hoạ | Caption | Nhạc | Tên gọi |
|---|---|---|---|---|---|---|---|
| Người dẫn | giọng của người dùng đã đồng ý, hoặc giọng thiết kế mới; không nhân bản giọng người trong mẫu | footage người dùng quay; không dùng khung của mẫu | cảnh minh hoạ lời của người dẫn mới, quay hoặc sinh mới | khung tên, thanh dưới màn hình theo thương hiệu người dùng | lời của người dẫn mới, nhãn người nói nếu có nhiều người (`T8`) | nhạc người dùng có quyền hoặc nhạc sinh mới | tên thật hoặc bút danh của người dùng |
| Nhân vật | giọng của diễn viên thật đã đồng ý, hoặc giọng thiết kế mới | ảnh/cảnh của nhân vật mới; ghi đặc điểm cần giữ (`T7`) | cảnh nhân vật mới trong bối cảnh mới | biểu tượng, màu nhận diện của nhân vật mới | caption của câu thoại mới | chủ đề nhạc của nhân vật mới | tên nhân vật mới |
| Sản phẩm | — (do người kể hoặc người dẫn đọc) | ảnh, cảnh quay sản phẩm của người dùng | cảnh dùng, so sánh, kết quả của sản phẩm này | bảng thông số, biểu đồ với số của sản phẩm này | chữ hiển thị đúng tên, số, đơn vị của sản phẩm (`T3`) | — | tên và dòng sản phẩm đúng như bao bì |
| Thương hiệu | — | logo, màu, kiểu chữ của người dùng | cảnh mang dấu thương hiệu của người dùng | mẫu đồ hoạ, cuối video, khung thương hiệu | cách viết hoa, dấu của tên thương hiệu | âm hiệu hay nhạc nhận diện của người dùng | tên thương hiệu, khẩu hiệu của người dùng |
| Người kể | giọng đọc của người dùng hoặc giọng thiết kế mới (qua `agent-voice-studio`) | ảnh, cảnh phục vụ lời kể; không cần xuất hiện mặt | cảnh bám theo ý của lời kể (`T4`) | tiêu đề phần, số liệu theo lời kể mới | lời kể mới, tách chữ hiển thị khỏi cách đọc (`T3`) | nhạc nền dưới lời kể, hạ khi có lời | — |

## Cách dùng

1. Từ `reference-map.md` liệt kê các vai trò thật sự có trong mẫu (người dẫn? sản phẩm? nhân vật?).
   Mẫu không có vai nào thì bỏ hàng đó.
2. Với mỗi vai, hỏi người dùng vai đó trong bản mới là ai/cái gì, rồi điền cả hàng.
3. Cột nào cần tài sản chưa có (chưa quay, chưa có giọng đã đồng ý): ghi «thiếu», dừng và hỏi;
   không lấy tạm của mẫu.
4. Cuối: mỗi tài sản trong bảng có dòng `assets[]` tương ứng trong `provenance.json`.
