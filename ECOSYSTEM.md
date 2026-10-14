# ECOSYSTEM — Agent Video Studio trong hệ thống ACD

## 🤝 ACD Ecosystem Integration
- **Role in ACD:** Studio thuộc Nhóm 2 (Production Studio) — xưởng video và motion: composition HTML/CSS/GSAP dựng ra MP4 qua HyperFrames, dựng và dọn footage, lồng tiếng qua trạm giọng. Repo đứng độc lập, cài khi cần dựng video. `agent-skill-studio` là xưởng nền cấp chuẩn `SKILL.md` portable, công cụ kiểm (`validate`/`audit`/`package`) và đóng gói skill; repo này tự giữ nghiệp vụ của mình, không nhờ xưởng nền viết thay.
- **Upstream Controllers:** Repo marketing (Ads, Shorts, Reels) và `agent-academy-team` (video e-learning) ở mức Cốt lõi, `agent-customer-team` (clip hướng dẫn) ở mức Thường xuyên. Trong dây chuyền media: `agent-voice-studio` cấp giọng đọc kèm mốc thời gian, `agent-design-studio` cấp tài sản và phong cách, `agent-slide-studio` cấp khung hình slide.
- **Downstream Consumers:** Các Team nhận MP4 hoàn chỉnh; không có Studio nào nhận tiếp kết quả của repo này trong dây chuyền hiện tại.
- **Recommended Bundles:** Bundle A (Content & Growth Machine, video Shorts/Reels) cùng `agent-voice-studio` và `agent-writing-studio`. Không thuộc Bundle E.
- **Handoff Artifacts:** Đầu vào là `production-brief.md` do Team giao hoặc thông số JSON (`schema_version: 1`) cho lệnh `render`, theo hợp đồng mã thoát cộng dòng JSON cuối ở stdout. Đầu ra là MP4 kèm biên nhận nghiệm thu.
