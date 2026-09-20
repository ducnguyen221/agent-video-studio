# `templates/` của trạm — spec mẫu và brand của bạn

Repo mang **template dựng hình** (mã). Thư mục này mang **mẫu dữ liệu** của bạn: file brand,
spec mẫu, lời dẫn mẫu. Chúng là danh tính của bạn, nên chúng ở trạm chứ không ở repo.

Hai file đáng có ngay từ đầu:

- `brand.json` — khối `brand` dùng lại cho mọi số báo:

  ```json
  {
    "a": "Phần đầu tên",
    "b": "Phần sau tên",
    "site": "trang-cua-ban.example",
    "accent": "#00E5FF",
    "pronounce": {"trang-cua-ban\\.example": "trang của bạn chấm example"}
  }
  ```

  `pronounce` là bảng {mẫu regex: cách đọc} cho bước chuẩn hoá trước khi tổng hợp giọng — thiếu
  nó thì chữ đúng mà **giọng đọc sai**, và lỗi đó chỉ nghe ra khi video đã xong.

- `spec.example.json` — một spec `schema_version: 1` bạn hay dùng, để lần sau chép ra sửa.
  Xem `docs/CONTRACT.md` trong repo để biết từng khoá.

Dùng: `video-studio render --project topstory --input <spec> --brand templates/brand.json --out <thư mục>`.
