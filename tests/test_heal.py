"""Cổng P1-25: `video-studio probe --heal` — gói chẩn đoán + thang tự chữa trước khi bắt khởi động lại.

Mac mini 02/10/2026: render kẹt, khởi động lại là hết, và sau đó không còn chứng cứ nào để tìm
nguyên nhân. Bốn thứ phải đúng:

* kẹt ⇒ chụp gói chẩn đoán TRƯỚC khi chữa (chữa xong là mất hiện trường), không lọt secret;
* thang: giết bộ dựng MỒ CÔI (không đụng lượt dựng còn cha) → xoá profile tạm cũ → chờ → thử lại;
* qua ở lần nào thì mã 0 và nói rõ đã tự chữa; hết thang mới `RENDER_STUCK` + đường gói;
* hỏng kiểu khác `RENDER_STUCK` thì KHÔNG chạy thang (thang chữa máy kẹt, không chữa cài đặt).

Không Node, không tiến trình thật: probe, `ps`, kill và sleep đều là hàm giả.
"""
import json
import os
import time

import pytest

from conftest import last_json
from video_studio import contract, heal, probe
from video_studio.contract import EngineError, StationMissing

STUCK_ERR = f"{probe.STUCK}: môi trường render kẹt — khởi động lại máy rồi chạy lại\nđuôi log"
OK = {"seconds": 2.8, "hyperframes": "0.8.54"}


class Probe:
    """Chuỗi kết quả lần lượt: "ok" | "stuck" | "fail"."""

    def __init__(self, *seq):
        self.seq, self.calls = list(seq), 0

    def __call__(self, timeout):
        r = self.seq[min(self.calls, len(self.seq) - 1)]
        self.calls += 1
        if r == "stuck":
            e = EngineError(STUCK_ERR)
            e.output = "page.goto: Navigation timeout of 60000 ms exceeded"
            raise e
        if r == "fail":
            raise StationMissing("thiếu npx")
        return dict(OK)


PROCS = [
    {"pid": 1, "ppid": 0, "name": "launchd", "cmd": "/sbin/launchd"},
    # mồ côi: Chrome của HyperFrames bị bỏ lại khi cha chết, kèm một helper con của nó
    {"pid": 500, "ppid": 1, "name": "chrome-headless-shell",
     "cmd": "/x/chrome-headless-shell --user-data-dir=/tmp/puppeteer_dev_chrome_profile-a"},
    {"pid": 501, "ppid": 500, "name": "chrome-headless-shell",
     "cmd": "/x/chrome-headless-shell --type=renderer"},
    # còn cha: một lượt dựng khác đang chạy thật — KHÔNG được đụng
    {"pid": 600, "ppid": 77, "name": "node", "cmd": "node /n/hyperframes render -o out.mp4"},
    {"pid": 77, "ppid": 1, "name": "pwsh", "cmd": "pwsh -File run.ps1 --api-key=SECRET123456789"},
    # mồ côi nhưng không phải bộ dựng
    {"pid": 700, "ppid": 1, "name": "ollama", "cmd": "ollama serve"},
]


@pytest.fixture
def quiet(monkeypatch, tmp_path):
    """Không `ps` thật, không kill thật, không sleep thật, thư mục tạm riêng."""
    monkeypatch.setattr(heal, "list_processes", lambda run=None: [dict(p) for p in PROCS])
    monkeypatch.setattr(heal, "_NT", False)          # PROCS mang hình POSIX (ppid 1 = mồ côi)
    killed, slept, logs = [], [], []
    tmp = tmp_path / "tmp"
    tmp.mkdir()

    def run(argv, **kw):
        class R:
            returncode = 0
            stdout = b"TOKEN=abc123 1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZ012345\n"
            stderr = b""
        return R()

    kw = dict(diag_dir=str(tmp_path / "render-stuck"), sleep=slept.append, run=run,
              kill=killed.append, tmpdir=str(tmp), log=logs.append)
    return kw, killed, slept, logs, tmp


# ── thang ──────────────────────────────────────────────────────────────────────────────

