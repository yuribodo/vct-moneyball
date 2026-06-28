"""Rank-agreement metrics: predicted order vs. actual final standings.

Pure functions (no scipy dependency) so they are deterministic and unit-testable:
Spearman's rho (Pearson correlation of ranks), Kendall's tau-b, and top-k hit rate.
Each takes two orderings (best-first) of the *same* set of teams.
"""

from __future__ import annotations

from collections.abc import Sequence
from itertools import combinations


def _validate(predicted: Sequence[str], actual: Sequence[str]) -> None:
    if set(predicted) != set(actual):
        raise ValueError("predicted and actual must rank the same set of teams")
    if len(predicted) != len(set(predicted)):
        raise ValueError("predicted order contains duplicates")


def _ranks(order: Sequence[str]) -> dict[str, int]:
    """Map team -> 1-based rank (best = 1)."""
    return {team: i + 1 for i, team in enumerate(order)}


def spearman_rho(predicted: Sequence[str], actual: Sequence[str]) -> float:
    """Spearman's rank correlation coefficient in ``[-1, 1]``."""
    _validate(predicted, actual)
    n = len(predicted)
    if n < 2:
        return 1.0
    pr, ar = _ranks(predicted), _ranks(actual)
    d2 = sum((pr[t] - ar[t]) ** 2 for t in predicted)
    return 1.0 - (6.0 * d2) / (n * (n * n - 1))


def kendall_tau(predicted: Sequence[str], actual: Sequence[str]) -> float:
    """Kendall's tau (no ties across distinct ranks) in ``[-1, 1]``."""
    _validate(predicted, actual)
    n = len(predicted)
    if n < 2:
        return 1.0
    pr, ar = _ranks(predicted), _ranks(actual)
    concordant = discordant = 0
    for a, b in combinations(predicted, 2):
        sign_pred = pr[a] - pr[b]
        sign_actual = ar[a] - ar[b]
        if sign_pred * sign_actual > 0:
            concordant += 1
        else:
            discordant += 1
    return (concordant - discordant) / (n * (n - 1) / 2)


def top_k_hit_rate(predicted: Sequence[str], actual: Sequence[str], k: int) -> float:
    """Fraction of the actual top-k that the prediction also placed in its top-k."""
    _validate(predicted, actual)
    k = min(k, len(predicted))
    if k == 0:
        return 0.0
    return len(set(predicted[:k]) & set(actual[:k])) / k


# Default metric set (CLI contract).
DEFAULT_METRICS = ("spearman_rho", "kendall_tau", "top4_hit_rate")


def compute_metric(name: str, predicted: Sequence[str], actual: Sequence[str]) -> float:
    if name == "spearman_rho":
        return spearman_rho(predicted, actual)
    if name == "kendall_tau":
        return kendall_tau(predicted, actual)
    if name.startswith("top") and name.endswith("_hit_rate"):
        k = int(name[len("top") : -len("_hit_rate")])
        return top_k_hit_rate(predicted, actual, k)
    raise ValueError(f"unknown metric {name!r}")
