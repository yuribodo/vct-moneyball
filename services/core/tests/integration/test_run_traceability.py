"""T025 — every run is traceable; different params yield distinguishable runs."""

from __future__ import annotations

import argparse
import json
from datetime import datetime

import pytest
from sqlalchemy.orm import Session

from tests.seed import seed_labeled_matches
from vct_moneyball.cli.eval_winrate import run_eval_winrate

pytestmark = pytest.mark.integration


def _args(cutoff: datetime, out_dir, learner: str) -> argparse.Namespace:
    return argparse.Namespace(
        cutoff=cutoff.isoformat(),
        lookback_months=12,
        learner=learner,
        baseline=["winrate-elo"],
        experiment="test-trace",
        out_dir=str(out_dir),
        json=True,
        verbose=False,
    )


def _report(out_dir) -> dict:
    path = next(out_dir.glob("*/report.json"))
    return json.loads(path.read_text())


def test_two_param_sets_are_distinguishable_and_complete(clean_db, tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("MLFLOW_TRACKING_URI", (tmp_path / "mlruns").as_uri())
    with Session(clean_db) as s:
        cutoff = seed_labeled_matches(s)
        s.commit()

    run_eval_winrate(_args(cutoff, tmp_path / "logreg", "logreg"))
    run_eval_winrate(_args(cutoff, tmp_path / "gbt", "gbt"))

    r1 = _report(tmp_path / "logreg")
    r2 = _report(tmp_path / "gbt")

    # Distinguishable: different runs and different feature/config fingerprints (learner differs).
    assert r1["run_id"] != r2["run_id"]
    assert r1["feature_fingerprint"] != r2["feature_fingerprint"]

    # Each run carries full lineage.
    required = ("data_window", "feature_fingerprint", "learner", "cutoff", "model", "baselines")
    for r in (r1, r2):
        for key in required:
            assert key in r
        assert r["data_window"]["start"] < r["data_window"]["end"]
