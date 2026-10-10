---
name: video-cleanup
description: Use when an agent must inspect, preview, remove, blur, cover, or crop a region in an existing local video with the video-studio cleanup command. Not for invisible watermarks, provenance metadata, VFR/HDR footage, or model-based inpainting.
---

# Chỉnh vùng trong video local

`video-studio cleanup` xử lý trực tiếp bằng FFmpeg. Tác vụ này không cần HyperFrames, Node,
Chromium hay trạm video. Đọc metadata trước, chọn ROI/phương pháp/thời gian có căn cứ, xem
preview rồi mới tạo bản giao riêng.

## Luồng thao tác

1. `video-studio cleanup inspect --input <video.mp4> --json` để đọc geometry, thời lượng,
   audio, hash và trạng thái CFR. `supported_for_cleanup=false` nghĩa là cần đổi nguồn hoặc
   dừng ở inspect; không tìm cách ép chạy.
2. Xác định ROI theo `x,y,width,height` **pixel** từ góc trên trái khung hình, cùng khoảng
   `--start` / `--end` tính bằng giây từ đầu video. ROI phải nằm gọn trong khung và cả bốn
   giá trị phải chẵn để khớp chính xác chroma 4:2:0; `delogo` cần cách mép khung ít nhất 1 pixel.
3. Xem trước bằng `video-studio cleanup preview --input <video.mp4> --out <thư-mục-preview>
   --name preview.mp4 --method <delogo|blur|cover|crop> --roi x,y,w,h --start S --end E --json`.
4. Khi preview phù hợp, chạy `apply` với cùng input, method, ROI và time range; đặt `--out`
   thành thư mục nhận bản giao và `--name` thành tên MP4 mới.
5. Chạy `video-studio cleanup verify --input <video.mp4> --out <thư-mục-bản-giao>
   --name <tên.mp4> --json`. Đọc từng `technical_checks`; `visual_review` và `overall` vẫn
   là `NOT_CHECKED` cho tới khi người xem kiểm video.

## Chọn phương pháp và báo đúng kết quả

- `delogo` nội suy vùng từ pixel lân cận. Có thể hợp với logo cố định trên nền đơn giản; không
  đảm bảo khôi phục pixel nền ban đầu.
- `blur` làm mờ vùng; `cover` tô màu đặc. Cả hai là che, không phải xóa/lấp nền.
- `crop` bỏ phần khung nằm ngoài ROI và đổi kích thước toàn video; chỉ dùng khi chấp nhận bố cục
  và aspect ratio mới. ROI crop cần tọa độ và kích thước chẵn.
- Logo nhìn thấy là pixel trong khung hình. Tính năng này không xử lý SynthID, C2PA hay metadata
  chứng thực nguồn gốc.

## Giới hạn media

Phase 1 chỉ xử lý MP4 SDR `yuv420p`, video CFR có PTS đã quét toàn bộ, không có rotation
metadata, và stream start time đo được. HDR, VFR, rotation, pixel format khác hoặc mốc thời gian
không xác định bị từ chối trước khi render. Apply mã hóa lại video H.264, giữ frame count/rate,
copy audio packet như nguồn và kiểm lại cấu hình audio, hash, duration, AV start offset cùng
geometry. Nếu bất kỳ kiểm tra kỹ thuật nào sai, lệnh không công bố output thành công.

Output không ghi đè file có sẵn. Apply tạo `<tên.mp4>.cleanup.json` với SHA-256 nguồn/output,
thông số thao tác và kết quả kiểm; verify đọc lại file hiện tại thay vì tin kết quả cũ trong
manifest. Hash/metadata không thay cho việc xem toàn bộ video và nghe tiếng.
