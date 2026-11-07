# Bảy khuôn dựng

Dùng khi viết Treatment: từ `reference-map.md` nhận ra mẫu gần khuôn nào, rồi đi theo đường dựng
có thật của `video-studio`. Tài liệu này tự viết theo các đường dựng của repo; ý thể loại tham khảo
nguồn ghi ở `NOTICE`. Khuôn chỉ là điểm xuất phát: mẫu lai thì ghi khuôn chính và khuôn phụ trong
Treatment.

Mỗi khuôn trả lời năm câu theo thứ tự: nhận ra ở đâu trong bản đồ beat, dựng bằng lệnh nào và cần
gì trong `assets/`, giữ gì của mẫu, bắt buộc đổi gì, kiểm gì trước khi dựng. Phần **giữ** là cấu
trúc và nhịp; phần **đổi** luôn gồm giọng, hình, lời, nhạc, tên gọi theo
[`role-matrix.md`](role-matrix.md) (đổi một vai thì đổi đủ hàng).

| Khuôn | Đường dựng |
|---|---|
| 1. Kể chuyện có lời dẫn | composition HyperFrames + `narrate` |
| 2. Người dẫn trình bày | `edit` từ footage người dùng quay |
| 3. Xếp hạng | `render` template `news` hoặc `topstory` |
| 4. Podcast hai người | `edit` (giới hạn: bản bóc lời tại máy không phân biệt người nói) |
| 5. Phỏng vấn đường phố | `edit` + đồng ý của người xuất hiện |
| 6. Talking head | `edit` |
| 7. Phim ngắn | **chưa hỗ trợ** |

Các khuôn dùng `edit` chạy theo ba bước: `edit --step transcribe`, `--step pack`, rồi
`edit --step render --edl <edl.json>` khi đã có EDL. Footage đặt trong thư mục `--footage`, tài sản
khác đặt trong `assets/` của project tham chiếu và khai trong `assets[]` của `provenance.json`.

## 1. Kể chuyện có lời dẫn

- **Nhận ra trong bản đồ:** cột Lời gần như liền mạch một giọng; cột Hình đổi nhiều lần dưới cùng
  một đoạn lời; người nói không xuất hiện mặt; cột Việc làm cho người xem ghi chứng minh, giải
  thích hoặc cho xem kết quả.
- **Đường dựng:** viết composition HyperFrames từ Treatment, rồi `narrate` thêm giọng đọc; lời neo
  theo thẻ `T4`. Cần trong `assets/`: ảnh hoặc cảnh quay sản phẩm của người dùng, ảnh chụp màn hình
  thật, đồ hoạ sinh mới hoặc từ template, tệp giọng hoặc cấu hình giọng của người kể.
- **Giữ từ mẫu:** thứ tự ý, độ dài tương đối của từng ý, chỗ để im lặng cho nhạc, mật độ đổi hình
  tính theo ý chứ không theo giây của mẫu.
- **Đổi bắt buộc:** hàng Người kể trong `role-matrix.md` (lời, giọng, hình bám lời), hàng Sản phẩm
  nếu có; mọi chữ trên màn hình.
- **Kiểm trước khi dựng:** mỗi cảnh trong composition trỏ được tới một câu lời nó làm rõ; chạy
  `reference audit --project <dir>` rồi xem khung đầu, giữa, cuối của bản ra.

## 2. Người dẫn trình bày

- **Nhận ra trong bản đồ:** có người nói trước máy; cột Hình xen giữa mặt người dẫn và đồ hoạ;
  các lần đổi bố cục trùng với lúc chuyển ý trong cột Lời.
- **Đường dựng:** `edit` trên footage người dùng tự quay (`edit --step transcribe`, `--step pack`,
  rồi `edit --step render --edl <edl.json>`); đồ hoạ chèn thêm từ template hoặc composition. Cần
  trong `assets/`: footage của người dẫn mới, đồ hoạ và số liệu thuộc đề tài mới.
- **Giữ từ mẫu:** thứ tự lập luận, chỗ người dẫn nhìn thẳng người xem, tỷ lệ thời gian giữa mặt
  người và đồ hoạ.
- **Đổi bắt buộc:** hàng Người dẫn đủ cột (giọng, footage, B-roll gắn với vai, khung tên, caption,
  tên gọi); ví dụ và số liệu. Không dùng khung hình của người dẫn trong mẫu. Người dẫn là người
  khác ngoài chủ project thì cần đồng ý của họ.
- **Kiểm trước khi dựng:** mỗi đoạn đồ hoạ trong EDL có nguồn khai trong `assets[]`; xem khung giữa
  video để chắc không còn vết của mẫu.

## 3. Xếp hạng

- **Nhận ra trong bản đồ:** cùng một cấu trúc con lặp lại cho từng mục (giới thiệu, bằng chứng,
  chốt); cột Hình có bảng hoặc danh sách thay đổi trạng thái; số mục cố định.
- **Đường dựng:** `render` với template `news` hoặc `topstory` từ spec JSON; bảng nhiều tầng tuỳ
  biến thì viết composition riêng. Cần trong `assets/`: biểu tượng hoặc ảnh từng mục, số liệu kèm
  nguồn của người dùng. Nên dựng thử một lần trước khi cam kết bản đầy đủ.
