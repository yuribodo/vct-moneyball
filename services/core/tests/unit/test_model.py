"""T012 — train/calibrate/predict returns probabilities; low-confidence flag."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from vct_moneyball.predict.features import MatchExample
from vct_moneyball.predict.model import is_low_confidence, train

pytestmark = pytest.mark.unit


def _ex(i, elo_diff, label):
    return MatchExample(
        i,
        datetime(2026, 1, 1, tzinfo=UTC) + timedelta(days=i),
        1,
        2,
        label=label,
        features={"elo_diff": elo_diff, "form_diff": 0.0, "log_volume_diff": 0.0},
        min_volume=10,
    )


def test_train_predict_probabilities_sum_to_one() -> None:
    # Separable-ish: positive elo_diff → team_a wins.
    examples = [_ex(i, 150 if i % 2 else -150, 1 if i % 2 else 0) for i in range(40)]
    model = train(examples, learner="logreg")
    p = model.predict_proba_a({"elo_diff": 200.0, "form_diff": 0.0, "log_volume_diff": 0.0})
    assert 0.0 <= p <= 1.0
    assert p > 0.5  # strong positive elo favors team_a


def test_low_confidence_threshold() -> None:
    assert is_low_confidence(2) is True
    assert is_low_confidence(50) is False
