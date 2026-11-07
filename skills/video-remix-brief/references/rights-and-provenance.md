# Cổng quyền và nhật ký nguồn

Bản tóm tắt cho video mẫu. Khái niệm lấy từ cổng quyền (Rights Gate) của `agent-marketing-team`
(mục 5 của tệp `YOUTUBE_SCORING.md` trong skill của nó); ở đây chỉ nói điều áp cho việc tải,
phân tích và dựng lại từ một video mẫu.

## Quyền ở đây là quyền gì

`rights_status: approved` cho phép **tải và phân tích** video mẫu. Nó **không** cho phép đưa khung
hình, âm thanh, giọng, nhạc, khuôn mặt, logo hay lời của mẫu vào bản dựng, và không cho phép nhân
bản giọng người trong mẫu. Hai chuyện đó đều bị cấm kể cả khi có giấy phép, vì bản chuyển thể
chỉ mượn cấu trúc và nhịp.

## Ba trạng thái

| `rights_status` | Nghĩa | Việc được làm |
|---|---|---|
| `approved` | có căn cứ rõ và (nếu cần) chứng từ | tải khi có phép đích danh từng URL; phân tích |
| `rights_pending` | chưa chốt, hoặc `approved` thiếu căn cứ/chứng từ | **không tải**; phân tích mô tả hoặc tệp người dùng có quyền |
| `blocked` | điều kiện «không» (chủ video từ chối, cấm sao chép, không rõ nguồn mà phải chắc) | không tải, không dùng |

`init` ghi `rights_pending` mặc định. Người dùng chưa trả lời rõ thì trạng thái vẫn là
`rights_pending`.

## Khi nào được `approved`

`rights_basis` phải thuộc một trong ba căn cứ: video tự làm (`own_content`), phép bằng văn bản,
giấy phép.

- `own_content`: người dùng khẳng định mình làm ra video; không bắt buộc chứng từ.
- Phép bằng văn bản hoặc giấy phép: `rights_proof` **bắt buộc** (đường tệp chứng từ trong project,
  URL trang giấy phép, hoặc số hợp đồng). `approved` mà thiếu `rights_proof` thì coi như
  `rights_pending`, và cổng `fetch` chặn bằng máy.

## Lời cho phép tải

Tải thật cần người dùng nói đích danh **đúng URL đó** ngay trong chat ở lượt đó. Hồ sơ ghi:

| Khoá `permission` | Điền gì |
|---|---|
| `url` | đúng URL cần tải |
| `quote` | chép **nguyên văn** lời người dùng trong chat, không tóm, không sửa |
| `granted_by` | người đã cho phép (khác rỗng) |
| `granted_at` | thời điểm, dạng ISO 8601 |

Cổng `fetch` là cổng thủ tục: nó kiểm hồ sơ có đủ khoá, không kiểm được chat. Vì vậy **agent
không bao giờ tự điền hồ sơ để qua cổng** (không tự đổi `rights_status`, không tự viết `quote`,
không điền `granted_by` thay người dùng). Người dùng bảo «sửa hồ sơ cho qua cũng được» khi chưa
có căn cứ thật: từ chối, nói rõ cần gì, đề xuất đường khác (tệp người dùng có quyền, hoặc chỉ mô
tả).

## Khoá `provenance.json`

| Khoá | Ý nghĩa |
|---|---|
| `schema` | số phiên bản hồ sơ; hiện là 1 |
| `project`, `created` | tên project, ngày tạo |
| `reference` | `url`, `local_file`, `sha256`, `title` của mẫu |
| `rights_status` | `approved` · `rights_pending` · `blocked` |
| `rights_basis` | căn cứ quyền, hoặc rỗng (`null`) khi chưa chốt |
| `rights_proof` | chứng từ: đường tệp trong project, URL hay số hợp đồng; bắt buộc khi căn cứ khác `own_content` |
| `publish_intent` | `public` (mặc định) hoặc `private`; đừng hạ xuống `private` chỉ để qua câu hỏi quyền |
| `permission` | `url`, `quote`, `granted_by`, `granted_at` như bảng trên |
| `fetch` | do lệnh `fetch` ghi sau khi tải: thời điểm, tệp, băm, công cụ; không sửa tay |
| `assets` | danh sách tài sản bản dựng: `path`, `origin`, `owner`, `note` |

Khoá lạ trong hồ sơ được giữ nguyên khi ghi lại. Chi tiết khoá và mã thoát: tài liệu lệnh
`reference` trong `docs/`.

### `assets[]`

- `path` tương đối **so với thư mục project** (ví dụ `assets/hero.png`, dùng dấu `/`), không `..`,
  không đường tuyệt đối.
- `origin` là nguồn gốc của tài sản: `user` (của người dùng), `generated` (sinh mới) hoặc
  `template`. Giá trị `reference` (lấy từ mẫu) là tài sản bị cấm trong bản dựng: ghi như vậy thì
  `audit` báo phát hiện.
- `owner` khác rỗng: ai có quyền với tài sản đó. Khai trùng `path` mà khác `origin` hay `owner`
  bị báo là phát hiện.

## `reference audit` bắt được gì, không bắt được gì

- Bắt: mọi tệp trong thư mục tài sản (kể cả tệp ẩn bắt đầu bằng `.`) phải có trong `assets[]`;
  không tệp nào **trùng byte** với tệp trong `source/` hay `evidence/` (khung, lưới cắt từ mẫu).
  Có phát hiện thì thoát **mã 2** và liệt kê từng tệp cùng lý do.
- Không bắt: tư liệu mẫu đã **chuyển mã, cắt, phóng, đổi màu** (băm khác); đường tệp ghi trong
  spec hay EDL (audit không đọc chúng); lời hay nhạc giống mà không trùng byte.
- Hệ quả bắt buộc: spec/EDL chỉ trỏ vào `assets/`; sau khi dựng, người xem lại khung đại diện của
  bản dựng rồi ghi «không có tư liệu của mẫu» vào `treatment.md`.

## Quy trình ngắn

1. Đọc `provenance.json`. Chưa có thì `reference init`.
2. `rights_status` khác `approved` → dừng ở phân tích từ mô tả hoặc tệp người dùng có quyền.
3. Cần tải: `reference fetch` mặc định chỉ in kế hoạch; chỉ thêm `--go` khi người dùng đã nói
   đúng URL trong chat và hồ sơ đủ khoá ở trên.
4. Dựng chỉ từ `assets/`; mỗi tệp có dòng `assets[]`.
5. `reference audit` mã 0 mới dựng; sau dựng, xem khung và ghi xác nhận.
