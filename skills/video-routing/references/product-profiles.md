# Nhóm sản phẩm và intake

Chọn nhóm theo **việc người xem cần hiểu hoặc làm**. Chọn một nhóm chính; thêm rubric phụ khi
một video lai có mục tiêu thứ hai thật sự. Engine, phong cách, nền tảng, tỷ lệ khung hình và độ
dài không đủ để suy ra nhóm. Đây là cách chọn hướng nội dung, không phải schema hay lệnh dựng mới.

## Bốn nhóm

### Đào tạo

- **Nhận diện:** người xem cần học rồi tự làm một quy trình hoặc thao tác.
- **Mạch:** mục tiêu → điều kiện cần → làm mẫu → thực hành/kiểm tra → tóm tắt. Cho UI và bước
  quan trọng đủ lớn, đủ lâu để quan sát.
- **Ưu tiên:** demo có bằng chứng, chữ hiển thị tách lời đọc khi cần, mốc lời–hình và QA.
- **Bỏ qua:** không dựng demo giao diện nếu kỹ năng không gắn với UI; không thêm bước cho đẹp.
- **Nghiệm thu:** người xem xác định được thao tác và kết quả; trạng thái trước/sau đúng; không
  thiếu bước trọng yếu; chữ đọc được ở khung phát hành.
- **Kết hợp:** `video-edit` cho footage; `general-video` hoặc `product-launch-video` chỉ mượn
  cách trình bày demo UI; `hyperframes` nếu thực sự dựng composition.

### Giải thích

- **Nhận diện:** người xem cần hiểu một câu hỏi, cơ chế hoặc quan hệ nhân quả.
- **Mạch:** câu hỏi → cơ chế → ví dụ/đối chiếu → kết luận. Sơ đồ và hình xuất hiện theo luận
  điểm, không chỉ lấp khoảng trống.
- **Ưu tiên:** anchor cho ý chính, hình minh họa có mục đích, dual text khi lời đọc và chữ cần
  khác nhau, QA.
- **Bỏ qua:** không gắn anchor cho mọi từ; không biến ví dụ minh họa thành bằng chứng của sự kiện.
- **Nghiệm thu:** luận điểm có căn cứ; hình diễn đạt đúng cơ chế; người xem phân biệt ví dụ với
  dữ kiện thực tế.
- **Kết hợp:** `faceless-explainer`, `motion-graphics`, `embedded-captions`; `hyperframes` khi
  composition HTML/animation là lựa chọn phù hợp.

### Bản tin dữ liệu

- **Nhận diện:** người xem cần biết số liệu/sự kiện mới, kỳ đo, nguồn và ý nghĩa của chúng.
- **Mạch:** rundown → headline → gói tin → ý nghĩa → chuyển mục. Giữ nhịp tin; không biến thành
  bài giảng chỉ vì có nhiều chỉ số.
- **Ưu tiên:** giữ số, đơn vị, kỳ và nguồn; tách lời đọc khỏi chữ chuẩn khi phát âm có thể sai;
  reuse asset chỉ khi provenance khớp; QA output.
- **Bỏ qua:** không thêm phân tích nhân quả khi nguồn chỉ cho thấy đồng biến; không tái dùng đồ họa
  có kỳ dữ liệu cũ như thể mới.
- **Nghiệm thu:** số, đơn vị, ngày/kỳ, nguồn đúng; bình luận phân biệt với số đo; nhịp và chuyển mục
  không làm mất ngữ cảnh.
- **Kết hợp:** `video-routing` cùng template `news`/`topstory`, `media-use`, `hyperframes-audio`.

### Kể chuyện có nhân vật

- **Nhận diện:** động cơ, hành động và hệ quả của nhân vật dẫn người xem qua nhiều cảnh.
- **Mạch:** thiết lập → động cơ/xung đột → hành động/hệ quả → kết. Bố cục phục vụ nhân vật và
  không gian, thay vì ép mọi cảnh theo một template tin.
- **Ưu tiên:** continuity nhân vật/đạo cụ/bối cảnh, shot/camera có chủ ý, B-roll đúng vai trò,
  xử lý âm thanh; caption theo người nói chỉ khi cần phân biệt.
- **Bỏ qua:** nhân vật xuất hiện một lần không cần hồ sơ dài; không mở lip-sync/provider pipeline
  chỉ vì truyện có nhân vật.
- **Nghiệm thu:** người xem nhận ra cùng nhân vật; diễn biến trước/sau hợp lý; hướng nhìn và đạo
  cụ nhất quán, trừ thay đổi có chủ ý.
- **Kết hợp:** `general-video`, `media-use`, `video-edit`, `hyperframes-audio` tùy tư liệu.

## Bản đồ kỹ thuật sang skill thực hiện

Bảng này chỉ ra nơi giao việc sau khi trigger của thẻ khớp. Các skill HyperFrames là hướng dẫn
cho engine đó; chúng không làm Hypit thành dependency. Thẻ T1–T9 và giới hạn capability nằm ở
[production-techniques.md](production-techniques.md).

