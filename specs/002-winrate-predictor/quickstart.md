# Quickstart & Validation: Match Winrate Predictor (Phase 2)

How to set up, run, and validate the winrate predictor end-to-end. Run/validation guide —
implementation lives in `tasks.md` and the code.

## Prerequisites

- Feature 001 collected data present (`vctm collect` has been run; cached HTML available).
- `cd services/core && uv sync --group ml` (adds MLflow alongside the existing ml stack).
- Schema migrated: `uv run alembic upgrade head` (adds the match outcome columns).

## Quality gates (must stay green — Constitution III)

```bash
make lint && make fmt && make test
```

## Scenario 0 — Backfill match outcomes (offline, no scraping)

```bash
uv run vctm backfill-results
```

- **Expected**: both teams + a series result populated on each match where the cached page
  has a parseable score; summary reports matches labeled vs. left unlabeled. Re-run is
  idempotent and offline.

## Scenario 1 — Single real match, end-to-end (NON-NEGOTIABLE gate)

Prove the chain on one real match before scaling (Constitution III).

1. From the captured fixture, derive the outcome label and build the as-of feature vector.
2. Assert: the label matches the page's series result; **every** feature input is dated
   strictly before the match; re-running gives byte-identical features (determinism).

## Scenario 2 — Train + evaluate vs. baseline (the honesty gate)

```bash
uv run vctm eval-winrate --cutoff <CUTOFF_DATE> --baseline roster-tier-seed --baseline power-rank-favorite
```

- **Expected**: trains on matches before the cutoff, evaluates only on/after it, and prints a
  table of **log-loss / accuracy / Brier / calibration** for the model and each baseline,
  plus the report path. Checks enforced (SC-001/002/003/006):
  - every eval match is dated after every train match (verified; `leakage_verified: true`);
  - no match straddles the cutoff;
  - the model's metrics appear beside each baseline's, and a below-baseline model is labeled
    a non-result;
  - the report validates against `contracts/eval-report.schema.json` and carries the MLflow
    run id + feature fingerprint.
- **Reproducibility**: re-running with the same cutoff/config reproduces the metrics exactly.

## Scenario 3 — Predict a matchup

```bash
uv run vctm predict-match --team-a "United States of America" --team-b "Brazil" --as-of 2026-11-08
```

- **Expected**: two win probabilities summing to 1.0, the predicted winner, and a
  low-confidence flag if either team is below the history threshold. Read-only.

## Scenario 4 — Leakage guard (negative test)

- Inject a stat dated on the match day into a training match and confirm the dataset builder
  **excludes** it and the run still reports `leakage_verified: true` (the guard catches it).

## Done = all gates green

- Outcomes backfilled offline with provenance; single-real-match label+features reproducible.
- `eval-winrate` produces a schema-valid, traceable, baseline-relative report on a verified
  temporal split.
- `predict-match` returns calibrated probabilities with confidence flagging.
- The model's value over the feature-001 prior is reported honestly — win or lose.
