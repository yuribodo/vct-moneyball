"""T018 — temporal split: zero overlap, no straddle, leakage verified."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from vct_moneyball.common.logging import CliError
from vct_moneyball.predict.dataset import temporal_split
from vct_moneyball.predict.features import build_examples
from vct_moneyball.predict.labels import LabeledMatch

pytestmark = pytest.mark.unit


def _m(mid, month, a, b, w):
    return LabeledMatch(mid, datetime(2026, month, 1, tzinfo=UTC), a, b, w)


MATCHES = [_m(i, i, 1, 2, 1 if i % 2 else 2) for i in range(1, 9)]
CUTOFF = datetime(2026, 6, 1, tzinfo=UTC)


def test_split_separates_train_before_eval_after() -> None:
    ds = temporal_split(build_examples(MATCHES), CUTOFF)
    assert ds.leakage_verified is True
    assert max(e.played_at for e in ds.train) < CUTOFF
    assert min(e.played_at for e in ds.eval) >= CUTOFF
    assert {e.match_id for e in ds.train}.isdisjoint({e.match_id for e in ds.eval})


def test_empty_eval_side_raises() -> None:
    with pytest.raises(CliError):
        temporal_split(build_examples(MATCHES), datetime(2027, 1, 1, tzinfo=UTC))


def test_empty_train_side_raises() -> None:
    with pytest.raises(CliError):
        temporal_split(build_examples(MATCHES), datetime(2025, 1, 1, tzinfo=UTC))
