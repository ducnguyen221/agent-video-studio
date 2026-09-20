---
name: figma
description: Import Figma content into a HyperFrames composition - rendered assets, brand tokens, components and storyboard sections turned into motion, with frames read as states rather than slides. Use when the user pastes a figma.com link or asks to bring a Figma design, frame, logo, brand or animation into a video or composition. Needs a Figma token in the environment; motion and shader import have no REST endpoint and stay manual.
---

# Đưa nội dung Figma vào composition

> **Nguồn:** `heygen-com/hyperframes` · `skills/figma/SKILL.md` @ **v0.8.51** · Apache-2.0 ·
> hash manifest `642cce1b5e211182` (2 file upstream).
> Bản này **đã dịch, rút gọn và biên tập lại** (Apache-2.0 §4(b)).

## Xác thực: một khoá, có phạm vi

Cần một token Figma đặt trong **biến môi trường**, không bao giờ ghi vào file trong repo, không dán
vào log, không đưa vào ảnh chụp màn hình.

> **Luật của repo này:** mọi bí mật nằm ở kho bí mật của trạm và được đọc lúc chạy. Agent **không**
> mở file bí mật để thay script; agent gọi script, script tự đọc.

## Năm chặng, độ tự động giảm dần

1. **Tài sản** — xuất ảnh/SVG đã render từ một node. Tự động được, qua REST.
2. **Token** — màu, cỡ chữ, khoảng cách. Tự động được; đây là thứ đáng lấy nhất vì nó giữ cho video
   trông đúng thương hiệu mà không phải nhìn bằng mắt rồi đoán mã màu.
3. **Component** — cấu trúc một thành phần. Lấy được, nhưng luôn phải sửa tay sau khi lấy.
4. **Chuyển động** — **không có REST endpoint**. Phải đọc thiết kế rồi tự dựng; nếu có connector thì
   nó chỉ hỗ trợ, không thay người.
5. **Shader** — gần như thủ công hoàn toàn.

## Đọc frame như trạng thái, không như slide

Một chuỗi frame trong Figma thường là **các trạng thái của cùng một màn hình**, không phải các
slide nối nhau. Dịch đúng cách là: một cảnh, nhiều trạng thái, chuyển động giữa chúng. Dịch sai
cách — mỗi frame một cảnh cắt cứng — cho ra video giật và mất hết ý đồ của người thiết kế.

## Tính tái lập

Tài sản kéo từ Figma phải được **đóng băng thành file trong project** kèm dòng sổ (file key, node
id, ngày lấy). Trỏ thẳng vào URL Figma là mời một lượt render tương lai ra kết quả khác — hoặc
hỏng hẳn khi ai đó sửa file thiết kế.

## Bàn giao

Ghi lại: node nào đã lấy, cái gì phải dựng tay, và chỗ nào bản video **cố ý** khác bản thiết kế.
Người thiết kế sẽ so từng pixel; danh sách khác biệt có chủ ý tiết kiệm cả một vòng phản hồi.