def test_healthy_probe_takes_no_snapshot_and_no_action(quiet, tmp_path):
    kw, killed, slept, logs, _ = quiet
    res = heal.ladder(Probe("ok"), 30, **kw)
    assert res["heal"] is None and res["seconds"] == 2.8
    assert killed == [] and slept == []
    assert not (tmp_path / "render-stuck").exists(), "máy khoẻ thì không chụp gì"


def test_stuck_then_recovers_after_first_wait(quiet):
    kw, killed, slept, logs, _ = quiet
    pr = Probe("stuck", "ok")
    res = heal.ladder(pr, 30, **kw)
    assert pr.calls == 2 and slept == [60]
    h = res["heal"]
    assert h["recovered"] is True and h["step"] == 2
    assert os.path.isdir(h["diag"]), "gói chẩn đoán phải chụp TRƯỚC khi chữa"
    assert killed == [500, 501], "giết mồ côi + cây con, không đụng lượt dựng còn cha"
    assert "RENDER_HEAL=recovered step=2" in logs
    assert any(l.startswith("RENDER_DIAG=") for l in logs)


def test_stuck_to_the_end_raises_with_diag_and_reboot_hint(quiet):
    kw, killed, slept, logs, _ = quiet
    pr = Probe("stuck")
    with pytest.raises(EngineError) as e:
        heal.ladder(pr, 30, **kw)
    assert pr.calls == 3 and slept == [60, 600], "thang mặc định: 60 s rồi 600 s"
    msg = str(e.value)
    assert msg.startswith(probe.STUCK + ":") and "khởi động lại máy" in msg
    assert e.value.diag in msg and os.path.isdir(e.value.diag)
    assert "RENDER_HEAL=failed steps=3" in logs


def test_other_failure_first_runs_no_ladder(quiet, tmp_path):
    kw, killed, slept, logs, _ = quiet
    with pytest.raises(StationMissing):
        heal.ladder(Probe("fail"), 30, **kw)
    assert killed == [] and slept == []
    assert not (tmp_path / "render-stuck").exists()


def test_other_failure_mid_ladder_is_raised_as_is(quiet):
    kw, *_ = quiet
    with pytest.raises(StationMissing):
        heal.ladder(Probe("stuck", "fail"), 30, **kw)


def test_custom_waits_are_used(quiet):
    kw, _, slept, *_ = quiet
    kw["waits"] = (1, 1)
    with pytest.raises(EngineError):
        heal.ladder(Probe("stuck"), 1, **kw)
    assert slept == [1, 1]


# ── mồ côi ─────────────────────────────────────────────────────────────────────────────

def test_find_orphans_posix_ppid_1_only_render_processes():
    ra = heal.find_orphans(PROCS, self_pid=99999, nt=False)
    assert [p["pid"] for p in ra] == [500, 501]


def test_find_orphans_windows_parent_gone():
    procs = [
        {"pid": 10, "ppid": 4, "name": "explorer.exe", "cmd": ""},
        {"pid": 20, "ppid": 3333, "name": "chrome-headless-shell.exe",
         "cmd": "chrome-headless-shell.exe --headless"},       # cha 3333 đã chết
        {"pid": 21, "ppid": 20, "name": "chrome-headless-shell.exe", "cmd": "--type=gpu"},
        {"pid": 30, "ppid": 10, "name": "node.exe", "cmd": "node hyperframes render"},  # còn cha
    ]
    assert [p["pid"] for p in heal.find_orphans(procs, self_pid=1, nt=True)] == [20, 21]


def test_find_orphans_never_returns_self():
    me = [{"pid": 4242, "ppid": 1, "name": "python", "cmd": "python -m hyperframes-probe"}]
    assert heal.find_orphans(me, self_pid=4242, nt=False) == []


# ── profile tạm ────────────────────────────────────────────────────────────────────────

