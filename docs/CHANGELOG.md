# Nhật ký thay đổi

Mỗi bản phát hành một mục, mới nhất ở trên. Mục **Chưa phát hành** gom những gì đã vào nhánh
chính nhưng chưa có tag; khi phát hành, mục đó đổi tên thành số phiên bản, và số đó phải khớp
`pyproject.toml`, `video_studio/__init__.py` cùng ba manifest plugin (`tests/test_version_sync.py`
kiểm).

## Chưa phát hành

- **Thêm `render --images <images.json>`:** ghép ảnh cục bộ vào đúng cảnh (số cảnh 1-based) cho project
  `repo-today`; lỗi đầu vào là mã 2. Chưa hỗ trợ `news`/`topstory`, nhiều ảnh mỗi cảnh, ảnh URL.
- **Sửa vỏ `render_and_narrate.ps1`:** máy có Python nhưng thiếu module `video_studio` nay thoát mã 3
  (cài thêm) thay vì mã 1 (thử lại); tham số lạ (vd `-Instruct`) nay thoát mã 2 kèm lời báo thay vì
  lỗi PowerShell. `video-routing` gọi chữ «mode» thay «lane».

## 0.4.0 — 2026-10-20

**Sửa lỗi dời trạm:** lỗi sau bước dời dữ liệu được hoàn tác theo trạng thái đã xác minh; nếu trạng thái không rõ hoặc phục hồi thất bại thì giữ dữ liệu và báo cách phục hồi, không dọn rộng.

- **Bố cục `workspaces`:** thư mục gốc luôn tên `workspaces`. Cài riêng lẻ thì trạm nhúng là chính
  `<repo>/workspaces` (thay cho `<repo>/workspace`); cài cùng OpcOS thì trạm là
  `<OPCOS_WORKSPACES>/video`. Bản cài cũ có `<repo>/workspace` mang dấu trạm vẫn được nhận kèm một
  dòng khuyến nghị đổi tên thành `workspaces`; có cả hai thì `workspaces` thắng; `init` mới không
  bao giờ tạo thư mục số ít. `.gitignore` và hook `pre-commit` chặn cả hai tên. Chế độ embedded
  không còn tin chuỗi `station_path: workspace` (hay `workspaces`) mà `init` đời trước ghi trong
  `studio.local.json`: luôn đi qua cách chọn trạm nhúng chung, nên đổi tên thư mục theo lời nhắc
  không làm mất trạm và có cả hai thì `workspaces` thắng; `init` ghi lại `station_path: workspaces`.
- **Cảnh báo (đổi hành vi):** máy đặt `OPCOS_WORKSPACES` thì `init --yes` và mọi lần chạy không người
  (pipe, `--non-interactive`, hết dữ liệu ở câu hỏi) nay ra trạm OpcOS `<biến>/video` thay vì
  `<repo>/workspaces` hay mã 2: đã mang dấu trạm thì dùng thẳng, chưa thì dựng mới và in một dòng nêu
  đường cùng `--station <đường>`. Ai quen `--yes` ra trạm trong repo trên máy có biến thì chạy
  `init --mode embedded --yes`.
- Thư mục trạm cũ ẩn trong thư mục cá nhân không còn được tự nhận; trỏ vào bằng
  `--station <đường>`.
- `init`: `--yes` không bao giờ hỏi; không có `OPCOS_WORKSPACES` thì `--yes` ra trạm nhúng, còn
  `--non-interactive` thiếu cả `--yes` lẫn `--mode` thoát mã 2 (không đoán chế độ); `--mode separate`
  thiếu `--station` thì có `OPCOS_WORKSPACES` ⇒ `<biến>/video` (đã mang dấu trạm thì dùng thẳng, không
  hỏi; chưa thì có người hỏi xác nhận/đổi, không người dùng luôn và in một dòng), không có biến ⇒ có
  người thì hỏi đường, không người thì mã 2 đòi `--station`.
- `init` có `OPCOS_WORKSPACES` mà chạy có người: đúng MỘT câu nhận đường (Enter = `<biến>/video`, hoặc
  gõ đường khác), kể cả khi `<biến>/video` đã mang dấu trạm; bảng `[1]/[2]` chỉ còn khi máy không đặt
  biến. Gõ `1`, `2`, `embedded` hay `separate` ở câu đó thoát mã 2 kèm hướng dẫn (trước đây `2` đi tiếp
  sang câu hỏi đường); trạm trong repo thì dùng `--mode embedded`. `< NUL` hoặc pipe hết dữ liệu khi máy
  có biến nay ra trạm OpcOS thay vì mã 2 (trạm cũ có dữ liệu thì giữ, xem dòng dưới).
