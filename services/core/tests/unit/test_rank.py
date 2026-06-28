"""T015 — team aggregation, strict 1..16 ordering, tie-break, map coverage."""

from __future__ import annotations

import pytest

from vct_moneyball.config import ScoringConfig
from vct_moneyball.rank.aggregate import RosterPlayer, TeamInput, aggregate_ranking
from vct_moneyball.score.player import PlayerMapScore

pytestmark = pytest.mark.unit

MAP_POOL = ["Ascent", "Bind", "Haven"]


def _team(i: int) -> TeamInput:
    return TeamInput(
        team_id=i,
        team=f"Team{i:02d}",
        country=f"C{i}",
        roster=[RosterPlayer(player_id=i * 10 + j, player=f"p{i}_{j}") for j in range(5)],
    )


def _scores_for(team: TeamInput, base: float) -> dict[tuple[int | str, str], PlayerMapScore]:
    out: dict[tuple[int | str, str], PlayerMapScore] = {}
    for p in team.roster:
        for m in MAP_POOL:
            out[(p.player_id, m)] = PlayerMapScore(
                player_id=p.player_id,
                player=p.player,
                map=m,
                team_id=team.team_id,
                score=base,
                maps_played=5,
                low_history_baseline=False,
            )
    return out


def test_strict_ordering_1_to_16_and_full_map_coverage() -> None:
    teams = [_team(i) for i in range(1, 17)]
    scores: dict[tuple[int | str, str], PlayerMapScore] = {}
    # Higher index -> higher score, so Team16 should land at position 1.
    for i, t in enumerate(teams, start=1):
        scores.update(_scores_for(t, base=0.1 + i * 0.05))
    ranking = aggregate_ranking(teams, scores, MAP_POOL, ScoringConfig())

    assert [r.position for r in ranking] == list(range(1, 17))
    assert ranking[0].team == "Team16"
    assert ranking[-1].team == "Team01"
    for r in ranking:
        assert [b.map for b in r.map_breakdown] == MAP_POOL  # every in-pool map present
        assert len(r.contributors) == 5


def test_deterministic_tie_break_by_name() -> None:
    teams = [_team(i) for i in range(1, 17)]
    scores: dict[tuple[int | str, str], PlayerMapScore] = {}
    for t in teams:  # identical score for everyone -> tie
        scores.update(_scores_for(t, base=0.5))
    ranking = aggregate_ranking(teams, scores, MAP_POOL, ScoringConfig())
    names = [r.team for r in ranking]
    assert names == sorted(names)  # tie-break ascending by name
    assert [r.position for r in ranking] == list(range(1, 17))


def test_missing_map_still_covered_with_low_confidence() -> None:
    teams = [_team(i) for i in range(1, 17)]
    scores: dict[tuple[int | str, str], PlayerMapScore] = {}
    for t in teams:
        s = _scores_for(t, base=0.5)
        # Drop every "Haven" score for Team01 -> no evidence on that map.
        if t.team == "Team01":
            s = {k: v for k, v in s.items() if k[1] != "Haven"}
        scores.update(s)
    ranking = aggregate_ranking(teams, scores, MAP_POOL, ScoringConfig())
    team01 = next(r for r in ranking if r.team == "Team01")
    haven = next(b for b in team01.map_breakdown if b.map == "Haven")
    assert haven.confidence == "low"
    assert {b.map for b in team01.map_breakdown} == set(MAP_POOL)
