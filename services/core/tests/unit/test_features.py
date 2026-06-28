"""T011 — as-of features are leakage-free and deterministic."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from vct_moneyball.predict.features import FeatureConfig, build_examples, features_as_of
from vct_moneyball.predict.labels import LabeledMatch

pytestmark = pytest.mark.unit

A, B, C = 1, 2, 3
T0 = datetime(2026, 1, 1, tzinfo=UTC)
T1 = datetime(2026, 2, 1, tzinfo=UTC)
T2 = datetime(2026, 3, 1, tzinfo=UTC)
CFG = FeatureConfig()


def _m(mid: int, t: datetime, a: int, b: int, winner: int) -> LabeledMatch:
    return LabeledMatch(match_id=mid, played_at=t, team_a_id=a, team_b_id=b, winner_team_id=winner)


MATCHES = [_m(1, T0, A, B, A), _m(2, T1, A, C, A), _m(3, T2, A, B, A)]


def test_first_match_has_neutral_features() -> None:
    ex = build_examples(MATCHES, CFG)
    # Both teams unseen → base elo, neutral form, zero volume.
    assert ex[0].features["elo_diff"] == 0.0
    assert ex[0].features["form_diff"] == 0.0
    assert ex[0].features["log_volume_diff"] == 0.0
    assert ex[0].min_volume == 0


def test_later_match_reflects_only_prior_results() -> None:
    ex = build_examples(MATCHES, CFG)
    # By match 3, A has beaten B and C → A's elo above B's.
    assert ex[2].features["elo_diff"] > 0.0
    assert ex[2].min_volume >= 1


def test_features_as_of_excludes_the_match_itself() -> None:
    ex = build_examples(MATCHES, CFG)
    # Reconstructing A-vs-B as of T2 must match what example 3 saw (only matches < T2).
    feats, vol = features_as_of(MATCHES, A, B, T2, CFG)
    assert feats == ex[2].features
    # As of T0 (before any match) everything is neutral — no leakage from future games.
    feats0, vol0 = features_as_of(MATCHES, A, B, T0, CFG)
    assert feats0["elo_diff"] == 0.0 and vol0 == 0


def test_build_examples_is_deterministic() -> None:
    assert build_examples(MATCHES, CFG) == build_examples(MATCHES, CFG)
