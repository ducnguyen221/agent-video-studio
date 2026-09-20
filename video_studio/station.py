"""station.py — `video-studio init`: dựng trạm video, di trú trạm đời cũ, hoàn tác.

    video-studio init --station DIR                 dựng (hoặc bổ sung) trạm ngoài repo
    video-studio init --station DIR --migrate       + di trú bố cục cũ: news/, topstory/ ở gốc
                                                      → projects/<tên>/, ghim bản HyperFrames
    video-studio init … --dry-run                   chỉ in kế hoạch, KHÔNG ghi gì
    video-studio init --station DIR --undo          đảo lần init gần nhất theo nhật ký

TRẠM là nơi chứa những gì của riêng người dùng (project đang dựng, seed, skill cho agent, nháp,
cache); repo chỉ chứa mã. Hai chế độ cài (F17):

    embedded   trạm = <repo>/workspace/ (gitignore) — "mở một folder là thấy hết". Mặc định và
               là khuyến nghị cho người dùng mới.
    separate   trạm ngoài repo (mặc định ~/.video) — cho người dùng nhiều máy, repo public của
               chính mình, nhiều repo chia sẻ trạm.

`--station DIR` = separate, không hỏi. Máy đã có trạm ngoài (VIDEO_STATION / VIDEO_ROOT đã đặt,
hoặc ~/.video đã có station.json, projects/, hay seed demo/ đời cũ) ⇒ tự chọn separate, KHÔNG
hỏi, KHÔNG BAO GIỜ tạo workspace/.

Kỷ luật thi hành:
- Lập KẾ HOẠCH trọn vẹn và kiểm xung đột TRƯỚC khi ghi byte nào; xung đột ⇒ mã 2, không đụng gì.
- Chỉ chạm danh sách cho phép (`ALLOWED_TOP`); mọi thư mục/file khác ở gốc trạm (dự án riêng,
  bản vendored, nhạc nền, log…) để nguyên từng byte — `_guard` chặn cả lỗi lập trình.
- Mỗi thao tác ghi xong mới ghi vào nhật ký `<trạm>/.video-studio/runs/<id>/journal.json`; bản cũ
  của thứ bị thay nằm ở `…/prev/`. Lỗi giữa chừng ⇒ tự đảo phần đã làm. `--undo` đảo theo nhật ký,
  và GIỮ file người dùng đã sửa sau lần init (báo lại, không xoá).
- Không xoá đệ quy: hoàn tác chỉ xoá đúng file mình đã tạo (khớp sha256) và thư mục đã rỗng.
- Không dời thư mục bằng shutil.move (rơi về copytree + rmtree dở dang khi file bị giữ).
"""
import argparse
import datetime
import errno
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile

from . import API_VERSION, __version__, _env, contract
from .contract import ContractError, StationMissing

MODES = _env.MODES                        # hợp đồng F17 — một nguồn sự thật ở _env
SECRET_DIR_NAME = "video-studio"          # ~/.secret/<tên> khi chạy chế độ separate
# Giá trị này ĐI VÀO studio.local.json, nên nó phải là ASCII và là một đường dẫn thật: một
# chuỗi mô tả có dấu đọc bằng công cụ khác encoding sẽ hiện ra rác, và không ai dán nó vào
# đâu được. Cùng khuôn với `agent-marketing-studio` và `agent-voice-studio`.
SECRET_STORE = f"~/.secret/{SECRET_DIR_NAME}"
LEGACY_PROJECTS = ("news", "topstory")
SKILL_TOOLS = (".claude/skills", ".agents/skills")
LOCK_FILE = "skills-lock.json"
LOCK_SOURCE = "agent-video-studio"
RUNS_DIR = ".video-studio/runs"
BASE_DIRS = ("projects", "scratch", "cache")
WORKSPACE_TEMPLATE = "workspace"
# Nháp và cache không vào gói backup: dựng lại được, và chúng là phần nặng nhất của trạm.
BACKUP_SKIP_TOP = {"scratch", "cache", ".video-studio"}
BACKUP_SKIP_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__"}
# Gốc trạm: engine chỉ được chạm những tên này (projects_dir tuỳ biến được thêm lúc chạy).
ALLOWED_TOP = {"projects", "scratch", "cache", "demo", ".claude", ".agents", LOCK_FILE,
               _env.STATION_FILE, ".video-studio", *LEGACY_PROJECTS}
PIN_RE = re.compile(r"(hyperframes@)([0-9A-Za-z.\-^~]+)")

CHOICE_TABLE = """\
Chọn chỗ đặt TRẠM VIDEO (nơi chứa project đang dựng, seed, skill cho agent, nháp, cache):

  [1] embedded — gọn trong repo   ← KHUYẾN NGHỊ (bấm Enter)
      Là gì : trạm nằm ở <repo>/workspace/, biến cấu hình ở <repo>/.env (git bỏ qua cả hai).
      Lợi   : mở một folder là thấy hết; không phải đặt biến môi trường; backup một phát.
      Hại   : xoá folder repo là mất luôn project — đừng xoá repo để cài lại, dùng
              `video-studio update`; và nhớ `video-studio backup`.
      Chọn khi: một máy, muốn dùng được ngay, không rành kỹ thuật.

  [2] separate — trạm ngoài repo (mặc định ~/.video)
      Là gì : trạm ở thư mục riêng; bí mật ở kho secret của máy ({kho}).
      Lợi   : repo luôn sạch (an toàn khi repo là bản public của chính bạn); nhiều máy /
              nhiều repo dùng chung một trạm; cập nhật repo không đụng dữ liệu.
      Hại   : thêm một chỗ phải nhớ; nên đặt VIDEO_STATION cho lịch chạy thấy trạm.
      Chọn khi: rành kỹ thuật, nhiều máy, hoặc repo public của chính bạn.

Sau này đổi ý được: `video-studio migrate --to separate`.
""".format(kho=SECRET_STORE)


# ── tiện ích ───────────────────────────────────────────────────────────────────────────

def _skills_root():
    """`skills/` đi cùng MÃ đang chạy (bản clone chứa package)."""
    return os.path.join(_env.package_repo(), "skills")


def _seed_dir():
    """Seed project HyperFrames đi cùng mã: `templates/_seed/` (None nếu repo chưa có)."""
    d = os.path.join(_env.package_repo(), "templates", "_seed")
    return d if os.path.isdir(d) else None


def _workspace_template():
    """Cây mẫu của một trạm MỚI: `templates/workspace/` (None nếu repo chưa có)."""
    d = os.path.join(_env.package_repo(), "templates", WORKSPACE_TEMPLATE)
    return d if os.path.isdir(d) else None


def _p(st, rel):
    return os.path.join(st, *rel.split("/"))


def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _files(root):
    """Danh sách file tương đối (posix) dưới `root`, sắp xếp."""
    out = []
    for dp, dn, fn in os.walk(root):
        dn.sort()
        for n in sorted(fn):
            out.append(os.path.relpath(os.path.join(dp, n), root).replace(os.sep, "/"))
    return out


def _tree_hash(root):
    h = hashlib.sha256()
    for rel in _files(root):
        h.update(rel.encode("utf-8") + b"\0" + _sha256(os.path.join(root, *rel.split("/"))).encode())
    return h.hexdigest()


