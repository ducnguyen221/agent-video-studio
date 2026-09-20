# Trạm video — thư mục này là gì

Repo `agent-video-studio` chỉ chứa **mã**. Mọi thứ của riêng bạn — project đang dựng, footage,
spec, nháp, cache — nằm ở **trạm video**, và đây chính là nó.

`video-studio init` dựng cây dưới đây. Chi tiết từng thư mục, hai chế độ đặt trạm, và việc gì
an toàn với từng chỗ: xem `docs/WORKSPACE.md` trong repo.

```
<trạm>/
├── station.json      QUẢN LÝ   cấu hình trạm (do `init` ghi — đừng chép tay từ file mẫu)
├── demo/             MẪU       project HyperFrames seed, để thử và để chép cấu hình
├── projects/         CONTENT   mỗi thư mục con là một project render
│   └── _example/               đọc README trong đó trước khi tạo project đầu tiên
├── templates/        CONTENT   spec mẫu, brand mẫu của riêng bạn
├── scratch/          NHÁP      `init` tạo; xoá lúc nào cũng được
└── cache/            NHÁP      `init` tạo; xoá lúc nào cũng được
```

`scratch/` và `cache/` không nằm trong bản mẫu này vì repo public chặn mọi thư mục nháp —
`init` tạo chúng lúc dựng trạm.

## Ba câu trả lời nhanh

- **Xoá được không?** `scratch/`, `cache/`: xoá thoải mái. `projects/`, `templates/`: đó là việc
  của bạn, chỉ bạn quyết. `station.json`, `demo/`: `video-studio init` dựng lại được.
- **Cái gì vào backup?** `video-studio backup --out <file>.zip` gói cả trạm trừ nháp và cache.
- **Cái gì KHÔNG được lên git?** Cả trạm. Ở chế độ `embedded` trạm nằm trong repo và được
  `.gitignore` + hook `pre-commit` chặn; đừng gỡ hai thứ đó.
