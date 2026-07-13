# CLI Contract: `vctm` roster-bridge subcommands (Phase 3)

Four new stages on the existing `vctm` CLI. Deterministic given versioned inputs + config.
Text in/out, `--json` optional; errors to stderr with non-zero exit.

## `vctm backfill-sides`

Populate `player_map_stat.team_id` (the side each player was on) offline from cached HTML.
Prerequisite for player ratings.

- **Options**: `--use-cache/--no-cache` (default `--use-cache`).
- **Postconditions**: each stat row's `team_id` set to the match side where resolvable.
- **Exit/validation**: non-zero if no labeled matches exist. Reports attributed vs.
  unresolved counts. Idempotent.
- **Output**: summary counts (text or `--json`).

## `vctm eval-bridge`

Honest evaluation of roster-derived strength vs. baselines on held-out real club matches.

- **Options**: `--cutoff <date>` (train before / eval on-after), `--lookback-months <int>`,
  `--aggregation <mean|topk>`, `--baseline <label>...` (default `roster-tier-seed`,
  `naive-rating-avg`), `--out-dir <path>` (default `artifacts/models/bridge/`),
  `--experiment <name>`.
- **Preconditions**: sides backfilled; labeled matches on both sides of the cutoff.
- **Postconditions**: writes `…/<run>/report.json` (validates against
  `bridge-report.schema.json`) + `report.md`; logs the run to MLflow.
- **Exit/validation**: non-zero (writes nothing) if the split overlaps, a match straddles the
  cutoff, the eval block is empty, or a baseline is missing; underpowered-sample warning when
  the eval block is small.
- **Output**: per-metric bridge-vs-baseline table (log-loss, accuracy, Brier) + report path.

## `vctm enc-predict`

Predict a single ENC matchup using roster-derived strength.

- **Options**: `--team-a <name|vlr-id>`, `--team-b <name|vlr-id>`, `--as-of <date>`
  (default now), `--lookback-months <int>`, `--run <mlflow-run-id>` (default latest bridge
  run), `--json`.
- **Preconditions**: a trained bridge run exists; both ENC teams resolvable with active
  rosters.
- **Postconditions**: none (read-only).
- **Exit/validation**: non-zero if a team is unresolvable or the run is unknown.
- **Output**: win probability per side (summing to 1.0), predicted winner, per-team
  confidence (low when a roster's club history is sparse), and the top contributing players.

## `vctm enc-ranking`

Roster-derived ordering of the 16 ENC teams.

- **Options**: `--as-of <date>` (lock date), `--lookback-months <int>`, `--run <id>`,
  `--out-dir <path>` (default `artifacts/models/bridge/`), `--version <id>`, `--publish`
  (points the `LATEST` pointer at this version once written).
- **Preconditions**: 16 ENC teams each with an active roster; sides backfilled.
- **Postconditions**: writes a dated, immutable `enc-ranking.json` (+ `.md`) citing its run;
  inserts no rows that modify feature-001/002 artifacts.
- **Exit/validation**: non-zero if ≠16 ENC teams resolve or the output already exists.
- **Output**: the 16-team ordered table with strength + confidence + `separation` (text or
  `--json`). Confidence measures per-player data sufficiency; each team additionally carries
  `elo_margin_to_next` (Elo gap to its nearest ranked neighbor) and a derived `separation`
  (`clear` / `contested` / `razor-thin`) — a data-rich team can still be a statistical dead
  heat with its neighbor, which confidence alone cannot express.

## Cross-cutting

- `--json` on every command for machine-readable output.
- Non-zero exit on any validation failure; reason on stderr.
- No command mutates a previously published artifact or MLflow run.
- Every strength/metric is traceable to its run id + feature fingerprint + contributing players.
