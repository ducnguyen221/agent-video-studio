---
title: Prompt Motion reference library
summary: Motion references, source prompt analysis and original HyperFrames adaptation briefs, with searchable scene purpose and layout cost.
---

# Prompt Motion — thư viện tham chiếu

**240 entry = 238 motion gallery + 2 trang template chi tiết**, mỗi entry một Markdown có ID ổn định. Đã phân tích toàn public prompt khi có; chưa xem toàn video, đo media hoặc chạy template HyperFrames. Prompt triển khai là bản viết mới của kho, không bulk copy prompt/code/video tác giả.

[Phân tích tổng hợp](ANALYSIS.md) · [Cách chọn và dựng](USAGE.md) · [Catalog đủ 240 mẫu](CATALOG.md) · [Taxonomy](TAXONOMY.md) · [JSON lọc](index.json) · [Metadata gallery](source/catalog-metadata.json) · [Metadata template](source/templates-metadata.json)

## Hai trang mẫu nền tảng

| ID / tên | Dùng khi | Tỉ lệ ưu tiên · vùng · thời lượng đề xuất | Nguồn |
|---|---|---|---|
| [PM-template-showreel — The showreel prompt](motions/template-showreel.md) | Một motif thống nhất cho hook → phát triển → chốt | 16:9 · fullscreen · 8–15s | [web](https://prompt-motion.com/templates/showreel) |
| [PM-template-realtime — The 3D template](motions/template-realtime.md) | Camera 3D và góc máy chủ đạo nối các shot | 16:9 · fullscreen · 12–20s | [web](https://prompt-motion.com/templates/realtime) |

## Chọn theo trục hình

Trục hình là ẩn dụ chính của cảnh (đếm số, lõi–vệ tinh, cửa sổ mã…). Mỗi trục liệt kê 4 mẫu có thiết kế riêng; bảng đủ 240 mẫu với cột «Ý chính» ở [CATALOG.md](CATALOG.md). 68/240 mẫu là baseline dùng chung theo nhóm (dấu ⚑ ở CATALOG): ý tưởng của chúng là khuôn nhóm, không phải phân tích riêng.

| Trục hình | Số mẫu | Vùng hay dùng | Mẫu riêng nên đọc trước |
|---|---|---|---|
| Đếm số / một con số lớn | 10 | partial | [PM-eyishazyer-af035b](motions/eyishazyer-af035b.md) Motion designer showreel<br>[PM-ismailfahmi-557268](motions/ismailfahmi-557268.md) Drone Emprit showreel<br>[PM-jasonzhou1993-8595e0](motions/jasonzhou1993-8595e0.md) Claude motion reel<br>[PM-palashbagchi11-0a4b6b](motions/palashbagchi11-0a4b6b.md) Backlink audit data promo |
| Cửa sổ mã / terminal | 2 | partial | [PM-dale-vaz-cc612a](motions/dale-vaz-cc612a.md) Sahi trading terminal reveal<br>[PM-rames-jusso-589f80](motions/rames-jusso-589f80.md) UK dubstep track with ASCII visual |
| Lõi–vệ tinh / hạt | 14 | fullscreen | [PM-ajith-io-4c248f](motions/ajith-io-4c248f.md) Distilbook promo showreel<br>[PM-ajith-io-ea7f2d](motions/ajith-io-ea7f2d.md) Distilbook motion showreel<br>[PM-apoorvjain25-d24184](motions/apoorvjain25-d24184.md) Photon journey from the Sun<br>[PM-blue-clarity-ef56d0](motions/blue-clarity-ef56d0.md) Particle sphere motion reel |
| Biến hình khối | 13 | fullscreen | [PM-demonugc-4c5753](motions/demonugc-4c5753.md) Morphing UI states loop<br>[PM-gdgtify-287ddf](motions/gdgtify-287ddf.md) Speech built as architecture<br>[PM-gorden-sun-041f56](motions/gorden-sun-041f56.md) Beat-synced bouncing 3D ball<br>[PM-kamstudiolabs-447565](motions/kamstudiolabs-447565.md) Collision-driven music machine |
| Đồ thị / biểu đồ | 20 | partial | [PM-daniel-haida-8691d4](motions/daniel-haida-8691d4.md) Taxtello bookkeeping app film<br>[PM-eyishazyer-af035b](motions/eyishazyer-af035b.md) Motion designer showreel<br>[PM-ismailfahmi-557268](motions/ismailfahmi-557268.md) Drone Emprit showreel<br>[PM-jasonzhou1993-8595e0](motions/jasonzhou1993-8595e0.md) Claude motion reel |
| Sơ đồ nút–liên kết | 25 | partial | [PM-0xnfrith-5be616](motions/0xnfrith-5be616.md) Celld job ownership explainer<br>[PM-alex-prompter-1ea044](motions/alex-prompter-1ea044.md) Animated business explainer<br>[PM-blueoctopusai-dd17bd](motions/blueoctopusai-dd17bd.md) First & 10 yellow line explainer<br>[PM-chatgptastra-0d95c7](motions/chatgptastra-0d95c7.md) Motion principles showreel |
| Camera / không gian 3D | 32 | fullscreen | [PM-aichrislee-a6cb42](motions/aichrislee-a6cb42.md) Motion designer showreel<br>[PM-ajith-io-4c248f](motions/ajith-io-4c248f.md) Distilbook promo showreel<br>[PM-ajith-io-ea7f2d](motions/ajith-io-ea7f2d.md) Distilbook motion showreel<br>[PM-allforbigfire-86ff3c](motions/allforbigfire-86ff3c.md) Anime robot combining sequence |
| Nhân vật / cảnh kể chuyện | 23 | fullscreen | [PM-abderrahmen-g-9e8ed0](motions/abderrahmen-g-9e8ed0.md) Sketchbook animals come alive<br>[PM-allforbigfire-86ff3c](motions/allforbigfire-86ff3c.md) Anime robot combining sequence<br>[PM-anilraok-eff262](motions/anilraok-eff262.md) Scrabble tile character story<br>[PM-axtonliu-0b861d](motions/axtonliu-0b861d.md) Pelican riding a bicycle |
| Chữ chuyển động | 60 | fullscreen | [PM-1littlecoder-9fef89](motions/1littlecoder-9fef89.md) Claude self-intro motion graphic<br>[PM-aichrislee-a6cb42](motions/aichrislee-a6cb42.md) Motion designer showreel<br>[PM-ajith-io-b5626e](motions/ajith-io-b5626e.md) Abstract motion design reel<br>[PM-aschapmann-131210](motions/aschapmann-131210.md) SaaS launch video |
| Ảnh / ghép cảnh | 10 | partial | [PM-apoorvjain25-d24184](motions/apoorvjain25-d24184.md) Photon journey from the Sun<br>[PM-gigabit-million-16b3a0](motions/gigabit-million-16b3a0.md) Steam new releases news recap<br>[PM-itsolelehmann-e47532](motions/itsolelehmann-e47532.md) Four seasons train window<br>[PM-justincooperman-e7bbc4](motions/justincooperman-e7bbc4.md) Tented image gen product video |
| Giao diện sản phẩm | 101 | partial | [PM-agonaliu-466a8f](motions/agonaliu-466a8f.md) Trezio app motion reel<br>[PM-ai-baymax-0ef9dd](motions/ai-baymax-0ef9dd.md) FigPad product promo<br>[PM-aistocksavvy-3fb9f5](motions/aistocksavvy-3fb9f5.md) Stock analysis app promo<br>[PM-ajith-io-c52e09](motions/ajith-io-c52e09.md) Distilbook product video |

## Chọn theo nhóm công việc

| Nhóm | Số mẫu | Trong CATALOG |
|---|---|---|
| Demo tác vụ / sản phẩm | 105 | [CATALOG.md](CATALOG.md) |
| Bằng chứng / số liệu | 11 | [CATALOG.md](CATALOG.md) |
| Giải thích / quy trình | 25 | [CATALOG.md](CATALOG.md) |
| Chữ / hook / chốt | 59 | [CATALOG.md](CATALOG.md) |
| Hình học / chuyển ý | 3 | [CATALOG.md](CATALOG.md) |
| Hạt / năng lượng | 8 | [CATALOG.md](CATALOG.md) |
| Nhân vật / kể chuyện | 20 | [CATALOG.md](CATALOG.md) |
| Ảnh / chứng cứ | 2 | [CATALOG.md](CATALOG.md) |
| Mã / công cụ | 1 | [CATALOG.md](CATALOG.md) |
| Không gian / camera | 6 | [CATALOG.md](CATALOG.md) |

## Bộ lọc và cách trình lựa chọn

JSON có các trục độc lập: scene_roles, techniques, intensity, rhythm, content_capacity, coverage, recommended_region, recommended_occupancy, primary_recommended_ratio và ratio_fit. preferred/low là điểm xuất phát thuận tiện, adaptable/medium cần bố trí lại, requires_redesign/high cần dựng lại framing. Đây là ước lượng thiết kế, chưa phải benchmark công sức.

Với mỗi beat, đưa 2–3 lựa chọn gồm **ID · tên · link nguồn · vai trò · aspect đề xuất · screen area đề xuất**, giải thích khác biệt. Đọc entry trước khi hứa hiệu ứng; kiểm license từng asset và dùng general-video cho các phim dài/có narration. Tất cả entry ở đây có runtime_tested:false.

## Độ phủ và giới hạn chứng cứ

235/240 entry có public prompt được đọc toàn bộ; 5 gallery entry giới thiệu skill thay cho prompt. Raw gallery giữ 233/238 cờ prompt, 238 preview URL; template detail có thêm 2 brief. No raw prompt/code/media archive. Source facts, brief specifications và Sol recommendations được tách trong từng file và JSON.

Sitemap có **260 URL = 238 gallery + 2 template chi tiết + 20 trang khác**, không còn URL chưa phân loại. [coverage.json](source/coverage.json) giữ danh sách đầy đủ và lý do phân loại, gồm trang chỉ mục, bộ lọc và blog. Tất cả 240 entry có link nguồn và provenance tới metadata/notes. Chưa có quyền bulk redistribution, nên prompt gốc chỉ được đọc để diễn giải; tác giả vẫn giữ quyền với prompt/video của họ.