- `init` trên máy có `OPCOS_WORKSPACES` mà trạm trong repo (`workspaces/`, hoặc `workspace/` cũ) ĐÃ có
  dữ liệu và chưa ghi lựa chọn: dữ liệu có sẵn thắng biến. `--yes`, chạy không người, hết dữ liệu hay
  Enter ⇒ giữ trạm đó, ghi `mode: embedded` và in một dòng chỉ cách dời sau
  (`migrate --to separate --station <biến>/video`); có người thì hỏi một câu "giữ hay chuyển", gõ
  `chuyen` (hoặc `chuyển`, `c`) thì `init` ghi `embedded` rồi hỏi `y/N` của `migrate` để dời vào
  `<biến>/video` (đích không rỗng ⇒ mã 2 trước câu `y/N`; trả lời không ⇒ giữ, mã 0; `--dry-run` chỉ in
  "sẽ dời"). Bố cục có cả `workspace/` cũ mang dấu lẫn `workspaces/` rỗng: giữ, nhắc gộp, không hỏi.
  Nếu `<biến>/video` cũng đã là một trạm thì có hai trạm mang dấu: giữ trạm trong repo và nhắc gộp bằng
  tay hoặc chọn một bằng `--station`.
- `studio.local.json` ghi `separate` mà thiếu `station_path` (bản ghi hỏng) ⇒ mã 2, không hỏi, nêu
  `--station`, với mọi cách gọi (trước đây `init` đoán sang trạm OpcOS và hỏi lại).
- `OPCOS_WORKSPACES` (hoặc `<biến>/video`) trỏ vào một FILE ⇒ mã 2 nêu tên biến, chưa ghi gì (trước đây
  mã 1 kèm traceback).
- `migrate` (và đáp án `chuyen` của `init`) so ĐƯỜNG THẬT: đích đi qua điểm nối (junction) hoặc liên kết mềm vào
  trạm đang dời, hoặc trạm chính là một điểm nối, nay bị từ chối mã 2 TRƯỚC câu `y/N` và trước byte nào (trước
  đây hỏi `y/N` rồi mới hỏng). `init --migrate` khi chưa có trạm nêu cách đi tiếp (`--station <đường trạm đã
  có>` hoặc bỏ `--migrate`) và không còn in dòng "dùng <biến>/video".
- `OPCOS_WORKSPACES` có dấu nháy dính vào giá trị, hoặc ký tự cấm trong đường dẫn Windows (`<` `>` `|` `?` `*`; dấu hỏi của tiền tố
  extended-length vẫn hợp lệ) ⇒ mã 2, một dòng nêu tên biến, 0 câu hỏi, chưa ghi gì (kể cả khi còn trạm cũ có dữ liệu).
- `OPCOS_WORKSPACES` chính nó đã là một trạm video (có `station.json`, `projects/`…) ⇒ mã 2 nêu tên biến, không dựng trạm
  lồng `<biến>/video`; đường mạng không tới được hay ổ chưa gắn ⇒ mã 2 nêu biến và đường, phần đã làm được hoàn tác
  (trước đây mã 1 kèm traceback).
- Ctrl+C ở bất kỳ lệnh nào của `video-studio` ⇒ một dòng "đã huỷ (Ctrl+C)" và mã 2 (với `--json` là
  `{"ok": false, "code": 2, …}`), không traceback; `migrate` đang dời giữa chừng vẫn trả lại thư mục
  đích rỗng như trước rồi mới thoát.
- `migrate` dời hỏng thì trả lại thư mục đích rỗng mà người dùng đã tạo sẵn; đích là một FILE
  (`--station` hay câu trả lời) thì dừng mã 2 với thông báo rõ thay vì traceback.
- Đường dán có cặp ngoặc kép bao quanh (`"C:\\x"`, kiểu "Copy as path" của Windows) được bóc ngoặc ở
  mọi chỗ nhập đường; `migrate` kiểm `.env` trong kho secret trước câu y/N thay vì sau.
- `video-studio migrate --to separate` hỏi nơi dời thay vì tự chọn một nơi: gợi ý
  `<OPCOS_WORKSPACES>/video` nếu biến đã đặt, hiện đường tuyệt đối đích cùng số file/dung lượng
  rồi xin xác nhận y/N. Không có người trả lời (`--non-interactive`, hoặc không có terminal) thì
  `--station DIR` là bắt buộc, thiếu thì thoát mã 2. Đích nằm trong trạm đang dời bị từ chối.

## 0.3.0 — 2026-10-18

- Station contract không còn fallback ẩn `~/.<station>`: trạm phải được chọn tường minh.
- `init` gợi ý (tuỳ chọn) trạm `workspaces` dùng chung.
- Thêm thông tin tác giả vào metadata và ghi chú tác giả.

## 0.2.8 — 2026-10-14

