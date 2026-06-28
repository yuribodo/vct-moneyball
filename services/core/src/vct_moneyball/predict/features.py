"""Leakage-free pre-match features via chronological replay.

For each match we record each team's state **before** that match — a chronologically
updated Elo rating (opponent-adjusted), recent win-rate (form), and prior-match volume —
then encode the example as the opponent **difference** ``f(A) − f(B)`` (research R2/R3).
Because the replay updates state only *after* emitting a match's features, no feature can
read its own or any later result: leakage-freedom is structural, not assumed.

Design note: ``player_map_stat`` carries no reliable team attribution from feature 001
(team_id is null), so the MVP signal is built from match outcomes — which are clean,
opponent-adjusted, and verifiably leakage-free. Per-player form is a future enhancement.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime

from vct_moneyball.predict.labels import LabeledMatch

FEATURE_NAMES = ("elo_diff", "form_diff", "log_volume_diff")


@dataclass(frozen=True)
class FeatureConfig:
    lookback_months: int = 12
    elo_base: float = 1500.0
    elo_k: float = 24.0
    form_window: int = 10  # recent matches for win-rate form

    def as_dict(self) -> dict[str, object]:
        return {
            "lookback_months": self.lookback_months,
            "elo_base": self.elo_base,
            "elo_k": self.elo_k,
            "form_window": self.form_window,
            "feature_names": list(FEATURE_NAMES),
        }


DEFAULT_FEATURE_CONFIG = FeatureConfig()


@dataclass(frozen=True)
class MatchExample:
    match_id: int
    played_at: datetime
    team_a_id: int
    team_b_id: int
    label: int
    features: dict[str, float]
    min_volume: int  # min prior matches of the two sides → confidence


@dataclass
class _TeamState:
    elo: float
    results: deque[int] = field(default_factory=deque)  # recent 1/0 outcomes
    count: int = 0


def _expected(elo_a: float, elo_b: float) -> float:
    return 1.0 / (1.0 + 10.0 ** ((elo_b - elo_a) / 400.0))


def _winrate(results: deque[int]) -> float:
    return sum(results) / len(results) if results else 0.5


def _features_from_states(a: _TeamState, b: _TeamState, cfg: FeatureConfig) -> dict[str, float]:
    import math

    return {
        "elo_diff": a.elo - b.elo,
        "form_diff": _winrate(a.results) - _winrate(b.results),
        "log_volume_diff": math.log1p(a.count) - math.log1p(b.count),
    }


class _Replay:
    """Chronological Elo/form replay; emits pre-match features then updates state."""

    def __init__(self, cfg: FeatureConfig) -> None:
        self.cfg = cfg
        self._states: dict[int, _TeamState] = {}

    def _state(self, team_id: int) -> _TeamState:
        st = self._states.get(team_id)
        if st is None:
            st = _TeamState(elo=self.cfg.elo_base, results=deque(maxlen=self.cfg.form_window))
            self._states[team_id] = st
        return st

    def pre_match_features(self, m: LabeledMatch) -> tuple[dict[str, float], int]:
        a, b = self._state(m.team_a_id), self._state(m.team_b_id)
        return _features_from_states(a, b, self.cfg), min(a.count, b.count)

    def update(self, m: LabeledMatch) -> None:
        a, b = self._state(m.team_a_id), self._state(m.team_b_id)
        exp_a = _expected(a.elo, b.elo)
        a.elo += self.cfg.elo_k * (m.label - exp_a)
        b.elo += self.cfg.elo_k * ((1 - m.label) - (1 - exp_a))
        a.results.append(m.label)
        b.results.append(1 - m.label)
        a.count += 1
        b.count += 1

    def state_of(self, team_id: int) -> _TeamState:
        return self._state(team_id)


def build_examples(
    matches: list[LabeledMatch], cfg: FeatureConfig = DEFAULT_FEATURE_CONFIG
) -> list[MatchExample]:
    """Build one leakage-free example per match (chronological order assumed)."""
    replay = _Replay(cfg)
    examples: list[MatchExample] = []
    for m in matches:
        feats, min_vol = replay.pre_match_features(m)
        examples.append(
            MatchExample(
                match_id=m.match_id,
                played_at=m.played_at,
                team_a_id=m.team_a_id,
                team_b_id=m.team_b_id,
                label=m.label,
                features=feats,
                min_volume=min_vol,
            )
        )
        replay.update(m)
    return examples


def features_as_of(
    matches: list[LabeledMatch],
    team_a_id: int,
    team_b_id: int,
    as_of: datetime,
    cfg: FeatureConfig = DEFAULT_FEATURE_CONFIG,
) -> tuple[dict[str, float], int]:
    """Replay all matches strictly before ``as_of`` and return the matchup's features."""
    replay = _Replay(cfg)
    for m in matches:
        if m.played_at >= as_of:
            break
        replay.update(m)
    a, b = replay.state_of(team_a_id), replay.state_of(team_b_id)
    return _features_from_states(a, b, cfg), min(a.count, b.count)
