"""T036 — rank-agreement metrics (Spearman rho, Kendall tau, top-k hit rate)."""

from __future__ import annotations

import pytest

from vct_moneyball.evaluate.metrics import (
    compute_metric,
    kendall_tau,
    spearman_rho,
    top_k_hit_rate,
)

pytestmark = pytest.mark.unit

ORDER = ["A", "B", "C", "D", "E"]


def test_perfect_agreement() -> None:
    assert spearman_rho(ORDER, ORDER) == pytest.approx(1.0)
    assert kendall_tau(ORDER, ORDER) == pytest.approx(1.0)
    assert top_k_hit_rate(ORDER, ORDER, 4) == pytest.approx(1.0)


def test_perfect_disagreement() -> None:
    reverse = list(reversed(ORDER))
    assert spearman_rho(ORDER, reverse) == pytest.approx(-1.0)
    assert kendall_tau(ORDER, reverse) == pytest.approx(-1.0)


def test_single_swap_is_positive_but_not_perfect() -> None:
    swapped = ["A", "C", "B", "D", "E"]  # one adjacent swap
    rho = spearman_rho(ORDER, swapped)
    tau = kendall_tau(ORDER, swapped)
    assert 0.0 < rho < 1.0
    assert 0.0 < tau < 1.0


def test_top_k_hit_rate_partial() -> None:
    predicted = ["A", "B", "C", "D", "E"]
    actual = ["A", "B", "E", "D", "C"]  # top-4 sets: {A,B,C,D} vs {A,B,E,D}
    assert top_k_hit_rate(predicted, actual, 4) == pytest.approx(3 / 4)


def test_compute_metric_dispatch() -> None:
    assert compute_metric("spearman_rho", ORDER, ORDER) == pytest.approx(1.0)
    assert compute_metric("top4_hit_rate", ORDER, ORDER) == pytest.approx(1.0)
    with pytest.raises(ValueError, match="unknown metric"):
        compute_metric("bogus", ORDER, ORDER)


def test_mismatched_sets_rejected() -> None:
    with pytest.raises(ValueError, match="same set"):
        spearman_rho(["A", "B"], ["A", "C"])
