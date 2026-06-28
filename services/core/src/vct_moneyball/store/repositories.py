"""Upsert repositories: write collected rows with provenance, idempotently.

Each method upserts on the row's natural key (so re-running collection is idempotent
and reproducible — Constitution I) and stamps ``source_url`` + ``captured_at`` on every
collected row. Postgres ``INSERT ... ON CONFLICT DO UPDATE`` is used for the upserts.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from vct_moneyball.store.models import (
    Map,
    Match,
    MatchMap,
    Player,
    PlayerMapStat,
    Team,
    TeamPlayer,
)


class Repositories:
    def __init__(self, session: Session) -> None:
        self.s = session

    def upsert_team(
        self,
        *,
        name: str,
        country: str,
        source_url: str,
        captured_at: datetime,
        vlr_team_id: str | None = None,
        is_enc_2026: bool = False,
    ) -> int:
        stmt = (
            insert(Team)
            .values(
                name=name,
                country=country,
                vlr_team_id=vlr_team_id,
                is_enc_2026=is_enc_2026,
                source_url=source_url,
                captured_at=captured_at,
            )
            .on_conflict_do_update(
                constraint="uq_team_name_country",
                set_={
                    "vlr_team_id": vlr_team_id,
                    "is_enc_2026": is_enc_2026,
                    "source_url": source_url,
                    "captured_at": captured_at,
                },
            )
            .returning(Team.id)
        )
        return self.s.execute(stmt).scalar_one()

    def upsert_player(
        self,
        *,
        handle: str,
        source_url: str,
        captured_at: datetime,
        vlr_player_id: str | None = None,
    ) -> int:
        if vlr_player_id is not None:
            stmt = (
                insert(Player)
                .values(
                    handle=handle,
                    vlr_player_id=vlr_player_id,
                    source_url=source_url,
                    captured_at=captured_at,
                )
                .on_conflict_do_update(
                    constraint="uq_player_vlr_id",
                    set_={"handle": handle, "source_url": source_url, "captured_at": captured_at},
                )
                .returning(Player.id)
            )
            return self.s.execute(stmt).scalar_one()
        # No VLR id: fall back to handle identity.
        existing = self.s.execute(
            select(Player.id).where(Player.handle == handle, Player.vlr_player_id.is_(None))
        ).scalar_one_or_none()
        if existing is not None:
            return existing
        player = Player(
            handle=handle, vlr_player_id=None, source_url=source_url, captured_at=captured_at
        )
        self.s.add(player)
        self.s.flush()
        return player.id

    def upsert_team_player(
        self,
        *,
        team_id: int,
        player_id: int,
        source_url: str,
        captured_at: datetime,
        role: str | None = None,
        is_active: bool = True,
    ) -> int:
        stmt = (
            insert(TeamPlayer)
            .values(
                team_id=team_id,
                player_id=player_id,
                role=role,
                is_active=is_active,
                source_url=source_url,
                captured_at=captured_at,
            )
            .on_conflict_do_update(
                constraint="uq_team_player",
                set_={
                    "role": role,
                    "is_active": is_active,
                    "source_url": source_url,
                    "captured_at": captured_at,
                },
            )
            .returning(TeamPlayer.id)
        )
        return self.s.execute(stmt).scalar_one()

    def upsert_map(
        self,
        *,
        name: str,
        in_pool: bool = True,
        source_url: str | None = None,
        captured_at: datetime | None = None,
    ) -> int:
        stmt = (
            insert(Map)
            .values(name=name, in_pool=in_pool, source_url=source_url, captured_at=captured_at)
            .on_conflict_do_update(constraint="uq_map_name", set_={"in_pool": in_pool})
            .returning(Map.id)
        )
        return self.s.execute(stmt).scalar_one()

    def upsert_match(
        self,
        *,
        vlr_match_id: str,
        event: str,
        played_at: datetime,
        source_url: str,
        captured_at: datetime,
    ) -> int:
        stmt = (
            insert(Match)
            .values(
                vlr_match_id=vlr_match_id,
                event=event,
                played_at=played_at,
                source_url=source_url,
                captured_at=captured_at,
            )
            .on_conflict_do_update(
                constraint="uq_match_vlr_id",
                set_={
                    "event": event,
                    "played_at": played_at,
                    "source_url": source_url,
                    "captured_at": captured_at,
                },
            )
            .returning(Match.id)
        )
        return self.s.execute(stmt).scalar_one()

    def upsert_match_map(
        self, *, match_id: int, map_id: int, winner_team_id: int | None = None
    ) -> int:
        stmt = (
            insert(MatchMap)
            .values(match_id=match_id, map_id=map_id, winner_team_id=winner_team_id)
            .on_conflict_do_update(
                constraint="uq_match_map", set_={"winner_team_id": winner_team_id}
            )
            .returning(MatchMap.id)
        )
        return self.s.execute(stmt).scalar_one()

    def upsert_player_map_stat(
        self,
        *,
        match_map_id: int,
        player_id: int,
        source_url: str,
        captured_at: datetime,
        team_id: int | None = None,
        rating: float | None = None,
        acs: float | None = None,
        kast: float | None = None,
        adr: float | None = None,
        kills: int | None = None,
        deaths: int | None = None,
        assists: int | None = None,
    ) -> int:
        values = dict(
            match_map_id=match_map_id,
            player_id=player_id,
            team_id=team_id,
            rating=rating,
            acs=acs,
            kast=kast,
            adr=adr,
            kills=kills,
            deaths=deaths,
            assists=assists,
            source_url=source_url,
            captured_at=captured_at,
        )
        update = {k: v for k, v in values.items() if k not in {"match_map_id", "player_id"}}
        stmt = (
            insert(PlayerMapStat)
            .values(**values)
            .on_conflict_do_update(constraint="uq_player_map_stat", set_=update)
            .returning(PlayerMapStat.id)
        )
        return self.s.execute(stmt).scalar_one()