def _json_text(data):
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"


def _pin_text(text, version):
    return PIN_RE.sub(lambda m: m.group(1) + version, text)


# ── chọn chế độ ────────────────────────────────────────────────────────────────────────

def detect_external():
    """Máy đã có trạm video ngoài? -> (đường trạm, lý do) hoặc None. Không ghi gì."""
    if _env.env("VIDEO_STATION"):
        return _env._expand(_env.env("VIDEO_STATION")), "biến VIDEO_STATION đã đặt"
    if _env.env("VIDEO_ROOT"):
        return _env._expand(_env.env("VIDEO_ROOT")), "biến VIDEO_ROOT (tên cũ) đã đặt"
    home = _env.default_station()
    if _env.has_marker(home):
        return home, "~/.video đã là một trạm (station.json, projects/ hoặc seed demo/ đời cũ)"
    return None


def _stdin_is_tty():
    try:
        return sys.stdin is not None and sys.stdin.isatty()
    except Exception:          # noqa: BLE001 — stdin bị thay (pytest, dịch vụ)
        return False


def _ask_console(prompt):
    contract.log(prompt)
    sys.stderr.write("Chọn [1/2] (Enter = 1, embedded): ")
    sys.stderr.flush()
    return input()


def choose_mode(station=None, mode=None, yes=False, ask=None, non_interactive=False):
    """-> (chế độ, gốc trạm, lý do). Ném ContractError khi cần người chọn mà không hỏi được.

    `non_interactive` = người gọi TỰ KHAI "không có ai ngồi đây". Nó KHÔNG có nghĩa là "cứ
    đoán hộ tôi": thiếu `--yes`/`--mode`/`--station` thì vẫn là mã 2. Đoán ở đây là dựng
    trạm sai chỗ, và người dùng chỉ phát hiện ra sau khi đã dựng vài project.
    """
    repo = _env.repo_root()
    if station:
        return "separate", _env._expand(station), "--station"
    ext = detect_external()
    if ext:
        if mode == "embedded":
            raise ContractError(
                f"máy đã có trạm video ngoài ({ext[1]}: {ext[0]}); tạo thêm workspace/ sẽ thành "
                "hai nguồn sự thật. Dùng trạm đó (bỏ --mode) hoặc gỡ biến/trạm cũ trước.")
        return "separate", ext[0], f"nhận diện trạm có sẵn — {ext[1]}"
    if not mode:
        local = _env.local_config(repo) if repo else {}
        prev = local.get("mode")
        if prev == "separate" and local.get("station_path"):
            return "separate", _env.resolve_station()[0], "studio.local.json (lần chọn trước)"
        if prev in MODES:
            mode, why = prev, "studio.local.json (lần chọn trước)"
        elif yes:
            mode, why = "embedded", "--yes (nhận khuyến nghị)"
        else:
            if ask is None:
                if non_interactive or not _stdin_is_tty():
                    contract.log(CHOICE_TABLE)
                    raise ContractError(
                        "cần người dùng chọn chế độ cài. Agent: trình bảng trên cho người dùng, "
                        "rồi chạy lại với --mode embedded|separate (hoặc --yes = embedded, "
                        "hoặc --station DIR = separate).")
                ask = _ask_console
            try:
                ans = (ask(CHOICE_TABLE) or "").strip().lower()
            except EOFError:
                # Windows: stdin là NUL vẫn báo isatty() = True — hết dữ liệu nghĩa là không có người.
                raise ContractError(
                    "không đọc được lựa chọn (stdin không có người). Agent: trình bảng lựa chọn cho "
                    "người dùng, rồi chạy lại với --mode embedded|separate (hoặc --yes = embedded).")
            if ans in ("", "1", "embedded"):
                mode = "embedded"
            elif ans in ("2", "separate"):
                mode = "separate"
            else:
                raise ContractError(f"lựa chọn không hợp lệ: {ans!r} (1 = embedded, 2 = separate)")
            why = "người dùng chọn"
    else:
        why = "--mode"
    if mode == "embedded":
        # Trạm nằm TRONG repo ⇒ phải có một repo thật để nằm vào. Bản cài wheel không có, và
        # `VIDEO_STUDIO_REPO` trỏ vào chỗ không tồn tại cũng không có: tạo workspace/ ở một
        # đường không có thật là cách làm mất dữ liệu người dùng mà không ai thấy.
        if not repo or not os.path.isdir(repo):
            raise ContractError("chế độ embedded cần chạy từ bản clone repo (pip install -e <repo>); "
                                "bản cài wheel chỉ dùng được separate (--station DIR).")
        return "embedded", os.path.join(repo, _env.WORKSPACE), why
    return "separate", _env.default_station(), why


# ── lập kế hoạch ───────────────────────────────────────────────────────────────────────

def _repo_skills():
    """{tên: thư mục} — mọi thư mục chứa SKILL.md dưới skills/ của repo (kể cả lồng một cấp)."""
    root = _skills_root()
    found = {}
    if not root or not os.path.isdir(root):
        return found
    for dp, dn, fn in os.walk(root):
        dn.sort()
        if "SKILL.md" in fn:
            name = os.path.basename(dp)
            if name in found:
                raise ContractError(f"repo có hai skill trùng tên '{name}': {found[name]} và {dp}")
            found[name] = dp
            dn[:] = []                      # không đi sâu vào references/ của skill
    return found


def _video_use_info(st):
    d = os.path.join(st, "video-use")
    if not os.path.isdir(d):
        return {"dir": None, "python": None}
    rel = ".venv/Scripts/python.exe" if os.name == "nt" else ".venv/bin/python"
    py = os.path.join(d, *rel.split("/"))
    return {"dir": "video-use", "python": "video-use/" + rel if os.path.isfile(py) else None}


def _station_json(st, mode, version, projects_rel):
    path = os.path.join(st, _env.STATION_FILE)
    cur, err = _env.read_json(path)
    if err:
        raise ContractError(f"station.json hỏng, sửa tay hoặc xoá rồi chạy lại: {err}")
    data = {
        "contract": API_VERSION,
        "mode": mode,
        "hyperframes_version": version,
        "projects_dir": projects_rel,
        "video_use": _video_use_info(st),
        "voice_station": _env.voice_station(),
        "created_by": f"video-studio {__version__}",
        "created": datetime.date.today().isoformat(),
    }
    for k in ("created_by", "created"):
        if k in cur:
            data[k] = cur[k]
    data.update(cur)                       # giá trị người dùng đã sửa luôn thắng
    return data, (data != cur)


