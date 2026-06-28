"""Match outcome labels — load labeled matches and derive the binary target.

A labeled match has both teams and a winner. The target is ``1`` when ``team_a`` won
(sides are fixed by the stored ``team_a_id``/``team_b_id``, so the encoding is reproducible).
Matches without a parseable result are simply absent (never guessed).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from vct_moneyball.store.models import Match


@dataclass(frozen=True)
class LabeledMatch:
    match_id: int
    played_at: datetime
    team_a_id: int
    team_b_id: int
    winner_team_id: int

    @property
    def label(self) -> int:
        """1 if team_a won, else 0."""
        return 1 if self.winner_team_id == self.team_a_id else 0


def load_labeled_matches(
    session: Session, window_start: datetime, window_end: datetime
) -> list[LabeledMatch]:
    """All labeled matches in the window, ordered chronologically (then by id)."""
    rows = session.execute(
        select(
            Match.id,
            Match.played_at,
            Match.team_a_id,
            Match.team_b_id,
            Match.winner_team_id,
        )
        .where(
            Match.winner_team_id.isnot(None),
            Match.team_a_id.isnot(None),
            Match.team_b_id.isnot(None),
            Match.team_a_id != Match.team_b_id,
            Match.played_at >= window_start,
            Match.played_at <= window_end,
        )
        .order_by(Match.played_at, Match.id)
    ).all()
    return [
        LabeledMatch(
            match_id=mid,
            played_at=played_at,
            team_a_id=a,
            team_b_id=b,
            winner_team_id=w,
        )
        for mid, played_at, a, b, w in rows
    ]
