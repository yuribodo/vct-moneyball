"""``vctm backfill-results`` — populate match identity + outcome from cached HTML.

Offline re-parse (no scraping): for every collected match, read its cached page, parse the
header (both teams + series score + winner), upsert a ``team`` row per side, and record the
result on the match. Matches with no parseable result are left unlabeled and counted — never
guessed (Constitution I). Idempotent.
"""

from __future__ import annotations

import argparse
import json

from sqlalchemy import select

from vct_moneyball.cli.collect import _raw_cache_root
from vct_moneyball.collect.parse import parse_match
from vct_moneyball.common.logging import CliError, get_logger
from vct_moneyball.store.db import make_engine, session_scope
from vct_moneyball.store.models import Match
from vct_moneyball.store.repositories import Repositories


def run_backfill_results(args: argparse.Namespace) -> int:
    log = get_logger()
    cache = _raw_cache_root()
    engine = make_engine()

    labeled = unlabeled = no_cache = 0
    with session_scope(engine) as session:
        repos = Repositories(session)
        matches = session.execute(select(Match.id, Match.source_url)).all()
        if not matches:
            raise CliError("no matches found; run `vctm collect` first")

        for match_id, source_url in matches:
            cached = cache.read_latest(source_url)
            if cached is None:
                no_cache += 1
                continue
            parsed = parse_match(cached.html, source_url=source_url, captured_at=cached.captured_at)
            ta, tb = parsed.team_a, parsed.team_b
            if not (ta and tb and ta.vlr_team_id and tb.vlr_team_id and parsed.winner_vlr_team_id):
                unlabeled += 1
                continue

            # Per-match savepoint: one bad row never rolls back the whole backfill.
            try:
                with session.begin_nested():
                    a_id = repos.upsert_team_by_vlr(
                        name=ta.name,
                        vlr_team_id=ta.vlr_team_id,
                        source_url=source_url,
                        captured_at=cached.captured_at,
                    )
                    b_id = repos.upsert_team_by_vlr(
                        name=tb.name,
                        vlr_team_id=tb.vlr_team_id,
                        source_url=source_url,
                        captured_at=cached.captured_at,
                    )
                    winner_id = a_id if parsed.winner_vlr_team_id == ta.vlr_team_id else b_id
                    repos.set_match_outcome(
                        match_id=match_id,
                        team_a_id=a_id,
                        team_b_id=b_id,
                        winner_team_id=winner_id,
                        score_a=parsed.score_a,
                        score_b=parsed.score_b,
                    )
                labeled += 1
            except Exception as exc:  # noqa: BLE001 - isolate and report, don't abort batch
                log.warning("skipped match %s: %s", source_url, str(exc).splitlines()[0])
                unlabeled += 1

    summary = {"labeled": labeled, "unlabeled": unlabeled, "no_cache": no_cache}
    if args.json:
        print(json.dumps(summary))
    else:
        log.info(
            "backfilled %d matches with results; %d unlabeled, %d without cache",
            labeled,
            unlabeled,
            no_cache,
        )
    return 0
