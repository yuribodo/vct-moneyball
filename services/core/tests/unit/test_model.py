"""T012 — train/calibrate/predict returns probabilities; low-confidence flag."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from vct_moneyball.predict.features import MatchExample
from vct_moneyball.predict.model import (
    _MIN_EXAMPLES_FOR_SELECTION,
    _select_calibration_method,
    is_low_confidence,
    train,
)

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
    assert model.calibration_method in ("sigmoid", "isotonic")


def test_train_honors_explicit_calibration_method() -> None:
    examples = [_ex(i, 150 if i % 2 else -150, 1 if i % 2 else 0) for i in range(40)]
    model = train(examples, learner="logreg", calibration_method="isotonic")
    assert model.calibration_method == "isotonic"


def test_low_confidence_threshold() -> None:
    assert is_low_confidence(2) is True
    assert is_low_confidence(50) is False


def test_select_calibration_method_falls_back_below_min_examples() -> None:
    small = [_ex(i, 150 if i % 2 else -150, 1 if i % 2 else 0) for i in range(10)]
    assert len(small) < _MIN_EXAMPLES_FOR_SELECTION
    assert _select_calibration_method(small, "logreg") == "sigmoid"
    assert _select_calibration_method(small, "gbt") == "isotonic"


def test_select_calibration_method_picks_lower_validation_ece(monkeypatch) -> None:
    n = _MIN_EXAMPLES_FOR_SELECTION + 20
    examples = [_ex(i, 150 if i % 2 else -150, 1 if i % 2 else 0) for i in range(n)]
    ordered = sorted(examples, key=lambda e: e.played_at)
    val_labels = [e.label for e in ordered[int(n * 0.8) :]]

    class _StubEstimator:
        def __init__(self, probs):
            self._probs = probs

        def fit(self, x, y):
            return self

        def predict_proba(self, x):
            return [[1 - p, p] for p in self._probs]

    def fake_build_estimator(learner, method):
        if method == "isotonic":
            probs = [0.99 if y == 1 else 0.01 for y in val_labels]  # near-perfect on val
        else:
            probs = [0.99 if y == 0 else 0.01 for y in val_labels]  # confidently wrong on val
        return _StubEstimator(probs)

    import vct_moneyball.predict.model as model_mod

    monkeypatch.setattr(model_mod, "_build_estimator", fake_build_estimator)
    assert model_mod._select_calibration_method(examples, "logreg") == "isotonic"
