"""`video-studio doctor`: mọi lệnh ngoài (node, npx, npm) và `which` là GIẢ — test không gọi
mạng, không cần Node/ffmpeg thật, và kiểm được đúng argv mà doctor sẽ chạy."""
import datetime
import json
import subprocess

import pytest

from video_studio import doctor
from video_studio.cli import main as cli_main
from conftest import last_json


def _days_ago(n):
    """Mốc ISO kiểu npm trả về, cách đây n ngày."""
    t = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=n, hours=1)
    return t.strftime("%Y-%m-%dT%H:%M:%S.000Z")


class FakeProc:
    def __init__(self, rc=0, out="", err=""):
        self.returncode, self.stdout, self.stderr = rc, out, err


class Machine:
    """Máy giả: bảng công cụ có trên PATH + kịch bản trả lời cho từng lệnh."""

    def __init__(self, tools=("node", "npx", "npm", "ffmpeg", "ffprobe"), node="v24.12.0",
                 hf_doctor_rc=0, npm_latest="0.8.51", npm_time=_days_ago(3)):
        self.tools = set(tools)
        self.node, self.hf_doctor_rc, self.npm_latest = node, hf_doctor_rc, npm_latest
        self.npm_time = npm_time          # ngày phát hành của bản ĐANG GHIM (chuỗi ISO / None)
        self.calls = []

    def which(self, name, path=None):
        return f"/fake/bin/{name}" if name in self.tools else None

    def run(self, argv, **kw):
        self.calls.append((list(argv), kw))
        assert isinstance(argv, list), "argv phải là list"
        assert not kw.get("shell"), "cấm shell=True"
        exe = argv[0].rsplit("/", 1)[-1]
        if exe == "node":
            return FakeProc(0, self.node + "\n")
        if exe == "npx":
            return FakeProc(self.hf_doctor_rc, "ok" if self.hf_doctor_rc == 0 else "",
                            "" if self.hf_doctor_rc == 0 else "missing chrome")
        if exe == "npm":
            if "time" in argv:
                # npm trả CẢ bảng version -> ngày phát hành (JSON), không trả một dòng.
                table = {"0.7.90": _days_ago(400)}
                if self.npm_time is not None:
                    table["0.7.94"] = self.npm_time
                return FakeProc(0, json.dumps(table))
            return FakeProc(0, self.npm_latest + "\n")
        raise AssertionError(f"lệnh lạ: {argv}")


@pytest.fixture
def machine(monkeypatch):
    m = Machine()
    monkeypatch.setattr(doctor._env.shutil, "which", m.which)
    monkeypatch.setattr(doctor, "_run", lambda argv, timeout=60: m.run(argv, timeout=timeout))
    return m


@pytest.fixture
def good_station(tmp_path, monkeypatch):
    st = tmp_path / "st"
    st.mkdir()
    (st / "station.json").write_text(json.dumps({"contract": "1.0.0", "hyperframes_version": "0.7.94"}),
                                     encoding="utf-8")
    monkeypatch.setenv("VIDEO_STATION", str(st))
    cache = tmp_path / "home" / ".cache" / "hyperframes"
    (cache / "chrome" / "chrome-headless-shell" / "win64-152.0.7928.2").mkdir(parents=True)
    (cache / "fonts" / "inter").mkdir(parents=True)
    return st


def run(argv, capsys):
    rc = cli_main(["doctor", *argv])
    out = capsys.readouterr()
    return rc, out.out, out.err


def _check(res, name):
    return next(c for c in res["checks"] if c["name"] == name)


def test_all_good_is_code_0(machine, good_station, capsys):
    rc, out, err = run(["--json"], capsys)
    assert rc == 0, err
    res = last_json(out)
    assert res["ok"] is True and res["errors"] == []
    assert res["hyperframes"] == "0.7.94"
    for name in ("node", "npx", "hyperframes-doctor", "ffmpeg", "ffprobe", "station", "chromium", "font"):
        assert _check(res, name)["ok"], name


def test_hyperframes_doctor_uses_pinned_version_no_shell(machine, good_station, capsys):
    run([], capsys)
    npx_calls = [a for a, _ in machine.calls if a[0].endswith("npx")]
    assert npx_calls == [["/fake/bin/npx", "--yes", "hyperframes@0.7.94", "doctor"]]


def test_hf_flag_overrides_version(machine, good_station, capsys):
    rc, out, _ = run(["--hf", "0.8.51", "--json"], capsys)
    assert last_json(out)["hyperframes"] == "0.8.51"
    assert ["/fake/bin/npx", "--yes", "hyperframes@0.8.51", "doctor"] in [a for a, _ in machine.calls]


