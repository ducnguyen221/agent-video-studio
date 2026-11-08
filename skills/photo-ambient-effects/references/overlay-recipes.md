# Chọn lớp phủ theo ảnh

| Lớp | Hình học/nhịp | Vùng mặc định 1920×1080 | Khi dùng |
|---|---|---|---|
| Sao lấp lánh | 48 sao seed cố định; sin 2–4 chu kỳ/8 s | Trời, y35–255 | Đêm, bầu trời; giảm khi ảnh sáng |
| Đom đóm | 34 điểm glow chuyển động sin/cos 8 s | Hai mép | Album lãng mạn, khu vườn; tránh mặt |
| Sao băng | 4 vệt dài .95 s theo chu kỳ 8 s | Mép trên | Điểm nhấn, không rơi giữa chữ |
| Mặt nước | 3 đường sóng và 30 phản xạ mỗi bên | Hai góc dưới | Ảnh có biển/hồ; tắt khi không có nước |
| Tia nắng góc | 5 dải quạt, 4 lớp feather, gradient dọc tia | Góc trên phải, hướng xuống trái | Ánh sáng ấm, đoạn hy vọng/điệp khúc |

`createAmbientPainter(canvas, {stars, fireflies, meteors, sea, glows})` trả hàm
`paint(seconds, strength=1)`. Các cờ boolean mặc định true, tắt phần không hợp ảnh.
Preset này có toạ độ 16:9; khung khác dù canvas co giãn vẫn cần thiết kế vùng bảo vệ lại.
Không hứa tự phát hiện mặt hoặc tự tránh vật thể.

`createSunRayPainter(canvas, options)` trả `paint(seconds,power=1)`.
Mặc định origin [1840,-75], direction 2.13 rad, period 8, strength 1;
đổi origin/direction nếu góc sáng thật khác. Góc trên trái gợi ý origin [80,-75], direction 1.01.
Cường độ demo có thể 1.25 để nhìn rõ, full video .6–1 và các cửa sổ thưa 4–10 s.
Trình tự: photo → rays → shade/gradient bảo vệ → particles → lyrics.
Nếu particles che mặt, dùng mask vùng riêng hoặc giảm/tắt lớp, không dựa vào may rủi.
