"""Read queries that load scoring inputs from the system of record.

These turn the persisted ENC cohort + in-window per-map stats into the plain
``StatRow``/``TeamInput`` shapes the (pure) scoring and aggregation stages consume.
A player's stats are attributed to the ENC team whose active roster they belong to.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from vct_moneyball.rank.aggregate import RosterPlayer, TeamInput
from vct_moneyball.score.player import StatRow
from vct_moneyball.store.models import (
    Map,
    Match,
    MatchMap,
    Player,
    PlayerMapStat,
    Team,
    TeamPlayer,
)


def load_map_pool(session: Session) -> list[str]:
    """In-pool map names (the maps a ranking must cover), ordered by name."""
    rows = session.execute(select(Map.name).where(Map.in_pool.is_(True)).order_by(Map.name)).all()
    return [r[0] for r in rows]


def load_teams(session: Session) -> list[TeamInput]:
    """ENC teams with their active rosters."""
    teams = (
        session.execute(select(Team).where(Team.is_enc_2026.is_(True)).order_by(Team.name))
        .scalars()
        .all()
    )
    out: list[TeamInput] = []
    for team in teams:
        members = session.execute(
            select(Player.id, Player.handle, TeamPlayer.role)
            .join(TeamPlayer, TeamPlayer.player_id == Player.id)
            .where(TeamPlayer.team_id == team.id, TeamPlayer.is_active.is_(True))
            .order_by(Player.handle)
        ).all()
        out.append(
            TeamInput(
                team_id=team.id,
                team=team.name,
                country=team.country,
                roster=[
                    RosterPlayer(player_id=pid, player=h, role=role) for pid, h, role in members
                ],
            )
        )
    return out


def load_stat_rows(session: Session, window_start: datetime, window_end: datetime) -> list[StatRow]:
    """Per-map stat rows for ENC roster players, within the data window."""
    # player_id -> (enc team id, name, country) from active rosters.
    roster_rows = session.execute(
        select(Player.id, Team.id, Team.name, Team.country)
        .join(TeamPlayer, TeamPlayer.player_id == Player.id)
        .join(Team, Team.id == TeamPlayer.team_id)
        .where(Team.is_enc_2026.is_(True), TeamPlayer.is_active.is_(True))
    ).all()
    team_of: dict[int, tuple[int, str, str]] = {
        pid: (tid, name, country) for pid, tid, name, country in roster_rows
    }
    if not team_of:
        return []

    stat_rows = session.execute(
        select(
            PlayerMapStat.player_id,
            Player.handle,
            Map.name,
            PlayerMapStat.rating,
            PlayerMapStat.acs,
            PlayerMapStat.kast,
            PlayerMapStat.adr,
            PlayerMapStat.kills,
            PlayerMapStat.deaths,
            PlayerMapStat.assists,
        )
        .join(Player, Player.id == PlayerMapStat.player_id)
        .join(MatchMap, MatchMap.id == PlayerMapStat.match_map_id)
        .join(Map, Map.id == MatchMap.map_id)
        .join(Match, Match.id == MatchMap.match_id)
        .where(
            PlayerMapStat.player_id.in_(team_of.keys()),
            Match.played_at >= window_start,
            Match.played_at <= window_end,
            Map.in_pool.is_(True),
        )
    ).all()

    rows: list[StatRow] = []
    for pid, handle, map_name, rating, acs, kast, adr, kills, deaths, assists in stat_rows:
        team_id, team_name, country = team_of[pid]
        rows.append(
            StatRow(
                player_id=pid,
                player=handle,
                map=map_name,
                team_id=team_id,
                team=team_name,
                country=country,
                rating=float(rating) if rating is not None else None,
                acs=float(acs) if acs is not None else None,
                kast=float(kast) if kast is not None else None,
                adr=float(adr) if adr is not None else None,
                kills=kills,
                deaths=deaths,
                assists=assists,
            )
        )
    return rows
