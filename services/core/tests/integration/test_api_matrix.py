"""GET /enc/matrix — pairwise win-probability matrix for the 16 seeded ENC teams."""

from __future__ import annotations

import json

import pytest
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from tests.seed import seed_attributed_matches
from vct_moneyball.api.app import create_app

pytestmark = pytest.mark.integration

AS_OF = "2026-11-08"


def _write_roster(tmp_path) -> None:
    d = tmp_path / "artifacts" / "models" / "bridge" / "enc-2026.bridge.v1"
    d.mkdir(parents=True)
    (d / "enc-ranking.json").write_text(
        json.dumps(
            {
                "version": "enc-2026.bridge.v1",
                "teams": [
                    {
                        "position": i + 1,
                        "team": f"BTeam{i:02d}",
                        "roster_elo": 1500 + (16 - i),
                        "confidence": "high",
                    }
                    for i in range(16)
                ],
            }
        )
    )


def test_matrix_is_16x16_with_valid_probs(clean_db, tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("vct_moneyball.api.artifacts.repo_root", lambda: tmp_path)
    _write_roster(tmp_path)
    with Session(clean_db) as s:
        seed_attributed_matches(s, n_teams=16, enc_teams=16, n_matches=240)
        s.commit()

    r = TestClient(create_app()).get(f"/enc/matrix?as_of={AS_OF}")
    assert r.status_code == 200
    body = r.json()

    assert len(body["teams"]) == 16
    assert [t["position"] for t in body["teams"]] == list(range(1, 17))
    p = body["p"]
    assert len(p) == 16 and all(len(row) == 16 for row in p)
    for i in range(16):
        assert p[i][i] == 0.5
        for j in range(16):
            assert 0.0 <= p[i][j] <= 1.0
    assert body["provenance"]["source"] == "model_run"


def test_matrix_bad_date_is_400(clean_db) -> None:
    r = TestClient(create_app()).get("/enc/matrix?as_of=not-a-date")
    assert r.status_code == 400
