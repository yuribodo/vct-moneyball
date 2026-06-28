"""T019 — single-match bridge E2E: confident, differentiated, reproducible ENC prediction."""

from __future__ import annotations

import argparse
import json
from datetime import datetime

import pytest
from sqlalchemy.orm import Session

from tests.seed import seed_attributed_matches
from vct_moneyball.cli.enc_predict import run_enc_predict

pytestmark = pytest.mark.integration


def _args() -> argparse.Namespace:
    return argparse.Namespace(
        team_a="BTeam15",
        team_b="BTeam00",
        as_of=datetime(2026, 11, 8).isoformat(),
        lookback_months=12,
        aggregation="mean",
        run=None,
        json=True,
        verbose=False,
    )


def test_enc_predict_is_confident_differentiated_reproducible(clean_db, capsys) -> None:
    with Session(clean_db) as s:
        seed_attributed_matches(s, n_teams=16, enc_teams=16, n_matches=240)
        s.commit()

    run_enc_predict(_args())
    first = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    run_enc_predict(_args())
    second = json.loads(capsys.readouterr().out.strip().splitlines()[-1])

    assert first == second  # reproducible
    assert abs(first["p_a"] + first["p_b"] - 1.0) < 1e-9
    assert abs(first["p_a"] - 0.5) > 0.02  # differentiated, not ~50/50
    assert first["low_confidence"] is False  # dense rosters
    assert first["winner"] == "BTeam15"  # strongest seed team
