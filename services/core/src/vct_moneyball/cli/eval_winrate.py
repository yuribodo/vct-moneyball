"""``vctm eval-winrate`` — leakage-free, baseline-relative evaluation (the honesty gate).

Trains on matches before the cutoff, evaluates on/after, scores the model and each baseline
on the identical held-out block, writes a schema-valid traceable report, and logs the run to
MLflow. A model that does not beat its baseline is reported as such (Constitution IV).
"""

from __future__ import annotations

import argparse
import json
import pathlib
from datetime import UTC, datetime, timedelta

from vct_moneyball.common.artifact_pointers import write_pointer
from vct_moneyball.common.logging import CliError, get_logger
from vct_moneyball.predict import tracking
from vct_moneyball.predict.baselines import DEFAULT_BASELINES, baseline_probs
from vct_moneyball.predict.dataset import temporal_split
from vct_moneyball.predict.evaluate import compute_metrics
from vct_moneyball.predict.features import FeatureConfig, build_examples
from vct_moneyball.predict.labels import load_labeled_matches
from vct_moneyball.predict.model import train
from vct_moneyball.predict.report import build_report, validate_report, write_report
from vct_moneyball.store.db import make_engine, session_scope


def _parse_ts(value: str) -> datetime:
    dt = datetime.fromisoformat(value)
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)


def _default_out_dir() -> pathlib.Path:
    for base in [pathlib.Path.cwd(), *pathlib.Path(__file__).resolve().parents]:
        if (base / ".git").is_dir() or (base / "services" / "core").is_dir():
            return base / "artifacts" / "models" / "winrate"
    return pathlib.Path.cwd() / "artifacts" / "models" / "winrate"


def run_eval_winrate(args: argparse.Namespace) -> int:
    log = get_logger()
    cutoff = _parse_ts(args.cutoff)
    cfg = FeatureConfig(lookback_months=args.lookback_months)
    window_start = cutoff - timedelta(days=30 * cfg.lookback_months)
    window_end = datetime.now(UTC)

    with session_scope(make_engine()) as session:
        matches = load_labeled_matches(session, window_start, window_end)
    if not matches:
        raise CliError("no labeled matches; run `vctm backfill-results` first")
    examples = build_examples(matches, cfg)
    dataset = temporal_split(examples, cutoff)

    baselines = tuple(args.baseline) if args.baseline else DEFAULT_BASELINES
    calibration = getattr(args, "calibration", "auto")
    model = train(
        dataset.train,
        learner=args.learner,
        calibration_method=None if calibration == "auto" else calibration,
    )

    y_eval = [e.label for e in dataset.eval]
    model_metrics = compute_metrics(y_eval, model.predict_block(dataset.eval))
    baseline_metrics = [
        (label, compute_metrics(y_eval, baseline_probs(label, dataset.eval))) for label in baselines
    ]

    fp = tracking.fingerprint({**cfg.as_dict(), "learner": args.learner})
    params = {
        "learner": args.learner,
        "calibration_method": model.calibration_method,
        "cutoff": args.cutoff,
        "lookback_months": cfg.lookback_months,
        "feature_fingerprint": fp,
        "n_train": len(dataset.train),
        "n_eval": len(dataset.eval),
    }
    data_window = (
        min(e.played_at for e in examples),
        max(e.played_at for e in examples),
    )
    out_dir = pathlib.Path(args.out_dir) if getattr(args, "out_dir", None) else _default_out_dir()

    with tracking.run(args.experiment, params) as active:
        run_id = active.info.run_id
        tracking.log_metrics("model", model_metrics.as_dict())
        for label, m in baseline_metrics:
            tracking.log_metrics(f"base_{label}", m.as_dict())
        report = build_report(
            run_id=run_id,
            created_at=datetime.now(UTC),
            cutoff=cutoff,
            data_window=data_window,
            feature_fingerprint=fp,
            learner=args.learner,
            calibration_method=model.calibration_method,
            n_train=len(dataset.train),
            n_eval=len(dataset.eval),
            underpowered=dataset.underpowered,
            model=model_metrics,
            baselines=baseline_metrics,
        )
        validate_report(report)
        written = write_report(report, out_dir)
        tracking.log_artifact(written / "report.json")
        if getattr(args, "publish", False):
            write_pointer(out_dir / "LATEST", written.name)

    best = min(baseline_metrics, key=lambda lm: lm[1].log_loss)
    beats = model_metrics.log_loss < best[1].log_loss
    if args.json:
        print(json.dumps({"run_id": run_id, "report_dir": str(written), "beats_baseline": beats}))
    else:
        if dataset.underpowered:
            log.warning("eval block is small (%d matches) — metrics are noisy", len(dataset.eval))
        log.info("wrote eval report to %s", written)
        print(f"{'predictor':<14} {'log-loss':>9} {'acc':>7} {'brier':>7} {'calib':>7}")
        mm = model_metrics
        print(
            f"{'model':<14} {mm.log_loss:>9.4f} {mm.accuracy:>7.4f} {mm.brier:>7.4f} "
            f"{mm.calibration_error:>7.4f}"
        )
        for label, m in baseline_metrics:
            print(
                f"{label:<14} {m.log_loss:>9.4f} {m.accuracy:>7.4f} {m.brier:>7.4f} "
                f"{m.calibration_error:>7.4f}"
            )
        print(f"\nmodel {'BEATS' if beats else 'does NOT beat'} best baseline ({best[0]}).")
    return 0
