"""``vctm enc-predict`` — confident ENC matchup from roster-derived strength (read-only).

Trains the bridge inline on club matches up to ``--as-of``, computes each ENC team's roster
strength from its active roster (using only pre-as-of data), and reports calibrated,
differentiated win probabilities + the top contributing players. Low-confidence when a
roster's club history is sparse — never a fabricated certainty (FR-002/FR-003).
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime

from vct_moneyball.bridge.model import predict_matchup
from vct_moneyball.bridge.player_rating import PlayerRatingConfig
from vct_moneyball.common.logging import get_logger
from vct_moneyball.store.db import make_engine, session_scope


def _parse_ts(value: str | None) -> datetime:
    if value is None:
        return datetime.now(UTC)
    dt = datetime.fromisoformat(value)
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)


def run_enc_predict(args: argparse.Namespace) -> int:
    log = get_logger()
    as_of = _parse_ts(getattr(args, "as_of", None))
    cfg = PlayerRatingConfig()
    aggregation = args.aggregation

    with session_scope(make_engine()) as session:
        pred = predict_matchup(
            session,
            args.team_a,
            args.team_b,
            as_of=as_of,
            lookback_months=args.lookback_months,
            aggregation=aggregation,
            cfg=cfg,
        )

    if args.json:
        print(
            json.dumps(
                {
                    "team_a": pred.team_a,
                    "team_b": pred.team_b,
                    "p_a": round(pred.p_a, 4),
                    "p_b": round(pred.p_b, 4),
                    "winner": pred.winner,
                    "low_confidence": pred.low_confidence,
                    "elo_a": round(pred.elo_a, 1),
                    "elo_b": round(pred.elo_b, 1),
                    "top_a": pred.contributors_a,
                    "top_b": pred.contributors_b,
                }
            )
        )
    else:
        flag = "  ⚠️ low confidence (sparse roster history)" if pred.low_confidence else ""
        log.info("ENC prediction as of %s%s", as_of.date(), flag)
        print(
            f"  {pred.team_a}: {pred.p_a:.1%}  (roster Elo {pred.elo_a:.0f}; "
            f"top: {', '.join(pred.contributors_a)})"
        )
        print(
            f"  {pred.team_b}: {pred.p_b:.1%}  (roster Elo {pred.elo_b:.0f}; "
            f"top: {', '.join(pred.contributors_b)})"
        )
        print(f"  predicted winner: {pred.winner}")
    return 0
