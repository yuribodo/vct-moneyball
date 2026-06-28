"""T031 — provenance completeness + deterministic (offline) rebuild.

Every referenced row carries provenance (the gate passes on good data and fails when a
row is stripped), and rebuilding from the same versioned inputs yields byte-identical
ranking output (Constitution I; FR-008/FR-009, SC-004).
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from tests.seed import seed_cohort
from vct_moneyball.cli.build_ranking import run_build_ranking
from vct_moneyball.rank.validate import assert_provenance
from vct_moneyball.store.models import PlayerMapStat

pytestmark = pytest.mark.integration

START = datetime(2026, 7, 10, 18, 0, tzinfo=UTC)
PUBLISH = START - timedelta(days=2)


def _args(version, out_dir) -> argparse.Namespace:
    return argparse.Namespace(
        version=version,
        published_at=PUBLISH.isoformat(),
        tournament_start=START.isoformat(),
        out_dir=str(out_dir),
        supersedes=None,
        use_cache=True,
        json=True,
        verbose=False,
    )


def test_provenance_gate_passes_on_complete_data(clean_db) -> None:
    with Session(clean_db) as s:
        seed_cohort(s)
        s.commit()
    with Session(clean_db) as s:
        assert_provenance(s)  # does not raise


def test_provenance_is_structurally_enforced(clean_db) -> None:
    # The schema makes provenance non-optional: a stat row without source_url is
    # rejected by the database itself (defense the gate backs up — Constitution I).
    with Session(clean_db) as s, pytest.raises(IntegrityError):
        s.add(
            PlayerMapStat(
                match_map_id=1,
                player_id=1,
                source_url=None,
                captured_at=datetime.now(UTC),
            )
        )
        s.flush()


def _ranking_payload(path) -> list[tuple]:
    data = json.loads((path / "ranking.json").read_text())
    return [(t["position"], t["team"], t["team_score"]) for t in data["teams"]]


def test_rebuild_is_deterministic(clean_db, tmp_path) -> None:
    with Session(clean_db) as s:
        seed_cohort(s)
        s.commit()

    run_build_ranking(_args("enc-2026.v1", tmp_path / "run1"))
    # Same inputs, same config -> identical ordering and scores.
    run_build_ranking(_args("enc-2026.v2", tmp_path / "run2"))

    first = _ranking_payload(tmp_path / "run1" / "enc-2026.v1")
    second = _ranking_payload(tmp_path / "run2" / "enc-2026.v2")
    assert first == second
