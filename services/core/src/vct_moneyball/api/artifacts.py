"""Locate + load the latest published artifacts (read-only).

Reads the committed ranking and evaluation artifacts byte-faithfully; the API never
recomputes or mutates them (Constitution II). "Latest" is resolved via a committed
``LATEST``/``LATEST_EVAL`` pointer file (see ``common.artifact_pointers``), never by
filesystem mtime — mtime is non-deterministic across a fresh checkout and can point at
an artifact that was never committed. Missing artifacts raise a 404.
"""

from __future__ import annotations

import json
import pathlib
from typing import Any

from fastapi import HTTPException

from vct_moneyball.common.artifact_pointers import read_pointer


def repo_root() -> pathlib.Path:
    for base in [pathlib.Path.cwd(), *pathlib.Path(__file__).resolve().parents]:
        if (base / ".git").is_dir() or (base / "services" / "core").is_dir():
            return base
    return pathlib.Path.cwd()


def _artifacts() -> pathlib.Path:
    return repo_root() / "artifacts"


def _resolve_by_pointer(
    parent: pathlib.Path, pointer_name: str, required_file: str, label: str
) -> pathlib.Path:
    if not parent.is_dir():
        raise HTTPException(status_code=404, detail=f"no published {label}")
    target_name = read_pointer(parent / pointer_name)
    if target_name is None:
        raise HTTPException(status_code=404, detail=f"no published {label} (no LATEST pointer)")
    target = parent / target_name
    if not (target / required_file).is_file():
        raise HTTPException(
            status_code=404, detail=f"pointer names unpublished {label} artifact {target_name!r}"
        )
    return target


def _latest_dir(parent: pathlib.Path, version: str | None) -> pathlib.Path:
    if version is not None:
        if not parent.is_dir():
            raise HTTPException(status_code=404, detail="no published artifact")
        target = parent / version
        if not target.is_dir():
            raise HTTPException(status_code=404, detail=f"unknown version {version!r}")
        return target
    return _resolve_by_pointer(parent, "LATEST", "ranking.json", "power ranking")


def _load(path: pathlib.Path) -> dict[str, Any]:
    if not path.is_file():
        raise HTTPException(status_code=404, detail="no published artifact")
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=503, detail=f"artifact is malformed: {exc}") from exc


def load_ranking(*, source: str = "roster", version: str | None = None) -> dict[str, Any]:
    """Load the latest published ENC ranking (roster-derived by default)."""
    if source == "power":
        parent = _artifacts() / "rankings" / "enc-2026"
        return _load(_latest_dir(parent, version) / "ranking.json")
    parent = _artifacts() / "models" / "bridge"
    if version is not None:
        target = parent / version
        if not (target / "enc-ranking.json").is_file():
            raise HTTPException(status_code=404, detail=f"unknown version {version!r}")
        return _load(target / "enc-ranking.json")
    target = _resolve_by_pointer(parent, "LATEST", "enc-ranking.json", "roster ranking")
    return _load(target / "enc-ranking.json")


def load_evaluation(*, kind: str = "bridge", run: str | None = None) -> dict[str, Any]:
    """Load the latest published evaluation report (bridge or winrate)."""
    sub = "bridge" if kind == "bridge" else "winrate"
    parent = _artifacts() / "models" / sub
    if run is not None:
        target = parent / run
        if not (target / "report.json").is_file():
            raise HTTPException(status_code=404, detail=f"unknown run {run!r}")
        return _load(target / "report.json")
    pointer_name = "LATEST_EVAL" if sub == "bridge" else "LATEST"
    target = _resolve_by_pointer(parent, pointer_name, "report.json", f"{sub} evaluation")
    return _load(target / "report.json")
