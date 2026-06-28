"""Unit tests for event-tier classification and tier-weighted scoring."""

from __future__ import annotations

import pytest

from vct_moneyball.config import ScoringConfig
from vct_moneyball.score.events import classify_event_tier
from vct_moneyball.score.player import StatRow, score_players

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    ("event", "tier"),
    [
        ("VCT 2026: Americas Stage 1", "t1"),
        ("Valorant Champions 2025", "t1"),
        ("Valorant Masters London 2026", "t1"),
        ("Esports World Cup 2026 Americas Qualifier", "t1"),
        ("Challengers 2026: North America ACE Stage 3", "t2"),
        ("VCL 26: NA Stage 3", "t2"),
        ("China-ASEAN Esports Competition 2025", "t3"),
        ("32nd Southeast Asian Games", "t3"),
        ("", "t3"),
    ],
)
def test_classify_event_tier(event: str, tier: str) -> None:
    assert classify_event_tier(event) == tier


def _row(pid: int, event: str, rating: float) -> StatRow:
    return StatRow(
        player_id=pid,
        player=f"p{pid}",
        map="Ascent",
        team_id=pid,
        team=f"t{pid}",
        country="XX",
        rating=rating,
        acs=200,
        kast=70,
        adr=140,
        kills=15,
        deaths=14,
        assists=5,
        event=event,
    )


def test_tier_weighting_favors_tier1_form() -> None:
    # Two players with identical maps; A's strong games are all tier-1, B's strong
    # games are all tier-3. With tier weighting A should outscore B even though their
    # raw distributions are mirror images.
    config = ScoringConfig(min_history_maps=1)
    rows = [
        # spread so normalization has range
        _row(1, "VCT 2026: Americas Stage 1", 1.6),
        _row(1, "VCT 2026: EMEA Stage 1", 1.5),
        _row(1, "China-ASEAN Esports Competition 2025", 0.7),
        _row(2, "China-ASEAN Esports Competition 2025", 1.6),
        _row(2, "32nd Southeast Asian Games", 1.5),
        _row(2, "VCT 2026: Pacific Stage 1", 0.7),
    ]
    scores = score_players(rows, config)
    assert scores[(1, "Ascent")].score > scores[(2, "Ascent")].score


def test_config_hash_changes_with_tier_weights() -> None:
    base = ScoringConfig()
    tweaked = ScoringConfig(event_tier_weights={"t1": 1.0, "t2": 0.5, "t3": 0.5})
    assert base.config_hash != tweaked.config_hash
