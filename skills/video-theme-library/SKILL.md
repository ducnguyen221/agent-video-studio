---
name: video-theme-library
description: Use when creating a video and looking for, selecting, advising on, reusing or preserving video layouts, motion references, prompts, components, media or online library links. Look up the station layout catalog first, otherwise the repo catalog; check provenance, permissions and evidence. Record eligible reusable patterns only within the authorized project scope; requests for advice only remain read-only. Not for rendering, narration or footage editing.
---

# Chọn template trước, sáng tác sau

## Catalog nào là nguồn sự thật — tìm theo thứ tự

1. **Catalog của trạm:** `THEME-LIBRARY.md` ở gốc trạm video (trạm = `VIDEO_STATION`, hoặc
   `studio.local.json`; `video-studio doctor` in đường trạm đang dùng). Nếu file này có thì
   **đó là nguồn duy nhất** — trạm là nơi thư viện sống và lớn lên theo từng đợt dựng của người
   dùng.
2. **Không có catalog ở trạm** → lùi về `docs/THEME-LIBRARY.md` trong repo này (bản gốc dùng
   chung, chưng cất từ bộ template của repo).

Đọc file đó — **không làm theo trí nhớ**, vì thư viện đổi theo từng đợt dựng và trí nhớ thì không.
Không trộn hai catalog trong cùng một video, và **không sửa nội dung catalog khi chỉ đang tra**.

## Tham chiếu chuyển động sau khi chọn layout

Khi lập hoặc đổi các beat, sau khi chọn layout trong catalog đang dùng, tra
[`assets/prompt-motion/INDEX.md`](assets/prompt-motion/INDEX.md)
để chọn cách chuyển động phù hợp với từng beat. Thư viện này bổ sung cách chuyển động, không
thay catalog layout của trạm và không mang tier S/A. Lọc vai trò và fullscreen/panel trước,
rồi xếp hạng theo `ratio_fit` của tỷ lệ đầu ra; với lớp phủ dùng `overlay_alternative.possible`.
Đừng đọc thẳng `index.json` (≈1,8 MB): lọc bằng `python scripts/motion_find.py` ở gốc repo
(vd. `--role explain --ratio 16:9 --coverage partial --individual --q "so do"`), mỗi entry một
dòng có mã, ý chính, link nguồn và file.
Không loại mọi mẫu ngang chỉ vì cần dựng dọc. Mở file theo mã `PM-<slug>` rồi đưa mã, tên và link nguồn vào đề xuất
phân cảnh cho người dùng. Kích thước và thời lượng khuyến nghị là phân tích, tách khỏi dữ kiện
nguồn; mọi bản chuyển thể vẫn cần dựng và kiểm hình ảnh.

Khi cần prompt, asset, liên kết tham khảo, thư viện online hoặc component mới, tra thêm
[bản đồ nguồn](references/effect-sources.md). Đây là điểm vào chung: catalog layout vẫn thuộc
trạm hoặc repo theo thứ tự trên; mỗi nguồn chuyên đề giữ dữ liệu gốc và quyền riêng. Nêu ID hoặc
đường nguồn, quyền, mức kiểm và giới hạn trong tư vấn. Không nhầm link với quyền sao chép.

Tra hợp nhất offline bằng `python -m video_studio.effect_library --q "tu khoa"` từ gốc plugin
chứa skill đang nạp (có thể ở cache); xác định gốc và đường project/station theo
[hướng dẫn chạy](references/effect-sources.md). Nếu thiếu plugin, báo và dừng; không tự cài.
thêm `--station <đường-trạm>` nếu muốn tra trạm đã chọn. Lọc bằng `--kind`, `--role`, `--ratio`,
`--runtime`, `--technique`, `--rights`, `--maturity` và `--check render=pass` (có thể lặp `--check`);
kết quả JSON rỗng có mã thoát 1, lỗi dữ liệu mã 2. CLI trả envelope; đọc `row["entry"]` và
xem cách lấy đủ tại [effect-sources.md](references/effect-sources.md).
`pass` chỉ là khai báo kèm bằng chứng,
không thay việc kiểm chứng bằng chứng đó.
Khi muốn xem thêm reference chưa rõ tỷ lệ, kết hợp `--ratio 16:9 --include-unknown-ratio`;
chưa rõ không có nghĩa là đã tương thích. `--runtime` lọc metadata, không chứng minh engine đã cài.
CLI không tự suy trạm. Kết quả chỉ là metadata; kiểm quyền, hash và runtime trước khi dùng.
Windows hỗ trợ `capture`, `materialize` và `materialize-repo` một file. Mã 3 có thể đã công bố:
kiểm trạm/đích trước khi thử lại. Xem [nguồn và giới hạn](references/effect-sources.md).
Bundle nhiều file chưa materialize được; metadata không tự chứng minh bản quyền.

