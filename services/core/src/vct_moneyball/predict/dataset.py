"""Temporal split + leakage verification.

Splits examples at a cutoff — train strictly before, evaluate on/after — and **verifies**
(not assumes) that every eval match post-dates every train match and that no match appears
on both sides (a match is atomic). Feature leakage-freedom is structural in
``features.build_examples``; this guards the train/eval boundary (FR-004, SC-001).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from vct_moneyball.common.logging import CliError
from vct_moneyball.predict.features import FEATURE_NAMES, MatchExample


@dataclass
class Dataset:
    train: list[MatchExample]
    eval: list[MatchExample]
    cutoff: datetime
    leakage_verified: bool

    def matrix(self, examples: list[MatchExample]) -> tuple[list[list[float]], list[int]]:
        x = [[ex.features[name] for name in FEATURE_NAMES] for ex in examples]
        y = [ex.label for ex in examples]
        return x, y

    @property
    def underpowered(self) -> bool:
        return len(self.eval) < 30


def temporal_split(examples: list[MatchExample], cutoff: datetime) -> Dataset:
    train = [e for e in examples if e.played_at < cutoff]
    eval_ = [e for e in examples if e.played_at >= cutoff]
    if not train:
        raise CliError("no training matches before the cutoff")
    if not eval_:
        raise CliError("no evaluation matches on/after the cutoff")

    # Verify the temporal boundary and atomicity.
    last_train = max(e.played_at for e in train)
    first_eval = min(e.played_at for e in eval_)
    train_ids = {e.match_id for e in train}
    eval_ids = {e.match_id for e in eval_}
    overlap = train_ids & eval_ids
    if overlap:
        raise CliError(f"{len(overlap)} match(es) appear in both train and eval")
    if not (last_train < cutoff <= first_eval):
        raise CliError("temporal split boundary violated (train must precede eval)")

    return Dataset(train=train, eval=eval_, cutoff=cutoff, leakage_verified=True)
