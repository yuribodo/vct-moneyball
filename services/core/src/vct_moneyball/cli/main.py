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

    # vctm build-ranking
    p_build = sub.add_parser("build-ranking", help="score, aggregate, write locked artifact")
    _add_common(p_build)
    p_build.add_argument("--version", required=True, help="e.g. enc-2026.v1")
    p_build.add_argument("--published-at", type=str, default=None, help="ISO ts (default now)")
    p_build.add_argument("--tournament-start", required=True, type=str, help="ISO ts lock deadline")
    p_build.add_argument("--out-dir", type=str, default=None)
    p_build.add_argument("--supersedes", type=str, default=None)
    p_build.add_argument("--use-cache", dest="use_cache", action="store_true", default=True)

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
