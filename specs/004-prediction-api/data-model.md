# Phase 1 Data Model: ENC Prediction API (Phase 4)

No database schema change — the service is read-only. The "data model" here is the **response
shapes** (Pydantic) the endpoints return, and the read sources they draw from.

## Read sources (no writes)

- **Published artifacts** (`artifacts/`): the roster-derived ENC ranking
  (`models/bridge/<version>/enc-ranking.json`), the feature-001 locked ranking
  (`rankings/enc-2026/<version>/ranking.json`), and eval reports
  (`models/{winrate,bridge}/<run>/report.json`). Served byte-faithfully.
- **Database** (read-only): rosters/players/matches for live predictions (via the existing
  bridge logic). No endpoint issues a write.

## Response entities (Pydantic schemas)

### `Provenance`

- `source` — `"artifact"` or `"model_run"`
- `version` / `run_id` — the artifact version or MLflow run id
- `as_of` / `data_window` — date or window the value reflects (when applicable)
- `feature_fingerprint` — when a model produced it

### `RankingResponse`

- `version`, `as_of`, `aggregation`
- `teams[]` — `{ position, team, score|roster_elo, confidence }` (16 entries)
- `provenance: Provenance`

### `PredictionResponse`

- `team_a`, `team_b`, `as_of`
- `p_a`, `p_b` (sum to 1.0), `winner`
- `low_confidence: bool`
- `contributors_a[]`, `contributors_b[]` — top player handles
- `provenance: Provenance`

### `EvaluationResponse`

- `kind` — `"winrate"` or `"bridge"`
- `cutoff`, `n_train`, `n_eval`, `leakage_verified`
- `model: Metrics`, `baselines[]: { label, metrics }`
- `provenance: Provenance`

### `ErrorResponse`

- `error` — human-readable message
- `status` — the HTTP status code (400/404/503)

## Validation rules (enforced in code, from spec)

- The ranking endpoint returns exactly the published artifact's 16 ordered teams + confidence,
  unchanged, with provenance (FR-001/FR-008); a missing artifact → 404 (FR-007).
- A prediction equals the CLI's for the same inputs (FR-005); unknown team / bad date → 400;
  sparse rosters → `low_confidence: true` (FR-003); DB down → 503 (FR-007).
- The evaluation endpoint returns the published report's metrics + baselines + run id
  unchanged (FR-004/FR-008).
- No endpoint performs a write (FR-006/SC-007).
- Every response carries provenance (SC-004).
