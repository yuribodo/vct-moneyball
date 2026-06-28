"""T008 — roster strength aggregation + sparse-aware confidence."""

from __future__ import annotations

import pytest

from vct_moneyball.bridge.player_rating import PlayerRatingConfig, PlayerState
from vct_moneyball.bridge.strength import roster_strength

pytestmark = pytest.mark.unit
CFG = PlayerRatingConfig(min_history=5)


def _st(elo, count):
    return PlayerState(elo=elo, count=count)


def test_mean_aggregation_and_confidence() -> None:
    states = {1: _st(1600, 10), 2: _st(1500, 10)}
    # player 3 absent (no history) → base elo, counts against confidence.
    ts = roster_strength(states, [1, 2, 3], cfg=CFG, aggregation="mean")
    assert ts.n_with_history == 2 and ts.n_players == 3
    assert ts.confidence == "medium"  # 2/3 backed
    assert 1500 <= ts.elo <= 1600


def test_all_sparse_is_low_confidence() -> None:
    ts = roster_strength({}, [1, 2, 3], cfg=CFG)
    assert ts.confidence == "low"
    assert ts.is_confident is False
    assert ts.elo == CFG.elo_base


def test_topk_uses_strongest() -> None:
    states = {1: _st(1700, 10), 2: _st(1600, 10), 3: _st(1500, 10), 4: _st(1000, 10)}
    mean = roster_strength(states, [1, 2, 3, 4], cfg=CFG, aggregation="mean").elo
    topk = roster_strength(states, [1, 2, 3, 4], cfg=CFG, aggregation="topk").elo
    assert topk > mean  # top-3 ignores the weak 4th
