# Phase 1 Data Model: Match Winrate Predictor (Phase 2)

The predictor reads feature-001 data; the only **schema change** is additive — persist each
match's two teams and its result so outcome labels exist. Everything else (features, runs,
reports) lives in code, MLflow, and committed artifacts, not new tables.

## Schema change (additive, Alembic migration)

### `match` — add match identity + outcome

New nullable columns on the existing `match` table (provenance columns already present):

- `team_a_id bigint NULL` FK → `team(id)` `ON DELETE SET NULL`
- `team_b_id bigint NULL` FK → `team(id)` `ON DELETE SET NULL`
- `winner_team_id bigint NULL` FK → `team(id)` `ON DELETE SET NULL`
- `score_a int NULL`, `score_b int NULL` — series score (maps won by each side)

**Indexes**: `(team_a_id)`, `(team_b_id)`, `(winner_team_id)`.

**Validation / population** (in code, from the cached match-page header — Constitution I):

- Both teams come from the header team links (`/team/<id>/…`), so collection now **upserts a
  `team` row for each side** (clubs included, `is_enc_2026 = false`) carrying `vlr_team_id` +
  provenance.
- `winner_team_id` is the side with the higher series score; if the score is unpar.seable,
  fall back to the majority of `match_map.winner_team_id`; if still undetermined the match is
  left **unlabeled** (excluded from training, logged — never guessed).
- A labeled match satisfies: `team_a_id` and `team_b_id` set and distinct, `winner_team_id ∈
  {team_a_id, team_b_id}`, `score_a ≠ score_b`.

> No other feature-001 tables change. `match_map.winner_team_id` (already present) may be
> populated by the same re-parse to enable optional map-level features.

## Logical entities (not new tables)

### Training example (built in memory, never persisted raw)

One labeled match → `(features, label)` where:

- `label ∈ {1, 0}` = did `team_a` win (sides assigned deterministically, e.g. by team id, so
  the encoding is reproducible).
- `features` = the **as-of** opponent-difference vector (research R2), every component
  computed only from rows dated `< match.played_at`.
- Carries `match_id` + `played_at` for the temporal split and traceability.

### Feature set

The named, **versioned** set of pre-match signals with a fingerprint hash (look-back
windows, which signals are on, smoothing). The fingerprint is logged with every run so a
metric is reproducible (FR-008/FR-009).

### Model run (MLflow)

A single train(+evaluate) execution: params (learner, look-backs, cutoff), metrics (model +
each baseline: log-loss, accuracy, Brier, calibration error), the data-window bounds, the
feature/config fingerprint, the dataset fingerprint, and the model artifact + report. Append
-only by nature (MLflow run ids).

### Baseline

An explicit non-learned rule producing a probability/label per eval match: roster-tier
pedigree, favorite-by-prior-power-ranking, or chronological win-rate/Elo (research R6).

### Evaluation report (committed artifact)

`artifacts/models/winrate/<run>/report.json` (+ `report.md`): the data window, cutoff,
feature/config fingerprint, MLflow run id, per-metric model-vs-baseline values, calibration
summary, and eval sample size. Append-only and schema-validated (see `contracts/`).

## Validation rules (enforced in code, from spec)

- Every evaluated match is dated strictly after every training match; zero overlap; no match
  split across the cutoff (FR-004, SC-001) — verified each run.
- No feature reads a row dated on/after its match (FR-002) — asserted in the dataset builder
  and unit-tested.
- A prediction for a team below the minimum-history threshold is returned with a
  low-confidence flag (FR-007, SC-007).
- Every reported metric is paired with ≥1 baseline value on the same matches (FR-005/FR-006).
- A reported number is traceable to its MLflow run + fingerprint (FR-008, SC-005).
