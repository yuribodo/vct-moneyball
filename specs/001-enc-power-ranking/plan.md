# Implementation Plan: ENC 2026 Power Ranking (MVP)

**Branch**: `001-enc-power-ranking` | **Date**: 2026-06-27 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/001-enc-power-ranking/spec.md`

## Summary

Build a reproducible pipeline that collects professional Valorant match data from
VLR.gg, scores each rostered player's per-map performance over a fixed recent window,
aggregates those scores into a team strength score with a per-map breakdown, and
publishes a dated, immutable power ranking of the 16 ENC 2026 national teams before
the Riyadh tournament. The MVP scoring model is a **transparent, deterministic
composite** of per-map performance metrics (no trained ML model) so every position is
explainable and the whole ranking is regenerable from versioned inputs. A separate,
post-tournament step compares the locked ranking against actual results.

## Technical Context

**Language/Version**: Python 3.12 (managed by `uv`, in `services/core/`)

**Primary Dependencies**: Playwright (VLR.gg collection), pandas + numpy (scoring &
normalization), SQLAlchemy 2.0 Core + Alembic (storage & migrations), psycopg 3
(Postgres driver), Pydantic (artifact schema validation), DVC (dataset/artifact
versioning). FastAPI/PyTorch/XGBoost are **not** used in this MVP (later phases).

**Storage**: PostgreSQL 16 (docker compose) — system of record for teams, players,
maps, matches, and per-map stats. Raw scraped HTML cached on disk and tracked by DVC.
Published ranking artifact is a committed JSON file (+ rendered Markdown).

**Testing**: pytest (unit + integration), with captured VLR.gg HTML fixtures so
scraper/pipeline tests run offline and deterministically. ruff for lint/format.

**Target Platform**: Linux (local dev + Docker); no server runtime for MVP (batch
pipeline + CLI).

**Project Type**: Single-project data pipeline + CLI (under `services/core/`).

**Performance Goals**: Not latency-sensitive. A full rebuild from cached raw data MUST
complete offline in minutes. A full fresh collection respects VLR.gg with rate limits;
total scope is small (see below), so a fresh run completing within a couple of hours
is acceptable.

**Constraints**: Respectful collection (cache raw responses, rate-limit, never hammer
the source); fully reproducible from versioned inputs (offline rebuild); every data
point carries source URL + capture time; published ranking immutable once dated.

**Scale/Scope**: 16 teams, ~80 players, the current competitive map pool (~7 maps), and
on the order of 1k–5k professional matches inside the data window.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Gate | Status |
|-----------|------|--------|
| I. Reproducible Data Provenance | Every stored data point carries `source_url` + `captured_at`; raw HTML cached and DVC-tracked; ranking regenerable offline from versioned inputs; no hand-edited data. | ✅ Design satisfies (provenance columns in schema; raw cache + DVC; deterministic rebuild in quickstart). |
| II. Falsifiable, Locked Predictions | Ranking published as a dated, immutable artifact ≥1 day before tournament start; corrections are new dated artifacts citing the original. | ✅ `ranking` artifact is append-only + versioned; immutability enforced by process (committed file + DVC) and documented. |
| III. Test-First & E2E Validation | TDD with pytest; scraper/pipeline tested against captured fixtures; one real match validated end-to-end before scaling; `make lint`/`make test` green. | ✅ Fixtures-based tests planned; quickstart includes the single-real-match E2E gate. |
| IV. Honest Model Evaluation | No leakage; compare against an explicit baseline; parameters traceable. | ✅ MVP score is deterministic (no learned model → no train/test leakage); scoring parameters (window, weights, threshold) versioned in config; post-tournament comparison runs against a stated baseline. MLflow deferred to Phase 2 (no training in MVP). |

**Result**: PASS — no violations. Complexity Tracking left empty.

## Project Structure

### Documentation (this feature)

```text
specs/001-enc-power-ranking/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (CLI + artifact schemas)
└── tasks.md             # Phase 2 output (/speckit-tasks — not created here)
```

### Source Code (repository root)

```text
services/core/
├── pyproject.toml                 # uv project + dependency groups
├── alembic/                       # schema migrations (versioned DDL)
│   └── versions/
├── src/vct_moneyball/
│   ├── config.py                  # data window, weights, min-history threshold (versioned params)
│   ├── common/                    # logging + error/exit helpers (shared)
│   ├── collect/                   # VLR.gg collection (Playwright) + raw HTML cache
│   │   ├── client.py              # rate-limited, caching fetcher
│   │   ├── parse.py               # HTML → structured records
│   │   └── targets.py             # ENC team/roster + match discovery
│   ├── store/                     # SQLAlchemy models, repositories, provenance
│   ├── score/                     # per-map player scoring + normalization
│   ├── rank/                      # team aggregation, tie-breaking, artifact builder
│   ├── evaluate/                  # post-tournament comparison vs baseline
│   └── cli/                       # `vctm collect | build-ranking | evaluate`
└── tests/
    ├── unit/                      # scoring, aggregation, parsing (pure)
    ├── integration/               # DB + pipeline against fixtures
    └── fixtures/                  # captured VLR.gg HTML (offline, deterministic)

artifacts/
└── rankings/
    └── enc-2026/                  # published, dated ranking files (JSON + Markdown), DVC-tracked
```

**Structure Decision**: Single Python project under `services/core/` (matches the
existing repo layout and Makefile). The pipeline is organized as a thin set of stages
— collect → store → score → rank → evaluate — each independently testable, exposed
through a `vctm` CLI. Published artifacts live in a top-level `artifacts/` directory so
the locked rankings are visible in the repo and versioned by DVC, separate from code.

## Complexity Tracking

> No constitution violations — nothing to justify.
