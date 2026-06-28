"""``vctm`` command-line entry point.

A single CLI exposes the pipeline stages: ``collect``, ``build-ranking``,
``evaluate``. Every command supports ``--json`` (machine-readable result on stdout);
human output and errors go to stderr; any validation failure exits non-zero
(CLI contract, Constitution observability discipline).
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence

from vct_moneyball.common.logging import CliError, get_logger, set_verbose


def _add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON on stdout")
    parser.add_argument("--verbose", action="store_true", help="enable debug logging on stderr")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="vctm", description="ENC 2026 power ranking pipeline")
    sub = parser.add_subparsers(dest="command", required=True)

    # vctm collect
    p_collect = sub.add_parser("collect", help="collect ENC teams, rosters, in-window matches")
    _add_common(p_collect)
    p_collect.add_argument("--window-months", type=int, default=None)
    p_collect.add_argument("--cutoff", type=str, default=None, help="ISO date; window end")
    p_collect.add_argument(
        "--use-cache",
        dest="use_cache",
        action="store_true",
        default=True,
        help="prefer cached raw HTML (default)",
    )
    p_collect.add_argument("--no-cache", dest="use_cache", action="store_false")
    p_collect.add_argument("--rate-limit", type=float, default=20.0, help="requests/minute")
    p_collect.add_argument(
        "--max-matches-per-player",
        type=int,
        default=30,
        help="cap on most-recent in-window club matches collected per rostered player",
    )

    # vctm build-ranking
    p_build = sub.add_parser("build-ranking", help="score, aggregate, write locked artifact")
    _add_common(p_build)
    p_build.add_argument("--version", required=True, help="e.g. enc-2026.v1")
    p_build.add_argument("--published-at", type=str, default=None, help="ISO ts (default now)")
    p_build.add_argument("--tournament-start", required=True, type=str, help="ISO ts lock deadline")
    p_build.add_argument("--out-dir", type=str, default=None)
    p_build.add_argument("--supersedes", type=str, default=None)
    p_build.add_argument("--use-cache", dest="use_cache", action="store_true", default=True)

    # vctm backfill-results
    p_backfill = sub.add_parser(
        "backfill-results", help="populate match outcomes from cached HTML (offline)"
    )
    _add_common(p_backfill)
    p_backfill.add_argument("--use-cache", dest="use_cache", action="store_true", default=True)

    # vctm train-winrate
    p_train = sub.add_parser("train-winrate", help="train + calibrate the winrate model")
    _add_common(p_train)
    p_train.add_argument("--cutoff", type=str, default=None, help="train strictly before (ISO)")
    p_train.add_argument("--lookback-months", type=int, default=12)
    p_train.add_argument("--learner", choices=["logreg", "gbt"], default="logreg")
    p_train.add_argument("--experiment", type=str, default="winrate")

    # vctm eval-winrate
    p_evalw = sub.add_parser("eval-winrate", help="evaluate on a held-out future block vs baseline")
    _add_common(p_evalw)
    p_evalw.add_argument("--cutoff", required=True, type=str, help="train before / eval on-after")
    p_evalw.add_argument("--lookback-months", type=int, default=12)
    p_evalw.add_argument("--learner", choices=["logreg", "gbt"], default="logreg")
    p_evalw.add_argument("--baseline", action="append", default=None, help="repeatable")
    p_evalw.add_argument("--experiment", type=str, default="winrate")
    p_evalw.add_argument("--out-dir", type=str, default=None)

    # vctm predict-match
    p_pred = sub.add_parser("predict-match", help="predict a single matchup")
    _add_common(p_pred)
    p_pred.add_argument("--team-a", required=True, type=str)
    p_pred.add_argument("--team-b", required=True, type=str)
    p_pred.add_argument("--as-of", type=str, default=None, help="ISO date (default now)")
    p_pred.add_argument("--lookback-months", type=int, default=12)
    p_pred.add_argument("--run", type=str, default=None, help="MLflow run id (default latest)")

    # vctm evaluate
    p_eval = sub.add_parser("evaluate", help="compare a locked ranking to final standings")
    _add_common(p_eval)
    p_eval.add_argument("--version", required=True)
    p_eval.add_argument("--standings", required=True, type=str)
    p_eval.add_argument("--baseline", default="vlr-seed")
    p_eval.add_argument(
        "--metric",
        action="append",
        default=None,
        help="repeatable; default spearman_rho, kendall_tau, top4_hit_rate",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    set_verbose(getattr(args, "verbose", False))
    logger = get_logger()

    # Lazy imports keep the CLI fast and let each stage own its dependencies.
    try:
        if args.command == "collect":
            from vct_moneyball.cli.collect import run_collect

            return run_collect(args)
        if args.command == "build-ranking":
            from vct_moneyball.cli.build_ranking import run_build_ranking

            return run_build_ranking(args)
        if args.command == "backfill-results":
            from vct_moneyball.cli.backfill_results import run_backfill_results

            return run_backfill_results(args)
        if args.command == "train-winrate":
            from vct_moneyball.cli.train_winrate import run_train_winrate

            return run_train_winrate(args)
        if args.command == "eval-winrate":
            from vct_moneyball.cli.eval_winrate import run_eval_winrate

            return run_eval_winrate(args)
        if args.command == "predict-match":
            from vct_moneyball.cli.predict_match import run_predict_match

            return run_predict_match(args)
        if args.command == "evaluate":
            from vct_moneyball.cli.evaluate import run_evaluate

            return run_evaluate(args)
    except CliError as exc:
        logger.error(str(exc))
        return exc.exit_code

    parser.error(f"unknown command {args.command!r}")  # pragma: no cover
    return 2


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
