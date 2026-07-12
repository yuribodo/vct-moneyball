"""T009 — GET /enc/predict: CLI-parity, low-confidence flag, 400 on bad input."""

from __future__ import annotations

import argparse
import json

import pytest
from fastapi.testclient import TestClient

from tests.seed import seed_attributed_matches
from vct_moneyball.api.app import create_app
from vct_moneyball.cli.enc_predict import run_enc_predict

pytestmark = pytest.mark.integration

AS_OF = "2026-11-08"


def test_predict_matches_cli(clean_db, capsys) -> None:
    with __import__("sqlalchemy.orm", fromlist=["Session"]).Session(clean_db) as s:
        seed_attributed_matches(s, n_teams=16, enc_teams=16, n_matches=240)
        s.commit()

    api = (
        TestClient(create_app())
        .get(f"/enc/predict?team_a=BTeam15&team_b=BTeam00&as_of={AS_OF}")
        .json()
    )

    run_enc_predict(
        argparse.Namespace(
            team_a="BTeam15",
            team_b="BTeam00",
            as_of=AS_OF,
            lookback_months=12,
            aggregation="mean",
            run=None,
            json=True,
            verbose=False,
        )
    )
    cli = json.loads(capsys.readouterr().out.strip().splitlines()[-1])

    assert api["p_a"] == cli["p_a"] and api["winner"] == cli["winner"]  # parity
    assert abs(api["p_a"] + api["p_b"] - 1.0) < 1e-9
    assert api["low_confidence"] is False
    assert isinstance(api["elo_a"], float) and isinstance(api["elo_b"], float)  # surfaced for UI
    assert api["provenance"]["source"] == "model_run"


def test_predict_unknown_team_is_400(clean_db) -> None:
    with __import__("sqlalchemy.orm", fromlist=["Session"]).Session(clean_db) as s:
        seed_attributed_matches(s, n_teams=16, enc_teams=16, n_matches=120)
        s.commit()
    r = TestClient(create_app()).get("/enc/predict?team_a=Nope&team_b=BTeam00")
    assert r.status_code == 400
    assert r.json()["status"] == 400


def test_predict_bad_date_is_400(clean_db) -> None:
    r = TestClient(create_app()).get("/enc/predict?team_a=A&team_b=B&as_of=not-a-date")
    assert r.status_code == 400
