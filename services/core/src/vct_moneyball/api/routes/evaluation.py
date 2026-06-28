"""GET /enc/evaluation — serve the latest published honest evaluation report."""

from __future__ import annotations

from fastapi import APIRouter

from vct_moneyball.api.artifacts import load_evaluation
from vct_moneyball.api.schemas import (
    BaselineMetrics,
    EvaluationResponse,
    Metrics,
    Provenance,
)

router = APIRouter()


def _metrics(m: dict) -> Metrics:
    return Metrics(
        log_loss=m["log_loss"],
        accuracy=m["accuracy"],
        brier=m["brier"],
        calibration_error=m.get("calibration_error"),
    )


@router.get("/enc/evaluation", response_model=EvaluationResponse)
def evaluation(kind: str = "bridge", run: str | None = None) -> EvaluationResponse:
    data = load_evaluation(kind=kind, run=run)
    return EvaluationResponse(
        kind=kind,
        cutoff=data["cutoff"],
        n_train=data["n_train"],
        n_eval=data["n_eval"],
        leakage_verified=bool(data.get("leakage_verified", True)),
        model_metrics=_metrics(data["model"]),
        baselines=[
            BaselineMetrics(label=b["label"], metrics=_metrics(b["metrics"]))
            for b in data["baselines"]
        ],
        provenance=Provenance(
            source="model_run",
            run_id=data["run_id"],
            data_window=data.get("data_window"),
            feature_fingerprint=data.get("feature_fingerprint"),
        ),
    )
