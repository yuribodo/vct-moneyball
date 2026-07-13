"""T-new — neighbor-separation signal (issue #10): orthogonal to confidence.

Confidence answers "do we have enough player-history data"; separation answers "is
this team's *rank* precise" — a data-rich team can still be in a statistical dead
heat with its neighbor, which is exactly the case the real enc-2026.bridge.v3 ranking
exposed (15/16 teams "high" confidence despite Elos clustered within ~57 points).
"""

from __future__ import annotations

import pytest

from vct_moneyball.cli.enc_ranking import _elo_margin_to_next, _separation

pytestmark = pytest.mark.unit


def test_margin_uses_smaller_of_the_two_neighbor_gaps() -> None:
    elos = [1600.0, 1550.0, 1500.0]
    assert _elo_margin_to_next(elos, 1) == pytest.approx(50.0)  # equidistant either way here


def test_margin_picks_the_closer_neighbor() -> None:
    elos = [1600.0, 1590.0, 1500.0]
    assert _elo_margin_to_next(elos, 1) == pytest.approx(10.0)  # 10 up, 90 down -> min is 10


def test_edge_positions_have_only_one_neighbor() -> None:
    elos = [1600.0, 1550.0, 1500.0]
    assert _elo_margin_to_next(elos, 0) == pytest.approx(50.0)
    assert _elo_margin_to_next(elos, 2) == pytest.approx(50.0)


def test_single_team_has_no_margin() -> None:
    assert _elo_margin_to_next([1500.0], 0) is None


def test_real_v3_neighbor_gap_is_razor_thin() -> None:
    # Positions 12/13 in the real enc-2026.bridge.v3 ranking: Thailand 1527.1, Poland 1526.9.
    elos = [1527.1, 1526.9]
    assert _elo_margin_to_next(elos, 0) == pytest.approx(0.2)
    assert _separation(_elo_margin_to_next(elos, 0)) == "razor-thin"


def test_separation_bands() -> None:
    assert _separation(None) == "clear"
    assert _separation(20.0) == "clear"
    assert _separation(10.0) == "contested"
    assert _separation(2.0) == "razor-thin"
