"""Bridge model + roster-strength resolution.

Reuses feature-002's calibrated model (the features share names). The model trains inline on
club matches up to the as-of date (deterministic, <1s on ~1k matches), so predictions need no
stored artifact. Also resolves an ENC team's active roster and its as-of strength + top
contributors for explainability.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from vct_moneyball.bridge.features import build_bridge_examples
from vct_moneyball.bridge.player_rating import (
    PlayerRatingConfig,
    PlayerRatings,
    load_player_matches,
)
from vct_moneyball.bridge.strength import TeamStrength, roster_strength
from vct_moneyball.predict.model import WinrateModel, train
from vct_moneyball.store.models import Player, Team, TeamPlayer


@dataclass(frozen=True)
class TeamView:
    team_id: int
    name: str
    strength: TeamStrength
    contributors: list[tuple[str, float]]  # (handle, elo), strongest first


def active_roster(session: Session, team_id: int) -> list[tuple[int, str]]:
    rows = session.execute(
        select(Player.id, Player.handle)
        .join(TeamPlayer, TeamPlayer.player_id == Player.id)
        .where(TeamPlayer.team_id == team_id, TeamPlayer.is_active.is_(True))
        .order_by(Player.handle)
    ).all()
    return [(pid, handle) for pid, handle in rows]


def resolve_team(session: Session, ref: str) -> tuple[int, str]:
    from sqlalchemy import or_

    from vct_moneyball.common.logging import CliError

    row = session.execute(
        select(Team.id, Team.name).where(or_(Team.name == ref, Team.vlr_team_id == ref))
    ).first()
    if row is None:
        raise CliError(f"team {ref!r} not found")
    return int(row[0]), row[1]


def train_bridge(
    session: Session,
    *,
    as_of: datetime,
    lookback_months: int,
    cfg: PlayerRatingConfig,
    aggregation: str,
    learner: str = "logreg",
) -> WinrateModel:
    window_start = as_of - timedelta(days=30 * lookback_months)
    matches = load_player_matches(session, window_start, as_of)
    examples = build_bridge_examples(matches, cfg=cfg, aggregation=aggregation)
    return train(examples, learner=learner)


def team_views_as_of(
    session: Session,
    team_ids: list[int],
    *,
    as_of: datetime,
    lookback_months: int,
    cfg: PlayerRatingConfig,
    aggregation: str,
) -> dict[int, TeamView]:
    """Replay player ratings to ``as_of`` once, then build each team's roster strength."""
    window_start = as_of - timedelta(days=30 * lookback_months)
    matches = load_player_matches(session, window_start, as_of)
    ratings = PlayerRatings(cfg)
    ratings.replay_until(matches, as_of)
    states = ratings._states

    views: dict[int, TeamView] = {}
    for team_id in team_ids:
        roster = active_roster(session, team_id)
        pids = [pid for pid, _ in roster]
        strength = roster_strength(states, pids, cfg=cfg, aggregation=aggregation)
        contributors = sorted(
            (
                (handle, states[pid].elo if pid in states else cfg.elo_base)
                for pid, handle in roster
            ),
            key=lambda hc: -hc[1],
        )
        name = session.get(Team, team_id).name
        views[team_id] = TeamView(team_id, name, strength, contributors)
    return views
