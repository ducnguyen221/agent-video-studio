# Workflow lyric video

## Intake và quyền
Ghi asset ID, đường dẫn tương đối, hash, bản phối/phiên bản, thời lượng, người cung cấp, nguồn và quyền riêng cho bản ghi, sáng tác/lời, ảnh/clip, font và các asset. Ghi kênh, tỉ lệ, thời lượng, độ phân giải và giới hạn xuất bản; thiếu quyền để trạng thái `unknown` và không công bố. Tư vấn hai phương án: một ảnh tĩnh với vùng bảo vệ hoặc nhiều ảnh/clip có shot list. Không yêu cầu người dùng chuyển asset riêng vào plugin.

## Lời và thời gian
Lưu mỗi ứng viên cùng nguồn và phiên bản bản thu; chép/ASR chỉ là ứng viên. Nghe đối chiếu toàn bài, so bản nguồn được phép và người có thẩm quyền khi có; giữ các câu lặp thành cue riêng. Ghi tình trạng xác minh text và timing độc lập (`unverified`, `verified`), người/phương pháp và bằng chứng. Câu chưa nghe rõ hoặc không đủ căn cứ vẫn `unverified`, ghi phần nghi ngờ; không tự nâng trạng thái. `start`, `sung_end`, `end` là giây trên cùng trục audio, bao gồm offset, phần ngân và khoảng giữ; `start <= sung_end <= end`. Khi cắt bản thu, đổi offset có ghi nhận, không ép cue vào beat.

## Metadata
Chỉ ghi bản sao sau khi lời được xác minh. Công cụ trong `assets/write_uslt.py` cần Mutagen đã có sẵn, không tự cài; truyền file text UTF-8 cùng mã ngôn ngữ ISO 639-2 ba ký tự, description và đường ra chưa tồn tại. Công cụ kiểm header MP3 bằng Mutagen, thay đúng cặp language/description, kiểm lại USLT và frame ID3 khác, so hash nội dung ngoài thẻ ID3 đầu file, so hash toàn file gốc; ghi tạm cạnh đầu ra và chỉ xuất khi kiểm xong. Header hợp lệ không chứng minh toàn bộ audio giải mã được; cần nghe/kiểm riêng. Công cụ từ chối frame ID3 không nhận diện vì không chứng minh giữ nguyên được; hệ thống file phải hỗ trợ hard link để xuất an toàn. Không xóa tag hoặc thay bản gốc. LRC/SYLT là tùy chọn; sidecar không chứng minh player đọc USLT và các player có thể hiển thị khác nhau. Với metadata không đọc/so được, dừng và báo; giữ bản gốc, không tuyên bố thành công.

Đây là cổng thủ công của agent: đối chiếu trạng thái verified, bằng chứng và đúng phiên bản bản thu/lời trước khi gọi; script không tự xác thực lời, bằng chứng hay quyền.

## Storyboard và dựng
Điền cả [ảnh tĩnh](../assets/storyboard-still.md) và [nhiều media](../assets/storyboard-multishot.md) từ cùng các ID segment/cue, nêu thiếu sót và xin quyết định lựa chọn trước dựng. Font ghi nguồn, giấy phép, fallback và kiểm glyph tiếng Việt; không đóng gói font chưa có quyền. Các lựa chọn A/B/C giữ tương thích; họ mở rộng là mã dùng lại, không được gọi là preset đã render nếu thiếu chứng cứ. Tham khảo [Envato lyric templates](https://elements.envato.com/video-templates/lyric) để tìm ý tưởng; không chép hay phân phối lại tài sản trả phí, kiểm giấy phép cụ thể trước khi dùng.

Lưu beat, section và envelope phân tích một lần; khi render lấy envelope đã lưu theo thời gian, không thu âm hay phân tích live. Giữ ảnh tĩnh khi brief yêu cầu, dùng mask thực cho mặt/chữ; tắt audio gốc clip mặc định. Kiểm seek cùng thời điểm, glyph/dấu, bounds ở scale lớn nhất và vùng an toàn từng tỉ lệ. Render và nghe/xem MP4 qua wrapper của repo khi đủ runtime; nếu không, ghi `not_run`, không suy từ static check.

Trong gói bên dưới, **`composition/` chính là project root của HyperFrames**: đặt `index.html` ở đó, và mọi đường media trong HTML phải resolve từ `composition/` (dùng đường tương đối hợp lệ tới asset được phép). Truyền chính thư mục `composition/` cho wrapper `video_studio.render.render_project`; wrapper chạy engine với thư mục đó là cwd. CLI `video-studio render --project` chỉ nhận các template tin tức đã đăng ký, không nhận đường dẫn composition tùy ý. Wrapper có thể xuất video câm: ghép master audio đúng offset sau render theo pipeline được duyệt, sau đó kiểm audio stream, thời lượng và điểm vào/ra so với cue bằng probe và nghe file cuối. Không coi MP4 có hình hoặc lệnh render thành công là bằng chứng đã có âm thanh.

Ví dụ từ Python đã import được package repo, với `project_root` là đường tuyệt đối đến thư mục `composition/` và `output_file` là đường tuyệt đối trong thư mục output được chọn:

```python
from video_studio.render import render_project
render_project(project_root, output_file)
```

Wrapper tự đặt cwd là `project_root`; không tự gọi HyperFrames trực tiếp. Đầu ra này là hình, cần ghép audio và kiểm như trên.

## Gói project (trong station)
`provenance.md`, `media-ledger.md`, `lyrics.md`, `cues.json`, `metadata/`, `storyboard-still.md`, `storyboard-multishot.md`, `analysis/` (beat/envelope), `media/`, `composition/`, `runtime.md`, `preview/`, `output/`, `qa.md`. Đường asset tương đối với gốc project; ledger liệt kê asset không phân phối và trạng thái thiếu. QA phân biệt static/test/render, quyền, hash, audio, cue, clipping, safe area, font fallback, các kiểm chưa chạy và quyết định người dùng. Không đưa nhạc/lời/ảnh riêng vào plugin.
