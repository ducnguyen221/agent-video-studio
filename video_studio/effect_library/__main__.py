"""Offline search and explicit station capture/materialization CLI."""
import argparse
import json
import os
import sys
from contextlib import ExitStack

from video_studio.contract import ContractError
from ._native_windows import PublishedButCloseFailed
from .catalog import CHECKS, _relative, capture, materialize, materialize_repo
from .search import search
from .resources import resource_root


_SUMMARY_FIELDS = ("id", "name", "kind", "maturity", "rights", "source", "file", "origin", "runtime", "checks", "checks_origin",
    "tags", "roles", "techniques", "ratios", "description", "asset",
    "assets", "evidence", "license", "license_note", "license_url", "repository", "details",
    "prompt_text", "ratio_fit")


def _summarize_value(value, path, changes, budget, depth=0):
    def changed():
        if len(changes) < 32:
            changes.append(path[:160])
        elif len(changes) == 32:
            changes.append("additional fields truncated")
    if budget[0] <= 0:
        changed()
        return None
    budget[0] -= 1
    if isinstance(value, str):
        if len(value) > 240:
            changed()
            return value[:240]
        return value
    if isinstance(value, list):
        if depth >= 3:
            changed()
            return []
        if len(value) > 8:
            changed()
        return [_summarize_value(item, f"{path}[{i}]", changes, budget, depth + 1)
                for i, item in enumerate(value[:8])]
    if isinstance(value, dict):
        if depth >= 3:
            changed()
            return {}
        result = {}
        for index, (key, item) in enumerate(value.items()):
            if index >= 12:
                changed()
                break
            if not isinstance(key, str) or len(key) > 80:
                changed()
                continue
            result[key] = _summarize_value(item, f"{path}.{key}", changes, budget, depth + 1)
        return result
    return value


def _limit_envelope(envelope):
    """Bound the default display; ASCII escaping is a conservative byte estimate."""
    def size():
        return len(json.dumps(envelope, ensure_ascii=True, indent=4).encode("utf-8"))
    entry = envelope["entry"]
    required = {"id", "name", "kind", "rights", "source", "file", "origin", "runtime", "checks", "checks_origin"}
    if size() <= 8192:
        return envelope
    for key in reversed(_SUMMARY_FIELDS):
        if key not in required and key in entry:
            del entry[key]
            if len(envelope["omitted_fields"]) < 32:
                envelope["omitted_fields"].append(key)
            elif len(envelope["omitted_fields"]) == 32:
                envelope["omitted_fields"].append("additional fields omitted")
            if key == "prompt_text":
                envelope["prompt_text_truncated"] = True
            envelope["retrieve"] = "Repeat this search with --full-record for complete metadata; --full-prompt restores prompt_text"
            if size() <= 8192:
                return envelope
    # Extremely long essential fields: keep their names and signal truncation.
    shortened = []
    for key, value in list(entry.items()):
        if key != "id" and isinstance(value, str) and len(value) > 80:
            entry[key] = value[:80]
            shortened.append(key)
        elif key == "checks" and isinstance(value, dict):
            entry[key] = {k: v[:32] if isinstance(v, str) else None for k, v in value.items() if k in CHECKS}
            if entry[key] != value:
                shortened.append("checks")
    envelope["truncated_fields"] = shortened or ["essential fields shortened to fit compact output"]
    envelope["omitted_fields"] = ["additional metadata omitted to fit compact output"]
    envelope["retrieve"] = "Repeat this search with --full-record for complete metadata; --full-prompt restores prompt_text"
    if size() > 8192:
        raise ContractError("Cannot produce bounded search result; retry with --full-record")
    return envelope


def _unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON field")
        result[key] = value
    return result


def _invalid_constant(value):
    raise ValueError(f"invalid JSON constant: {value}")


