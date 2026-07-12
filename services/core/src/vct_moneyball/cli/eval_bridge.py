"""``vctm eval-bridge`` — honest, baseline-relative evaluation of roster-derived strength.

Builds bridge examples from real club matches (each side's roster strength as-of), runs a
verified temporal split, trains the calibrated model, and scores it against baselines on the
held-out future block — reusing feature-002's split/metrics/tracking. A bridge that does not
beat its baseline is reported as such (Constitution IV).
"""

from __future__ import annotations

import argparse
import json
import pathlib
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select

from vct_moneyball.bridge.baselines import DEFAULT_BRIDGE_BASELINES, baseline_probs
from vct_moneyball.bridge.features import build_bridge_examples
from vct_moneyball.bridge.player_rating import PlayerRatingConfig, load_player_matches
from vct_moneyball.bridge.report import build_report, validate_report, write_report
from vct_moneyball.common.artifact_pointers import write_pointer
from vct_moneyball.common.logging import CliError, get_logger
from vct_moneyball.predict import tracking
from vct_moneyball.predict.dataset import temporal_split
from vct_moneyball.predict.evaluate import compute_metrics
from vct_moneyball.predict.model import train
from vct_moneyball.store.db import make_engine, session_scope
from vct_moneyball.store.models import PlayerMapStat


def _parse_ts(value: str) -> datetime:
    dt = datetime.fromisoformat(value)
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)


def _default_out_dir() -> pathlib.Path:
    for base in [pathlib.Path.cwd(), *pathlib.Path(__file__).resolve().parents]:
        if (base / ".git").is_dir() or (base / "services" / "core").is_dir():
            return base / "artifacts" / "models" / "bridge"
    return pathlib.Path.cwd() / "artifacts" / "models" / "bridge"


def run_eval_bridge(args: argparse.Namespace) -> int:
    log = get_logger()
    cutoff = _parse_ts(args.cutoff)
    cfg = PlayerRatingConfig()
    aggregation = args.aggregation
    window_start = cutoff - timedelta(days=30 * args.lookback_months)
    window_end = datetime.now(UTC)

    with session_scope(make_engine()) as session:
        matches = load_player_matches(session, window_start, window_end)
        total = session.execute(select(func.count()).select_from(PlayerMapStat)).scalar_one()
        attributed = session.execute(
            select(func.count()).select_from(PlayerMapStat).where(PlayerMapStat.team_id.isnot(None))
        ).scalar_one()
    if not matches:
        raise CliError("no attributed matches; run `vctm backfill-sides` first")
    coverage = (attributed / total) if total else 0.0

    examples = build_bridge_examples(matches, cfg=cfg, aggregation=aggregation)
    dataset = temporal_split(examples, cutoff)
    baselines = tuple(args.baseline) if args.baseline else DEFAULT_BRIDGE_BASELINES
    model = train(dataset.train, learner="logreg")

    y_eval = [e.label for e in dataset.eval]
    model_metrics = compute_metrics(y_eval, model.predict_block(dataset.eval))
    baseline_metrics = [
        (label, compute_metrics(y_eval, baseline_probs(label, dataset.eval))) for label in baselines
    ]

    fp = tracking.fingerprint({**cfg.as_dict(), "aggregation": aggregation})
    data_window = (min(e.played_at for e in examples), max(e.played_at for e in examples))
    out_dir = pathlib.Path(args.out_dir) if getattr(args, "out_dir", None) else _default_out_dir()
    params = {
        "aggregation": aggregation,
        "cutoff": args.cutoff,
        "lookback_months": args.lookback_months,
        "feature_fingerprint": fp,
        "n_train": len(dataset.train),
        "n_eval": len(dataset.eval),
        "attribution_coverage": round(coverage, 4),
    }

    with tracking.run(args.experiment, params) as active:
        run_id = active.info.run_id
        tracking.log_metrics("bridge", model_metrics.as_dict())
        for label, m in baseline_metrics:
            tracking.log_metrics(f"base_{label}", m.as_dict())
        report = build_report(
            run_id=run_id,
            created_at=datetime.now(UTC),
            cutoff=cutoff,
            data_window=data_window,
            feature_fingerprint=fp,
            aggregation=aggregation,
            n_train=len(dataset.train),
            n_eval=len(dataset.eval),
            attribution_coverage=coverage,
            underpowered=dataset.underpowered,
            model=model_metrics,
            baselines=baseline_metrics,
        )
        validate_report(report)
        written = write_report(report, out_dir)
        tracking.log_artifact(written / "report.json")
        if getattr(args, "publish", False):
            write_pointer(out_dir / "LATEST_EVAL", written.name)

    best = min(baseline_metrics, key=lambda lm: lm[1].log_loss)
    beats = model_metrics.log_loss < best[1].log_loss
    if args.json:
        print(json.dumps({"run_id": run_id, "report_dir": str(written), "beats_baseline": beats}))
    else:
        log.info(
            "wrote bridge eval report to %s (attribution coverage %.1f%%)", written, coverage * 100
        )
        print(f"{'predictor':<14} {'log-loss':>9} {'acc':>7} {'brier':>7}")
        mm = model_metrics
        print(f"{'bridge':<14} {mm.log_loss:>9.4f} {mm.accuracy:>7.4f} {mm.brier:>7.4f}")
        for label, m in baseline_metrics:
            print(f"{label:<14} {m.log_loss:>9.4f} {m.accuracy:>7.4f} {m.brier:>7.4f}")
        print(f"\nbridge {'BEATS' if beats else 'does NOT beat'} best baseline ({best[0]}).")
    return 0
