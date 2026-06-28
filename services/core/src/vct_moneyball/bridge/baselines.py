"""Bridge baselines — explicit, non-learned rules the bridge model must beat.

Reuses feature-002's baselines, which operate on the shared feature names: ``winrate-elo``
is the pure roster-Elo expectation (the key thing the learned model must improve on — does
calibration + form + volume add value over just averaging roster Elo?), and ``coin`` is the
honesty floor. Scored on the identical eval matches (FR-005/FR-006).
"""

from __future__ import annotations

from vct_moneyball.predict.baselines import baseline_probs as _predict_baseline_probs
from vct_moneyball.predict.features import MatchExample

DEFAULT_BRIDGE_BASELINES = ("winrate-elo", "coin")


def baseline_probs(label: str, examples: list[MatchExample]) -> list[float]:
    return _predict_baseline_probs(label, examples)
