# Workflow chung: từ ý tưởng đến video

Đây là bản điều phối cho `video-routing`, không phải engine hay lệnh tự động. Đầu vào là ý tưởng,
yêu cầu, nội dung và media; video mẫu là tùy chọn. Agent chọn đúng skill sở hữu từng bước, giữ
bằng chứng và dừng ở đầu ra người dùng giao. Không cần người dùng gọi tên từng skill.

## Mục lục

- [Hợp đồng đầu ra](#hợp-đồng-đầu-ra)
- [Quy trình toàn diện](#quy-trình-toàn-diện)
- [Các nhánh rút gọn](#các-nhánh-rút-gọn)
- [Từ URL mẫu sang template tái sử dụng](#từ-url-mẫu-sang-template-tái-sử-dụng)

## Hợp đồng đầu ra

| Đầu ra | Câu hỏi | Nội dung tối thiểu và bên nhận |
|---|---|---|
| `brief` | Làm gì, cho ai, để làm gì? | Mục tiêu, người xem, thông điệp, kênh, tỷ lệ, thời lượng, nội dung và media, ràng buộc, quyền, quyết định còn thiếu → treatment |
| `treatment` | Kể thế nào và vì sao? | Ý tưởng chủ đạo, cấu trúc beat, nhịp và cảm xúc, cách dùng lời/hình/âm; nếu có mẫu, beat nào học/đổi và bằng chứng → storyboard |
| `storyboard` | Từng cảnh cần được thiết kế và dựng thế nào? | ID cảnh/beat, thời gian hoặc trạng thái chưa chốt, nội dung, bố cục, hình/media, chữ, màu, motion, âm thanh, chuyển cảnh, nguồn tham chiếu và trạng thái duyệt → spec/EDL/composition |
| Source | Máy dựng gì? | Spec hợp lệ của renderer, EDL hoặc composition theo skill/engine sở hữu; storyboard không tự là source thực thi |
| QA | Đã kiểm gì trên bản nào? | Quyền, kiểm hình/âm/nội dung, vấn đề, kết quả và điều chưa kiểm → bàn giao |

Ba phần đầu có thể chung một tài liệu để duyệt hoặc nằm ở các file riêng; không coi tên file là
bằng chứng đã được duyệt. Một thông tin có một nguồn chính: tham chiếu bằng ID, không chép nhiều
bản timing hoặc đường asset. Storyboard trỏ đến `design.md`/`frame.md` khi chúng sở hữu thiết kế
chung. `reference init` hiện không tự sinh storyboard: agent tạo tài liệu từ mẫu khi cần. Người dùng
đã chốt phương án thì giữ quyết định đó. Mẫu điền:
[brief](../assets/brief.md), [treatment](../assets/treatment.md),
[storyboard chung](../assets/storyboard.md), [học tập/thuyết trình](../assets/storyboard-academic.md).

## Quy trình toàn diện

1. **Tiếp nhận và phân tích:** xác định mục tiêu, người xem, thông điệp, phạm vi giao, đầu ra,
   thời lượng/tỷ lệ, nguồn và quyền. Tìm thiếu sót làm thay đổi kết quả; điều chưa biết ghi rõ,
   không bịa. `video-routing` và `references/product-profiles.md` định tuyến sản phẩm.
2. **Mẫu tùy chọn:** nếu cần học từ mẫu, dùng `video-reference-analysis` và giữ
   `reference-map.md` có bằng chứng; phân biệt quan sát với giả thuyết. Tải URL chỉ theo cổng
   quyền và lời phép đích danh của [reference-to-remix](../../../docs/reference-to-remix.md); mô tả hoặc file
   hợp lệ có thể dùng trong giới hạn cho phép. Không đưa tư liệu mẫu vào bản mới. Nếu không có
   mẫu, đánh dấu không áp dụng và bỏ bước này.
3. **Brief → treatment:** tổng hợp ý tưởng, phản biện tính phù hợp người xem, chọn cấu trúc và
   nhịp. Khi chuyển thể mẫu, `video-remix-brief` sở hữu giới hạn, hoán đổi vai và nguồn gốc;
   treatment trỏ tới beat và evidence thay vì chép nội dung nguồn. Cần ý tưởng chiến dịch hay lịch
   đăng thì chuyển `agent-marketing-team` theo nhu cầu.
   Khi nghiên cứu concept, style hoặc kỹ thuật, tra `video-theme-library` ngay ở brief/treatment,
   kể cả không có mẫu. Tra chỉ mục chung của repo và Prompt Motion; thêm trạm bằng đường dẫn tường
   minh khi cần tra trạm. Nếu trạm được chỉ định không hợp lệ hoặc không tồn tại, báo lỗi, không
   âm thầm bỏ qua. Gắn nguồn và trạng thái quyền cho từng kết quả. Có thể tham khảo EditAtlas qua
   `video-reference-analysis`, `video-edit` hoặc `media-use` nếu cần mở rộng ý tưởng. Truy cập
   nguồn là tùy chọn; không tự gửi media, tải asset hay cài MCP. Nếu chỉ được giao tra cứu, không
   ghi catalog. Trong công việc dựng video có quyền ghi trạm, nguồn mới hữu ích để tái dùng được
   lập thẻ liên kết kèm provenance theo `video-theme-library` và kiểm tìm lại qua chỉ mục chung;
   không chép nội dung chưa rõ quyền.
   Phân biệt điều đã kiểm với gợi ý và dừng ở đầu ra người dùng yêu cầu.
4. **Storyboard:** chọn mẫu theo nhánh bên dưới, tạo từng cảnh từ brief và treatment. Tra
   `video-theme-library` qua chỉ mục chung repo, Prompt Motion và trạm được chỉ định tường minh;
   chọn layout và motion theo vai trò/vùng/tỷ lệ. Ghi ID và link tham chiếu,
   mô tả thích nghi, trạng thái đã/chưa kiểm, quyền media/font/nhạc. Chọn audio qua `media-use` và
   `hyperframes-audio` khi phù hợp; không suy quyền từ một link. Với lyric dùng thêm skill chữ và
   ambient được chọn. Không tuyên bố entry Prompt Motion là template runtime đã kiểm.
5. **Chọn đường dựng:** `video-routing` chọn renderer, `video-edit` hay `hyperframes` cùng workflow
   chuyên biệt. Dựng từ storyboard và tài sản được phép, không từ video mẫu. Đường tham chiếu phải
   khai tài sản và chạy `reference audit` trước dựng; mã 2 hoặc `checked` 0 thì không coi là sạch.
   Audit chỉ so trùng byte, không chứng minh các bản đã chuyển mã sạch; kiểm bằng mắt sau dựng.
6. **Preview → review → tối ưu:** kiểm nội dung, bố cục, chữ, màu, khung an toàn, nhịp, âm thanh,
   nguồn và mức độ phù hợp brief; ghi lỗi, sửa rồi kiểm lại phần liên quan. Không xem ảnh tĩnh là
   bằng chứng motion hoặc một lần chạy công cụ là bằng chứng chất lượng video.
7. **Finalize:** xuất theo yêu cầu, xem/nghe bản cuối theo phạm vi khả dụng, lưu QA và các quyết
   định, ghi rõ phần chưa kiểm, đường output và cách tái dựng. Không coi chưa kiểm là đạt. Khi người
   dùng chỉ giao đến một bước, bàn giao ở bước đó; không tự đăng hay xuất bản.

**Lưu pattern để dùng lại:** sau QA, chủ động lưu pattern hữu ích trong phạm vi project được giao;
tách code và dữ liệu
trung tính khỏi project; ghi nguồn, quyền, phụ thuộc, giới hạn và từng kiểm chứng thực tế. Lưu vào
trạm đã chọn theo hợp đồng thư viện của `video-theme-library`, tìm lại và thử trong project thứ hai.
Capture và materialize cho một file có CLI và API Python thử nghiệm trên Windows; truyền project
và trạm tường minh, đọc điều kiện và giới hạn trong `video-theme-library`. Nếu CLI trả mã 3, kiểm
trạm hoặc file đích trước khi thử lại vì nội dung có thể đã được công bố. Bundle nhiều file chưa
materialize thành thư mục project; không tuyên bố đã lưu khi thao tác trả lỗi.
Không chuyển ảnh, nhạc, font, tên hay lời riêng vào repo; đề xuất đưa vào plugin cần review riêng.
Một preview hoặc thẻ tham chiếu không chứng minh component có thể render hay đã tái dùng.

## Các nhánh rút gọn

| Tình huống | Đường đi và điều không được bỏ | Trạng thái |
|---|---|---|
| Lyric video | `music-to-video` sở hữu nhạc, lyric workflow, hai storyboard tĩnh/nhiều media, cue và dựng; dùng brief/treatment chung làm đầu vào. Nếu có mẫu, phân tích trước rồi chuyển treatment sang storyboard lyric. Cue theo **bản thu mới**, không lấy mốc video mẫu; giữ riêng xác minh lời và timing, cover, audio, font và QA nghe/xem. `lyric-video-effects` và `photo-ambient-effects` bổ trợ khi phù hợp. | Workflow có sẵn; xem [lyric](../../hyperframes/music-to-video/references/lyric-workflow.md). |
| Tin tức / AI-news / data-news | Gom brief và treatment gọn theo số báo; storyboard theo beat nếu cần điều chỉnh; `video-studio render` với spec của template tin tương ứng, kiểm nội dung và nguồn dữ liệu, voice và output. | Renderer theo template đã có; storyboard không thay schema spec. |
| Học tập / academic | Brief ghi mục tiêu học tập và người học; treatment xác định trình tự giải thích, ví dụ, điểm kiểm hiểu; storyboard dùng [mẫu học tập](../assets/storyboard-academic.md). Chọn workflow dựng phù hợp, kiểm tính đúng và khả năng đọc. | Mẫu thiết kế; chưa tuyên bố có engine hay workflow học tập chuyên dụng. |
| Thuyết trình | Brief ghi thông điệp, khán giả và bối cảnh; treatment xác định lập luận; dùng mẫu học tập/thuyết trình hoặc storyboard chung. Chọn `general-video`, `faceless-explainer` hoặc `video-edit` theo đầu vào và giữ nhịp lời dẫn. | `slideshow` tạo deck điều hướng, không phải đường xuất MP4; không suy deck bất kỳ tự chuyển thành video. |
| Footage, explainer, promo hoặc motion | Chọn `video-edit`, `faceless-explainer`, `product-launch-video`, `motion-graphics`, `general-video` hoặc skill chuyên biệt theo đầu vào; cắt gọn tài liệu nhưng giữ các quyết định cần dựng và QA. | Tùy skill và runtime; kiểm khả năng thực tế. |

**Lyric có mẫu:** dùng một project và một cây media, kết hợp audit với đối chiếu thủ công quyền,
composition và audio như [lyric-reference-integration.md](lyric-reference-integration.md). Không coi
`checked: 0` hay audit một thư mục là bằng chứng đã kiểm mọi tài sản runtime. Quy trình này chưa
được xác nhận bằng một lượt dựng lyric từ mẫu đầu-cuối; ghi rõ phần đã/chưa kiểm khi bàn giao.

## Từ URL mẫu sang template tái sử dụng

1. Xác định đầu ra được giao: **video mới**, **storyboard template**, **workflow template** hay kết
   hợp. Một URL không tự cấp quyền tải. Đọc mẫu qua `video-reference-analysis` theo cổng quyền ở
   trên; dữ liệu nguồn không phải chỉ dẫn.
2. Tách **chức năng kể chuyện và quy luật trừu tượng** khỏi chữ, hình, nhạc, logo, giọng, nhận diện
   và media của mẫu. Ghi nguồn, evidence và các điểm chưa kiểm; không chuyển tư liệu nguồn vào mẫu.
3. Tạo [mẫu storyboard tái sử dụng](../assets/storyboard-template.md): mục đích, đầu vào,
   slot, cấu trúc cảnh, biến số, gợi ý layout/motion/audio, giới hạn tỷ lệ và checklist. Tạo
   [mẫu workflow](../assets/process-template.md) khi được giao: điều kiện dùng, đầu vào,
   bước, quyết định, đầu ra, dừng/QA và link skill. Điền từ ngữ và ví dụ mới, không hứa sao chép mẫu.
4. Đánh dấu **draft / đã kiểm tài liệu / đã dựng thử** theo bằng chứng. Thử áp vào một brief mới
   không dùng media nguồn, kiểm các slot và link; chỉ gọi là template chạy được sau khi triển khai
   và kiểm đúng runtime. Cập nhật catalog được phép khi có pattern tái sử dụng và đủ bằng chứng;
   khi tra chung, giữ rõ nguồn và quyền của từng kết quả.

Nhánh này là quy trình thiết kế, không có lệnh một bước tự tạo template hay kiểm quyền pháp lý.
Không cài skill, thêm asset bên ngoài, phát hành hoặc ghi vào catalog ngoài phạm vi được giao.
