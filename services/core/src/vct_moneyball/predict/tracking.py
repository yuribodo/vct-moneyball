"""MLflow tracking wrapper + dataset/feature/config fingerprint.

Every training/evaluation run is logged to a local MLflow file store (``mlruns/``) with its
params, metrics, data window, and a deterministic fingerprint of the feature/config, so any
reported number is traceable to the exact run (Constitution I/IV; FR-008, SC-005).
"""

from __future__ import annotations

import hashlib
import json
import pathlib
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any


def fingerprint(payload: dict[str, Any]) -> str:
    """Deterministic short hash of a JSON-serializable config payload."""
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


def _mlruns_dir() -> pathlib.Path:
    for base in [pathlib.Path.cwd(), *pathlib.Path(__file__).resolve().parents]:
        if (base / ".git").is_dir() or (base / "services" / "core").is_dir():
            return base / "mlruns"
    return pathlib.Path.cwd() / "mlruns"


def configure_tracking() -> None:
    import os

    import mlflow

    # The local file store is sufficient for this project; opt out of MLflow 3's
    # maintenance-mode guard for it.
    os.environ.setdefault("MLFLOW_ALLOW_FILE_STORE", "true")
    # Honor an explicit override (tests point this at a tmp dir); else the repo mlruns/.
    uri = os.environ.get("MLFLOW_TRACKING_URI") or _mlruns_dir().as_uri()
    mlflow.set_tracking_uri(uri)


@contextmanager
def run(experiment: str, params: dict[str, Any]) -> Iterator[Any]:
    """Open an MLflow run under ``experiment`` with ``params`` logged."""
    import mlflow

    configure_tracking()
    mlflow.set_experiment(experiment)
    with mlflow.start_run() as active:
        mlflow.log_params(params)
        yield active


def log_metrics(prefix: str, metrics: dict[str, float]) -> None:
    import mlflow

    mlflow.log_metrics({f"{prefix}_{k}": float(v) for k, v in metrics.items()})


def log_artifact(path: str | pathlib.Path) -> None:
    import mlflow

    mlflow.log_artifact(str(path))
