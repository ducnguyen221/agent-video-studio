# Hướng dẫn dùng agent-video-studio

*[English](GUIDE.md)*

## 1. Chuẩn bị máy

| Cần | Windows | macOS |
|---|---|---|
| Python ≥ 3.10 | python.org hoặc `winget install Python.Python.3.12` | `brew install python@3.12` |
| Node ≥ 22 | `winget install OpenJS.NodeJS.LTS` | `brew install node` |
| ffmpeg + ffprobe | `winget install Gyan.FFmpeg` | `brew install ffmpeg` |
| Font Inter | tải từ rsms.me/inter rồi Install | `brew install --cask font-inter` |

Công cụ không nằm trên PATH thì đặt `NODE_DIR` / `FFMPEG_DIR` trỏ tới thư mục chứa nó.

## 2. Cài repo

Clone repo, tạo venv, `pip install -e ".[test]"`, rồi chạy `video-studio doctor`. Lệnh này không
cài gì: nó chỉ ra thứ còn thiếu và cách cài.

## 3. Chọn chỗ đặt trạm

`video-studio init` hỏi bạn chọn một trong hai:

- **embedded** (khuyến nghị cho người mới) — trạm nằm ở `workspace/` trong repo, git bỏ qua. Mở
  một folder là thấy hết. Đừng xoá folder repo để cài lại: project của bạn nằm trong đó.
- **separate** — trạm ở thư mục riêng (mặc định `~/.video`). Hợp khi dùng nhiều máy hoặc repo là
  public của chính bạn. Đặt biến `VIDEO_STATION` trỏ vào trạm để mọi công cụ khác thấy.

Máy đã có trạm từ trước thì `init` tự nhận ra và không hỏi.

## 4. Nhận một trạm có sẵn

Trạm bố cục cũ (thư mục `news/`, `topstory/` nằm ngay ở gốc) chuyển sang bố cục mới bằng:

1. `video-studio init --station <trạm> --migrate --dry-run` — đọc kế hoạch: dời gì, ghim gì, không
   đụng gì.
2. Đồng ý thì chạy lại, bỏ `--dry-run`. Đóng trình duyệt/preview đang mở file trong trạm trước.
3. Không ưng: `video-studio init --station <trạm> --undo`.

## 5. Bản HyperFrames

Bản dùng để render luôn là một bản cụ thể (`HYPERFRAMES_VERSION`, hoặc `hyperframes_version` trong
`station.json`). `video-studio doctor --check-updates` báo khi có bản mới; nâng bản là việc có chủ
đích — render thử, so kết quả, rồi mới đổi.

## 6. Làm ba việc chính

| Bạn có gì | Lệnh |
|---|---|
| Dữ liệu (bản tin, deep-dive) + muốn một video | `video-studio render --project topstory --input spec.json --out <thư mục>` |
| Một video câm + lời dẫn | `video-studio narrate --video in.mp4 --file loi.txt --out final.mp4 --profile <tên>` |
| Footage quay thật | `video-studio edit --footage <thư mục quay> --out <thư mục ra>` |

Muốn soi trước khi render: `video-studio preview --project <tên>` (Ctrl+C để dừng).

Lồng tiếng cần **trạm giọng cài trong cùng venv** — xem `docs/INSTALL.md` mục "cài vào venv nào",
đó là chỗ hay sai nhất.

## 7. Giữ đồ của bạn an toàn

```
video-studio backup --out sao-luu.zip          # zip cả trạm, trừ nháp và cache
video-studio migrate --to separate             # chuyển trạm embedded ra ngoài repo
video-studio update                            # git pull --ff-only, không bao giờ xoá gì
```

Thư mục nào xoá được, thư mục nào không: `docs/WORKSPACE.md`.

## 8. Chuyển sang máy khác

```
video-studio export --out goi.zip --personal --include nhac-nen   # chỉ đồ của bạn
video-studio import --in goi.zip --dry-run                        # xem sẽ ghi gì
video-studio import --in goi.zip                                  # bung vào trạm
```

`--personal` lấy `projects/*/assets` và **đúng** những thư mục bạn kể tên bằng `--include`; nháp,
cache, venv và cây `.git` của bản vendored không bao giờ vào gói. Bỏ `--personal` thì gói cả trạm.

`import` **không đè** file đã có: nó bỏ qua và in tên ra, để bạn nhìn rồi quyết. Muốn đè thật thì
thêm `--overwrite`. Máy mới nên `video-studio init --station <trạm>` trước, rồi mới `import`.
