"""Leakage-free chronological player Elo + form.

Replays attributed matches in time order. For each match, both sides' mean player Elo gives
the expected result; every player on a side is updated by that side's outcome. A player's
state **as of** a date uses only matches before it (the replay updates only after reading
pre-match state), so leakage-freedom is structural (R2).
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from vct_moneyball.store.models import Match, MatchMap, PlayerMapStat


@dataclass(frozen=True)
class PlayerRatingConfig:
    elo_base: float = 1500.0
    elo_k: float = 24.0
    form_window: int = 10
    min_history: int = 5  # min prior matches for a confident player rating

    def as_dict(self) -> dict[str, object]:
        return {
            "elo_base": self.elo_base,
            "elo_k": self.elo_k,
            "form_window": self.form_window,
            "min_history": self.min_history,
        }


DEFAULT_RATING_CONFIG = PlayerRatingConfig()


@dataclass(frozen=True)
class PlayerMatch:
    match_id: int
    played_at: datetime
    side_a: frozenset[int]  # player ids on team_a
    side_b: frozenset[int]  # player ids on team_b
    a_won: int  # 1 if team_a won


@dataclass
class PlayerState:
    elo: float
    results: deque[int] = field(default_factory=deque)
    count: int = 0

    @property
    def form(self) -> float:
        return sum(self.results) / len(self.results) if self.results else 0.5


def load_player_matches(
    session: Session, window_start: datetime, window_end: datetime
) -> list[PlayerMatch]:
    """Labeled matches with attributed player sides, chronological."""
    rows = session.execute(
        select(
            Match.id,
            Match.played_at,
            Match.team_a_id,
            Match.winner_team_id,
            PlayerMapStat.player_id,
            PlayerMapStat.team_id,
        )
        .join(MatchMap, MatchMap.match_id == Match.id)
        .join(PlayerMapStat, PlayerMapStat.match_map_id == MatchMap.id)
        .where(
            Match.winner_team_id.isnot(None),
            Match.team_a_id.isnot(None),
            Match.team_b_id.isnot(None),
            PlayerMapStat.team_id.isnot(None),
            Match.played_at >= window_start,
            Match.played_at <= window_end,
        )
        .order_by(Match.played_at, Match.id)
    ).all()

    by_match: dict[int, dict] = {}
    for mid, played_at, team_a_id, winner_id, player_id, team_id in rows:
        m = by_match.setdefault(
            mid,
            {"played_at": played_at, "a": set(), "b": set(), "a_won": int(winner_id == team_a_id)},
        )
        (m["a"] if team_id == team_a_id else m["b"]).add(player_id)

    matches = [
        PlayerMatch(
            match_id=mid,
            played_at=m["played_at"],
            side_a=frozenset(m["a"]),
            side_b=frozenset(m["b"]),
            a_won=m["a_won"],
        )
        for mid, m in by_match.items()
        if m["a"] and m["b"]
    ]
    matches.sort(key=lambda pm: (pm.played_at, pm.match_id))
    return matches


def _expected(mean_a: float, mean_b: float) -> float:
    return 1.0 / (1.0 + 10.0 ** ((mean_b - mean_a) / 400.0))


class PlayerRatings:
    """Chronological player-Elo replay with as-of queries."""

    def __init__(self, cfg: PlayerRatingConfig = DEFAULT_RATING_CONFIG) -> None:
        self.cfg = cfg
        self._states: dict[int, PlayerState] = {}

    def state(self, player_id: int) -> PlayerState:
        st = self._states.get(player_id)
        if st is None:
            st = PlayerState(elo=self.cfg.elo_base, results=deque(maxlen=self.cfg.form_window))
            self._states[player_id] = st
        return st

    def _mean_elo(self, players: frozenset[int]) -> float:
        if not players:
            return self.cfg.elo_base
        return sum(self.state(p).elo for p in players) / len(players)

    def update(self, pm: PlayerMatch) -> None:
        exp_a = _expected(self._mean_elo(pm.side_a), self._mean_elo(pm.side_b))
        for p in pm.side_a:
            st = self.state(p)
            st.elo += self.cfg.elo_k * (pm.a_won - exp_a)
            st.results.append(pm.a_won)
            st.count += 1
        for p in pm.side_b:
            st = self.state(p)
            st.elo += self.cfg.elo_k * ((1 - pm.a_won) - (1 - exp_a))
            st.results.append(1 - pm.a_won)
            st.count += 1

    def replay_until(self, matches: list[PlayerMatch], as_of: datetime) -> None:
        for pm in matches:
            if pm.played_at >= as_of:
                break
            self.update(pm)


def player_states_as_of(
    matches: list[PlayerMatch], as_of: datetime, cfg: PlayerRatingConfig = DEFAULT_RATING_CONFIG
) -> dict[int, PlayerState]:
    ratings = PlayerRatings(cfg)
    ratings.replay_until(matches, as_of)
    return dict(ratings._states)
