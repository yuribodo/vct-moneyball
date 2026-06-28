"""T009 — roster-strength matchup features + leakage-free example building."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from vct_moneyball.bridge.features import build_bridge_examples, matchup_features
from vct_moneyball.bridge.player_rating import PlayerMatch
from vct_moneyball.bridge.strength import TeamStrength

pytestmark = pytest.mark.unit


def _ts(elo, form=0.5, vol=10.0):
    return TeamStrength(
        elo=elo, form=form, volume=vol, confidence="high", n_players=5, n_with_history=5
    )


def test_matchup_features_are_differences() -> None:
    f = matchup_features(_ts(1600, 0.6), _ts(1400, 0.4))
    assert f["elo_diff"] == pytest.approx(200.0)
    assert f["form_diff"] == pytest.approx(0.2)
    assert f["log_volume_diff"] == pytest.approx(0.0)


def test_build_examples_leakage_free_and_differentiated() -> None:
    t0 = datetime(2026, 1, 1, tzinfo=UTC)
    matches = [
        PlayerMatch(i, t0 + timedelta(days=i), frozenset({1, 2}), frozenset({3, 4}), 1)
        for i in range(1, 8)
    ]
    ex = build_bridge_examples(matches)
    # First example: nobody has history → neutral.
    assert ex[0].features["elo_diff"] == 0.0
    # Later example: side A (consistent winners) has higher roster Elo.
    assert ex[-1].features["elo_diff"] > 0.0
    assert build_bridge_examples(matches) == ex  # deterministic
