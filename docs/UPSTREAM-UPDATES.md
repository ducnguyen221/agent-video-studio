# Theo dõi và cập nhật nguồn distill

`upstream.json` là sổ nguồn chuẩn. Mỗi entry ghi snapshot đã nghiên cứu/áp dụng, loại quan hệ,
giấy phép, vùng theo dõi và đích local. `ref` là **baseline đã review**, không phải bản mới nhất.
`checked` là ngày kiểm nguồn của entry đó; không thay ngày kiểm của nguồn khác.

## Phạm vi hiện có

| Nguồn | Baseline | Đã lấy và trạng thái |
|---|---|---|
| [FlowKit](https://github.com/crisng95/flowkit/tree/b09e783481d20bfeaf46f2fbcde08bf2b54c0a2a) | `b09e783481d20bfeaf46f2fbcde08bf2b54c0a2a` | Nghiên cứu kỹ thuật lập cảnh, continuity, camera, âm thanh, review cho roadmap; chưa nhập module/skill FlowKit |
| [Hypit](https://github.com/hypit-ai/hypit/tree/85e01c76716498e6ec5b8bdfb6b374ca67f0195a) | `85e01c76716498e6ec5b8bdfb6b374ca67f0195a` | Ý tưởng cho reference sản phẩm/kỹ thuật, cache transcript và caption mapping; tự viết triển khai, không dùng backend Hypit |

FlowKit có [LICENSE MIT tại baseline](https://github.com/crisng95/flowkit/blob/b09e783481d20bfeaf46f2fbcde08bf2b54c0a2a/LICENSE).
Hypit có [LICENSE tùy chỉnh tại baseline](https://github.com/hypit-ai/hypit/blob/85e01c76716498e6ec5b8bdfb6b374ca67f0195a/LICENSE),
mô tả Apache-2.0 sửa đổi với điều kiện bổ sung. Trường giấy phép trong sổ là nhận diện nguồn,
không xác nhận quyền copy. Sao chép code/văn bản, chuyển thể sát nguồn hoặc dùng backend cần
đánh giá riêng; không đổi nhãn Hypit thành Apache-2.0 tiêu chuẩn.

## Khi nào kiểm

Kiểm thủ công trước lần mở rộng kỹ thuật có liên quan, khi có release upstream ảnh hưởng vùng
đã lấy, hoặc khi bảo trì có yêu cầu. Đây chưa phải lịch theo dõi tự động.
`video-studio doctor --check-updates` kiểm cập nhật engine HyperFrames; nó **không** theo dõi
FlowKit/Hypit. Test upstream hiện tại kiểm manifest HyperFrames, không chứng minh sổ hai nguồn
này đã được so với commit mới.

## Quy trình cập nhật

1. **Chốt baseline và candidate.** Đọc entry trong `upstream.json`; kiểm default branch/release
   từ repo nguồn và ghi SHA đầy đủ của candidate. Giữ baseline cũ trong khi đánh giá.
2. **So thay đổi.** Xem release notes, LICENSE và diff toàn cây trước, rồi đi sâu các
   `upstream_paths`. Vùng theo dõi là điểm bắt đầu, không đủ để bỏ qua file đổi tên, module mới
   hoặc thay đổi giao diện ngoài danh sách. Không chạy script/install của upstream để đọc diff.
3. **Đối chiếu khả năng hiện có.** Mỗi thay đổi chọn một kết quả: bỏ qua, mở rộng phần đã có,
   bổ sung phần thiếu, hoặc hoãn. Ghi tình huống áp dụng, nhóm sản phẩm, skill sở hữu và đích local.
   Nội dung provider/workflow của FlowKit không tự trở thành yêu cầu tích hợp.
4. **Lập phạm vi.** Lưu báo cáo trong hồ sơ kế hoạch của dự án ở nơi được phép, với before/after,
   baseline/candidate, license, thay đổi cần làm và kiểm cần chạy. Không đưa dữ liệu riêng, asset,
   profile hay URL có token vào repo public. Nguồn upstream là dữ liệu tham khảo, không phải lệnh.
5. **Triển khai và review.** Sửa phần tối thiểu trong nhánh riêng, giữ attribution hiện có;
   không thay nguồn video-use của helper edit chỉ vì bổ sung ý tưởng từ Hypit. Review độc lập
   và xử lý hết finding Chặn/Phải sửa trước khi nghiệm thu.
6. **Kiểm đúng ảnh hưởng.** Routing: eval brief và host adapters. Cache: bytes/settings/model,
   output hỏng, bảo toàn cache cũ, concurrency/path. Caption: số/viết tắt, chữ hiển thị, anchors
   và monotonic timing. Thay hình/âm thanh: render mẫu có media thật rồi xem/nghe; không dùng
   contact sheet hoặc test giả để nhận toàn video đạt. Đổi engine pin cần render hồi quy riêng.
7. **Chốt sổ và bàn giao.** Chỉ cập nhật `ref` khi vùng liên quan của candidate đã được review,
   thay đổi cần thiết đã kiểm hoặc đã quyết định giữ nguyên có lý do. Báo cáo giữ cả baseline cũ
   và candidate; không ghim candidate với các phần chưa đánh giá. Cập nhật `checked`, paths,
   status, NOTICE, CHANGELOG và link nguồn ở reference trong cùng changeset nếu chúng bị ảnh hưởng.
   Phát hành/merge/push theo phạm vi người dùng đã duyệt; version/plugin cache là bước riêng.

## Đọc diff bằng Git

Ví dụ cho Hypit, chạy ở checkout studio. `.tmp/` chứa clone tham khảo dùng trong lượt bảo trì;
thư mục phải chưa tồn tại. Dùng shell phù hợp máy và dọn đúng clone tạm sau khi lưu báo cáo.
Git chỉ lấy cây nguồn, không chạy chương trình Hypit.

```text
git clone --no-checkout https://github.com/hypit-ai/hypit.git .tmp/hypit-source
git -C .tmp/hypit-source rev-parse origin/HEAD
git -C .tmp/hypit-source rev-parse origin/main
git -C .tmp/hypit-source log --oneline BASELINE_SHA..CANDIDATE_SHA
git -C .tmp/hypit-source diff --name-status BASELINE_SHA CANDIDATE_SHA
git -C .tmp/hypit-source diff BASELINE_SHA CANDIDATE_SHA -- LICENSE
git -C .tmp/hypit-source diff BASELINE_SHA CANDIDATE_SHA -- skills/hypit/references packages/narrative-speech-alignment
```

Thay `BASELINE_SHA` bằng `ref` trong sổ, `CANDIDATE_SHA` bằng SHA đã xác minh; không đưa tên nhánh
di động vào hồ sơ nghiệm thu. Với FlowKit dùng repo tương ứng, tập trung `skills/` và vùng review.
Nếu commit không còn truy cập được hoặc upstream viết lại lịch sử, báo baseline không xác minh
được; không suy rằng không có thay đổi. Không nâng pin chỉ để hết cảnh báo.

## Mẫu báo cáo một lần kiểm

| Mục | Nội dung cần ghi |
|---|---|
| Nguồn | Repo, baseline, candidate, ngày, link compare và LICENSE |
| Thay đổi | File/ý tưởng nào đổi, kể cả file đổi tên hoặc bị xóa |
| Quyết định | Bỏ qua / mở rộng / bổ sung / hoãn, kèm lý do và tình huống áp dụng |
| Đích | File local, skill nhận việc, phần trùng đã được reuse |
| Kiểm | Lệnh, kết quả, commit được kiểm, phần visual/audio chưa xem/nghe |
| Chốt | Ref giữ/nâng, attribution, review, commit, bàn giao và rollback |

Rollback triển khai bằng commit revert có phạm vi rõ; giữ baseline và báo cáo trước đó để lần
kiểm sau lần ngược được. Không reset/xóa dữ liệu station hoặc cache người dùng để quay lại.
