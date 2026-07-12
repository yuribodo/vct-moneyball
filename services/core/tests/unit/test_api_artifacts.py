"""T-new — artifact resolution is pointer-based, never filesystem mtime."""

from __future__ import annotations

import json

import pytest
from fastapi import HTTPException

from vct_moneyball.api import artifacts


def _write_ranking(d, version: str) -> None:
    d.mkdir(parents=True)
    (d / "ranking.json").write_text(json.dumps({"version": version, "teams": []}))


def test_multi_candidate_resolves_by_pointer_not_mtime(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(artifacts, "repo_root", lambda: tmp_path)
    parent = tmp_path / "artifacts" / "rankings" / "enc-2026"
    _write_ranking(parent / "enc-2026.v1", "enc-2026.v1")
    # v2 is written *after* v1 (strictly newer mtime) but the pointer names v1 —
    # proves resolution follows the pointer, not "most recently written".
    _write_ranking(parent / "enc-2026.v2", "enc-2026.v2")
    (parent / "LATEST").write_text("enc-2026.v1\n")

    result = artifacts.load_ranking(source="power")
    assert result["version"] == "enc-2026.v1"


def test_pointer_names_missing_dir_returns_404(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(artifacts, "repo_root", lambda: tmp_path)
    parent = tmp_path / "artifacts" / "rankings" / "enc-2026"
    parent.mkdir(parents=True)
    (parent / "LATEST").write_text("enc-2026.v9\n")  # never published

    with pytest.raises(HTTPException) as exc_info:
        artifacts.load_ranking(source="power")
    assert exc_info.value.status_code == 404
    assert "unpublished" in exc_info.value.detail


def test_no_pointer_file_returns_404(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(artifacts, "repo_root", lambda: tmp_path)
    parent = tmp_path / "artifacts" / "rankings" / "enc-2026"
    parent.mkdir(parents=True)

    with pytest.raises(HTTPException) as exc_info:
        artifacts.load_ranking(source="power")
    assert exc_info.value.status_code == 404
    assert "no LATEST pointer" in exc_info.value.detail
