"""T010 — match outcome label."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from vct_moneyball.predict.labels import LabeledMatch

pytestmark = pytest.mark.unit

T = datetime(2026, 1, 1, tzinfo=UTC)


def test_label_is_one_when_team_a_won() -> None:
    m = LabeledMatch(1, T, team_a_id=10, team_b_id=20, winner_team_id=10)
    assert m.label == 1


def test_label_is_zero_when_team_b_won() -> None:
    m = LabeledMatch(1, T, team_a_id=10, team_b_id=20, winner_team_id=20)
    assert m.label == 0
