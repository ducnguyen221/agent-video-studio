# Thẻ kỹ thuật sản xuất

Chọn thẻ khi có dấu hiệu cụ thể; không áp dụng cả bộ cho mọi clip. Mỗi lựa chọn giữ lại cần có
lý do trong brief, nơi thực hiện, fallback và bằng chứng QA. Nội dung dưới đây tự viết; liên kết
Hypit ở cuối thẻ là nguồn ý tưởng được ghim, không phải runtime hoặc chỉ dẫn cần chép.

## T1 — QA có bằng chứng

- **Dùng khi:** bàn giao video, đổi render/codec, sửa vùng, có cut hoặc lời–hình dễ lệch.
- **Bỏ qua khi:** clip chưa có file xuất; không lấy preview hay metadata làm bằng chứng review
  hình/tiếng.
- **Intake:** xác định file đích, mục tiêu phát, điểm rủi ro và ai sẽ xem/nghe. Nếu thiếu file,
  chỉ nêu phần chưa thể kiểm.
- **Khuyến nghị:** probe trước; lấy một frame ở đầu/cuối, mỗi cut rủi ro và vài mốc đại diện;
  xem contact sheet để định hướng rồi xem đoạn và video hoàn chỉnh theo rubric sản phẩm.
- **Fallback:** thiếu ffmpeg/ffprobe/decoder thì báo giới hạn, không PASS. Không quét mọi frame
  mặc định. Với VFR không đổi số frame thành thời gian bằng `frame / fps`.
- **QA:** ghi SHA-256 file, PTS/timestamp lấy từ output decoder, kiểm kỹ thuật riêng với trạng
  thái visual/audio. `visual_review` là `NOT_CHECKED` tới khi có người thực sự xem.
- **Thực hiện:** [`video-edit`](../../video-edit/SKILL.md) sở hữu review footage/cut; [`video-cleanup`](../../video-cleanup/SKILL.md) sở hữu verify chỉ cho output và manifest do cleanup tạo; [`hyperframes`](../../hyperframes/hyperframes/SKILL.md) xử lý review composition khi dùng engine đó. Công thức ở đây là checklist thủ công, không phải verifier dùng chung.

### Recipe FFmpeg cục bộ: frame có PTS thật

Chạy trong thư mục làm việc được phép, với file local. `T_SECONDS` là **PTS tuyệt đối trên timeline
nguồn video**, không phải số giây tính từ đầu clip hay file. Giữ PTS gốc bằng `-copyts`. Nếu brief
cho mốc elapsed từ đầu stream video, trước tiên probe `stream.start_time`:

```text
ffprobe -v error -select_streams v:0 -show_entries stream=start_time,time_base,width,height,color_range,color_space,color_transfer,color_primaries -of default=noprint_wrappers=1 INPUT
ffprobe -v error -select_streams v:0 -show_frames -show_entries frame=best_effort_timestamp_time,pkt_duration_time -of csv=p=0 INPUT
```

Khi `start_time` là số hữu hạn, tính `T_SECONDS = start_time + elapsed_seconds`. Ví dụ brief nói
1 giây sau điểm bắt đầu stream và probe trả `start_time=10.0`, chọn từ PTS 11.0. Với VFR, nếu
mốc 6.2 nằm giữa các frame có PTS 6.0 và 7.5 thì ảnh chọn có PTS 7.5; ghi PTS thực thay vì gắn
ảnh với 6.2. Không dùng
`format.start_time` thay cho start của stream video. Nếu `start_time` là `N/A`, không đọc được,
hoặc nguồn cần clock khác chưa quy đổi, dừng chọn bằng recipe này và báo origin chưa xác định;
đừng giả định nó bằng zero. `select` giải mã và chọn frame trình chiếu đầu tiên có PTS không nhỏ
hơn mốc. `showinfo` ghi `pts`, `pts_time` và `time_base`; giữ log cạnh ảnh.

```text
ffmpeg -hide_banner -copyts -i INPUT -vf "select='gte(t,T_SECONDS)',trim=end_frame=1,showinfo" -frames:v 1 -fps_mode passthrough -update 1 frame.png
```

Đối chiếu `pts_time` thực trong stderr với ảnh được giải mã; `trim` giữ một dòng PTS trong log và
`-update 1` ghi một ảnh thay vì tên chuỗi. Không gắn nhãn ảnh bằng mốc yêu cầu nếu chúng khác nhau.
Với nhiều mốc, lặp cho các điểm rủi ro/cut, lưu mỗi log riêng. Probe đủ `color_range`, `color_space`,
`color_transfer`, `color_primaries`; giá trị `unknown` không chứng minh metadata SDR. Contact sheet
chỉ giúp lướt tổng quan, không chứng minh pixel bất biến. Đoạn GOP dài có thể cần giải mã từ keyframe
trước đó; lệnh trên ưu tiên mốc đúng hơn tốc độ seek. Offset A/V và timestamp âm vẫn cần được kiểm
riêng trước khi khẳng định hỗ trợ.

