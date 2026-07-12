"""T007 — GET /enc/ranking serves the published artifact (byte-faithful) or 404."""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from vct_moneyball.api.app import create_app

pytestmark = pytest.mark.integration


def _write_ranking(tmp_path):
    d = tmp_path / "artifacts" / "models" / "bridge" / "enc-2026.bridge.v1"
    d.mkdir(parents=True)
    (d / "enc-ranking.json").write_text(
        json.dumps(
            {
                "version": "enc-2026.bridge.v1",
                "as_of": "2026-11-08",
                "aggregation": "mean",
                "teams": [
                    {
                        "position": i,
                        "team": f"T{i:02d}",
                        "roster_elo": 1500 + (17 - i),
                        "confidence": "high",
                    }
                    for i in range(1, 17)
                ],
            }
        )
    )
    (d.parent / "LATEST").write_text("enc-2026.bridge.v1\n")


def test_ranking_404_when_absent(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("vct_moneyball.api.artifacts.repo_root", lambda: tmp_path)
    assert TestClient(create_app()).get("/enc/ranking").status_code == 404


def test_ranking_served_with_provenance(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("vct_moneyball.api.artifacts.repo_root", lambda: tmp_path)
    _write_ranking(tmp_path)
    r = TestClient(create_app()).get("/enc/ranking")
    assert r.status_code == 200
    body = r.json()
    assert len(body["teams"]) == 16
    assert [t["position"] for t in body["teams"]] == list(range(1, 17))
    assert body["provenance"]["version"] == "enc-2026.bridge.v1"
