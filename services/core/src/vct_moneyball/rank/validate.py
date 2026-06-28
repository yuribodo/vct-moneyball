"""Pre-build validation gates for a ranking.

Before a ranking is written, every collected row it references MUST carry provenance
(``source_url`` + ``captured_at``), the cohort MUST be exactly 16 ENC teams each with an
active roster, and the lock deadline MUST be respected (Constitution I/II;
FR-006/FR-007/FR-009, SC-001/SC-003/SC-004).
"""

from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from vct_moneyball.common.logging import CliError
from vct_moneyball.store.models import (
    Match,
    MatchMap,
    Player,
    PlayerMapStat,
    Team,
    TeamPlayer,
)

ENC_TEAM_COUNT = 16
LOCK_MARGIN = timedelta(hours=24)


def assert_lock_deadline(published_at: datetime, tournament_start: datetime) -> None:
    """Published timestamp must be at least 24h before tournament start (FR-007)."""
    if published_at > tournament_start - LOCK_MARGIN:
        raise CliError(
            "lock deadline violated: published_at "
            f"({published_at.isoformat()}) must be at least 24h before tournament_start "
            f"({tournament_start.isoformat()})"
        )


def assert_cohort(session: Session) -> None:
    """Exactly 16 ENC teams, each with at least one active roster player (SC-001)."""
    n_teams = session.execute(
        select(func.count()).select_from(Team).where(Team.is_enc_2026.is_(True))
    ).scalar_one()
    if n_teams != ENC_TEAM_COUNT:
        raise CliError(f"expected exactly {ENC_TEAM_COUNT} ENC teams, found {n_teams}")

    teams_without_active = session.execute(
        select(Team.id, Team.name)
        .where(Team.is_enc_2026.is_(True))
        .where(
            ~select(TeamPlayer.id)
            .where(TeamPlayer.team_id == Team.id, TeamPlayer.is_active.is_(True))
            .exists()
        )
    ).all()
    if teams_without_active:
        names = ", ".join(name for _, name in teams_without_active)
        raise CliError(f"ENC teams missing an active roster: {names}")


def assert_provenance(session: Session) -> None:
    """Every collected row referenced by scoring carries source_url + captured_at."""
    checks = [
        ("player_map_stat", PlayerMapStat, PlayerMapStat.source_url, PlayerMapStat.captured_at),
        ("match", Match, Match.source_url, Match.captured_at),
        ("team", Team, Team.source_url, Team.captured_at),
        ("player", Player, Player.source_url, Player.captured_at),
    ]
    for name, model, src, cap in checks:
        missing = session.execute(
            select(func.count()).select_from(model).where((src.is_(None)) | (cap.is_(None)))
        ).scalar_one()
        if missing:
            raise CliError(f"{missing} {name} row(s) missing provenance (source_url/captured_at)")

    # match_map references must resolve (no orphan stats).
    orphan = session.execute(
        select(func.count())
        .select_from(PlayerMapStat)
        .where(~select(MatchMap.id).where(MatchMap.id == PlayerMapStat.match_map_id).exists())
    ).scalar_one()
    if orphan:
        raise CliError(f"{orphan} player_map_stat row(s) reference a missing match_map")