def _manifest_in_project(project, path):
    """Read a bounded manifest through no-reparse, no-recall Windows handles."""
    if os.name != "nt":
        raise ContractError("Manifest reading unavailable: secure reads not verified on this platform")
    parts = _relative(path).parts
    if "/".join(parts) != path:
        raise ContractError("Unsafe relative path")
    from . import _native_windows as native
    with ExitStack() as handles:
        root = native.open_root(os.path.abspath(project))
        handles.callback(native.close, root)
        for part in parts[:-1]:
            root = native.open_directory(root, part)
            handles.callback(native.close, root)
        handle = native.open_file(root, parts[-1])
        handles.callback(native.close, handle)
        raw = native.read_all(handle, limit=1024 * 1024)
    obj = json.loads(raw.decode("utf-8-sig"), object_pairs_hook=_unique_pairs, parse_constant=_invalid_constant)
    if not isinstance(obj, dict):
        raise ValueError("manifest must be a JSON object")
    return obj


def _write_result(payload):
    try:
        if sys.stdout is None:
            raise OSError("standard output is unavailable")
        print(json.dumps(payload, ensure_ascii=False), flush=True)
    except (OSError, ValueError, UnicodeError):
        # The write has already completed. Do not claim rollback or invite a retry.
        try:
            print("Operation completed, but reporting the result failed.", file=sys.stderr)
        except (OSError, ValueError, UnicodeError):
            pass
        try:
            with open(os.devnull, "w") as sink:
                os.dup2(sink.fileno(), sys.stdout.fileno())
        except (OSError, ValueError, AttributeError):
            pass
        return 3
    return 0


