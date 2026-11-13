---
title: Prompt Motion reference usage
summary: Select a reference by scene purpose and adapt it into a deterministic HyperFrames composition.
---

# Dùng thư viện để chọn cảnh và dựng bản riêng

Kho này là **tài liệu tham chiếu và đề xuất dựng**, không phải bộ template đã chạy. Tra [INDEX.md](INDEX.md), chọn motion theo việc cảnh cần làm, rồi đọc file của motion. Không coi hình đẹp trên web là bằng chứng một composition HyperFrames đã render được.

[Đối chiếu độ phủ nguồn](source/coverage.json) liệt kê 260 URL sitemap: 238 gallery, 2 trang template chi tiết và 20 trang không phải entry motion. Trang blog và bộ lọc không được tính thành motion riêng.

## Chọn trước khi dựng

1. Chia kịch bản thành các nhịp: hook, giải thích, chứng minh, chuyển ý, nhấn mạnh, chốt, CTA. Mỗi cảnh cần một ý chính.
2. Lọc theo `scene_roles`, `primary_recommended_ratio`, `ratio_fit`, `content_capacity`, `intensity` và `coverage` trong [index.json](index.json). Muốn lớp phủ, lọc thêm `overlay_alternative.possible`; đây là khả năng thiết kế alpha riêng, không phải source overlay có sẵn. Đọc [TAXONOMY.md](TAXONOMY.md) để hiểu các giá trị.
   Không đọc thẳng `index.json` (≈1,8 MB): dùng `python scripts/motion_find.py` ở gốc repo — ví dụ `--role proof --ratio 16:9 --technique count-up` hoặc `--q "so do"` (không phân biệt dấu), thêm `--individual` để bỏ baseline dùng chung của nhóm, `--json` để lấy tóm tắt máy đọc. Lệnh luôn in UTF-8 và chỉ trả 10 dòng mặc định.
   `primary_recommended_ratio` dùng để xếp hạng, không phải điều kiện loại bỏ mọi mẫu khác khung cần giao. Sau khi lọc vai trò/vùng, đọc `ratio_fit` để cân nhắc các phương án `preferred`, `adaptable` hoặc `requires_redesign` và công sức bố trí lại.
3. Đưa người dùng 2–3 phương án có khác biệt thực sự. Mỗi phương án ghi **ID · tên · link nguồn · vai trò cảnh · tỉ lệ đề xuất · vùng màn hình đề xuất**, kèm cách thích nghi khi đổi khung. Ví dụ cấu trúc: `PM-… | tên | nguồn | hook | 9:16 | phần giữa khung`. Những thông số đề xuất là quyết định thiết kế mới, không phải số đo video gốc.
4. Chọn một motion chính cho mỗi nhịp. Ghép hiệu ứng khi chúng cùng dẫn mắt đến một thông điệp; tránh chất nhiều nhịp mạnh liên tiếp làm mất điểm nhấn.
5. Dùng prompt mới trong entry làm brief triển khai. Điền nội dung, thương hiệu, font có quyền dùng, số liệu, thời lượng và khung hình thật của dự án. Không dùng tên thương hiệu minh họa trong nguồn làm thương hiệu mặc định.

## Đọc đúng hai lớp dữ kiện

`source_facts` giữ dữ kiện Terra thu từ nguồn, URL và dấu vết kiểm chứng. `sol_analysis` là phân tích và khuyến nghị của Sol. *Terra* và *Sol* là tên hai bước xử lý của kho (thu dữ kiện và phân tích), không phải tác giả hay người thật. Mọi `unknown` là thiếu bằng chứng; không tự suy nó thành một giá trị chính xác.

- **Tỉ lệ/kích thước nguồn** khác **tỉ lệ dựng đề xuất**. Kích thước thẻ preview hay cửa sổ browser không chứng minh kích thước video gốc.
- **Thời lượng nguồn** khác **thời lượng đề xuất**. Prompt có nói một số giây vẫn cần phân biệt với media được đo; không gọi đó là duration đo được.
- **Vùng nội dung** khác **khung preview**. Một clip có nền phủ khung nhưng chủ thể chỉ chiếm giữa màn; `coverage` khuyến nghị chỉ cách dùng trong bản dựng mới.
- **Công nghệ được nguồn mô tả** khác **runtime đã xác minh**. Thấy hiệu ứng giống 3D không chứng minh nguồn dùng Three.js. Khuyến nghị DOM/SVG/Canvas/WebGL là đường dựng mới, trừ khi có bằng chứng source rõ ràng.
- **Đã đọc metadata/prompt** khác **đã xem đủ chuyển động**. Trạng thái quan sát và hạn chế được giữ trong từng entry.

