"""T030 — immutability: never overwrite a version/dir; --supersedes links a revision."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from tests.seed import seed_cohort
from vct_moneyball.cli.build_ranking import run_build_ranking
from vct_moneyball.common.logging import CliError
from vct_moneyball.store.models import Ranking

pytestmark = pytest.mark.integration

START = datetime(2026, 7, 10, 18, 0, tzinfo=UTC)
PUBLISH = START - timedelta(days=2)


def _args(version, out_dir, supersedes=None) -> argparse.Namespace:
    return argparse.Namespace(
        version=version,
        published_at=PUBLISH.isoformat(),
        tournament_start=START.isoformat(),
        out_dir=str(out_dir),
        supersedes=supersedes,
        use_cache=True,
        json=True,
        verbose=False,
    )


def test_refuses_to_overwrite_existing_version(clean_db, tmp_path) -> None:
    with Session(clean_db) as s:
        seed_cohort(s)
        s.commit()

    assert run_build_ranking(_args("enc-2026.v1", tmp_path)) == 0
    # Re-running the same version must fail without overwriting.
    with pytest.raises(CliError, match="already exists|overwrite"):
        run_build_ranking(_args("enc-2026.v1", tmp_path))


def test_supersedes_creates_new_artifact_linked_to_original(clean_db, tmp_path) -> None:
    with Session(clean_db) as s:
        seed_cohort(s)
        s.commit()

    run_build_ranking(_args("enc-2026.v1", tmp_path))
    run_build_ranking(_args("enc-2026.v2", tmp_path, supersedes="enc-2026.v1"))

    with Session(clean_db) as s:
        v1 = s.execute(select(Ranking).where(Ranking.version == "enc-2026.v1")).scalar_one()
        v2 = s.execute(select(Ranking).where(Ranking.version == "enc-2026.v2")).scalar_one()
        assert v2.supersedes_ranking_id == v1.id

    assert (tmp_path / "enc-2026.v1" / "ranking.json").is_file()
    assert (tmp_path / "enc-2026.v2" / "ranking.json").is_file()


def test_supersedes_unknown_version_fails(clean_db, tmp_path) -> None:
    with Session(clean_db) as s:
        seed_cohort(s)
        s.commit()
    with pytest.raises(CliError, match="supersedes"):
        run_build_ranking(_args("enc-2026.v2", tmp_path, supersedes="enc-2026.v9"))
