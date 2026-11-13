"""spec_audit.py — `reference audit --spec FILE`: spec/EDL không được trỏ tệp ngoài `assets/`.

`audit --project` chỉ nhìn thư mục tài sản nên spec của `render` hay EDL của `edit` trỏ thẳng
`source/reference.*` thì lọt. Ở đây mọi chuỗi trong JSON (mọi template, không cần hiểu lược đồ) mà là
đường tệp CÓ THẬT phải nằm trong `assets/` của project hoặc template của repo.

An toàn: chỉ `stat`/`realpath`; KHÔNG mở tệp đích (chỉ mở chính spec). So sánh bằng `realpath` nên `..`,
đường tuyệt đối và liên kết mềm trỏ ra ngoài đều bị bắt. Chuỗi không phải đường (URL, chữ thường,
có NUL, quá dài), thư mục, và tệp không tồn tại bị bỏ qua.
"""
import json
import os

from ..contract import ContractError

MAX_SPEC_BYTES = 5 * 1024 * 1024
MAX_STRING = 1024
MAX_STRINGS = 200000

_PKG = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO_TEMPLATE_DIRS = tuple(d for d in (os.path.join(_PKG, "templates"),
                                       os.path.join(os.path.dirname(_PKG), "templates"))
                           if os.path.isdir(d))


def _strings(node, pointer=""):
    """(chuỗi, con trỏ JSON) của mọi giá trị chuỗi; lặp bằng stack để spec lồng sâu không tràn đệ quy."""
    stack = [(node, pointer)]
    while stack:
        cur, ptr = stack.pop()
        if isinstance(cur, str):
            yield cur, ptr or "/"
        elif isinstance(cur, dict):
            stack.extend((v, f"{ptr}/{k}") for k, v in reversed(list(cur.items())))
        elif isinstance(cur, list):
            stack.extend((v, f"{ptr}/{i}") for i, v in reversed(list(enumerate(cur))))


def _inside(root, path):
    try:
        return os.path.commonpath([os.path.normcase(root), os.path.normcase(path)]) == os.path.normcase(root)
    except ValueError:      # khác ổ đĩa trên Windows
        return False


def _candidates(value, bases):
    if os.path.isabs(value):
        return [value]
    return [os.path.join(b, value) for b in bases]


def audit_spec(spec_path, project_dir, assets_dir=None):
    """`{"ok", "checked", "findings": [{"path", "problem"}]}`; `checked` = số chuỗi là tệp có thật."""
    if not os.path.isfile(spec_path):
        raise ContractError(f"--spec không phải tệp: {spec_path}")
    project = os.path.abspath(project_dir)
    assets = os.path.abspath(assets_dir or os.path.join(project, "assets"))
    if not _inside(os.path.realpath(project), os.path.realpath(assets)):
        raise ContractError(f"thư mục tài sản {assets} phải nằm trong project {project_dir}")
    if os.path.getsize(spec_path) > MAX_SPEC_BYTES:
        raise ContractError(f"spec lớn hơn {MAX_SPEC_BYTES} byte: {spec_path}")
    try:
        with open(spec_path, encoding="utf-8-sig") as f:
            data = json.load(f)
    except (OSError, ValueError) as exc:
        raise ContractError(f"--spec không đọc được như JSON: {exc}") from None

    roots = [os.path.realpath(assets), *(os.path.realpath(d) for d in REPO_TEMPLATE_DIRS)]
    bases = [os.path.dirname(os.path.abspath(spec_path)), project]
    findings, checked = [], 0
    for n, (value, ptr) in enumerate(_strings(data)):
        if n >= MAX_STRINGS:
            raise ContractError(f"spec có hơn {MAX_STRINGS} chuỗi")
        if not value.strip() or len(value) > MAX_STRING or "\x00" in value or "\n" in value or "://" in value \
                or value.lower().startswith("data:"):
            continue
        hit = None
        for cand in _candidates(value, bases):
            try:
                if os.path.isfile(cand) or os.path.islink(cand):
                    hit = cand
                    break
            except (OSError, ValueError):
                continue
        if hit is None:
            continue
        checked += 1
        real = os.path.realpath(hit)
        if any(_inside(r, real) for r in roots):
            continue
        link = os.path.islink(hit) or os.path.normcase(real) != os.path.normcase(os.path.abspath(hit))
        why = "liên kết mềm trỏ ra ngoài" if link and any(_inside(r, os.path.abspath(hit)) for r in roots) \
            else "tệp nằm ngoài assets/ và template của repo"
        findings.append({"path": value, "problem": f"{ptr}: {why}"})
    return {"ok": not findings, "checked": checked, "findings": findings}
