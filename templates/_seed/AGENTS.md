# Project HyperFrames — luật cho agent làm việc trong thư mục này

Thư mục này là **một project render**: `index.html` là composition gốc, `hyperframes.json` khai
bố cục thư mục, `package.json` **ghim đúng một bản engine**, `meta.json` là tên/mô tả.

## Lệnh

```
video-studio preview --project <tên>            # studio xem trước (Ctrl+C để dừng)
video-studio render  --project <template> …     # dựng theo template + spec của video-studio
npx --yes hyperframes@<bản ghim> lint           # kiểm composition trước khi render
```

Bản engine lấy từ `station.json` của trạm (hoặc biến `HYPERFRAMES_VERSION`) — **luôn là một bản
cụ thể `x.y.z`**. Đừng thay bằng một bản trôi: lượt render đêm nay và lượt render tuần sau phải
là cùng một engine, nếu không thì "video tự nhiên khác đi" mà không ai đổi gì.

## Ba luật cứng

1. **Mọi phần tử định thời phải khai `data-start` và `data-duration`.** Engine tua timeline tới
   một mốc rồi chụp khung; phần tử không khai mốc thì khung chụp được là ngẫu nhiên.
2. **Timeline `paused`, đăng ký vào `window.__timelines["<id>"]`.** Không `Date.now()`, không
   `Math.random()`, không `requestAnimationFrame` tự chạy, không hiệu ứng theo chuột — hai lần
   render cùng một file phải ra cùng một video.
3. **Không lặp vô hạn.** `repeat: -1` của GSAP làm tiến trình render phình tới khi chết. Mọi
   vòng lặp tính số lần hữu hạn từ tổng thời lượng.

## Tài sản

Ảnh, clip, font riêng để trong `assets/` của project này và tham chiếu bằng **đường tương đối**.
Đường tuyệt đối làm project không chạy được trên máy khác — và trong filtergraph của ffmpeg, dấu
`:` của ổ đĩa Windows còn làm vỡ cả câu lệnh.
