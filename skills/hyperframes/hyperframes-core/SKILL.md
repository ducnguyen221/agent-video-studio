---
name: hyperframes-core
description: The HyperFrames composition contract - how to build one renderable project. Use for composition structure, the data-* timing attributes, class="clip", tracks, sub-compositions, variables, framework-owned media playback, deterministic-render rules and validation. Read this before writing any composition HTML, and before editing an existing composition. Not for animation runtime APIs (hyperframes-animation) or for CLI command details (hyperframes-cli).
---

# Hợp đồng composition của HyperFrames

> **Nguồn:** `heygen-com/hyperframes` · `skills/hyperframes-core/SKILL.md` @ **v0.8.51** ·
> Apache-2.0 · hash manifest `77ce4deba31148a2` (11 file upstream).
> Bản này **đã dịch, rút gọn và biên tập lại** (Apache-2.0 §4(b)); `references/*` của upstream
> không chép vào repo — cần chi tiết thì đọc upstream đúng bản trong `upstream.json`.

HyperFrames render video **từ HTML**: một composition là một file HTML mà DOM của nó khai báo thời
gian bằng thuộc tính `data-*`, runtime hoạt hình **tua được**, và phần phát media do framework nắm.

## Bốn cái bẫy hay dính ngay lượt đầu

- **Căn giữa bằng flex hoặc `inset`, đừng dùng `transform: translate(-50%,-50%)`** trên phần tử mà
  sau đó bạn lại tween `x`/`y` bằng GSAP. Hai giá trị đánh nhau, `lint` báo
  `gsap_css_transform_conflict`. Muốn đặt trạng thái đầu thì đặt trong `gsap.fromTo(...)`.
- **Đừng tắt cảnh bằng `tl.set(..., {visibility:"hidden"})`.** Runtime tự ẩn clip hết giờ; làm thêm
  là làm hỏng.
- **`window.__timelines["id"]` phải trùng `data-composition-id` của gốc.** Lệch là im lặng: không
  báo lỗi, chỉ ra video trắng.
- **Đọc dòng thứ hai của bản tóm tắt sau khi render** (`beginframe` hay `screenshot`, chế độ GPU,
  thời gian từng chặng). `screenshot` + GPU phần mềm là đường chậm.

## Hai dạng gốc, không thay thế cho nhau

- **Standalone** (`index.html` ở cấp cao nhất): gốc `<div data-composition-id="…">` nằm thẳng
  trong `<body>`, **không bọc `<template>`**. Bọc vào là toàn bộ nội dung biến mất và `lint` từ chối.
- **Sub-composition** (nạp qua `data-composition-src`): gốc **phải** bọc trong `<template>`. Với
  dạng này bộ lắp ráp **bỏ** `<style>`/`<script>` nằm ở `<head>` của file, nên đặt chúng **bên
  trong** `<template>`. `<link>` thì được nâng lên trong cả hai dạng.
- Đặt cùng một id cho: slot chủ, template bên trong, và khoá `window.__timelines["<id>"]`.

## Kích thước và timeline

- Gốc để `width`/`height: 100%`. Kích thước khung lấy từ `data-width`/`data-height`; **đừng** ghi
  cứng `1920px`/`1080px` vào `#root`.
- **Đúng một** `gsap.timeline({ paused: true })` cho mỗi composition, đăng ký vào
  `window.__timelines["<id>"]`, và chỉ đăng ký **sau khi** dựng xong.
- Độ dài render là `data-duration` của gốc, **không phải** độ dài timeline: timeline dài hơn thì bị
  cắt, ngắn hơn thì giữ khung cuối.
- Đừng tự lồng timeline con vào timeline chủ — runtime tự lồng timeline con đã đăng ký.

## Luật `lint` bắt được, nhưng bắt sau khi bạn đã sai

- Không đặt `transform` khởi tạo bằng CSS rồi lại tween đúng thuộc tính đó bằng GSAP.
- Không bao giờ gắn `crossorigin` lên `<video>`/`<audio>` — bị từ chối vô điều kiện, không có
  cách bỏ qua.
- Một `<video data-start>` không được nằm trong phần tử cha cũng mang `data-start`. Chọn một chỗ
  để định giờ: hoặc cái bọc, hoặc chính video.
- Mọi `<audio>` **phải có `id`** — thiếu id thì bộ trộn không thấy nó và bản render **câm**.
- Không tween `autoAlpha` hay `visibility` trên phần tử `.clip`; hoạt hình phần tử con.
- Khai một `font-family` có tên thì phải có `@font-face` trỏ tới file font đi kèm.

> Một lỗi `lint` **tắt luôn** phần kiểm bố cục và tương phản: `check` sẽ in "0 mẫu" trông như sạch
> mà thật ra chưa chạy gì. Dọn hết lỗi `lint` rồi mới tin những con số đó.

## Luật không thương lượng (lỗi im lặng, cổng tự động có thể không bắt)

- Không đồng hồ lúc render, không `Math.random` không seed, không gọi mạng, không đọc trạng thái
  bàn phím/chuột. **Không `repeat: -1`** — dùng số lần hữu hạn.
- Không `<br>` trong thân chữ; phần tử bị transform phải là block và có kích thước.
- Giữ mọi `id` duy nhất trên **trang đã lắp ráp** — tiền tố id của sub-composition bằng id
  composition.
- Nền phủ toàn khung đặt trên **gốc** composition sẽ bị bỏ ở đường layered-composite (nội dung HDR
  hoặc có chuyển cảnh shader). Trường hợp đó đặt nền lên một phần tử **con** phủ kín.

## Sửa composition đã có

Đọc file trước. Giữ nguyên thời gian, track, id, biến và đường media không liên quan. Muốn biết
trên timeline đang có gì thì chạy `npx hyperframes timeline --json` thay vì đọc `index.html` cùng
mọi file sub-composition. `data-track-index` chỉ là làn hiển thị trong Studio, **không** ràng buộc
thời gian. `data-hidden` ẩn phần tử ở cả xem trước lẫn render, và đảo lại được.

## Cổng nghiệm thu

1. `npx hyperframes check` sạch (0 phát hiện).
2. Project có sub-composition: `snapshot` ở các mốc giữa và **nhìn từng khung**.
3. `preview --background` cho người duyệt xem.
4. `render` **chỉ sau khi** người duyệt đồng ý.