- Ghi nguồn nghiên cứu FlowKit và ý tưởng Hypit trong `upstream.json`/NOTICE: baseline đầy đủ,
  license tại snapshot, phạm vi theo dõi và đích local. Thêm quy trình bảo trì thủ công tại
  `docs/UPSTREAM-UPDATES.md`; không tự nâng pin hoặc nhận `doctor` là bộ theo dõi hai repo.
- Cache transcript theo snapshot bytes nguồn, model/cài đặt ASR và schema; metadata dùng sidecar riêng để pack vẫn chỉ đọc transcript JSON. Mỗi lượt chép source vào ổ tạm, kể cả cache hit; source vượt nửa dung lượng trống của ổ tạm bị từ chối. Model/weights tùy biến chưa rõ luôn miss; batch tên trùng và thư mục cache trỏ ra ngoài work bị từ chối. Transcript cũ thiếu sidecar sẽ được bóc lại, và bản đang có được giữ nếu ASR lỗi hoặc timestamp ASR không hợp lệ.
- Routing bản tin phân biệt 4 nhóm sản phẩm và 9 thẻ tình huống kỹ thuật để chọn profile, kỹ thuật, skill nhận việc và fallback phù hợp.
- Caption news/top-story giữ chữ authored và map timing qua text normalize; fallback chỉ nhận ASR span còn đúng nguồn và thứ tự, còn tuần cùng số giữ anchor riêng. API và schema không đổi.
- Thêm `video-studio cleanup inspect|preview|apply|verify` để chỉnh vùng trong video local bằng
  FFmpeg: delogo, blur, cover và crop; không cần HyperFrames hoặc model GPU.
- Kiểm ROI, thời gian và profile media trước xử lý; xuất file riêng cùng manifest, kiểm lại hash,
  audio, timing, geometry và màu. Không ghi đè nguồn hoặc output có sẵn.
- Thêm skill `video-cleanup`, adapter host và hướng dẫn. Phạm vi ban đầu: MP4 SDR/CFR yuv420p;
  chất lượng vá hình vẫn cần xem lại, không bảo đảm khôi phục nền gốc.

## 0.2.7 — 2026-10-04

Tự chữa render kẹt + chụp chứng cứ (P1-25, Mac mini 02–03/10). Mã thoát và JSON của `probe` không
`--heal` không đổi.

- **`video-studio probe --heal [--diag-dir DIR] [--heal-waits 60,600]`** (`video_studio/heal.py`):
  lần probe đầu ra `RENDER_STUCK` ⇒ (1) chụp **gói chẩn đoán** vào `DIR/<YYYYmmdd-HHMMSS>/`: top CPU,
  tiến trình Chrome/HyperFrames + số mồ côi, thư mục tạm của Chrome, lỗi + output của probe; macOS
  thêm `pmset -g assertions`, `pmset -g therm`, 10 phút `log show` của WindowServer/coreaudiod. Không
  đọc biến môi trường, không ghi dòng lệnh tiến trình (chỉ tên chương trình), che chuỗi dạng token;
  (2) giết Chrome/HyperFrames **mồ côi** của user (POSIX `ppid == 1`, Windows cha không còn) cùng cây
  con — tiến trình còn cha (một lượt dựng khác) không bị đụng; (3) xoá profile tạm
  `puppeteer_dev_chrome_profile-*` / `hyperframes*` / `video-studio-probe-*` cũ hơn 1 h; (4) chờ
  60 s → probe lại; (5) chờ 600 s → probe lần cuối. Qua ⇒ mã 0, JSON có `heal` (bước nào qua, đường
  gói); hết thang ⇒ mã 1 `RENDER_STUCK:` "đã tự chữa … vẫn kẹt — khởi động lại máy" + `diag`. Dòng
  stderr `RENDER_DIAG=` / `RENDER_HEAL=` cho pipeline đọc. Đo trên Windows: probe khoẻ với `--heal`
  9,1 s, JSON y như cũ; giả lập kẹt (`--timeout 1 --heal-waits 1,1`) ⇒ gói 5 file, mã 1.
- **Sau review độc lập (04/10):** chỉ nhận gốc là Chrome headless (chrome-headless-shell, hoặc Chrome
  `--headless` với profile puppeteer) hoặc node đang `hyperframes … render` — không đụng `hyperframes
  preview --background`, bộ cập nhật nền `node -e`, Chrome của chrome-devtools MCP; Windows: chỉ tiến
  trình cùng phiên đăng nhập, chống PID cấp lại bằng giờ tạo (cha sinh sau con = cha đã chết; cây con
  chỉ nhận con sinh sau cha), `taskkill /F` không `/T`, đọc lại danh sách ngay trước khi giết (đổi
  tên/giờ tạo ⇒ bỏ); profile tạm chỉ xoá khi mtime MỚI NHẤT trong cây > 1 h và không tiến trình sống
  nào nhắc tới; danh sách tiến trình đọc hỏng ⇒ dòng WARN (không im lặng "giết 0"); che thêm
  `Bearer <token>` và `"khoá": "giá trị"` kiểu JSON.
  Vòng 2: profile của chính Chrome mồ côi vừa giết được xoá ngay trong lần chữa đó; `node.exe" -e`
  (Windows) cũng bị loại như `node -e`.