## Prompt và quyền sử dụng

Không lưu hàng loạt prompt nguyên văn, source code, video hoặc thumbnail của bên thứ ba khi chưa có quyền phân phối lại. `original_prompt_archived: false` có nghĩa bản gốc không nằm trong kho này. Link nguồn dùng để mở lại và kiểm tra; quyền xem/copy trên website không tự đồng nghĩa với quyền phân phối trong plugin.

Prompt dựng trong mỗi entry do Sol viết mới bằng tiếng Việt, dựa trên ý tưởng chuyển động và dữ kiện đã thu. Đây là **bản chuyển thể HyperFrames nguyên gốc của kho**, không phải prompt gốc, không cam kết pixel giống nguồn, và không cấp quyền đối với media, font, nhãn hiệu hoặc code của tác giả nguồn. Chỉ mang media vào dự án khi đã xác nhận quyền dùng cho dự án đó.

## Hợp đồng triển khai HyperFrames

- Đọc `hyperframes-core` và `hyperframes-animation` trước khi viết HTML. Dùng một `gsap.timeline({ paused: true })` cho mỗi composition; đăng ký vào `window.__timelines` bằng đúng `data-composition-id`, sau khi dựng xong timeline.
- Mọi trạng thái phải suy ra từ thời gian tuyệt đối. Không `Date.now()`, tương tác chuột, mạng lúc render, random chưa seed, hoặc vòng `requestAnimationFrame` tự chạy. Không `repeat: -1`; số chu kỳ hữu hạn nằm trong `data-duration`.
- DOM/SVG phù hợp chữ, thẻ, mask, đường vector, diagram và phần lớn hiệu ứng giao diện. Canvas/WebGL chỉ khi chất liệu, số lượng điểm hoặc không gian 3D thực sự cần; redraw trực tiếp theo thời gian seek, không dựa tích lũy frame trước. Chỉ có 3D giả bằng CSS thì không tự nâng lên Three.js.
- Đặt trạng thái đầu bằng `fromTo`. Không tween visibility/autoAlpha trên `.clip`; tween phần tử con. Không đặt CSS transform lên cùng phần tử bị GSAP tween x/y/scale.
- Tham số hoá màu, text, dữ liệu và kích thước. Tải font/media cục bộ hợp lệ trước render. Không nhúng CDN hoặc tài sản nguồn chưa có quyền vào bản phân phối.
- Khung dọc: xếp lại quan hệ, giảm panel, tăng cỡ chữ và chừa vùng phụ đề theo dự án; không crop screenshot có chữ. Khung vuông: gom một tiêu điểm, đưa nhãn phụ ra vành. Vùng đề xuất là hộp chuẩn hoá cần chỉnh theo canvas và nội dung thật, không phải bố cục đã QA mọi tỉ lệ.
- Giữ trạng thái cuối đủ đọc; thường tối thiểu 0,8 giây sau chuyển động cuối theo skill motion-graphics. Thời lượng và nhịp cụ thể phải chốt theo nội dung thật.
- Với overlay, nền trong suốt và kênh alpha cần đường xuất hỗ trợ alpha. Video MP4 thường không giữ alpha. Đừng gọi một motion là overlay chỉ vì nó nhỏ trong preview.

## Kiểm chứng trước khi nâng thành template

Với mỗi bản dựng mới: lint/check sạch → snapshot tại đầu, giữa các pha, cuối và sau seek ngược → xem chữ, clipping, z-order, tương phản và vùng phụ đề → preview cho người duyệt → render đúng quy trình studio khi được giao. Thử tỉ lệ cần giao riêng, không suy PASS từ 16:9 sang 9:16.

Chỉ sau chạy thật mới ghi một template vào catalog có code và tier thích hợp. Các entry ở đây giữ `runtime_tested: false` cho tới khi có bằng chứng của đúng bản triển khai; không tự đổi sang tier S/A vì motion nguồn trông hoàn thiện.
