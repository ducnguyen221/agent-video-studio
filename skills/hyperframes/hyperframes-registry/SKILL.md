---
name: hyperframes-registry
description: Search, install and wire registry blocks and components into a HyperFrames composition. Use BEFORE hand-building any named visual - whenever a brief, a user or a storyboard names a look, effect, treatment or transition such as CRT scanlines, glitch, chromatic aberration, film grain, a shimmer sweep, a chart, a code or terminal window, a map or a confetti burst - because a few hundred hosted items already cover many of them. Also use when running hyperframes add or hyperframes catalog, wiring an installed item into index.html, or authoring a new block to contribute upstream.
---

# Kho block và component: tra trước khi tự viết

> **Nguồn:** `heygen-com/hyperframes` · `skills/hyperframes-registry/SKILL.md` @ **v0.8.51** ·
> Apache-2.0 · hash manifest `51e6dba95a8dfb45` (12 file upstream).
> Bản này **đã dịch, rút gọn và biên tập lại** (Apache-2.0 §4(b)); `references/*` không chép vào repo.

## Luật một dòng

Khi yêu cầu **gọi tên** một hiệu ứng — nhiễu CRT, glitch, sai lệch màu, hạt phim, vệt loé, biểu đồ,
cửa sổ terminal, bản đồ, pháo giấy — thì **tra kho trước**. Khoảng vài trăm mục đã có sẵn, tra
không cần tài khoản, không cần project, không gửi gì ra ngoài.

```
catalog --query "<mô tả nhịp đó bằng tiếng Anh>"
add <tên mục>
```

Tự viết tay chỉ khi tra xong không có gì khớp — và khi đó nên báo lại chỗ thiếu.

## Hai loại mục, hai cách nối

- **Block** = một sub-composition trọn gói. Cài xong thì nối bằng host slot
  (`data-composition-src`), đặt id cho khớp, và đặt `data-start`/`data-duration` ở host.
- **Component** = một mẩu snippet trộn vào composition đang có. Cài xong phải **gộp** phần CSS/JS
  của nó vào đúng chỗ, và giữ id duy nhất trên trang đã lắp ráp.

`hyperframes.json` của project ghi lại những mục đã cài (khoá `registryItems`, có từ 0.8.14).
**Bẫy lùi bản:** project đã `add` ở nhánh 0.8.x mang khoá đó; bản 0.7.94 dùng schema cũ với
`additionalProperties: false` nên **từ chối file**. Lùi bản thì phải xoá khoá đó trước.

## Đọc kết quả tra cho đúng

- Kết quả có `tier`: `words` (khớp theo từ vựng) hay `on-device` (khớp theo nghĩa). **Đọc trường
  đó**, đừng suy ra từ việc có kết quả. Kết quả yếu ở `words` là bình thường; yếu ở `on-device`
  mới đáng nghi.
- `dropped` = số mục xếp hạng được nhưng kho này không cài được — tức chính những mục khớp nhất
  đang bị rơi. `unindexed` = số mục kho có mà chỉ mục không thấy. **Đổi câu truy vấn không chữa
  được cái nào trong hai.**
- Truy vấn **bằng tiếng Anh**. Chỉ mục là tiếng Anh; truy vấn chữ khác trả rỗng, và thông báo
  "không có từ tra được" nghĩa đúng là vậy — không phải kho thiếu mục.
- Tầng tìm theo nghĩa cần tải ~33 MB về cache người dùng: **nói rõ dung lượng rồi hỏi**, không bật
  lặng lẽ.

## Đóng góp mục mới

Chỉ đóng góp thứ **dùng lại được**: một hiệu ứng có tên, có tham số, không dính dữ liệu của một số
báo cụ thể. Mục mới cần trang demo, mô tả nói đúng việc nó làm (đây là thứ bộ tra dùng để xếp hạng),
và không kéo theo font hay media không có giấy phép rõ ràng.
