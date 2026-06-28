"""T015 — bridge baselines produce probabilities on the same examples."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from vct_moneyball.bridge.baselines import DEFAULT_BRIDGE_BASELINES, baseline_probs
from vct_moneyball.predict.features import MatchExample

pytestmark = pytest.mark.unit


def _ex(elo_diff):
    return MatchExample(
        match_id=1,
        played_at=datetime(2026, 1, 1, tzinfo=UTC),
        team_a_id=0,
        team_b_id=1,
        label=1,
        features={"elo_diff": elo_diff, "form_diff": 0.0, "log_volume_diff": 0.0},
        min_volume=10,
    )


def test_default_baselines_score_same_examples() -> None:
    examples = [_ex(150.0), _ex(-150.0)]
    for label in DEFAULT_BRIDGE_BASELINES:
        probs = baseline_probs(label, examples)
        assert len(probs) == len(examples)
        assert all(0.0 <= p <= 1.0 for p in probs)


def test_roster_elo_baseline_favors_higher_elo() -> None:
    assert baseline_probs("winrate-elo", [_ex(300.0)])[0] > 0.5
    assert baseline_probs("coin", [_ex(300.0)])[0] == 0.5
