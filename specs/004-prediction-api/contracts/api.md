# API Contract: ENC Prediction API (Phase 4)

Read-only HTTP service. All responses are JSON; every success carries a `provenance` block;
failures use honest status codes with an `ErrorResponse` body. No endpoint mutates anything.

## `GET /health`

- **200**: `{ "status": "ok", "database": "ok"|"unavailable" }` — liveness + DB reachability.

## `GET /enc/ranking`

Serve the latest published ENC ranking (default: the roster-derived feature-003 artifact).

- **Query**: `version` (optional — a specific artifact version), `source`
  (`roster`|`power`, default `roster`).
- **200**: `RankingResponse` — 16 ordered teams with score/roster-Elo + confidence, the
  `version`/`as_of`, and `provenance`. Byte-faithful to the artifact (no recomputation).
- **404**: no published ranking (or unknown `version`).
- **503**: read source unavailable.

## `GET /enc/predict`

Live ENC matchup prediction via the feature-003 bridge.

- **Query**: `team_a` (name|vlr-id, required), `team_b` (required), `as_of` (ISO date,
  default now), `aggregation` (`mean`|`topk`, default `mean`).
- **200**: `PredictionResponse` — `p_a`, `p_b` (sum 1.0), `winner`, `low_confidence`, top
  contributors per side, and `provenance` (model run/fingerprint + `as_of`). **Equal to the
  `vctm enc-predict` output for the same inputs.**
- **400**: unknown team or malformed date.
- **503**: database unavailable.

## `GET /enc/evaluation`

Serve the latest published honest evaluation.

- **Query**: `kind` (`bridge`|`winrate`, default `bridge`), `run` (optional run id).
- **200**: `EvaluationResponse` — per-metric model-vs-baseline values, `cutoff`,
  `n_train`/`n_eval`, `leakage_verified`, and `provenance` (run id + window/fingerprint).
- **404**: no published evaluation (or unknown `run`).

## Cross-cutting

- Every success response includes `provenance`; every failure returns `ErrorResponse`
  (`{ "error", "status" }`) with the matching HTTP status (400/404/503) — never a 200 with
  empty/misleading data, never an unhandled 500.
- The service is **read-only**: no route writes to the database, artifacts, or runs.
- Predictions are deterministic and identical to the CLI for the same inputs.
- OpenAPI docs are auto-generated (the schemas are typed).