`video-studio cleanup verify` chỉ xác minh MP4 và manifest do contract `cleanup apply` tạo: dùng
đúng `--input`, thư mục `--out` và `--name` của lần apply. Không dùng nó làm verifier chung, không
dùng cho VFR/HDR/rotation/format bị cleanup từ chối. Technical pass cũng không tự hoàn thành visual
review. Khi cần chứng minh pixel ngoài vùng sửa không đổi, so sánh native decoded planes; JPEG/RGB
contact sheet không đủ.

## T2 — Nguồn, fingerprint và reuse

- **Dùng khi:** sửa lặp asset/transcript hoặc nguy cơ lấy nhầm file cùng tên.
- **Bỏ qua khi:** clip dùng một lần, không có cache cần quyết định; provenance tối thiểu vẫn phải
  giữ nếu nguồn cần ghi công.
- **Intake:** xác định đường local được phép, nguồn/quyền dùng, nội dung, tham số và phiên bản công
  cụ liên quan.
- **Khuyến nghị:** tái dùng chỉ khi fingerprint nội dung, setting và version khớp; giữ quan hệ
  nguồn → output và lý do reuse. Ưu tiên cache transcript hiện có, không dựng asset database.
- **Fallback:** metadata thiếu, model/version không rõ, output lỗi hoặc nguồn đổi thì cache miss có
  lý do; không tự tải lại hay gọi provider.
- **QA:** cùng basename nhưng khác bytes không được hit; đổi setting phải miss; output phải đọc
  được, nguồn không bị ghi đè. Không đưa credential hay URL có token vào manifest.
- **Thực hiện:** [`media-use`](../../hyperframes/media-use/SKILL.md) hướng dẫn nguồn/quyền dùng;
  [`video-edit`](../../video-edit/SKILL.md) sở hữu luồng transcript hiện có. Phần fingerprint tổng
  quát trong thẻ là kiểm tra thủ công; không có asset ledger/runtime cache chung trong TK1.

## T3 — Chữ hiển thị và lời đọc

- **Dùng khi:** số, tỷ lệ, đơn vị, tên hoặc viết tắt có nguy cơ bị TTS/ASR đọc sai.
- **Bỏ qua khi:** lời và chữ chuẩn giống nhau, dễ đọc; không nhân đôi nội dung mọi câu.
- **Intake:** hỏi cách đọc được duyệt và chữ chính xác cần giữ; kiểm xem voice/pronounce hiện có
  giải quyết được chưa.
- **Khuyến nghị:** giữ chữ authored làm caption/visual; chỉ chuẩn hóa bản đưa vào TTS tại đoạn cần
  thiết. Tận dụng `brand.pronounce` và đường voice hiện có.
- **Fallback:** ASR thiếu hoặc lệch thì caption theo cụm có nhãn cần review; không để ASR ghi đè
  lời đã duyệt và không giả độ chính xác karaoke.
- **QA:** đối chiếu nghĩa số/đơn vị/tên trên hình với audio xuất; nghe thử audio, không chỉ kiểm
  chuỗi text. Chỉ mở code mapping mới nếu pilot tái hiện gap.
- **Thực hiện:** [`embedded-captions`](../../hyperframes/embedded-captions/SKILL.md) sở hữu hướng
  dẫn caption; [`hyperframes-audio`](../../hyperframes/hyperframes-audio/SKILL.md) xử lý audio
  composition; [`video-edit`](../../video-edit/SKILL.md) xử lý footage đã thu. TTS normalize và
  `brand.pronounce` sẵn có không đồng nghĩa đã có schema display/spoken hay mapping span mới.

## T4 — Anchor lời–hình

- **Dùng khi:** đổi lời/nhịp làm chart, callout hoặc cảnh lệch khỏi luận điểm.
- **Bỏ qua khi:** clip ngắn, một lần dựng, cue theo đoạn đủ dùng.
- **Intake:** chốt lời/audio nào là nguồn thời gian và các cue nào thực sự cần bám.
- **Khuyến nghị:** gắn ID cho beat/cụm ý rồi dùng timing quan sát được để định vị cue; giữ source
  clock tách final clock khi cắt/retime.
- **Fallback:** anchor trùng/thiếu hoặc biến đổi không hỗ trợ thì báo rõ, dùng cue theo đoạn sau khi
  thống nhất; không tự chọn lần xuất hiện đầu của phrase lặp.
