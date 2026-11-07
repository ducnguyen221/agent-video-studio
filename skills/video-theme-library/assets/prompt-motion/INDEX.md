---
title: Prompt Motion reference library
summary: Motion references, source prompt analysis and original HyperFrames adaptation briefs, with searchable scene purpose and layout cost.
---

# Prompt Motion — thư viện tham chiếu

**240 entry = 238 motion gallery + 2 trang template chi tiết**, mỗi entry một Markdown có ID ổn định. Đã phân tích toàn public prompt khi có; chưa xem toàn video, đo media hoặc chạy template HyperFrames. Prompt triển khai là bản viết mới của kho, không bulk copy prompt/code/video tác giả.

[Phân tích tổng hợp](ANALYSIS.md) · [Cách chọn và dựng](USAGE.md) · [Taxonomy](TAXONOMY.md) · [JSON lọc](index.json) · [Metadata gallery](source/catalog-metadata.json) · [Metadata template](source/templates-metadata.json)

## Hai trang mẫu nền tảng

| ID / tên | Dùng khi | Tỉ lệ ưu tiên · vùng · thời lượng đề xuất | Nguồn |
|---|---|---|---|
| [PM-template-showreel — The showreel prompt](motions/template-showreel.md) | Một motif thống nhất cho hook → phát triển → chốt | 16:9 · fullscreen · 8–15s | [web](https://prompt-motion.com/templates/showreel) |
| [PM-template-realtime — The 3D template](motions/template-realtime.md) | Camera 3D và góc máy chủ đạo nối các shot | 16:9 · fullscreen · 12–20s | [web](https://prompt-motion.com/templates/realtime) |

## Chọn theo việc cảnh cần làm

Đây là **khuyến nghị dựng mới**. Tỉ lệ ưu tiên khác source aspect; thời lượng đề xuất khác duration media; area là bố cục đề xuất, không số đo pixel nguồn.

| Việc | Tham chiếu nên đọc | Vai trò / ratio / screen area |
|---|---|---|
| Demo tác vụ / sản phẩm | [PM-twoclipping-5cba86 — Shape morphing through UI states](motions/twoclipping-5cba86.md) ([web](https://prompt-motion.com/twoclipping-5cba86))<br>[PM-twoclipping-221cab — Photo print app launch film](motions/twoclipping-221cab.md) ([web](https://prompt-motion.com/twoclipping-221cab))<br>[PM-tstfully-0aa6b4 — YouTube transcript product ad](motions/tstfully-0aa6b4.md) ([web](https://prompt-motion.com/tstfully-0aa6b4)) | explain / 1:1 / partial<br>explain / 1:1 / partial<br>explain / 16:9 / partial |
| Bằng chứng / số liệu | [PM-parkerrex-1a54fe — Token bucket rate limiter](motions/parkerrex-1a54fe.md) ([web](https://prompt-motion.com/parkerrex-1a54fe))<br>[PM-linearuncle-5d2bae — Derivative concept explainer](motions/linearuncle-5d2bae.md) ([web](https://prompt-motion.com/linearuncle-5d2bae))<br>[PM-palashbagchi11-0a4b6b — Backlink audit data promo](motions/palashbagchi11-0a4b6b.md) ([web](https://prompt-motion.com/palashbagchi11-0a4b6b)) | explain / 16:9 / partial<br>explain / 16:9 / partial<br>proof / 16:9 / partial |
| Giải thích / quy trình | [PM-yunn260414-60d996 — What is Git explainer](motions/yunn260414-60d996.md) ([web](https://prompt-motion.com/yunn260414-60d996))<br>[PM-ror-fly-9950f1 — Negroni recipe animation](motions/ror-fly-9950f1.md) ([web](https://prompt-motion.com/ror-fly-9950f1))<br>[PM-blueoctopusai-dd17bd — First & 10 yellow line explainer](motions/blueoctopusai-dd17bd.md) ([web](https://prompt-motion.com/blueoctopusai-dd17bd)) | explain / 16:9 / partial<br>explain / 16:9 / partial<br>explain / 16:9 / partial |
| Chữ / hook / chốt | [PM-template-showreel — The showreel prompt](motions/template-showreel.md) ([web](https://prompt-motion.com/templates/showreel))<br>[PM-gdgtify-287ddf — Speech built as architecture](motions/gdgtify-287ddf.md) ([web](https://prompt-motion.com/gdgtify-287ddf))<br>[PM-rneayan-474bcf — Risograph studio intro](motions/rneayan-474bcf.md) ([web](https://prompt-motion.com/rneayan-474bcf)) | hook / 16:9 / fullscreen<br>hook / 1:1 / fullscreen<br>explain / 16:9 / partial |
| Hình học / chuyển ý | [PM-tdinh-me-815acb — TypingMind logo reveal](motions/tdinh-me-815acb.md) ([web](https://prompt-motion.com/tdinh-me-815acb))<br>[PM-kantamk-61f410 — Ball escaping twelve rings](motions/kantamk-61f410.md) ([web](https://prompt-motion.com/kantamk-61f410)) | hook / 16:9 / fullscreen<br>hook / 16:9 / fullscreen |
| Hạt / năng lượng | [PM-blue-clarity-ef56d0 — Particle sphere motion reel](motions/blue-clarity-ef56d0.md) ([web](https://prompt-motion.com/blue-clarity-ef56d0))<br>[PM-ajith-io-4c248f — Distilbook promo showreel](motions/ajith-io-4c248f.md) ([web](https://prompt-motion.com/ajith-io-4c248f)) | hook / 16:9 / fullscreen<br>hook / 16:9 / fullscreen |
| Nhân vật / kể chuyện | [PM-loicrambo-ad6830 — Cycle of life animation](motions/loicrambo-ad6830.md) ([web](https://prompt-motion.com/loicrambo-ad6830))<br>[PM-abderrahmen-g-9e8ed0 — Sketchbook animals come alive](motions/abderrahmen-g-9e8ed0.md) ([web](https://prompt-motion.com/abderrahmen-g-9e8ed0)) | hook / 16:9 / fullscreen<br>hook / 16:9 / fullscreen |
| Ảnh / chứng cứ | [PM-sab8a-364a5a — Talking-head clip edit](motions/sab8a-364a5a.md) ([web](https://prompt-motion.com/sab8a-364a5a)) | hook / 16:9 / partial |
| Mã / công cụ | [PM-kloss-xyz-15182a — Chaotic Claude POV video](motions/kloss-xyz-15182a.md) ([web](https://prompt-motion.com/kloss-xyz-15182a)) | hook / 9:16 / fullscreen |
| Không gian / camera | [PM-template-realtime — The 3D template](motions/template-realtime.md) ([web](https://prompt-motion.com/templates/realtime))<br>[PM-twoclipping-d89be5 — Landing page 3D scroll](motions/twoclipping-d89be5.md) ([web](https://prompt-motion.com/twoclipping-d89be5)) | hook / 16:9 / fullscreen<br>explain / 16:9 / partial |

## Bộ lọc và cách trình lựa chọn

JSON có các trục độc lập: scene_roles, techniques, intensity, rhythm, content_capacity, coverage, recommended_region, recommended_occupancy, primary_recommended_ratio và ratio_fit. preferred/low là điểm xuất phát thuận tiện, adaptable/medium cần bố trí lại, requires_redesign/high cần dựng lại framing. Đây là ước lượng thiết kế, chưa phải benchmark công sức.

Với mỗi beat, đưa 2–3 lựa chọn gồm **ID · tên · link nguồn · vai trò · aspect đề xuất · screen area đề xuất**, giải thích khác biệt. Đọc entry trước khi hứa hiệu ứng; kiểm license từng asset và dùng general-video cho các phim dài/có narration. Tất cả entry ở đây có runtime_tested:false.

## Catalog theo nhóm công việc

Nhóm là cách Sol đề xuất truy vấn, không thay nhãn nguồn. Một motion có thể làm nhiều vai trò; JSON giữ tất cả tags.

### Demo tác vụ / sản phẩm (105)

| ID / tên → file | Vai trò | Tỉ lệ ưu tiên | Vùng / diện tích hộp | Giây đề xuất | Nhịp mạnh | Kỹ thuật | Nguồn |
|---|---|---|---|---|---|---|---|
| [PM-twoclipping-5cba86 — Shape morphing through UI states](motions/twoclipping-5cba86.md) | explain/proof/cta | 1:1 | partial / 60% | 6–12 | medium | morph, ui | [web](https://prompt-motion.com/twoclipping-5cba86) |
| [PM-twoclipping-221cab — Photo print app launch film](motions/twoclipping-221cab.md) | explain/proof/cta | 1:1 | partial / 60% | 6–12 | medium | image, ui | [web](https://prompt-motion.com/twoclipping-221cab) |
| [PM-twoclipping-d89be5 — Landing page 3D scroll](motions/twoclipping-d89be5.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | camera, ui, 3d | [web](https://prompt-motion.com/twoclipping-d89be5) |
| [PM-gabrielbuzziv-4ff0c6 — Enxovaly baby app promo](motions/gabrielbuzziv-4ff0c6.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/gabrielbuzziv-4ff0c6) |
| [PM-notdwd-c2037d — Launch video remake comparison](motions/notdwd-c2037d.md) | explain/proof/cta | 1:1 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/notdwd-c2037d) |
| [PM-thismacapital-dfba20 — Travel visa service promo](motions/thismacapital-dfba20.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/thismacapital-dfba20) |
| [PM-lexnlin-f9b3bd8 — TasteSkill dashboard showcase](motions/lexnlin-f9b3bd8.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/lexnlin-f9b3bd8) |
| [PM-mengto-a7f4679 — HTML app demo skill](motions/mengto-a7f4679.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/mengto-a7f4679) |
| [PM-ajith-io-c52e09 — Distilbook product video](motions/ajith-io-c52e09.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/ajith-io-c52e09) |
| [PM-twoclipping-6dd14e — UGC ad generator promo](motions/twoclipping-6dd14e.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/twoclipping-6dd14e) |
| [PM-samuel-yostt-891f87 — ViralGrow product promo](motions/samuel-yostt-891f87.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/samuel-yostt-891f87) |
| [PM-lexnlin-6161a6 — Cinetic skill launch film](motions/lexnlin-6161a6.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/lexnlin-6161a6) |
| [PM-steventey-0d20e4 — Dub promo video](motions/steventey-0d20e4.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/steventey-0d20e4) |
| [PM-thayto-dev-44b911 — AjustaCV Pro pricing promo](motions/thayto-dev-44b911.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/thayto-dev-44b911) |
| [PM-anthonyriera-9b1b2a — Reddit marketing tool launch video](motions/anthonyriera-9b1b2a.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/anthonyriera-9b1b2a) |
| [PM-rossaxbt-94583b — White ball UI motion loop](motions/rossaxbt-94583b.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, shape | [web](https://prompt-motion.com/rossaxbt-94583b) |
| [PM-pankajstwt-49978ed — Voice agent landing page](motions/pankajstwt-49978ed.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, mask, stagger, 3d, camera | [web](https://prompt-motion.com/pankajstwt-49978ed) |
| [PM-robj3d3-b18fad — SuperX feature release teaser](motions/robj3d3-b18fad.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/robj3d3-b18fad) |
| [PM-ho-ba-f3f0e9 — mdfor.dev product intro video](motions/ho-ba-f3f0e9.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/ho-ba-f3f0e9) |
| [PM-itisrazak-3ad902 — Distilbook motion showreel](motions/itisrazak-3ad902.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/itisrazak-3ad902) |
| [PM-notdwd-7de38a — Frame by Frame launch video](motions/notdwd-7de38a.md) | explain/proof/cta | 1:1 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/notdwd-7de38a) |
| [PM-viktoroddy-98c1d8 — MotionSites one million visitors](motions/viktoroddy-98c1d8.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/viktoroddy-98c1d8) |
| [PM-melvynx-6cde6c — Email tool promo reel](motions/melvynx-6cde6c.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/melvynx-6cde6c) |
| [PM-rossaxbt-3085b7 — Ora 2 image model launch film](motions/rossaxbt-3085b7.md) | explain/proof/cta | 1:1 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/rossaxbt-3085b7) |
| [PM-polydao-7a572b — Jev engineering showreel](motions/polydao-7a572b.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/polydao-7a572b) |
| [PM-ultimaxbt-2ddf1e — Food craving launch film](motions/ultimaxbt-2ddf1e.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/ultimaxbt-2ddf1e) |
| [PM-ddryo-loos-300829 — Lism CSS 1.0 release video](motions/ddryo-loos-300829.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/ddryo-loos-300829) |
| [PM-brainextends-e19ac3 — Spotify product film](motions/brainextends-e19ac3.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/brainextends-e19ac3) |
| [PM-sudo-kiran-b055de — DistilBook motion explainer](motions/sudo-kiran-b055de.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/sudo-kiran-b055de) |
| [PM-arjunsh1607-93005d — Pixelup Labs studio showreel](motions/arjunsh1607-93005d.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/arjunsh1607-93005d) |
| [PM-hqmank-7c61f1 — Browser automation skill launch](motions/hqmank-7c61f1.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/hqmank-7c61f1) |
| [PM-ratheejaisal-1f4538 — founder.page launch video](motions/ratheejaisal-1f4538.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/ratheejaisal-1f4538) |
| [PM-prasad-pilla-2c0cba — Alan agent platform promo](motions/prasad-pilla-2c0cba.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/prasad-pilla-2c0cba) |
| [PM-dale-vaz-cc612a — Sahi trading terminal reveal](motions/dale-vaz-cc612a.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/dale-vaz-cc612a) |
| [PM-ezshine-c90d73 — AI Arena product promo](motions/ezshine-c90d73.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/ezshine-c90d73) |
| [PM-aistocksavvy-3fb9f5 — Stock analysis app promo](motions/aistocksavvy-3fb9f5.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/aistocksavvy-3fb9f5) |
| [PM-techyoutbe-945b56 — Visual guides library launch](motions/techyoutbe-945b56.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/techyoutbe-945b56) |
| [PM-lemomo-ai-0d9cff — Whiteboard skill tutorial](motions/lemomo-ai-0d9cff.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/lemomo-ai-0d9cff) |
| [PM-deifosv-04e4d3 — Tennis game launch video](motions/deifosv-04e4d3.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/deifosv-04e4d3) |
| [PM-visheshbaghell-3aba37 — Tally product demo](motions/visheshbaghell-3aba37.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/visheshbaghell-3aba37) |
| [PM-imthatcarlos-e04bfe — Sherwood agentic hedge fund explainer](motions/imthatcarlos-e04bfe.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/imthatcarlos-e04bfe) |
| [PM-paulo-kombucha-96431c — Mascot referral program promo](motions/paulo-kombucha-96431c.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/paulo-kombucha-96431c) |
| [PM-sudo-kiran-6609ed — DistilBook product explainer](motions/sudo-kiran-6609ed.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/sudo-kiran-6609ed) |
| [PM-demonugc-4c5753 — Morphing UI states loop](motions/demonugc-4c5753.md) | explain/proof/cta | 1:1 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/demonugc-4c5753) |
| [PM-jhylee95-e1152f — Supademo launch video](motions/jhylee95-e1152f.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/jhylee95-e1152f) |
| [PM-sachaarbonel-8f14f4 — Norilu product launch video](motions/sachaarbonel-8f14f4.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/sachaarbonel-8f14f4) |
| [PM-ercankeskinx-ec2568 — Five scroll-based sections](motions/ercankeskinx-ec2568.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/ercankeskinx-ec2568) |
| [PM-agonaliu-466a8f — Trezio app motion reel](motions/agonaliu-466a8f.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/agonaliu-466a8f) |
| [PM-daniel-haida-8691d4 — Taxtello bookkeeping app film](motions/daniel-haida-8691d4.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/daniel-haida-8691d4) |
| [PM-bthreeagency-b9b8d9 — Badge unlock screen animation](motions/bthreeagency-b9b8d9.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, particles | [web](https://prompt-motion.com/bthreeagency-b9b8d9) |
| [PM-bogdandragomir-35e024 — Product intro synced to music](motions/bogdandragomir-35e024.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/bogdandragomir-35e024) |
| [PM-en-ra-81c6dd — Website analyzer product promo](motions/en-ra-81c6dd.md) | explain/proof/cta | 1:1 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/en-ra-81c6dd) |
| [PM-jesscaroline7-1ff7cb — Ondefica app motion reel](motions/jesscaroline7-1ff7cb.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/jesscaroline7-1ff7cb) |
| [PM-theviableedge-9065be — Second brain service promo](motions/theviableedge-9065be.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/theviableedge-9065be) |
| [PM-0xfemyn-e114d3 — AIsa API key promo](motions/0xfemyn-e114d3.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/0xfemyn-e114d3) |
| [PM-reyzostyle-b55864 — Chunku product promo](motions/reyzostyle-b55864.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/reyzostyle-b55864) |
| [PM-macrohou-33959d — Ren app launch video](motions/macrohou-33959d.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/macrohou-33959d) |
| [PM-buildfastwithai-ed9447 — Three.js Skyraider aircraft model](motions/buildfastwithai-ed9447.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | 3d, camera | [web](https://prompt-motion.com/buildfastwithai-ed9447) |
| [PM-wani-shola-16ca7a — Developer portfolio site showreel](motions/wani-shola-16ca7a.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/wani-shola-16ca7a) |
| [PM-jayscambler-3f8889 — FundMyCompute platform overview](motions/jayscambler-3f8889.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/jayscambler-3f8889) |
| [PM-utopyaszx-1b2f94 — Bold Pilot SEO promo](motions/utopyaszx-1b2f94.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/utopyaszx-1b2f94) |
| [PM-aschapmann-131210 — SaaS launch video](motions/aschapmann-131210.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/aschapmann-131210) |
| [PM-marklaunches-3b9492 — Step race app promo](motions/marklaunches-3b9492.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/marklaunches-3b9492) |
| [PM-1stnoel-c20a89 — Sotto reading app explainer](motions/1stnoel-c20a89.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/1stnoel-c20a89) |
| [PM-devius-maximus-beab45 — Dubz Up motion showreel](motions/devius-maximus-beab45.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/devius-maximus-beab45) |
| [PM-elliot-garreffa-f334bc — Muse connector tracker promo](motions/elliot-garreffa-f334bc.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/elliot-garreffa-f334bc) |
| [PM-adamdesgns-478d6d — Fitters Bible app promo](motions/adamdesgns-478d6d.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/adamdesgns-478d6d) |
| [PM-andginja-333d32 — Studio website showreel](motions/andginja-333d32.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/andginja-333d32) |
| [PM-l3d1c-0e35a3 — PicTwin AI app ad](motions/l3d1c-0e35a3.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/l3d1c-0e35a3) |
| [PM-wozu-co-242285 — Supasito launch video](motions/wozu-co-242285.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/wozu-co-242285) |
| [PM-tstfully-0aa6b4 — YouTube transcript product ad](motions/tstfully-0aa6b4.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/tstfully-0aa6b4) |
| [PM-bizibeast-10f264 — Bento.surf product video](motions/bizibeast-10f264.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/bizibeast-10f264) |
| [PM-heyiammallik-e72d17 — Portfolio motion reel](motions/heyiammallik-e72d17.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/heyiammallik-e72d17) |
| [PM-quickdesignio-dd93d0 — QuickDesign brand promo](motions/quickdesignio-dd93d0.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/quickdesignio-dd93d0) |
| [PM-slvdev-64c45a — Claude self-promo spot](motions/slvdev-64c45a.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/slvdev-64c45a) |
| [PM-sudo-kiran-4f8b59 — DistilBook product explainer](motions/sudo-kiran-4f8b59.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/sudo-kiran-4f8b59) |
| [PM-xelandre-363f00 — SaaS product launch video](motions/xelandre-363f00.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/xelandre-363f00) |
| [PM-justincooperman-e7bbc4 — Tented image gen product video](motions/justincooperman-e7bbc4.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/justincooperman-e7bbc4) |
| [PM-fractadev-149adc — Voice agent SaaS launch](motions/fractadev-149adc.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/fractadev-149adc) |
| [PM-gautam-mer1-2ae354 — Matra caption app promo](motions/gautam-mer1-2ae354.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/gautam-mer1-2ae354) |
| [PM-miskinho-443898 — Quetzal social app reel](motions/miskinho-443898.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/miskinho-443898) |
| [PM-francoxavier33-d2dfd2 — Parenting app hype video](motions/francoxavier33-d2dfd2.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/francoxavier33-d2dfd2) |
| [PM-kangaroohere-b10f8d — Motion designer showreel](motions/kangaroohere-b10f8d.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/kangaroohere-b10f8d) |
| [PM-kyonax-on-tech-aabc1d — org2html product showreel](motions/kyonax-on-tech-aabc1d.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/kyonax-on-tech-aabc1d) |
| [PM-madebyjmayala-b9204d — Gene Spectra promo](motions/madebyjmayala-b9204d.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/madebyjmayala-b9204d) |
| [PM-antonio-kodheli-490109 — Prompt Motion site promo](motions/antonio-kodheli-490109.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/antonio-kodheli-490109) |
| [PM-oliahmed205-3e31c4 — Photo retouch app promo](motions/oliahmed205-3e31c4.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/oliahmed205-3e31c4) |
| [PM-danilowm-d3720d — Motion designer showreel](motions/danilowm-d3720d.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/danilowm-d3720d) |
| [PM-kmasiff-cc72cb — Email verification tool promo](motions/kmasiff-cc72cb.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/kmasiff-cc72cb) |
| [PM-rammanq-f5a90f — AllInvestView product promo](motions/rammanq-f5a90f.md) | explain/proof/cta | 1:1 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/rammanq-f5a90f) |
| [PM-amol909s-27533e — Commotion app showreel](motions/amol909s-27533e.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/amol909s-27533e) |
| [PM-cansincengiz-me-cf68dd — Lidlezz app promo](motions/cansincengiz-me-cf68dd.md) | explain/proof/cta | 1:1 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/cansincengiz-me-cf68dd) |
| [PM-marouanegazouzi-6071d5 — Crux motion design showreel](motions/marouanegazouzi-6071d5.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/marouanegazouzi-6071d5) |
| [PM-mehul4795-4a7007 — ocrX app launch video](motions/mehul4795-4a7007.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/mehul4795-4a7007) |
| [PM-listudio-820c7b — GenVizu product launch](motions/listudio-820c7b.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/listudio-820c7b) |
| [PM-thilina-a-891c09 — sweetRegret app update reel](motions/thilina-a-891c09.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/thilina-a-891c09) |
| [PM-ceowinkz-7c776b — Amazon wholesale pitch video](motions/ceowinkz-7c776b.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/ceowinkz-7c776b) |
| [PM-ibrahimwasim240-809370 — Personal skills showreel](motions/ibrahimwasim240-809370.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/ibrahimwasim240-809370) |
| [PM-jazzen-chen-4542ae — AgentHud project motion video](motions/jazzen-chen-4542ae.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/jazzen-chen-4542ae) |
| [PM-lester-tyy-f897f7 — CloudJoi search showcase](motions/lester-tyy-f897f7.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/lester-tyy-f897f7) |
| [PM-majorbaguette-fb11d7 — Brieform product presentation](motions/majorbaguette-fb11d7.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/majorbaguette-fb11d7) |
| [PM-ai-baymax-0ef9dd — FigPad product promo](motions/ai-baymax-0ef9dd.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/ai-baymax-0ef9dd) |
| [PM-iammxfschr-d68f90 — Database client launch video](motions/iammxfschr-d68f90.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/iammxfschr-d68f90) |
| [PM-kikelopezdesign-7cc9e8 — Design portfolio video reel](motions/kikelopezdesign-7cc9e8.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/kikelopezdesign-7cc9e8) |
| [PM-charlesmendez-73b6e4 — Datagran ChatGPT ads explainer](motions/charlesmendez-73b6e4.md) | explain/proof/cta | 16:9 | partial / 60% | 6–12 | medium | ui, mask, stagger | [web](https://prompt-motion.com/charlesmendez-73b6e4) |

### Bằng chứng / số liệu (11)

| ID / tên → file | Vai trò | Tỉ lệ ưu tiên | Vùng / diện tích hộp | Giây đề xuất | Nhịp mạnh | Kỹ thuật | Nguồn |
|---|---|---|---|---|---|---|---|
| [PM-jasonzhou1993-8595e0 — Claude motion reel](motions/jasonzhou1993-8595e0.md) | proof/explain/emphasis | 16:9 | partial / 59% | 5–9 | medium | chart, stagger, count-up | [web](https://prompt-motion.com/jasonzhou1993-8595e0) |
| [PM-ismailfahmi-557268 — Drone Emprit showreel](motions/ismailfahmi-557268.md) | proof/explain/emphasis | 16:9 | partial / 59% | 5–9 | medium | chart, stagger, count-up | [web](https://prompt-motion.com/ismailfahmi-557268) |
| [PM-eyishazyer-af035b — Motion designer showreel](motions/eyishazyer-af035b.md) | proof/explain/emphasis | 16:9 | partial / 59% | 5–9 | medium | chart, stagger, count-up | [web](https://prompt-motion.com/eyishazyer-af035b) |
| [PM-triglyceee-bd5b08 — Moroccan political history timeline](motions/triglyceee-bd5b08.md) | proof/explain/emphasis | 16:9 | partial / 59% | 5–9 | medium | chart, stagger, count-up | [web](https://prompt-motion.com/triglyceee-bd5b08) |
| [PM-sudeepsd-1a3485 — Flexprice motion showreel](motions/sudeepsd-1a3485.md) | proof/explain/emphasis | 16:9 | partial / 59% | 5–9 | medium | chart, stagger, count-up | [web](https://prompt-motion.com/sudeepsd-1a3485) |
| [PM-motiondsgnr-9dcfa6 — Bold typographic motion showreel](motions/motiondsgnr-9dcfa6.md) | proof/explain/emphasis | 16:9 | partial / 59% | 5–9 | medium | chart, stagger, count-up | [web](https://prompt-motion.com/motiondsgnr-9dcfa6) |
| [PM-astrodevil-3f2054 — Studio1 intro showreel](motions/astrodevil-3f2054.md) | proof/explain/emphasis | 16:9 | partial / 59% | 5–9 | medium | chart, stagger, count-up | [web](https://prompt-motion.com/astrodevil-3f2054) |
| [PM-3xtihor-0f6911 — Claude motion designer showreel](motions/3xtihor-0f6911.md) | proof/explain/emphasis | 16:9 | partial / 59% | 5–9 | medium | chart, stagger, count-up | [web](https://prompt-motion.com/3xtihor-0f6911) |
| [PM-palashbagchi11-0a4b6b — Backlink audit data promo](motions/palashbagchi11-0a4b6b.md) | proof/explain/emphasis | 16:9 | partial / 59% | 5–9 | medium | chart, stagger, count-up | [web](https://prompt-motion.com/palashbagchi11-0a4b6b) |
| [PM-blushpetal795-0c85c2 — Recruiter self-intro reel](motions/blushpetal795-0c85c2.md) | proof/explain/emphasis | 16:9 | partial / 59% | 5–9 | medium | chart, stagger, count-up | [web](https://prompt-motion.com/blushpetal795-0c85c2) |
| [PM-rneayan-ea6129 — Oscilloscope-style studio motion graphic](motions/rneayan-ea6129.md) | proof/explain/emphasis | 16:9 | partial / 59% | 5–9 | medium | chart, path | [web](https://prompt-motion.com/rneayan-ea6129) |

### Giải thích / quy trình (25)

| ID / tên → file | Vai trò | Tỉ lệ ưu tiên | Vùng / diện tích hộp | Giây đề xuất | Nhịp mạnh | Kỹ thuật | Nguồn |
|---|---|---|---|---|---|---|---|
| [PM-himanshutwtxs-5f4b43 — Motion designer showreel](motions/himanshutwtxs-5f4b43.md) | explain/proof | 16:9 | partial / 67% | 7–12 | low | diagram, path, stagger | [web](https://prompt-motion.com/himanshutwtxs-5f4b43) |
| [PM-ror-fly-9950f1 — Negroni recipe animation](motions/ror-fly-9950f1.md) | explain/proof | 16:9 | partial / 67% | 7–12 | low | diagram, mask | [web](https://prompt-motion.com/ror-fly-9950f1) |
| [PM-emollick-8661a8 — Recursion explained in genres](motions/emollick-8661a8.md) | explain/proof | 16:9 | fullscreen / 100% | 6–12 | low | diagram, recursion, stagger | [web](https://prompt-motion.com/emollick-8661a8) |
| [PM-alex-prompter-1ea044 — Animated business explainer](motions/alex-prompter-1ea044.md) | explain/proof | 16:9 | partial / 67% | 7–12 | low | diagram, path, stagger | [web](https://prompt-motion.com/alex-prompter-1ea044) |
| [PM-linearuncle-5d2bae — Derivative concept explainer](motions/linearuncle-5d2bae.md) | explain/proof | 16:9 | partial / 67% | 7–12 | low | chart, path | [web](https://prompt-motion.com/linearuncle-5d2bae) |
| [PM-kloss-xyz-fe0c31 — History of AI timeline](motions/kloss-xyz-fe0c31.md) | explain/proof | 16:9 | partial / 67% | 7–12 | low | diagram, camera | [web](https://prompt-motion.com/kloss-xyz-fe0c31) |
| [PM-chatgptastra-0d95c7 — Motion principles showreel](motions/chatgptastra-0d95c7.md) | explain/proof | 16:9 | partial / 67% | 7–12 | low | diagram, path, stagger | [web](https://prompt-motion.com/chatgptastra-0d95c7) |
| [PM-0xnfrith-5be616 — Celld job ownership explainer](motions/0xnfrith-5be616.md) | explain/proof | 16:9 | partial / 67% | 7–12 | low | diagram, path | [web](https://prompt-motion.com/0xnfrith-5be616) |
| [PM-math-files-39c9d0 — Mathematics motion showreel](motions/math-files-39c9d0.md) | explain/proof | 16:9 | partial / 67% | 7–12 | low | diagram, path, stagger | [web](https://prompt-motion.com/math-files-39c9d0) |
| [PM-nikolajankovic-ce4ff4 — DeFi Saver stop-motion explainer](motions/nikolajankovic-ce4ff4.md) | explain/proof | 16:9 | partial / 67% | 7–12 | low | diagram, path, stagger | [web](https://prompt-motion.com/nikolajankovic-ce4ff4) |
| [PM-sayan-shanky-f850d8 — AI data centre 3D tour](motions/sayan-shanky-f850d8.md) | explain/proof | 16:9 | partial / 67% | 7–12 | low | 3d, camera, diagram | [web](https://prompt-motion.com/sayan-shanky-f850d8) |
| [PM-yunn260414-60d996 — What is Git explainer](motions/yunn260414-60d996.md) | explain/proof | 16:9 | partial / 67% | 7–12 | low | diagram, path | [web](https://prompt-motion.com/yunn260414-60d996) |
| [PM-sarut0bisasuke-cefa43 — White Russian recipe animation](motions/sarut0bisasuke-cefa43.md) | explain/proof | 16:9 | partial / 67% | 7–12 | low | diagram, mask | [web](https://prompt-motion.com/sarut0bisasuke-cefa43) |
| [PM-tak3sh8-be5012 — Replica symmetry breaking whiteboard](motions/tak3sh8-be5012.md) | explain/proof | 16:9 | partial / 67% | 7–12 | low | diagram, path | [web](https://prompt-motion.com/tak3sh8-be5012) |
| [PM-henkvaness-0e06af — Prompting mistakes video tutorial](motions/henkvaness-0e06af.md) | explain/proof | 16:9 | partial / 67% | 7–12 | low | diagram, path, stagger | [web](https://prompt-motion.com/henkvaness-0e06af) |
| [PM-misbahsy-80eaec — LiteLLM promo reel](motions/misbahsy-80eaec.md) | explain/proof | 16:9 | partial / 67% | 7–12 | low | diagram, path, stagger | [web](https://prompt-motion.com/misbahsy-80eaec) |
| [PM-mdaman010-e7226a — AI data centre 3D film](motions/mdaman010-e7226a.md) | explain/proof | 16:9 | partial / 67% | 7–12 | low | diagram, path, stagger | [web](https://prompt-motion.com/mdaman010-e7226a) |
| [PM-ik-builds-b8bdcf — Paper-style product launch film](motions/ik-builds-b8bdcf.md) | explain/proof | 16:9 | partial / 67% | 7–12 | low | diagram, mask | [web](https://prompt-motion.com/ik-builds-b8bdcf) |
| [PM-buildfastwithai-53234e — Indian civilisation history film](motions/buildfastwithai-53234e.md) | explain/proof | 16:9 | partial / 67% | 7–12 | low | diagram, path, stagger | [web](https://prompt-motion.com/buildfastwithai-53234e) |
| [PM-pluginplay-3d4006 — Pixel art LLM history](motions/pluginplay-3d4006.md) | explain/proof | 16:9 | partial / 67% | 7–12 | low | diagram, path, stagger | [web](https://prompt-motion.com/pluginplay-3d4006) |
| [PM-blueoctopusai-dd17bd — First & 10 yellow line explainer](motions/blueoctopusai-dd17bd.md) | explain/proof | 16:9 | partial / 67% | 7–12 | low | diagram, path | [web](https://prompt-motion.com/blueoctopusai-dd17bd) |
| [PM-teslachartz-c58b32 — Motion designer showreel](motions/teslachartz-c58b32.md) | explain/proof | 16:9 | partial / 67% | 7–12 | low | diagram, path, stagger | [web](https://prompt-motion.com/teslachartz-c58b32) |
| [PM-leadnotifi-e83f94 — Lead Notifi product ad](motions/leadnotifi-e83f94.md) | explain/proof | 16:9 | partial / 67% | 7–12 | low | diagram, path, stagger | [web](https://prompt-motion.com/leadnotifi-e83f94) |
| [PM-rneayan-474bcf — Risograph studio intro](motions/rneayan-474bcf.md) | explain/proof | 16:9 | partial / 67% | 7–12 | low | typography, mask | [web](https://prompt-motion.com/rneayan-474bcf) |
| [PM-parkerrex-1a54fe — Token bucket rate limiter](motions/parkerrex-1a54fe.md) | explain/proof | 16:9 | partial / 67% | 7–12 | low | diagram, chart | [web](https://prompt-motion.com/parkerrex-1a54fe) |

### Chữ / hook / chốt (59)

| ID / tên → file | Vai trò | Tỉ lệ ưu tiên | Vùng / diện tích hộp | Giây đề xuất | Nhịp mạnh | Kỹ thuật | Nguồn |
|---|---|---|---|---|---|---|---|
| [PM-stephanlivera-df17a2 — Claude motion designer showreel](motions/stephanlivera-df17a2.md) | hook/emphasis/closing | 16:9 | fullscreen / 100% | 3–7 | high | typography, mask, stagger | [web](https://prompt-motion.com/stephanlivera-df17a2) |
| [PM-shneural-2abdfa — Bold kinetic type showreel](motions/shneural-2abdfa.md) | hook/emphasis/closing | 16:9 | fullscreen / 100% | 3–7 | high | typography, mask, stagger | [web](https://prompt-motion.com/shneural-2abdfa) |
| [PM-ajith-io-b5626e — Abstract motion design reel](motions/ajith-io-b5626e.md) | hook/emphasis/closing | 16:9 | fullscreen / 100% | 3–7 | high | typography, mask, stagger | [web](https://prompt-motion.com/ajith-io-b5626e) |
| [PM-lexnlin-038035 — Engraving-style Claude ad](motions/lexnlin-038035.md) | hook/emphasis/closing | 16:9 | fullscreen / 100% | 3–7 | high | typography, mask, stagger | [web](https://prompt-motion.com/lexnlin-038035) |
| [PM-majin-appsheet-2d3c1a — Shin Majin-shiki promo](motions/majin-appsheet-2d3c1a.md) | hook/emphasis/closing | 16:9 | fullscreen / 100% | 3–7 | high | typography, mask, stagger | [web](https://prompt-motion.com/majin-appsheet-2d3c1a) |
| [PM-davidmarcus-a28a60 — Lightspark social promo video](motions/davidmarcus-a28a60.md) | hook/emphasis/closing | 16:9 | fullscreen / 100% | 3–7 | high | typography, mask, stagger | [web](https://prompt-motion.com/davidmarcus-a28a60) |
| [PM-techhalla-90b8ec — TechHalla kinetic type bumper](motions/techhalla-90b8ec.md) | hook/emphasis/closing | 1:1 | fullscreen / 100% | 3–7 | high | typography, mask, stagger | [web](https://prompt-motion.com/techhalla-90b8ec) |
| [PM-ultimaxbt-bbebf5 — Orange dot motion system](motions/ultimaxbt-bbebf5.md) | hook/emphasis/closing | 16:9 | fullscreen / 100% | 3–7 | high | shape, path | [web](https://prompt-motion.com/ultimaxbt-bbebf5) |
| [PM-jacksonfall-54b2ac — Branding agency showreel](motions/jacksonfall-54b2ac.md) | hook/emphasis/closing | 16:9 | fullscreen / 100% | 3–7 | high | typography, mask, stagger | [web](https://prompt-motion.com/jacksonfall-54b2ac) |
| [PM-tequilafunks-97f6c9 — Claude motion design reel](motions/tequilafunks-97f6c9.md) | hook/emphasis/closing | 16:9 | fullscreen / 100% | 3–7 | high | typography, mask, stagger | [web](https://prompt-motion.com/tequilafunks-97f6c9) |
| [PM-sudo-kiran-49176d — Claude motion design showreel](motions/sudo-kiran-49176d.md) | hook/emphasis/closing | 16:9 | fullscreen / 100% | 3–7 | high | typography, mask, stagger | [web](https://prompt-motion.com/sudo-kiran-49176d) |
| [PM-lukasersil-0ed38e — Motion techniques showreel](motions/lukasersil-0ed38e.md) | hook/emphasis/closing | 16:9 | fullscreen / 100% | 3–7 | high | typography, mask, stagger | [web](https://prompt-motion.com/lukasersil-0ed38e) |
| [PM-gizakdag-cf4ae6 — Overthinking motion study](motions/gizakdag-cf4ae6.md) | hook/emphasis/closing | 16:9 | fullscreen / 100% | 3–7 | high | typography, stagger | [web](https://prompt-motion.com/gizakdag-cf4ae6) |
| [PM-ayushunleashed-ece3e3 — Claude motion design showreel](motions/ayushunleashed-ece3e3.md) | hook/emphasis/closing | 16:9 | fullscreen / 100% | 3–7 | high | typography, mask, stagger | [web](https://prompt-motion.com/ayushunleashed-ece3e3) |
| [PM-kloss-xyz-15182a — Chaotic Claude POV video](motions/kloss-xyz-15182a.md) | hook/emphasis/closing | 9:16 | fullscreen / 100% | 3–7 | high | typography, mask, stagger | [web](https://prompt-motion.com/kloss-xyz-15182a) |
| [PM-hanifproduktif-54bdee — Motion designer showreel](motions/hanifproduktif-54bdee.md) | hook/emphasis/closing | 16:9 | fullscreen / 100% | 3–7 | high | typography, mask, stagger | [web](https://prompt-motion.com/hanifproduktif-54bdee) |
| [PM-roundtablespace-d3a1be — Easing and morphing showreel](motions/roundtablespace-d3a1be.md) | hook/emphasis/closing | 16:9 | fullscreen / 100% | 3–7 | high | typography, mask, stagger | [web](https://prompt-motion.com/roundtablespace-d3a1be) |
| [PM-1littlecoder-9fef89 — Claude self-intro motion graphic](motions/1littlecoder-9fef89.md) | hook/emphasis/closing | 16:9 | fullscreen / 100% | 3–7 | high | typography, mask, stagger | [web](https://prompt-motion.com/1littlecoder-9fef89) |
| [PM-pankajkumar-dev-0bee87 — Poster breaking its frame](motions/pankajkumar-dev-0bee87.md) | hook/emphasis/closing | 16:9 | fullscreen / 100% | 3–7 | high | mask, typography | [web](https://prompt-motion.com/pankajkumar-dev-0bee87) |
| [PM-codestackr-c071bf — Claude motion reel](motions/codestackr-c071bf.md) | hook/emphasis/closing | 16:9 | fullscreen / 100% | 3–7 | high | typography, mask, stagger | [web](https://prompt-motion.com/codestackr-c071bf) |
| [PM-tankazunori0914-0fc886 — What day is it](motions/tankazunori0914-0fc886.md) | hook/emphasis/closing | 16:9 | fullscreen / 100% | 3–7 | high | typography, mask, stagger | [web](https://prompt-motion.com/tankazunori0914-0fc886) |
| [PM-maxalexweber-67688b — ODATANO Cardano hype edit](motions/maxalexweber-67688b.md) | hook/emphasis/closing | 16:9 | fullscreen / 100% | 3–7 | high | typography, mask, stagger | [web](https://prompt-motion.com/maxalexweber-67688b) |
| [PM-samuel-spitz-974923 — Motion design showreel](motions/samuel-spitz-974923.md) | hook/emphasis/closing | 16:9 | fullscreen / 100% | 3–7 | high | typography, mask, stagger | [web](https://prompt-motion.com/samuel-spitz-974923) |
| [PM-micheleharmonic-77628e — GravityDEX anime hype edit](motions/micheleharmonic-77628e.md) | hook/emphasis/closing | 16:9 | fullscreen / 100% | 3–7 | high | typography, mask, stagger | [web](https://prompt-motion.com/micheleharmonic-77628e) |
| [PM-zheke-38deff — Kinetic type showreel](motions/zheke-38deff.md) | hook/emphasis/closing | 16:9 | fullscreen / 100% | 3–7 | high | typography, mask, stagger | [web](https://prompt-motion.com/zheke-38deff) |
| [PM-gdgtify-287ddf — Speech built as architecture](motions/gdgtify-287ddf.md) | hook/emphasis/closing | 1:1 | fullscreen / 100% | 3–7 | high | typography, shape | [web](https://prompt-motion.com/gdgtify-287ddf) |
| [PM-influencer-seo-ce8c33 — fal motion design showreel](motions/influencer-seo-ce8c33.md) | hook/emphasis/closing | 16:9 | fullscreen / 100% | 3–7 | high | typography, mask, stagger | [web](https://prompt-motion.com/influencer-seo-ce8c33) |
| [PM-ndhabarde11-f155b4 — Motion designer portrait showreel](motions/ndhabarde11-f155b4.md) | hook/emphasis/closing | 9:16 | fullscreen / 100% | 3–7 | high | typography, mask, stagger | [web](https://prompt-motion.com/ndhabarde11-f155b4) |
| [PM-topi-003-9ca6b5 — Kinetic type motion showreel](motions/topi-003-9ca6b5.md) | hook/emphasis/closing | 16:9 | fullscreen / 100% | 3–7 | high | typography, mask, stagger | [web](https://prompt-motion.com/topi-003-9ca6b5) |
| [PM-rendesr-86be44 — Claude motion design showreel](motions/rendesr-86be44.md) | hook/emphasis/closing | 16:9 | fullscreen / 100% | 3–7 | high | typography, mask, stagger | [web](https://prompt-motion.com/rendesr-86be44) |
| [PM-madhav-xo-f97f20 — Personal research intro reel](motions/madhav-xo-f97f20.md) | hook/emphasis/closing | 16:9 | fullscreen / 100% | 3–7 | high | typography, mask, stagger | [web](https://prompt-motion.com/madhav-xo-f97f20) |
| [PM-web3wesley-7bb108 — Type, form, space showreel](motions/web3wesley-7bb108.md) | hook/emphasis/closing | 16:9 | fullscreen / 100% | 3–7 | high | typography, mask, stagger | [web](https://prompt-motion.com/web3wesley-7bb108) |
| [PM-reflex-cloud-72ffe5 — Reflex brand motion reel](motions/reflex-cloud-72ffe5.md) | hook/emphasis/closing | 16:9 | fullscreen / 100% | 3–7 | high | typography, mask, stagger | [web](https://prompt-motion.com/reflex-cloud-72ffe5) |
| [PM-sudiyasa-f48ac9 — EyezOn 100 users thank-you](motions/sudiyasa-f48ac9.md) | hook/emphasis/closing | 16:9 | fullscreen / 100% | 3–7 | high | typography, mask, stagger | [web](https://prompt-motion.com/sudiyasa-f48ac9) |
| [PM-m1n9-k7-ff9ab9 — Kinetic type and particle showreel](motions/m1n9-k7-ff9ab9.md) | hook/emphasis/closing | 16:9 | fullscreen / 100% | 3–7 | high | typography, mask, stagger | [web](https://prompt-motion.com/m1n9-k7-ff9ab9) |
| [PM-levabashidze-2d713a — Swiss-style motion showreel](motions/levabashidze-2d713a.md) | hook/emphasis/closing | 16:9 | fullscreen / 100% | 3–7 | high | typography, mask, stagger | [web](https://prompt-motion.com/levabashidze-2d713a) |
| [PM-zaqailo-212ad3 — Motion designer showreel](motions/zaqailo-212ad3.md) | hook/emphasis/closing | 16:9 | fullscreen / 100% | 3–7 | high | typography, mask, stagger | [web](https://prompt-motion.com/zaqailo-212ad3) |
| [PM-crazyalphaaa-bc7e75 — Claude motion designer showreel](motions/crazyalphaaa-bc7e75.md) | hook/emphasis/closing | 16:9 | fullscreen / 100% | 3–7 | high | typography, mask, stagger | [web](https://prompt-motion.com/crazyalphaaa-bc7e75) |
| [PM-fionntobin-97b7af — Blue editorial motion showreel](motions/fionntobin-97b7af.md) | hook/emphasis/closing | 16:9 | fullscreen / 100% | 3–7 | high | typography, mask, stagger | [web](https://prompt-motion.com/fionntobin-97b7af) |
| [PM-itsuki-dev-10942d — Kinetic type showreel](motions/itsuki-dev-10942d.md) | hook/emphasis/closing | 16:9 | fullscreen / 100% | 3–7 | high | typography, mask, stagger | [web](https://prompt-motion.com/itsuki-dev-10942d) |
| [PM-tolgayhickiran-e90799 — Motion design principles reel](motions/tolgayhickiran-e90799.md) | hook/emphasis/closing | 16:9 | fullscreen / 100% | 3–7 | high | typography, mask, stagger | [web](https://prompt-motion.com/tolgayhickiran-e90799) |
| [PM-robvjourney-ce3e1a — Nohandslabs brand promo](motions/robvjourney-ce3e1a.md) | hook/emphasis/closing | 16:9 | fullscreen / 100% | 3–7 | high | typography, mask, stagger | [web](https://prompt-motion.com/robvjourney-ce3e1a) |
| [PM-vanshwtfff-db0466 — Motion designer showreel](motions/vanshwtfff-db0466.md) | hook/emphasis/closing | 16:9 | fullscreen / 100% | 3–7 | high | typography, mask, stagger | [web](https://prompt-motion.com/vanshwtfff-db0466) |
| [PM-ghinaiya-nirmal-5d8fec — Claude motion design reel](motions/ghinaiya-nirmal-5d8fec.md) | hook/emphasis/closing | 16:9 | fullscreen / 100% | 3–7 | high | typography, mask, stagger | [web](https://prompt-motion.com/ghinaiya-nirmal-5d8fec) |
| [PM-johnsavage-ai-b091c0 — Code-only motion design reel](motions/johnsavage-ai-b091c0.md) | hook/emphasis/closing | 16:9 | fullscreen / 100% | 3–7 | high | typography, mask, stagger | [web](https://prompt-motion.com/johnsavage-ai-b091c0) |
| [PM-leonkohli-6dc01b — Geometric motion designer showreel](motions/leonkohli-6dc01b.md) | hook/emphasis/closing | 16:9 | fullscreen / 100% | 3–7 | high | typography, mask, stagger | [web](https://prompt-motion.com/leonkohli-6dc01b) |
| [PM-safarkhanshuvo-ffd52d — Motion design showreel](motions/safarkhanshuvo-ffd52d.md) | hook/emphasis/closing | 16:9 | fullscreen / 100% | 3–7 | high | typography, mask, stagger | [web](https://prompt-motion.com/safarkhanshuvo-ffd52d) |
| [PM-sahildesigner23-ee3155 — 3D motion design showreel](motions/sahildesigner23-ee3155.md) | hook/emphasis/closing | 16:9 | fullscreen / 100% | 3–7 | high | typography, mask, stagger | [web](https://prompt-motion.com/sahildesigner23-ee3155) |
| [PM-grace-sunnyy-29bc61 — Keyframe motion design reel](motions/grace-sunnyy-29bc61.md) | hook/emphasis/closing | 16:9 | fullscreen / 100% | 3–7 | high | typography, mask, stagger | [web](https://prompt-motion.com/grace-sunnyy-29bc61) |
| [PM-apoorvjain25-d24184 — Photon journey from the Sun](motions/apoorvjain25-d24184.md) | hook/emphasis/closing | 16:9 | fullscreen / 100% | 3–7 | high | particles, path | [web](https://prompt-motion.com/apoorvjain25-d24184) |
| [PM-aichrislee-a6cb42 — Motion designer showreel](motions/aichrislee-a6cb42.md) | hook/emphasis/closing | 16:9 | fullscreen / 100% | 3–7 | high | typography, mask, stagger | [web](https://prompt-motion.com/aichrislee-a6cb42) |
| [PM-amitsingha89-150378 — Handwoven textiles brand explainer](motions/amitsingha89-150378.md) | hook/emphasis/closing | 16:9 | fullscreen / 100% | 3–7 | high | typography, mask, stagger | [web](https://prompt-motion.com/amitsingha89-150378) |
| [PM-nolkeeg-bf062e — What happens in one second](motions/nolkeeg-bf062e.md) | hook/emphasis/closing | 16:9 | fullscreen / 100% | 3–7 | high | typography, chart | [web](https://prompt-motion.com/nolkeeg-bf062e) |
| [PM-souravbhar871-61f424 — Kinetic type self-portrait](motions/souravbhar871-61f424.md) | hook/emphasis/closing | 16:9 | fullscreen / 100% | 3–7 | high | typography, mask, stagger | [web](https://prompt-motion.com/souravbhar871-61f424) |
| [PM-spearwtf-3c1fd1 — Chain.wtf pitch video](motions/spearwtf-3c1fd1.md) | hook/emphasis/closing | 16:9 | fullscreen / 100% | 3–7 | high | typography, mask, stagger | [web](https://prompt-motion.com/spearwtf-3c1fd1) |
| [PM-samaote-5e2fc2 — Synced lyrics motion video](motions/samaote-5e2fc2.md) | hook/emphasis/closing | 16:9 | fullscreen / 100% | 3–7 | high | typography, highlight | [web](https://prompt-motion.com/samaote-5e2fc2) |
| [PM-shinskinakamoto-20190b — Kinetic shapes showreel](motions/shinskinakamoto-20190b.md) | hook/emphasis/closing | 16:9 | fullscreen / 100% | 3–7 | high | typography, mask, stagger | [web](https://prompt-motion.com/shinskinakamoto-20190b) |
| [PM-gonzalomacagno-2de1a9 — Festival lineup promo reel](motions/gonzalomacagno-2de1a9.md) | hook/emphasis/closing | 16:9 | fullscreen / 100% | 3–7 | high | typography, stagger | [web](https://prompt-motion.com/gonzalomacagno-2de1a9) |
| [PM-template-showreel — The showreel prompt](motions/template-showreel.md) | hook/emphasis/closing | 16:9 | fullscreen / 100% | 8–15 | high | typography, morph, beat-grid | [web](https://prompt-motion.com/templates/showreel) |

### Hình học / chuyển ý (3)

| ID / tên → file | Vai trò | Tỉ lệ ưu tiên | Vùng / diện tích hộp | Giây đề xuất | Nhịp mạnh | Kỹ thuật | Nguồn |
|---|---|---|---|---|---|---|---|
| [PM-tdinh-me-815acb — TypingMind logo reveal](motions/tdinh-me-815acb.md) | hook/transition/emphasis | 16:9 | fullscreen / 100% | 3–6 | medium | shape, mask | [web](https://prompt-motion.com/tdinh-me-815acb) |
| [PM-monokern-ade5b6 — Psychedelic hypnotic eye showreel](motions/monokern-ade5b6.md) | hook/transition/emphasis | 16:9 | fullscreen / 100% | 3–6 | medium | shape, morph, stagger | [web](https://prompt-motion.com/monokern-ade5b6) |
| [PM-kantamk-61f410 — Ball escaping twelve rings](motions/kantamk-61f410.md) | hook/transition/emphasis | 16:9 | fullscreen / 100% | 3–6 | medium | shape, path | [web](https://prompt-motion.com/kantamk-61f410) |

### Hạt / năng lượng (8)

| ID / tên → file | Vai trò | Tỉ lệ ưu tiên | Vùng / diện tích hộp | Giây đề xuất | Nhịp mạnh | Kỹ thuật | Nguồn |
|---|---|---|---|---|---|---|---|
| [PM-ajith-io-4c248f — Distilbook promo showreel](motions/ajith-io-4c248f.md) | hook/ambient/transition | 16:9 | fullscreen / 100% | 4–8 | medium | particles, depth, stagger | [web](https://prompt-motion.com/ajith-io-4c248f) |
| [PM-ajith-io-ea7f2d — Distilbook motion showreel](motions/ajith-io-ea7f2d.md) | hook/ambient/transition | 16:9 | fullscreen / 100% | 4–8 | medium | particles, depth, stagger | [web](https://prompt-motion.com/ajith-io-ea7f2d) |
| [PM-blue-clarity-ef56d0 — Particle sphere motion reel](motions/blue-clarity-ef56d0.md) | hook/ambient/transition | 16:9 | fullscreen / 100% | 3–7 | medium | particles, depth, stagger | [web](https://prompt-motion.com/blue-clarity-ef56d0) |
| [PM-raphaelaubryy-4b137e — Motion designer résumé reel](motions/raphaelaubryy-4b137e.md) | hook/ambient/transition | 16:9 | fullscreen / 100% | 4–8 | medium | particles, depth, stagger | [web](https://prompt-motion.com/raphaelaubryy-4b137e) |
| [PM-hbcoop-de365c — Full Stop figure sequence](motions/hbcoop-de365c.md) | hook/ambient/transition | 16:9 | fullscreen / 100% | 4–8 | medium | particles, depth, stagger | [web](https://prompt-motion.com/hbcoop-de365c) |
| [PM-manuelogomigo-f33ca9 — Flowdrive motion showreel](motions/manuelogomigo-f33ca9.md) | hook/ambient/transition | 16:9 | fullscreen / 100% | 4–8 | medium | particles, depth, stagger | [web](https://prompt-motion.com/manuelogomigo-f33ca9) |
| [PM-kamstudiolabs-447565 — Collision-driven music machine](motions/kamstudiolabs-447565.md) | hook/ambient/transition | 16:9 | fullscreen / 100% | 4–8 | medium | path, shape | [web](https://prompt-motion.com/kamstudiolabs-447565) |
| [PM-deebeeeff-50fcd0 — Recipe brand 20th anniversary](motions/deebeeeff-50fcd0.md) | hook/ambient/transition | 16:9 | fullscreen / 100% | 4–8 | medium | particles, depth, stagger | [web](https://prompt-motion.com/deebeeeff-50fcd0) |

### Nhân vật / kể chuyện (20)

| ID / tên → file | Vai trò | Tỉ lệ ưu tiên | Vùng / diện tích hộp | Giây đề xuất | Nhịp mạnh | Kỹ thuật | Nguồn |
|---|---|---|---|---|---|---|---|
| [PM-axtonliu-0b861d — Pelican riding a bicycle](motions/axtonliu-0b861d.md) | hook/explain/closing | 16:9 | fullscreen / 100% | 6–12 | medium | character, pose, staging | [web](https://prompt-motion.com/axtonliu-0b861d) |
| [PM-mandelduck-95fd08 — Starry Night cat-spotting game](motions/mandelduck-95fd08.md) | hook/explain/closing | 16:9 | fullscreen / 100% | 6–12 | medium | character, pose, staging, 3d, camera | [web](https://prompt-motion.com/mandelduck-95fd08) |
| [PM-jake11moran-a269c4 — Animated agent session story](motions/jake11moran-a269c4.md) | hook/explain/closing | 16:9 | fullscreen / 100% | 6–12 | medium | character, pose, staging | [web](https://prompt-motion.com/jake11moran-a269c4) |
| [PM-hoyoyoda-3a5c08 — Chuseok pixel night scene](motions/hoyoyoda-3a5c08.md) | hook/explain/closing | 16:9 | fullscreen / 100% | 6–12 | medium | character, pose, staging | [web](https://prompt-motion.com/hoyoyoda-3a5c08) |
| [PM-topi-003-b0e12c — Anime maid dance showreel](motions/topi-003-b0e12c.md) | hook/explain/closing | 16:9 | fullscreen / 100% | 6–12 | medium | character, pose, staging | [web](https://prompt-motion.com/topi-003-b0e12c) |
| [PM-0xevinho-3777d8 — Pixel wizard crypto animation](motions/0xevinho-3777d8.md) | hook/explain/closing | 16:9 | fullscreen / 100% | 6–12 | medium | character, pose, staging | [web](https://prompt-motion.com/0xevinho-3777d8) |
| [PM-chrisjdimarco-f068db — Fiery samurai kata](motions/chrisjdimarco-f068db.md) | hook/explain/closing | 16:9 | fullscreen / 100% | 6–12 | medium | character, pose, staging | [web](https://prompt-motion.com/chrisjdimarco-f068db) |
| [PM-ryzoft-4f85bd — Animated space cartoon episode](motions/ryzoft-4f85bd.md) | hook/explain/closing | 16:9 | fullscreen / 100% | 6–12 | medium | character, pose, staging, 3d, camera | [web](https://prompt-motion.com/ryzoft-4f85bd) |
| [PM-kamstudiolabs-c9bb28 — Animated short about a bug](motions/kamstudiolabs-c9bb28.md) | hook/explain/closing | 16:9 | fullscreen / 100% | 6–12 | medium | character, pose, staging | [web](https://prompt-motion.com/kamstudiolabs-c9bb28) |
| [PM-allforbigfire-86ff3c — Anime robot combining sequence](motions/allforbigfire-86ff3c.md) | hook/explain/closing | 16:9 | fullscreen / 100% | 6–12 | medium | character, pose, staging | [web](https://prompt-motion.com/allforbigfire-86ff3c) |
| [PM-davidshulmanfl-371638 — Clay-style music video](motions/davidshulmanfl-371638.md) | hook/explain/closing | 16:9 | fullscreen / 100% | 6–12 | medium | character, pose, staging | [web](https://prompt-motion.com/davidshulmanfl-371638) |
| [PM-faroukzy-9ff23e — The Last Light animated short](motions/faroukzy-9ff23e.md) | hook/explain/closing | 16:9 | fullscreen / 100% | 6–12 | medium | character, pose, staging | [web](https://prompt-motion.com/faroukzy-9ff23e) |
| [PM-henkpoley-3d3407 — Deliberately terrible motion showreel](motions/henkpoley-3d3407.md) | hook/explain/closing | 16:9 | fullscreen / 100% | 6–12 | medium | character, pose, staging | [web](https://prompt-motion.com/henkpoley-3d3407) |
| [PM-loicrambo-ad6830 — Cycle of life animation](motions/loicrambo-ad6830.md) | hook/explain/closing | 16:9 | fullscreen / 100% | 6–12 | medium | character, pose, staging | [web](https://prompt-motion.com/loicrambo-ad6830) |
| [PM-aisongman-71ffac — Pixel art card battle game](motions/aisongman-71ffac.md) | hook/explain/closing | 16:9 | fullscreen / 100% | 6–12 | medium | character, pose, staging | [web](https://prompt-motion.com/aisongman-71ffac) |
| [PM-abderrahmen-g-9e8ed0 — Sketchbook animals come alive](motions/abderrahmen-g-9e8ed0.md) | hook/explain/closing | 16:9 | fullscreen / 100% | 6–12 | medium | character, pose, staging | [web](https://prompt-motion.com/abderrahmen-g-9e8ed0) |
| [PM-x4b47x-9cc84f — Shadow theatre home story](motions/x4b47x-9cc84f.md) | hook/explain/closing | 9:16 | fullscreen / 100% | 6–12 | medium | character, pose, staging | [web](https://prompt-motion.com/x4b47x-9cc84f) |
| [PM-anas0ra-e57aea — Shop chatbot mascot promo](motions/anas0ra-e57aea.md) | hook/explain/closing | 16:9 | fullscreen / 100% | 6–12 | medium | character, pose, staging | [web](https://prompt-motion.com/anas0ra-e57aea) |
| [PM-anilraok-eff262 — Scrabble tile character story](motions/anilraok-eff262.md) | hook/explain/closing | 16:9 | fullscreen / 100% | 6–12 | medium | character, 3d, camera | [web](https://prompt-motion.com/anilraok-eff262) |
| [PM-kamstudiolabs-0b0824 — Lighthouse keeper silent short](motions/kamstudiolabs-0b0824.md) | hook/explain/closing | 16:9 | fullscreen / 100% | 6–12 | medium | character, pose, staging | [web](https://prompt-motion.com/kamstudiolabs-0b0824) |

### Ảnh / chứng cứ (2)

| ID / tên → file | Vai trò | Tỉ lệ ưu tiên | Vùng / diện tích hộp | Giây đề xuất | Nhịp mạnh | Kỹ thuật | Nguồn |
|---|---|---|---|---|---|---|---|
| [PM-sab8a-364a5a — Talking-head clip edit](motions/sab8a-364a5a.md) | hook/proof/explain | 16:9 | partial / 64% | 5–9 | low | image, mask, parallax | [web](https://prompt-motion.com/sab8a-364a5a) |
| [PM-gigabit-million-16b3a0 — Steam new releases news recap](motions/gigabit-million-16b3a0.md) | explain/proof | 16:9 | partial / 59% | 8–14 | medium | cards, carousel, mask, stagger | [web](https://prompt-motion.com/gigabit-million-16b3a0) |

### Mã / công cụ (1)

| ID / tên → file | Vai trò | Tỉ lệ ưu tiên | Vùng / diện tích hộp | Giây đề xuất | Nhịp mạnh | Kỹ thuật | Nguồn |
|---|---|---|---|---|---|---|---|
| [PM-rames-jusso-589f80 — UK dubstep track with ASCII visuals](motions/rames-jusso-589f80.md) | explain/proof | 16:9 | partial / 67% | 6–10 | low | code, typography | [web](https://prompt-motion.com/rames-jusso-589f80) |

### Không gian / camera (6)

| ID / tên → file | Vai trò | Tỉ lệ ưu tiên | Vùng / diện tích hộp | Giây đề xuất | Nhịp mạnh | Kỹ thuật | Nguồn |
|---|---|---|---|---|---|---|---|
| [PM-itsolelehmann-e47532 — Four seasons train window](motions/itsolelehmann-e47532.md) | ambient/hook/transition | 16:9 | fullscreen / 100% | 6–12 | low | image, mask | [web](https://prompt-motion.com/itsolelehmann-e47532) |
| [PM-nft-chen-5f8bb0 — Porco Rosso sunset dogfight](motions/nft-chen-5f8bb0.md) | ambient/hook/transition | 16:9 | fullscreen / 100% | 6–12 | low | staging, camera, depth, 3d | [web](https://prompt-motion.com/nft-chen-5f8bb0) |
| [PM-gorden-sun-041f56 — Beat-synced bouncing 3D ball](motions/gorden-sun-041f56.md) | ambient/hook/transition | 16:9 | fullscreen / 100% | 6–12 | low | 3d, shape, camera | [web](https://prompt-motion.com/gorden-sun-041f56) |
| [PM-demitiyageekzen-7770ad — Tengwang Pavilion moonlit river](motions/demitiyageekzen-7770ad.md) | ambient/hook/transition | 16:9 | fullscreen / 100% | 6–12 | low | staging, camera, depth | [web](https://prompt-motion.com/demitiyageekzen-7770ad) |
| [PM-rebutonepress-810f78 — Black hole time story](motions/rebutonepress-810f78.md) | ambient/hook/transition | 16:9 | fullscreen / 100% | 6–12 | low | staging, camera, depth | [web](https://prompt-motion.com/rebutonepress-810f78) |
| [PM-template-realtime — The 3D template](motions/template-realtime.md) | hook/explain/closing | 16:9 | fullscreen / 100% | 12–20 | medium | 3d, camera, lighting | [web](https://prompt-motion.com/templates/realtime) |

## Độ phủ và giới hạn chứng cứ

235/240 entry có public prompt được đọc toàn bộ; 5 gallery entry giới thiệu skill thay cho prompt. Raw gallery giữ 233/238 cờ prompt, 238 preview URL; template detail có thêm 2 brief. No raw prompt/code/media archive. Source facts, brief specifications và Sol recommendations được tách trong từng file và JSON.

Sitemap có **260 URL = 238 gallery + 2 template chi tiết + 20 trang khác**, không còn URL chưa phân loại. [coverage.json](source/coverage.json) giữ danh sách đầy đủ và lý do phân loại, gồm trang chỉ mục, bộ lọc và blog. Tất cả 240 entry có link nguồn và provenance tới metadata/notes. Chưa có quyền bulk redistribution, nên prompt gốc chỉ được đọc để diễn giải; tác giả vẫn giữ quyền với prompt/video của họ.
