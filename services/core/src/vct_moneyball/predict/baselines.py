"""Explicit, non-learned baselines — the model must beat at least one (Constitution IV).

Each baseline maps a match example to P(team_a wins) using only the same leakage-free
pre-match features the model sees, so it is scored on the identical eval matches.
"""

from __future__ import annotations

from collections.abc import Callable

from vct_moneyball.predict.features import MatchExample

BaselineFn = Callable[[MatchExample], float]

_EPS = 1e-6


def _clamp(p: float) -> float:
    return min(1.0 - _EPS, max(_EPS, p))


def winrate_elo(ex: MatchExample) -> float:
    """Pure Elo expectation from the chronological rating difference."""
    return _clamp(1.0 / (1.0 + 10.0 ** (-ex.features["elo_diff"] / 400.0)))


def recent_form(ex: MatchExample) -> float:
    """Map the recent win-rate difference onto a probability."""
    return _clamp(0.5 + 0.5 * ex.features["form_diff"])


def coin(ex: MatchExample) -> float:
    """Uninformed 0.5 — the honesty floor."""
    return 0.5


_REGISTRY: dict[str, BaselineFn] = {
    "winrate-elo": winrate_elo,
    "recent-form": recent_form,
    "coin": coin,
}

DEFAULT_BASELINES = ("winrate-elo", "coin")


def get_baseline(label: str) -> BaselineFn:
    if label not in _REGISTRY:
        from vct_moneyball.common.logging import CliError

        raise CliError(f"unknown baseline {label!r}; available: {sorted(_REGISTRY)}")
    return _REGISTRY[label]


def baseline_probs(label: str, examples: list[MatchExample]) -> list[float]:
    fn = get_baseline(label)
    return [fn(ex) for ex in examples]
