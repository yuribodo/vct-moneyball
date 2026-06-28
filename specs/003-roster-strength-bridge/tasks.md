---
description: "Task list for ENC Roster-Strength Bridge (Phase 3)"
---

# Tasks: ENC Roster-Strength Bridge (Phase 3)

**Input**: Design documents from `specs/003-roster-strength-bridge/`

**Prerequisites**: features 001 + 002 done; data collected; match outcomes backfilled.

**Tests**: INCLUDED — Constitution III (TDD); leakage/as-of correctness and reproducibility
are tested against fixtures and must fail before implementation.

**Organization**: Grouped by user story. Paths under `services/core/`; source root
`services/core/src/vct_moneyball/`, tests under `services/core/tests/`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no incomplete dependencies)
- **[Story]**: US1, US2, US3 (Setup/Foundational/Polish carry no story label)

---

## Phase 1: Setup

- [X] T001 Create the `bridge/` package (`src/vct_moneyball/bridge/__init__.py`) + repo-root
  `artifacts/models/bridge/` dir
- [X] T002 [P] Register `backfill-sides`, `eval-bridge`, `enc-predict`, `enc-ranking`
  subcommands (args per contracts/cli.md, `--json`) in src/vct_moneyball/cli/main.py

---

## Phase 2: Foundational (Blocking Prerequisites)

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T003 Player-side attribution: map each `player_map_stat` to the match side from the
  parser's `team_abbrev` vs the match's two teams in src/vct_moneyball/bridge/attribution.py
- [X] T004 [P] `vctm backfill-sides`: offline re-parse to populate `player_map_stat.team_id`
  (idempotent; reports attributed vs. unresolved) in src/vct_moneyball/cli/backfill_sides.py
- [X] T005 Leakage-free chronological **player Elo** + form + volume replay in
  src/vct_moneyball/bridge/player_rating.py
- [X] T006 Roster/lineup → team strength as-of (mean/top-k aggregate + confidence) in
  src/vct_moneyball/bridge/strength.py (depends on T005)

**Checkpoint**: sides attributed; player ratings + roster strength computable.

---

## Phase 3: User Story 1 - Confidently predict an ENC matchup (Priority: P1) 🎯 MVP

**Goal**: Two ENC teams + a date → differentiated, calibrated win probabilities from roster
strength.

**Independent Test**: Predict an ENC matchup as of a date; assert differentiated probabilities
(not ~0.5) when rosters are dense, low-confidence when sparse, and no input dated on/after.

### Tests for User Story 1 (write first, ensure they FAIL)

- [X] T007 [P] [US1] Unit test: player Elo + roster strength as-of excludes on/after rows
  (no leakage) + determinism in tests/unit/test_player_rating.py
- [X] T008 [P] [US1] Unit test: roster strength aggregation + low-confidence on sparse rosters
  in tests/unit/test_strength.py
- [X] T009 [P] [US1] Unit test: roster-strength matchup features (diff encoding) +
  differentiated output for unequal rosters in tests/unit/test_bridge_features.py

### Implementation for User Story 1

- [X] T010 [US1] Roster-derived matchup features (Elo/form/volume diffs) in
  src/vct_moneyball/bridge/features.py (depends on T006)
- [X] T011 [US1] Train a calibrated bridge model on club matches (reuse predict/model +
  tracking) and load it in src/vct_moneyball/bridge/model.py (depends on T010)
- [X] T012 [US1] `vctm enc-predict` (resolve ENC teams, as-of roster strength, calibrated
  probabilities + winner + confidence + top contributors) in
  src/vct_moneyball/cli/enc_predict.py (depends on T011)

**Checkpoint**: a confident ENC matchup prediction — demoable MVP.

---

## Phase 4: User Story 2 - Roster-derived ENC ranking (Priority: P1)

**Goal**: Order the 16 ENC teams by roster-derived strength as a dated, immutable artifact.

**Independent Test**: Build the ordering as of the lock date; confirm all 16 placed with
strength + confidence, using only pre-lock data, written immutably.

### Tests for User Story 2 (write first, ensure they FAIL)

