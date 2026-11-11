"""Locate the canonical effect resources in a checkout or an installed package."""
import os
from contextlib import ExitStack
from pathlib import Path

from video_studio.contract import ContractError


_CATALOG = Path("skills/video-theme-library/assets/effect-library/entries.json")
_MOTION = Path("skills/video-theme-library/assets/prompt-motion/index.json")


def resource_root():
    """Use an installed bundle when present; otherwise use a complete checkout.

    A partial bundle is always an error, even if sibling checkout-like files exist.
    """
    # Preserve reparse points for the native Windows boundary to reject; resolve()
    # would follow one before the no-reparse open.
    package = Path(os.path.abspath(__file__)).parents[1]
    checkout = package.parent
    bundled = package / "_bundled"
    if os.name != "nt":
        root = bundled if os.path.lexists(bundled) else checkout
        if root.is_symlink() or not all((root / part).is_file() for part in (_CATALOG, _MOTION)):
            raise ContractError("Effect library resources are missing or incomplete")
        return root

    from . import _native_windows as native
    try:
        with ExitStack() as handles:
            package_handle = native.open_root(str(package))
            handles.callback(native.close, package_handle)
            try:
                root_handle = native.open_directory(package_handle, "_bundled")
            except OSError as exc:
                if "0xc0000034" not in str(exc):
                    raise
                selected = checkout
                root_handle = native.open_root(str(checkout))
            else:
                selected = bundled
            handles.callback(native.close, root_handle)
            for relative in (_CATALOG, _MOTION):
                current = root_handle
                for part in relative.parts[:-1]:
                    current = native.open_directory(current, part)
                    handles.callback(native.close, current)
                file_handle = native.open_file(current, relative.parts[-1])
                handles.callback(native.close, file_handle)
            return selected
    except (OSError, ValueError) as exc:
        raise ContractError("Effect library resources are missing or incomplete or unsafe") from exc
