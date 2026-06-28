---
description: "Task list for ENC 2026 Power Ranking (MVP)"
---

# Tasks: ENC 2026 Power Ranking (MVP)

**Input**: Design documents from `specs/001-enc-power-ranking/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: INCLUDED — Constitution III makes TDD with pytest non-negotiable; scraper /
pipeline tests run against captured fixtures and must fail before implementation.

**Organization**: Grouped by user story. All paths are under `services/core/` unless
noted. Source root is `services/core/src/vct_moneyball/`; tests under `services/core/tests/`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: US1, US2, US3 (Setup/Foundational/Polish carry no story label)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and structure

- [X] T001 Create source/test tree per plan (`src/vct_moneyball/{collect,store,score,rank,evaluate,cli}`, `tests/{unit,integration,fixtures}`, `alembic/`, and repo-root `artifacts/rankings/enc-2026/`) under services/core/
- [X] T002 Initialize uv project with dependency groups (base: sqlalchemy, psycopg[binary], alembic, pydantic; scraping: playwright; ml: pandas, numpy, scipy; dev: pytest, ruff) in services/core/pyproject.toml
- [X] T003 [P] Configure ruff lint + format rules in services/core/pyproject.toml
- [X] T004 [P] Configure pytest (testpaths, markers `unit`/`integration`) in services/core/pyproject.toml
- [X] T005 [P] Initialize DVC and track `artifacts/` + raw HTML cache dir at repo root (.dvc/, .dvcignore)
- [X] T006 Verify Postgres connectivity from `.env` `DATABASE_URL` via `make up` (Postgres 16 container)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Schema, config, persistence, and CLI scaffold shared by all stories

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T007 Implement versioned scoring/config params (data-window months, cutoff, metric weights, min-history threshold, confidence cutoffs, `config_hash`) in src/vct_moneyball/config.py
- [X] T008 Implement SQLAlchemy 2.0 engine/session factory (psycopg driver) in src/vct_moneyball/store/db.py
- [X] T009 Initialize Alembic (alembic.ini, env.py wired to `DATABASE_URL`) in services/core/alembic/
- [X] T010 Define all SQLAlchemy models (team, player, team_player, map, match, match_map, player_map_stat, ranking, ranking_entry, ranking_map_breakdown, outcome_comparison) with provenance columns, constraints, and indexes per data-model.md in src/vct_moneyball/store/models.py
- [X] T011 Generate initial Alembic migration creating the full schema (UNIQUE/CHECK/FK constraints + indexes) in services/core/alembic/versions/
- [X] T012 [P] Implement `vctm` CLI skeleton (collect/build-ranking/evaluate subcommands, `--json`, stderr+non-zero exit convention) in src/vct_moneyball/cli/main.py
- [X] T013 [P] Implement logging + error/exit helpers in src/vct_moneyball/common/logging.py

**Checkpoint**: Schema migrated, config + DB + CLI scaffold ready — stories can begin.

---

## Phase 3: User Story 1 - Read the ENC team power ranking (Priority: P1) 🎯 MVP

**Goal**: Produce a ranking artifact of the 16 ENC teams in strict order, each with a
per-map breakdown and per-player contributors that explain its position.

**Independent Test**: Run `vctm collect` then `vctm build-ranking` on fixture data; open
the artifact and confirm 16 ordered teams, full per-map breakdown, and visible
contributors (spec SC-001/002/005).

### Tests for User Story 1 (write first, ensure they FAIL)

- [X] T014 [P] [US1] Unit test: per-map player composite scoring (normalization + weights + low-history baseline) in tests/unit/test_score.py
- [X] T015 [P] [US1] Unit test: team aggregation, strict 1..16 ordering, and tie-break in tests/unit/test_rank.py
- [X] T016 [P] [US1] Unit test: VLR parser turns fixture HTML into `player_map_stat` records with provenance in tests/unit/test_parse.py
- [X] T017 [P] [US1] Integration test: `build-ranking` on fixtures yields a schema-valid artifact (16 teams, full map breakdown, contributors) validated against contracts/ranking-artifact.schema.json in tests/integration/test_build_ranking.py

### Implementation for User Story 1

- [X] T018 [P] [US1] Raw HTML cache (write/read keyed by URL + captured_at) in src/vct_moneyball/collect/cache.py
- [X] T019 [US1] Rate-limited, cache-first Playwright fetcher in src/vct_moneyball/collect/client.py (depends on T018)
- [X] T020 [P] [US1] VLR parsers (team, roster, match, per-map stats) in src/vct_moneyball/collect/parse.py
- [X] T021 [US1] ENC team/roster + in-window match discovery in src/vct_moneyball/collect/targets.py (depends on T019, T020)
- [X] T022 [US1] Upsert repositories writing provenance for collected rows in src/vct_moneyball/store/repositories.py (depends on T010)
- [X] T023 [US1] `vctm collect` command (validates exactly 16 ENC teams) in src/vct_moneyball/cli/collect.py (depends on T021, T022)
- [X] T024 [P] [US1] Per-map player scoring + window normalization + labeled low-confidence baseline in src/vct_moneyball/score/player.py (depends on T007)
- [X] T025 [US1] Team aggregation, per-map breakdown, tie-break, confidence rollup in src/vct_moneyball/rank/aggregate.py (depends on T024)
- [X] T026 [US1] Ranking artifact builder (JSON validated vs schema + Markdown render) in src/vct_moneyball/rank/artifact.py (depends on T025)
- [X] T027 [US1] `vctm build-ranking` command writing artifact + `ranking*` rows in src/vct_moneyball/cli/build_ranking.py (depends on T026)
- [X] T028 [US1] Capture one real match fixture and validate the full chain end-to-end (quickstart scenario 1) in tests/fixtures/ + tests/integration/test_single_match_e2e.py

**Checkpoint**: A ranking artifact builds from data and is independently testable — MVP.

---

## Phase 4: User Story 2 - Trust the prediction was locked before kickoff (Priority: P1)

**Goal**: Guarantee the artifact is dated before kickoff, immutable, and reproducible
from versioned inputs.

**Independent Test**: Attempt to build with `published_at >= tournament_start` (rejected,
nothing written); attempt to overwrite an existing version (rejected); rebuild offline
from cache and get identical output (spec SC-003/004, FR-006/008/009).

### Tests for User Story 2 (write first, ensure they FAIL)

- [X] T029 [P] [US2] Integration test: `build-ranking` exits non-zero and writes nothing when `published_at` is within 24h of (or after) `tournament_start` in tests/integration/test_lock_deadline.py
- [X] T030 [P] [US2] Integration test: refusing to overwrite an existing version/dir; `--supersedes` creates a new artifact referencing the original in tests/integration/test_immutability.py
- [X] T031 [P] [US2] Integration test: provenance completeness for every referenced row + deterministic offline cache rebuild in tests/integration/test_provenance_repro.py

### Implementation for User Story 2

- [X] T032 [US2] Enforce lock-deadline gate (`published_at` ≤ `tournament_start` − 24h) in src/vct_moneyball/cli/build_ranking.py
- [X] T033 [US2] Immutability guard (never overwrite output dir/`ranking.version`; append-only) + `--supersedes` linkage in src/vct_moneyball/rank/artifact.py
- [X] T034 [US2] Pre-build provenance validation gate (fail if any referenced row lacks `source_url`/`captured_at`) in src/vct_moneyball/rank/validate.py
- [X] T035 [US2] Record `config_hash` + data window in artifact and confirm `--use-cache` offline rebuild path in src/vct_moneyball/rank/artifact.py + src/vct_moneyball/collect/client.py

**Checkpoint**: The artifact is provably locked, dated, immutable, and reproducible.

---

## Phase 5: User Story 3 - Settle the bet after the tournament (Priority: P2)

**Goal**: Compare a locked ranking against final standings using stated metrics vs a
baseline, without mutating the ranking.

**Independent Test**: Run `vctm evaluate` against a locked ranking + sample standings;
confirm per-metric predicted vs baseline values and `outcome_comparison` rows, with the
ranking untouched (spec SC-006, FR-011).

### Tests for User Story 3 (write first, ensure they FAIL)

- [X] T036 [P] [US3] Unit test: rank-agreement metrics (Spearman's rho, Kendall's tau, top-k hit rate) in tests/unit/test_metrics.py
- [X] T037 [P] [US3] Integration test: `evaluate` writes `outcome_comparison`, reports vs baseline, leaves the ranking unchanged in tests/integration/test_evaluate.py

### Implementation for User Story 3

- [X] T038 [P] [US3] Final-standings loader/validator in src/vct_moneyball/evaluate/standings.py
- [X] T039 [P] [US3] Rank-agreement metrics in src/vct_moneyball/evaluate/metrics.py
- [X] T040 [US3] Comparison service (predicted vs baseline, write `outcome_comparison`) in src/vct_moneyball/evaluate/compare.py (depends on T038, T039)
- [X] T041 [US3] `vctm evaluate` command in src/vct_moneyball/cli/evaluate.py (depends on T040)

**Checkpoint**: All three stories independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T042 [P] Document the `vctm` commands and run flow in services/core/README.md
- [X] T043 [P] Add Makefile targets `collect` / `build-ranking` / `evaluate` in Makefile
- [X] T044 Run the full quickstart.md validation (all 4 scenarios) end-to-end
- [X] T045 [P] Consistency pass on exit codes, stderr messages, and low-confidence flagging across CLI commands
- [X] T046 Confirm `make lint && make fmt && make test` are green

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: no dependencies — start immediately.
- **Foundational (Phase 2)**: depends on Setup — BLOCKS all user stories.
- **US1 (Phase 3)**: depends on Foundational. The MVP.
- **US2 (Phase 4)**: depends on Foundational; builds on the US1 `build-ranking` path
  (US2 hardens the same command with lock/immutability/provenance gates).
- **US3 (Phase 5)**: depends on Foundational; independent of US1/US2 internals (consumes
  a locked ranking + external standings).
- **Polish (Phase 6)**: after the desired stories are complete.

### Within Each Story

- Tests written and failing before implementation (Constitution III).
- Models → repositories → services → CLI command.
- US1 core (`build-ranking`) before US2 gates that wrap it.

### Parallel Opportunities

- Setup: T003, T004, T005 in parallel.
- Foundational: T012, T013 in parallel (after T010/T011 land for models/migration).
- US1 tests T014–T017 in parallel; impl T018, T020, T024 in parallel (distinct files).
- US2 tests T029–T031 in parallel.
- US3 tests T036–T037 and impl T038–T039 in parallel.

---

## Parallel Example: User Story 1

```bash
# Tests first (parallel — distinct files):
Task: "Unit test per-map scoring in tests/unit/test_score.py"
Task: "Unit test aggregation/ordering in tests/unit/test_rank.py"
Task: "Unit test VLR parser in tests/unit/test_parse.py"
Task: "Integration test build-ranking artifact in tests/integration/test_build_ranking.py"

# Then independent implementation files in parallel:
Task: "Raw HTML cache in src/vct_moneyball/collect/cache.py"
Task: "VLR parsers in src/vct_moneyball/collect/parse.py"
Task: "Per-map player scoring in src/vct_moneyball/score/player.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 only)

1. Phase 1 Setup → 2. Phase 2 Foundational → 3. Phase 3 US1 →
4. **STOP and VALIDATE** the single-real-match E2E (T028) and the artifact →
5. This is a demoable MVP: a ranking of the 16 teams with per-map breakdown.

### Incremental Delivery

- US1 → testable ranking artifact (MVP).
- + US2 → the artifact is now provably locked/dated/reproducible (publish-ready).
- + US3 → post-tournament scoring closes the Moneyball loop.

---

## Notes

- [P] = different files, no incomplete dependencies.
- US1 + US2 are both P1: ship US1 to produce the ranking, then US2 before publishing so
  the artifact carries its lock/immutability/provenance guarantees.
- Do not hardcode the 16 teams, map pool, or tournament date — collect/validate them at
  runtime (research.md "Open items") and record them in the artifact.
- Verify tests fail before implementing; commit after each task or logical group.