## Template tin tức không đi qua thư viện motion

Các template `news`, `news-weekly`, `topstory` và `repo-today` của `video-studio render` tự dựng
bố cục và chuyển động riêng; chúng **không** đọc catalog layout hay thư viện motion ở trên. Muốn
áp motion từng cảnh thì dựng một project HyperFrames tuỳ biến (`index.html` + `assets/`) rồi dựng
bằng `video-studio render --project-dir <thư mục> --out <thư mục ra>`: lệnh kiểm `check --strict`
và render bằng engine ghim trên bản chép cô lập; project có `.npmrc`, `package.json` hay
`node_modules/` bị từ chối (mã 2).

## Quy trình bốn bước

Với lyric video, sau layout hãy tra skill `lyric-video-effects`
cho preset chữ A/B/C và kiểm nét script. Với ảnh tĩnh có lớp phủ chuyển động, tra
skill `photo-ambient-effects`. Đây là reference chuyên đề,
không tự thêm style ngoài bộ người dùng đã duyệt.

1. **Phân loại TỪNG đoạn nội dung theo việc nó làm**. Các loại gồm mở màn/hook · con số chủ đạo ·
   N điểm · quy trình/chuỗi sự kiện · so sánh A-B · xếp hạng. Các loại khác gồm phát ngôn ·
   demo sản phẩm/clip nguồn · mặt trái/cảnh báo · chốt hạ · kết + kêu gọi.
2. **Tra bảng chọn nhanh** (§1 của catalog) → lấy template **tier cao nhất** khớp việc đó VÀ khớp
   tỉ lệ khung (16:9 hay 9:16 — hai cột khác nhau, đừng lấy nhầm). Template tier `NEW` mới có mô
   tả giải phẫu, chưa có code: dựng theo mô tả rồi ghi nguồn code vào catalog.
3. **Chọn một hệ màu theo thương hiệu** (§9 nếu catalog có) và **không trộn hai hệ** trong một
   video.
4. **Tuân luật cứng** (§6). Vi phạm luật cứng là video **hỏng**, không phải video xấu.

## Nghĩa vụ giữ thư viện còn sống

Áp cho catalog **đang dùng**, trong phạm vi người dùng đã giao quyền ghi:

- Khi tạo được pattern hoặc tìm được tài nguyên hữu ích có thể dùng lại, chủ động bổ sung entry và
  index vào thư viện phù hợp trong phạm vi project được giao, kèm nguồn và trạng thái kiểm. Lưu tại
  trạm được chọn khi có quyền ghi và đủ quyền sử dụng; không cần hỏi lại chỉ vì thao tác capture.
  Đưa vào repo phải qua kiểm quyền, dữ liệu riêng và review. Chỉ tra cứu thì không ghi.
- Capture component hoặc prompt mới: điền `description` ngắn về mục đích, đầu vào/đầu ra, tham số,
  cách dùng và giới hạn; ghi “chưa biết” nếu chưa xác minh. Giữ nguồn và trạng thái kiểm riêng;
  thẻ cũ thiếu `description` vẫn hợp lệ.
- Dựng xong một pattern đang ở tier `NEW` → đề xuất đổi tier (S/A), trỏ tới nguồn code và ghi
  bằng chứng; chỉ cập nhật catalog khi được giao quyền ghi.
- Khi đang dựng video trong phạm vi được ghi trạm và phát hiện nguồn online mới hữu ích để tái dùng,
  lập thẻ liên kết `reference_only` kèm nguồn, quyền và trạng thái kiểm; kiểm tìm lại qua chỉ mục
  chung. Nếu chưa rõ quyền, giữ `unknown` và chỉ lưu metadata liên kết, không chép nội dung nguồn.
  Việc chưng cất, đóng gói hoặc phân phối nội dung vẫn cần kiểm quyền và phạm vi riêng.
- Sửa một template theo yêu cầu riêng của một số báo thì **đừng** sửa vào thư viện: thư viện là
  cái dùng lại được, không phải nhật ký của một số báo.

## Ba luật hay bị quên nhất

- **Cấm lặp vô hạn** (`repeat: -1`): tiến trình render phình tới khi chết, và chết sau vài phút
  chứ không chết ngay.
- **Tái lập được:** mọi phần tử định thời có `data-start`/`data-duration`; timeline `paused`
  đăng ký vào `window.__timelines`; không `Date.now()`, không `Math.random()`.
- **Ghim một bản engine cụ thể.** Xem trước và render thật phải cùng một bản, nếu không thì thứ
  soi trên trình duyệt không phải thứ sẽ ra video.

Hai luật nữa thuộc về nội dung và được catalog nêu chi tiết: chữ phụ đề tô **từ khoá**, và bản
công khai **không lộ tên công cụ nội bộ**.
