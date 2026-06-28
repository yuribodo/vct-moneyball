"""T037 — evaluate writes outcome_comparison, reports vs baseline, no mutation."""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from tests.seed import seed_cohort
from vct_moneyball.cli.build_ranking import run_build_ranking
from vct_moneyball.cli.evaluate import run_evaluate
from vct_moneyball.store.models import OutcomeComparison, RankingEntry, Team

pytestmark = pytest.mark.integration

START = datetime(2026, 7, 10, 18, 0, tzinfo=UTC)
PUBLISH = START - timedelta(days=2)


def _build(out_dir) -> argparse.Namespace:
    return argparse.Namespace(
        version="enc-2026.v1",
        published_at=PUBLISH.isoformat(),
        tournament_start=START.isoformat(),
        out_dir=str(out_dir),
        supersedes=None,
        use_cache=True,
        json=True,
        verbose=False,
    )


def _predicted_order(engine) -> list[str]:
    with Session(engine) as s:
        rows = s.execute(
            select(Team.name)
            .join(RankingEntry, RankingEntry.team_id == Team.id)
            .order_by(RankingEntry.position)
        ).all()
    return [r[0] for r in rows]


def test_evaluate_writes_rows_and_leaves_ranking_untouched(clean_db, tmp_path) -> None:
    with Session(clean_db) as s:
        seed_cohort(s)
        s.commit()
    run_build_ranking(_build(tmp_path))

    predicted = _predicted_order(clean_db)
    # Final standings = predicted order with one adjacent swap; baseline = reverse.
    final = predicted[:]
    final[0], final[1] = final[1], final[0]
    standings = {
        "source": "https://example.test/final",
        "final": final,
        "baselines": {"vlr-seed": list(reversed(predicted))},
    }
    sfile = tmp_path / "standings.json"
    sfile.write_text(json.dumps(standings))

    args = argparse.Namespace(
        version="enc-2026.v1",
        standings=str(sfile),
        baseline="vlr-seed",
        metric=None,
        json=True,
        verbose=False,
    )
    assert run_evaluate(args) == 0

    with Session(clean_db) as s:
        n = s.execute(select(func.count()).select_from(OutcomeComparison)).scalar_one()
        assert n == 3  # spearman_rho, kendall_tau, top4_hit_rate
        rows = s.execute(
            select(
                OutcomeComparison.metric,
                OutcomeComparison.predicted_value,
                OutcomeComparison.baseline_value,
            )
        ).all()
        by_metric = {m: (float(p), float(b)) for m, p, b in rows}
        # Prediction is near-perfect (one swap); baseline is reversed -> prediction wins.
        assert by_metric["spearman_rho"][0] > by_metric["spearman_rho"][1]

    # The ranking entries are unchanged (read-only evaluation).
    assert _predicted_order(clean_db) == predicted


def test_evaluate_unknown_version_fails(clean_db, tmp_path) -> None:
    sfile = tmp_path / "s.json"
    sfile.write_text(json.dumps({"source": "x", "final": ["A", "B"]}))
    args = argparse.Namespace(
        version="enc-2026.v9",
        standings=str(sfile),
        baseline="vlr-seed",
        metric=None,
        json=True,
        verbose=False,
    )
    with pytest.raises(Exception):  # noqa: B017
        run_evaluate(args)