def test_hf_flag_rejects_floating_tag(machine, good_station, capsys):
    rc, _, _ = run(["--hf", "latest"], capsys)
    assert rc == 2


def test_missing_node_is_code_3_with_install_hint(machine, good_station, capsys):
    machine.tools -= {"node", "npx", "npm"}
    rc, out, err = run(["--json"], capsys)
    assert rc == 3
    res = last_json(out)
    assert "node" in res["errors"] and "npx" in res["errors"]
    assert "nodejs.org" in err or "brew install node" in err or "winget" in err
    assert not any(a[0].endswith("npx") for a, _ in machine.calls)


def test_old_node_is_code_3(machine, good_station, capsys):
    machine.node = "v20.11.1"
    rc, out, _ = run(["--json"], capsys)
    assert rc == 3 and "node" in last_json(out)["errors"]


def test_missing_ffmpeg_is_code_3(machine, good_station, capsys):
    machine.tools -= {"ffmpeg"}
    rc, out, _ = run(["--json"], capsys)
    assert rc == 3 and "ffmpeg" in last_json(out)["errors"]


def test_missing_station_is_code_3(machine, tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("VIDEO_STATION", str(tmp_path / "nope"))
    rc, out, err = run(["--json"], capsys)
    assert rc == 3 and "station" in last_json(out)["errors"]
    assert "video-studio init" in err


def test_legacy_station_without_station_json_warns_migrate(machine, tmp_path, monkeypatch, capsys):
    st = tmp_path / "old"
    (st / "demo").mkdir(parents=True)
    (st / "demo" / "hyperframes.json").write_text("{}", encoding="utf-8")
    monkeypatch.setenv("VIDEO_STATION", str(st))
    rc, out, _ = run(["--json"], capsys)
    c = _check(last_json(out), "station-json")
    assert c["level"] == "warn" and "--migrate" in c["hint"] and "--station" in c["hint"]


@pytest.mark.filterwarnings("ignore::DeprecationWarning")
def test_video_root_legacy_name_warns(machine, good_station, monkeypatch, capsys):
    monkeypatch.delenv("VIDEO_STATION")
    monkeypatch.setenv("VIDEO_ROOT", str(good_station))
    rc, out, _ = run(["--json"], capsys)
    assert rc == 0
    assert "env-name" in last_json(out)["warnings"]


def test_hyperframes_doctor_failure_is_warning_not_error(machine, good_station, capsys):
    machine.hf_doctor_rc = 1
    rc, out, _ = run(["--json"], capsys)
    assert rc == 0
    assert "hyperframes-doctor" in last_json(out)["warnings"]


def test_no_chromium_suggests_browser_ensure(machine, good_station, tmp_path, capsys):
    import shutil
    shutil.rmtree(tmp_path / "home" / ".cache" / "hyperframes" / "chrome")
    rc, out, _ = run(["--json"], capsys)
    c = _check(last_json(out), "chromium")
    assert c["level"] == "warn" and "hyperframes@0.7.94 browser ensure" in c["hint"]


def test_known_version_needs_matching_chromium(machine, good_station, capsys):
    rc, out, _ = run(["--hf", "0.8.51", "--json"], capsys)
    c = _check(last_json(out), "chromium")
    assert c["level"] == "warn" and "152.0.7977.30" in c["hint"]


def test_offline_never_calls_npx_or_npm(machine, good_station, capsys):
    rc, out, _ = run(["--offline", "--check-updates", "--json"], capsys)
    assert rc == 0
    assert not any(a[0].endswith(("npx", "npm")) for a, _ in machine.calls)
    assert _check(last_json(out), "hyperframes-doctor")["level"] == "skip"


def test_check_updates_reports_minor_gap_only_reports(machine, good_station, capsys):
    rc, out, err = run(["--check-updates", "--json"], capsys)
    assert rc == 0
    res = last_json(out)
    upd = res["updates"]
    assert upd["pinned"] == "0.7.94" and upd["latest"] == "0.8.51" and upd["behind"] == "minor"
    assert "hyperframes-update" in res["warnings"]
    assert ["/fake/bin/npm", "view", "hyperframes", "version"] in [a for a, _ in machine.calls]
    # chỉ báo: station.json không đổi
    assert json.loads((good_station / "station.json").read_text(encoding="utf-8"))[
        "hyperframes_version"] == "0.7.94"


def test_check_updates_patch_gap_on_a_fresh_pin_is_not_a_warning(machine, good_station, capsys):
    """Nhịp phát hành ~1,5 bản/ngày: lệch patch trên bản ghim còn mới chỉ được GHI NHẬN."""
    machine.npm_latest = "0.7.99"
    rc, out, _ = run(["--check-updates", "--json"], capsys)
    res = last_json(out)
    assert res["updates"]["behind"] == "patch"
    assert res["updates"]["pinned_age_days"] == 3
    assert "hyperframes-update" not in res["warnings"]


def test_check_updates_warns_when_the_pin_is_older_than_the_age_threshold(machine, good_station,
                                                                          capsys):
    """Lệch patch nhưng bản ghim đã quá 30 ngày ⇒ cảnh báo: lâu rồi không ai nhìn lại bản ghim."""
    machine.npm_latest = "0.7.99"
    machine.npm_time = _days_ago(doctor.PIN_MAX_AGE_DAYS + 5)
    rc, out, _ = run(["--check-updates", "--json"], capsys)
    res = last_json(out)
    assert rc == 0                                   # cảnh báo, không chặn
    assert res["updates"]["behind"] == "patch"
    assert res["updates"]["pinned_age_days"] == doctor.PIN_MAX_AGE_DAYS + 5
    assert "hyperframes-update" in res["warnings"]
    assert f"quá {doctor.PIN_MAX_AGE_DAYS} ngày" in _check(res, "hyperframes-update")["hint"]


def test_a_stale_pin_that_is_already_the_latest_is_not_told_to_upgrade_to_itself(
        machine, good_station, capsys):
    """Bản ghim == bản mới nhất + quá hạn xem lại: cảnh báo về HẠN, không phải về bản mới.

    Câu cũ ghi "có bản {latest} — nâng…" với `latest == pinned`, tức khuyên nâng lên chính
    bản đang chạy. Không ca test nào phủ nhánh `behind is None` + stale nên nó sống sót.
    """
    machine.npm_latest = "0.7.94"                    # đúng bản đang ghim
    machine.npm_time = _days_ago(doctor.PIN_MAX_AGE_DAYS + 5)
    rc, out, _ = run(["--check-updates", "--json"], capsys)
    res = last_json(out)
    assert rc == 0
    assert res["updates"]["behind"] is None and res["updates"]["latest"] == "0.7.94"
    assert "hyperframes-update" in res["warnings"]
    hint = _check(res, "hyperframes-update")["hint"]
    assert "đang LÀ bản mới nhất" in hint
    assert "nâng là việc CÓ CHỦ ĐÍCH" not in hint    # không khuyên nâng lên chính nó
    assert f"{doctor.PIN_MAX_AGE_DAYS + 5} ngày" in hint


def test_check_updates_stays_quiet_right_at_the_age_threshold(machine, good_station, capsys):
    """Đúng ngưỡng vẫn im — cổng là 'quá 30 ngày', không phải 'tròn 30 ngày'."""
    machine.npm_latest = "0.7.99"
    machine.npm_time = _days_ago(doctor.PIN_MAX_AGE_DAYS)
    rc, out, _ = run(["--check-updates", "--json"], capsys)
    res = last_json(out)
    assert res["updates"]["pinned_age_days"] == doctor.PIN_MAX_AGE_DAYS
    assert "hyperframes-update" not in res["warnings"]


def test_check_updates_asks_npm_for_the_whole_publish_time_table(machine, good_station, capsys):
    """Hỏi `time` rồi tra bản ghim — `npm view <gói> time.<bản>` trả RỖNG với mã 0 vì npm đọc
    dấu chấm là đường dẫn lồng nhau, và một cổng tin vào nó sẽ luôn thấy 'không rõ tuổi'."""
    run(["--check-updates", "--json"], capsys)
    argvs = [a for a, _ in machine.calls]
    assert ["/fake/bin/npm", "view", "hyperframes", "time", "--json"] in argvs
    assert not any(any(str(x).startswith("time.") for x in a) for a in argvs)


def test_unknown_publish_date_is_not_treated_as_fresh_nor_as_stale(machine, good_station, capsys):
    """npm không có ngày của bản đang ghim ⇒ tuổi là None, cổng lùi về mỗi luật lệch bản."""
    machine.npm_latest = "0.7.99"
    machine.npm_time = None
    rc, out, _ = run(["--check-updates", "--json"], capsys)
    res = last_json(out)
    assert res["updates"]["pinned_age_days"] is None
    assert "hyperframes-update" not in res["warnings"]


def test_offline_check_updates_reports_no_age(machine, good_station, capsys):
    rc, out, _ = run(["--check-updates", "--offline", "--json"], capsys)
    res = last_json(out)
    assert res["updates"] == {"pinned": "0.7.94", "latest": None, "behind": None,
                              "pinned_age_days": None}
    assert not any(a[0].endswith("npm") for a, _ in machine.calls)


def test_two_sources_is_red(machine, good_station, tmp_path, monkeypatch, capsys):
    repo = tmp_path / "repo"
    (repo / "video_studio").mkdir(parents=True)
    (repo / "pyproject.toml").write_text("", encoding="utf-8")
    (repo / "workspace").mkdir()
    monkeypatch.setenv("VIDEO_STUDIO_REPO", str(repo))
    rc, out, _ = run(["--json"], capsys)
    assert rc == 3 and "two-sources" in last_json(out)["errors"]


def test_optional_parts_only_warn(machine, good_station, capsys):
    rc, out, _ = run(["--json"], capsys)
    res = last_json(out)
    assert _check(res, "video-use")["level"] in ("ok", "warn")
    assert _check(res, "voice-studio")["level"] in ("ok", "warn")


def test_real_run_helper_is_list_argv_no_shell(monkeypatch):
    seen = {}

    def fake_run(argv, **kw):
        seen["argv"], seen["kw"] = argv, kw
        return FakeProc(0, "v24.0.0")
    monkeypatch.setattr(subprocess, "run", fake_run)
    doctor._run(["node", "--version"])
    assert isinstance(seen["argv"], list) and seen["kw"].get("shell") in (None, False)
    assert seen["kw"]["timeout"] > 0


# ── hai lớp rào của chế độ embedded (F17) ───────────────────────────────────────────────

def _embedded_repo(tmp_path, monkeypatch, with_git=True):
    repo = tmp_path / "repo"
    (repo / "video_studio").mkdir(parents=True)
    (repo / "pyproject.toml").write_text("", encoding="utf-8")
    (repo / "workspace").mkdir()
    if with_git:
        (repo / ".git" / "hooks").mkdir(parents=True)
    monkeypatch.setenv("VIDEO_STUDIO_REPO", str(repo))
    return repo


def test_gitignore_check_is_skipped_before_git_init(tmp_path, monkeypatch):
    _embedded_repo(tmp_path, monkeypatch, with_git=False)
    checks = {c["name"]: c for c in doctor.embedded_guard_checks()}
    assert checks["gitignore"]["level"] == "skip"


def test_gitignore_check_asks_git_not_the_file(tmp_path, monkeypatch):
    """Phải hỏi `git check-ignore`: một dòng `!` phía dưới có thể mở lại thứ đã chặn phía trên."""
    _embedded_repo(tmp_path, monkeypatch)
    monkeypatch.setattr(doctor.shutil, "which", lambda n: "/fake/bin/git")
    asked = []

    def fake_run(argv, timeout=None):
        asked.append(argv[-1])
        return FakeProc(0)

    monkeypatch.setattr(doctor, "_run", fake_run)
    checks = {c["name"]: c for c in doctor.embedded_guard_checks()}
    assert asked == list(doctor.IGNORE_MUST)
    assert checks["gitignore"]["ok"] is True


def test_a_leaking_gitignore_is_red_and_names_the_path(tmp_path, monkeypatch):
    _embedded_repo(tmp_path, monkeypatch)
    monkeypatch.setattr(doctor.shutil, "which", lambda n: "/fake/bin/git")
    monkeypatch.setattr(doctor, "_run",
                        lambda argv, timeout=None: FakeProc(1 if argv[-1] == ".env" else 0))
    checks = {c["name"]: c for c in doctor.embedded_guard_checks()}
    assert checks["gitignore"]["ok"] is False
    assert checks["gitignore"]["level"] == "error"
    assert ".env" in checks["gitignore"]["detail"]


def test_a_missing_pre_commit_hook_only_warns(tmp_path, monkeypatch):
    _embedded_repo(tmp_path, monkeypatch)
    monkeypatch.setattr(doctor.shutil, "which", lambda n: "/fake/bin/git")
    monkeypatch.setattr(doctor, "_run", lambda argv, timeout=None: FakeProc(0))
    checks = {c["name"]: c for c in doctor.embedded_guard_checks()}
    assert checks["pre-commit"]["ok"] is False and checks["pre-commit"]["level"] == "warn"


def test_separate_mode_has_no_embedded_checks(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    (repo / "video_studio").mkdir(parents=True)
    (repo / "pyproject.toml").write_text("", encoding="utf-8")
    monkeypatch.setenv("VIDEO_STUDIO_REPO", str(repo))
    assert doctor.embedded_guard_checks() == []
