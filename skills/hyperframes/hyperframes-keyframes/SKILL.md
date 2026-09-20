---
name: hyperframes-keyframes
description: Seek-safe 2D and 3D keyframes in a HyperFrames composition - punch-in, punch-out, zoom, reframe, Ken Burns, camera move, visual match or whip handoff; also GSAP, CSS keyframes, Anime.js, WAAPI, FLIP, motion paths, masks, SVG morph and draw, text trails, 3D depth, and reading the hyperframes keyframes diagnostic. Not for broad scene strategy, brand design, media sourcing, captions or general video planning.
---

# Keyframe tua được: punch-in, zoom, camera move

> **Nguồn:** `heygen-com/hyperframes` · `skills/hyperframes-keyframes/SKILL.md` @ **v0.8.51** ·
> Apache-2.0 · hash manifest `6bc62531ecea9a52` (3 file upstream).
> Bản này **đã dịch, rút gọn và biên tập lại** (Apache-2.0 §4(b)); `references/keyframe-patterns.md`
> của upstream không chép vào repo.

## Luật gốc: mọi thứ phải đúng ở MỘT khung bất kỳ

Engine không phát video từ đầu tới cuối rồi quay màn hình. Nó **nhảy tới một mốc thời gian, dựng
trạng thái ở đó, rồi chụp**. Hệ quả:

- Chuyển động nào được tính dồn (mỗi khung cộng thêm một chút vào khung trước) sẽ sai ngay khi
  engine nhảy cóc — và sai **im lặng**, video vẫn ra, chỉ là sai.
- Mọi keyframe phải mô tả **trạng thái tuyệt đối tại thời điểm t**, không phải "so với khung trước".
- Không dùng đồng hồ thực, không dùng số ngẫu nhiên chưa seed, không đọc kích thước thật của cửa sổ.

## Quy trình

1. Nói rõ **cú máy** muốn có bằng lời trước: đẩy vào đâu, trong bao lâu, dừng ở khung hình nào.
2. Viết keyframe trên một timeline **đã tạm dừng**, thuộc về composition đó.
3. Ưu tiên `transform` (`scale`, `x`, `y`, `rotate`) — chúng chạy trên GPU và tua chính xác. Tránh
   hoạt hình `width`/`height`/`top`/`left`: vừa chậm vừa làm bố cục nhảy.
4. Đặt trạng thái đầu bằng `fromTo`, **không** đặt bằng CSS rồi tween đè lên cùng thuộc tính.
5. Kiểm bằng `snapshot` ở ít nhất ba mốc: trước cú máy, giữa, và sau khi dừng.

## Bảng chọn cơ chế

| Muốn gì | Dùng gì |
|---|---|
| Đẩy vào / lùi ra trên ảnh tĩnh (Ken Burns) | `scale` + `x`/`y` trên phần tử ảnh, ease vào–ra nhẹ |
| Đổi khung hình trong một cảnh | `transform-origin` đặt đúng điểm quan tâm rồi `scale` |
| Chuyển cảnh kiểu "bắt hình" | hai phần tử cùng hình dạng, khớp vị trí và kích thước ở mốc giao |
| Quét ngang nhanh (whip) | dịch mạnh + nhoè chuyển động, thời lượng rất ngắn |
| Đi theo đường cong | motion path, không phải chuỗi tween thẳng nối nhau |
| Vẽ nét SVG, biến hình SVG | thuộc tính `stroke-dashoffset` / morph, tính theo t tuyệt đối |
| Chiều sâu 3D | lớp có `translateZ` khác nhau + perspective trên cha chung |

## Thời lượng gợi ý

Punch-in cảm giác "có chủ ý" ở khoảng 0,6–1,2 s; dưới 0,3 s bị đọc thành giật, trên 2 s bị đọc
thành trôi. Cú máy nên **kết thúc trước** khi lời đọc chuyển ý, không kết thúc cùng lúc.

## Đọc chẩn đoán

`npx hyperframes keyframes <project> --json` cho thấy quỹ đạo chuyển động và chỗ nào không tua
được. Nó **không** chẩn đoán việc cắt clip hay thời gian clip — chuyện đó thuộc `hyperframes-core`.
