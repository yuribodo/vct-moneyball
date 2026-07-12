"""T011 — GET /enc/evaluation serves the published report or 404."""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from vct_moneyball.api.app import create_app

pytestmark = pytest.mark.integration


def _write_eval(tmp_path):
    d = tmp_path / "artifacts" / "models" / "bridge" / "run123"
    d.mkdir(parents=True)
    (d / "report.json").write_text(
        json.dumps(
            {
                "run_id": "run123",
                "cutoff": "2026-04-01T00:00:00+00:00",
                "n_train": 600,
                "n_eval": 400,
                "leakage_verified": True,
                "feature_fingerprint": "abcd1234",
                "data_window": {
                    "start": "2025-07-01T00:00:00+00:00",
                    "end": "2026-06-25T00:00:00+00:00",
                },
                "model": {"log_loss": 0.64, "accuracy": 0.62, "brier": 0.23},
                "baselines": [
                    {
                        "label": "winrate-elo",
                        "metrics": {"log_loss": 0.66, "accuracy": 0.6, "brier": 0.24},
                    }
                ],
            }
        )
    )
    (d.parent / "LATEST_EVAL").write_text("run123\n")


def test_evaluation_404_when_absent(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("vct_moneyball.api.artifacts.repo_root", lambda: tmp_path)
    assert TestClient(create_app()).get("/enc/evaluation").status_code == 404


def test_evaluation_served(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("vct_moneyball.api.artifacts.repo_root", lambda: tmp_path)
    _write_eval(tmp_path)
    body = TestClient(create_app()).get("/enc/evaluation?kind=bridge").json()
    assert body["model_metrics"]["log_loss"] == 0.64
    assert body["baselines"][0]["label"] == "winrate-elo"
    assert body["provenance"]["run_id"] == "run123"
    assert body["leakage_verified"] is True


def test_health_ok() -> None:
    body = TestClient(create_app()).get("/health").json()
    assert body["status"] == "ok"
