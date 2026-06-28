# Implementation Plan: ENC Prediction API (Phase 4)

**Branch**: `004-prediction-api` | **Date**: 2026-06-28 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/004-prediction-api/spec.md`

## Summary

A thin, read-only HTTP service over the existing pipeline. It serves the latest published ENC
ranking (read from the committed artifact on disk), answers live ENC matchup predictions
(delegating to the feature-003 roster-strength bridge), and exposes the honest evaluation
results (from the published reports). It introduces no new modeling and no data collection;
it is a transport layer whose predictions are **identical to the CLI** for the same inputs,
carry provenance, flag low confidence, and mutate nothing.

## Technical Context

**Language/Version**: Python 3.12 (uv, `services/core/`).

**Primary Dependencies**: FastAPI + Uvicorn (already in the `api` group) for the service;
Pydantic for response schemas; httpx (test client) added to the `api` group. Reuses
feature-001/002/003 code (bridge, predict, rank) and SQLAlchemy for reads.

**Storage**: Reads only — PostgreSQL (rosters/matches) for live predictions and the committed
`artifacts/` files (rankings, eval reports). No writes.

**Testing**: pytest with FastAPI's `TestClient` (httpx) — fully headless, no running server
needed; integration tests seed the isolated `<db>_test` and assert endpoint responses + CLI
parity.

**Target Platform**: Linux (local dev + Docker). `uvicorn` for local serving; no public
deployment in scope.

**Project Type**: Single Python project under `services/core/` (adds an API surface to the
existing CLI).

**Performance Goals**: Typical ranking/prediction requests under 1 second (the bridge trains
inline on ~1k matches in well under a second; ranking reads a small file).

**Constraints**: Strictly read-only (no endpoint mutates data/artifacts/runs); responses carry
provenance (artifact version or run id + window/fingerprint); CLI-parity for predictions;
clear status codes for invalid/unavailable requests; deterministic + reproducible.

**Scale/Scope**: A handful of read endpoints; 16 ENC teams; local/trusted use (no auth/rate
limiting in the MVP).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Status |
|-----------|------|--------|
| I. Reproducible Data Provenance | Serves provenance-bearing artifacts unchanged; predictions are deterministic functions of versioned inputs; responses carry the source artifact/run. | ✅ |
| II. Falsifiable, Locked Predictions | Locked artifacts are served **byte-faithfully** and never mutated; the API does not republish or alter them. | ✅ Read-only (FR-001/FR-006). |
| III. Test-First & E2E Validation | TDD with `TestClient`; CLI-parity and read-only behavior tested; one real end-to-end request validated. | ✅ |
| IV. Honest Model Evaluation | Exposes the honest, baseline-relative evaluation results unchanged; low-confidence flags preserved in responses. | ✅ FR-003/FR-004. |

**Result**: PASS — no violations. Complexity Tracking left empty.

## Project Structure

### Documentation (this feature)

```text
specs/004-prediction-api/
├── plan.md          # This file
├── research.md      # Phase 0 output
├── data-model.md    # Phase 1 output
├── quickstart.md    # Phase 1 output
├── contracts/       # Phase 1 output (endpoint + response schemas)
└── tasks.md         # Phase 2 output (/speckit-tasks — not created here)
```

### Source Code (repository root)

```text
services/core/
├── src/vct_moneyball/
│   └── api/                         # NEW — the read-only serving layer
│       ├── app.py                   # FastAPI app factory + exception handlers
│       ├── schemas.py               # Pydantic response models
│       ├── deps.py                  # DB session + settings dependencies
│       ├── artifacts.py             # locate + load latest published ranking/eval (read-only)
│       └── routes/
│           ├── health.py            # GET /health
│           ├── ranking.py           # GET /enc/ranking
│           ├── predict.py           # GET /enc/predict
│           └── evaluation.py        # GET /enc/evaluation
└── tests/
    ├── unit/                        # artifact discovery, schema mapping
    └── integration/                 # TestClient endpoint tests + CLI parity
```

**Structure Decision**: Add an `api/` package that composes the existing layers — it reads
the latest published artifacts from disk for rankings/evaluations and calls the feature-003
bridge for live predictions. A `vctm serve` CLI (or `uvicorn` invocation) runs it. The
service holds no business logic of its own beyond transport, validation, and provenance
shaping, so CLI-parity is structural.

## Complexity Tracking

> No constitution violations — nothing to justify.
