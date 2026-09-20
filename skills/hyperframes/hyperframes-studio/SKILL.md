---
name: hyperframes-studio
description: Timeline conventions for a HyperFrames project that people will open in Studio - one caption track, one element kind per track, every scene as a sub-composition, and where captions and key content may sit (safe zones). Use when building or editing a project a human will review or edit visually. Not for how to perform an individual edit such as split, trim, retime, volume, copy or swap - that lives in hyperframes-core.
---

# Quy ước timeline cho người mở Studio

> **Nguồn:** `heygen-com/hyperframes` · `skills/hyperframes-studio/SKILL.md` @ **v0.8.51** ·
> Apache-2.0 · hash manifest `b063eaa9eb1e4b9b` (1 file upstream).
> Bản này **đã dịch, rút gọn và biên tập lại** (Apache-2.0 §4(b)).

Một project chạy đúng nhưng timeline rối là project chỉ mình bạn sửa được. Bốn quy ước dưới đây
tồn tại để **người khác mở ra và hiểu ngay**.

## 1. Mỗi cảnh là một sub-composition

Đừng nhét năm cảnh vào một file. Mỗi cảnh một file, nối vào `index.html` bằng host slot. Lợi ích
thật: sửa cảnh 3 không đụng cảnh 1; `snapshot` soi được từng cảnh; và người mở Studio thấy timeline
là một dãy khối có tên, không phải một biển phần tử.

## 2. Một track phụ đề, đúng một

Tất cả phụ đề nằm trên cùng một track. Rải phụ đề ra nhiều track là cách chắc chắn để hai dòng
chồng lên nhau ở đâu đó mà chỉ phát hiện lúc xem bản render cuối.

## 3. Một loại phần tử cho một track

Chữ đi với chữ, hình đi với hình, video đi với video, nhạc đi với nhạc. `data-track-index` **không**
ràng buộc thời gian — nó chỉ là làn hiển thị — nên nó chỉ có một công dụng: làm timeline đọc được.
Dùng sai thì mất luôn công dụng duy nhất đó.

## 4. Vùng an toàn

- **16:9**: chữ quan trọng tránh 5 % mép mỗi bên.
- **9:16**: chừa đỉnh và đáy nhiều hơn — giao diện nền tảng (tên kênh, nút, mô tả) sẽ đè lên đó.
  Phụ đề đặt ở khoảng giữa dưới, không sát đáy.
- **4:5**: coi như 9:16 nhưng chừa hai bên ít hơn.

Kiểm bằng `snapshot` ở vài mốc rồi **nhìn**, đừng suy từ số đo trong CSS.

## Nghiệm thu

Mở `preview --background`, nhìn timeline như một người chưa đọc mã: có đoán được cảnh nào là cảnh
nào không? Có track nào lẫn hai loại phần tử không? Có phụ đề nào rơi ra ngoài vùng an toàn không?
Ba câu đó trả lời được thì project bàn giao được.
