"""T013 — enc-ranking places all 16 ENC teams and is immutable."""

from __future__ import annotations

import argparse
import json
from datetime import datetime

import pytest
from sqlalchemy.orm import Session

from tests.seed import seed_attributed_matches
from vct_moneyball.cli.enc_ranking import run_enc_ranking
from vct_moneyball.common.logging import CliError

pytestmark = pytest.mark.integration


def _args(out_dir, version="enc-2026.bridge.v1") -> argparse.Namespace:
    return argparse.Namespace(
        as_of=datetime(2026, 11, 8).isoformat(),
        lookback_months=12,
        aggregation="mean",
        out_dir=str(out_dir),
        version=version,
        json=True,
        verbose=False,
    )


def test_ranks_16_teams_and_is_immutable(clean_db, tmp_path) -> None:
    with Session(clean_db) as s:
        seed_attributed_matches(s, n_teams=16, enc_teams=16, n_matches=200)
        s.commit()
    assert run_enc_ranking(_args(tmp_path)) == 0

    artifact = json.loads((tmp_path / "enc-2026.bridge.v1" / "enc-ranking.json").read_text())
    assert len(artifact["teams"]) == 16
    assert [t["position"] for t in artifact["teams"]] == list(range(1, 17))
    assert all("confidence" in t for t in artifact["teams"])
    # Immutable: refuse to overwrite.
    with pytest.raises(CliError, match="overwrite"):
        run_enc_ranking(_args(tmp_path))
