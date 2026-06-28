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


@dataclass(frozen=True)
class MatchupPrediction:
    team_a: str
    team_b: str
    p_a: float
    p_b: float
    winner: str
    low_confidence: bool
    elo_a: float
    elo_b: float
    contributors_a: list[str]
    contributors_b: list[str]


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


def predict_matchup(
    session: Session,
    team_a_ref: str,
    team_b_ref: str,
    *,
    as_of: datetime,
    lookback_months: int = 12,
    aggregation: str = "mean",
    cfg: PlayerRatingConfig | None = None,
) -> MatchupPrediction:
    """Predict a matchup — the single code path shared by the CLI and the API."""
    from vct_moneyball.bridge.features import matchup_features

    cfg = cfg or PlayerRatingConfig()
    a_id, a_name = resolve_team(session, team_a_ref)
    b_id, b_name = resolve_team(session, team_b_ref)
    model = train_bridge(
        session, as_of=as_of, lookback_months=lookback_months, cfg=cfg, aggregation=aggregation
    )
    views = team_views_as_of(
        session,
        [a_id, b_id],
        as_of=as_of,
        lookback_months=lookback_months,
        cfg=cfg,
        aggregation=aggregation,
    )
    va, vb = views[a_id], views[b_id]
    p_a = model.predict_proba_a(matchup_features(va.strength, vb.strength))
    p_b = 1.0 - p_a
    return MatchupPrediction(
        team_a=a_name,
        team_b=b_name,
        p_a=p_a,
        p_b=p_b,
        winner=a_name if p_a >= p_b else b_name,
        low_confidence=not (va.strength.is_confident and vb.strength.is_confident),
        elo_a=va.strength.elo,
        elo_b=vb.strength.elo,
        contributors_a=[h for h, _ in va.contributors[:3]],
        contributors_b=[h for h, _ in vb.contributors[:3]],
    )
