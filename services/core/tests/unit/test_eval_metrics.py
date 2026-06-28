"""T019 — probabilistic metrics + baselines."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from vct_moneyball.predict.baselines import baseline_probs
from vct_moneyball.predict.evaluate import accuracy, brier, compute_metrics, log_loss
from vct_moneyball.predict.features import MatchExample

pytestmark = pytest.mark.unit


def test_perfect_predictions_minimize_loss() -> None:
    y = [1, 0, 1, 0]
    perfect = [0.999, 0.001, 0.999, 0.001]
    assert accuracy(y, perfect) == 1.0
    assert log_loss(y, perfect) < 0.05
    assert brier(y, perfect) < 0.01


def test_metrics_bundle_in_range() -> None:
    y = [1, 0, 1, 1, 0]
    p = [0.6, 0.4, 0.7, 0.55, 0.45]
    m = compute_metrics(y, p)
    assert 0 <= m.accuracy <= 1 and m.log_loss >= 0 and 0 <= m.brier <= 1


def test_baseline_elo_uses_feature_diff() -> None:
    ex = MatchExample(
        1,
        datetime(2026, 1, 1, tzinfo=UTC),
        1,
        2,
        label=1,
        features={"elo_diff": 200.0, "form_diff": 0.0, "log_volume_diff": 0.0},
        min_volume=5,
    )
    probs = baseline_probs("winrate-elo", [ex])
    assert probs[0] > 0.5  # +200 elo favors team_a
    assert baseline_probs("coin", [ex])[0] == 0.5
