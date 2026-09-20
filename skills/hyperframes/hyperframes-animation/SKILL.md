---
name: hyperframes-animation
description: All animation knowledge for HyperFrames - atomic motion rules, multi-phase scene blueprints, scene transitions, broader motion-design technique, and the seven runtime adapters (GSAP by default, plus Lottie, Three.js, Anime.js, CSS keyframes, Web Animations API, TypeGPU). Use for any motion task - compose two to four atomic rules, load a blueprint, look up a runtime API, or audit an existing composition's choreography. Not for composition structure (hyperframes-core) or camera keyframes (hyperframes-keyframes).
---

# Chuyển động trong HyperFrames

> **Nguồn:** `heygen-com/hyperframes` · `skills/hyperframes-animation/SKILL.md` @ **v0.8.51** ·
> Apache-2.0 · hash manifest `479c716293a26531` (122 file upstream: ~60 luật nguyên tử, ~22 bản
> thiết kế cảnh, 12 adapter runtime).
> Bản này **đã dịch, rút gọn và biên tập lại** (Apache-2.0 §4(b)); thư viện luật và blueprint của
> upstream **không** chép vào repo — đọc upstream khi cần đúng một luật cụ thể.

## Mặc định: ghép luật nguyên tử, đừng chế cảnh từ đầu

Một cảnh tốt thường là **2–4 luật nguyên tử ghép lại**, không phải một hiệu ứng khổng lồ tự nghĩ.
Luật nguyên tử là những đơn vị nhỏ đã được đặt tên ở upstream (chữ hiện theo dòng, số đếm tăng,
camera lướt, ánh sáng nở, thanh chạy, lưới thẻ lắp vào chỗ, con trỏ thao tác trên giao diện…).

Chỉ nạp một **blueprint** (bản thiết kế cảnh nhiều pha) khi cảnh thật sự có nhiều pha nối tiếp và
bạn muốn giữ nguyên nhịp đã được thử: ví dụ mở màn tiêu đề, so sánh hai phía, hành trình camera,
tiết lộ không gian làm việc, chữ gõ máy, sân khấu tiến trình.

## Chọn runtime

| Runtime | Khi nào |
|---|---|
| **GSAP** | mặc định cho gần như mọi thứ — timeline, ease, stagger, transform |
| CSS keyframes / WAAPI | chuyển động nhỏ, lặp, không cần đồng bộ với timeline chính |
| Lottie | đã có sẵn file Lottie do thiết kế giao |
| Three.js | cảnh 3D thật, camera trong không gian |
| Anime.js | khi đã có mã cũ dùng nó — không phải lựa chọn mới |
| TypeGPU | hiệu ứng shader nặng, số lượng phần tử rất lớn |

Trộn hai runtime trong một composition là tự tạo hai nguồn thời gian; chỉ làm khi có lý do và phải
đăng ký cùng một timeline đã tạm dừng.

## Ràng buộc bắt buộc

- **Một timeline, đã `paused`, đăng ký đúng khoá `data-composition-id`.**
- **Tua được ở mọi thời điểm**: engine nhảy tới một mốc bất kỳ rồi chụp khung. Hiệu ứng nào chỉ
  đúng khi chạy tuần tự từ đầu sẽ ra khung sai mà không báo lỗi.
- **Tái lập được**: không `Date.now()`, không `Math.random()` chưa seed, không đo kích thước cửa sổ
  thật, không gọi mạng lúc render.
- **Cấm `repeat: -1`.** Tween vô hạn làm tiến trình render phình tới khi chết — và nó chết sau vài
  phút chứ không chết ngay, nên lỗi hiện ra ở lượt lịch lúc nửa đêm chứ không hiện lúc bạn thử.
- Không tween `display`/`visibility`/`autoAlpha` trên `.clip`; hoạt hình phần tử con.
- Đặt trạng thái đầu bằng `fromTo`, đừng đặt bằng CSS rồi tween đè.

## Soi lại một composition đã có

Trước khi thêm chuyển động vào cảnh người khác viết: đọc bản đồ chuyển động hiện có (phần tử nào
động, vào lúc nào, bằng luật gì). Thêm một tween chồng lên một tween sẵn có trên cùng thuộc tính là
cách tạo ra "lúc được lúc không" — thứ rất khó truy khi chỉ xem bản render.
