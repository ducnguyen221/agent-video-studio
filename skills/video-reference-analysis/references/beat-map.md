# Danh mục yếu tố soi mỗi beat

Dùng khi điền bảng beat của `reference-map.md`. Một beat là một đoạn có một việc rõ với người
xem; đổi việc là sang beat mới. Ô nào không quan sát được thì ghi «không rõ», không suy ra.

## Lời

- Câu mở (hook): nói gì trong vài giây đầu, hứa điều gì hoặc đặt câu hỏi gì.
- Lời hứa: video cam kết người xem sẽ nhận được gì, và khi nào lời hứa được thực hiện.
- Chuyển ý: câu nối giữa hai beat, cách báo «tiếp theo».
- Độ dài câu và nhịp nói; chỗ nhấn mạnh hoặc lặp lại có chủ ý.

## Hình

- Cỡ cảnh (toàn, trung, cận) và góc nhìn.
- Chữ trên màn hình: nội dung, vị trí, lúc xuất hiện so với lời.
- Chuyển động: máy quay, phóng/thu, đồ họa chạy; có hay không.
- Vật hoặc người chính trong khung; cái gì dẫn mắt.

## Âm

- Nhạc: có không, đổi theo beat thế nào, to nhỏ so với lời.
- Hiệu ứng âm: tiếng chuyển cảnh, nhấn, môi trường.
- Khoảng lặng: chỗ nào dừng và dừng bao lâu.

## Nhịp

- Độ dài beat (giây) và độ dài các cảnh trong beat.
- Mật độ cắt: số lần cắt mỗi 10 giây; chỗ nhanh lên hay chậm lại.
- Điểm đảo nhịp: chỗ video đột ngột đổi tốc độ.

Khi điền bảng: **Nhịp** và **Chuyển động** (mục Hình) cùng đi vào cột «Cắt/hiệu ứng».

## Việc làm cho người xem

Chọn một hoặc hai, ghi lý do bằng chứng:

- giữ chân (gài câu hỏi, hứa phần sau);
- giải thích (đưa kiến thức, ví dụ);
- cho thấy (minh chứng bằng hình);
- gây cảm xúc (hài, bất ngờ, đồng cảm);
- kêu gọi (theo dõi, bình luận, làm thử).

## Bằng chứng cho mỗi ô

Ghi nơi người khác mở ra kiểm lại được: khung ở `evidence/frames/frames.json` (mốc `pts_time`,
chính xác), ô ở `evidence/tiles/tiles.json` (mốc gần đúng) hoặc cue trong `transcripts/<stem>.json`
(độ mịn `cue`). Nhận xét không có nguồn nào trong ba loại này thì chuyển sang «Chưa kiểm chứng».
