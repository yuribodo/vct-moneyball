"""``vctm enc-ranking`` — roster-derived ordering of the 16 ENC teams.

Ranks the ENC cohort by roster-derived strength (active rosters' club Elo as-of the lock
date) and writes a dated, immutable artifact citing its config — never modifying
feature-001/002 artifacts (Constitution II; FR-004/FR-010).
"""

from __future__ import annotations

import argparse
import json
import pathlib
from datetime import UTC, datetime

from sqlalchemy import select

from vct_moneyball.bridge.model import team_views_as_of
from vct_moneyball.bridge.player_rating import PlayerRatingConfig
from vct_moneyball.common.artifact_pointers import write_pointer
from vct_moneyball.common.logging import CliError, get_logger
from vct_moneyball.store.db import make_engine, session_scope
from vct_moneyball.store.models import Team

ENC_TEAM_COUNT = 16

# Elo-gap bands for the neighbor-separation signal (issue #10): "confidence" measures
# per-player data sufficiency and says nothing about how close a team sits to its
# ranking neighbors — a data-rich team can still be in a statistical dead heat. These
# thresholds are eyeballed against the real enc-2026.bridge.v3 neighbor gaps (0.2-43.8
# Elo, most of the mid-pack under 10) and are not yet statistically calibrated.
_RAZOR_THIN_MAX = 5.0
_CONTESTED_MAX = 15.0


def _elo_margin_to_next(elos: list[float], i: int) -> float | None:
    """Smallest Elo gap to an adjacent rank (previous and/or next), or None if isolated."""
    gaps = [abs(elos[i] - elos[j]) for j in (i - 1, i + 1) if 0 <= j < len(elos)]
    return round(min(gaps), 1) if gaps else None


def _separation(margin: float | None) -> str:
    """How precisely a team's rank is pinned down by the gap to its nearest neighbor."""
    if margin is None or margin >= _CONTESTED_MAX:
        return "clear"
    return "razor-thin" if margin < _RAZOR_THIN_MAX else "contested"


def _parse_ts(value: str | None) -> datetime:
    if value is None:
        return datetime.now(UTC)
    dt = datetime.fromisoformat(value)
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)


def _default_out_dir() -> pathlib.Path:
    for base in [pathlib.Path.cwd(), *pathlib.Path(__file__).resolve().parents]:
        if (base / ".git").is_dir() or (base / "services" / "core").is_dir():
            return base / "artifacts" / "models" / "bridge"
    return pathlib.Path.cwd() / "artifacts" / "models" / "bridge"


def run_enc_ranking(args: argparse.Namespace) -> int:
    log = get_logger()
    as_of = _parse_ts(getattr(args, "as_of", None))
    cfg = PlayerRatingConfig()
    aggregation = args.aggregation

    with session_scope(make_engine()) as session:
        enc_ids = [
            r[0]
            for r in session.execute(
                select(Team.id).where(Team.is_enc_2026.is_(True)).order_by(Team.name)
            ).all()
        ]
        if len(enc_ids) != ENC_TEAM_COUNT:
            raise CliError(f"expected {ENC_TEAM_COUNT} ENC teams, found {len(enc_ids)}")
        views = team_views_as_of(
            session,
            enc_ids,
            as_of=as_of,
            lookback_months=args.lookback_months,
            cfg=cfg,
            aggregation=aggregation,
        )

    ordered = sorted(views.values(), key=lambda v: (-v.strength.elo, v.name))
    elos = [v.strength.elo for v in ordered]
    margins = [_elo_margin_to_next(elos, i) for i in range(len(elos))]
    version = args.version or f"enc-2026.bridge.{as_of.date().isoformat()}"
    artifact = {
        "version": version,
        "as_of": as_of.isoformat(),
        "aggregation": aggregation,
        "teams": [
            {
                "position": i + 1,
                "team": v.name,
                "roster_elo": round(v.strength.elo, 1),
                "confidence": v.strength.confidence,
                "elo_margin_to_next": margins[i],
                "separation": _separation(margins[i]),
                "contributors": [h for h, _ in v.contributors[:5]],
            }
            for i, v in enumerate(ordered)
        ],
    }

    out_dir = pathlib.Path(args.out_dir) if getattr(args, "out_dir", None) else _default_out_dir()
    target = out_dir / version
    if target.exists():
        raise CliError(f"refusing to overwrite existing artifact dir: {target}")
    target.mkdir(parents=True)
    (target / "enc-ranking.json").write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n")
    md = [
        "# ENC 2026 Power Ranking — roster-derived",
        "",
        f"- Version: `{version}`  ·  as of `{as_of.isoformat()}`  ·  aggregation `{aggregation}`",
        "",
        "| # | Team | Roster Elo | Confidence | Separation |",
        "|--:|------|-----------:|------------|------------|",
    ]
    md += [
        f"| {t['position']} | {t['team']} | {t['roster_elo']:.0f} | {t['confidence']} | "
        f"{t['separation']} |"
        for t in artifact["teams"]
    ]
    (target / "enc-ranking.md").write_text("\n".join(md) + "\n")

    if getattr(args, "publish", False):
        write_pointer(out_dir / "LATEST", version)

    if args.json:
        print(json.dumps({"artifact_dir": str(target), "version": version}))
    else:
        log.info("wrote roster-derived ENC ranking to %s", target)
        for t in artifact["teams"]:
            print(
                f"{t['position']:>2}. {t['team']:<28} Elo {t['roster_elo']:.0f}  "
                f"({t['confidence']}, {t['separation']})"
            )
    return 0