- **Hai giới hạn còn lại sau review, sửa trọn (04/10):** (1) Windows lọc theo phiên đăng nhập chưa
  đủ — task "dù user có đăng nhập hay không" chạy ở phiên 0 chung với task của user khác — nên trước
  khi giết còn đối chiếu SID chủ của từng tiến trình sắp giết với SID của chính mình
  (`Invoke-CimMethod GetOwnerSid`, chỉ hỏi các pid sắp giết); không đọc được chủ ⇒ không giết gì,
  có dòng WARN. (2) Che secret ba lớp trên mọi file của gói: theo GIÁ TRỊ (giá trị biến môi trường
  có tên như secret, dài ≥ 8, đọc trong bộ nhớ chỉ để che), theo TÊN KHOÁ (`khoá=…`, `khoá: …`,
  `"khoá": "…"`, `'khoá': '…'`, `--khoá …`, khoá chứa từ nhạy cảm ở bất kỳ vị trí nào như
  `AWS_SECRET_ACCESS_KEY`), theo HÌNH DẠNG (JWT, AWS `AKIA…`, Telegram, GitHub/OpenAI/Slack/Google,
  hex ≥ 40). Test cài sẵn secret vào env + output probe + output lệnh chụp + dòng lệnh tiến trình
  rồi khẳng định không file nào của gói chứa chúng.
- **Review vòng 3 (04/10) — viết lại lần nữa:** (a) regex che bản trước quay lui BẬC HAI (40 KB chữ
  liền 74 s — gói 5 MB treo `--heal`): nay mọi tên khoá neo đầu từ + trần độ dài, giá trị/PEM có
  trần, văn bản cắt về 5 MB TRƯỚC khi che; test đo 8 chuỗi xấu nhất 1 MB (đo trên Windows ≤ 0,54 s
  mỗi chuỗi). (b) Tra SID bằng ctypes `OpenProcessToken`/`GetTokenInformation` (đo: ~200 tiến trình
  trong ~1 s cả liệt kê; bản PowerShell `GetOwnerSid` tốn ~0,5 s mỗi tiến trình ⇒ quá trần từ ~35
  pid); đọc lại danh sách SAU khi hỏi chủ. (c) Hết lọt: mật khẩu trong URL `scheme://user:pass@`,
  giá trị trong nháy có dấu cách, header `Cookie:`/`Authorization:` che tới hết dòng, `passphrase`,
  `auth`, `%3D`, khoá Google `AIza…`, GitLab `glpat-`, `npm_`, khối PEM. (d) Không che quá tay: bỏ
  `PWD`/`OLDPWD` khỏi danh sách biến secret, số đếm ngắn (`token_count: 123`, `cookie: 42`) giữ nguyên.
- **Review vòng 4 (04/10):** mọi mẫu hình dạng neo bằng `(?<![\w-])` thay `\b` (`\b` khớp sau `-` ⇒
  `eyJ-eyJ-…` mất 4,65 s/MB; nay ≤ 0,55 s/MB trên 14 chuỗi đối kháng 1 MB, có test); thêm che:
  `redis://:pass@`, token Telegram trong URL `/bot123:…`, JSON thoát `{\"password\":…}`, dấu tách
  `:=`/`=>`, giá trị chứa `,;}`, giá trị trong nháy chứa nháy kia hoặc dài tới 4096, PEM có
  `Proc-Type:`/`DEK-Info:`, thân PEM khi điểm cắt 5 MB rơi giữa khối, `sig=`, `hf_`/`ghr_`/`xapp-`,
  webhook Slack; header `Cookie:`/`Authorization:` chỉ tính ở đầu dòng; không che `true/false/…`,
  `token.js:12:3`, `PWD=`, nhãn log `[com.apple.Authorization:authd]`. Giới hạn đã biết (không
  che): mật khẩu dính liền cờ một chữ (`mysql -pX`), giá trị cờ nằm ở dòng sau (`--token⏎X`).
- **Review vòng 5 (04/10) — sửa hồi quy của bản chống-che-quá-tay:** `Pwd=…` trong chuỗi kết nối
  ODBC/SQL Server lại được che (chỉ `PWD=/đường/dẫn` của shell được giữ); `Cookie:`/`Authorization:`
  giữa dòng (`curl -H "Cookie: …"`) che tới hết dòng; khoá mật khẩu/secret/PIN không bao giờ được miễn
  che kể cả giá trị toàn số; ngoại lệ nhãn log chỉ cho `com.apple.*`; giá trị trần không dừng ở `&`;
  giá trị trong nháy hiểu nháy thoát (`"ab\\"cd"`) và JSON lồng thoát mà không sửa nội dung gói; thêm
  khối PGP private key; không che `signature: valid`, `auth_mode=password`, `tokenizer: loaded`.
  `tests/test_heal.py` gộp mọi ca của 5 vòng review thành bảng hồi quy PHẢI CHE / PHẢI GIỮ, và đo
  5 MB văn bản xấu hỗn hợp (< 10 s).
