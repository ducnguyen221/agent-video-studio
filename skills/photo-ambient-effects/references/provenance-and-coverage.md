# Nguồn và phạm vi đã kiểm

Seeded twinkle và chu kỳ thời gian tham khảo [HyperFrames registry](https://github.com/heygen-com/hyperframes),
block `starfield`; painter là code canvas tự viết, không chép asset Envato. Tia nắng là hình học
quạt gradient tự viết, khác radial glow hai mép ảnh. Ảnh, nhạc, font và GIF riêng không vào gói.

Đã dựng kiểm demo ambient 8 s 1080p30 và GIF 960×540/15 fps; có sao, đom đóm, sao băng,
sóng/phản xạ hai mép. Demo tia nắng riêng 8 s cùng kích thước, có hình quạt chéo từ góc trên.
Bản full tích hợp dùng cùng clock và envelope lưu sẵn, không animate ảnh gốc.

Preset mặc định được thiết kế cho ảnh 16:9. Chưa chứng minh tự phát hiện mặt, tự thích ứng
9:16, xử lý mọi loại ảnh hay đồng bộ nhạc không có cue. Co giãn canvas chỉ là đổi hệ toạ độ,
không phải chứng nhận bố cục. Unit test draw calls kiểm tính xác định, không thay xem video.
Model baseline và model A/B của skill chưa chạy (`not_run`).
