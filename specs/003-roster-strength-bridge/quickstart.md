# Quickstart & Validation: ENC Roster-Strength Bridge (Phase 3)

How to set up, run, and validate the roster-strength bridge end-to-end. Run/validation guide;
implementation lives in `tasks.md` and the code.

## Prerequisites

- Features 001 + 002 done: data collected, match outcomes backfilled (`vctm backfill-results`).
- `cd services/core && uv sync --group ml` (MLflow already present from feature 002).
- Schema migrated (no new migration for this feature).

## Quality gates (must stay green — Constitution III)

```bash
make lint && make fmt && make test
```

## Scenario 0 — Backfill player sides (offline, no scraping)

```bash
uv run vctm backfill-sides
```

- **Expected**: each `player_map_stat` is attributed to a match side where resolvable;
  summary reports attributed vs. unresolved counts. Idempotent and offline.

## Scenario 1 — Single real match, end-to-end (NON-NEGOTIABLE gate)

Prove the chain on one real club match before scaling (Constitution III).

1. From a captured match, attribute each player to a side, and build each lineup's as-of
   roster strength (player Elo aggregate) using only matches dated before it.
2. Assert: the strengths are reproducible (byte-identical on re-run) and **no** contributing
   match is dated on/after the match.

## Scenario 2 — Honest bridge evaluation vs. baseline

```bash
uv run vctm eval-bridge --cutoff 2026-04-01 \
  --baseline roster-tier-seed --baseline naive-rating-avg
```

- **Expected**: trains on club matches before the cutoff, evaluates on/after, and prints
  log-loss / accuracy / Brier for the bridge and each baseline + the report path. Checks
  (SC-002/004): every eval match post-dates every train match (`leakage_verified: true`); no
  straddling match; baselines scored on identical matches; a below-baseline bridge labeled a
  non-result. Report validates against `contracts/bridge-report.schema.json`.

## Scenario 3 — Confident ENC matchup

```bash
uv run vctm enc-predict --team-a "Brazil" --team-b "United States of America" --as-of 2026-11-08
```

- **Expected**: **differentiated**, calibrated win probabilities (not ~50/50) with a
  predicted winner and per-team confidence (low when a roster's club history is sparse), plus
  the top contributing players. Read-only.

## Scenario 4 — Roster-derived ENC ranking

```bash
uv run vctm enc-ranking --as-of 2026-11-08 --version enc-2026.bridge.v1
```

- **Expected**: all 16 ENC teams ordered by roster-derived strength, each with confidence and
  contributing players, written as a dated, immutable artifact under
  `artifacts/models/bridge/` (never modifying 001/002 artifacts).

## Done = all gates green

- Sides backfilled with provenance; single-real-match strengths reproducible + leakage-free.
- `eval-bridge` produces a schema-valid, traceable, baseline-relative report on a verified
  split — and reports honestly whether roster-derived strength beats the baseline.
- `enc-predict` returns differentiated, calibrated ENC probabilities with confidence flagging.
- `enc-ranking` produces a dated, immutable 16-team ordering.
