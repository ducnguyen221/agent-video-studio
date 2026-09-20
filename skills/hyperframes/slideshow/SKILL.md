---
name: slideshow
description: Author a HyperFrames slideshow - a presentation, pitch deck or interactive deck with discrete slides, fragment reveals, branching, hotspot navigation and presenter mode with speaker notes; also converts an existing page into a deck. The output is a navigable deck, not a rendered MP4. If the user did not explicitly ask for a slideshow, confirm before authoring.
---

# Deck bấm được, không phải video

> **Nguồn:** `heygen-com/hyperframes` · `skills/slideshow/SKILL.md` @ **v0.8.51** · Apache-2.0 ·
> hash manifest `71174bff2d869f18` (2 file upstream).
> Bản này **đã dịch, rút gọn và biên tập lại** (Apache-2.0 §4(b)).

## Hỏi trước khi làm

Đầu ra của skill này là **deck điều hướng được**, không phải MP4 chạy thẳng. Người dùng không nói
rõ muốn deck thì **hỏi lại**: "anh muốn một file video chạy liền, hay một deck bấm qua từng slide?"
Làm nhầm hướng là làm lại từ đầu, vì cấu trúc hai thứ khác hẳn nhau.

## Hai phần của một deck

1. **Các cảnh** — khai đúng như mọi composition bình thường (mỗi slide là một cảnh/sub-composition).
2. **Một khối JSON** nhúng trong composition, mô tả deck: thứ tự slide, điểm dừng tiết lộ
   (fragment), điểm bấm (hotspot), nhánh rẽ, ghi chú cho người trình bày.

Hai phần này phải khớp nhau: mỗi mục trong khối JSON trỏ tới một cảnh có thật, và ngược lại mỗi
cảnh dự định làm slide phải có mặt trong khối JSON — cảnh không được khai sẽ không bao giờ hiện ra
và **không có lỗi nào báo** chuyện đó.

## Luật viết slide

- **Một slide một ý.** Slide có ba ý là ba slide, hoặc là một slide có ba fragment.
- **Fragment là điểm dừng, không phải hiệu ứng.** Dùng nó khi người trình bày cần nói xong một ý
  rồi mới cho ý sau hiện; đừng dùng nó để làm chữ bay.
- **Nhánh rẽ phải quay về được.** Mọi hotspot dẫn đi phải có đường quay lại mạch chính, nếu không
  người trình bày bị kẹt giữa buổi.
- **Ghi chú người trình bày viết bằng lời nói thật**, không phải chép lại chữ trên slide.
- **Dọn media khi rời slide.** Video/nhạc của slide trước phải dừng và tắt tiếng, nếu không hai
  nguồn tiếng chồng lên nhau khi người ta bấm nhanh.

## Chuyển một trang có sẵn thành deck

Được, nhưng phải cắt theo **ý**, không cắt theo chiều cao màn hình. Một trang dài không tự chia
thành slide tốt; chỗ ngắt phải là chỗ ý đổi.

## Nghiệm thu

`npx hyperframes present <project-dir>` rồi **bấm hết một lượt**: mọi fragment, mọi hotspot, mọi
nhánh, và đường quay về. Deck chỉ xem bằng mắt qua timeline là deck chưa được kiểm.
