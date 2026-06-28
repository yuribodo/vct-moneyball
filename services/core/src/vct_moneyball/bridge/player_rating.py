"""Leakage-free chronological player Elo + form.

Replays attributed matches in time order. For each match, both sides' mean player Elo gives
the expected result; every player on a side is updated by that side's outcome. A player's
state **as of** a date uses only matches before it (the replay updates only after reading
pre-match state), so leakage-freedom is structural (R2).

The per-match update strength is shaped by three signals so the ladder reflects real tiers
rather than raw activity:

* **Event tier** — a win at Masters/Champions moves Elo more than one in regional Challengers,
  so dominating a weak circuit no longer looks like beating the world.
* **Margin of victory** — a 2-0 sweep moves more than a 2-1 grind.
* **Individual performance** — within a side, the carry (higher in-match rating) gains more and
  the passenger less. This is normalised to be zero-sum per side, so it separates players
  without changing the team-level Elo dynamics that the tier/margin signals drive.
"""

from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from vct_moneyball.store.models import Match, MatchMap, PlayerMapStat


# --- Event tiers ---------------------------------------------------------------
# Substring match (case-insensitive), first hit wins. Beating strong international
# fields counts most; regional tier-2 counts least.
_EVENT_TIERS: list[tuple[str, float]] = [
    ("champions", 1.7),
    ("masters", 1.6),
    ("esports world cup", 1.45),
    ("game changers", 0.45),
    ("challengers", 0.5),  # regional tier-2 — winning here says little about world level
    ("vct", 1.2),  # tier-1 regional leagues (Americas/EMEA/Pacific/China)
]
_DEFAULT_TIER = 0.5  # unknown / minor events


def event_tier_weight(event: str | None) -> float:
    if not event:
        return _DEFAULT_TIER
    e = event.casefold()
    for needle, w in _EVENT_TIERS:
        if needle in e:
            return w
    return _DEFAULT_TIER


@dataclass(frozen=True)
class PlayerRatingConfig:
    elo_base: float = 1500.0
    elo_k: float = 24.0
    form_window: int = 10
    min_history: int = 5  # min prior matches for a confident player rating
    # Tier / margin / individual shaping (all on by default; flip off for the old model).
    use_event_tier: bool = True
    use_margin: bool = True
    use_individual: bool = True
    mov_coef: float = 0.5  # margin-of-victory log scaling
    perf_clip: float = 0.5  # individual multiplier stays within [1-clip, 1+clip]

    def as_dict(self) -> dict[str, object]:
        return {
            "elo_base": self.elo_base,
            "elo_k": self.elo_k,
            "form_window": self.form_window,
            "min_history": self.min_history,
            "use_event_tier": self.use_event_tier,
            "use_margin": self.use_margin,
            "use_individual": self.use_individual,
            "mov_coef": self.mov_coef,
            "perf_clip": self.perf_clip,
        }


DEFAULT_RATING_CONFIG = PlayerRatingConfig()


@dataclass(frozen=True)
class PlayerMatch:
    match_id: int
    played_at: datetime
    side_a: frozenset[int]  # player ids on team_a
    side_b: frozenset[int]  # player ids on team_b
    a_won: int  # 1 if team_a won
    event: str | None = None
    margin: int = 0  # |series score difference|, 0 if unknown
    ratings: dict[int, float] = field(default_factory=dict)  # player_id -> mean in-match rating


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
    """Labeled matches with attributed player sides + event/margin/ratings, chronological."""
    rows = session.execute(
        select(
            Match.id,
            Match.played_at,
            Match.team_a_id,
            Match.winner_team_id,
            Match.event,
            Match.score_a,
            Match.score_b,
            PlayerMapStat.player_id,
            PlayerMapStat.team_id,
            PlayerMapStat.rating,
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
    for mid, played_at, team_a_id, winner_id, event, score_a, score_b, player_id, team_id, rating in rows:
        m = by_match.setdefault(
            mid,
            {
                "played_at": played_at,
                "a": set(),
                "b": set(),
                "a_won": int(winner_id == team_a_id),
                "event": event,
                "margin": abs((score_a or 0) - (score_b or 0)) if score_a is not None else 0,
                "rsum": {},
                "rcnt": {},
            },
        )
        (m["a"] if team_id == team_a_id else m["b"]).add(player_id)
        if rating is not None:
            m["rsum"][player_id] = m["rsum"].get(player_id, 0.0) + float(rating)
            m["rcnt"][player_id] = m["rcnt"].get(player_id, 0) + 1

    matches = [
        PlayerMatch(
            match_id=mid,
            played_at=m["played_at"],
            side_a=frozenset(m["a"]),
            side_b=frozenset(m["b"]),
            a_won=m["a_won"],
            event=m["event"],
            margin=m["margin"],
            ratings={p: m["rsum"][p] / m["rcnt"][p] for p in m["rsum"]},
        )
        for mid, m in by_match.items()
        if m["a"] and m["b"]
    ]
    matches.sort(key=lambda pm: (pm.played_at, pm.match_id))
    return matches


def _expected(mean_a: float, mean_b: float) -> float:
    return 1.0 / (1.0 + 10.0 ** ((mean_b - mean_a) / 400.0))


def _margin_factor(margin: int, coef: float) -> float:
    """1.0 for a one-game margin, growing with the log of the gap."""
    return 1.0 + coef * math.log1p(max(0, margin - 1))


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

    def _perf_mults(
        self, players: frozenset[int], ratings: dict[int, float], tier_w: float
    ) -> dict[int, float]:
        """Per-player multiplier from in-match rating, normalised to mean 1 across the side.

        The deviation from 1.0 is scaled by the event tier, so out-rating teammates in a
        weak event (stat-padding a tier-2 lobby) barely moves a player's rating.
        """
        if not self.cfg.use_individual or not ratings:
            return {p: 1.0 for p in players}
        rated = [ratings[p] for p in players if p in ratings]
        if not rated:
            return {p: 1.0 for p in players}
        team_avg = sum(rated) / len(rated)
        lo, hi = 1.0 - self.cfg.perf_clip, 1.0 + self.cfg.perf_clip
        shrink = min(1.0, tier_w)  # weak events => individual edge counts less
        raw = {
            p: 1.0
            + shrink
            * (min(hi, max(lo, (ratings[p] / team_avg) if (p in ratings and team_avg) else 1.0)) - 1.0)
            for p in players
        }
        scale = len(players) / sum(raw.values())  # renormalise so the side stays zero-sum
        return {p: raw[p] * scale for p in players}

    def update(self, pm: PlayerMatch) -> None:
        exp_a = _expected(self._mean_elo(pm.side_a), self._mean_elo(pm.side_b))
        tier_w = event_tier_weight(pm.event)
        k = self.cfg.elo_k
        if self.cfg.use_event_tier:
            k *= tier_w
        if self.cfg.use_margin:
            k *= _margin_factor(pm.margin, self.cfg.mov_coef)

        mults_a = self._perf_mults(pm.side_a, pm.ratings, tier_w)
        mults_b = self._perf_mults(pm.side_b, pm.ratings, tier_w)
        for p in pm.side_a:
            st = self.state(p)
            st.elo += k * mults_a[p] * (pm.a_won - exp_a)
            st.results.append(pm.a_won)
            st.count += 1
        for p in pm.side_b:
            st = self.state(p)
            st.elo += k * mults_b[p] * ((1 - pm.a_won) - (1 - exp_a))
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
