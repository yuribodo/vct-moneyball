# Phase 1 Data Model: ENC Roster-Strength Bridge (Phase 3)

The bridge reads the feature-001/002 schema; the only persisted change is **populating an
existing column**. Everything else (ratings, strengths, runs, reports) is computed in memory,
tracked in MLflow, and written as committed artifacts.

## Persisted change (no new columns/migration)

### `player_map_stat.team_id` — populate the existing (currently null) column

Set each stat row's `team_id` to the match side the player was on, derived offline from the
cached HTML: match the parser's per-player `team_abbrev` to the match's `team_a_id` /
`team_b_id` (whose teams carry name + `vlr_team_id`).

- **Validation**: `team_id ∈ {match.team_a_id, match.team_b_id}` for a labeled match; rows
  whose side cannot be resolved are left `NULL` (excluded from rating, logged — never guessed).
- **Idempotent**: re-running the attribution yields the same assignments.
- Uses the existing FK/index on `player_map_stat.team_id`; no DDL.

## Logical entities (not new tables)

### Player rating state (in-memory, chronological replay)

Per player: an Elo updated by the result of each attributed club match they played, a recent
win-rate (form), and a match count. A player's strength **as of** a date uses only matches
dated before it (leakage-free by construction).

### Roster / lineup strength (as-of)

The aggregate of a set of players' as-of ratings into a team strength: mean (optionally
top-k) Elo, aggregate form, total volume, and a **confidence** label derived from how much of
the lineup meets the minimum-history threshold.

- National team → its **active roster** (from `team_player`, `is_active = true`).
- Club match side → the players who actually played that match.

### Bridge example (built in memory)

One real club match → `(features, label)`: features = the as-of **difference** of the two
sides' roster strengths (Elo diff, form diff, log-volume diff); label = which side won.
Carries `match_id` + `played_at` for the temporal split and traceability.

### Bridge baseline

An explicit non-derived rule producing a probability/ordering on the same matches: the
feature-001 roster-tier pedigree, or a naive lineup average of player VLR rating.

### Bridge evaluation (committed artifact)

`artifacts/models/bridge/<run>/report.json` (+ `report.md`): data window, cutoff,
feature/config fingerprint, MLflow run id, leakage flag, n_train/n_eval, and per-metric
bridge-vs-baseline values (accuracy, log-loss, Brier). Append-only, schema-validated.

### ENC ranking (committed artifact)

`artifacts/models/bridge/<run>/enc-ranking.json` (+ `.md`): the 16 ENC teams ordered by
roster-derived strength as of the lock date, each with strength, confidence, and the
contributing players. Dated, immutable, citing its run (Constitution II).

## Validation rules (enforced in code, from spec)

- A roster-derived strength uses only data dated before its as-of date (FR-001, SC-002) —
  verified.
- ENC matchups with both rosters above the history threshold yield differentiated, calibrated
  probabilities; otherwise low-confidence (FR-002/FR-003, SC-001/SC-003).
- All 16 ENC teams are placed with a strength + confidence; sparse rosters flagged, not
  dropped (FR-004, SC-003).
- Bridge metrics are reported beside ≥1 baseline on identical held-out matches; a
  non-improvement is reported (FR-005/FR-006, SC-004).
- Strengths/metrics are traceable to contributing players + run + config (FR-007, SC-005) and
  reproducible (FR-008, SC-006).