- [X] T013 [P] [US2] Integration test: `enc-ranking` places all 16 ENC teams with strength +
  confidence and refuses to overwrite an existing artifact in
  tests/integration/test_enc_ranking.py

### Implementation for User Story 2

- [X] T014 [US2] `vctm enc-ranking` (rank 16 ENC rosters by strength as-of; write dated,
  immutable JSON+MD with contributors, citing the run) in src/vct_moneyball/cli/enc_ranking.py
  (depends on T006)

**Checkpoint**: a roster-derived, immutable 16-team ENC ranking.

---

## Phase 5: User Story 3 - Prove the bridge beats a baseline (Priority: P2)

**Goal**: Leakage-free held-out evaluation on real club matches vs. explicit baselines.

**Independent Test**: Run `eval-bridge` on a cutoff; confirm zero overlap, no straddle,
baselines on identical matches, and a below-baseline bridge reported as a non-result.

### Tests for User Story 3 (write first, ensure they FAIL)

- [X] T015 [P] [US3] Unit test: bridge baselines (pedigree, naive-rating-avg) produce probs on
  the same examples in tests/unit/test_bridge_baselines.py
- [X] T016 [P] [US3] Integration test: `eval-bridge` writes a report validating against
  contracts/bridge-report.schema.json with model + ≥1 baseline + `leakage_verified` in
  tests/integration/test_eval_bridge.py

### Implementation for User Story 3

- [X] T017 [P] [US3] Bridge baselines (roster-tier pedigree + naive player-rating average) in
  src/vct_moneyball/bridge/baselines.py
- [X] T018 [US3] Bridge evaluation (temporal split on club matches, model vs baselines,
  schema-valid report, MLflow run) in src/vct_moneyball/bridge/evaluate.py +
  src/vct_moneyball/cli/eval_bridge.py (depends on T010, T011, T017)

**Checkpoint**: an honest, baseline-relative, traceable bridge evaluation.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T019 [US1] Single-real-match E2E: attribution + roster strengths + prediction from a
  captured fixture, reproducible (quickstart scenario 1) in
  tests/integration/test_single_match_bridge_e2e.py
- [X] T020 [P] Document the new `vctm` commands + bridge workflow in services/core/README.md
- [X] T021 [P] Add Makefile targets `backfill-sides` / `eval-bridge` / `enc-predict` /
  `enc-ranking` in Makefile
- [X] T022 Run the full quickstart.md validation (scenarios 0–4) end-to-end
- [X] T023 Confirm `make lint && make fmt && make test` are green

---

## Dependencies & Execution Order

- **Setup (P1)** → **Foundational (P2: attribution → player Elo → roster strength)** blocks
  all stories.
- **US1 (P3)**: the MVP (features → model → enc-predict).
- **US2 (P4)**: depends on roster strength; produces the immutable ENC ranking.
- **US3 (P5)**: depends on US1 features/model + baselines; the honesty gate.
- **Polish (P6)**: after the desired stories.

### Within each story

- Tests written and failing before implementation (Constitution III).
- Attribution → ratings → strength → features → model → CLI.
- Leakage/as-of correctness verified, not assumed.

### Parallel Opportunities

- Setup: T002.
- Foundational: T004 alongside T005 (distinct files) after T003.
- US1 tests T007–T009 in parallel.
- US3: T015, T017 in parallel.

---

## Implementation Strategy

### MVP First (US1)

1. Setup → 2. Foundational (attribute sides, player Elo, roster strength) → 3. US1 → **STOP &
VALIDATE** the single-real-match prediction (T019) → a confident ENC matchup.

### Incremental Delivery

- US1 → confident ENC matchup (MVP).
- + US2 → a roster-derived, immutable 16-team ENC ranking.
- + US3 → proven honest vs. a baseline on held-out real matches.

---

## Notes

- Never invent strength: unresolved sides and sparse rosters are excluded/flagged, never guessed.
- No roster-derived strength may read data dated on/after its as-of date — verified.
- A bridge that does not beat its baseline is reported as such, not hidden.
- Feature-001/002 artifacts are never modified; new outputs are new dated artifacts.
