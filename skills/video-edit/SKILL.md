---
name: video-edit
description: Use when cutting real recorded footage into a finished video - talking heads, interviews, tutorials, travel or montage - through `video-studio edit`: transcribe the takes, read the packed transcript, agree a cut strategy with the user, write an EDL, then render with grade, overlays and subtitles. Not for generating a video from data or a script (that is `video-studio render` with a template), and not for writing HTML/CSS animation itself.
---

# Chỉnh footage quay thật — quy trình qua `video-studio edit`

Phỏng theo `SKILL.md` của `browser-use/video-use` (MIT, © 2026 Browser Use), đọc tại bản vendored
`92c2b34` — **đã dịch, biên tập và nối vào CLI của repo này**. Giấy phép: xem `NOTICE`.

## Nguyên tắc

1. **Tiếng nói là chính, hình theo sau.** Điểm cắt đến từ biên của TỪ và từ khoảng lặng, không
   từ cảm giác nhìn timeline. Chỉ soi hình ở những chỗ phải quyết.
2. **Một artifact dẫn đường duy nhất:** `takes_packed.md` — bản ghi lời gom thành cụm, có mốc
   `[bắt đầu-kết thúc]`. Mọi thứ khác (đánh dấu từ đệm, nhận diện quay lại, chấm điểm nhấn) suy
   ra lúc quyết định, đừng dựng sẵn.
3. **Hỏi → chốt → làm → sửa → ghi lại.** Không đụng vào bản dựng trước khi người dùng gật với
   một chiến lược nói bằng tiếng người.
4. **Đừng đoán đây là loại video gì.** Nhìn tư liệu, hỏi, rồi mới dựng.
5. **Tự soi trước khi đưa xem.** Thứ mình không dám giao thì đừng giao.

## Luật cứng (sai là hỏng câm, không phải xấu)

1. **Phụ đề đốt SAU CÙNG**, sau mọi overlay — ngược lại thì overlay che mất chữ.
2. **Cắt từng đoạn rồi nối `-c copy`**, không dựng một filtergraph cho cả video: nối kiểu kia là
   mã hoá lại toàn bộ mỗi lần thêm một overlay.
3. **Vuốt tiếng 30 ms ở HAI đầu mỗi đoạn** — thiếu là nghe "tạch" ở từng mối nối.
4. **Overlay phải dịch PTS** (`setpts=PTS-STARTPTS+T/TB`) để khung 0 của nó rơi đúng mốc; thiếu
   thì người xem thấy khúc GIỮA của hoạt ảnh.
5. **Phụ đề tính theo mốc của VIDEO RA**: `mốc ra = từ.start − đoạn.start + tổng các đoạn trước`.
6. **Không bao giờ cắt giữa một từ.** Mọi mép cắt bám biên từ trong bản bóc lời.
7. **Chừa lề mỗi mép cắt: 30–200 ms.** Mốc của ASR trôi 50–100 ms; lề hấp thụ chỗ trôi đó.
8. **Bóc lời mức TỪ.** Không dùng chế độ câu/SRT (mất thông tin khoảng lặng dưới giây).
9. **Bóc lời một lần rồi dùng lại.** Chỉ bóc lại khi chính file nguồn đổi (`--force`).
10. **Chốt chiến lược trước khi thi hành.**
11. **Mọi thứ sinh ra nằm ở nơi làm việc** (`<footage>/edit/`), không bao giờ ghi vào cây repo.

Những dòng còn lại trong tài liệu này là **ví dụ đã chạy được**, không phải mệnh lệnh: đổi khi
tư liệu đòi hỏi.

## Quy trình

