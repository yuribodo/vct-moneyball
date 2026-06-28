# CLI Contract: `vctm` winrate subcommands (Phase 2)

Three new pipeline stages on the existing `vctm` CLI. Deterministic given versioned inputs +
config. Text in/out, `--json` optional; errors to stderr with non-zero exit.

## `vctm backfill-results`

Re-parse cached match HTML to populate the new match identity + outcome (offline; no
scraping). Prerequisite for labeled training.

- **Options**: `--use-cache/--no-cache` (default `--use-cache`).
- **Postconditions**: `team` rows upserted for both sides of each match (with `vlr_team_id`
  + provenance); `match.team_a_id/team_b_id/winner_team_id/score_a/score_b` set where
  derivable.
- **Exit/validation**: non-zero if no cached matches exist. Reports counts: matches labeled,
  matches left unlabeled (no parseable result).
- **Output**: summary counts (text or `--json`).

## `vctm train-winrate`

Train + calibrate a model on matches before a cutoff and log the run.

- **Options**: `--cutoff <date>` (train strictly before), `--lookback-months <int>`,
  `--learner <logreg|gbt>` (default `logreg`), `--features <fingerprintable flags>`,
  `--experiment <name>` (MLflow).
- **Preconditions**: labeled matches exist (run `backfill-results` first).
- **Postconditions**: an MLflow run logging params, the data window, the feature/config +
  dataset fingerprint, and the calibrated model artifact.
- **Exit/validation**: non-zero if no labeled training matches, or if any training feature is
  found to read on/after its match (leakage guard).
- **Output**: run id + training summary (text or `--json`).

## `vctm eval-winrate`

Evaluate on a held-out future block vs. baselines (the honesty gate).

- **Options**: `--cutoff <date>` (train before / eval on-after), `--baseline <label>...`
  (default `roster-tier-seed`, `power-rank-favorite`, `winrate-elo`), `--rolling <int>`
  (optional successive cutoffs), `--out-dir <path>` (default
  `artifacts/models/winrate/`), plus the `train-winrate` learner/feature options.
- **Preconditions**: labeled matches on both sides of the cutoff.
- **Postconditions**: writes `…/<run>/report.json` (validates against
  `eval-report.schema.json`) + `report.md`; logs metrics to the MLflow run.
- **Exit/validation**: non-zero (writes nothing) if the split has any overlap, if a match
  straddles the cutoff, if the eval block is empty, or if any baseline is missing. Emits an
  underpowered-sample warning when the eval block is small.
- **Output**: per-metric model-vs-baseline table (log-loss, accuracy, Brier, calibration)
  and the report path (text or `--json`).

## `vctm predict-match`

Predict a single upcoming matchup.

- **Options**: `--team-a <name|vlr-id>`, `--team-b <name|vlr-id>`, `--as-of <date>`
  (default now), `--run <mlflow-run-id>` (default latest), `--json`.
- **Preconditions**: a trained model exists; both teams resolvable.
- **Postconditions**: none (read-only).
- **Exit/validation**: non-zero if a team is unresolvable or the model run is unknown.
- **Output**: win probability per side (summing to 1.0), predicted winner, and a
  low-confidence flag when either team is below the history threshold.

## Cross-cutting

- `--json` on every command for machine-readable output.
- Non-zero exit on any validation failure; human-readable reason on stderr.
- No command mutates a previously published report or an MLflow run.
- Every reported metric is traceable to its MLflow run id + fingerprint.
