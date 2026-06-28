"""Team aggregation: player-map scores -> ordered team ranking with breakdowns.

A team's score on a map is the mean of its active roster's per-map scores; the team
score is the mean across the in-pool maps. Teams are ordered strictly 1..N by team
score (deterministic tie-break by name). Confidence rolls up from how much of the
evidence is data-driven vs. the low-history baseline (R3, FR-004/FR-005, SC-002/SC-007).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from statistics import mean, median

from vct_moneyball.config import DEFAULT_CONFIG, ScoringConfig
from vct_moneyball.score.player import PlayerMapScore

Confidence = str  # "high" | "medium" | "low"


@dataclass(frozen=True)
class RosterPlayer:
    player_id: int | str
    player: str
    role: str | None = None


@dataclass(frozen=True)
class TeamInput:
    team_id: int | str
    team: str
    country: str
    roster: list[RosterPlayer] = field(default_factory=list)


@dataclass(frozen=True)
class MapBreakdown:
    map: str
    map_score: float
    confidence: Confidence


@dataclass(frozen=True)
class Contributor:
    player: str
    player_score: float
    confidence: Confidence
    maps_played: int
    low_history_baseline: bool


@dataclass(frozen=True)
class TeamRanking:
    position: int
    team_id: int | str
    team: str
    country: str
    team_score: float
    confidence: Confidence
    map_breakdown: list[MapBreakdown]
    contributors: list[Contributor]


def _confidence(backed: int, total: int, config: ScoringConfig) -> Confidence:
    """Roll a fraction of data-backed evidence into a confidence label."""
    if total == 0:
        return "low"
    frac = backed / total
    if frac >= config.confidence_high_cutoff:
        return "high"
    if frac >= config.confidence_medium_cutoff:
        return "medium"
    return "low"


def aggregate_ranking(
    teams: list[TeamInput],
    scores: dict[tuple[int | str, str], PlayerMapScore],
    map_pool: list[str],
    config: ScoringConfig = DEFAULT_CONFIG,
) -> list[TeamRanking]:
    """Build the ordered ranking. ``map_pool`` is the set of in-pool map names."""
    if not map_pool:
        raise ValueError("map_pool must contain at least one map")

    # Cohort baseline per map (median over all observed player-map scores) for coverage
    # when a roster has no evidence on a given map.
    per_map_values: dict[str, list[float]] = {m: [] for m in map_pool}
    for (_, map_name), s in scores.items():
        if map_name in per_map_values:
            per_map_values[map_name].append(s.score)
    overall = [s.score for s in scores.values()]
    global_baseline = median(overall) if overall else 0.5
    map_baseline = {m: (median(v) if v else global_baseline) for m, v in per_map_values.items()}

    built: list[TeamRanking] = []
    for team in teams:
        map_breakdowns: list[MapBreakdown] = []
        team_backed = team_total = 0
        for map_name in map_pool:
            present = [
                scores[(p.player_id, map_name)]
                for p in team.roster
                if (p.player_id, map_name) in scores
            ]
            if present:
                map_score = mean(s.score for s in present)
                backed = sum(0 if s.low_history_baseline else 1 for s in present)
                conf = _confidence(backed, len(present), config)
                team_backed += backed
                team_total += len(present)
            else:
                map_score = map_baseline[map_name]
                conf = "low"
                team_total += len(team.roster)
            map_breakdowns.append(MapBreakdown(map_name, map_score, conf))

        contributors: list[Contributor] = []
        for p in team.roster:
            p_scores = [scores[(p.player_id, m)] for m in map_pool if (p.player_id, m) in scores]
            if p_scores:
                p_score = mean(s.score for s in p_scores)
                maps_played = sum(s.maps_played for s in p_scores)
                low = all(s.low_history_baseline for s in p_scores)
                backed = sum(0 if s.low_history_baseline else 1 for s in p_scores)
                conf = _confidence(backed, len(p_scores), config)
            else:
                p_score, maps_played, low, conf = global_baseline, 0, True, "low"
            contributors.append(Contributor(p.player, p_score, conf, maps_played, low))

        team_score = mean(b.map_score for b in map_breakdowns)
        team_conf = _confidence(team_backed, team_total, config)
        built.append(
            TeamRanking(
                position=0,  # assigned after sort
                team_id=team.team_id,
                team=team.team,
                country=team.country,
                team_score=team_score,
                confidence=team_conf,
                map_breakdown=map_breakdowns,
                contributors=contributors,
            )
        )

    # Strict order by score desc; deterministic tie-break by team name then id.
    built.sort(key=lambda t: (-t.team_score, t.team.lower(), str(t.team_id)))
    return [
        TeamRanking(
            position=i + 1,
            team_id=t.team_id,
            team=t.team,
            country=t.country,
            team_score=t.team_score,
            confidence=t.confidence,
            map_breakdown=t.map_breakdown,
            contributors=t.contributors,
        )
        for i, t in enumerate(built)
    ]