def test_clean_profiles_removes_only_old_matching_dirs(tmp_path):
    now = time.time()
    for name, age in [("puppeteer_dev_chrome_profile-old", 7200), ("hyperframes-abc", 7200),
                      ("video-studio-probe-x", 7200), ("puppeteer_dev_chrome_profile-new", 60),
                      ("khac-old", 7200)]:
        d = tmp_path / name
        d.mkdir()
        os.utime(d, (now - age, now - age))
    (tmp_path / "hyperframes.log").write_text("x")             # file, không phải thư mục
    xoa = heal.clean_profiles(str(tmp_path), now=now)
    assert sorted(os.path.basename(p) for p in xoa) == [
        "hyperframes-abc", "puppeteer_dev_chrome_profile-old", "video-studio-probe-x"]
    assert (tmp_path / "puppeteer_dev_chrome_profile-new").is_dir(), "profile mới = lượt đang chạy"
    assert (tmp_path / "khac-old").is_dir() and (tmp_path / "hyperframes.log").is_file()


# ── gói chẩn đoán ──────────────────────────────────────────────────────────────────────

def test_diag_bundle_has_evidence_and_no_secret(quiet, tmp_path):
    kw, *_ = quiet
    d = heal.diag_bundle(str(tmp_path / "rs"), STUCK_ERR, "Navigation timeout", run=kw["run"],
                         tmpdir=kw["tmpdir"], procs=[dict(p) for p in PROCS])
    files = sorted(os.listdir(d))
    for f in ("probe-error.txt", "ps-top-cpu.txt", "render-procs.txt", "temp-profiles.txt",
              "summary.json"):
        assert f in files
    allt = "".join(open(os.path.join(d, f), encoding="utf-8").read() for f in files)
    assert "SECRET123456789" not in allt, "dòng lệnh tiến trình không được vào gói"
    assert "abc123" not in allt and "ABCDEFGHIJKLMNOPQRSTUVWXYZ012345" not in allt, "phải che token"
    rp = open(os.path.join(d, "render-procs.txt"), encoding="utf-8").read()
    assert "2 mồ côi" in rp and "pid=500" in rp and "MO_COI" in rp
    assert json.load(open(os.path.join(d, "summary.json"), encoding="utf-8"))["orphans"] == 2


def test_che_masks_common_secret_shapes():
    s = heal._che("api_key=XYZ password: hunter2 bot 1234567:AAAAAAAAAAAAAAAAAAAAAAAA ghp_abcdefghijklmnop1234")
    assert "XYZ" not in s and "hunter2" not in s and "AAAAAAAA" not in s and "ghp_abc" not in s


# ── CLI ────────────────────────────────────────────────────────────────────────────────

def _khong_cham_may_that(monkeypatch):
    """CLI đi đường thật: chặn `ps`/`pmset`/`log show` (macOS: tới 120 s) và thư mục tạm thật."""
    def goi(root, *a, **k):
        d = os.path.join(root, "gia")
        os.makedirs(d, exist_ok=True)
        return d
    monkeypatch.setattr(heal, "diag_bundle", goi)
    monkeypatch.setattr(heal, "clean_profiles", lambda *a, **k: [])

def test_cli_heal_recovered_json_carries_heal(monkeypatch, capsys, tmp_path):
    pr = Probe("stuck", "ok")
    monkeypatch.setattr(probe, "run_probe", pr)
    monkeypatch.setattr(heal, "list_processes", lambda run=None: [])
    monkeypatch.setattr(heal.time, "sleep", lambda s: None)
    _khong_cham_may_that(monkeypatch)
    code = probe.main(["--json", "--heal", "--diag-dir", str(tmp_path), "--heal-waits", "0,0"])
    assert code == 0
    out = last_json(capsys.readouterr().out)
    assert out["ok"] is True and out["heal"]["recovered"] is True and out["heal"]["step"] == 2


