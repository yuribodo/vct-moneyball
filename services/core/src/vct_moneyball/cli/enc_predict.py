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

from vct_moneyball.bridge.features import matchup_features
from vct_moneyball.bridge.model import resolve_team, team_views_as_of, train_bridge
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
        a_id, a_name = resolve_team(session, args.team_a)
        b_id, b_name = resolve_team(session, args.team_b)
        model = train_bridge(
            session,
            as_of=as_of,
            lookback_months=args.lookback_months,
            cfg=cfg,
            aggregation=aggregation,
        )
        views = team_views_as_of(
            session,
            [a_id, b_id],
            as_of=as_of,
            lookback_months=args.lookback_months,
            cfg=cfg,
            aggregation=aggregation,
        )

    va, vb = views[a_id], views[b_id]
    p_a = model.predict_proba_a(matchup_features(va.strength, vb.strength))
    p_b = 1.0 - p_a
    winner = a_name if p_a >= p_b else b_name
    low_conf = not (va.strength.is_confident and vb.strength.is_confident)

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
                    "elo_a": round(va.strength.elo, 1),
                    "elo_b": round(vb.strength.elo, 1),
                    "top_a": [h for h, _ in va.contributors[:3]],
                    "top_b": [h for h, _ in vb.contributors[:3]],
                }
            )
        )
    else:
        flag = "  ⚠️ low confidence (sparse roster history)" if low_conf else ""
        log.info("ENC prediction as of %s%s", as_of.date(), flag)
        print(
            f"  {a_name}: {p_a:.1%}  (roster Elo {va.strength.elo:.0f}; "
            f"top: {', '.join(h for h, _ in va.contributors[:3])})"
        )
        print(
            f"  {b_name}: {p_b:.1%}  (roster Elo {vb.strength.elo:.0f}; "
            f"top: {', '.join(h for h, _ in vb.contributors[:3])})"
        )
        print(f"  predicted winner: {winner}")
    return 0
