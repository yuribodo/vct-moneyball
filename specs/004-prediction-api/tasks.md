---
description: "Task list for ENC Prediction API (Phase 4)"
---

# Tasks: ENC Prediction API (Phase 4)

**Input**: Design documents from `specs/004-prediction-api/`

**Prerequisites**: features 001–003 done; an ENC ranking published (`vctm enc-ranking`).

**Tests**: INCLUDED — Constitution III; endpoint behavior, CLI-parity, and error/read-only
guarantees are tested headless (FastAPI TestClient) and must fail before implementation.

**Organization**: Grouped by user story. Paths under `services/core/`; source root
`services/core/src/vct_moneyball/`, tests under `services/core/tests/`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no incomplete dependencies)
- **[Story]**: US1, US2, US3 (Setup/Foundational/Polish carry no story label)

---

## Phase 1: Setup

- [X] T001 Add `httpx>=0.27` to the `api` dependency group and create the `api/` package
  (`src/vct_moneyball/api/__init__.py`, `api/routes/__init__.py`) in services/core/pyproject.toml
- [X] T002 [P] Register a `serve` subcommand (host/port/reload) in src/vct_moneyball/cli/main.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T003 [P] Pydantic response schemas (Provenance, RankingResponse, PredictionResponse,
  EvaluationResponse, ErrorResponse) in src/vct_moneyball/api/schemas.py
- [X] T004 Read-only DB session + settings dependencies in src/vct_moneyball/api/deps.py
- [X] T005 Artifact discovery/loading (latest published ranking + eval reports, read-only) in
  src/vct_moneyball/api/artifacts.py
- [X] T006 FastAPI app factory + exception handlers (map errors to 400/404/503 ErrorResponse)
  in src/vct_moneyball/api/app.py (depends on T003, T004)

**Checkpoint**: app boots; schemas + read sources + error model ready.

---

## Phase 3: User Story 1 - Read the ENC rankings over the network (Priority: P1) 🎯 MVP

**Goal**: Serve the published 16-team ENC ranking byte-faithfully with provenance.

**Independent Test**: GET /enc/ranking returns 16 ordered teams + confidence + provenance,
matching the committed artifact; 404 when none is published.

### Tests for User Story 1 (write first, ensure they FAIL)

- [X] T007 [P] [US1] Integration test: GET /enc/ranking returns 16 teams + provenance and 404
  when absent, via TestClient in tests/integration/test_api_ranking.py

### Implementation for User Story 1

- [X] T008 [US1] GET /enc/ranking route (read latest artifact, map to RankingResponse) in
  src/vct_moneyball/api/routes/ranking.py (depends on T005, T006)

**Checkpoint**: the ENC ranking is consumable over HTTP — demoable MVP.

---

## Phase 4: User Story 2 - Predict an ENC matchup over the network (Priority: P1)

**Goal**: Live ENC matchup prediction equal to the CLI, with confidence + contributors.

**Independent Test**: GET /enc/predict returns probabilities summing to 1.0, a winner,
confidence, contributors — identical to `vctm enc-predict`; 400 on bad input.

### Tests for User Story 2 (write first, ensure they FAIL)

- [X] T009 [P] [US2] Integration test: GET /enc/predict CLI-parity + low-confidence flag +
  400 on unknown team/bad date in tests/integration/test_api_predict.py

### Implementation for User Story 2

- [X] T010 [US2] GET /enc/predict route (delegate to the feature-003 bridge) in
  src/vct_moneyball/api/routes/predict.py (depends on T006)

**Checkpoint**: live ENC predictions over HTTP, matching the CLI.

---

## Phase 5: User Story 3 - Read the honest evaluation (Priority: P2)

**Goal**: Serve the published evaluation (model vs. baseline) with run provenance.

**Independent Test**: GET /enc/evaluation returns per-metric model-vs-baseline values +
run id + window; 404 when none.

### Tests for User Story 3 (write first, ensure they FAIL)

- [X] T011 [P] [US3] Integration test: GET /enc/evaluation returns metrics + baselines +
  provenance, 404 when absent in tests/integration/test_api_evaluation.py

### Implementation for User Story 3

- [X] T012 [US3] GET /enc/evaluation route (read latest report) in
  src/vct_moneyball/api/routes/evaluation.py (depends on T005, T006)

**Checkpoint**: the honest evaluation is consumable over HTTP.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T013 [P] GET /health (liveness + DB reachability) in src/vct_moneyball/api/routes/health.py
- [X] T014 [P] Read-only guarantee test (no endpoint mutates data) + error-model test (400/404/
  503 shapes) in tests/integration/test_api_contract.py
- [X] T015 [US1] `vctm serve` runs the app via uvicorn in src/vct_moneyball/cli/serve.py
- [X] T016 [P] Document the API + run flow in services/core/README.md and add a Makefile `serve`
  target in Makefile
- [X] T017 Confirm `make lint && make fmt && make test` are green

---

## Dependencies & Execution Order

- **Setup (P1)** → **Foundational (P2: schemas, deps, artifacts, app)** blocks all stories.
- **US1 (P3)**: the MVP (serve the ranking).
- **US2 (P4)**: live predict (CLI-parity via the bridge).
- **US3 (P5)**: serve the evaluation.
- **Polish (P6)**: health, contract guarantees, serve CLI, docs.

### Parallel Opportunities

- Setup: T002. Foundational: T003 alongside T004/T005 (distinct files).
- Story tests T007, T009, T011 in parallel; routes are independent files.

---

## Implementation Strategy

### MVP First (US1)

1. Setup → 2. Foundational → 3. US1 → a served ENC ranking over HTTP.

### Incremental Delivery

- US1 → ranking endpoint (MVP). + US2 → live predictions. + US3 → honest evaluation.

---

## Notes

- Read-only: no route writes to the DB, artifacts, or runs (verified).
- Predictions are deterministic and identical to the CLI for the same inputs.
- Every response carries provenance; failures use honest status codes, never a misleading 200.
