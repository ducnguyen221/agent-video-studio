---
name: embedded-captions
description: Add captions or subtitles to an existing single-subject talking-head video without editing the footage - plain verbatim captions, cinematic captions embedded behind the subject, VFX captions, or a named identity from the style catalog. Route by visual identity, not by backend engine. The quiet rail is the default; embed every word only when the user explicitly asks for a fully cinematic treatment. Runs locally end to end, including transcription and subject matting. Split multi-shot footage before applying it. Not for graphic overlay cards - that is talking-head-recut.
---

# Phụ đề gắn vào video người nói

> **Nguồn:** `heygen-com/hyperframes` · `skills/embedded-captions/SKILL.md` @ **v0.8.51** ·
> Apache-2.0 · hash manifest `f1b298aa899d86df` (142 file upstream, trong đó **44 file font
> `woff2`** — **không** chép vào repo này, giấy phép từng font chưa kiểm).
> Bản này **đã dịch, rút gọn và biên tập lại** (Apache-2.0 §4(b)); catalog kiểu chữ và các
> `references/*` của upstream không chép vào repo.

## Hai đường, một mặc định

- **Rail** (mặc định): phụ đề chạy trên một dải yên tĩnh, cố định vị trí. Người xem đọc được, hình
  không bị phá. **Gần như luôn chọn cái này.**
- **Embed**: từng chữ được cài vào khung hình, có chữ đi sau đầu người nói. Đẹp, tốn công, và dễ
  làm hỏng nếu footage không sạch. Chỉ chọn khi người dùng **nói rõ** muốn xử lý kiểu điện ảnh.

Định tuyến theo **hình thức nhìn thấy**, không theo engine phía sau: người dùng mô tả "chữ bay",
"phụ đề đơn giản", "kiểu tạp chí" — đó là dữ liệu để chọn, còn chuyện nó chạy bằng gì là việc của
bạn.

## Điều kiện đầu vào

- **Một người nói, một cú máy.** Footage nhiều cảnh phải **cắt ra trước**; chạy thẳng lên footage
  đa cảnh là cách chắc chắn để khối chữ nhảy lung tung.
- Video có tiếng nghe được. Tiếng ồn nền nặng thì phiên âm sai, và phụ đề sai còn tệ hơn không có
  phụ đề.
- Chạy trọn tại máy: phiên âm và tách nền người đều chạy cục bộ.

## Quy trình năm bước

1. **Chốt MỘT phong cách** trước khi làm gì — một phong cách cho cả video, không đổi giữa chừng.
2. **Thăm dò trước, tốn 0 đồng:** đọc thời lượng, kích thước, fps, số track tiếng; thử phiên âm 30
   giây đầu. Ba phép này chặn phần lớn thất bại nặng.
3. **Phiên âm và sửa bản chữ.** Đây là bước tốn công thật: tên riêng, số liệu, thuật ngữ luôn sai.
   Sửa ở bước này, đừng sửa sau khi đã dựng.
4. **Chia cụm chữ theo hơi thở, không theo số ký tự.** Ngắt ở chỗ người nói ngừng; một dòng nên
   đọc được trong một nhịp mắt.
5. **Xem trước rồi mới render.** Nhìn ít nhất một khung ở mỗi đoạn dài — đặc biệt chỗ chữ dài nhất.

## Những chỗ hỏng hay gặp

- **Chữ tràn khung** ở câu dài nhất: kiểm đúng câu dài nhất, không kiểm câu đầu.
- **Tách nền lem ở tóc** khi dùng đường embed — nhìn khung có chuyển động nhanh.
- **Footage có GOP thưa** (khoảng cách keyframe > ~1 s) làm khung đứng hình khi tua. Mã hoá lại
  video nguồn với keyframe dày trước khi dựng.
- **Phụ đề rơi vào vùng giao diện nền tảng** ở khung dọc — xem `hyperframes-studio` phần vùng an toàn.
