"""``vctm build-ranking`` — score, aggregate, and write the locked artifact.

Loads the persisted cohort + in-window stats, scores players per map, aggregates to an
ordered 16-team ranking, then writes a dated, schema-valid, immutable artifact (JSON +
Markdown) and the append-only ``ranking*`` rows. Enforces every publish gate: lock
deadline (FR-007), provenance (FR-009), full map coverage (FR-004), version/dir
immutability (FR-006/FR-008), and ``--supersedes`` linkage (Constitution II).
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from vct_moneyball.common.logging import CliError, get_logger
from vct_moneyball.config import DEFAULT_CONFIG
from vct_moneyball.rank.aggregate import aggregate_ranking
from vct_moneyball.rank.artifact import build_artifact, validate_artifact, write_artifact
from vct_moneyball.rank.validate import assert_cohort, assert_lock_deadline, assert_provenance
from vct_moneyball.score.player import score_players
from vct_moneyball.store.db import make_engine, session_scope
from vct_moneyball.store.models import (
    Map,
    Ranking,
    RankingEntry,
    RankingMapBreakdown,
    Team,
)
from vct_moneyball.store.queries import load_map_pool, load_stat_rows, load_teams

VERSION_RE = re.compile(r"^enc-2026\.v[0-9]+$")


def _parse_ts(value: str | None, *, default: datetime | None = None) -> datetime:
    if value is None:
        if default is None:
            raise CliError("missing timestamp")
        return default
    dt = datetime.fromisoformat(value)
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)


def _default_out_dir() -> pathlib.Path:
    for base in [pathlib.Path.cwd(), *pathlib.Path(__file__).resolve().parents]:
        if (base / ".git").is_dir() or (base / "services" / "core").is_dir():
            return base / "artifacts" / "rankings" / "enc-2026"
    return pathlib.Path.cwd() / "artifacts" / "rankings" / "enc-2026"


def run_build_ranking(args: argparse.Namespace) -> int:
    log = get_logger()
    config = DEFAULT_CONFIG

    if not VERSION_RE.match(args.version):
        raise CliError(f"invalid --version {args.version!r}; expected pattern enc-2026.vN")

    published_at = _parse_ts(getattr(args, "published_at", None), default=datetime.now(UTC))
    tournament_start = _parse_ts(args.tournament_start)

    # Gate 1: lock deadline (write nothing if violated).
    assert_lock_deadline(published_at, tournament_start)

    window_end = published_at
    window_start = window_end - timedelta(days=30 * config.data_window_months)
    out_dir = pathlib.Path(args.out_dir) if getattr(args, "out_dir", None) else _default_out_dir()

    engine = make_engine()
    with session_scope(engine) as session:
        # Gate 2: cohort + provenance (write nothing if violated).
        assert_cohort(session)
        assert_provenance(session)

        # Immutability: version must be new (append-only).
        existing = session.execute(
            select(Ranking.id).where(Ranking.version == args.version)
        ).scalar_one_or_none()
        if existing is not None:
            raise CliError(f"ranking version {args.version!r} already exists (immutable)")

        supersedes_id: int | None = None
        if getattr(args, "supersedes", None):
            supersedes_id = session.execute(
                select(Ranking.id).where(Ranking.version == args.supersedes)
            ).scalar_one_or_none()
            if supersedes_id is None:
                raise CliError(f"--supersedes {args.supersedes!r} not found")

        map_pool = load_map_pool(session)
        if not map_pool:
            raise CliError("no in-pool maps found; run `vctm collect` first")
        teams = load_teams(session)
        rows = load_stat_rows(session, window_start, window_end)
        scores = score_players(rows, config)
        ranking = aggregate_ranking(teams, scores, map_pool, config)

        artifact = build_artifact(
            ranking,
            version=args.version,
            published_at=published_at,
            tournament_start=tournament_start,
            data_window=(window_start, window_end),
            config_hash=config.config_hash,
            map_pool=map_pool,
            supersedes=getattr(args, "supersedes", None),
        )
        validate_artifact(artifact)

        # Gate 3: full map coverage for every team.
        pool_set = set(map_pool)
        for t in artifact["teams"]:
            covered = {b["map"] for b in t["map_breakdown"]}
            if not pool_set <= covered:
                raise CliError(f"team {t['team']!r} missing maps: {pool_set - covered}")

        # Write the artifact directory (refuses to overwrite — immutable).
        written = write_artifact(artifact, out_dir, slug=args.version)

        # Persist append-only ranking* rows.
        team_id_by_name = {
            name: tid
            for tid, name in session.execute(
                select(Team.id, Team.name).where(Team.is_enc_2026.is_(True))
            ).all()
        }
        map_id_by_name = {
            name: mid for mid, name in session.execute(select(Map.id, Map.name)).all()
        }
        ranking_row = Ranking(
            published_at=published_at,
            tournament_start=tournament_start,
            version=args.version,
            data_window_start=window_start,
            data_window_end=window_end,
            config_hash=config.config_hash,
            supersedes_ranking_id=supersedes_id,
        )
        session.add(ranking_row)
        session.flush()
        for t in ranking:
            session.add(
                RankingEntry(
                    ranking_id=ranking_row.id,
                    team_id=team_id_by_name[t.team],
                    position=t.position,
                    team_score=round(t.team_score, 4),
                    confidence=t.confidence,
                )
            )
            for b in t.map_breakdown:
                session.add(
                    RankingMapBreakdown(
                        ranking_id=ranking_row.id,
                        team_id=team_id_by_name[t.team],
                        map_id=map_id_by_name[b.map],
                        map_score=round(b.map_score, 4),
                        confidence=b.confidence,
                    )
                )

    if args.json:
        print(json.dumps({"artifact_dir": str(written), "version": args.version}))
    else:
        log.info("wrote ranking artifact to %s", written)
        for t in ranking:
            print(f"{t.position:>2}. {t.team:<24} {t.team_score:.4f}  ({t.confidence})")
    return 0