- Stderr Chrome riêng (`--enable-logging`) chưa vào gói: HyperFrames không mở cờ Chrome ra ngoài;
  output gộp của HyperFrames ở lần probe hỏng đã có trong `probe-error.txt`.

## 0.2.6 — 2026-10-03

Một skill duy nhất cho thư viện theme (bản trùng tên ở bộ skill khác trên máy đã bỏ). Mã engine,
render và mã thoát không đổi.

- **`video-theme-library` đọc catalog của trạm trước.** Skill tìm `THEME-LIBRARY.md` ở gốc trạm
  video (nơi thư viện sống theo từng đợt dựng của người dùng); trạm chưa có thì lùi về
  `docs/THEME-LIBRARY.md` của repo. Nghĩa vụ giữ thư viện còn sống áp cho catalog đang dùng.
  Nội dung `docs/THEME-LIBRARY.md` không đổi. Nhánh này viết khi 0.2.5 còn chờ gộp; 0.2.5 đã gắn
  tag trước nên mục này thành bản riêng. Adapter `.claude/skills` + `.agents/skills` đã sinh lại.

## 0.2.5 — 2026-10-02

Rào cho bước render (P1-24). Mac mini 02/10/2026: Hot AI 18:00 hỏng sau 42 phút — `page.goto …
Navigation timeout of 60000 ms` ở frame 0, ba lần thử, mọi project và cả bản HyperFrames mới nhất
đều hỏng, Chromium/puppeteer mở cùng trang bình thường; **khởi động lại máy là hết**. Lỗi môi
trường, không phải lỗi repo — nhưng pipeline chỉ biết sau 40 phút agent + TTS, và thông báo lỗi
khuyên `doctor --hf`, tức chỉ sai hướng.

- **Lệnh mới `video-studio probe [--timeout 30] [--json]`** (`video_studio/probe.py`): render thật
  một trang 320×180 dài 0,5 s, không tài nguyên ngoài (không font web, không GSAP từ CDN), timeline
  giả tối thiểu (thiếu nó engine chờ 45 s). Đo trên Windows: 7–9 s kể cả khởi động npx. Quá giờ hoặc
  `Navigation timeout` ⇒ mã 1, lỗi mở đầu `RENDER_STUCK:` + "khởi động lại máy rồi chạy lại", giết
  **cả cây** tiến trình (npx → node → Chrome). Hỏng kiểu khác ⇒ mã 1 kèm đuôi log + `doctor --hf`.
  Thiếu `npx` ⇒ mã 3. Không in traceback: hỏng của phép thử là kết quả đo.
  **Làm ấm NGOÀI trần giờ** (`warm_up`): `npx hyperframes@<bản> --version` + `browser ensure` nếu
  `doctor` không thấy Chromium, mỗi bước trần 600 s; hỏng ⇒ mã 3 — lượt đầu sau nâng bản ghim /
  xoá cache không bị gọi nhầm là "kẹt". `Navigation timeout` chỉ tính khi render thử HỎNG.
  Làm ấm chạy qua Popen + giết cả cây khi quá giờ (`subprocess.run` treo trên Windows khi node
  cháu giữ pipe). `docs/CONTRACT.md` ghi rõ `--timeout` chỉ đo phần render.
- **`render_project`**: MỌI lần thử chết vì `Navigation timeout` ⇒ lỗi `RENDER_STUCK:` nói thẳng
  "khởi động lại máy" (kèm `video-studio probe` để kiểm nhanh); hỏng lẫn lộn giữ lời khuyên cũ.
- `docs/CONTRACT.md` §1: tên `RENDER_STUCK:` trong mã 1 và hợp đồng của `probe`. README, trang
  giới thiệu: thêm dòng `probe` vào bảng lệnh.
- **Bên gọi**: agent-marketing-studio 1.1.8 chạy `probe` trước bước nghiên cứu của ba runner tin.

## 0.2.4 — 2026-10-01

ffmpeg phải **đủ bộ lọc chữ**, không chỉ có lệnh. Trên Mac mini (01/10/2026), `brew install
ffmpeg` theo INSTALL cũ cho bản Homebrew core đã bỏ libfreetype + libass ⇒ không có `drawtext`,
`subtitles`, `ass`; `doctor` vẫn PASS, `edit` đốt phụ đề hỏng, và runner truyện của
marketing-studio (dùng chung ffmpeg) chết ở bước dựng video sau 7 giờ đọc. Render bản tin
(HyperFrames) không đổi.

