"""Locate + load the latest published artifacts (read-only).

Reads the committed ranking and evaluation artifacts byte-faithfully; the API never
recomputes or mutates them (Constitution II). Missing artifacts raise a 404.
"""

from __future__ import annotations

import json
import pathlib
from typing import Any

from fastapi import HTTPException


def repo_root() -> pathlib.Path:
    for base in [pathlib.Path.cwd(), *pathlib.Path(__file__).resolve().parents]:
        if (base / ".git").is_dir() or (base / "services" / "core").is_dir():
            return base
    return pathlib.Path.cwd()


def _artifacts() -> pathlib.Path:
    return repo_root() / "artifacts"


def _latest_dir(parent: pathlib.Path, version: str | None) -> pathlib.Path:
    if not parent.is_dir():
        raise HTTPException(status_code=404, detail="no published artifact")
    if version is not None:
        target = parent / version
        if not target.is_dir():
            raise HTTPException(status_code=404, detail=f"unknown version {version!r}")
        return target
    dirs = [d for d in parent.iterdir() if d.is_dir()]
    if not dirs:
        raise HTTPException(status_code=404, detail="no published artifact")
    return max(dirs, key=lambda d: d.stat().st_mtime)


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
    # roster ranking dirs hold enc-ranking.json (eval dirs hold report.json — skip those)
    candidates = (
        [d for d in parent.iterdir() if d.is_dir() and (d / "enc-ranking.json").is_file()]
        if parent.is_dir()
        else []
    )
    if version is not None:
        target = parent / version
        if not (target / "enc-ranking.json").is_file():
            raise HTTPException(status_code=404, detail=f"unknown version {version!r}")
        return _load(target / "enc-ranking.json")
    if not candidates:
        raise HTTPException(status_code=404, detail="no published roster ranking")
    latest = max(candidates, key=lambda d: d.stat().st_mtime)
    return _load(latest / "enc-ranking.json")


def load_evaluation(*, kind: str = "bridge", run: str | None = None) -> dict[str, Any]:
    """Load the latest published evaluation report (bridge or winrate)."""
    sub = "bridge" if kind == "bridge" else "winrate"
    parent = _artifacts() / "models" / sub
    candidates = (
        [d for d in parent.iterdir() if d.is_dir() and (d / "report.json").is_file()]
        if parent.is_dir()
        else []
    )
    if run is not None:
        target = parent / run
        if not (target / "report.json").is_file():
            raise HTTPException(status_code=404, detail=f"unknown run {run!r}")
        return _load(target / "report.json")
    if not candidates:
        raise HTTPException(status_code=404, detail=f"no published {sub} evaluation")
    latest = max(candidates, key=lambda d: d.stat().st_mtime)
    return _load(latest / "report.json")
