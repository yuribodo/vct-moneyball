"""Per-map player scoring: within-window normalization + weighted composite.

The MVP score is a transparent, deterministic composite (R1): each per-map performance
is the weighted sum of within-window min-max-normalized metrics. A player's score on a
map is the mean composite over the maps they played of that type. A player below the
minimum-history threshold is represented by a labeled low-confidence baseline — the
cohort median for that map — and flagged ``low_history_baseline`` (R3, FR-010/FR-012).

Pure Python (no pandas/numpy) keeps the core path deterministic and dependency-light.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from statistics import median

from vct_moneyball.config import DEFAULT_CONFIG, ScoringConfig

# Metrics that feed the composite. ``kd`` is derived from kills/deaths.
_METRICS = ("rating", "acs", "kast", "adr", "kd")


@dataclass(frozen=True)
class StatRow:
    """One player's performance on one played map (a normalized view of a stat row)."""

    player_id: int | str
    player: str
    map: str
    team_id: int | str
    team: str
    country: str
    rating: float | None = None
    acs: float | None = None
    kast: float | None = None
    adr: float | None = None
    kills: int | None = None
    deaths: int | None = None
    assists: int | None = None
    role: str | None = None

    def metric(self, name: str) -> float | None:
        if name == "kd":
            if self.kills is None or self.deaths is None:
                return None
            return self.kills / max(self.deaths, 1)
        return getattr(self, name)


@dataclass(frozen=True)
class PlayerMapScore:
    player_id: int | str
    player: str
    map: str
    team_id: int | str
    score: float
    maps_played: int
    low_history_baseline: bool


def normalize(values: list[float | None]) -> list[float]:
    """Min-max normalize to ``[0, 1]``; missing -> 0.5, constant series -> 0.5."""
    present = [v for v in values if v is not None]
    if not present:
        return [0.5] * len(values)
    lo, hi = min(present), max(present)
    if hi == lo:
        return [0.5] * len(values)
    span = hi - lo
    return [0.5 if v is None else (v - lo) / span for v in values]


def _row_composites(rows: list[StatRow], weights: dict[str, float]) -> list[float]:
    """Composite score per row using within-window normalized metrics."""
    normalized: dict[str, list[float]] = {}
    for metric_name in _METRICS:
        normalized[metric_name] = normalize([r.metric(metric_name) for r in rows])
    composites: list[float] = []
    for i in range(len(rows)):
        composites.append(sum(weights[m] * normalized[m][i] for m in weights))
    return composites


def score_players(
    rows: list[StatRow], config: ScoringConfig = DEFAULT_CONFIG
) -> dict[tuple[int | str, str], PlayerMapScore]:
    """Score every (player, map) pair present in ``rows``.

    Players with at least ``config.min_history_maps`` maps of a given type get a
    data-driven score (mean composite). Those below threshold get the cohort median
    for that map and are flagged ``low_history_baseline``.
    """
    if not rows:
        return {}

    composites = _row_composites(rows, config.metric_weights)

    # Group composites by (player, map).
    grouped: dict[tuple[int | str, str], list[float]] = defaultdict(list)
    meta: dict[tuple[int | str, str], tuple[str, int | str]] = {}
    by_map: dict[str, list[float]] = defaultdict(list)
    for row, comp in zip(rows, composites, strict=True):
        key = (row.player_id, row.map)
        grouped[key].append(comp)
        meta[key] = (row.player, row.team_id)
        by_map[row.map].append(comp)

    # Cohort baseline = median composite per map (over all observed performances).
    baseline_by_map = {m: median(v) for m, v in by_map.items()}

    scores: dict[tuple[int | str, str], PlayerMapScore] = {}
    for key, comps in grouped.items():
        player, team_id = meta[key]
        _, map_name = key
        maps_played = len(comps)
        if maps_played >= config.min_history_maps:
            value, low = sum(comps) / maps_played, False
        else:
            value, low = baseline_by_map[map_name], True
        scores[key] = PlayerMapScore(
            player_id=key[0],
            player=player,
            map=map_name,
            team_id=team_id,
            score=value,
            maps_played=maps_played,
            low_history_baseline=low,
        )
    return scores