- **INSTALL**: macOS cài `ffmpeg-full` thay `ffmpeg` (INSTALL.md bảng công cụ + lệnh `brew`,
  docs/INSTALL.md, GUIDE, START-HERE); giải thích keg-only. Bảng ghi rõ "bản có libfreetype +
  libass".
- **Dò ffmpeg**: `FFMPEG_DIR` → (macOS) keg `/opt/homebrew/opt/ffmpeg-full/bin` → `PATH`. Keg thắng
  bản core trên `PATH`, không cần symlink hay sửa `PATH`.
- **`doctor`**: dòng mới `ffmpeg-filters` đọc `ffmpeg -hide_banner -filters`, đòi `drawtext`,
  `subtitles`, `ass`. Thiếu là **WARN** (render bản tin không cần) kèm lệnh cài; mã thoát không
  đổi.
- **`edit`**: cần đốt phụ đề mà ffmpeg không có `subtitles` ⇒ **mã 3 ngay**, trước khi cắt/ghép
  đoạn nào (`edit/render.py: require_filters`); `--no-subtitles` vẫn chạy.
- **CI job `ffmpeg`** (Windows + macOS): cài đúng bản INSTALL dạy (keg KHÔNG thêm vào `PATH`), rồi
  kiểm bộ lọc + đốt phụ đề thật; `VIDEO_STUDIO_REQUIRE_FFMPEG=1` biến skip thành đỏ.
- **Nâng cấp máy Mac đang chạy**: `brew install ffmpeg-full`; gỡ symlink tạm
  `~/.local/bin/ffmpeg`/`ffprobe` nếu đã tạo; `video-studio doctor` phải có
  `[PASS] ffmpeg-filters`.

## 0.2.3 — 2026-09-30

Bản dọn theo báo cáo review repo 30/09, chỉ các mục rủi ro không/thấp. **Hành vi render, init và
trạm không đổi** trên Windows lẫn Mac; mã thoát của mọi lệnh giữ nguyên.

- **Tài liệu `init`:** `GUIDE.md`/`GUIDE.vi.md` và skill `video-routing` còn nói `init` tự nhận
  trạm có sẵn — sai từ 0.2.2. Viết lại đúng mã: trạm đã chọn (`VIDEO_STATION`,
  `studio.local.json` ghi `separate`) dùng luôn; `~/.video` chỉ tình cờ có mặt thì `init` hỏi,
  `--yes`/không người là mã 2, nhận bằng `--mode separate`/`--station`/`--migrate`. Cổng
  `tests/test_docs_drift.py` thêm danh sách câu đã sai, cấm quay lại. `START-HERE.md` thêm hai
  dòng dưới `init --yes`: báo "máy đã có trạm video ở …" thì dùng `init --mode separate`.
- **Telemetry HyperFrames:** bước tắt telemetry dời lên **trước** `doctor` (`INSTALL.md` mục 7,
  trước là 7b) vì `doctor` gọi `npx hyperframes doctor`; các mục sau đánh lại số (doctor 8, bài
  mẫu 9, báo cáo 10, gỡ vướng 11). `doctor` thêm một dòng `[NOT_CHECKED] telemetry` in đúng lệnh
  `npx --yes hyperframes@<bản ghim> telemetry disable` — không gọi thêm lệnh nào, không đổi mã thoát.
- **Lời khuyên khi thiếu phụ thuộc render** (mã 3, không đổi): bỏ `pip install -e ".[voice]"` (hỏng
  khi chưa có bản clone repo giọng); nay trỏ `INSTALL.md` mục 5b, `pip install -e "<repo giọng>[engine]"`,
  và in đường thật khi thấy bản clone repo giọng cạnh repo này (như `doctor`).
- **CI:** `actions/checkout` v5.1.0 và `actions/setup-python` v6.3.0 (chạy Node 24), vẫn ghim SHA.
- **`.gitignore`:** thêm `.coverage`, `htmlcov/`, `.mypy_cache/`, `.ruff_cache/`,
  `templates/_seed/package-lock.json`.

## 0.2.2 — 2026-09-30

Bản vá sau lượt kiểm trên Mac mini (báo cáo MAC-REVIEW-FOR-WINDOWS). Máy Windows đã đặt
`VIDEO_STATION` không đổi hành vi.

