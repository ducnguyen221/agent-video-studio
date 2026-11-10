# Danh mục công cụ FFmpeg của Video Studio

Tra bảng khi người dùng nói đến kiểm video, cắt footage, phụ đề, âm thanh, hiệu ứng hay xuất file.
FFmpeg/ffprobe dùng bản đã được studio tìm qua `_env`; không cài thêm runtime hay MCP. `doctor`
kiểm công cụ nhưng không chứng minh đã render. Chỉ dùng lệnh có trong `--help` và skill tương ứng.

| Nhóm / tình huống | Kích hoạt | Năng lực hiện có / điểm vào | Giới hạn |
|---|---|---|---|
| Kiểm media / thông số, decode | «kiểm video», «file lỗi», «QC» | `video-studio media-check` mới là prototype, chưa có trong bản phát hành | Không coi là sẵn dùng hay thay xem/nghe. |
| Xem video mẫu / lưới, khung | «phân tích video mẫu», «tìm khung» | `video-studio reference frames`, `reference tiles`; `video-reference-analysis` | Phải có quyền với file; ô lưới là mốc gần đúng. |
| Bóc lời / cắt theo lời | «transcribe», «cắt talking head» | `video-studio edit` + `video-edit` | ASR local tùy chọn cần đã cài; duyệt chiến lược cắt. |
| Cắt, nối, grade | «cắt đoạn», «nối take», «chỉnh màu» | `video-studio edit --edl …`; pipeline `video_studio/edit/render.py` | Cắt đang mã hóa đoạn rồi nối copy; không tuyên bố cắt gốc lossless. |
| Fade âm thanh ở mép cắt | «bớt tiếng tạch», «nối âm» | Pipeline `video_studio/edit/render.py` thêm fade khi cắt EDL | Nghe lại từng điểm nối, không dùng fade như bằng chứng không mất lời. |
| Phụ đề và overlay | «thêm chữ», «phụ đề» | EDL/`video-studio edit --build-subtitles`; `embedded-captions` | Kiểm mốc, font, và khả năng đọc; overlay trước phụ đề. |
| Chữ chuyển động theo lời | «lyric», «karaoke», «chữ chạy theo nhạc» | `lyric-video-effects`, `music-to-video` và HyperFrames | Cần timing theo bản thu, kiểm từng đoạn; không tự suy karaoke chính xác. |
| Ảnh tĩnh có chuyển động môi trường | «ảnh nền chuyển động», «ambient» | `photo-ambient-effects`, HyperFrames | Chọn hiệu ứng theo nguồn và quyền asset, kiểm xuất cuối. |
| Sound design / nhạc, cue | «thêm SFX», «phối cue» | `media-use` sound-design và `video_studio/sound_design.py` | Quyền asset và cue phải xác minh; mức âm cần nghe. |
| Dựng đồ họa, motion và xuất | «video đồ họa», «hiệu ứng chuyển động» | `video-routing` → HyperFrames qua `video-studio render`; `video-theme-library` | Dùng engine ghim; không áp cho mọi footage. |
| Xóa vùng/che vật thể | «làm sạch vùng video», «blur», «delogo», «che màu», «crop» | `video-studio cleanup`; `video-cleanup` | Các thao tác trên vùng do người dùng chỉ định; xem preview, không tự nhận diện đối tượng. |

## Chưa có trong lát cắt này

Auto scene detection, cắt thông minh theo keyframe, reframe theo chủ thể, chuẩn hóa nhiều
camera, tự xóa từ đệm, chỉnh video 360, stabilization và batch FFmpeg là **ứng viên**, không
phải lệnh studio đã có. Với yêu cầu này, kiểm `--help`, báo phần thiếu và chọn cách làm phù hợp;
không giả định một trong 42 công cụ upstream đã được cài.

Để tra thêm ý tưởng theo nhóm, 42 tên sau là **tên trong tài liệu nguồn**, không phải lệnh local:

| Nhóm | Tên upstream để tra | Tình huống khai thác |
|---|---|---|
| Đo và kiểm | `probe`, `scenes`, `look`, `cropdetect`, `check`, `report`, `verify` | Đo file, tìm cảnh, xem khung, kiểm sản phẩm. |
| Dựng timeline | `cut`, `join`, `silence`, `fit`, `crop`, `insert`, `background`, `sequence`, `freeze`, `pad`, `speedramp`, `loop`, `broll`, `metadata`, `grid` | Dựng đoạn, thay khung, thẻ hình, timeline và metadata. |
| Hiệu ứng hình | `deinterlace`, `denoise`, `redact`, `sphere`, `straighten`, `reverse`, `stabilize`, `color` | Làm sạch/chỉnh hình, chuyển động hoặc màu; phải xem lại kết quả. |
| Âm thanh | `waveform`, `audio`, `sync`, `loudness` | Hiển thị sóng âm, phối/đồng bộ và đo âm lượng. |
| Chữ và đồ họa | `caption`, `overlay`, `graphics` | Phụ đề, lớp phủ, typography và đồ họa. |
| Xuất và quy trình | `export`, `proxy`, `render`, `batch`, `multicam` | Xuất bản, preview, dựng toàn project, nhiều file hoặc nhiều máy. |

Tên trong bảng gợi ý **từ khóa nghiên cứu**; trước thực thi phải quay lại bảng năng lực local
ở trên. Không tự tải, cài hoặc gọi các script đó.

Nguồn ý tưởng: [ffmpeg-skill, commit 6e42a79](https://github.com/kajisho5/ffmpeg-skill/tree/6e42a79247909659b3d80833120b272fb5e46aba), MIT.
Đây là đối chiếu tham khảo; không sao chép hay chạy mã upstream.
