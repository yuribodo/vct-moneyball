"""T027 — single real match label + train→predict reproducibility (Constitution III)."""

from __future__ import annotations

import argparse
import json
import pathlib
from datetime import UTC, datetime

import pytest
from sqlalchemy.orm import Session

from tests.seed import seed_labeled_matches
from vct_moneyball.cli.predict_match import run_predict_match
from vct_moneyball.cli.train_winrate import run_train_winrate
from vct_moneyball.collect.parse import parse_match
from vct_moneyball.predict.labels import LabeledMatch

pytestmark = pytest.mark.integration

FIXTURE = pathlib.Path(__file__).parent.parent / "fixtures" / "vlr" / "match_706327.html"
SOURCE_URL = "https://www.vlr.gg/706327/qor-vs-yft"


def test_real_fixture_yields_a_label() -> None:
    # The captured match (QoR 1 : 2 YFT) reduces to a clean binary label.
    parsed = parse_match(FIXTURE.read_text(), source_url=SOURCE_URL, captured_at=datetime.now(UTC))
    assert parsed.winner_vlr_team_id == parsed.team_b.vlr_team_id  # YFT (team_b) won
    m = LabeledMatch(
        match_id=1,
        played_at=parsed.played_at,
        team_a_id=1,  # QoR
        team_b_id=2,  # YFT
        winner_team_id=2,
    )
    assert m.label == 0  # team_a (QoR) lost


def _train_args(cutoff: datetime) -> argparse.Namespace:
    return argparse.Namespace(
        cutoff=cutoff.isoformat(),
        lookback_months=12,
        learner="logreg",
        experiment="test-e2e",
        json=True,
        verbose=False,
    )


def _predict_args() -> argparse.Namespace:
    return argparse.Namespace(
        team_a="WTeam07",
        team_b="WTeam00",
        as_of=None,
        lookback_months=12,
        run=None,
        json=True,
        verbose=False,
    )


def test_train_then_predict_is_reproducible(clean_db, tmp_path, monkeypatch, capsys) -> None:
    monkeypatch.setenv("MLFLOW_TRACKING_URI", (tmp_path / "mlruns").as_uri())
    with Session(clean_db) as s:
        seed_labeled_matches(s)
        s.commit()
    assert run_train_winrate(_train_args(datetime.now(UTC))) == 0

    run_predict_match(_predict_args())
    first = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    run_predict_match(_predict_args())
    second = json.loads(capsys.readouterr().out.strip().splitlines()[-1])

    assert first == second  # deterministic
    assert abs(first["p_a"] + first["p_b"] - 1.0) < 1e-9
    # WTeam07 is the strongest seed team, WTeam00 the weakest → favored.
    assert first["winner"] == "WTeam07"
