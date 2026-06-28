"""T014 — per-map player composite scoring (normalization + weights + baseline)."""

from __future__ import annotations

import pytest

from vct_moneyball.config import ScoringConfig
from vct_moneyball.score.player import StatRow, normalize, score_players

pytestmark = pytest.mark.unit


def _row(pid: int, mapname: str, **stats: float) -> StatRow:
    return StatRow(
        player_id=pid,
        player=f"p{pid}",
        map=mapname,
        team_id=pid % 2,
        team=f"t{pid % 2}",
        country="XX",
        **stats,
    )


def test_normalize_minmax_and_edge_cases() -> None:
    assert normalize([0.0, 5.0, 10.0]) == [0.0, 0.5, 1.0]
    assert normalize([3.0, 3.0, 3.0]) == [0.5, 0.5, 0.5]  # constant
    assert normalize([None, None]) == [0.5, 0.5]  # all missing
    out = normalize([0.0, None, 10.0])
    assert out[0] == 0.0 and out[1] == 0.5 and out[2] == 1.0


def test_higher_metrics_yield_higher_score() -> None:
    config = ScoringConfig(min_history_maps=1)
    rows = [
        _row(1, "Ascent", rating=1.5, acs=300, kast=90, adr=180, kills=25, deaths=10, assists=5),
        _row(2, "Ascent", rating=0.7, acs=120, kast=60, adr=90, kills=8, deaths=20, assists=3),
    ]
    scores = score_players(rows, config)
    assert scores[(1, "Ascent")].score > scores[(2, "Ascent")].score
    assert all(0.0 <= s.score <= 1.0 for s in scores.values())


def test_below_threshold_uses_flagged_baseline() -> None:
    config = ScoringConfig(min_history_maps=3)
    # Player 1 has 3 maps (enough history); player 2 has only 1 (below threshold).
    rows = [
        _row(1, "Bind", rating=1.4, acs=280, kast=85, adr=170, kills=20, deaths=12, assists=4),
        _row(1, "Bind", rating=1.3, acs=270, kast=84, adr=165, kills=19, deaths=12, assists=4),
        _row(1, "Bind", rating=1.2, acs=260, kast=83, adr=160, kills=18, deaths=13, assists=4),
        _row(2, "Bind", rating=0.9, acs=150, kast=65, adr=110, kills=10, deaths=18, assists=2),
    ]
    scores = score_players(rows, config)
    low = scores[(2, "Bind")]
    high = scores[(1, "Bind")]
    assert high.low_history_baseline is False
    assert high.maps_played == 3
    assert low.low_history_baseline is True
    assert low.maps_played == 1


def test_scoring_is_deterministic() -> None:
    config = ScoringConfig(min_history_maps=1)
    rows = [
        _row(1, "Haven", rating=1.1, acs=210, kast=75, adr=140, kills=15, deaths=14, assists=6),
        _row(2, "Haven", rating=1.0, acs=200, kast=72, adr=135, kills=14, deaths=15, assists=5),
    ]
    assert score_players(rows, config) == score_players(rows, config)
