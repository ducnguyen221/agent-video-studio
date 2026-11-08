# Đồng hồ và GIF

Hai painter không gọi mạng, không dùng thời gian máy hoặc random trong render. Caller sở hữu
timeline paused, tween một state.t tuyến tính từ 0 tới duration, onUpdate gọi painter.
Đăng ký timeline vào `window.__timelines`. Không thêm requestAnimationFrame loop hoặc repeat vô hạn.
Canvas trả về lỗi khi thiếu context hoặc time/power không hữu hạn, không nuốt lỗi rồi render nền trống.
Mỗi painter xoá canvas trước khi vẽ: khi kết hợp ambient và nắng, phải dùng hai canvas riêng,
kể cả lúc power của nắng bằng 0; dùng chung sẽ xoá lớp trước.

Demo loop: 8 s, 30 fps MP4; GIF 960×540,15 fps, palette 192 màu, loop 0. Không thêm frame ở t=8
vì frame đầu đã đại diện biên vòng. Kiểm frame119→frame0 ở GIF và seek cùng t hai lần.
FFmpeg: lấy fps/scale, split thành palettegen và paletteuse; `sierra2_4a` phù hợp glow.
Không lấy GIF nén chồng vào full; dùng painter gốc, giữ ảnh gốc nguyên nếu brief đã khoá.

Nhạc: lưu envelope RMS hoặc beat grid trước; nội suy strength theo envelope. Ghi hop và smoothing
trong dự án để có thể dựng lại. Tia nắng dùng cửa sổ thời gian rõ với fade hai đầu;
đừng bật liên tục chỉ vì có beat. 0 power phải clear canvas hoàn toàn.
Tua 0 → 6 → 2 → 6: hai frame6 phải giống nhau; test toán/draw calls chưa thay kiểm MP4.
