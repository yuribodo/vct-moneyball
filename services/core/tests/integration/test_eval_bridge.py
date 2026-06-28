"""T016 — eval-bridge writes a schema-valid, baseline-relative report."""

from __future__ import annotations

import argparse
import json
from datetime import datetime

import pytest
from sqlalchemy.orm import Session

from tests.seed import seed_attributed_matches
from vct_moneyball.bridge.report import validate_report
from vct_moneyball.cli.eval_bridge import run_eval_bridge

pytestmark = pytest.mark.integration


def _args(cutoff: datetime, out_dir) -> argparse.Namespace:
    return argparse.Namespace(
        cutoff=cutoff.isoformat(),
        lookback_months=12,
        aggregation="mean",
        baseline=["winrate-elo", "coin"],
        experiment="test-bridge",
        out_dir=str(out_dir),
        json=True,
        verbose=False,
    )


def test_eval_bridge_report(clean_db, tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("MLFLOW_TRACKING_URI", (tmp_path / "mlruns").as_uri())
    with Session(clean_db) as s:
        cutoff = seed_attributed_matches(s)
        s.commit()
    assert run_eval_bridge(_args(cutoff, tmp_path / "reports")) == 0

    report = json.loads(next((tmp_path / "reports").glob("*/report.json")).read_text())
    validate_report(report)
    assert report["leakage_verified"] is True
    assert report["attribution_coverage"] > 0.9
    assert report["aggregation"] == "mean"
    coin = next(b for b in report["baselines"] if b["label"] == "coin")
    assert report["model"]["log_loss"] < coin["metrics"]["log_loss"]
