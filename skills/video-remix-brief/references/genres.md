# Bảy khuôn thể loại

Dùng khi viết Treatment: nhận ra mẫu thuộc khuôn nào, giữ gì, đổi gì, và dựng bằng đường nào của
`video-studio`. Mỗi khuôn do repo này tự viết lại từ ý tham khảo, không dịch từng câu của tài liệu nào. Khuôn chỉ là
điểm xuất phát: mẫu lai thì ghi khuôn chính và khuôn phụ trong Treatment.

Quy ước chung cho cả bảy khuôn: **giữ** là cấu trúc và nhịp; **đổi** luôn gồm giọng, hình, lời,
nhạc, tên gọi (theo [`role-matrix.md`](role-matrix.md)). Đường dựng: `render` (spec JSON theo
template), `edit` (EDL từ footage của người dùng), composition HyperFrames viết tay, `narrate`
(thêm giọng vào video câm).

| Khuôn | Đường dựng |
|---|---|
| 1. Kể chuyện có lời dẫn | composition HyperFrames + `narrate` |
| 2. Người dẫn trình bày | `edit` từ footage người dùng quay |
| 3. Xếp hạng | template `news` hoặc `topstory` của `render` |
| 4. Podcast hai người | `edit` (giới hạn: bản bóc lời tại máy không phân biệt người nói) |
| 5. Phỏng vấn đường phố | `edit` + đồng ý của người xuất hiện |
| 6. Talking head | `edit` |
| 7. Phim ngắn | **chưa hỗ trợ** |

## 1. Kể chuyện có lời dẫn (demo, hướng dẫn, tiểu luận hình ảnh)

- **Cấu trúc:** một mạch lời kể liền; hình thay đổi liên tục bên dưới để chứng minh từng ý. Mở
  bằng cảnh đặt bối cảnh, sau đó xen cảnh chứng minh (dùng thật, kết quả, so sánh), màn hình khi
  chi tiết giao diện quan trọng, đồ hoạ khi ý cần sơ đồ.
- **Nhịp:** đổi hình theo ý chứ không theo đồng hồ; một đoạn lời dài có thể mang nhiều hình.
- **Giữ:** thứ tự ý, tỷ lệ cảnh chứng minh so với cảnh minh hoạ chung, chỗ im lặng cho nhạc.
- **Đổi:** toàn bộ lời, giọng người kể, sản phẩm/màn hình thật của người dùng, đồ hoạ.
- **Cạm bẫy:** minh hoạ từng danh từ bằng ảnh chung chung cho cảm giác bận rộn mà không chứng minh
  gì; mỗi hình phải làm rõ hoặc chứng minh điều đang nói.
- **Đường dựng:** viết composition HyperFrames từ Treatment, thêm lời bằng `narrate`; lời neo
  theo thẻ `T4`.

## 2. Người dẫn trình bày kèm hình minh hoạ

- **Cấu trúc:** người dẫn nói, còn hình dần phát triển lập luận: so sánh hai thứ, giữ cả hai trên
  màn hình khi giải thích, đổi quan hệ khi có thứ thứ ba. Người dẫn lúc chiếm khung, lúc thu
  nhỏ vào góc, lúc nhường khung cho đồ hoạ rồi quay lại.
- **Nhịp:** thay đổi bố cục khi ý đổi, không theo giờ; vật lặp lại giúp người xem nhớ mạch.
- **Giữ:** thứ tự lập luận, chỗ người dẫn quay lại nhìn thẳng người xem.
- **Đổi:** người dẫn (cả hàng vai trò), ví dụ, số liệu, đồ hoạ.
- **Cạm bẫy:** kể ra các đồ vật xuất hiện mà bỏ quên hành vi của chúng (xuất hiện, di chuyển,
  rời đi).
- **Đường dựng:** `edit` trên footage người dùng tự quay; đồ hoạ chèn thêm bằng template hoặc
  composition. Không dùng khung của người dẫn trong mẫu.

## 3. Xếp hạng

- **Cấu trúc:** bảng xếp hạng đóng vai bộ nhớ của video: những mục đã chấm nằm sẵn trên màn hình,
  còn lời nói và bằng chứng chỉ lo mục đang xét. Video có thể bắt đầu khi bảng đã có vài hàng.
- **Nhịp:** mỗi mục một đoạn có mở (giới thiệu), bằng chứng, phán quyết; bảng đổi trạng thái đúng
  lúc phán quyết, không phải lúc bắt đầu nói.
