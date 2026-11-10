# Workflow lyric video

## Intake và quyền
Ghi asset ID, đường dẫn tương đối, hash, bản phối/phiên bản, thời lượng, người cung cấp, nguồn và quyền riêng cho bản ghi, sáng tác/lời, ảnh/clip, font và các asset. Ghi kênh, tỉ lệ, thời lượng, độ phân giải và giới hạn xuất bản; thiếu quyền để trạng thái `unknown` và không công bố. Tư vấn hai phương án: một ảnh tĩnh với vùng bảo vệ hoặc nhiều ảnh/clip có shot list. Không yêu cầu người dùng chuyển asset riêng vào plugin.

## Lời và thời gian
Trước khi kết luận thiếu lời hoặc chạy ASR, kiểm tra thẻ metadata lời nhúng của bản thu (ví dụ USLT/SYLT nếu có) và các nguồn lời người dùng cung cấp; ghi nguồn, không coi metadata tự động là lời đã duyệt. Đưa các tên riêng, cách xưng hô, từ viết bất thường hoặc chênh lệch giữa tên bài, metadata và bản hát ra trao đổi; đề xuất cách viết và ghi quyết định của người dùng trước khi chuẩn hóa. Không tự sửa bản gốc.

Lưu mỗi ứng viên cùng nguồn và phiên bản bản thu; chép/ASR chỉ là ứng viên. Nghe đối chiếu toàn bài, so bản nguồn được phép và người có thẩm quyền khi có; giữ các câu lặp thành cue riêng. Ghi tình trạng xác minh text và timing độc lập (`unverified`, `verified`), người/phương pháp và bằng chứng. Câu chưa nghe rõ hoặc không đủ căn cứ vẫn `unverified`, ghi phần nghi ngờ; không tự nâng trạng thái. `start`, `sung_end`, `end` là giây trên cùng trục audio, bao gồm offset, phần ngân và khoảng giữ; `start <= sung_end <= end`. Khi cắt bản thu, đổi offset có ghi nhận, không ép cue vào beat.

## Metadata
Chỉ ghi bản sao sau khi lời được xác minh. Công cụ trong `assets/write_uslt.py` cần Mutagen đã có sẵn, không tự cài; truyền file text UTF-8 cùng mã ngôn ngữ ISO 639-2 ba ký tự, description và đường ra chưa tồn tại. Công cụ kiểm header MP3 bằng Mutagen, thay đúng cặp language/description, kiểm lại USLT và frame ID3 khác, so hash nội dung ngoài thẻ ID3 đầu file, so hash toàn file gốc; ghi tạm cạnh đầu ra và chỉ xuất khi kiểm xong. Header hợp lệ không chứng minh toàn bộ audio giải mã được; cần nghe/kiểm riêng. Công cụ từ chối frame ID3 không nhận diện vì không chứng minh giữ nguyên được; hệ thống file phải hỗ trợ hard link để xuất an toàn. Không xóa tag hoặc thay bản gốc. LRC/SYLT là tùy chọn; sidecar không chứng minh player đọc USLT và các player có thể hiển thị khác nhau. Với metadata không đọc/so được, dừng và báo; giữ bản gốc, không tuyên bố thành công.

Đây là cổng thủ công của agent: đối chiếu trạng thái verified, bằng chứng và đúng phiên bản bản thu/lời trước khi gọi; script không tự xác thực lời, bằng chứng hay quyền.

## Storyboard và dựng
Trao đổi về ảnh người dùng có sẵn, ảnh cần tạo, hay phương án không dùng ảnh; tư vấn ảnh cover và nền phù hợp lời, chủ đề, tỉ lệ và vùng đặt chữ. Khi cần tạo ảnh, dùng công cụ tạo ảnh phù hợp và lưu nguồn/prompt, trạng thái duyệt trong project. Trước khi dựng chi tiết, trình một số mẫu khung hình đại diện cho các phân cảnh để chọn hình, bố cục và font có dấu; kèm các lựa chọn hiệu ứng và bản xem chuyển động khi cần đánh giá motion. Ảnh tĩnh chỉ chứng minh hình thức tại một thời điểm, không chứng minh chuyển động. Ghi rõ lựa chọn và phần chưa duyệt; áp dụng những quyết định người dùng đã đưa, không hỏi lại.

