"""T020 — eval-winrate writes a schema-valid, baseline-relative, leakage-verified report."""

from __future__ import annotations

import argparse
import json
from datetime import datetime

import pytest
from sqlalchemy.orm import Session

from tests.seed import seed_labeled_matches
from vct_moneyball.cli.eval_winrate import run_eval_winrate
from vct_moneyball.predict.report import validate_report

pytestmark = pytest.mark.integration


def _args(cutoff: datetime, out_dir, learner: str = "logreg") -> argparse.Namespace:
    return argparse.Namespace(
        cutoff=cutoff.isoformat(),
        lookback_months=12,
        learner=learner,
        baseline=["winrate-elo", "coin"],
        experiment="test-winrate",
        out_dir=str(out_dir),
        json=True,
        verbose=False,
    )


def test_eval_writes_schema_valid_report(clean_db, tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("MLFLOW_TRACKING_URI", (tmp_path / "mlruns").as_uri())
    with Session(clean_db) as s:
        cutoff = seed_labeled_matches(s)
        s.commit()

    assert run_eval_winrate(_args(cutoff, tmp_path / "reports")) == 0

    reports = list((tmp_path / "reports").glob("*/report.json"))
    assert len(reports) == 1
    report = json.loads(reports[0].read_text())
    validate_report(report)  # raises if invalid
    assert report["leakage_verified"] is True
    assert report["n_train"] > 0 and report["n_eval"] > 0
    labels = {b["label"] for b in report["baselines"]}
    assert {"winrate-elo", "coin"} <= labels
    # The learnable seed should let the model beat the coin baseline on log-loss.
    coin = next(b for b in report["baselines"] if b["label"] == "coin")
    assert report["model"]["log_loss"] < coin["metrics"]["log_loss"]
