"""T007 — player Elo replay is leakage-free, deterministic, and opponent-adjusted."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from vct_moneyball.bridge.player_rating import PlayerMatch, player_states_as_of

pytestmark = pytest.mark.unit

T0 = datetime(2026, 1, 1, tzinfo=UTC)


def _pm(i, a_players, b_players, a_won):
    return PlayerMatch(i, T0 + timedelta(days=i), frozenset(a_players), frozenset(b_players), a_won)


# Players 1,2 keep beating 3,4.
MATCHES = [_pm(1, [1, 2], [3, 4], 1), _pm(2, [1, 2], [3, 4], 1), _pm(3, [1, 2], [3, 4], 1)]


def test_winners_gain_losers_lose() -> None:
    states = player_states_as_of(MATCHES, T0 + timedelta(days=100))
    assert states[1].elo > 1500 > states[3].elo
    assert states[1].count == 3


def test_as_of_excludes_future_matches() -> None:
    # As of day 2, only match 1 (day 1) has happened.
    states = player_states_as_of(MATCHES, T0 + timedelta(days=2))
    assert states[1].count == 1
    # As of day 1 (before any match), nobody has played.
    early = player_states_as_of(MATCHES, T0 + timedelta(days=1))
    assert early == {} or all(s.count == 0 for s in early.values())


def test_replay_is_deterministic() -> None:
    a = player_states_as_of(MATCHES, T0 + timedelta(days=100))
    b = player_states_as_of(MATCHES, T0 + timedelta(days=100))
    assert {k: v.elo for k, v in a.items()} == {k: v.elo for k, v in b.items()}