def build_plan(st, mode, migrate, version):
    """-> dict kế hoạch (không ghi gì). Ném ContractError / StationMissing khi không làm được."""
    if os.path.exists(st) and not os.path.isdir(st):
        raise ContractError(f"{st} không phải thư mục")
    exists = os.path.isdir(st)
    if migrate and not exists:
        raise StationMissing(f"--migrate nhưng không có trạm: {st}")
    info, err = _env.read_json(os.path.join(st, _env.STATION_FILE))
    if err:
        raise ContractError(f"station.json hỏng, sửa tay hoặc xoá rồi chạy lại: {err}")
    projects_rel = str(info.get("projects_dir") or "projects").replace("\\", "/").strip("/")
    if os.path.isabs(projects_rel) or ".." in projects_rel.split("/"):
        raise ContractError(f"station.json projects_dir phải là đường tương đối trong trạm: {projects_rel}")
    plan, notes, kept = [], [], []

    if not exists:
        plan.append({"op": "mkdir", "path": "."})
    for d in (projects_rel,) + BASE_DIRS[1:]:
        if not os.path.isdir(_p(st, d)):
            plan.append({"op": "mkdir", "path": d})

    # 1. project đời cũ ở gốc trạm → projects/<tên>
    moved = []
    for name in LEGACY_PROJECTS:
        src = _p(st, name)
        if not os.path.isdir(src):
            continue
        dst_rel = f"{projects_rel}/{name}"
        if not migrate:
            notes.append(f"{name}/ còn ở gốc trạm (bố cục cũ) — chạy lại với --migrate để dời vào "
                         f"{dst_rel}/")
            continue
        if os.path.exists(_p(st, dst_rel)):
            raise ContractError(f"xung đột: đã có {dst_rel} trong khi {name}/ vẫn ở gốc trạm — gộp tay "
                                "(hoặc đổi tên một bên) rồi chạy lại. Chưa đụng gì.")
        plan.append({"op": "move", "src": name, "dst": dst_rel})
        moved.append((name, dst_rel))

    # 2. ghim bản HyperFrames trong package.json của project + seed
    if migrate:
        targets = [(f"{name}/package.json", f"{dst}/package.json") for name, dst in moved]
        targets.append(("demo/package.json", "demo/package.json"))
        for now_rel, final_rel in targets:
            f = _p(st, now_rel)
            if not os.path.isfile(f):
                continue
            with open(f, "r", encoding="utf-8") as fh:
                text = fh.read()
            pins = sorted(set(m.group(2) for m in PIN_RE.finditer(text)))
            if pins and pins != [version]:
                plan.append({"op": "pin", "path": final_rel, "from": pins, "to": version})

    # 3. filler cho short tin: chép từ trạm giọng (không đè)
    news_dst = f"{projects_rel}/news"
    news_will_exist = os.path.isdir(_p(st, news_dst)) or any(d == news_dst for _, d in moved)
    if migrate and news_will_exist:
        fill_dst = f"{news_dst}/assets/fillers"
        src = next((c for c in _env.filler_source_candidates() if os.path.isdir(c)), None)
        if src is None:
            notes.append("không thấy thư mục filler ở trạm giọng (VOICE_STATION / OMNIVOICE_DIR) — bỏ qua")
        else:
            todo = [r for r in _files(src) if not os.path.exists(_p(st, f"{fill_dst}/{r}"))]
            if todo or not os.path.isdir(_p(st, fill_dst)):
                plan.append({"op": "copy", "src": src, "dst": fill_dst, "files": todo})

    # 3b. cây mẫu của một trạm MỚI (README từng thư mục, project ví dụ, brand mẫu).
    # CHỈ khi trạm chưa tồn tại: trạm đang dùng là của người ta, đừng rải README vào đó.
    ws_extra = set()
    ws = _workspace_template()
    if not exists and ws:
        ws_files = [r for r in _files(ws) if not os.path.exists(_p(st, r))]
        if ws_files:
            plan.append({"op": "workspace", "src": ws, "dst": ".", "files": ws_files})
            ws_extra = {r.split("/")[0] for r in ws_files}

    # 4. seed demo/
    seed = _seed_dir()
    if not os.path.isdir(_p(st, "demo")):
        if seed:
            plan.append({"op": "seed", "src": seed, "dst": "demo", "files": _files(seed),
                         "pin": version})
        else:
            notes.append("repo chưa có templates/_seed/ — chưa dựng demo/ (seed project HyperFrames)")

    # 5. skill cho agent: chép từ repo vào .claude/skills và .agents/skills
    skills = _repo_skills()
    replace_lock = False
    for tool in SKILL_TOOLS:
        for name, src in sorted(skills.items()):
            rel = f"{tool}/{name}"
            dst = _p(st, rel)
            if not os.path.isdir(dst):
                plan.append({"op": "skill", "action": "add", "src": src, "dst": rel})
            elif _tree_hash(dst) == _tree_hash(src):
                continue
            elif migrate:
                plan.append({"op": "skill", "action": "replace", "src": src, "dst": rel})
            else:
                kept.append(f"{rel} (khác bản trong repo — giữ; --migrate để thay, bản cũ được lưu)")
    # Skill ở trạm mà repo KHÔNG có: bộ đời cũ do công cụ khác cài. `--migrate` dọn chúng đi
    # (bản cũ vào prev/ của nhật ký ⇒ `--undo` trả lại được); không --migrate thì chỉ báo tên.
    legacy = sorted({n for tool in SKILL_TOOLS if os.path.isdir(_p(st, tool))
                     for n in os.listdir(_p(st, tool))
                     if os.path.isdir(_p(st, f"{tool}/{n}")) and n not in skills})
    pruned = []
    if migrate and legacy:
        for tool in SKILL_TOOLS:
            for name in legacy:
                rel = f"{tool}/{name}"
                if os.path.isdir(_p(st, rel)):
                    plan.append({"op": "prune-skill", "dst": rel})
                    pruned.append(rel)

    # 6. skills-lock.json
    lock = {"version": 1, "source": LOCK_SOURCE, "video_studio": __version__,
            # `p` (skills/ đi cùng mã) và gốc repo có thể nằm trên hai Ổ ĐĨA khác nhau — đây
            # là phép tính đường DUY NHẤT đi giữa hai cây, nên là chỗ duy nhất cần `rel_path`.
            "skills": {n: {"path": _env.rel_path(p, _env.package_repo()),
                           "sha256": _tree_hash(p)} for n, p in sorted(skills.items())}}
    cur_lock, lock_err = _env.read_json(_p(st, LOCK_FILE))
    if not os.path.isfile(_p(st, LOCK_FILE)):
        plan.append({"op": "write", "path": LOCK_FILE, "content": _json_text(lock)})
    elif lock_err or cur_lock.get("source") != LOCK_SOURCE:
        if migrate:
            plan.append({"op": "write", "path": LOCK_FILE, "content": _json_text(lock)})
            replace_lock = True
        else:
            kept.append(f"{LOCK_FILE} (do công cụ khác ghi — giữ; --migrate để thay, bản cũ được lưu)")
    elif cur_lock != lock:
        plan.append({"op": "write", "path": LOCK_FILE, "content": _json_text(lock)})

    # 7. station.json
    data, changed = _station_json(st, mode, version, projects_rel)
    if changed:
        plan.append({"op": "write", "path": _env.STATION_FILE, "content": _json_text(data)})

    touched = {(p.get("path") or p.get("dst") or "").split("/")[0] for p in plan} | \
              {(p.get("src") or "").split("/")[0] for p in plan if p["op"] == "move"}
    untouched = sorted(n for n in (os.listdir(st) if exists else [])
                       if n not in touched and n not in ALLOWED_TOP)
    _guard(plan, extra={projects_rel.split("/")[0]} | ws_extra)
    return {"plan": plan, "notes": notes, "kept": kept, "legacy_skills": legacy,
            "pruned_skills": sorted(pruned), "untouched": untouched,
            "replace_lock": replace_lock, "station_json": data}


