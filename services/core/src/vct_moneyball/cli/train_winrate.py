"""``vctm train-winrate`` — train + calibrate on matches before a cutoff, log the run.

Logs params, the data window, the feature/config fingerprint, and the calibrated model
artifact to MLflow so a prediction is traceable to its run (FR-008).
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime, timedelta

from vct_moneyball.common.logging import CliError, get_logger
from vct_moneyball.predict import tracking
from vct_moneyball.predict.features import FeatureConfig, build_examples
from vct_moneyball.predict.labels import load_labeled_matches
from vct_moneyball.predict.model import train
from vct_moneyball.store.db import make_engine, session_scope


def _parse_ts(value: str | None) -> datetime:
    if value is None:
        return datetime.now(UTC)
    dt = datetime.fromisoformat(value)
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)


def run_train_winrate(args: argparse.Namespace) -> int:
    log = get_logger()
    cutoff = _parse_ts(getattr(args, "cutoff", None))
    cfg = FeatureConfig(lookback_months=args.lookback_months)
    window_start = cutoff - timedelta(days=30 * cfg.lookback_months)

    with session_scope(make_engine()) as session:
        matches = load_labeled_matches(session, window_start, cutoff)
    if not matches:
        raise CliError("no labeled training matches; run `vctm backfill-results` first")
    examples = build_examples(matches, cfg)
    model = train(examples, learner=args.learner)

    fp = tracking.fingerprint({**cfg.as_dict(), "learner": args.learner})
    params = {
        "learner": args.learner,
        "cutoff": cutoff.isoformat(),
        "lookback_months": cfg.lookback_months,
        "feature_fingerprint": fp,
        "n_train": len(examples),
        "purpose": "train",
    }
    with tracking.run(args.experiment, params) as active:
        import mlflow

        run_id = active.info.run_id
        # cloudpickle (not skops) so the calibrated pipeline reloads without trusted-type prompts.
        mlflow.sklearn.log_model(model.estimator, name="model", serialization_format="cloudpickle")
        mlflow.log_dict(cfg.as_dict(), "feature_config.json")

    if args.json:
        print(json.dumps({"run_id": run_id, "n_train": len(examples), "fingerprint": fp}))
    else:
        log.info(
            "trained %s on %d matches before %s (run %s)",
            args.learner,
            len(examples),
            cutoff.date(),
            run_id,
        )
    return 0
