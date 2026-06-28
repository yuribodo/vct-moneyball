"""T029 — build-ranking refuses to publish inside the 24h lock window (FR-007)."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from tests.seed import seed_cohort
from vct_moneyball.cli.build_ranking import run_build_ranking
from vct_moneyball.common.logging import CliError
from vct_moneyball.store.models import Ranking

pytestmark = pytest.mark.integration

START = datetime(2026, 7, 10, 18, 0, tzinfo=UTC)


def _args(published_at: datetime, out_dir, version="enc-2026.v1") -> argparse.Namespace:
    return argparse.Namespace(
        version=version,
        published_at=published_at.isoformat(),
        tournament_start=START.isoformat(),
        out_dir=str(out_dir),
        supersedes=None,
        use_cache=True,
        json=True,
        verbose=False,
    )


def test_rejects_publish_within_24h_and_writes_nothing(clean_db, tmp_path) -> None:
    with Session(clean_db) as s:
        seed_cohort(s)
        s.commit()

    too_late = START - timedelta(hours=12)  # inside the lock window
    with pytest.raises(CliError, match="lock deadline"):
        run_build_ranking(_args(too_late, tmp_path))

    # Nothing written to disk or DB.
    assert not any(tmp_path.iterdir())
    with Session(clean_db) as s:
        assert s.execute(select(func.count()).select_from(Ranking)).scalar_one() == 0


def test_allows_publish_before_deadline(clean_db, tmp_path) -> None:
    with Session(clean_db) as s:
        seed_cohort(s)
        s.commit()

    on_time = START - timedelta(days=2)  # safely before the deadline
    rc = run_build_ranking(_args(on_time, tmp_path))
    assert rc == 0
    with Session(clean_db) as s:
        assert s.execute(select(func.count()).select_from(Ranking)).scalar_one() == 1