- **`init` không còn tự nhận `~/.video` có sẵn** (sự cố lượt Mac 29/09). `~/.video` chỉ tình cờ
  mang dấu trạm thì `init` hỏi người dùng; với `--yes` hay khi không có người trả lời, nó in đường
  trạm cũ rồi thoát mã 2 và không ghi gì. Nhận trạm đó phải bằng `--mode separate`,
  `--station <thư mục>` hoặc `--migrate`. `--yes` giữ đúng nghĩa: embedded, `<repo>/workspace/`.
  Trạm đã chọn (biến `VIDEO_STATION`/`VIDEO_ROOT`, hoặc `studio.local.json` ghi `separate`) vẫn
  dùng luôn không hỏi; `studio.local.json` ghi `separate` nay thắng một `~/.video` tình cờ có mặt.
- **Khối `engine` của JSON kết quả (P2-17):** `engine.voice_studio` nay là bản **hợp đồng** của
  repo giọng (`API_VERSION`) ở cả `render` lẫn `narrate`, đúng nghĩa repo giọng tự trả; bản phát
  hành của gói giọng đi khoá mới `engine.voice_studio_version`. Trước đây `render` trả bản phát hành
  dưới cùng khoá. Bảng nghĩa từng khoá ở `docs/CONTRACT.md` §2.
- **`scripts/install-video-use.{ps1,sh}`** không còn đoán trạm là `$HOME/.video`: trạm do package
  phân giải (biến → `studio.local.json` → `<repo>/workspace/`), và lệnh gợi ý cuối cùng khớp chế độ
  cài. Cổng `tests/test_ps1_portable.py` thêm luật chặn mọi script đoán trạm ở home.
- **`doctor`:** chưa cài repo giọng mà bản clone của nó nằm cạnh repo này (cùng thư mục cha, tên gì
  cũng được, nhận bằng nội dung) thì dòng `voice-studio` in sẵn lệnh `pip install -e "<đường>[engine]"`.