def test_cli_heal_exhausted_is_code_1_with_diag(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(probe, "run_probe", Probe("stuck"))
    monkeypatch.setattr(heal, "list_processes", lambda run=None: [])
    monkeypatch.setattr(heal.time, "sleep", lambda s: None)
    _khong_cham_may_that(monkeypatch)
    code = probe.main(["--json", "--heal", "--diag-dir", str(tmp_path), "--heal-waits", "0,0"])
    assert code == contract.ENGINE_ERROR
    out = last_json(capsys.readouterr().out)
    assert out["error"].startswith(probe.STUCK) and os.path.isdir(out["diag"])


def test_cli_without_heal_json_unchanged(monkeypatch, capsys):
    monkeypatch.setattr(probe, "run_probe", lambda t: dict(OK))
    assert probe.main(["--json"]) == 0
    assert last_json(capsys.readouterr().out) == {"ok": True, **OK}


@pytest.mark.parametrize("bad", ["", "a,b", "-1,5"])
def test_cli_bad_heal_waits_is_code_2(bad, capsys):
    assert probe.main(["--json", "--heal", "--heal-waits", bad]) == contract.CONTRACT_ERROR


# ── review 04/10: PID cấp lại (Windows), dấu nhận hẹp, profile đang dùng, che token ─────

def test_windows_pid_cap_lai_KHONG_keo_explorer_vao_cay():
    """explorer.exe mang ppid 1234 của userinit đã chết; PID 1234 nay là Chrome mồ côi."""
    procs = [
        {"pid": 1234, "ppid": 9999, "name": "chrome-headless-shell.exe", "cmd": "chrome-headless-shell.exe", "tao": 500},
        {"pid": 1235, "ppid": 1234, "name": "chrome-headless-shell.exe", "cmd": "--type=gpu", "tao": 501},
        {"pid": 4000, "ppid": 1234, "name": "explorer.exe", "cmd": "explorer.exe", "tao": 100},
    ]
    assert [p["pid"] for p in heal.find_orphans(procs, self_pid=1, nt=True)] == [1234, 1235]


def test_windows_cha_sinh_SAU_con_la_mo_coi():
    procs = [
        {"pid": 50, "ppid": 1234, "name": "chrome-headless-shell.exe", "cmd": "chrome-headless-shell.exe", "tao": 100},
        {"pid": 1234, "ppid": 4, "name": "notepad.exe", "cmd": "notepad.exe", "tao": 900},  # PID cấp lại
    ]
    assert [p["pid"] for p in heal.find_orphans(procs, self_pid=1, nt=True)] == [50]


@pytest.mark.parametrize("cmd,name,la", [
    ("node /x/hyperframes/dist/cli.js render -o out.mp4", "node", True),
    ("node /x/hyperframes/dist/cli.js preview --background", "node", False),   # cố ý tách cha
    ("node -e require('hyperframes/update')", "node", False),                  # cập nhật nền
    ("/x/Chrome --remote-debugging-pipe --user-data-dir=/tmp/puppeteer_dev_chrome_profile-a", "Chrome", False),
    ("/x/chrome --headless --user-data-dir=/tmp/puppeteer_dev_chrome_profile-a", "chrome", True),
    ("/x/chrome-headless-shell --type=renderer", "chrome-headless-shell", True),
])
def test_dau_nhan_bo_dung_hep(cmd, name, la):
    assert heal._la_bo_dung({"cmd": cmd, "name": name}) is la


def test_kill_doc_lai_truoc_khi_giet_pid_doi_thi_bo(monkeypatch):
    truoc = [{"pid": 500, "ppid": 1, "name": "chrome-headless-shell", "cmd": "chrome-headless-shell", "tao": None}]
    sau = [{"pid": 500, "ppid": 1, "name": "bash", "cmd": "bash", "tao": None}]
    monkeypatch.setattr(heal, "_NT", False)
    monkeypatch.setattr(heal, "list_processes", lambda run=None, log=None: sau)
    killed = []
    assert heal.kill_orphans(truoc, kill=killed.append) == [] and killed == []


def test_profile_DANG_DUNG_hoac_co_file_moi_ben_trong_thi_giu(tmp_path):
    now = time.time()
    for name in ("puppeteer_dev_chrome_profile-dangdung", "puppeteer_dev_chrome_profile-ruot-moi",
                 "puppeteer_dev_chrome_profile-cu"):
        d = tmp_path / name
        (d / "Default").mkdir(parents=True)
        f = d / "Default" / "Cookies"
        f.write_text("x")
        tuoi = 60 if name.endswith("ruot-moi") else 7200
        os.utime(f, (now - tuoi, now - tuoi))
        os.utime(d / "Default", (now - 7200, now - 7200))
        os.utime(d, (now - 7200, now - 7200))
    procs = [{"pid": 9, "ppid": 2, "name": "chrome",
              "cmd": f"chrome --user-data-dir={tmp_path}/puppeteer_dev_chrome_profile-dangdung"}]
    xoa = heal.clean_profiles(str(tmp_path), now=now, procs=procs)
    assert [os.path.basename(p) for p in xoa] == ["puppeteer_dev_chrome_profile-cu"]


def test_che_bearer_va_json():
    s = heal._che('Authorization: Bearer abcdefghijklmnop {"access_token": "ya29.AAAAAAAAAAAAAAAAAAAA"}')
    assert "abcdefghijklmnop" not in s and "ya29.AAAA" not in s


def test_run_out_chi_lay_stdout_va_ma_khac_0_la_None():
    class R:
        def __init__(self, rc):
            self.returncode, self.stdout, self.stderr = rc, b'[{"a":1}]', b"canh bao"
    assert heal._run_out(["x"], run=lambda *a, **k: R(0)) == '[{"a":1}]'
    assert heal._run_out(["x"], run=lambda *a, **k: R(1)) is None


def test_node_exe_e_tren_windows_khong_phai_luot_dung():
    cmd = '"C:\\nodejs\\node.exe" -e fetch("posthog") hyperframes {"command":"render"}'
    assert heal._la_bo_dung({"cmd": cmd, "name": "node.exe"}) is False


def test_thang_xoa_DUNG_profile_cua_chrome_vua_giet(monkeypatch, tmp_path):
    """Review vòng 2 N1: profile nằm trong dòng lệnh của chính Chrome mồ côi vừa giết vẫn phải xoá."""
    tmp = tmp_path / "tmp"
    d = tmp / "puppeteer_dev_chrome_profile-mo-coi"
    d.mkdir(parents=True)
    cu = time.time() - 7200
    os.utime(d, (cu, cu))
    mo_coi = {"pid": 500, "ppid": 1, "name": "chrome-headless-shell", "tao": None,
              "cmd": f"chrome-headless-shell --user-data-dir={d}"}
    monkeypatch.setattr(heal, "_NT", False)
    monkeypatch.setattr(heal, "list_processes", lambda run=None, log=None: [dict(mo_coi)])
    monkeypatch.setattr(heal, "diag_bundle", lambda root, *a, **k: root)
    with pytest.raises(EngineError):
        heal.ladder(Probe("stuck"), 1, diag_dir=str(tmp_path / "rs"), waits=(0,), sleep=lambda s: None,
                    kill=lambda pid: None, tmpdir=str(tmp), log=lambda m: None)
    assert not d.exists()


# ── điểm 1 (04/10): Windows đối chiếu SID chủ tiến trình trước khi giết ──────────────────

MO_COI_WIN = [
    {"pid": 500, "ppid": 9999, "name": "chrome-headless-shell.exe", "cmd": "chrome-headless-shell.exe", "tao": 10},
    {"pid": 600, "ppid": 9998, "name": "chrome-headless-shell.exe", "cmd": "chrome-headless-shell.exe", "tao": 11},
]


def test_windows_chi_giet_tien_trinh_CUA_MINH(monkeypatch):
    """Task chạy phiên 0 thấy cả Chrome mồ côi của user khác — lọc phiên chưa đủ."""
    monkeypatch.setattr(heal, "_NT", True)
    monkeypatch.setattr(heal, "list_processes", lambda run=None, log=None: [dict(p) for p in MO_COI_WIN])
    killed, logs = [], []
    ra = heal.kill_orphans([dict(p) for p in MO_COI_WIN], kill=killed.append, log=logs.append,
                           owner=lambda pids: ("S-ME", {500: "S-ME", 600: "S-KHAC"}))
    assert killed == [500] and [p["pid"] for p in ra] == [500]
    assert any("không thuộc user này" in l for l in logs)


def test_windows_khong_doc_duoc_chu_thi_KHONG_giet_gi(monkeypatch):
    monkeypatch.setattr(heal, "_NT", True)
    monkeypatch.setattr(heal, "list_processes", lambda run=None, log=None: [dict(p) for p in MO_COI_WIN])
    killed, logs = [], []
    assert heal.kill_orphans([dict(p) for p in MO_COI_WIN], kill=killed.append, log=logs.append,
                             owner=lambda pids: (None, {})) == []
    assert killed == [] and any("KHÔNG giết" in l for l in logs)


def test_chu_so_huu_windows_bo_pid_khong_doc_duoc_va_thieu_SID_minh_thi_rong():
    me = os.getpid()
    bang = {me: "S-1", 500: "S-1", 600: "S-2"}
    assert heal.chu_so_huu_windows([500, 600, 700], sid_cua=bang.get) == ("S-1", {500: "S-1", 600: "S-2"})
    assert heal.chu_so_huu_windows([500], sid_cua={500: "S-1"}.get) == (None, {})


@pytest.mark.skipif(os.name != "nt", reason="ctypes OpenProcessToken chỉ có trên Windows")
def test_sid_that_tren_windows_nhanh_va_dung():
    t0 = time.time()
    me, sid = heal.chu_so_huu_windows([os.getpid(), 4, 999999])
    assert me and me.startswith("S-1-") and sid.get(os.getpid()) == me
    assert 999999 not in sid and sid.get(4) != me, "System / pid không tồn tại không bao giờ là của mình"
    assert time.time() - t0 < 5, "review 04/10: bản PowerShell tốn ~0,5 s mỗi tiến trình"


# ── điểm 2 (04/10): che secret ba lớp ────────────────────────────────────────────────────

@pytest.mark.parametrize("vao,lo", [
    ("{'access_token': 'vvvvvvvv'}", "vvvvvvvv"),                       # repr Python
    ("--token abcdef123 --out x.mp4", "abcdef123"),                    # cờ dòng lệnh
    ("AWS_SECRET_ACCESS_KEY=zzzzzzzz", "zzzzzzzz"),                    # khoá có tiền tố
    ("Authorization: Bearer abcdefghijkl", "abcdefghijkl"),
    ('{"access_token": "ya29.AAAAAAAAAAAAAAAAAAAA"}', "AAAAAAAAAAAA"),
    ("x-api-key: kkkkkkkk", "kkkkkkkk"),
    ("refresh_token=rrrrrrrr&x=1", "rrrrrrrr"),
    ("jwt eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.abcdefghij", "eyJhbGci"),
    ("AKIAABCDEFGHIJKLMNOP", "AKIAABCDEFGHIJKLMNOP"),
    ("cookie: sid=ssssssss", "ssssssss"),
])
def test_che_cac_dang_secret(vao, lo):
    assert lo not in heal._che(vao, bi_mat=[])


@pytest.mark.parametrize("giu", [
    "/Users/x/Library/Caches/ms-playwright/chromium-1234/chrome-headless-shell",
    "Session 257 state=1 author=Duc",
    "WindowServer: CPU 21.3% coreaudiod 14%",
])
def test_che_KHONG_lam_hong_van_ban_chan_doan_binh_thuong(giu):
    assert heal._che(giu, bi_mat=[]) == giu


def test_che_theo_GIA_TRI_bien_moi_truong():
    bm = heal.gia_tri_bi_mat({"MY_WEIRD_API_KEY": "khongcohinhdangnao99", "PATH": "/usr/bin:/bin",
                              "SHORT_TOKEN": "1"})
    assert bm == ["khongcohinhdangnao99"], "chỉ tên như secret, đủ dài; PATH không bị coi là secret"
    assert "khongcohinhdangnao99" not in heal._che("loi: khongcohinhdangnao99.", bi_mat=bm)


def test_goi_chan_doan_KHONG_chua_secret_cai_san(monkeypatch, tmp_path):
    """Kiểm cả gói: secret cài vào env, output probe và output lệnh chụp — không file nào chứa nó."""
    monkeypatch.setenv("STUDIO_FAKE_CLIENT_SECRET", "giatribimatthu42xyz")
    bi_mat = ["giatribimatthu42xyz", "tokenkieuthu77", "1234567:ABCDEFGHIJKLMNOPQRSTUV"]

    def run(argv, **kw):
        class R:
            returncode = 0
            stdout = ("pid name\n1 x --token tokenkieuthu77\nloi giatribimatthu42xyz\n").encode()
            stderr = b""
        return R()
    procs = [{"pid": 7, "ppid": 1, "name": "chrome-headless-shell",
              "cmd": "chrome-headless-shell --api-key=giatribimatthu42xyz", "tao": None}]
    d = heal.diag_bundle(str(tmp_path / "rs"), "RENDER_STUCK: x 1234567:ABCDEFGHIJKLMNOPQRSTUV",
                         "output giatribimatthu42xyz", run=run, tmpdir=str(tmp_path), procs=procs)
    for f in os.listdir(d):
        noi_dung = open(os.path.join(d, f), encoding="utf-8").read()
        for b in bi_mat:
            assert b not in noi_dung, f"{f} lọt {b}"


# ── review vòng 3 (04/10): che tuyến tính, hết lọt, không che quá tay ───────────────────

CHUOI_XAU = {
    "chu-lien": lambda: "a" * 1_000_000,
    "hex": lambda: "0123456789abcdef" * 62_500,
    "base64": lambda: ("QUJDREVGR0hJSktMTU5PUFFSU1RVVldYWVo+/" * 28_000)[:1_000_000],
    "khoa-lap": lambda: "token=" * 160_000,
    "gach": lambda: "-" * 1_000_000,
    "co-lap": lambda: "--token " * 120_000,
    "pem-lap": lambda: "-----BEGIN PRIVATE KEY-----" * 30_000,
    "gach-chu": lambda: ("--" + "a" * 38 + " ") * 25_000,
    # review vòng 4: `\b` khớp sau `-` ⇒ mỗi 4 ký tự một điểm bắt đầu (4,65 s/MB)
    "jwt-gach": lambda: "eyJ-" * 250_000,
    "sk-gach": lambda: "sk-" * 333_333,
    "telegram-lap": lambda: "1234567:" * 125_000,
    "pem-gach": lambda: "-----BEGIN PRIVATE KEY-----" + "-" * 1_000_000,
    "nhay-lap": lambda: "token='" + 'x"y' * 300_000,
    "slack-lap": lambda: "hooks.slack.com/services/" * 40_000,
}


# Tên test là KHOÁ, không phải chuỗi 1 MB: pytest đặt tên test vào biến môi trường
# PYTEST_CURRENT_TEST (Windows trần 32 767 ký tự).
@pytest.mark.parametrize("ten", sorted(CHUOI_XAU))
def test_che_TUYEN_TINH_tren_1MB(ten):
    """Bản trước quay lui bậc hai: 40 KB chữ liền mất 74 s — gói 5 MB treo `--heal`."""
    chuoi = CHUOI_XAU[ten]()
    t0 = time.time()
    heal._che(chuoi, bi_mat=[])
    assert time.time() - t0 < 5, f"{ten}: che 1 MB quá chậm"


@pytest.mark.parametrize("vao,lo", [
    ("https://user:hunter2pass@host/x", "hunter2pass"),
    ("postgres://admin:pwpwpwpw@db:5432/x", "pwpwpwpw"),
    ("password: 'my secret pass'", "secret pass"),
    ('TOKEN="abc def ghi"', "def ghi"),
    ("api_key = 'AAAA BBBB'", "BBBB"),
    ("Cookie: a=1; session=SSSSSSSS", "SSSSSSSS"),
    ("Authorization: token ghp_short", "ghp_short"),
    ("passphrase=pppppppp", "pppppppp"),
    ("auth=aaaaaaaa", "aaaaaaaa"),
    ("x-auth: xxxxxxxx", "xxxxxxxx"),
    ("token%3Dqqqqqqqq", "qqqqqqqq"),
    ("AIzaSyA1234567890abcdefghijklmnopqrstuv", "AIzaSyA1234567890"),
    ("glpat-abcdefghijklmnopqrst", "abcdefghijklmnopqrst"),
    ("npm_abcdefghijklmnopqrstuvwxyz0123456789", "abcdefghijklmnop"),
    ("-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkq\n-----END PRIVATE KEY-----", "MIIEvQIBADANBgkq"),
])
def test_che_cac_dang_review_vong_3(vao, lo):
    assert lo not in heal._che(vao, bi_mat=[])


@pytest.mark.parametrize("giu", [
    "token_count: 12345678",
    "cookie: 42",
    "author=Duc authority=x",
    "--max-old-space-size=4096",
    "PreventUserIdleSystemSleep named: \"com.apple.audio\"",
    "/Users/x/Code/agent-video-studio/video_studio/heal.py:120",
])
def test_che_KHONG_qua_tay_review_vong_3(giu):
    assert heal._che(giu, bi_mat=[]) == giu


def test_PWD_khong_bi_coi_la_secret():
    assert heal.gia_tri_bi_mat({"PWD": "/Users/x/Code/agent-video-studio",
                                "OLDPWD": "/Users/x/Code/agent-marketing"}) == []


def test_ghi_CAT_truoc_khi_che(tmp_path, monkeypatch):
    goi = []
    monkeypatch.setattr(heal, "_che", lambda t, bi_mat=None: goi.append(len(t)) or t)
    monkeypatch.setattr(heal, "TRAN_FILE", 1000)
    heal._ghi(str(tmp_path), "x.txt", "a" * 50_000)
    assert goi == [1000], "che phải chạy trên phần ĐÃ cắt, không phải toàn bộ"


# ── review vòng 4 (04/10) ────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("vao,lo", [
    ("redis://:passpassxx@host:6379", "passpassxx"),
    ("https://api.telegram.org/bot123456789:AAHabcdefghijklmnopqrstuvwxyz0123456/sendMessage",
     "AAHabcdefghijklmnopqrstuvwxyz"),
    ('{\\"password\\":\\"xxxxsecret\\"}', "xxxxsecret"),
    ("PASSWORD := xxxxsecret", "xxxxsecret"),
    ("password => 'xxxxsecret'", "xxxxsecret"),
    ("password=S3cr,etVal", "etVal"),
    ('"password": "it\'s xxxsecret"', "xxxsecret"),
    ("token='" + "z" * 1000 + "'", "z" * 20),
    ("sig=abcdEFGH1234", "abcdEFGH1234"),
    ("-----BEGIN RSA PRIVATE KEY-----\nProc-Type: 4,ENCRYPTED\nDEK-Info: AES-128-CBC,AB\n"
     "MIIEabcdefgh\n-----END RSA PRIVATE KEY-----", "MIIEabcdefgh"),
    ("hooks.slack.com/services/T000/B000/XXXXXXXXXXXX", "XXXXXXXXXXXX"),
    ("hf_abcdefghijklmnopqrstuvwx", "abcdefghijklmnop"),
    ("[token:abcd1234]", "abcd1234"),
])
def test_che_cac_dang_review_vong_4(vao, lo):
    assert lo not in heal._che(vao, bi_mat=[])


@pytest.mark.parametrize("giu", [
    "[com.apple.Authorization:authd] Succeeded authorizing right",
    "token.js:12:3",
    '"auth": true',
    "OAuth: disabled",
    "PWD=/Users/x/Code",
    "OLDPWD=/a/b/c",
])
def test_che_KHONG_qua_tay_review_vong_4(giu):
    assert heal._che(giu, bi_mat=[]) == giu


def test_cat_roi_giua_khoi_PEM_van_che_than_khoa():
    assert heal._che_duoi_pem(b"MIIEbody\n-----END PRIVATE KEY-----\nduoi") == b"<da-che>\nduoi"
    nguyen = b"-----BEGIN PRIVATE KEY-----\nMIIE\n-----END PRIVATE KEY-----"
    assert heal._che_duoi_pem(nguyen) == nguyen, "khối đủ BEGIN/END để _che lo"
