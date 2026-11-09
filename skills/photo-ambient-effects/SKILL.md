---
name: photo-ambient-effects
description: "Design and render deterministic ambient overlays and looping GIF previews over a still photo. Use when a video needs stars, fireflies, meteors, sea shimmer or corner sun rays while protecting lyric text and subjects; supports an owning video workflow."
---

# Làm ảnh tĩnh có không khí chuyển động

Đầu vào: ảnh, vùng cần bảo vệ, đồng hồ composition, nhịp/cường độ nhạc đã lưu nếu có.
Đầu ra: lớp phủ tái lập được, GIF/MP4 demo và preset có mức opacity rõ.
Chỉ dùng envelope đã lưu cùng mốc audio; nội suy theo thời gian composition, giới hạn
strength và che vùng bảo vệ bằng mask thực trong composition. Không coi vị trí mặc định
của painter là bằng chứng vùng mặt hoặc chữ đã được bảo vệ.
Skill này bổ trợ workflow đang dựng video; không thay ảnh, sửa khuôn mặt hoặc tự sinh chuyển động nhân vật.

## Quy trình

1. Khoá ảnh và vùng mặt/chữ, chọn hiệu ứng theo ánh sáng/cảnh. Đọc
   [references/overlay-recipes.md](references/overlay-recipes.md) để chọn sao, đom đóm, sao băng,
   mặt nước hoặc tia nắng. Xong khi mỗi lớp có vị trí, thời gian, cường độ; sai cảnh thì đổi preset.
2. Nạp [assets/ambient-painter.js](assets/ambient-painter.js) và/hoặc
   [assets/sun-rays.js](assets/sun-rays.js), caller truyền canvas có sẵn và thời gian composition.
   [assets/dust.js](assets/dust.js) là preset bụi sáng mới; cần mask vùng bảo vệ và render kiểm.
   Đọc [references/runtime-and-gif.md](references/runtime-and-gif.md) trước khi tích hợp clock/loop.
   Xong khi cùng t cho cùng ảnh và t+8 s nối vòng; lỗi thì sửa clock/seed, không thêm timer riêng.
3. Dựng demo 8 s, nhìn ở kích thước video và GIF nhỏ. Tia nắng phải có hình quạt chéo từ góc,
   không gọi radial glow là tia nắng. Xong khi hình học thấy rõ và mặt/chữ vẫn đọc được;
   lỗi thì giảm opacity, đổi góc hoặc che vùng cần bảo vệ.
4. Gắn các cửa sổ nắng thưa vào cấu trúc nhạc, fade .8–1.2 s. Có thể nhân strength bằng envelope
   đã phân tích/lưu file; [assets/envelope.js](assets/envelope.js) nội suy xác định và
   giới hạn strength. Không phân tích live hay dùng âm thanh hệ thống khi render.
   Xong khi seek lùi/tiến giống nhau và ảnh gốc không bị transform nếu brief yêu cầu giữ nguyên.
5. Kiểm MP4 thật, GIF loop, frame đen, thời lượng; ghi phần đã xem và phần chưa kiểm.
   Đọc [references/provenance-and-coverage.md](references/provenance-and-coverage.md) để mô tả
   giới hạn: preset hiện được dựng kiểm 16:9; khung khác cần đổi vùng và xem lại.

## Gotchas

- GIF là bản xem hiệu ứng, không phải nguồn tốt để chồng vào full video. Render canvas gốc để
  tránh dải màu, nền đen và giảm độ phân giải; MP4 thường nhỏ hơn GIF.
- Một chu kỳ canvas không bảo đảm video cuối nối vòng nếu strength/nhạc thay đổi ở biên.
- Giữ glow nhỏ, lớp phủ sau ảnh và trước chữ; shade giúp tương phản nhưng không thay việc nhìn kiểm.
- Không đóng gói ảnh, nhạc, font, waveform hoặc đường dẫn riêng của project vào skill.