- **Tài liệu:** clone vào `<thư mục cha>` người dùng chọn thay cho đường cứng; repo giọng là anh em
  cùng thư mục cha (`INSTALL.md` mục 4, 5b); bước tắt telemetry của HyperFrames
  `npx --yes hyperframes@<bản ghim> telemetry disable` (mục 7b, P2-18); mọi chỗ nói `browser ensure`
  ghi rõ dạng `npx --yes hyperframes@<bản ghim> browser ensure` — đó là lệnh của HyperFrames, CLI
  repo này không có lệnh con `browser` (P2-2); `package.json` của project không quyết bản render,
  `station.json` mới quyết (P3-2); bảng nền tảng ghi macOS arm64 đã render thật bài mẫu (dòng macOS
  của `samples/news-mini/EXPECTED.md`, PR #3).

## 0.2.1 — 2026-09-29

Bản vá tài liệu để một agent trên Mac Apple Silicon mới tinh tự cài được theo `INSTALL.md`, không
biến môi trường nào (chế độ embedded).

- **macOS trong `INSTALL.md`, `START-HERE.md`, `docs/INSTALL.md`:** tạo venv bằng `python3.12`
  (`python3` của Mac mới là 3.9, dưới mức tối thiểu); điều kiện trước cho Mac mới — Xcode Command
  Line Tools, Homebrew do người dùng tự cài (agent không chạy lệnh tải-rồi-chạy), `/opt/homebrew/bin`
  trên `PATH`, `brew install python@3.12 node ffmpeg git`; kiểm biến và `PATH` bằng
  `zsh -lic 'echo $…'` vì shell của agent không nạp `~/.zshrc`. Lần render đầu cần mạng (HyperFrames,
  Chromium, CDN), và bản HyperFrames đang ghim (0.8.54) chưa render gì trên arm64.
- **Một đường cài lồng tiếng duy nhất** (mục 5b mới của `INSTALL.md`): clone `agent-voice-studio`
  cạnh repo này, `pip install -e "../agent-voice-studio[engine]"` vào chính `.venv` của repo video,
  `voice-studio init --yes`, rồi tạo giọng mặc định bằng `make-profile --instruct … --set-default`.
  Bỏ câu "cài vào venv của trạm giọng" ở `docs/INSTALL.md` và trang web, vốn mâu thuẫn với
  `INSTALL.md`. Thiếu bước giọng mặc định thì bài mẫu dừng vì chưa có profile — trước đây tài liệu
  không nói.
- **Bài mẫu `news-mini`:** dòng Windows trong `EXPECTED.md` có số đo thật (HyperFrames 0.8.54,
  113 s, 51,05 s / 24,93 s), đo bằng một bản cài mới theo đúng mục 5b.
- **`INSTALL.md` mục 6:** máy đã có trạm `~/.video` thì `init --yes` tự nhận trạm đó — agent phải
  đọc dòng `station` của `doctor` và hỏi trước khi render thử vào trạm đang chạy lịch.

## 0.2.0 — 2026-09-29

Chuẩn hóa để chạy như nhau trên Windows và macOS, cài được bằng một lời nhờ agent.

- **Trạm mặc định nằm trong repo.** Không đặt biến nào thì trạm là `<repo>/workspace/` (Git bỏ
  qua cả thư mục), kể cả trước khi `video-studio init` tạo nó. Bỏ tầng đoán `~/.video`: máy dùng
  trạm ngoài chọn tường minh bằng `VIDEO_STATION` hoặc `init --station DIR`. Bản cài wheel không
  có repo thì mọi lệnh cần trạm dừng mã 3 và chỉ cách chọn trạm.
- **Trạm giọng không bị đoán.** `VOICE_STATION` → `OMNIVOICE_DIR` → trạm mà repo giọng cài cùng
  venv đã được chọn; không có gì thì là "chưa có trạm giọng".
- **Bài mẫu `samples/news-mini/`** — bản tin hai cảnh, giọng ghim hạt giống, kèm `EXPECTED.md`
  (lệnh chạy, tên file ra, bảng số đo theo máy) và test không cần mạng.
- **CI** chạy trên mọi nhánh, ma trận Windows + macOS × Python 3.10 / 3.12 / 3.13, action ghim
  theo SHA commit.
- **Skill không còn được chép vào trạm.** `init` thôi chép 24 skill vào `<trạm>/.claude/skills` +
  `.agents/skills` và thôi ghi `skills-lock.json`. Gốc repo có adapter `.claude/skills/` và
  `.agents/skills/` (sinh bằng `scripts/build_host_adapters.py`, `--check` báo lệch) trỏ về skill
  gốc trong `skills/` — một nguồn, `git pull` là có bản mới. Trạm cũ: `init --station DIR --migrate`
  gỡ bản đã chép cùng file khoá (dời vào nhật ký, `--undo` trả về), skill riêng của người dùng giữ.
- **`video-studio uninstall`** — chỉ gỡ thứ bộ cài đã đặt (skill bản cũ đã chép nếu chưa sửa, liên kết
  repo → trạm, `.env` chưa điền, hook pre-commit của chính nó), dời vào nhật ký của trạm thay vì
  xoá; trạm và mọi project giữ nguyên. `--dry-run` in kế hoạch.
- **`doctor` có mức `NOT_CHECKED`** cho thứ chưa kiểm được (chạy `--offline`, thiếu npx) và cho
  `render` — doctor không tự render, nên không để một bảng toàn PASS nói thay. Nhãn người đọc
  đổi thành `PASS` / `WARN` / `FAIL` / `NOT_CHECKED` / `SKIP`; JSON thêm danh sách `not_checked`.
- **Cài bằng một lời nhờ agent:** `INSTALL.md` ở gốc repo là hướng dẫn dành cho agent (Windows và
  macOS, hỏi trước khi cài phần mềm, không tải-rồi-chạy, báo nguyên văn từng dòng `doctor`) kèm
  prompt copy-dán tiếng Việt và tiếng Anh; README và START-HERE chép đúng prompt đó.
- `AGENTS.md` (hướng dẫn chung cho mọi agent) với `CLAUDE.md` / `GEMINI.md` là con trỏ, và
  `hosts/` cho Claude Code, Codex, Antigravity, Claude Desktop — nói rõ đường nạp skill nào đã
  chạy, đường nào chưa kiểm.
- Trang web `/install/`: chọn ứng dụng AI, dán prompt (chép nguyên văn từ `INSTALL.md`), đọc nhãn kiểm tra.
- `START-HERE.md` và nhật ký thay đổi này.

## 0.1.0 — 2026-09-22

Bản công khai đầu tiên.

- Lệnh `video-studio`: `init` (hai chế độ `embedded` / `separate`, `--migrate`, `--undo`,
  `--dry-run`), `doctor`, `render`, `edit`, `preview`, `narrate`, `export`, `import`, `backup`,
  `migrate`, `update`.
- Hợp đồng gọi từ chương trình khác: mã thoát 0 / 1 / 2 / 3 và một dòng JSON cuối stdout
  ([CONTRACT.md](CONTRACT.md)), phủ cả `doctor` và lỗi nạp lệnh.
- `render` theo template bản tin `news`, `news-weekly`, `topstory`, `repo-today` từ một spec JSON;
  thương hiệu bắt buộc khai trong spec (thiếu là mã 2).
- HyperFrames ghim bản `0.8.54`, render khai `-q standard` tường minh; `doctor --check-updates`
  chỉ báo, không tự nâng.
- 21 skill HyperFrames chưng cất (thân tiếng Việt, ghi nguồn và hash đối chiếu upstream) cùng 3
  skill riêng: `video-routing`, `video-edit`, `video-theme-library`.
- Cổng chống ghi thoát khỏi `--out` độc lập hệ điều hành, chịu được hai cây trên hai ổ đĩa khác
  nhau trên Windows.
- CI Windows + macOS, và một job riêng so hash skill với manifest upstream.
