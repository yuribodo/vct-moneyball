"""Versioned scoring & pipeline configuration.

Every parameter that influences a ranking lives here so the whole ranking is a
deterministic function of (data + this config). ``config_hash`` is recorded in the
artifact for lineage (Constitution I / IV). Changing any value below changes the hash
and therefore must produce a new, separately-versioned ranking.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field, replace

# --- Metric weights -------------------------------------------------------------
# Per-map player composite = weighted sum of within-window normalized metrics.
# Weights are explicit and versioned; they MUST sum to 1.0.
DEFAULT_METRIC_WEIGHTS: dict[str, float] = {
    "rating": 0.40,
    "acs": 0.25,
    "kast": 0.15,
    "adr": 0.10,
    "kd": 0.10,
}


@dataclass(frozen=True)
class ScoringConfig:
    """Immutable, hashable scoring parameters."""

    # Data window (R2): a fixed recent window of professional play.
    data_window_months: int = 12

    # Minimum maps (per map type) a player must have in-window to receive a
    # data-driven score; below this they fall back to the labeled baseline (R3).
    min_history_maps: int = 3

    # Metric weights for the per-map player composite (must sum to 1.0).
    metric_weights: dict[str, float] = field(default_factory=lambda: dict(DEFAULT_METRIC_WEIGHTS))

    # Confidence cutoffs expressed as the fraction of a team/contributor's maps that
    # are backed by sufficient history. >= high_cutoff -> high; >= medium_cutoff ->
    # medium; otherwise low.
    confidence_high_cutoff: float = 0.80
    confidence_medium_cutoff: float = 0.50

    def __post_init__(self) -> None:
        total = sum(self.metric_weights.values())
        if abs(total - 1.0) > 1e-9:
            raise ValueError(f"metric_weights must sum to 1.0, got {total!r}")
        if not 0.0 <= self.confidence_medium_cutoff <= self.confidence_high_cutoff <= 1.0:
            raise ValueError("confidence cutoffs must satisfy 0 <= medium <= high <= 1")
        if self.min_history_maps < 1:
            raise ValueError("min_history_maps must be >= 1")
        if self.data_window_months < 1:
            raise ValueError("data_window_months must be >= 1")

    def canonical(self) -> dict[str, object]:
        """Stable, JSON-serializable representation used for hashing."""
        return {
            "data_window_months": self.data_window_months,
            "min_history_maps": self.min_history_maps,
            "metric_weights": {k: round(v, 6) for k, v in sorted(self.metric_weights.items())},
            "confidence_high_cutoff": self.confidence_high_cutoff,
            "confidence_medium_cutoff": self.confidence_medium_cutoff,
        }

    @property
    def config_hash(self) -> str:
        """Deterministic hash of all scoring parameters (lineage)."""
        blob = json.dumps(self.canonical(), sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]

    def with_(self, **changes: object) -> ScoringConfig:
        """Return a copy with overrides (e.g. a different window for one run)."""
        return replace(self, **changes)  # type: ignore[arg-type]


# The default, versioned configuration used unless a command overrides it.
DEFAULT_CONFIG = ScoringConfig()
