"""``vctm evaluate`` — compare a locked ranking to final standings (post-tournament).

Reads the named (frozen) ranking, loads + validates the final standings, computes the
requested rank-agreement metrics for the prediction and a baseline, writes
``outcome_comparison`` rows, and reports predicted vs. baseline. The ranking is never
mutated (CLI contract; SC-006, FR-011).
"""

from __future__ import annotations

import argparse
import json

from vct_moneyball.common.logging import get_logger
from vct_moneyball.evaluate.compare import compare
from vct_moneyball.evaluate.metrics import DEFAULT_METRICS
from vct_moneyball.evaluate.standings import load_standings
from vct_moneyball.store.db import make_engine, session_scope


def run_evaluate(args: argparse.Namespace) -> int:
    log = get_logger()
    metrics = tuple(args.metric) if getattr(args, "metric", None) else DEFAULT_METRICS
    standings = load_standings(args.standings)

    engine = make_engine()
    with session_scope(engine) as session:
        results = compare(
            session,
            version=args.version,
            standings=standings,
            baseline_label=args.baseline,
            metrics=metrics,
        )

    payload = [
        {
            "metric": r.metric,
            "predicted": round(r.predicted_value, 4),
            "baseline_label": r.baseline_label,
            "baseline": round(r.baseline_value, 4),
            "delta": round(r.predicted_value - r.baseline_value, 4),
        }
        for r in results
    ]
    if args.json:
        print(json.dumps({"version": args.version, "results": payload}))
    else:
        log.info("evaluation of %s vs baseline %r:", args.version, args.baseline)
        for row in payload:
            verdict = "beats" if row["delta"] > 0 else ("ties" if row["delta"] == 0 else "loses to")
            print(
                f"  {row['metric']:<16} predicted={row['predicted']:+.4f}  "
                f"baseline({row['baseline_label']})={row['baseline']:+.4f}  "
                f"-> {verdict} baseline"
            )
    return 0
