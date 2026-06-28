"""Roster-derived matchup features + leakage-free example building.

Encodes a matchup as the difference of two teams' roster strengths, reusing feature-002's
``MatchExample``/feature names so the calibrated model, metrics, and baselines all apply
unchanged. Examples over real club matches are built in a single chronological pass: each
match's features come from pre-match player ratings, then the ratings update — leakage-free
by construction (R4).
"""

from __future__ import annotations

import math

from vct_moneyball.bridge.player_rating import (
    DEFAULT_RATING_CONFIG,
    PlayerMatch,
    PlayerRatingConfig,
    PlayerRatings,
)
from vct_moneyball.bridge.strength import TeamStrength, roster_strength
from vct_moneyball.predict.features import MatchExample

# Same feature names as feature 002 → its model/baselines/metrics work directly.
BRIDGE_FEATURE_NAMES = ("elo_diff", "form_diff", "log_volume_diff")


def matchup_features(a: TeamStrength, b: TeamStrength) -> dict[str, float]:
    return {
        "elo_diff": a.elo - b.elo,
        "form_diff": a.form - b.form,
        "log_volume_diff": math.log1p(a.volume) - math.log1p(b.volume),
    }


def build_bridge_examples(
    matches: list[PlayerMatch],
    *,
    cfg: PlayerRatingConfig = DEFAULT_RATING_CONFIG,
    aggregation: str = "mean",
) -> list[MatchExample]:
    """One leakage-free example per club match: roster-strength diff -> outcome."""
    ratings = PlayerRatings(cfg)
    examples: list[MatchExample] = []
    for pm in matches:
        a = roster_strength(ratings._states, pm.side_a, cfg=cfg, aggregation=aggregation)
        b = roster_strength(ratings._states, pm.side_b, cfg=cfg, aggregation=aggregation)
        examples.append(
            MatchExample(
                match_id=pm.match_id,
                played_at=pm.played_at,
                team_a_id=0,
                team_b_id=1,
                label=pm.a_won,
                features=matchup_features(a, b),
                min_volume=int(min(a.volume, b.volume)),
            )
        )
        ratings.update(pm)
    return examples