def _guard(plan, extra=()):
    """Chặn lỗi lập trình: kế hoạch chỉ được chạm tên nằm trong ALLOWED_TOP."""
    allowed = ALLOWED_TOP | set(extra)
    for p in plan:
        for key in ("path", "dst", "src"):
            if key == "src" and p["op"] != "move":
                continue                    # src của copy/skill/seed ở NGOÀI trạm (repo, trạm giọng)
            rel = p.get(key)
            if rel is None or rel == ".":
                continue
            top = rel.split("/")[0]
            if top not in allowed:
                raise AssertionError(f"kế hoạch chạm '{rel}' — ngoài danh sách cho phép của engine")


# ── thi hành có nhật ký ────────────────────────────────────────────────────────────────

def _move_tree(src, dst):
    """Dời thư mục an toàn. Cùng ổ: `os.rename` — hỏng thì hỏng SẠCH, không đụng gì.
    Khác ổ: chép → đối chiếu sha256 từng file → mới xoá nguồn."""
    try:
        os.rename(src, dst)
        return
    except OSError as e:
        cross = e.errno == errno.EXDEV or getattr(e, "winerror", None) == 17
        if not cross:
            raise ContractError(f"không dời được {src} → {dst} ({e}). Có thể một chương trình "
                                "đang mở file trong trạm (preview, trình duyệt, render) — đóng nó rồi "
                                "chạy lại.")
    shutil.copytree(src, dst)
    for rel in _files(src):
        a, b = os.path.join(src, *rel.split("/")), os.path.join(dst, *rel.split("/"))
        if not os.path.isfile(b) or _sha256(a) != _sha256(b):
            raise ContractError(f"chép sang {dst} không khớp ở {rel} — nguồn giữ nguyên.")
    shutil.rmtree(src)


class _Run:
    """Một lần init: ghi nhật ký sau MỖI thao tác, để lỗi giữa chừng hay `--undo` đều đảo được."""

    def __init__(self, st):
        self.st = st
        self.id = datetime.datetime.now().strftime("%Y%m%d-%H%M%S-%f")
        self.dir = _p(st, f"{RUNS_DIR}/{self.id}")
        self.ops = []

    def _save(self, status="running"):
        os.makedirs(self.dir, exist_ok=True)
        with open(os.path.join(self.dir, "journal.json"), "w", encoding="utf-8", newline="\n") as f:
            f.write(_json_text({"id": self.id, "status": status, "video_studio": __version__,
                                "ops": self.ops}))

    def record(self, op):
        self.ops.append(op)
        self._save()

    def backup(self, rel):
        """Dời thứ sắp bị thay vào prev/ (cùng ổ ⇒ rename)."""
        dst = os.path.join(self.dir, "prev", *rel.split("/"))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        src = _p(self.st, rel)
        if os.path.isdir(src):
            _move_tree(src, dst)
        else:
            os.replace(src, dst)
        return os.path.relpath(dst, self.st).replace(os.sep, "/")

    # thao tác nguyên tử + nhật ký
    def mkdir(self, rel):
        """Tạo thư mục, ghi nhật ký TỪNG cấp còn thiếu (để hoàn tác gỡ đúng, không sót cha)."""
        if rel == ".":
            if not os.path.isdir(self.st):
                os.makedirs(self.st)
                self.record({"op": "mkdir", "path": "."})
            return
        parts = rel.split("/")
        for i in range(1, len(parts) + 1):
            sub = "/".join(parts[:i])
            if not os.path.isdir(_p(self.st, sub)):
                os.mkdir(_p(self.st, sub))
                self.record({"op": "mkdir", "path": sub})

    def ensure_dirs(self, rel_file):
        """Tạo thư mục cha còn thiếu của một file."""
        parent = "/".join(rel_file.split("/")[:-1])
        if parent:
            self.mkdir(parent)

    def move(self, src, dst):
        self.ensure_dirs(dst)
        _move_tree(_p(self.st, src), _p(self.st, dst))
        self.record({"op": "move", "src": src, "dst": dst})

    def write(self, rel, content):
        path = _p(self.st, rel)
        backup = self.backup(rel) if os.path.exists(path) else None
        self.ensure_dirs(rel)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
        self.record({"op": "write", "path": rel, "backup": backup, "sha256": _sha256(path)})

    def copy_file(self, src_file, rel, transform=None):
        path = _p(self.st, rel)
        self.ensure_dirs(rel)
        if transform:
            with open(src_file, "r", encoding="utf-8") as f:
                text = transform(f.read())
            with open(path, "w", encoding="utf-8", newline="\n") as f:
                f.write(text)
        else:
            shutil.copyfile(src_file, path)
        self.record({"op": "create", "path": rel, "sha256": _sha256(path)})

    def finish(self, status):
        self._save(status)


def _apply(run, p):
    st = run.st
    op = p["op"]
    if op == "mkdir":
        run.mkdir(p["path"])
    elif op == "move":
        run.move(p["src"], p["dst"])
    elif op == "pin":
        with open(_p(st, p["path"]), "r", encoding="utf-8") as f:
            text = f.read()
        run.write(p["path"], _pin_text(text, p["to"]))
    elif op == "write":
        run.write(p["path"], p["content"])
    elif op in ("copy", "seed"):
        run.mkdir(p["dst"])
        for rel in p["files"]:
            tf = None
            if op == "seed" and rel == "package.json":
                tf = lambda t, v=p["pin"]: _pin_text(t, v)      # noqa: E731
            run.copy_file(os.path.join(p["src"], *rel.split("/")), f"{p['dst']}/{rel}", tf)
        if op == "copy":                    # giữ cả thư mục rỗng của nguồn (vd fillers/data/)
            for dp, dn, _fn in os.walk(p["src"]):
                for d in dn:
                    r = os.path.relpath(os.path.join(dp, d), p["src"]).replace(os.sep, "/")
                    run.mkdir(f"{p['dst']}/{r}")
    elif op == "workspace":
        for rel in p["files"]:
            run.copy_file(os.path.join(p["src"], *rel.split("/")), rel)
    elif op == "prune-skill":
        # Không xoá thẳng: dời vào prev/ của nhật ký, để `--undo` trả lại nguyên vẹn.
        b = run.backup(p["dst"])
        run.record({"op": "move", "src": p["dst"], "dst": b})
    elif op == "skill":
        if p["action"] == "replace":
            b = run.backup(p["dst"])
            run.record({"op": "move", "src": p["dst"], "dst": b})
        run.mkdir(p["dst"])
        for rel in _files(p["src"]):
            run.copy_file(os.path.join(p["src"], *rel.split("/")), f"{p['dst']}/{rel}")
    else:                                   # pragma: no cover
        raise AssertionError(op)


