"""``vctm predict-match`` — predict a single upcoming matchup (read-only).

Loads a trained model (latest run by default), rebuilds each team's as-of features from the
labeled history strictly before ``--as-of``, and reports calibrated win probabilities, the
predicted winner, and a low-confidence flag when either team is below the history threshold.
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime, timedelta

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from vct_moneyball.common.logging import CliError, get_logger
from vct_moneyball.predict import tracking
from vct_moneyball.predict.features import FeatureConfig, features_as_of
from vct_moneyball.predict.labels import load_labeled_matches
from vct_moneyball.predict.model import WinrateModel, is_low_confidence
from vct_moneyball.store.db import make_engine, session_scope
from vct_moneyball.store.models import Team


def _parse_ts(value: str | None) -> datetime:
    if value is None:
        return datetime.now(UTC)
    dt = datetime.fromisoformat(value)
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)


def _resolve_team(session: Session, ref: str) -> tuple[int, str]:
    row = session.execute(
        select(Team.id, Team.name).where(or_(Team.name == ref, Team.vlr_team_id == ref))
    ).first()
    if row is None:
        raise CliError(f"team {ref!r} not found (by name or vlr id)")
    return int(row[0]), row[1]


def _load_model(run: str | None) -> WinrateModel:
    import mlflow

    tracking.configure_tracking()
    run_id = run
    if run_id is None:
        runs = mlflow.search_runs(search_all_experiments=True, order_by=["start_time DESC"])
        runs = runs[runs.get("params.purpose", "") == "train"] if "params.purpose" in runs else runs
        if runs.empty:
            raise CliError("no trained run found; run `vctm train-winrate` first")
        run_id = runs.iloc[0]["run_id"]
    estimator = mlflow.sklearn.load_model(f"runs:/{run_id}/model")
    from vct_moneyball.predict.features import FEATURE_NAMES

    return WinrateModel(estimator=estimator, feature_names=FEATURE_NAMES, learner="loaded")


def run_predict_match(args: argparse.Namespace) -> int:
    log = get_logger()
    as_of = _parse_ts(getattr(args, "as_of", None))
    cfg = FeatureConfig(lookback_months=args.lookback_months)
    window_start = as_of - timedelta(days=30 * cfg.lookback_months)

    with session_scope(make_engine()) as session:
        a_id, a_name = _resolve_team(session, args.team_a)
        b_id, b_name = _resolve_team(session, args.team_b)
        matches = load_labeled_matches(session, window_start, as_of)

    model = _load_model(getattr(args, "run", None))
    feats, min_vol = features_as_of(matches, a_id, b_id, as_of, cfg)
    p_a = model.predict_proba_a(feats)
    p_b = 1.0 - p_a
    winner = a_name if p_a >= p_b else b_name
    low_conf = is_low_confidence(min_vol)

    if args.json:
        print(
            json.dumps(
                {
                    "team_a": a_name,
                    "team_b": b_name,
                    "p_a": round(p_a, 4),
                    "p_b": round(p_b, 4),
                    "winner": winner,
                    "low_confidence": low_conf,
                }
            )
        )
    else:
        flag = "  ⚠️ low confidence (sparse history)" if low_conf else ""
        log.info("prediction as of %s%s", as_of.date(), flag)
        print(f"  {a_name}: {p_a:.1%}")
        print(f"  {b_name}: {p_b:.1%}")
        print(f"  predicted winner: {winner}")
    return 0
