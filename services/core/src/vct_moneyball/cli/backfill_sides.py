"""``vctm backfill-sides`` — attribute each player_map_stat to its match side (offline).

Re-parses cached match HTML (no scraping) and sets the existing-but-null
``player_map_stat.team_id`` to the side (team_a/team_b) the player was on, via the parsed
stats-table index keyed by VLR player id. Rows that cannot be resolved are left null and
counted — never guessed (Constitution I). Idempotent.
"""

from __future__ import annotations

import argparse
import json

from sqlalchemy import select

from vct_moneyball.bridge.attribution import side_team_id, sides_for_match
from vct_moneyball.cli.collect import _raw_cache_root
from vct_moneyball.collect.parse import parse_match
from vct_moneyball.common.logging import CliError, get_logger
from vct_moneyball.store.db import make_engine, session_scope
from vct_moneyball.store.models import Match, MatchMap, Player, PlayerMapStat


def run_backfill_sides(args: argparse.Namespace) -> int:
    log = get_logger()
    cache = _raw_cache_root()
    engine = make_engine()

    attributed = unresolved = no_cache = 0
    with session_scope(engine) as session:
        matches = session.execute(
            select(Match.id, Match.source_url, Match.team_a_id, Match.team_b_id).where(
                Match.team_a_id.isnot(None), Match.team_b_id.isnot(None)
            )
        ).all()
        if not matches:
            raise CliError("no labeled matches; run `vctm backfill-results` first")

        for match_id, source_url, team_a_id, team_b_id in matches:
            cached = cache.read_latest(source_url)
            if cached is None:
                no_cache += 1
                continue
            parsed = parse_match(cached.html, source_url=source_url, captured_at=cached.captured_at)
            sides = sides_for_match(parsed)  # vlr_player_id -> side index

            stats = session.execute(
                select(PlayerMapStat, Player.vlr_player_id)
                .join(MatchMap, MatchMap.id == PlayerMapStat.match_map_id)
                .join(Player, Player.id == PlayerMapStat.player_id)
                .where(MatchMap.match_id == match_id)
            ).all()
            for stat, vlr_player_id in stats:
                side = sides.get(vlr_player_id) if vlr_player_id else None
                if side is None:
                    unresolved += 1
                    continue
                stat.team_id = side_team_id(side, team_a_id, team_b_id)
                attributed += 1

    summary = {"attributed": attributed, "unresolved": unresolved, "no_cache": no_cache}
    if args.json:
        print(json.dumps(summary))
    else:
        log.info(
            "attributed %d player-map stats to a side; %d unresolved, %d without cache",
            attributed,
            unresolved,
            no_cache,
        )
    return 0