- **QA:** sửa tốc độ audio phải cập nhật cue; kiểm file xuất tại cut/offset. Gắn nhãn observed,
  aligned, interpolated hoặc estimated theo bằng chứng; không gọi estimated là word-accurate.
- **Thực hiện:** [`hyperframes-animation`](../../hyperframes/hyperframes-animation/SKILL.md) đặt cue
  thủ công trong composition; [`video-edit`](../../video-edit/SKILL.md) xử lý mốc EDL cho footage.
  Resolver anchor dùng chung chưa có; nếu không thể ánh xạ thủ công đáng tin cậy, dùng cue theo đoạn.

## T5 — Demo màn hình có bằng chứng

- **Dùng khi:** người xem cần học thao tác UI hoặc xác minh trạng thái sản phẩm.
- **Bỏ qua khi:** luận điểm không gắn giao diện; dùng sơ đồ nếu giải thích khái niệm tốt hơn.
- **Intake:** hỏi hành động cần làm lại và có quay/ảnh thật hay chưa.
- **Khuyến nghị:** ghép trước → thao tác thật → sau; crop/zoom vừa đủ, dùng callout để chỉ điểm
  quan trọng, kiểm ở kích thước phát hành.
- **Fallback:** ảnh chỉ chứng minh trạng thái; thiếu video thì ghi là minh họa, không claim chứng
  minh thao tác. Dùng fixture giả, không capture dữ liệu nhạy cảm.
- **QA:** kiểm bước trọng yếu, trạng thái trước/sau, khả năng đọc và phần UI bị che. Không yêu cầu
  recorder hay runtime mới.
- **Thực hiện:** [`product-launch-video`](../../hyperframes/product-launch-video/SKILL.md) cung cấp
  cách trình bày demo; [`video-edit`](../../video-edit/SKILL.md) cắt bản quay thật. Chụp/quay màn
  hình là đầu vào người dùng cung cấp; skill không tự capture hay xác minh sản phẩm đang chạy.

## T6 — B-roll và overlay theo mục đích

- **Dùng khi:** cần bằng chứng, hành động, bối cảnh hoặc hình giúp hiểu claim.
- **Bỏ qua khi:** UI/sơ đồ chính đã nói rõ; tránh chèn footage cho từng danh từ.
- **Intake:** xác định claim/beat, source được phép, đoạn vào/ra và mục đích của mỗi shot.
- **Khuyến nghị:** gắn vai trò `evidence`, `illustration`, `context` hoặc `action`; chọn shot theo
  khoảng nội dung, source span, crop và vùng chữ an toàn.
- **Fallback:** thiếu footage đúng thì dùng đồ họa trung tính, ghi rõ là minh họa; không loop/freeze
  để kéo dài mà không kiểm hậu quả.
- **QA:** hình không ám chỉ sự kiện sai; nguồn và độ dài đủ; caption không che dữ liệu; xem đoạn cut
  vào/ra ở video thật.
- **Thực hiện:** [`media-use`](../../hyperframes/media-use/SKILL.md) quản lý lựa chọn và provenance;
  [`faceless-explainer`](../../hyperframes/faceless-explainer/SKILL.md) định hướng hình giải thích;
  [`video-edit`](../../video-edit/SKILL.md) áp dụng overlay vào footage. Shot map là tài liệu thủ
  công, chưa có asset graph hoặc chọn B-roll tự động.

## T7 — Continuity nhân vật và camera

- **Dùng khi:** nhân vật, đạo cụ hay không gian quay lại qua nhiều cảnh hoặc continuity đang lỗi.
- **Bỏ qua khi:** chỉ có một lần xuất hiện; không dựng character bible dài mặc định.
- **Intake:** hỏi đặc điểm nào phải giữ và ngoại lệ nào có chủ ý.
- **Khuyến nghị:** ghi gọn identity/costume/props/location; liên kết reference asset với beat,
  action, shot/camera và trục nhìn; theo dõi thay đổi có chủ đích.
- **Fallback:** ưu tiên ảnh nhất quán kèm narration; không thêm provider/lip-sync chỉ để chữa
  continuity.
- **QA:** xem contact sheet theo thứ tự; kiểm nhân vật/đạo cụ, hành động trước-sau và hướng nhìn;
  similarity score riêng lẻ không đủ nghiệm thu.
- **Thực hiện:** [`general-video`](../../hyperframes/general-video/SKILL.md) giúp cấu trúc cảnh;
  [`media-use`](../../hyperframes/media-use/SKILL.md) theo dõi reference asset; [`video-edit`](../../video-edit/SKILL.md)
  xử lý footage/cut. Đây là checklist sản xuất thủ công; chưa có runtime continuity store hay
  character provider mặc định.

