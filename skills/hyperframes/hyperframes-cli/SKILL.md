---
name: hyperframes-cli
description: The HyperFrames CLI development loop - init, add, catalog, capture, lint, check, snapshot, compare, preview, play, present, beats, keyframes, single or batch render, publish, doctor, browser, info, upgrade, skills, compositions, timeline, docs, transcribe and tts. Use it to drive a project from scaffold to rendered MP4, and when diagnosing a build or render failure. validate, inspect and layout are deprecated aliases of check. Not for composition markup rules (hyperframes-core).
---

# Vòng lặp lệnh của HyperFrames

> **Nguồn:** `heygen-com/hyperframes` · `skills/hyperframes-cli/SKILL.md` @ **v0.8.51** ·
> Apache-2.0 · hash manifest `986414090bf6442f` (11 file upstream).
> Bản này **đã dịch, rút gọn và biên tập lại** (Apache-2.0 §4(b)); `references/*` không chép vào repo.

Lệnh chạy dạng `npx hyperframes …`. **Trong repo này luôn đi qua vỏ bọc**
`video_studio/render.py` (`hyperframes_argv()`) — vỏ đó ghim đúng bản trong `HYPERFRAMES_VERSION`,
truyền argv dạng danh sách, không qua shell, và luôn đẩy stderr vào log. Gọi `npx` thẳng trong
pipeline là bỏ mất cả ba thứ đó.

Yêu cầu nền: **Node ≥ 22** và ffmpeg.

## Chín bước, theo đúng thứ tự

1. **Dựng khung** — `init <project>`, hoặc chụp một trang web.
2. **Tìm nước đi có sẵn trước khi tự viết** — `catalog --query "<mô tả hiệu ứng bằng tiếng Anh>"`,
   rồi `add <tên>`. Chỉ tự viết khi không có gì khớp.
3. **Viết composition** theo `hyperframes-core`. Muốn biết timeline đang có gì thì
   `timeline --json`, đừng đọc tay từng file.
4. **Phản hồi nhanh khi đang sửa** — `lint` sau lượt HTML đầu và sau mỗi thay đổi cấu trúc.
5. **Cổng cuối** — `check` (đã tự chạy `lint` bên trong, đừng gọi `lint` thêm cho thừa).
6. **Soi sub-composition** — `snapshot --at <t1>,<t2>,<t3>` rồi nhìn từng khung.
7. **Xem trước** — `preview --background`, kiểm URL trả 200, đưa người duyệt.
8. **Render sau khi được duyệt** — `--quality draft` khi lặp, `looks` cho bản thật đầu tiên,
   `delivery` cho bản giao.
9. **Nghiệm thu file** — file tồn tại, khác rỗng; đọc dòng thứ hai của bản tóm tắt render;
   `ffprobe` so thời lượng với `data-duration` của gốc.

## Bẫy đã đo, phải nhớ

- **Từ 0.8.38, `-q/--quality` mặc định đổi từ `standard` sang `looks`** (tương đương `standard` +
  CRF 16). Không truyền cờ thì file **nặng hơn và encode lâu hơn** bản cũ dù hình gần như y hệt.
  Muốn giống hệt bản trước thì truyền `-q standard` tường minh. Tài liệu đi kèm gói vẫn ghi
  "default: standard" — **lạc hậu, đừng tin**, đọc `--help`.
- **Từ 0.8.17 render fail-closed**: script của sub-composition lỗi, trích media lỗi, hay artifact
  hỏng nay làm lượt render **thất bại** thay vì "xanh giả". Lượt lịch từng xanh có thể đỏ lên — đó
  là engine bắt đúng, không phải engine hỏng.
- `check` chỉ chạy một phiên trình duyệt và một lượt tua; phát hiện dai dẳng mới chặn mã thoát,
  phát hiện thoáng qua lúc vào/ra chỉ là thông tin. `--strict` để cảnh báo cũng chặn.
- `doctor --json` **luôn thoát 0** — phải đọc `ok` trong payload, đừng tin mã thoát.
- Ưu tiên `--json` cho mọi lệnh gọi từ agent/CI. Đường dẫn trong JSON được thay bằng `$HOME`;
  đừng cố dựng ngược lại.
- Truy vấn `catalog` **viết bằng tiếng Anh** kể cả khi video là tiếng Việt: bộ chỉ mục là tiếng
  Anh, truy vấn chữ khác trả về rỗng. Chữ trên màn hình thì cứ để tiếng Việt.
- Đọc `tier` trong kết quả `catalog --json`, đừng suy từ việc có kết quả hay không. Kết quả yếu ở
  tier `words` là bình thường; yếu ở `on-device` mới là lỗi.
- Tầng tìm theo nghĩa cần tải ~33 MB về cache của người dùng — **nói rõ dung lượng và hỏi trước**,
  đừng bật lén.

## Chọn cách render

| Nhu cầu | Lệnh |
|---|---|
| Lặp nhanh tại máy | `render --quality draft` |
| Bản thật đầu tiên | `render --quality looks --output out.mp4` |
| Bản giao cuối | `render --quality delivery --output out.mp4` |
| Render lặp lại được trong container | `render --docker --strict` |
| Nhiều biến, một lượt | `render --batch rows.json --output "renders/{name}.mp4"` |

Đường render đám mây (HeyGen cloud, AWS Lambda, Google Cloud Run) **không dùng trong repo này**:
pipeline chạy tại máy, và đẩy nội dung chưa phát hành lên dịch vụ ngoài là một quyết định riêng,
phải hỏi người dùng.

## Lệnh không nên chạy

`validate`, `inspect`, `layout` — bí danh cũ của `check`, không được xuất hiện trong script mới.
`feedback --file-issue` công bố một bản tái hiện ra URL công khai: **chỉ chạy khi người dùng đồng ý**.