| Nhóm | Thẻ khi có trigger | Skill nhận việc và ranh giới |
|---|---|---|
| Đào tạo | T1, T5; T3/T4 nếu có số dễ đọc sai hoặc cue cần bám | [`video-edit`](../../video-edit/SKILL.md) cắt footage, [`product-launch-video`](../../hyperframes/product-launch-video/SKILL.md) gợi ý trình bày demo UI; capture và xác minh trạng thái thật vẫn cần media do người dùng cung cấp. |
| Giải thích | T1, T4, T6; T3 nếu lời đọc/chữ khác nhau | [`faceless-explainer`](../../hyperframes/faceless-explainer/SKILL.md) và [`hyperframes-animation`](../../hyperframes/hyperframes-animation/SKILL.md) cho hình/cue; [`media-use`](../../hyperframes/media-use/SKILL.md) cho source, [`embedded-captions`](../../hyperframes/embedded-captions/SKILL.md) cho caption. T4 hiện là cue thủ công, chưa có resolver chung. |
| Bản tin dữ liệu | T1, T2 khi thay/reuse asset, T3 khi số/tên dễ sai, T4 khi cue bị lệch | Template `news`/`topstory` trong `video-studio` sở hữu render; [`media-use`](../../hyperframes/media-use/SKILL.md) giúp provenance, [`hyperframes-audio`](../../hyperframes/hyperframes-audio/SKILL.md) voice/audio. Không suy từ reference ra asset ledger hay schema display/spoken mới. |
| Kể chuyện có nhân vật | T1, T7 qua nhiều cảnh, T6 nếu cần hình, T8 với nhiều speaker, T9 nếu có lỗi âm thanh | [`general-video`](../../hyperframes/general-video/SKILL.md) cấu trúc cảnh; [`media-use`](../../hyperframes/media-use/SKILL.md) reference; [`video-edit`](../../video-edit/SKILL.md), [`embedded-captions`](../../hyperframes/embedded-captions/SKILL.md), [`hyperframes-audio`](../../hyperframes/hyperframes-audio/SKILL.md) nhận phần footage/caption/audio. T7 là checklist thủ công; T8 không claim local diarization/tracking. |

Không có skill nhận việc phù hợp đồng nghĩa chưa có workflow runtime được hỗ trợ: giao phần phù
hợp cho skill gần nhất như hướng dẫn thủ công, nói rõ giới hạn, rồi hỏi trước khi thêm provider,
dependency hoặc khả năng engine mới.

## Intake: trích trước, chỉ hỏi phần còn thiếu

Trước khi hỏi, lấy từ brief những gì đã có: người xem; điều cần hiểu/làm; nhóm chính; thời lượng
và kênh; footage/dữ liệu/nguồn; lời đã duyệt; brand; công cụ sẵn có; giới hạn thời gian/chi phí.
Không hỏi lại dữ kiện đã nêu. Giữ mặc định đảo ngược được ở mức thấp rủi ro và nói rõ.

Chỉ hỏi khi câu trả lời có thể đổi kết quả. Gộp tối đa ba câu trọng tâm trong một lượt. Brief đủ
thông tin thì định tuyến và nêu giả định, không tạo câu hỏi cho đủ mẫu. Brief “làm đẹp hơn” chưa
nêu vấn đề thì hỏi cần cải thiện điều gì trước; không đoán nhóm hoặc kê menu kỹ thuật.

| Dấu hiệu | Hỏi nếu còn thiếu | Khuyến nghị ban đầu |
|---|---|---|
| Hướng dẫn thao tác | Người xem phải làm lại thao tác nào? Có quay thật không? | Trình bày trước / thao tác / sau; zoom vùng đọc; ảnh tĩnh nếu chỉ cần chứng minh trạng thái. |
| KPI, tên riêng, viết tắt | Cách đọc nào cần giữ chính xác? Có lời đã duyệt không? | Giữ chữ chuẩn trên hình, tách lời đọc ở đoạn dễ sai. |
| Hình lệch lời | Lời đã chốt hay còn được biên tập? | Căn theo audio xuất thật; chọn vài mốc ý nghĩa. |
| Nhân vật đổi giữa cảnh | Đặc điểm nào bắt buộc liên tục? | Chốt reference nhân vật/đạo cụ trước khi tạo lại asset. |
| “Đẹp hơn” chung chung | Lỗi là khó hiểu, nhịp chậm, thiếu minh họa hay thiếu nhất quán? | Xem một đoạn để chẩn đoán; chưa thấy lỗi thì không thêm hiệu ứng. |

## Khuyến nghị và giới hạn

Nêu theo thứ tự: **vấn đề quan sát được → kỹ thuật → lợi ích dự kiến → chi phí/rủi ro → cách
đơn giản hơn**. Chọn một vấn đề ưu tiên mỗi vòng sửa; thử tối đa hai candidate nhỏ rồi báo đánh
đổi. Nếu kỹ thuật cần gửi media ra nền tảng hoặc cần cài công cụ, nêu rõ trước khi thực hiện và
theo quyền đã giao. Không gọi provider, cài dependency hay tự tải media để lấp thiếu dữ liệu.

Kỹ thuật chi tiết nằm trong [production-techniques.md](production-techniques.md). Chỉ đọc thẻ
được gọi bởi brief. Ví dụ và đường đọc Hypit dùng để tham khảo ý tưởng, không là quy trình bắt
buộc hay dependency.
