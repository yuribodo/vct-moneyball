"""Comparison service: locked ranking vs. final standings, predicted vs. baseline.

For each requested metric, scores the predicted order and a baseline order against the
actual final standings and writes one ``outcome_comparison`` row per metric. The locked
ranking is read-only input (Constitution II; FR-011, SC-006).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from vct_moneyball.common.logging import CliError
from vct_moneyball.evaluate.metrics import DEFAULT_METRICS, compute_metric
from vct_moneyball.evaluate.standings import Standings
from vct_moneyball.store.models import Ranking, RankingEntry, Team


@dataclass(frozen=True)
class MetricResult:
    metric: str
    predicted_value: float
    baseline_label: str
    baseline_value: float


def predicted_order(session: Session, version: str) -> tuple[int, list[str]]:
    """Return ``(ranking_id, team names in predicted order)`` for a locked ranking."""
    ranking = session.execute(
        select(Ranking).where(Ranking.version == version)
    ).scalar_one_or_none()
    if ranking is None:
        raise CliError(f"ranking version {version!r} not found")
    rows = session.execute(
        select(Team.name)
        .join(RankingEntry, RankingEntry.team_id == Team.id)
        .where(RankingEntry.ranking_id == ranking.id)
        .order_by(RankingEntry.position)
    ).all()
    return ranking.id, [r[0] for r in rows]


def compare(
    session: Session,
    *,
    version: str,
    standings: Standings,
    baseline_label: str,
    metrics: tuple[str, ...] = DEFAULT_METRICS,
    evaluated_at: datetime | None = None,
) -> list[MetricResult]:
    """Compute + persist metric comparisons; returns the results.

    Raises if the ranking's team set does not match the final standings.
    """
    evaluated_at = evaluated_at or datetime.now(UTC)
    ranking_id, predicted = predicted_order(session, version)
    if set(predicted) != set(standings.final):
        raise CliError("ranking teams do not match the final standings team set")

    baseline = standings.baseline(baseline_label)
    results: list[MetricResult] = []
    for metric in metrics:
        predicted_value = compute_metric(metric, predicted, standings.final)
        baseline_value = compute_metric(metric, baseline, standings.final)
        results.append(
            MetricResult(
                metric=metric,
                predicted_value=predicted_value,
                baseline_label=baseline_label,
                baseline_value=baseline_value,
            )
        )

    # Persist append-only outcome_comparison rows (idempotent on the unique key).
    from sqlalchemy.dialects.postgresql import insert

    from vct_moneyball.store.models import OutcomeComparison

    for r in results:
        stmt = (
            insert(OutcomeComparison)
            .values(
                ranking_id=ranking_id,
                evaluated_at=evaluated_at,
                metric=r.metric,
                predicted_value=r.predicted_value,
                baseline_label=r.baseline_label,
                baseline_value=r.baseline_value,
                final_standings_source=standings.source,
            )
            .on_conflict_do_update(
                constraint="uq_outcome_comparison",
                set_={
                    "evaluated_at": evaluated_at,
                    "predicted_value": r.predicted_value,
                    "baseline_value": r.baseline_value,
                    "final_standings_source": standings.source,
                },
            )
        )
        session.execute(stmt)
    return results
