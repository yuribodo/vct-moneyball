---
description: "Task list for Match Winrate Predictor (Phase 2)"
---

# Tasks: Match Winrate Predictor (Phase 2)

**Input**: Design documents from `specs/002-winrate-predictor/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md;
feature 001 collected data present (cached HTML available).

**Tests**: INCLUDED — Constitution III (TDD) is non-negotiable; leakage/split correctness
and feature determinism are tested against fixtures and must fail before implementation.

**Organization**: Grouped by user story. Paths under `services/core/`; source root
`services/core/src/vct_moneyball/`, tests under `services/core/tests/`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no incomplete dependencies)
- **[Story]**: US1, US2, US3 (Setup/Foundational/Polish carry no story label)

---

## Phase 1: Setup

- [ ] T001 Add `mlflow>=2.14` to the `ml` dependency group and create the `predict/` package
  (`src/vct_moneyball/predict/__init__.py`) + repo-root `artifacts/models/winrate/` in
  services/core/pyproject.toml
- [ ] T002 [P] Register `backfill-results`, `train-winrate`, `eval-winrate`, `predict-match`
  subcommands (args per contracts/cli.md, `--json`) in src/vct_moneyball/cli/main.py
- [ ] T003 [P] Ignore `mlruns/` (MLflow local store) in repo .gitignore

---

## Phase 2: Foundational (Blocking Prerequisites)

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [ ] T004 Add match identity/outcome columns (`team_a_id`, `team_b_id`, `winner_team_id`,
  `score_a`, `score_b` + indexes) to the `Match` model in src/vct_moneyball/store/models.py
- [ ] T005 Generate the Alembic migration for the new `match` columns in
  services/core/alembic/versions/
- [ ] T006 [US-prep] Extend the VLR match parser to read both teams (`vlr_team_id`), series
  score, and winner from the match header in src/vct_moneyball/collect/parse.py
- [ ] T007 Repository upserts for the match outcome + a `team` row per side (clubs,
  `is_enc_2026=false`, with provenance) in src/vct_moneyball/store/repositories.py
- [ ] T008 [P] `vctm backfill-results`: offline re-parse of cached HTML to populate match
  outcomes (idempotent; reports labeled vs. unlabeled) in src/vct_moneyball/cli/backfill_results.py
- [ ] T009 [P] MLflow run wrapper + dataset/feature/config fingerprint in
  src/vct_moneyball/predict/tracking.py

**Checkpoint**: outcomes can be backfilled; schema + tracking ready.

---

## Phase 3: User Story 1 - Predict a match (Priority: P1) 🎯 MVP

**Goal**: From two teams + a date, produce calibrated win probabilities using only
pre-match data.

**Independent Test**: Train to a cutoff, predict a held-out future match; assert two
probabilities summing to 1.0 and that no feature read on/after the match date.

### Tests for User Story 1 (write first, ensure they FAIL)

- [ ] T010 [P] [US1] Unit test: outcome label (team_a win) from stored result in
  tests/unit/test_labels.py
- [ ] T011 [P] [US1] Unit test: as-of feature builder excludes any row dated on/after the
  match (no leakage) + determinism in tests/unit/test_features.py
- [ ] T012 [P] [US1] Unit test: train→calibrate→predict_proba returns probabilities summing
  to 1.0; low-history flag set in tests/unit/test_model.py

### Implementation for User Story 1

- [ ] T013 [P] [US1] Match outcome labels in src/vct_moneyball/predict/labels.py (depends on T007)
- [ ] T014 [US1] Leakage-free as-of opponent-difference feature builder in
  src/vct_moneyball/predict/features.py (reuses score/player + config)
- [ ] T015 [US1] Calibrated model (regularized logreg + `CalibratedClassifierCV`),
  `predict_proba`, low-confidence flagging in src/vct_moneyball/predict/model.py (depends on T014)
- [ ] T016 [US1] `vctm train-winrate` (train before cutoff, log MLflow run + artifact) in
  src/vct_moneyball/cli/train_winrate.py (depends on T015, T009)
- [ ] T017 [US1] `vctm predict-match` (resolve teams, as-of features, probabilities + winner +
  confidence) in src/vct_moneyball/cli/predict_match.py (depends on T015)

**Checkpoint**: a trained model predicts a single matchup — demoable MVP.

---

## Phase 4: User Story 2 - Prove the model is honest (Priority: P1)

**Goal**: Temporally-correct held-out evaluation vs. explicit baselines, schema-valid +
traceable report.

**Independent Test**: Run `eval-winrate` on a cutoff; confirm zero train/eval overlap, no
match straddles the split, baselines scored on identical matches, and a below-baseline model
reported as a non-result.

### Tests for User Story 2 (write first, ensure they FAIL)

- [ ] T018 [P] [US2] Unit test: temporal split has zero overlap, no match straddles cutoff,
  `leakage_verified` true in tests/unit/test_dataset.py
- [ ] T019 [P] [US2] Unit test: metrics (log-loss, accuracy, Brier, calibration) + baselines
  in tests/unit/test_eval_metrics.py
- [ ] T020 [P] [US2] Integration test: `eval-winrate` writes a report validating against
  contracts/eval-report.schema.json with model + ≥1 baseline in
  tests/integration/test_eval_winrate.py

### Implementation for User Story 2

- [ ] T021 [US2] Temporal split + atomic-match + leakage verification in
  src/vct_moneyball/predict/dataset.py (depends on T014)
- [ ] T022 [P] [US2] Explicit baselines (roster-tier pedigree, power-rank favorite,
  win-rate/Elo) in src/vct_moneyball/predict/baselines.py
- [ ] T023 [P] [US2] Evaluation metrics (log-loss, accuracy, Brier, calibration error) in
  src/vct_moneyball/predict/evaluate.py
- [ ] T024 [US2] `vctm eval-winrate` (forward-chaining split, model vs. baselines, write
  schema-valid JSON+MD report, log to MLflow, underpowered warning) in
  src/vct_moneyball/cli/eval_winrate.py (depends on T021, T022, T023)

**Checkpoint**: an honest, baseline-relative, traceable evaluation report builds.

---

## Phase 5: User Story 3 - Trace every number to its run (Priority: P2)

**Goal**: Each reported metric recoverable from a stored run (data window, fingerprint,
params, baseline).

**Independent Test**: Two trainings with different params produce two distinguishable,
retrievable runs each carrying full lineage.

### Tests for User Story 3 (write first, ensure they FAIL)

- [ ] T025 [P] [US3] Integration test: a completed run records data window, feature/config
  fingerprint, params, baseline, and all metrics; two param sets are distinguishable in
  tests/integration/test_run_traceability.py

### Implementation for User Story 3

- [ ] T026 [US3] Ensure train/eval log params + data window + dataset/feature fingerprint +
  metrics + model artifact + report path to MLflow, and the report embeds run id + fingerprint
  in src/vct_moneyball/predict/tracking.py + cli/eval_winrate.py (depends on T024)

**Checkpoint**: every reported number is traceable.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [ ] T027 [US1] Single-real-match E2E: label + as-of features + prediction from a captured
  fixture, reproducible (quickstart scenario 1) in tests/integration/test_single_match_pred_e2e.py
- [ ] T028 [P] Document the new `vctm` commands + model workflow in services/core/README.md
- [ ] T029 [P] Add Makefile targets `backfill-results` / `train-winrate` / `eval-winrate` /
  `predict-match` in Makefile
- [ ] T030 Run the full quickstart.md validation (scenarios 0–4) end-to-end
- [ ] T031 Confirm `make lint && make fmt && make test` are green

---

## Dependencies & Execution Order

- **Setup (P1)** → **Foundational (P2)** blocks all stories.
- **US1 (P3)**: the MVP (label → features → model → predict).
- **US2 (P4)**: depends on Foundational + US1's feature/model; adds split/baselines/eval.
- **US3 (P5)**: cross-cutting on tracking; depends on US2's eval.
- **Polish (P6)**: after the desired stories.

### Within each story

- Tests written and failing before implementation (Constitution III).
- Models → repositories → services → CLI command.
- Leakage/split correctness verified, not assumed.

### Parallel Opportunities

- Setup: T002, T003.
- Foundational: T008, T009 (after T004–T007).
- US1 tests T010–T012 in parallel; impl T013 parallel to T014 start.
- US2 tests T018–T020; impl T022, T023 in parallel.

---

## Implementation Strategy

### MVP First (US1)

1. Setup → 2. Foundational (backfill labels) → 3. US1 → **STOP & VALIDATE** the
single-real-match prediction (T027) → a model that predicts a matchup.

### Incremental Delivery

- US1 → predicts a matchup (MVP).
- + US2 → the prediction is now proven honest vs. a baseline on a leakage-free split.
- + US3 → every reported number is traceable (publish-ready).

---

## Notes

- Do not invent outcomes: matches with no parseable result stay unlabeled and excluded
  (logged), never guessed.
- No feature may read data dated on/after its match — verified in the dataset builder and
  unit tests.
- A model that does not beat its baseline is reported as such, not hidden.
