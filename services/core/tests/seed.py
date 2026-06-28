"""Test helper: seed a full, valid ENC cohort into the database.

Builds 16 ENC teams (5 active players each), the in-pool map set, and in-window
per-map stats so ``build-ranking`` has a schema-valid, fully-covered dataset to run on.
All rows carry provenance.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from vct_moneyball.store.repositories import Repositories

MAP_POOL = ["Ascent", "Bind", "Haven", "Lotus", "Split", "Icebox", "Sunset"]
SRC = "https://www.vlr.gg/seed"


def seed_cohort(session: Session, *, now: datetime | None = None, maps_per_pair: int = 3) -> None:
    now = now or datetime.now(UTC)
    captured = now
    played = now - timedelta(days=30)
    repos = Repositories(session)

    map_ids = {name: repos.upsert_map(name=name) for name in MAP_POOL}

    for ti in range(1, 17):
        team_id = repos.upsert_team(
            name=f"Team{ti:02d}",
            country=f"C{ti:02d}",
            source_url=SRC,
            captured_at=captured,
            vlr_team_id=f"t{ti}",
            is_enc_2026=True,
        )
        skill = 0.2 + ti * 0.04  # stronger teams at higher index
        for pj in range(5):
            player_id = repos.upsert_player(
                handle=f"t{ti}p{pj}",
                vlr_player_id=f"p{ti}_{pj}",
                source_url=SRC,
                captured_at=captured,
            )
            repos.upsert_team_player(
                team_id=team_id,
                player_id=player_id,
                source_url=SRC,
                captured_at=captured,
                is_active=True,
            )
            for mi, mapname in enumerate(MAP_POOL):
                for k in range(maps_per_pair):
                    match_id = repos.upsert_match(
                        vlr_match_id=f"m_{ti}_{pj}_{mi}_{k}",
                        event="Seed Event",
                        played_at=played,
                        source_url=SRC,
                        captured_at=captured,
                    )
                    match_map_id = repos.upsert_match_map(
                        match_id=match_id, map_id=map_ids[mapname]
                    )
                    repos.upsert_player_map_stat(
                        match_map_id=match_map_id,
                        player_id=player_id,
                        source_url=SRC,
                        captured_at=captured,
                        rating=1.0 + skill,
                        acs=150 + skill * 200,
                        kast=60 + skill * 30,
                        adr=100 + skill * 100,
                        kills=int(12 + skill * 18),
                        deaths=14,
                        assists=5,
                    )
    session.flush()
