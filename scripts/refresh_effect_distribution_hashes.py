"""Refresh hashes for an already reviewed effect-distribution path allowlist.

This does not add or remove paths. Review changes to the manifest and rights
before creating a release; the builder never refreshes hashes automatically.
"""
import hashlib
import json
from pathlib import Path
import sys

from build_effect_distribution import MANIFEST, ROOT, _read_relative, _source_allowed
from video_studio.effect_library import _native_windows as nt


def main():
    root = nt.open_root(str(ROOT))
    try:
        data = json.loads(_read_relative(root, MANIFEST).decode("utf-8"))
        if data.get("schema") != "effect-distribution-manifest/1" or any(not _source_allowed(p) for p in data["files"]):
            raise ValueError("invalid manifest or forbidden input")
        data["files"] = {name: hashlib.sha256(_read_relative(root, name)).hexdigest() for name in sorted(data["files"])}
    finally:
        nt.close(root)
    # Build scripts and the manifest are repo-owned development inputs, not
    # user data. Never let a reparse point redirect this write.
    directory = nt.open_root(str(ROOT / "scripts"))
    output = None
    import uuid
    try:
        output = nt.create_file(directory, "effect-manifest-" + uuid.uuid4().hex)
        nt.write_all(output, (json.dumps(data, indent=2, ensure_ascii=False) + "\n").encode("utf-8"))
        nt.flush(output)
        # Replacing an existing manifest needs a separate reviewed operation;
        # leave an explicit candidate instead of silently overwriting it.
        nt.rename_no_replace(output, directory, "effect-distribution-manifest.candidate.json")
    except BaseException:
        if output is not None:
            nt.delete_on_close(output)
        raise
    finally:
        if output is not None:
            nt.close(output)
        nt.close(directory)
    print("Candidate written: scripts/effect-distribution-manifest.candidate.json")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, OSError, KeyError) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(1)
