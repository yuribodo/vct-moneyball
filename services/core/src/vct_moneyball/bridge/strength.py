"""Roster/lineup -> team strength (as-of), with sparse-aware confidence.

Aggregates a set of players' as-of Elo/form/volume into a team strength. Players with no
history contribute the base prior and lower the team's confidence; a roster that is mostly
sparse is flagged low-confidence (R3, FR-003).
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from statistics import mean

from vct_moneyball.bridge.player_rating import (
    DEFAULT_RATING_CONFIG,
    PlayerRatingConfig,
    PlayerState,
)

_HIGH_CUTOFF = 0.80
_MEDIUM_CUTOFF = 0.50
_TOPK = 3


@dataclass(frozen=True)
class TeamStrength:
    elo: float
    form: float
    volume: float  # mean prior-match count across the lineup
    confidence: str  # high | medium | low
    n_players: int
    n_with_history: int

    @property
    def is_confident(self) -> bool:
        return self.confidence != "low"


def _confidence(backed: int, total: int) -> str:
    if total == 0:
        return "low"
    frac = backed / total
    if frac >= _HIGH_CUTOFF:
        return "high"
    if frac >= _MEDIUM_CUTOFF:
        return "medium"
    return "low"


def roster_strength(
    states: dict[int, PlayerState],
    player_ids: Iterable[int],
    *,
    cfg: PlayerRatingConfig = DEFAULT_RATING_CONFIG,
    aggregation: str = "mean",
) -> TeamStrength:
    """Aggregate a lineup's as-of player ratings into a team strength."""
    ids = list(player_ids)
    base = cfg.elo_base
    elos: list[float] = []
    forms: list[float] = []
    counts: list[int] = []
    backed = 0
    for pid in ids:
        st = states.get(pid)
        if st is None:
            elos.append(base)
            forms.append(0.5)
            counts.append(0)
            continue
        elos.append(st.elo)
        forms.append(st.form)
        counts.append(st.count)
        if st.count >= cfg.min_history:
            backed += 1

    if not ids:
        return TeamStrength(base, 0.5, 0.0, "low", 0, 0)

    if aggregation == "topk":
        top = sorted(elos, reverse=True)[: min(_TOPK, len(elos))]
        elo = mean(top)
    else:
        elo = mean(elos)

    return TeamStrength(
        elo=elo,
        form=mean(forms),
        volume=mean(counts),
        confidence=_confidence(backed, len(ids)),
        n_players=len(ids),
        n_with_history=backed,
    )