- **Giữ từ mẫu:** số mục, chiều xếp (trên xuống hoặc dưới lên), thời điểm bảng đổi trạng thái so
  với lời, độ dài tương đối mỗi mục.
- **Đổi bắt buộc:** chủ đề, các mục, tiêu chí, hàng Sản phẩm của từng mục (tên, phiên bản, số liệu
  lấy từ nguồn người dùng, không chép từ mẫu), hàng Thương hiệu (màu, chữ), giọng.
- **Kiểm trước khi dựng:** `reference audit --project <dir>`; xem một khung ở kích thước thật để
  chắc biểu tượng từng mục còn nhận ra được.

## 4. Podcast hai người

- **Nhận ra trong bản đồ:** hai giọng luân phiên trong cột Lời; cột Hình gồm hai khung người và
  đôi lúc cảnh minh hoạ che khi một người kể ví dụ.
- **Đường dựng:** `edit` từ footage hai người của người dùng, `edit --step render --edl <edl.json>`.
  Cần trong `assets/`: footage cả hai người, B-roll nếu cần che. Giới hạn: bản bóc lời tại máy
  **không phân biệt người nói**, nên nhãn người nói trong caption do người dựng xác nhận (thẻ `T8`);
  ghi giới hạn này vào Treatment.
- **Giữ từ mẫu:** thứ tự hỏi–đáp, vị trí hai người trong khung, chỗ chèn B-roll, mật độ cắt giữa
  hai góc máy.
- **Đổi bắt buộc:** hàng Người dẫn cho từng người (hai hàng), giọng, bối cảnh, chủ đề. Mỗi người
  xuất hiện phải có đồng ý riêng.
- **Kiểm trước khi dựng:** mỗi điểm cắt trong EDL rơi vào đúng người đang giữ ý chính (so lại với
  transcript do người dựng gán nhãn); xem khung đầu, giữa, cuối để chắc nhãn không đảo.

## 5. Phỏng vấn đường phố

- **Nhận ra trong bản đồ:** cột Lời có một câu hỏi ngắn rồi một câu trả lời dài hơn, lặp lại nhiều
  lần với những người khác nhau; cột Hình ở ngoài trời, nhiều người xuất hiện chỉ một lần.
- **Đường dựng:** `edit` từ footage người dùng quay, `edit --step render --edl <edl.json>`. Cần
  trong `assets/`: footage quay thật, và bằng chứng đồng ý của từng người xuất hiện (khai ở hồ sơ
  quyền trước khi dựng, xem [`rights-and-provenance.md`](rights-and-provenance.md)). Thiếu đồng ý
  của ai thì dừng và hỏi, không dựng đoạn có người đó.
- **Giữ từ mẫu:** thứ tự mở–hỏi–đáp–kết trong mỗi lượt, tần suất cắt, vị trí chữ trên màn hình.
- **Đổi bắt buộc:** hàng Người dẫn (người hỏi), toàn bộ người trả lời, địa điểm, câu hỏi, chữ
  hiển thị, giọng.
- **Kiểm trước khi dựng:** mỗi người xuất hiện trong EDL đối chiếu được với một đồng ý đã khai;
  `reference audit --project <dir>` sạch trước khi xuất bản.

## 6. Talking head

- **Nhận ra trong bản đồ:** một người nói liền suốt video; cột Cắt/hiệu ứng toàn cắt nhảy; chữ
  trên màn hình theo sát từng câu.
- **Đường dựng:** `edit` từ footage của người dùng, có caption theo thẻ `T3` và `T8`:
  `edit --step transcribe`, `--step pack`, `--step render --edl <edl.json>`. Cần trong `assets/`:
  footage người nói, bằng chứng hoặc đồ hoạ cho số liệu nếu có.
- **Giữ từ mẫu:** nhịp cắt bỏ khoảng lặng (tham số `--silence`), chỗ nhấn bằng chữ, vị trí chữ so
  với khuôn mặt.
- **Đổi bắt buộc:** hàng Người dẫn đủ cột, kịch bản, caption (tách chữ hiển thị khỏi cách đọc), nhạc,
  tên gọi.
- **Kiểm trước khi dựng:** mọi con số và tên riêng hiện ở caption hoặc đồ hoạ, khớp với nguồn của
  người dùng; xem khung đầu, giữa, cuối để chắc chữ không đè lên mặt.

## 7. Phim ngắn

- **Nhận ra trong bản đồ:** nhiều cảnh với nhân vật lặp lại; cột Lời là thoại; cột Việc làm cho
  người xem là diễn biến chuyện chứ không phải thông tin.
- **Đường dựng: `chưa hỗ trợ`.** Repo này không sinh diễn xuất nhất quán nhiều cảnh. Phần làm được:
  viết kịch bản và danh sách cảnh để người dùng quay, giữ nhân vật nhất quán theo thẻ `T7`; khi đã
  có footage thì dựng bằng `edit`. Không giả vờ dựng bản phim.
- **Giữ từ mẫu:** thứ tự các cảnh và quan hệ nhân quả giữa chúng.
- **Đổi bắt buộc:** hàng Nhân vật đủ cột, nơi chốn, đạo cụ, lời thoại.
- **Kiểm trước khi dựng:** nói thẳng với người dùng rằng đây là khuôn `chưa hỗ trợ` trước khi viết
  Treatment; Treatment chỉ chứa kịch bản và danh sách cảnh.
