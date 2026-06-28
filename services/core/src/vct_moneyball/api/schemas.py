"""Pydantic response schemas for the read-only prediction API.

Every success response carries a ``Provenance`` block (which artifact/run produced it) so a
consumer can audit any served value (FR-008).
"""

from __future__ import annotations

from pydantic import BaseModel


class Provenance(BaseModel):
    source: str  # "artifact" | "model_run"
    version: str | None = None
    run_id: str | None = None
    as_of: str | None = None
    data_window: dict[str, str] | None = None
    feature_fingerprint: str | None = None


class RankingTeam(BaseModel):
    position: int
    team: str
    score: float
    confidence: str


class RankingResponse(BaseModel):
    version: str
    as_of: str | None = None
    aggregation: str | None = None
    teams: list[RankingTeam]
    provenance: Provenance


class PredictionResponse(BaseModel):
    team_a: str
    team_b: str
    as_of: str
    p_a: float
    p_b: float
    winner: str
    low_confidence: bool
    contributors_a: list[str]
    contributors_b: list[str]
    provenance: Provenance


class Metrics(BaseModel):
    log_loss: float
    accuracy: float
    brier: float
    calibration_error: float | None = None


class BaselineMetrics(BaseModel):
    label: str
    metrics: Metrics


class EvaluationResponse(BaseModel):
    kind: str
    cutoff: str
    n_train: int
    n_eval: int
    leakage_verified: bool
    model_metrics: Metrics
    baselines: list[BaselineMetrics]
    provenance: Provenance


class HealthResponse(BaseModel):
    status: str
    database: str


class ErrorResponse(BaseModel):
    error: str
    status: int
