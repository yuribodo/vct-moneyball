"""Probabilistic evaluation metrics (pure Python, deterministic).

Log-loss (primary), accuracy, Brier score, and expected calibration error — computed the
same way for the model and every baseline so they are directly comparable (FR-006, SC-003).
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass

_EPS = 1e-12


@dataclass(frozen=True)
class Metrics:
    log_loss: float
    accuracy: float
    brier: float
    calibration_error: float

    def as_dict(self) -> dict[str, float]:
        return {
            "log_loss": round(self.log_loss, 6),
            "accuracy": round(self.accuracy, 6),
            "brier": round(self.brier, 6),
            "calibration_error": round(self.calibration_error, 6),
        }


def _clip(p: float) -> float:
    return min(1.0 - _EPS, max(_EPS, p))


def log_loss(y_true: Sequence[int], probs: Sequence[float]) -> float:
    n = len(y_true)
    if n == 0:
        return 0.0
    total = 0.0
    for y, p in zip(y_true, probs, strict=True):
        p = _clip(p)
        total += -(y * math.log(p) + (1 - y) * math.log(1 - p))
    return total / n


def accuracy(y_true: Sequence[int], probs: Sequence[float]) -> float:
    n = len(y_true)
    if n == 0:
        return 0.0
    return sum((p > 0.5) == bool(y) for y, p in zip(y_true, probs, strict=True)) / n


def brier(y_true: Sequence[int], probs: Sequence[float]) -> float:
    n = len(y_true)
    if n == 0:
        return 0.0
    return sum((p - y) ** 2 for y, p in zip(y_true, probs, strict=True)) / n


def calibration_error(y_true: Sequence[int], probs: Sequence[float], bins: int = 10) -> float:
    """Expected calibration error over equal-width probability bins."""
    n = len(y_true)
    if n == 0:
        return 0.0
    buckets: list[list[tuple[int, float]]] = [[] for _ in range(bins)]
    for y, p in zip(y_true, probs, strict=True):
        idx = min(bins - 1, int(p * bins))
        buckets[idx].append((y, p))
    ece = 0.0
    for bucket in buckets:
        if not bucket:
            continue
        conf = sum(p for _, p in bucket) / len(bucket)
        acc = sum(y for y, _ in bucket) / len(bucket)
        ece += (len(bucket) / n) * abs(acc - conf)
    return ece


def compute_metrics(y_true: Sequence[int], probs: Sequence[float]) -> Metrics:
    return Metrics(
        log_loss=log_loss(y_true, probs),
        accuracy=accuracy(y_true, probs),
        brier=brier(y_true, probs),
        calibration_error=calibration_error(y_true, probs),
    )