def _undo_ops(st, ops, dry_run=False):
    """Đảo danh sách thao tác (ngược thứ tự). -> (số thao tác đã đảo, danh sách giữ lại)."""
    done, kept = 0, []
    for op in reversed(ops):
        kind = op["op"]
        if kind == "mkdir":
            path = st if op["path"] == "." else _p(st, op["path"])
            if op["path"] == ".":
                continue                    # gốc trạm còn chứa .video-studio/ (nhật ký) — giữ
            if os.path.isdir(path) and not os.listdir(path):
                if not dry_run:
                    os.rmdir(path)
                done += 1
            elif os.path.isdir(path):
                kept.append(f"{op['path']}/ (không rỗng — giữ)")
        elif kind == "move":
            src, dst = _p(st, op["src"]), _p(st, op["dst"])
            if os.path.exists(dst) and not os.path.exists(src):
                if not dry_run:
                    os.makedirs(os.path.dirname(src), exist_ok=True)
                    _move_tree(dst, src)
                done += 1
            else:
                kept.append(f"{op['dst']} (không dời về {op['src']} được — một bên đã đổi)")
        elif kind in ("create", "write"):
            path = _p(st, op["path"])
            if os.path.isfile(path) and _sha256(path) != op["sha256"]:
                kept.append(f"{op['path']} (đã sửa sau init — giữ)")
                if kind == "write" and op.get("backup"):
                    kept.append(f"{op['backup']} (bản trước init của {op['path']} — còn nguyên)")
                continue
            if not dry_run:
                if os.path.isfile(path):
                    os.remove(path)
                if kind == "write" and op.get("backup"):
                    os.replace(_p(st, op["backup"]), path)
            done += 1
    return done, kept


def _clean_prev(run_dir):
    """Gỡ các thư mục rỗng còn lại trong prev/ sau khi đã trả bản cũ về chỗ."""
    prev = os.path.join(run_dir, "prev")
    for dp, dn, fn in sorted(os.walk(prev, topdown=False), key=lambda x: -len(x[0])):
        if not os.listdir(dp):
            os.rmdir(dp)


def _execute(st, plan):
    run = _Run(st)
    try:
        for p in plan:
            _apply(run, p)
    except Exception as exc:
        _done, kept = _undo_ops(st, run.ops)
        _clean_prev(run.dir)
        run.finish("rolled-back")
        msg = f"{exc} — đã hoàn tác phần đã làm"
        if kept:
            msg += "; còn giữ: " + ", ".join(kept)
        if isinstance(exc, contract.VideoStudioError):
            raise exc.__class__(msg) from exc
        raise contract.EngineError(msg) from exc
    run.finish("done")
    return run


# ── init / undo ────────────────────────────────────────────────────────────────────────

def _hook_text():
    py = sys.executable.replace("\\", "/")
    return ("#!/bin/sh\n"
            "# video-studio: chan commit du lieu tram (workspace/), .env, studio.local.json,\n"
            "# file media va chuoi giong token. Cai boi `video-studio init` (che do embedded).\n"
            f"exec \"{py}\" -m video_studio.precommit\n")


def copy_env(repo):
    """`embedded`: dọn sẵn `<repo>/.env` từ `.env.example`. -> 'created' | 'kept' | 'no-example'.

    Không có bước này thì "clone là chạy" chỉ đúng một nửa: `.env` được `_env.env()` đọc,
    được `.gitignore` chặn, được hook chặn lần nữa, được `doctor` kiểm — nhưng không ai tạo
    ra nó, nên người dùng phải tự biết là phải chép. Không bao giờ đè file đã điền: chạy lại
    bộ cài không được ăn mất cấu hình của người ta.
    """
    src = os.path.join(repo, _env.ENV_EXAMPLE)
    dst = os.path.join(repo, _env.ENV_FILE)
    if os.path.exists(dst):
        return "kept"
    if not os.path.isfile(src):
        return "no-example"
    shutil.copyfile(src, dst)
    if os.name != "nt":
        try:
            os.chmod(dst, 0o600)
        except OSError as e:               # hệ tệp không hỗ trợ (exFAT, chia sẻ mạng)
            contract.log(f"[init] không đặt được quyền 600 cho .env ({e}) — kiểm tay.")
    return "created"


def install_hook(repo):
    """Cài hook pre-commit cho chế độ embedded. -> 'installed' | 'kept' | 'no-git'.

    Không bao giờ đè hook sẵn có: hook của người ta có thể đang làm việc khác, và một cổng
    an toàn không được phép là thứ phá mất cổng an toàn khác.
    """
    hooks = os.path.join(repo, ".git", "hooks")
    if not os.path.isdir(hooks):
        return "no-git"
    hook = os.path.join(hooks, "pre-commit")
    if os.path.exists(hook):
        return "kept"
    with open(hook, "w", encoding="utf-8", newline="\n") as f:
        f.write(_hook_text())
    try:
        os.chmod(hook, 0o755)
    except OSError:
        pass
    return "installed"