Với bài hát cần ảnh cover/thumbnail, xác định nơi dùng (thumbnail video, ảnh bìa trang hoặc nền video) và tỉ lệ/kích thước tương ứng trước khi tạo; không dùng ảnh bìa siêu rộng thay cho thumbnail 16:9. Tạo hoặc chuẩn bị cover theo nguồn ảnh người dùng chọn, đặt đúng tên bài đã xác nhận, kiểm từng dấu, bố cục khi thu nhỏ và kích thước file thực tế. Khi phù hợp, trình mẫu cover cùng storyboard; lưu ảnh đã chọn, nguồn hoặc prompt, kích thước, giấy phép và quyết định. Cover tĩnh chỉ mô tả một khung, không chứng minh hiệu ứng động.

Mặc định lyric video mở tại khung hình đầu bằng cover tương đương ảnh đã chọn, có tên bài đúng dấu và đủ nét ngay từ frame đầu. Sau đó fade chuyển có chủ đích sang phần lời; đưa lời xuất hiện dần theo cue giọng hát, không hiện sớm hơn lời đang hát. Kiểm frame đầu thực tế, dấu, vùng an toàn, chuyển tiếp và đối chiếu audio ở điểm vào; chưa nghe kiểm thì không xác nhận đồng bộ. Nếu người dùng chỉ định mở đầu khác, dùng phương án họ chọn.

