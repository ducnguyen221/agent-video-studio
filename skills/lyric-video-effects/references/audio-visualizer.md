# Phổ tròn và nốt theo giọng

`assets/audio-visualizer.js` vẽ trên một canvas riêng, nhận dữ liệu đã lưu và thời gian
composition; không giải mã audio, không phân tích live và không tự xác minh cue. Nó là
thành phần tùy chọn cho lyric video, không phải beat tracker hay công cụ nhận dạng giọng.

## Đầu vào và offset

- `spectrum.frames`: mảng frame, mỗi frame có cùng số dải, mỗi giá trị hữu hạn trong `0..1`.
  Lưu cùng phân tích ngoài thành phần: hash/phiên bản bản thu, dải tần, FFT, tần số mẫu,
  hop, cách chuẩn hóa và offset. Envelope và phổ đa dải là dữ liệu khác nhau.
- `sampleRate` và `hopSamples`: tần số mẫu và số mẫu giữa hai frame phổ. `offset` là
  giây trong composition tại đó **giây 0 của audio** bắt đầu. Nếu dữ liệu phổ được cắt từ
  giữa bản thu, phải căn lại mốc trước khi dùng; không cộng offset hai lần.
- `wordCues`: mảng `{start}` theo giây audio, đã sắp theo thời gian. Mỗi cue tạo một nốt;
  cue câu không thay được cue từ. Nhận dạng máy chỉ là ứng viên và phải ghi rõ trạng thái
  riêng của text và timing; không nâng lên verified khi chưa đối chiếu.
- `region`: `{x,y,width,height}` nằm trong canvas. Vòng đặt phía trái vùng, nốt bay sang
  phải theo đường uốn lên xuống rồi mờ; `ringRadius`, `maxBarLength`, `centerX`, `centerY`
  tùy chọn điều chỉnh bán kính, độ dài cột và tâm vòng theo pixel canvas. `noteDuration`,
  `barCount`, `hueStart`, `hueRate` điều chỉnh thời gian, khoảng cách cột và tốc độ chuyển
  màu. Vòng, cột và khoảng bay tối thiểu của nốt phải vừa trong vùng hoặc hàm sẽ báo lỗi.
  Phải chọn vùng/mask bảo vệ
  chữ và mặt; thành phần không nhận diện khuôn mặt và không tự tạo mask nội dung.

## Cách gắn

Nạp `assets/audio-visualizer.js`, tạo canvas riêng và gọi một lần để nhận hàm vẽ. Canvas
sẽ bị xóa và vẽ lại mỗi lần gọi; đừng dùng chung canvas chứa nội dung khác.

```js
const paint = LyricAudioVisualizer.createAudioVisualizer(canvas, {
  spectrum: { frames, sampleRate, hopSamples, offset: audioOffset },
  wordCues, region: { x: 40, y: 450, width: 640, height: 230 },
  barCount: 64, noteDuration: 2, hueStart: 35, hueRate: 16,
});
// Trong callback seek/timeline của composition:
paint(compositionSeconds);
```

`paint(t)` trả `{bands, notes, ring}` để kiểm thử; nội suy frame phổ và các quỹ đạo là xác định
theo `t`, không dùng timer riêng. Dữ liệu sai bị từ chối bằng lỗi, không tự thay bằng mảng
trống. Hiệu ứng cần kiểm render/seek và glyph tại độ phân giải đích; test số học hoặc canvas
giả không chứng minh video cuối đã đồng bộ. Kiểm mặt, chữ, vùng cắt, audio vào/ra và các cue
trên MP4; ghi riêng kết quả đã chạy và `not_run`.
