# Hai mươi họ chuyển động mở rộng

Đây là thư viện bổ sung từ bản dựng trước, không phải ba preset A/B/C.
Chỉ chọn khi brief cho phép. Runtime [motion-families.mjs](../assets/motion-families.mjs)
nhận GSAP timeline và cue, không tạo clock mới. DOM/input contract ghi ở đầu module.
Runtime mặc định từ chối họ mở rộng; chỉ truyền `{allowExtended:true}` sau yêu cầu rõ của
người dùng. Không dùng cờ này để tự đổi bộ A/B/C đã duyệt.
Các từ đã hát có thể ra trong .18–.24 s; luôn giữ từ cuối tới sung_end.

| Họ | Vào | Ra | Dùng khi |
|---|---|---|---|
| F01 | Mở từ dưới, từ nhô lên | Nâng và khép dọc | Ký ức mở đầu |
| F02 | Từ gom về tâm | Tản nhẹ hai bên | Cụm ấm áp |
| F03 | Trượt ngang kèm mask | Wipe ngang | Chuyển ý |
| F04 | Blur 5→0, scale .97→1 | Blur 3 và fade | Nhớ nhung |
| F05 | Nảy scale .88→1 | Thu .96 và fade | Câu vui |
| F06 | Từ đan xen hai phía | Tách trái/phải | Đối đáp |
| F07 | Mở ngang trên dải màu | Khép dải | Từ khoá mạnh |
| F08 | Trượt từ trái, icon đi cùng | Trượt phải | Chuyện kể |
| F09 | Reveal từng từ theo hát | Tắt theo thứ tự ngược | Câu nhanh |
| F10 | Từ rơi theo cung | Bay lên lệch nhịp | Vui nhẹ |
| F11 | Mở vòng tròn | Khép vòng tròn | Cụm rất ngắn |
| F12 | Gập rotationX | Gập ngược/fade | Nhấn nhịp |
| F13 | Hai nửa tiến về tâm | Thu/fade | Gắn kết |
| F14 | Hai tầng lên/xuống | Bay lên tuần tự | Cặp ý |
| F15 | Text/icon rơi nhẹ | Khép từ hai mép | Từ ngắn |
| F16 | Gạch chân vẽ rồi reveal | Rút gạch/fade | Tên hoặc lời hứa |
| F17 | Scale .82, nhô lên | Thu và nâng | Từ đinh; nhấn thêm opt-in |
| F18 | Bóng màu lệch rồi tụ | Tách bóng/fade | Nhạc tươi, dùng thưa |
| F19 | Giãn chữ về vị trí | Tách ký tự/fade | Câu ngắn |
| F20 | Từ nâng lần lượt | Fade lần lượt | Đoạn kết |

Các họ mask phải có khoảng đệm ink như B; chữ script không tự an toàn vì đổi họ.
F19 cần `.letter` đã tách theo grapheme; không dùng letter spacing phá liên kết font script.
Không dùng cả 20 họ để chứng minh đa dạng; chọn theo nhạc và tính đọc.
Nguồn private đã có bản full dựng trước; các adapter tái dùng mới cần kiểm lại với font/khung
và cue của project mới. Test lập lịch không chứng minh mọi font đều render đúng.
