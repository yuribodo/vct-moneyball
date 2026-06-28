"""T017 — build-ranking yields a schema-valid artifact (16 teams, maps, contributors).

Exercises the score -> aggregate -> artifact -> schema-validate chain end-to-end on
deterministic fixture data, asserting the published contract
(``contracts/ranking-artifact.schema.json``).
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from vct_moneyball.config import DEFAULT_CONFIG
from vct_moneyball.rank.aggregate import RosterPlayer, TeamInput, aggregate_ranking
from vct_moneyball.rank.artifact import build_artifact, validate_artifact, write_artifact
from vct_moneyball.score.player import StatRow, score_players

pytestmark = pytest.mark.integration

MAP_POOL = ["Ascent", "Bind", "Haven", "Lotus", "Split", "Icebox", "Sunset"]


def _build_dataset() -> tuple[list[TeamInput], dict]:
    teams: list[TeamInput] = []
    rows: list[StatRow] = []
    for ti in range(1, 17):
        roster = [RosterPlayer(player_id=ti * 100 + j, player=f"t{ti}p{j}") for j in range(5)]
        teams.append(TeamInput(team_id=ti, team=f"Team{ti:02d}", country=f"C{ti}", roster=roster))
        skill = 0.3 + ti * 0.03  # stronger teams at higher index
        for p in roster:
            for m in MAP_POOL:
                for _ in range(3):  # 3 maps each -> above history threshold
                    rows.append(
                        StatRow(
                            player_id=p.player_id,
                            player=p.player,
                            map=m,
                            team_id=ti,
                            team=f"Team{ti:02d}",
                            country=f"C{ti}",
                            rating=1.0 + skill,
                            acs=150 + skill * 200,
                            kast=60 + skill * 30,
                            adr=100 + skill * 100,
                            kills=int(10 + skill * 20),
                            deaths=15,
                            assists=5,
                        )
                    )
    scores = score_players(rows, DEFAULT_CONFIG)
    return teams, scores


def test_artifact_is_schema_valid_with_full_structure() -> None:
    teams, scores = _build_dataset()
    ranking = aggregate_ranking(teams, scores, MAP_POOL, DEFAULT_CONFIG)
    now = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)
    artifact = build_artifact(
        ranking,
        version="enc-2026.v1",
        published_at=now,
        tournament_start=datetime(2026, 7, 10, 12, 0, tzinfo=UTC),
        data_window=(datetime(2025, 7, 1, tzinfo=UTC), now),
        config_hash=DEFAULT_CONFIG.config_hash,
        map_pool=MAP_POOL,
    )
    validate_artifact(artifact)  # raises if invalid

    assert len(artifact["teams"]) == 16
    positions = [t["position"] for t in artifact["teams"]]
    assert positions == list(range(1, 17))
    for t in artifact["teams"]:
        assert {b["map"] for b in t["map_breakdown"]} == set(MAP_POOL)
        assert len(t["contributors"]) == 5


def test_write_artifact_is_immutable(tmp_path) -> None:
    teams, scores = _build_dataset()
    ranking = aggregate_ranking(teams, scores, MAP_POOL, DEFAULT_CONFIG)
    now = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)
    artifact = build_artifact(
        ranking,
        version="enc-2026.v1",
        published_at=now,
        tournament_start=datetime(2026, 7, 10, 12, 0, tzinfo=UTC),
        data_window=(datetime(2025, 7, 1, tzinfo=UTC), now),
        config_hash=DEFAULT_CONFIG.config_hash,
        map_pool=MAP_POOL,
    )
    written = write_artifact(artifact, tmp_path, slug="v1")
    assert (written / "ranking.json").is_file()
    assert (written / "ranking.md").is_file()
    with pytest.raises(Exception):  # noqa: B017 - never overwrite (Constitution II)
        write_artifact(artifact, tmp_path, slug="v1")
