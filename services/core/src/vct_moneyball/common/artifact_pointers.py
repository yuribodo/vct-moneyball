"""Git-tracked LATEST pointer files: deterministic 'which version is published'.

One plaintext file per artifact family, holding exactly the target directory name
(the ranking's ``version`` or the eval report's ``run_id``) plus a trailing newline.
No mtime, no globbing — resolution is a two-step, fully reproducible lookup: read the
pointer, then check the thing it names actually exists on disk (== is committed, in a
clean checkout).
"""

from __future__ import annotations

import pathlib


def read_pointer(pointer_path: pathlib.Path) -> str | None:
    """Return the pointed-at directory name, or ``None`` if unset/missing/blank."""
    if not pointer_path.is_file():
        return None
    value = pointer_path.read_text().strip()
    return value or None


def write_pointer(pointer_path: pathlib.Path, value: str) -> None:
    """Point ``pointer_path`` at ``value`` (creates parent dirs as needed)."""
    pointer_path.parent.mkdir(parents=True, exist_ok=True)
    pointer_path.write_text(f"{value}\n")