## T8 — Caption người nói và safe area

- **Dùng khi:** nhiều người nói khó phân biệt hoặc caption che mặt/UI.
- **Bỏ qua khi:** narration một giọng và caption cố định đọc được.
- **Intake:** xác nhận có nhiều speaker thật không, cần nhận diện bằng tên hay chỉ phân biệt lượt nói,
  và có crop/reframe không.
- **Khuyến nghị:** giữ nhãn speaker ở cue do người dựng xác nhận; đặt safe area trước; tracking khuôn
  mặt là lớp riêng chỉ khi có pilot và căn cứ map speaker-face.
- **Fallback:** speaker/track không chắc thì dùng caption cố định hoặc nhãn trung tính; unknown/null
  hợp lệ. Không cài WhisperX/face tracker mặc định.
- **QA:** kiểm speaker qua edit, cut/occlusion, crop 9:16 và vùng UI; không mang tọa độ cũ sang canvas
  mới nếu chưa đổi hệ tọa độ.
- **Thực hiện:** [`video-edit`](../../video-edit/SKILL.md) sở hữu dựng footage; [`embedded-captions`](../../hyperframes/embedded-captions/SKILL.md)
  sở hữu hướng dẫn caption cố định. Local distill backend hiện không diarize; speaker-aware caption
  qua pack/render và face tracking chưa được triển khai trong TK1/TK7. Nếu không có workflow sẵn
  được duyệt để giữ speaker ID, dùng nhãn thủ công/neutral hoặc hỏi trước khi mở rộng.

## T9 — Nhịp dựng và bàn giao âm thanh

- **Dùng khi:** nhạc lấn narration, khoảng nghỉ cắt ý hoặc transition âm thanh bị gãy.
- **Bỏ qua khi:** giọng sạch trên nền yên và đuôi lời nguyên vẹn.
- **Intake:** hỏi kênh phát/thiết bị mục tiêu và điểm nghe có vấn đề; không áp một loudness target
  chung cho mọi sản phẩm.
- **Khuyến nghị:** dùng mix/ducking hiện có; rà khoảng nghỉ, đuôi lời và transition; thêm nhạc/SFX
  chỉ khi nó phục vụ ý hoặc nhịp.
- **Fallback:** nếu không nghe được bản cuối, ghi rõ chưa kiểm; không coi meter là thay thế nghe.
- **QA:** nghe file encode cuối, kiểm clipping, lời không cụt và timing sau edit; ghi thiết bị/giới
  hạn đã thử.
- **Thực hiện:** [`hyperframes-audio`](../../hyperframes/hyperframes-audio/SKILL.md) xử lý audio
  composition; [`video-edit`](../../video-edit/SKILL.md) sửa âm thanh trên footage. Cả hai là hướng
  dẫn cho công cụ/luồng hiện có; không có module audio runtime mới trong TK1.

## Nguồn Hypit đã ghim

- [Review reference video](https://github.com/hypit-ai/hypit/blob/85e01c76716498e6ec5b8bdfb6b374ca67f0195a/skills/hypit/references/creation/reference-video.md) và [production review](https://github.com/hypit-ai/hypit/blob/85e01c76716498e6ec5b8bdfb6b374ca67f0195a/skills/hypit/references/production/review.md): gợi ý xem output cùng mốc rủi ro.
- [Narrative speech alignment](https://github.com/hypit-ai/hypit/blob/85e01c76716498e6ec5b8bdfb6b374ca67f0195a/packages/narrative-speech-alignment/README.md): gợi ý gắn ngữ nghĩa với timing.
- [Screen demonstrations](https://github.com/hypit-ai/hypit/blob/85e01c76716498e6ec5b8bdfb6b374ca67f0195a/skills/hypit/references/playbooks/craft/screen-demonstrations.md), [B-roll](https://github.com/hypit-ai/hypit/blob/85e01c76716498e6ec5b8bdfb6b374ca67f0195a/skills/hypit/references/playbooks/craft/b-roll.md), [short drama](https://github.com/hypit-ai/hypit/blob/85e01c76716498e6ec5b8bdfb6b374ca67f0195a/skills/hypit/references/playbooks/formats/short-drama.md) và [caption tracking](https://github.com/hypit-ai/hypit/blob/85e01c76716498e6ec5b8bdfb6b374ca67f0195a/skills/hypit/references/playbooks/craft/caption-tracking.md): gợi ý về demo, shot, continuity và caption.

Các liên kết trên không xác nhận license cho sao chép/chuyển thể và không ngụ ý Hypit đã cài,
chạy hoặc benchmark. Mô tả sản phẩm và checklist này là văn bản độc lập.
