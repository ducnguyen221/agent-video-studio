"""Read lookup records from the existing, canonical video reference documents."""
from contextlib import ExitStack
import os
import re

from video_studio.contract import ContractError
from .catalog import CHECKS

FFMPEG_PATH = "skills/video-edit/references/ffmpeg-tool-index.md"
HYPIT_PATH = "skills/video-routing/references/production-techniques.md"


def _record(identifier, name, description, source, upstream, tags):
    return {
        "id": identifier, "name": name, "kind": "reference", "maturity": "reference_only",
        "rights": "unknown", "source": source, "upstream_source": upstream,
        "runtime": "Reference only; upstream is not installed by this library; runtime not verified",
        "description": description, "tags": tags, "roles": [], "techniques": tags,
        "ratios": [], "checks": dict.fromkeys(CHECKS, "not_run"),
        "checks_origin": "default_not_run", "origin": "distilled_reference",
    }


def parse_ffmpeg(document):
    """Derive tools from the upstream-name table; never treat them as local commands."""
    marker = "42 tên sau là **tên trong tài liệu nguồn**"
    end = "Tên trong bảng gợi ý"
    if document.count(marker) != 1 or document.count(end) != 1:
        raise ContractError("FFmpeg reference format changed")
    fence = None
    for line in document.splitlines():
        match = re.match(r"^\s*(`{3,}|~{3,})", line)
        if match:
            token = match.group(1)
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence):
                fence = None
        elif fence and (marker in line or end in line):
            raise ContractError("FFmpeg reference table is inside a code fence")
    after_marker = document.split(marker, 1)[1]
    if "\n" not in after_marker:
        raise ContractError("FFmpeg reference table missing")
    table = after_marker.split("\n", 1)[1].split(end, 1)[0]
    table_lines = [line.strip() for line in table.splitlines() if line.strip()]
    if len(table_lines) != 8 or table_lines[:2] != [
        "| Nhóm | Tên upstream để tra | Tình huống khai thác |", "|---|---|---|"
    ]:
        raise ContractError("FFmpeg reference table structure changed")
    links = re.findall(r"\[ffmpeg-skill, commit ([0-9a-f]{7,40})\]\((https://github\.com/kajisho5/ffmpeg-skill/tree/([0-9a-f]{40}))\)", document)
    if len(links) != 1 or not links[0][2].startswith(links[0][0]):
        raise ContractError("FFmpeg reference provenance is missing or ambiguous")
    rows = []
    groups = []
    for line in table_lines[2:]:
        if not line.startswith("| ") or not line.endswith("|"):
            raise ContractError("FFmpeg reference table row is invalid")
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != 3:
            raise ContractError("FFmpeg reference table row is invalid")
        group, tool_cell, description = cells
        names = re.findall(r"`([a-z][a-z0-9-]*)`", tool_cell)
        if not group or not description or not names:
            raise ContractError("FFmpeg reference table row is incomplete")
        if re.sub(r"`[a-z][a-z0-9-]*`|[,\s]", "", tool_cell):
            raise ContractError("FFmpeg reference tool list is invalid")
        groups.append(group)
        for name in names:
            rows.append(_record("VE-ref-ffmpeg-" + name, f"FFmpeg reference: {name}",
                                f"{group}: {description} Upstream reference only; verify local capability.",
                                FFMPEG_PATH + "#chưa-có-trong-lát-cắt-này", links[0][1], [name, group]))
    if len(groups) != 6 or len(set(groups)) != 6 or len(rows) != 42 or len({row["id"] for row in rows}) != 42:
        raise ContractError("FFmpeg reference table is incomplete or has duplicate tools")
    return rows


def parse_hypit(document):
    """Derive nine original local technique cards; upstream is provenance only."""
    outside_lines, provenance_fence = [], None
    for line in document.splitlines():
        match = re.match(r"^\s*(`{3,}|~{3,})", line)
        if match:
            token = match.group(1)
            if provenance_fence is None:
                provenance_fence = token
            elif token[0] == provenance_fence[0] and len(token) >= len(provenance_fence):
                provenance_fence = None
        elif provenance_fence is None:
            outside_lines.append(line)
    refs = set(re.findall(r"https://github\.com/hypit-ai/hypit/blob/([0-9a-f]{40})/", "\n".join(outside_lines)))
    if len(refs) != 1:
        raise ContractError("Hypit reference provenance is missing or ambiguous")
    upstream = "https://github.com/hypit-ai/hypit/tree/" + next(iter(refs))
    anchors = {}
    for match in re.finditer(r"^- \[(T[1-9]) — ([^\]]+)\]\((#[^)]+)\)$", document, re.MULTILINE):
        if match.group(1) in anchors:
            raise ContractError("Duplicate Hypit contents entry")
        anchors[match.group(1)] = (match.group(2), match.group(3))
    if len({value[1] for value in anchors.values()}) != len(anchors):
        raise ContractError("Duplicate Hypit anchor")
    rows, active, fence = [], None, None
    for line in document.splitlines():
        fence_match = re.match(r"^\s*(`{3,}|~{3,})", line)
        if fence_match:
            token = fence_match.group(1)
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence):
                fence = None
            continue
        if fence:
            continue
        heading = re.fullmatch(r"## (T\d+) — (.+)", line)
        if heading:
            if heading.group(1) not in {f"T{i}" for i in range(1, 10)}:
                raise ContractError("Unexpected Hypit card")
            if active is not None:
                raise ContractError("Hypit card is missing its use condition")
            active = heading.groups()
            continue
        if active and line.startswith("- **Dùng khi:** "):
            ident, title = active
            condition = line.removeprefix("- **Dùng khi:** ").strip()
            expected_anchor = "#" + re.sub(r"[^\w\- ]", "", (ident + " — " + title).lower()).replace(" ", "-")
            if not condition or ident not in anchors or anchors[ident] != (title, expected_anchor):
                raise ContractError("Hypit card is incomplete")
            rows.append(_record("VE-ref-hypit-" + ident.lower(), title, condition,
                                HYPIT_PATH + expected_anchor, upstream, [ident, title]))
            active = None
    if active or fence or len(rows) != 9 or {row["id"] for row in rows} != {f"VE-ref-hypit-t{i}" for i in range(1, 10)} or len(anchors) != 9:
        raise ContractError("Hypit reference cards are incomplete or duplicated")
    return rows


def load_distilled(root):
    """Read the fixed files via Windows no-reparse/no-recall handles; never fetch a URL."""
    if os.name != "nt":
        raise ContractError("Distilled references unavailable: secure local reader not verified on this platform")
    from . import _native_windows as native

    try:
        with ExitStack() as handles:
            root_handle = native.open_root(os.path.abspath(os.fspath(root)))
            handles.callback(native.close, root_handle)
            docs = []
            for relative in (FFMPEG_PATH, HYPIT_PATH):
                parent = root_handle
                parts = relative.split("/")
                for part in parts[:-1]:
                    parent = native.open_directory(parent, part)
                    handles.callback(native.close, parent)
                handle = native.open_file(parent, parts[-1])
                handles.callback(native.close, handle)
                docs.append(native.read_all(handle, limit=2 * 1024 * 1024).decode("utf-8-sig"))
            return parse_ffmpeg(docs[0]) + parse_hypit(docs[1])
    except (OSError, ValueError, UnicodeError) as exc:
        raise ContractError(f"Cannot safely read distilled references: {exc}") from exc
