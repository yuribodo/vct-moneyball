"""T028 — single real match, end-to-end (Constitution III, NON-NEGOTIABLE gate).

Proves the whole collect chain on one *real* captured VLR.gg match: parse the cached
HTML and persist it through the upsert repositories, asserting one ``player_map_stat``
per player per map, every row carrying provenance, and that re-running is idempotent
(deterministic offline rebuild).
"""

from __future__ import annotations

import pathlib
from datetime import UTC, datetime

import pytest
from sqlalchemy import func, select

from vct_moneyball.collect.parse import parse_match
from vct_moneyball.store.models import Match, MatchMap, Player, PlayerMapStat
from vct_moneyball.store.repositories import Repositories

pytestmark = pytest.mark.integration

FIXTURE = pathlib.Path(__file__).parent.parent / "fixtures" / "vlr" / "match_706327.html"
SOURCE_URL = (
    "https://www.vlr.gg/706327/qor-vs-yft-challengers-2026-north-america-ace-stage-3-r6-3-2"
)
CAPTURED_AT = datetime(2026, 6, 27, 20, 0, tzinfo=UTC)


def _persist(session) -> int:
    """Parse the fixture and persist it; return the match id."""
    match = parse_match(FIXTURE.read_text(), source_url=SOURCE_URL, captured_at=CAPTURED_AT)
    repos = Repositories(session)
    match_id = repos.upsert_match(
        vlr_match_id=match.vlr_match_id,
        event=match.event,
        played_at=match.played_at or CAPTURED_AT,
        source_url=match.source_url,
        captured_at=match.captured_at,
    )
    for parsed_map in match.maps:
        map_id = repos.upsert_map(name=parsed_map.map_name)
        match_map_id = repos.upsert_match_map(match_id=match_id, map_id=map_id)
        for stat in parsed_map.players:
            player_id = repos.upsert_player(
                handle=stat.handle,
                vlr_player_id=stat.vlr_player_id,
                source_url=stat.source_url,
                captured_at=stat.captured_at,
            )
            repos.upsert_player_map_stat(
                match_map_id=match_map_id,
                player_id=player_id,
                source_url=stat.source_url,
                captured_at=stat.captured_at,
                rating=stat.rating,
                acs=stat.acs,
                kast=stat.kast,
                adr=stat.adr,
                kills=stat.kills,
                deaths=stat.deaths,
                assists=stat.assists,
            )
    session.flush()
    return match_id


def test_real_match_persists_with_full_provenance(db_session) -> None:
    match_id = _persist(db_session)

    # 3 maps, 10 players each -> 30 stat rows.
    n_maps = db_session.execute(
        select(func.count()).select_from(MatchMap).where(MatchMap.match_id == match_id)
    ).scalar_one()
    assert n_maps == 3

    n_stats = db_session.execute(select(func.count()).select_from(PlayerMapStat)).scalar_one()
    assert n_stats == 30

    # Every stat row carries provenance.
    missing = db_session.execute(
        select(func.count())
        .select_from(PlayerMapStat)
        .where((PlayerMapStat.source_url.is_(None)) | (PlayerMapStat.captured_at.is_(None)))
    ).scalar_one()
    assert missing == 0

    # The match itself carries provenance.
    match = db_session.get(Match, match_id)
    assert match is not None and match.source_url == SOURCE_URL


def test_known_player_row_roundtrips(db_session) -> None:
    _persist(db_session)
    kumi = db_session.execute(select(Player).where(Player.vlr_player_id == "25745")).scalar_one()
    stat = db_session.execute(
        select(PlayerMapStat).where(PlayerMapStat.player_id == kumi.id).limit(1)
    ).scalar_one()
    assert stat.source_url == SOURCE_URL


def test_reingest_is_idempotent(db_session) -> None:
    _persist(db_session)
    _persist(db_session)  # second pass must not duplicate
    n_stats = db_session.execute(select(func.count()).select_from(PlayerMapStat)).scalar_one()
    assert n_stats == 30