| Bước | Làm gì | Lệnh |
|---|---|---|
| 1. Kiểm kê | bóc lời mọi file quay, gom cụm | `video-studio edit --footage <thư mục> --out <thư mục ra>` |
| 2. Đọc | đọc `<nơi làm việc>/takes_packed.md`, ghi chú chỗ nói hụt, chỗ phải giữ | — |
| 3. Hỏi | mô tả tư liệu bằng tiếng người; hỏi **câu hỏi do tư liệu đặt ra**, không theo checklist cố định | — |
| 4. Chốt | 4–8 câu: hình dạng, chọn take nào, hướng cắt, màu, phụ đề, độ dài dự kiến. **Chờ gật** | — |
| 5. Dựng | viết `edl.json` (xem dưới) rồi render | `video-studio edit --footage … --out … --edl edl.json --build-subtitles` |
| 6. Xem thử | bản nhanh để soi điểm cắt | thêm `--quality preview` (hoặc `draft` chỉ để kiểm mép cắt) |
| 7. Tự soi | xem lại từng mép cắt: nhảy hình, "tạch" tiếng, phụ đề bị che, overlay lệch. Hỏng thì sửa → dựng lại. **Tối đa 3 vòng**, còn lỗi thì nói ra chứ đừng lặp mãi | — |
| 8. Giao + ghi lại | bản cuối, rồi ghi vào `<nơi làm việc>/project.md` phiên này đã quyết gì | — |

Không có `edl.json` thì lệnh **dừng ở bước gom cụm** và in bước tiếp theo — đó là chủ ý, không
phải lỗi.

## EDL

```json
{
  "sources": {"take1": "TAKE1.mp4", "take2": "TAKE2.mp4"},
  "grade": "auto",
  "ranges": [
    {"source": "take1", "start": 2.52, "end": 5.36, "beat": "câu mở"},
    {"source": "take2", "start": 18.04, "end": 24.90, "beat": "chốt", "grade": "subtle"}
  ],
  "overlays": [{"file": "anim/slot1.mov", "start_in_output": 3.0, "duration": 2.5}],
  "subtitles": null
}
```

Đường tương đối tính từ **thư mục chứa file EDL**. `grade`: `auto` (đo từng đoạn rồi chỉnh trong
±8 %, mặc định) · `subtle` · `neutral_punch` · `warm_cinematic` (preset sáng tác, chỉ khi được
yêu cầu) · `none` · hoặc một chuỗi filter ffmpeg.

## Nghề cắt

- **Giữ đỉnh:** tiếng cười, câu chốt, nhịp nhấn. Kéo dài qua câu chốt để lấy phản ứng — tiếng
  cười CHÍNH LÀ nhịp đó.
- **Khoảng lặng ≥ 400 ms** là chỗ cắt sạch nhất; 150–400 ms dùng được nếu soi hình; dưới 150 ms
  là đang cắt giữa câu.
- **Đổi người nói** cần chừa khoảng thở, thường 400–600 ms; ít hơn cho nhịp nhanh, nhiều hơn cho
  chất tài liệu.
- **Không bao giờ nghĩ tiếng và hình tách rời** — một mép cắt phải ổn trên cả hai.

## Hai đường thi hành

- **`--backend distill`** (mặc định khi chạy được): mã trong repo này. Bóc lời **tại máy** bằng
  faster-whisper, không cần khoá API, không gửi tiếng nói của ai đi đâu. Cần
  `pip install -e ".[edit]"` + ffmpeg. Không phân biệt người nói.
- **`--backend vendored`**: gọi bản `video-use` đã cài ở trạm (`station.json: video_use`). Dùng
  khi cần phân biệt người nói hoặc bản ASR chi tiết tới từng từ đệm — đường đó gọi dịch vụ trả
  phí và đòi khoá API. Cài: `scripts/install-video-use.ps1` / `.sh`.

Không có đường nào chạy được thì lệnh trả **mã 3** và in cả hai cách cài — đừng thử lại, hãy cài.

## Sai lầm hay gặp

- Dựng một filtergraph khổng lồ cho cả video "cho gọn" → mã hoá lại mọi đoạn, chất lượng rụng.
- Đốt phụ đề trước overlay → chữ bị che, và lỗi chỉ lộ ra khi xem lại bản cuối.
- Bóc lời lại mỗi phiên → đốt thời gian (và tiền, nếu đi đường dịch vụ) cho thứ đã có.
- Cắt theo cảm giác nhìn sóng âm mà không đọc chữ → cắt giữa từ.
- Ép 24 fps lên footage 60 fps rồi nối nhiều nguồn khác fps → tiếng trôi dần khỏi hình.
