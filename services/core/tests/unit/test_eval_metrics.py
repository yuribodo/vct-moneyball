"""T019 — probabilistic metrics + baselines."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from vct_moneyball.predict.baselines import baseline_probs
from vct_moneyball.predict.evaluate import (
    accuracy,
    brier,
    calibration_error,
    compute_metrics,
    log_loss,
)
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


def test_calibration_error_hand_computed() -> None:
    # bin0=[0,.5): (0, 0.1) -> conf .1 acc 0, diff .1
    # bin1=[.5,1]: (1, 0.9) -> conf .9 acc 1, diff .1
    # weighted average over 2 equal-size bins = .1
    assert calibration_error([1, 0], [0.9, 0.1], bins=2) == pytest.approx(0.1)


def test_calibration_error_skips_empty_bins() -> None:
    # only 2 of the default 10 bins are populated; empty bins must not raise or skew the result
    y = [0, 0, 1, 1]
    p = [0.05, 0.06, 0.95, 0.96]
    assert calibration_error(y, p) == pytest.approx(0.05)


def test_calibration_error_empty_input_is_zero() -> None:
    assert calibration_error([], []) == 0.0


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
