"""``vctm collect`` — gather the ENC cohort + in-window matches into Postgres.

Resolves the 16 ENC teams (runtime data via config/env), persists their active
rosters, discovers each team's in-window matches, and stores per-map player stats with
provenance. Exits non-zero if the cohort is not exactly 16 teams or the source is
unreachable with no cache (CLI contract; SC-001/SC-004).
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from vct_moneyball.collect.cache import RawHtmlCache
from vct_moneyball.collect.client import Fetcher
from vct_moneyball.collect.parse import parse_match
from vct_moneyball.collect.targets import (
    discover_rosters,
    parse_match_urls,
    resolve_cohort_team_urls,
)
from vct_moneyball.common.logging import CliError, get_logger
from vct_moneyball.config import DEFAULT_CONFIG
from vct_moneyball.store.db import make_engine, session_scope
from vct_moneyball.store.repositories import Repositories

ENC_TEAM_COUNT = 16

# Sentinel "map" labels VLR uses for undecided maps — not real map identities.
_NON_MAP_NAMES = {"TBD"}


@dataclass
class CollectSummary:
    teams: int = 0
    players: int = 0
    matches: int = 0
    stat_rows: int = 0
    maps: int = 0

    def as_dict(self) -> dict[str, int]:
        return {
            "teams": self.teams,
            "players": self.players,
            "matches": self.matches,
            "stat_rows": self.stat_rows,
            "maps": self.maps,
        }


def _raw_cache_root() -> RawHtmlCache:
    # Repo-root data/ dir (git-ignored, DVC-trackable).
    for base in [pathlib.Path.cwd(), *pathlib.Path(__file__).resolve().parents]:
        if (base / ".git").is_dir() or (base / "services" / "core").is_dir():
            return RawHtmlCache(base / "data" / "raw_html" / "vlr")
    return RawHtmlCache(pathlib.Path.cwd() / "data" / "raw_html" / "vlr")


def _team_matches_url(team_url: str) -> str:
    m = re.search(r"/team/(\d+)/([a-z0-9-]+)", team_url)
    if not m:
        return team_url
    return f"https://www.vlr.gg/team/matches/{m.group(1)}/{m.group(2)}/?group=completed"


def run_collect(args: argparse.Namespace) -> int:
    log = get_logger()
    config = DEFAULT_CONFIG
    window_months = args.window_months or config.data_window_months
    cutoff = (
        datetime.fromisoformat(args.cutoff).replace(tzinfo=UTC)
        if getattr(args, "cutoff", None)
        else datetime.now(UTC)
    )
    window_start = cutoff - timedelta(days=30 * window_months)

    fetcher = Fetcher(
        _raw_cache_root(),
        rate_limit_per_min=args.rate_limit,
        use_cache=args.use_cache,
    )

    team_urls = resolve_cohort_team_urls(fetcher)
    if len(team_urls) != ENC_TEAM_COUNT:
        raise CliError(f"expected exactly {ENC_TEAM_COUNT} ENC teams, resolved {len(team_urls)}")

    rosters = discover_rosters(fetcher, team_urls)
    for r in rosters:
        if not any(m.is_active for m in r.members):
            raise CliError(f"team {r.name!r} has no active roster players")

    engine = make_engine()
    summary = CollectSummary()
    seen_players: set[str] = set()
    seen_matches: set[str] = set()
    seen_maps: set[str] = set()

    with session_scope(engine) as session:
        repos = Repositories(session)
        for roster in rosters:
            now = datetime.now(UTC)
            team_id = repos.upsert_team(
                name=roster.name,
                country=roster.country,
                source_url=roster.team_url,
                captured_at=now,
                vlr_team_id=roster.vlr_team_id,
                is_enc_2026=True,
            )
            summary.teams += 1
            for member in roster.members:
                if not member.is_active:
                    continue
                player_id = repos.upsert_player(
                    handle=member.handle,
                    vlr_player_id=member.vlr_player_id,
                    source_url=member.player_url or roster.team_url,
                    captured_at=now,
                )
                repos.upsert_team_player(
                    team_id=team_id,
                    player_id=player_id,
                    source_url=roster.team_url,
                    captured_at=now,
                    role=member.role,
                    is_active=True,
                )
                seen_players.add(member.vlr_player_id or member.handle)

            # Discover + persist this team's in-window matches.
            try:
                listing = fetcher.fetch(_team_matches_url(roster.team_url))
            except CliError as exc:
                log.warning("match listing unavailable for %s: %s", roster.name, exc)
                continue
            for match_url in parse_match_urls(listing.html):
                if match_url in seen_matches:
                    continue
                try:
                    page = fetcher.fetch(match_url)
                except CliError:
                    continue
                parsed = parse_match(page.html, source_url=match_url, captured_at=page.captured_at)
                if parsed.played_at and not (window_start <= parsed.played_at <= cutoff):
                    continue
                seen_matches.add(match_url)
                match_db_id = repos.upsert_match(
                    vlr_match_id=parsed.vlr_match_id,
                    event=parsed.event,
                    played_at=parsed.played_at or page.captured_at,
                    source_url=parsed.source_url,
                    captured_at=parsed.captured_at,
                )
                summary.matches += 1
                for pmap in parsed.maps:
                    in_pool = pmap.map_name.upper() not in _NON_MAP_NAMES
                    map_db_id = repos.upsert_map(name=pmap.map_name, in_pool=in_pool)
                    seen_maps.add(pmap.map_name)
                    match_map_id = repos.upsert_match_map(match_id=match_db_id, map_id=map_db_id)
                    for stat in pmap.players:
                        pid = repos.upsert_player(
                            handle=stat.handle,
                            vlr_player_id=stat.vlr_player_id,
                            source_url=stat.source_url,
                            captured_at=stat.captured_at,
                        )
                        repos.upsert_player_map_stat(
                            match_map_id=match_map_id,
                            player_id=pid,
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
                        summary.stat_rows += 1

    summary.players = len(seen_players)
    summary.maps = len(seen_maps)

    if args.json:
        print(json.dumps(summary.as_dict()))
    else:
        log.info(
            "collected %d teams, %d players, %d matches, %d stat rows across %d maps",
            summary.teams,
            summary.players,
            summary.matches,
            summary.stat_rows,
            summary.maps,
        )
    if summary.stat_rows == 0:
        print("warning: no player_map_stat rows collected", file=sys.stderr)
    return 0