def _action(argv):
    parser = argparse.ArgumentParser(description="Capture or materialize an explicit station entry")
    commands = parser.add_subparsers(dest="action", required=True)
    save = commands.add_parser("capture")
    save.add_argument("--project", required=True)
    save.add_argument("--station", required=True)
    save.add_argument("--manifest", required=True, help="UTF-8 JSON path relative to project")
    restore = commands.add_parser("materialize")
    restore.add_argument("--project", required=True)
    restore.add_argument("--station", required=True)
    restore.add_argument("--id", required=True)
    restore.add_argument("--name", required=True)
    restore_repo = commands.add_parser("materialize-repo")
    restore_repo.add_argument("--project", required=True)
    restore_repo.add_argument("--id", required=True)
    restore_repo.add_argument("--name", required=True)
    args = parser.parse_args(argv)
    try:
        if args.action == "capture":
            manifest = _manifest_in_project(args.project, args.manifest)
            identifier = capture(args.project, args.station, manifest)
        elif args.action == "materialize":
            identifier = args.id
            materialize(args.station, identifier, args.project, args.name)
        else:
            identifier = args.id
            materialize_repo(identifier, args.project, args.name)
    except PublishedButCloseFailed:
        try:
            print("Entry published, but finalization failed; verify the station or destination before retrying.", file=sys.stderr)
        except (OSError, ValueError, UnicodeError):
            pass
        return 3
    except (ContractError, OSError, ValueError, KeyError, UnicodeError, RecursionError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    return _write_result({"operation": args.action, "id": identifier})


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        try:
            if hasattr(stream, "reconfigure"):
                stream.reconfigure(encoding="utf-8")
        except (OSError, ValueError, UnicodeError):
            try:
                if sys.stderr is not None:
                    print("Cannot configure output streams; no action performed.", file=sys.stderr)
            except (OSError, ValueError, UnicodeError):
                pass
            return 2
    argv = sys.argv[1:] if argv is None else argv
    if argv and argv[0] in {"capture", "materialize", "materialize-repo"}:
        return _action(argv)
    parser = argparse.ArgumentParser(
        description="Search video effects and Prompt Motion offline",
        epilog=("Actions: capture --help; materialize --help; materialize-repo --help. "
                "Action status 3 means the operation completed but finalization or reporting failed; "
                "verify the station or destination before retrying."),
    )
    parser.add_argument("--q", default="")
    parser.add_argument("--full-prompt", action="store_true",
                        help="Return complete prompt_text instead of the 240-character preview")
    parser.add_argument("--full-record", action="store_true",
                        help="Return complete records, including full prompts and additional metadata")
    parser.add_argument("--station")
    parser.add_argument("--pm-index")
    parser.add_argument("--repo-entries")
    parser.add_argument("--no-distilled", action="store_true", help="Search only other sources; omit distilled references")
    for flag in ("kind", "maturity", "rights", "role", "technique", "ratio"):
        parser.add_argument("--" + flag)
    parser.add_argument("--runtime", help="Match whole tokens in runtime metadata; does not verify installation")
    parser.add_argument("--include-unknown-ratio", action="store_true",
                        help="Include records with unknown ratio; requires --ratio")
    parser.add_argument("--check", action="append", default=[], metavar="NAME=STATE",
                        help="Filter a check (not_run, pass, fail); may be repeated")
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args(argv)
    filters = {key: getattr(args, key) for key in ("kind", "maturity", "rights", "role", "technique", "ratio") if getattr(args, key)}
    if args.runtime is not None:
        filters["runtime"] = args.runtime
    try:
        for item in args.check:
            name, sep, state = item.partition("=")
            key = f"check.{name}"
            if not sep or name not in CHECKS or state not in {"not_run", "pass", "fail"} or key in filters:
                raise ContractError("Invalid or duplicate evidence filter")
            filters[key] = state
        root = resource_root() if not args.pm_index or not args.repo_entries or not args.no_distilled else None
        pm = args.pm_index or root / "skills/video-theme-library/assets/prompt-motion/index.json"
        repo = args.repo_entries or root / "skills/video-theme-library/assets/effect-library/entries.json"
        if args.no_distilled:
            print("Warning: distilled references omitted from search.", file=sys.stderr)
        elif os.name != "nt":
            print("Warning: FFmpeg and Hypit distilled references omitted; search results are incomplete because the secure reader is not verified on this platform.", file=sys.stderr)
        results = search(args.q, filters, station=args.station, repo_entries=repo, pm_index=pm, limit=args.limit,
                         distilled_root=root if not args.no_distilled and os.name == "nt" else None,
                         include_unknown_ratio=args.include_unknown_ratio)
    except (ContractError, OSError, ValueError, KeyError) as exc:
        print(str(exc), file=sys.stderr)
        return 2
    formatted = []
    for result in results:
        prompt = result.get("prompt_text")
        changes = []
        omitted = []
        if not args.full_record:
            if isinstance(result.get("id"), str) and len(result["id"]) > 240:
                print("Entry ID exceeds compact limit; retry with --full-record", file=sys.stderr)
                return 2
            summary = {}
            for key in result:
                if key not in _SUMMARY_FIELDS:
                    if len(omitted) < 32:
                        omitted.append(str(key)[:160])
                    elif len(omitted) == 32:
                        omitted.append("additional fields omitted")
            budget = [128]
            for key in _SUMMARY_FIELDS:
                if key not in result or key in summary:
                    continue
                value = result[key]
                if key == "checks" and isinstance(value, dict):
                    summary[key] = {check: value[check] for check in CHECKS if check in value}
                    if any(check not in CHECKS for check in value):
                        omitted.append("checks: additional fields omitted")
                elif key == "prompt_text" and args.full_prompt:
                    summary[key] = value
                else:
                    summary[key] = _summarize_value(value, key, changes, budget)
            result = summary
        truncated = isinstance(prompt, str) and result.get("prompt_text") != prompt
        envelope = {"entry": result, "prompt_text_truncated": truncated,
                          "prompt_text_chars": len(prompt) if isinstance(prompt, str) else None,
                          "truncated_fields": changes, "omitted_fields": omitted,
                          "retrieve": "Repeat this search with --full-record for complete metadata; --full-prompt restores prompt_text" if changes or omitted else None}
        if not args.full_record and not args.full_prompt:
            try:
                envelope = _limit_envelope(envelope)
            except ContractError as exc:
                print(str(exc), file=sys.stderr)
                return 2
        formatted.append(envelope)
    results = formatted
    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 0 if results else 1


if __name__ == "__main__":
    sys.exit(main())
