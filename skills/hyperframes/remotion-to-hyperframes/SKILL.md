---
name: remotion-to-hyperframes
description: Port an existing Remotion (React) composition's source to HyperFrames HTML. Use ONLY on an explicit request to port, convert, migrate or translate Remotion source - one way, Remotion only. A passing mention of Remotion, reference-only code, or "make something like my Remotion video" is a fresh build and belongs to general-video instead.
---

# Chuyển nguồn Remotion sang HTML HyperFrames

> **Nguồn:** `heygen-com/hyperframes` · `skills/remotion-to-hyperframes/SKILL.md` @ **v0.8.51** ·
> Apache-2.0 · hash manifest `c8eb6f48889f5c06` (77 file upstream, gồm một bộ ngữ liệu thử chứa mã
> React dùng API Remotion — **không** chép vào repo này).
> Bản này **đã dịch, rút gọn và biên tập lại** (Apache-2.0 §4(b)).

> ⚠ **Cảnh báo giấy phép, riêng của repo này.** Remotion **không** phải nguồn mở dễ dãi: bản Free
> License chỉ cho cá nhân, công ty vì lợi nhuận rất nhỏ, tổ chức phi lợi nhuận hoặc người đang đánh
> giá; lớn hơn phải mua giấy phép công ty; và **cấm chép hoặc sửa mã Remotion để bán lại bản phái
> sinh**. Repo này **không chép một dòng nào** của Remotion. Skill này chỉ **đọc** mã nguồn mà
> người dùng đã sở hữu và viết lại thành HTML — người dùng phải tự chịu trách nhiệm về quyền với
> mã đầu vào của họ.

## Chỉ dùng khi được yêu cầu đích danh

Một lần nhắc tên Remotion, một đoạn mã đưa ra để tham khảo, hay câu "làm cho tôi cái giống video
Remotion của tôi" **đều không phải** yêu cầu chuyển đổi. Chuyển đổi là một chiều, tốn công, và chỉ
đáng làm khi người dùng thật sự muốn bỏ Remotion.

## Năm bước

1. **Soi nguồn.** Liệt kê thành phần, chuỗi thời gian, media, font, hiệu ứng dùng API riêng của
   Remotion. Cái gì không ánh xạ được thì ghi ra **ngay** — đừng để phát hiện lúc render.
2. **Lập bản đồ dịch.** Khung → thời gian; thành phần React → cảnh/sub-composition; `useCurrentFrame`
   → timeline đã tạm dừng với `data-start`/`data-duration`.
3. **Sinh composition HTML** theo `hyperframes-core`.
4. **Nghiệm thu bằng cách so.** Render bản gốc (nếu người dùng có môi trường Remotion chạy được) và
   bản HTML, so khung ở vài mốc. Không so được thì nói rõ là chưa so, đừng tuyên "tương đương".
5. **Ghi lại chỗ hụt.** Danh sách thứ không chuyển được và cách thay thế — đây là phần có giá trị
   nhất của lượt việc, đừng bỏ.

## Thứ skill này không làm

Không dựng mới từ ý tưởng, không chuyển ngược HTML sang Remotion, không "cải tiến" thiết kế trong
lúc chuyển. Chuyển đổi và thiết kế lại là hai lượt việc; trộn vào nhau thì không ai biết khác biệt
đến từ đâu.
