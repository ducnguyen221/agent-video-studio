---
name: faceless-explainer
description: Turn arbitrary text - an article, notes, a topic, a brief - into a faceless explainer video. There is no site to capture and no footage, so every visual is invented per scene from typography, abstract graphics, diagrams and data-viz. Use for topic explainers, concept breakdowns, how-tos and listicles. Not a video built from a website (product-launch-video) and not one built from a pull request (pr-to-video).
---

# Video giải thích không mặt người

> **Nguồn:** `heygen-com/hyperframes` · `skills/faceless-explainer/SKILL.md` @ **v0.8.51** ·
> Apache-2.0 · hash manifest `39e1e4d42e9a5ebe` (24 file upstream).
> Bản này **đã dịch, rút gọn và biên tập lại** (Apache-2.0 §4(b)); `references/*` không chép vào repo.

Đầu vào là **chữ**: một bài viết, một mớ ghi chú, một chủ đề, một brief. Không có trang web để
chụp, không có footage. Mọi hình đều phải **bịa ra theo từng cảnh** — chữ, đồ hoạ trừu tượng, sơ
đồ, biểu đồ.

## Bảy bước

0. **Dựng project** và chốt khung hình (16:9 hay 9:16 — quyết trước, vì bố cục khác hẳn nhau).
1. **Brief, không chụp gì.** Rút từ nguồn chữ ra: video này nói với ai, trả lời câu hỏi gì, kết
   thúc bằng điều gì. Ba câu, viết ra giấy.
2. **Hệ thiết kế.** Bảng màu, bộ chữ, cách chia khung, tông. Một lần, rồi mọi cảnh bám theo.
3. **Bảng phân cảnh và lời đọc.** Lời đọc viết **trước**; hình cắt theo lời.
   3.1 **Âm thanh** — giọng đọc và nhạc nền chốt ở đây, vì nhịp hình phụ thuộc vào độ dài thật
   của lời đọc, không phụ thuộc vào ước lượng.
4. **Thiết kế hình từng khung** — mỗi cảnh: chữ gì trên màn hình, hình gì, chuyển động gì.
5. **Dựng khung.** Tra kho (`hyperframes-registry`) trước khi tự viết hiệu ứng.
6. **Chốt:** `check` sạch → `preview` → người duyệt → `render`.

## Ba luật của thể loại này

1. **Không bịa dữ kiện để cho đẹp hình.** Một sơ đồ đẹp mà sai là một sơ đồ tệ hơn không có. Số nào
   lên màn hình phải có trong nguồn chữ.
2. **Chữ trên màn hình không phải bản chép lời đọc.** Lời đọc kể; chữ trên màn hình chốt lại từ
   khoá, con số, tên. Chép nguyên lời lên màn là bắt người xem đọc và nghe cùng một thứ.
3. **Mỗi cảnh một ý.** Cảnh nào giải thích hai ý thì tách thành hai cảnh — hoặc bỏ bớt một ý.

## Nhịp

Cảnh 3–6 giây là khoảng dễ chịu; dưới 2 giây người xem chưa kịp đọc, trên 10 giây mà hình không
đổi thì mắt rời đi. Mở màn **không quá 3 giây**: chỗ đó quyết định người ta ở lại hay lướt qua.