- **Giữ:** số mục, thứ tự từ dưới lên hoặc trên xuống, cách đẩy bảng.
- **Đổi:** chủ đề, các mục, tiêu chí, biểu tượng từng mục, giọng, màu.
- **Cạm bẫy:** biểu tượng cần nhận ra được ở cỡ hiển thị thật; tên, phiên bản, số liệu của mục
  phải lấy từ nguồn người dùng, không chép từ mẫu.
- **Đường dựng:** `render` với template `news` hoặc `topstory`; bảng nhiều tầng tuỳ biến thì viết
  composition riêng. Khuôn này nên được kiểm thật bằng một lần dựng thử trước khi cam kết.

## 4. Podcast hai người

- **Cấu trúc:** lập luận đi qua sự tương tác giữa hai người: người này đặt vấn đề, người kia phản
  ứng làm ý đó đổi sắc thái, rồi một câu đáp khép lại. Hai góc máy đối xứng nhau; người đang nghe
  vẫn có cử động nhỏ như đổi tư thế hoặc liếc đi.
- **Nhịp:** cắt sang người đang có ý quan trọng hoặc người phản ứng đáng giá, không luân phiên
  máy móc.
- **Giữ:** cấu trúc hỏi–đáp–phản ứng, vị trí hai người, các đoạn B-roll che khi một người kể ví dụ.
- **Đổi:** cả hai người, giọng, bối cảnh, sản phẩm, chủ đề.
- **Cạm bẫy / giới hạn:** bản `edit` và bản bóc lời tại máy **không phân biệt người nói**, nên nhãn
  người nói trong caption phải do người dựng xác nhận (thẻ `T8`); ghi giới hạn này vào Treatment.
- **Đường dựng:** `edit` từ footage hai người của người dùng.

## 5. Phỏng vấn đường phố

- **Cấu trúc:** một người hỏi chặn đường người qua đường đang bận việc của họ, đặt câu hỏi và thu
  về câu trả lời đáng xem. Phần hấp dẫn nằm ở khách; người hỏi chỉ dẫn khán giả vào. Cảnh mở cho
  thấy khách đang làm gì đó rồi người hỏi tiến lại; cảnh kết để khách rời đi sau câu chốt.
- **Nhịp:** cắt về khách khi họ trả lời; người hỏi chỉ lên khi ngạc nhiên hoặc phản biện thật.
  Khoảnh khắc lộ đáp án có thể kèm đổi chữ, âm và màu cùng lúc.
- **Giữ:** cấu trúc mở–hỏi–đáp–kết, tần suất cắt, chỗ lộ đáp án.
- **Đổi:** người xuất hiện, địa điểm, câu hỏi, giọng, chữ trên màn hình.
- **Cạm bẫy:** cần **đồng ý của người xuất hiện** cho việc quay và dùng hình/giọng họ; nếu chưa có
  thì dừng và hỏi, không dựng.
- **Đường dựng:** `edit` từ footage người dùng quay.

## 6. Talking head

- **Cấu trúc:** một người nói thẳng với người xem; thái độ của họ dẫn video, caption và bằng
  chứng giúp theo kịp. Có thể kèm bảng xếp hạng hoặc minh hoạ nhưng không bắt buộc.
- **Nhịp:** cắt nhảy bỏ khoảng lặng, thay đổi nhẹ tư thế giữa hai đoạn như một bản ghi đã dựng;
  nhấn bằng cử chỉ nhỏ có lý do.
- **Giữ:** nhịp cắt, chỗ nhấn, vị trí chữ so với mặt người nói.
- **Đổi:** người nói (cả hàng vai trò), kịch bản, caption, bằng chứng, nhạc.
- **Cạm bẫy:** chữ và số quan trọng nên nằm trong caption hay đồ hoạ, đừng trông vào cử chỉ.
- **Đường dựng:** `edit` từ footage của người dùng, có caption theo thẻ `T3`/`T8`.

## 7. Phim ngắn

- **Cấu trúc:** kể chuyện bằng diễn xuất: nhân vật muốn gì, hành động gây hậu quả, tiết lộ làm
  người xem hiểu khác đi. Nhân vật, bối cảnh và hành động phải nhất quán qua nhiều cảnh.
- **Nhịp:** theo quan hệ nhân quả giữa cảnh, có chỗ cho im lặng và phản ứng.
- **Giữ:** chuỗi nhân quả, vai trò từng cảnh.
- **Đổi:** toàn bộ người, nơi chốn, đạo cụ, lời thoại.
- **Đường dựng: `chưa hỗ trợ`.** Repo này không sinh diễn xuất nhất quán nhiều cảnh; cần người
  dùng quay thật hoặc cung cấp footage, và continuity theo thẻ `T7`. Phần làm được: viết kịch bản
  và danh sách cảnh để quay, rồi dựng bằng `edit` khi đã có footage. Không giả vờ dựng bản phim.
