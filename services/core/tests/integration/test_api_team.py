"""GET /enc/team/{name} — rich team detail merged from power + roster artifacts."""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from vct_moneyball.api.app import create_app

pytestmark = pytest.mark.integration


def _write_artifacts(tmp_path) -> None:
    power = tmp_path / "artifacts" / "rankings" / "enc-2026" / "enc-2026.v2"
    power.mkdir(parents=True)
    (power / "ranking.json").write_text(
        json.dumps(
            {
                "version": "enc-2026.v2",
                "teams": [
                    {
                        "position": 1,
                        "team": "China",
                        "country": "China",
                        "team_score": 0.39,
                        "confidence": "medium",
                        "contributors": [
                            {
                                "player": "CHICHOO",
                                "player_score": 0.39,
                                "maps_played": 76,
                                "confidence": "high",
                                "low_history_baseline": False,
                            }
                        ],
                        "map_breakdown": [
                            {"map": "Ascent", "map_score": 0.46, "confidence": "high"}
                        ],
                    }
                ],
            }
        )
    )
    (power.parent / "LATEST").write_text("enc-2026.v2\n")
    roster = tmp_path / "artifacts" / "models" / "bridge" / "enc-2026.bridge.v1"
    roster.mkdir(parents=True)
    (roster / "enc-ranking.json").write_text(
        json.dumps(
            {
                "version": "enc-2026.bridge.v1",
                "teams": [
                    {"position": 2, "team": "China", "roster_elo": 1563.7, "confidence": "high"}
                ],
            }
        )
    )
    (roster.parent / "LATEST").write_text("enc-2026.bridge.v1\n")


def test_team_404_when_absent(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("vct_moneyball.api.artifacts.repo_root", lambda: tmp_path)
    _write_artifacts(tmp_path)
    r = TestClient(create_app()).get("/enc/team/Nowhere")
    assert r.status_code == 404
    assert r.json()["status"] == 404


def test_team_merges_power_and_roster(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("vct_moneyball.api.artifacts.repo_root", lambda: tmp_path)
    _write_artifacts(tmp_path)
    r = TestClient(create_app()).get("/enc/team/china")  # case-insensitive
    assert r.status_code == 200
    body = r.json()
    assert body["team"] == "China"
    assert body["country"] == "China"
    assert body["position"] == 2  # roster position wins
    assert body["roster_elo"] == pytest.approx(1563.7)
    assert body["confidence"] == "high"  # roster confidence wins
    assert body["team_score"] == pytest.approx(0.39)  # from power artifact
    assert len(body["contributors"]) == 1
    assert body["contributors"][0]["player"] == "CHICHOO"
    assert len(body["map_breakdown"]) == 1
    assert body["provenance"]["source"] == "artifact"
