---
title: Motion design synthesis from Prompt Motion briefs
summary: Reusable design decisions inferred from full public briefs, separated from unverified rendered behavior.
---

# Những gì có thể tái dùng từ các brief

Đây là **phân tích của Sol dựa trên brief và metadata**, không phải báo cáo xem và đo toàn bộ video. Nhiều prompt chỉ yêu cầu một showreel ngắn với toàn quyền sáng tạo; từ prompt như vậy không thể truy ngược chính xác cấu trúc hình ảnh của clip. Những brief chi tiết hơn giúp rút ra cách tổ chức chuyển động, nhưng không chứng minh bản render đã làm đúng chúng.

## Sáu cơ chế đáng đưa vào cách thiết kế cảnh

| Cơ chế | Tham chiếu | Vì sao hữu ích | Chuyển sang HyperFrames |
|---|---|---|---|
| Một vật thể liên tục qua nhiều trạng thái | [UI morph](motions/twoclipping-5cba86.md), [photo-print film](motions/twoclipping-221cab.md) | Người xem nhận ra cùng một vật dù hình dạng/chức năng đổi; giảm cảm giác các slide rời | Giữ anchor và một wrapper; tween thuộc tính con theo pha, chỉ đổi một quan hệ lớn mỗi nhịp |
| Camera giải thích cấu trúc | [landing-page camera](motions/twoclipping-d89be5.md), [3D template](motions/template-realtime.md) | Tiến/lùi và đổi góc giúp tiết lộ quan hệ giữa chi tiết và toàn thể | Định nghĩa các pose camera và khoảng chuyển hữu hạn; một nguồn thời gian, không scroll/chuột thật |
| Cảnh lớn chứa nhiều nhịp | [gallery promo](motions/antonio-kodheli-490109.md) | Một world layer giữ quan hệ card → gallery → detail; chuyển cảnh có địa chỉ thay vì bay ngẫu nhiên | Layout world coordinates trước, camera hoặc wrapper transform sau; giữ đối tượng ở cùng vị trí logic khi match-cut |
| Motif tạo mạch kể chuyện | [showreel template](motions/template-showreel.md), [orange dot](motions/ultimaxbt-bbebf5.md) | Một ý tưởng có biến thể dễ nhớ hơn danh sách kỹ xảo | Chọn motif gắn thông điệp, dùng 2–4 quy tắc nguyên tử; chừa nhịp yên để tạo tương phản |
| Hình và âm cùng một sự kiện | [collision machine](motions/kamstudiolabs-447565.md), [beat ball](motions/gorden-sun-041f56.md) | Âm thanh có nguyên nhân nhìn thấy, không chỉ rải whoosh lên mọi tween | Lập event table trước; pose, cue hình và audio dùng cùng mốc, không chạy mô phỏng tích lũy |
| Giải thích bằng trạng thái có nghĩa | [token bucket](motions/parkerrex-1a54fe.md), [Git](motions/yunn260414-60d996.md) | Sự thay đổi thể hiện cơ chế, không biến diagram thành trang trí | Tạo bảng state/input/output, rồi vẽ từ time; dữ liệu và hình lấy cùng mô hình, không animate độc lập |

Motif và orange-dot mapping là đề xuất đọc thiết kế mới; prompt mở không đủ xác minh đường đi của chấm trong clip. Các hướng dựng riêng đã được ghi rõ trong entry để tránh biến suy luận thành fact nguồn.

## Chọn đơn vị chuyển động theo ý nghĩa

- **Hook:** một biến đổi dễ nhận ra, một câu chủ đạo. Độ mạnh nằm ở tương phản trước/sau; nhiều chuyển động cùng lúc thường làm mất vị trí cần nhìn.
- **Explainer:** xuất hiện theo nguyên nhân → thao tác → kết quả. Con trỏ chỉ nên có khi thao tác sản phẩm là thông điệp; không thêm con trỏ để giả clip đang chạy thật.
- **Proof:** scale biểu đồ, nhãn và số lấy từ cùng dữ liệu. Một trường hạt hoặc số đếm không biến nội dung chưa kiểm thành bằng chứng.
- **Transition:** chuyển vật thể đang có sang vai trò mới hoặc đổi khung nhìn để lộ bối cảnh. Dịch toàn cảnh chỉ hữu ích khi có quan hệ không gian rõ.
- **Closing:** giảm số vật chuyển động, trả hierarchy về tên và câu chốt. Kết một vòng hình học không bắt buộc timeline phải lặp vô hạn.

## Tách motion đơn vị khỏi phim dài

Kho có cả brief launch nhiều cảnh, video có lời đọc, phim hoạt hình và cả trò chơi/skill. Chúng hữu ích làm tham chiếu, nhưng không cùng đơn vị với một sting vài giây. Ví dụ [portfolio](motions/wani-shola-16ca7a.md), [Sotto](motions/1stnoel-c20a89.md) và [silent short](motions/kamstudiolabs-0b0824.md) cần general-video nếu dựng toàn bộ. Khi dùng motion-graphics, trích một beat có điểm bắt đầu/kết thúc rõ; giữ phần còn lại trong storyboard.

## Bố cục là một quyết định mới

Nhãn UI/Charts không tự cho biết một clip hợp khung dọc. Với screenshot/desktop nhiều cột, khuyến nghị bắt đầu ngang và thiết kế lại bản dọc bằng một tác vụ nổi bật. Với hình biến đổi tập trung ở giữa, khung vuông thường thuận tiện. Với cảnh nhân vật/camera, kiểm quan hệ chủ thể và vật cản ở cả đầu, giữa, cuối đường đi; một frame đầu đẹp không chứng minh camera không cắt mất nội dung sau đó.

`primary_recommended_ratio`, `ratio_fit`, hộp chuẩn hoá và sức chứa là các ước lượng này. Chúng giúp chọn nhanh, không thay việc kiểm snapshot trên canvas thật. Overlay cần thiết kế nền/alpha riêng; link MP4 nguồn không chứng minh nguồn có alpha.

## Chuyển thể tốt cần đổi nguồn thời gian

Trong website, hiệu ứng có thể chạy theo scroll, mouse, audio realtime hoặc physics. Trong HyperFrames, renderer có thể nhảy thẳng đến bất kỳ mốc nào. Đường chuyển thể an toàn là **state = function(time, parameters, seeded assets)**: animation, camera, particle và audio cue dùng cùng một timeline đã paused. Có thể chọn DOM, SVG, Canvas hoặc Three.js; điều quyết định là trạng thái có tái lập và seek ngược được hay không.

Những adapter trong từng entry mới là hướng dẫn thiết kế, chưa là mã đã chạy. Muốn nâng thành template tái dùng: dựng một bản cụ thể, kiểm lint/check, nhìn snapshot khi seek không tuần tự và render thật đúng phiên bản engine của dự án; sau đó mới đưa code có chứng cứ vào catalog template.