def do_init(station=None, mode=None, yes=False, migrate=False, dry_run=False, ask=None,
            non_interactive=False):
    mode, st, why = choose_mode(station=station, mode=mode, yes=yes, ask=ask,
                                non_interactive=non_interactive)
    if migrate and mode != "separate":
        raise ContractError("--migrate chỉ dùng để nhận một trạm ngoài đã có (separate): "
                            "truyền --station DIR")
    version = _env.hyperframes_version(st)
    pl = build_plan(st, mode, migrate, version)
    res = {"mode": mode, "station": st, "reason": why, "dry_run": bool(dry_run),
           "migrate": bool(migrate), "hyperframes_version": version,
           "plan": [{k: v for k, v in p.items() if k not in ("content", "files")} |
                    ({"files": len(p["files"])} if "files" in p else {}) for p in pl["plan"]],
           "notes": pl["notes"], "kept": pl["kept"], "legacy_skills": pl["legacy_skills"],
           "pruned_skills": pl["pruned_skills"], "untouched": pl["untouched"]}
    if dry_run:
        return res
    # Phần TRẠM có thể rỗng (chạy lại trên một trạm đã đúng chuẩn), nhưng phần REPO thì
    # không được bỏ qua vì thế: `studio.local.json`, `.env` và hook là những thứ người dùng
    # xoá nhầm hoặc chưa bao giờ có, và "chạy lại bộ cài" phải là đường sửa cho chúng.
    if pl["plan"]:
        run = _execute(st, pl["plan"])
        res["run_id"] = run.id
    repo = _env.repo_root()
    if repo and os.path.isdir(repo):
        local_path = os.path.join(repo, _env.LOCAL_CONFIG)
        local = _env.read_json(local_path)[0]
        local.update({
            "mode": mode,
            "station_path": _env.WORKSPACE if mode == "embedded" else st,
            "secrets": _env.ENV_FILE if mode == "embedded" else SECRET_STORE,
        })
        with open(local_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(_json_text(local))
        if mode == "embedded":
            # Sau khi studio.local.json đã khai `mode: embedded` — trước đó `_env.env_file()`
            # còn trả None và một `.env` vừa chép ra sẽ không được ai đọc.
            res["env"] = copy_env(repo)
            res["hook"] = install_hook(repo)
    return res


def _runs(st):
    root = _p(st, RUNS_DIR)
    if not os.path.isdir(root):
        return []
    out = []
    for rid in sorted(os.listdir(root)):
        j, err = _env.read_json(os.path.join(root, rid, "journal.json"))
        if j and not err:
            out.append((rid, j))
    return out


def do_undo(station=None, dry_run=False):
    st = _env._expand(station) if station else _env.station_dir()
    todo = [(rid, j) for rid, j in _runs(st) if j.get("status") == "done"]
    if not todo:
        raise ContractError(f"không có lần init nào để hoàn tác ở {st}")
    rid, j = todo[-1]
    done, kept = _undo_ops(st, j.get("ops") or [], dry_run=dry_run)
    if not dry_run:
        run_dir = _p(st, f"{RUNS_DIR}/{rid}")
        _clean_prev(run_dir)
        j["status"] = "undone"
        j["undone_at"] = datetime.datetime.now().isoformat(timespec="seconds")
        with open(os.path.join(run_dir, "journal.json"), "w", encoding="utf-8", newline="\n") as f:
            f.write(_json_text(j))
    return {"station": st, "run_id": rid, "dry_run": bool(dry_run), "undone": done, "kept": kept}


# ── in cho người đọc ───────────────────────────────────────────────────────────────────

def _describe(p):
    op = p["op"]
    if op == "mkdir":
        return "tạo thư mục trạm" if p["path"] == "." else f"tạo {p['path']}/"
    if op == "move":
        return f"dời {p['src']}/ → {p['dst']}/"
    if op == "pin":
        return f"ghim {p['path']}: hyperframes@{','.join(p['from'])} → @{p['to']}"
    if op == "copy":
        return f"chép {p['files']} file filler từ trạm giọng → {p['dst']}/"
    if op == "seed":
        return f"dựng {p['dst']}/ từ seed của repo ({p['files']} file)"
    if op == "workspace":
        return f"dựng cây mẫu của trạm mới ({p['files']} file: README, project ví dụ, brand mẫu)"
    if op == "prune-skill":
        return f"gỡ skill đời cũ {p['dst']}/ (không có trong repo; bản cũ lưu lại, --undo trả về)"
    if op == "skill":
        return ("thay" if p["action"] == "replace" else "thêm") + f" skill {p['dst']}/ (từ repo)"
    if op == "write":
        return f"ghi {p['path']}"
    return op


def _print_init(res):
    log = contract.log
    tag = "(xem trước — chưa ghi gì) " if res["dry_run"] else ""
    log(f"[init] {tag}chế độ: {res['mode']} · trạm: {res['station']}")
    log(f"[init] lý do: {res['reason']} · HyperFrames {res['hyperframes_version']}")
    if not res["plan"]:
        log("[init] trạm đã đúng chuẩn — không có gì phải làm")
    for p in res["plan"]:
        log(("  • " if res["dry_run"] else "  + ") + _describe(p))
    for k in res["kept"]:
        log(f"  = giữ: {k}")
    if res["untouched"]:
        log("  = không đụng: " + ", ".join(res["untouched"]))
    if res["legacy_skills"]:
        if res.get("pruned_skills"):
            log("  - skill đời cũ được gỡ (không có trong repo): " + ", ".join(res["legacy_skills"]))
        else:
            log("  = skill không có trong repo (để nguyên; --migrate để gỡ): "
                + ", ".join(res["legacy_skills"]))
    for n in res["notes"]:
        log(f"  ! {n}")
    if res.get("env") == "created":
        log("  + .env (từ .env.example)")
    if not res["dry_run"] and res["plan"]:
        log(f"[init] xong — hoàn tác: video-studio init --station \"{res['station']}\" --undo")
    if not res["dry_run"]:
        if res["mode"] == "separate":
            log(f"\nNên đặt biến cho lịch chạy thấy trạm: VIDEO_STATION={res['station']}")
            log(f"Bí mật để ở kho secret của máy ({SECRET_STORE}); biến chỉ giữ ĐƯỜNG DẪN.")
        else:
            log("\nĐiền biến của bạn vào <repo>/.env (chỉ đường dẫn + cấu hình, KHÔNG token).")


# ── backup / migrate / update ──────────────────────────────────────────────────────────

def backup_files(st):
    """File sẽ vào gói backup: cả trạm TRỪ nháp, cache, nhật ký init, venv và cây git."""
    out = []
    for dp, dn, fn in os.walk(st):
        rel_dir = os.path.relpath(dp, st).replace(os.sep, "/")
        dn[:] = [d for d in sorted(dn) if d not in BACKUP_SKIP_DIRS
                 and not (rel_dir == "." and d in BACKUP_SKIP_TOP)]
        for n in sorted(fn):
            full = os.path.join(dp, n)
            rel = os.path.relpath(full, st).replace(os.sep, "/")
            out.append((full, rel))
    return out


def backup(out_path, station=None):
    """Zip cả trạm (trừ nháp/cache/venv). -> dict."""
    st = _env._expand(station) if station else _env.station_dir()
    if not os.path.isdir(st):
        raise StationMissing(f"không có trạm video: {st}")
    files = backup_files(st)
    out_path = _env._expand(out_path)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    manifest = {"kind": "backup", "contract": API_VERSION, "station": st,
                "created": datetime.datetime.now().isoformat(timespec="seconds"),
                "video_studio": __version__, "files": [rel for _f, rel in files]}
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("manifest.json", _json_text(manifest))
        for full, rel in files:
            z.write(full, "station/" + rel)
    return {"out": out_path, "files": manifest["files"], "station": st,
            "bytes": os.path.getsize(out_path)}


def personal_files(st, include=()):
    """File "của riêng người dùng": `projects/*/assets/**` + các thư mục gốc được gọi tên.

    Cố ý KHÔNG đoán: gói cá nhân chỉ gồm tài sản của project và đúng những thư mục người dùng
    kể ra bằng `--include`. Đoán hộ ở đây nghĩa là hoặc bỏ sót thứ họ cần, hoặc gói kèm thư mục
    của khách hàng vào một file zip rồi gửi đi máy khác.
    """
    out, missing = [], []
    projects_rel = str((_env.read_json(os.path.join(st, _env.STATION_FILE))[0] or {})
                       .get("projects_dir") or "projects").replace("\\", "/").strip("/")
    roots = []
    pdir = _p(st, projects_rel)
    for name in sorted(os.listdir(pdir) if os.path.isdir(pdir) else []):
        assets = f"{projects_rel}/{name}/assets"
        if os.path.isdir(_p(st, assets)):
            roots.append(assets)
    for name in include:
        rel = name.replace("\\", "/").strip("/")
        if os.path.isabs(rel) or ".." in rel.split("/"):
            raise ContractError(f"--include phải là tên bên trong trạm: {name}")
        if os.path.isdir(_p(st, rel)):
            roots.append(rel)
        else:
            missing.append(rel)
    if missing:
        raise ContractError("không có trong trạm: " + ", ".join(missing))
    for rel_root in roots:
        base = _p(st, rel_root)
        for dp, dn, fn in os.walk(base):
            dn[:] = [d for d in sorted(dn) if d not in BACKUP_SKIP_DIRS]
            for n in sorted(fn):
                full = os.path.join(dp, n)
                out.append((full, os.path.relpath(full, st).replace(os.sep, "/")))
    return sorted(set(out))


def export(out_path, station=None, personal=False, include=()):
    """Đóng gói trạm (hoặc chỉ phần cá nhân) thành một zip mang theo manifest. -> dict."""
    st = _env._expand(station) if station else _env.station_dir()
    if not os.path.isdir(st):
        raise StationMissing(f"không có trạm video: {st}")
    files = personal_files(st, include) if personal else backup_files(st)
    out_path = _env._expand(out_path)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    manifest = {"kind": "export", "personal": bool(personal), "contract": API_VERSION,
                "station": st, "include": sorted(include),
                "created": datetime.datetime.now().isoformat(timespec="seconds"),
                "video_studio": __version__, "files": [rel for _f, rel in files]}
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("manifest.json", _json_text(manifest))
        for full, rel in files:
            z.write(full, "station/" + rel)
    return {"out": out_path, "station": st, "personal": bool(personal),
            "files": manifest["files"], "bytes": os.path.getsize(out_path)}


def _safe_member(name):
    """Tên file trong zip → đường tương đối trong trạm, hoặc None nếu không phải nội dung trạm.

    Chặn zip-slip: tuyệt đối, `..`, ổ đĩa Windows, và mọi thứ không nằm dưới `station/`.
    """
    if name.endswith("/"):
        return None
    name = name.replace("\\", "/")
    if not name.startswith("station/"):
        return None
    rel = name[len("station/"):]
    if not rel or rel.startswith("/") or ":" in rel.split("/")[0] or ".." in rel.split("/"):
        raise ContractError(f"gói chứa đường dẫn không an toàn: {name}")
    return rel


def import_pack(in_path, station=None, overwrite=False, dry_run=False):
    """Bung một gói `export` vào trạm. Mặc định KHÔNG đè: file đã có thì bỏ qua và báo tên."""
    in_path = _env._expand(in_path)
    if not os.path.isfile(in_path):
        raise ContractError(f"không thấy gói: {in_path}")
    st = _env._expand(station) if station else _env.station_dir()
    with zipfile.ZipFile(in_path) as z:
        names = z.namelist()
        if "manifest.json" not in names:
            raise ContractError("gói không có manifest.json — không phải gói của video-studio")
        man = json.loads(z.read("manifest.json").decode("utf-8"))
        if man.get("kind") not in ("export", "backup"):
            raise ContractError(f"loại gói lạ: {man.get('kind')!r}")
        want, got = API_VERSION.split(".")[0], str(man.get("contract", "")).split(".")[0]
        if want != got:
            raise ContractError(f"gói theo hợp đồng {man.get('contract')}, bản này {API_VERSION} — "
                                "khác phiên bản lớn, không bung tự động")
        plan, skipped = [], []
        for n in names:
            rel = _safe_member(n)
            if rel is None:
                continue
            exists = os.path.exists(_p(st, rel))
            if exists and not overwrite:
                skipped.append(rel)
            else:
                plan.append((n, rel, exists))
        res = {"pack": in_path, "station": st, "dry_run": bool(dry_run),
               "kind": man.get("kind"), "personal": bool(man.get("personal")),
               "written": [rel for _n, rel, _e in plan],
               "replaced": [rel for _n, rel, e in plan if e], "skipped": sorted(skipped)}
        if dry_run:
            return res
        for n, rel, _e in plan:
            dst = _p(st, rel)
            os.makedirs(os.path.dirname(dst) or st, exist_ok=True)
            with z.open(n) as fh, open(dst, "wb") as out:
                shutil.copyfileobj(fh, out)
    return res


def _move_file(src, dst):
    """Dời MỘT file. Cùng ổ: `os.rename`. Khác ổ: chép → đối chiếu sha256 → mới xoá nguồn."""
    try:
        os.rename(src, dst)
    except OSError:
        shutil.copy2(src, dst)
        if _sha256(src) != _sha256(dst):
            os.remove(dst)
            raise ContractError(f"chép {src} → {dst} không khớp; giữ nguyên nguồn")
        os.remove(src)


def migrate_to_separate(target=None):
    """Chuyển trạm `embedded` (<repo>/workspace/) ra ngoài repo.

    Kiểm mọi điều kiện TRƯỚC khi dời byte nào: đích phải trống, repo phải đang ở chế độ
    embedded. Dời bằng `os.rename` khi cùng ổ (hỏng thì hỏng sạch), khác ổ thì chép → đối
    chiếu sha256 → mới xoá nguồn.
    """
    repo = _env.repo_root()
    if not repo:
        raise ContractError("không xác định được repo (cài -e từ bản clone, hoặc đặt "
                            "VIDEO_STUDIO_REPO)")
    ws = os.path.join(repo, _env.WORKSPACE)
    if not os.path.isdir(ws):
        raise ContractError(f"không có {ws} — máy này không ở chế độ embedded")
    target = _env._expand(target) if target else _env.default_station()
    if os.path.exists(target) and os.listdir(target):
        raise ContractError(f"thư mục đích không rỗng: {target} — chọn chỗ khác (--station)")
    # `.env` phải đi theo, và phải được kiểm TRƯỚC khi dời byte nào. Bỏ nó lại trong repo là
    # kiểu hỏng tệ nhất: file vẫn nằm đó, vẫn đọc được bằng mắt, nhưng `_env.env()` thôi
    # không nạp nó nữa (chế độ đã là `separate`) — cấu hình ngừng có tác dụng trong im lặng.
    env_file = os.path.join(repo, _env.ENV_FILE)
    sec = os.path.join(os.path.expanduser("~"), ".secret", SECRET_DIR_NAME)
    moved_env = os.path.join(sec, _env.ENV_FILE) if os.path.isfile(env_file) else None
    if moved_env and os.path.exists(moved_env):
        raise ContractError(f"{moved_env} đã có — gộp tay rồi xoá {env_file}, sau đó chạy lại")
    if os.path.isdir(target):
        os.rmdir(target)
    os.makedirs(os.path.dirname(target) or ".", exist_ok=True)
    _move_tree(ws, target)
    if moved_env:
        os.makedirs(sec, exist_ok=True)
        _move_file(env_file, moved_env)
    local_path = os.path.join(repo, _env.LOCAL_CONFIG)
    local = _env.read_json(local_path)[0]
    local.update({"mode": "separate", "station_path": target, "secrets": SECRET_STORE})
    with open(local_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(_json_text(local))
    sj = os.path.join(target, _env.STATION_FILE)
    info, err = _env.read_json(sj)
    if info and not err:
        info["mode"] = "separate"
        with open(sj, "w", encoding="utf-8", newline="\n") as f:
            f.write(_json_text(info))
    return {"mode": "separate", "station": target, "env_moved_to": moved_env}


def update():
    """`git pull --ff-only` trên bản clone. Không bao giờ `clean`, không bao giờ xoá gì."""
    repo = _env.repo_root()
    if not repo or not os.path.isdir(os.path.join(repo, ".git")):
        raise ContractError("không thấy bản clone git của repo — `update` chỉ chạy trên bản clone")
    r = subprocess.run(["git", "-C", repo, "pull", "--ff-only"], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=300)
    if r.returncode != 0:
        raise contract.EngineError(
            "git pull --ff-only không chạy được (sửa đổi cục bộ, hay nhánh đã lệch?). Không "
            "xoá gì; xử lý tay rồi chạy lại.\n" + (r.stderr or r.stdout).strip())
    return {"repo": repo, "output": (r.stdout or "").strip()}


def backup_main(argv=None):
    ap = argparse.ArgumentParser(prog="video-studio backup",
                                 description="Zip cả trạm (trừ nháp, cache, venv, cây git).")
    ap.add_argument("--out", required=True, help="file .zip sẽ ghi ra")
    ap.add_argument("--station", help="trạm khác trạm đang phân giải")
    ap.add_argument("--json", action="store_true")
    args, code = contract.parse(ap, argv)
    if args is None:
        return code

    def fn(a):
        res = backup(a.out, a.station)
        contract.log(f"[backup] {len(res['files'])} file → {res['out']} "
                     f"({res['bytes'] / (1024 * 1024):.1f} MB)")
        return res
    return contract.run(fn, args, args.json)


def export_main(argv=None):
    ap = argparse.ArgumentParser(
        prog="video-studio export",
        description="Đóng gói trạm thành zip. --personal: chỉ tài sản của project "
                    "(projects/*/assets) cộng các thư mục gốc kể tên bằng --include.")
    ap.add_argument("--out", required=True, help="file .zip sẽ ghi ra")
    ap.add_argument("--personal", action="store_true", help="chỉ phần dữ liệu cá nhân")
    ap.add_argument("--include", action="append", default=[], metavar="TÊN",
                    help="thêm một thư mục ở gốc trạm vào gói cá nhân (lặp lại được)")
    ap.add_argument("--station", help="trạm khác trạm đang phân giải")
    ap.add_argument("--json", action="store_true")
    args, code = contract.parse(ap, argv)
    if args is None:
        return code

    def fn(a):
        if a.include and not a.personal:
            raise ContractError("--include chỉ có nghĩa cùng --personal (gói đầy đủ đã có tất cả)")
        res = export(a.out, a.station, personal=a.personal, include=a.include)
        contract.log(f"[export] {'cá nhân' if res['personal'] else 'cả trạm'}: "
                     f"{len(res['files'])} file → {res['out']} "
                     f"({res['bytes'] / (1024 * 1024):.1f} MB)")
        return res
    return contract.run(fn, args, args.json)


def import_main(argv=None):
    ap = argparse.ArgumentParser(
        prog="video-studio import",
        description="Bung gói export vào trạm. Mặc định KHÔNG đè file đã có.")
    ap.add_argument("--in", dest="pack", required=True, help="file .zip của `export`")
    ap.add_argument("--station", help="trạm khác trạm đang phân giải")
    ap.add_argument("--overwrite", action="store_true", help="cho phép đè file đã có")
    ap.add_argument("--dry-run", action="store_true", help="chỉ in kế hoạch, không ghi")
    ap.add_argument("--json", action="store_true")
    args, code = contract.parse(ap, argv)
    if args is None:
        return code

    def fn(a):
        res = import_pack(a.pack, a.station, overwrite=a.overwrite, dry_run=a.dry_run)
        tag = "(xem trước — chưa ghi gì) " if res["dry_run"] else ""
        contract.log(f"[import] {tag}{len(res['written'])} file vào {res['station']}"
                     + (f" · đè {len(res['replaced'])}" if res["replaced"] else ""))
        if res["skipped"]:
            contract.log(f"  = bỏ qua {len(res['skipped'])} file đã có "
                         "(dùng --overwrite nếu muốn đè): " + ", ".join(res["skipped"][:5])
                         + (" …" if len(res["skipped"]) > 5 else ""))
        return res
    return contract.run(fn, args, args.json)


def migrate_main(argv=None):
    ap = argparse.ArgumentParser(prog="video-studio migrate",
                                 description="Chuyển trạm embedded (workspace/) ra ngoài repo.")
    ap.add_argument("--to", required=True, choices=["separate"])
    ap.add_argument("--station", help="đích (mặc định ~/.video)")
    ap.add_argument("--json", action="store_true")
    args, code = contract.parse(ap, argv)
    if args is None:
        return code

    def fn(a):
        res = migrate_to_separate(a.station)
        contract.log(f"[migrate] trạm giờ ở {res['station']} — đặt VIDEO_STATION trỏ vào đó "
                     "để mọi công cụ khác thấy")
        return res
    return contract.run(fn, args, args.json)


def update_main(argv=None):
    ap = argparse.ArgumentParser(prog="video-studio update",
                                 description="Cập nhật repo: git pull --ff-only. Không xoá gì.")
    ap.add_argument("--json", action="store_true")
    args, code = contract.parse(ap, argv)
    if args is None:
        return code

    def fn(a):
        res = update()
        contract.log(res["output"] or "[update] đã mới nhất")
        return res
    return contract.run(fn, args, args.json)


def init_main(argv=None):
    ap = argparse.ArgumentParser(
        prog="video-studio init",
        description="Dựng trạm video + station.json; --migrate nhận trạm đời cũ. Không cài Node, "
                    "không gọi npx, không tải gì.")
    ap.add_argument("--station", help="trạm ngoài repo (chọn separate, không hỏi)")
    ap.add_argument("--mode", choices=MODES, help="chọn chế độ không cần hỏi")
    ap.add_argument("--yes", action="store_true", help="nhận khuyến nghị (embedded) không hỏi")
    ap.add_argument("--non-interactive", action="store_true",
                    help="không có ai trả lời: KHÔNG hỏi và KHÔNG đoán — thiếu "
                         "--yes/--mode/--station thì dừng với mã 2")
    ap.add_argument("--migrate", action="store_true",
                    help="di trú bố cục cũ: news/, topstory/ → projects/, ghim HyperFrames, "
                         "chép filler, thay skill cũ khác repo và GỠ skill đời cũ không có trong "
                         "repo (bản cũ đều lưu lại, --undo trả về)")
    ap.add_argument("--undo", action="store_true", help="đảo lần init gần nhất theo nhật ký")
    ap.add_argument("--dry-run", action="store_true", help="chỉ in kế hoạch, không ghi")
    ap.add_argument("--json", action="store_true")
    args, code = contract.parse(ap, argv)
    if args is None:
        return code

    def fn(a):
        if a.undo:
            if a.migrate or a.mode or a.yes:
                raise ContractError("--undo không đi cùng --migrate/--mode/--yes")
            res = do_undo(a.station, dry_run=a.dry_run)
            tag = "(xem trước) " if res["dry_run"] else ""
            contract.log(f"[init --undo] {tag}lần {res['run_id']}: đảo {res['undone']} thao tác")
            for k in res["kept"]:
                contract.log(f"  = giữ: {k}")
            return res
        res = do_init(station=a.station, mode=a.mode, yes=a.yes, migrate=a.migrate,
                      dry_run=a.dry_run, non_interactive=a.non_interactive)
        _print_init(res)
        return res
    return contract.run(fn, args, args.json)