Điền cả [ảnh tĩnh](../assets/storyboard-still.md) và [nhiều media](../assets/storyboard-multishot.md) từ cùng các ID segment/cue, nêu thiếu sót và xin quyết định lựa chọn trước dựng. Font ghi nguồn, giấy phép, fallback và kiểm glyph tiếng Việt; không đóng gói font chưa có quyền. Các lựa chọn A/B/C giữ tương thích; họ mở rộng là mã dùng lại, không được gọi là preset đã render nếu thiếu chứng cứ. Tham khảo [Envato lyric templates](https://elements.envato.com/video-templates/lyric) để tìm ý tưởng; không chép hay phân phối lại tài sản trả phí, kiểm giấy phép cụ thể trước khi dùng.

Lưu beat, section và envelope phân tích một lần; khi render lấy envelope đã lưu theo thời gian, không thu âm hay phân tích live. Giữ ảnh tĩnh khi brief yêu cầu, dùng mask thực cho mặt/chữ; tắt audio gốc clip mặc định. Kiểm seek cùng thời điểm, glyph/dấu, bounds ở scale lớn nhất và vùng an toàn từng tỉ lệ. Render và nghe/xem MP4 qua wrapper của repo khi đủ runtime; nếu không, ghi `not_run`, không suy từ static check.

Nếu dùng dải phổ phản ứng theo nhạc, lưu thêm dữ liệu phân tích, phiên bản audio, offset, tần số lấy mẫu, FFT, hop và cách chuẩn hóa. Phổ đa dải, envelope cường độ và lưới beat là ba dữ liệu khác nhau; không gọi phổ là beat tracking. Kiểm đồng bộ với audio thực tế và ghi phạm vi đã nghe/xem.

Trong gói bên dưới, **`composition/` chính là project root của HyperFrames**: đặt `index.html` ở đó, và mọi đường media trong HTML phải resolve từ `composition/` (dùng đường tương đối hợp lệ tới asset được phép). Truyền chính thư mục `composition/` cho wrapper `video_studio.render.render_project`; wrapper chạy engine với thư mục đó là cwd. CLI `video-studio render --project` chỉ nhận các template tin tức đã đăng ký, không nhận đường dẫn composition tùy ý. Wrapper có thể xuất video câm: ghép master audio đúng offset sau render theo pipeline được duyệt, sau đó kiểm audio stream, thời lượng và điểm vào/ra so với cue bằng probe và nghe file cuối. Không coi MP4 có hình hoặc lệnh render thành công là bằng chứng đã có âm thanh.

Ví dụ từ Python đã import được package repo, với `project_root` là đường tuyệt đối đến thư mục `composition/` và `output_file` là đường tuyệt đối trong thư mục output được chọn:

```python
from video_studio.render import render_project
render_project(project_root, output_file)
```

Wrapper tự đặt cwd là `project_root`; không tự gọi HyperFrames trực tiếp. Đầu ra này là hình, cần ghép audio và kiểm như trên.

## Gói project (trong station)
`provenance.md`, `media-ledger.md`, `lyrics.md`, `cues.json`, `metadata/`, `storyboard-still.md`, `storyboard-multishot.md`, `analysis/` (beat/envelope), `media/`, `composition/`, `runtime.md`, `preview/`, `output/`, `qa.md`. Đường asset tương đối với gốc project; ledger liệt kê asset không phân phối và trạng thái thiếu. QA phân biệt static/test/render, quyền, hash, audio, cue, clipping, safe area, font fallback, các kiểm chưa chạy và quyết định người dùng. Không đưa nhạc/lời/ảnh riêng vào plugin.

Khi tổ chức lại project có sẵn, lập bảng đường cũ → mới, hash và các tham chiếu script/composition/link đã bàn giao. Tạo bản sao không ghi đè, sửa đường dẫn trong bản sao, kiểm hash, resolve media và chạy thử thích hợp trước khi chọn bản chính. Ghi rõ đường cũ còn tương thích thế nào và cách hoàn tác; không xóa bản gốc khi chưa xác minh và được phép. Tách audio nguồn, brief, lời/cue, ảnh/cover, composition/analysis, preview, output và QA; cấu trúc cụ thể phải giữ được hợp đồng `composition/` ở trên.

## Chốt bản cuối và bàn giao

Khi người dùng chốt phiên bản cuối, yêu cầu finalize, **hoặc trước khi kết thúc phiên lyric video**, chủ động trình đủ năm mục dưới đây để người dùng chọn việc muốn làm. Nếu video còn là bản nháp hoặc chưa nghiệm thu, ghi đúng trạng thái và phần chưa kiểm; không gọi là bản cuối chỉ vì đang kết phiên.

1. **Chuẩn hóa project:** đề xuất bố cục cho nhạc nguồn, ảnh, lời/cue, dữ liệu dựng, video được chọn và bản cũ; khi thực hiện, theo quy trình đường cũ → mới, hash và kiểm tham chiếu ở trên.
2. **Dọn file thừa:** kiểm kê demo, bản thử và file trung gian; phân biệt với nguồn, bản duy nhất, bản cũ cần giữ và file cần để dựng lại. Nêu file và dung lượng dự kiến, chỉ xóa hoặc chuyển thùng rác trong phạm vi người dùng đã giao; kiểm lại sau khi dọn.
3. **YouTube:** đề xuất soạn tiêu đề và mô tả cho đúng bài, phiên bản và kênh; hỏi thông tin thiếu ảnh hưởng nội dung, không bịa credit, quyền hay link.
4. **Facebook:** đề xuất soạn bài giới thiệu phù hợp bài hát và giọng người dùng; làm rõ kênh, hình thức và link nếu cần, không tự bịa.
5. **Thumbnail:** đề xuất tạo ảnh đại diện video từ ảnh mở đầu đã chọn cùng tiêu đề bài đã xác nhận; theo kích thước/tỉ lệ nơi dùng và kiểm dấu, độ đọc khi thu nhỏ, kích thước file như mục storyboard. Nếu người dùng chọn ảnh khác thì theo lựa chọn đó. Trình mẫu để duyệt, lưu file và nguồn; tạo thumbnail không đồng nghĩa đăng video.

Phân biệt **tư vấn · soạn nháp · đăng/gửi**: tư vấn đủ năm mục trước khi kết thúc; làm ngay các mục đã được giao, không hỏi lại quyết định đã có. Chưa được giao thì để người dùng chọn; chỉ đăng, gửi hay công bố khi người dùng đã giao rõ. Trong bàn giao, nêu mục đã làm, chưa làm và quyền/kiểm tra còn mở; không coi nháp nội dung là bài đã đăng.

## Cue SFX tùy chọn

Sau storyboard và trước dựng chi tiết, tạo `sfx-cues.json` và bổ sung ledger theo
[quy trình sound design](../../media-use/references/sound-design.md); giữ nguyên schema `cues.json`
cho lyric cũ. Trình vị trí, lý do, vùng không SFX và quyền để người dùng duyệt. Chỉ đưa cue đã
duyệt và asset vượt kiểm hash/quyền vào bản phối. Ghi cue và ledger trong gói project.
