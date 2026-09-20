# Một "project" ở đây là gì

Mỗi thư mục con của `projects/` là **một project HyperFrames**: ba file cấu hình cộng với
`index.html` do template sinh ra mỗi lần render.

```
projects/<tên>/
├── hyperframes.json   bố cục thư mục + registry của HyperFrames (bắt buộc)
├── package.json       ghim ĐÚNG bản engine — không `^`, không bản trôi
├── meta.json          id/tên/ngày tạo
├── index.html         SINH RA mỗi lần render, đừng sửa tay rồi mong nó còn đó
└── assets/            ảnh, clip, filler của riêng project
```

## Tạo project mới

Đừng chép tay: `video-studio render --project news …` tự tạo `projects/news/` và chép ba file
cấu hình còn thiếu từ `demo/`. Cách đó giữ một điều quan trọng — **không bao giờ đè** file bạn
đã sửa, chỉ bù file thiếu.

Muốn một project trống để tự viết composition: chép `demo/` sang tên mới, rồi sửa `meta.json`.

## Ba luật cứng khi viết composition

1. **Không lặp vô hạn.** `repeat: -1` của GSAP làm tiến trình render phình tới khi chết; mọi
   vòng lặp phải có số lần hữu hạn tính từ tổng thời lượng.
2. **Phải tái lập được.** Không `Date.now()`, không `Math.random()`, không hiệu ứng theo thời
   gian thực hay theo chuột: mỗi phần tử có `data-start` / `data-duration`, engine tua tới đâu
   thì khung hình ở đó phải luôn giống nhau.
3. **Xem trước bằng đúng bản sẽ render.** `video-studio preview --project <tên>` dùng bản ghim
   trong `station.json`; soi bằng một bản khác là soi một video khác.
