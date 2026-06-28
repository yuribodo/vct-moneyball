<!--
SYNC IMPACT REPORT
Version change: (template) → 1.0.0
Bump rationale: Initial ratification of the project constitution.
Principles defined:
  I.   Reproducible Data Provenance (NON-NEGOTIABLE)
  II.  Falsifiable, Locked Predictions
  III. Test-First & End-to-End Validation (NON-NEGOTIABLE)
  IV.  Honest Model Evaluation
Sections added:
  - Technology & Data Constraints
  - Development Workflow & Quality Gates
  - Governance
Removed sections: none (initial version)
Templates reviewed:
  ✅ .specify/templates/plan-template.md — generic Constitution Check gate; compatible
  ✅ .specify/templates/spec-template.md — no constitution-specific edits required
  ✅ .specify/templates/tasks-template.md — task categories cover data/test/eval work
Follow-up TODOs: none
-->

# VCT Moneyball Constitution

Quantitative draft intelligence for Valorant pro play. The project's value rests
entirely on the credibility of its data and predictions: "when it's over, the data
shows who was right." These principles exist to protect that credibility.

## Core Principles

### I. Reproducible Data Provenance (NON-NEGOTIABLE)

Every dataset and model artifact MUST be reproducible from versioned sources.

- All input data MUST trace to a recorded VLR.gg source (URL + capture timestamp);
  raw scraped HTML MUST be cached so a scrape can be replayed without re-hitting the site.
- Datasets and model artifacts MUST be tracked with DVC once real data exists; the
  Postgres schema and its migrations are the single source of truth for structure.
- Data MUST NOT be hand-edited. Any correction is a code or pipeline change, committed
  and re-runnable. A dataset that cannot be regenerated from versioned inputs does not exist.

Rationale: a Moneyball claim is only as trustworthy as the chain from raw evidence to
prediction. If that chain cannot be replayed, the conclusion cannot be defended.

### II. Falsifiable, Locked Predictions

Public predictions MUST be timestamped and frozen before the event they predict.

- A published ranking or forecast (e.g., the ENC 2026 power ranking) MUST be committed
  as a dated, immutable artifact before the relevant matches are played.
- A locked prediction MUST NOT be retroactively edited, deleted, or quietly re-tuned.
  Revisions are new, separately dated artifacts that cite what they supersede.
- Outcomes MUST be scored against the original locked artifact, and the result —
  right or wrong — MUST be reported.

Rationale: the project exists to settle "feel vs. data" honestly. A prediction that can
be changed after kickoff proves nothing.

### III. Test-First & End-to-End Validation (NON-NEGOTIABLE)

Behavior MUST be specified by tests before it is implemented, and proven on real data.

- Features and bug fixes follow TDD with pytest: write a failing test, then implement to
  green, then refactor. Scrapers and pipelines MUST have tests against captured fixtures.
- Before any component is scaled (more teams, more matches, more maps), it MUST be
  validated end-to-end on at least one real VLR.gg match.
- `make lint` (ruff check) and `make test` (pytest) MUST pass before work is merged;
  `make fmt` (ruff format) defines formatting.

Rationale: a scraper or model that is "probably right" silently corrupts every downstream
prediction. One verified real case beats a hundred untested assumptions.

### IV. Honest Model Evaluation

Model claims MUST be earned on data the model has never seen.

- Evaluation MUST use temporally-correct splits (held-out future matches); there MUST be
  no leakage of post-match information into features.
- Every model MUST be compared against an explicit baseline; a model that does not beat its
  baseline is reported as such, not shipped as a result.
- Training runs, metrics, parameters, and artifacts MUST be tracked (MLflow) so any reported
  number is traceable to the exact run that produced it.

Rationale: in sports prediction it is trivially easy to fool yourself with leakage or a
cherry-picked split. Honest, baseline-relative, tracked evaluation is the only defense.

## Technology & Data Constraints

- **Language & deps:** Python 3.12 managed by `uv` in `services/core/`. Optional dependency
  groups (`scraping`, `ml`, `dl`, `api`) are pulled on demand, not installed by default.
- **Storage:** PostgreSQL 16 (via docker compose) is the system of record for matches, maps,
  players, and per-map stats. Data versioning via DVC.
- **Collection:** VLR.gg via Playwright. Scraping MUST be respectful — cache raw responses,
  avoid unnecessary repeat requests, and never depend on hammering the source.
- **ML/Serving:** pandas + scikit-learn, XGBoost/LightGBM, PyTorch (embeddings), MLflow
  (tracking/registry), FastAPI (serving), Next.js (Phase 3 demo).
- Adding a new core technology MUST be justified against an existing capability before adoption.

## Development Workflow & Quality Gates

- Work is spec-driven via Spec Kit: `/speckit-specify` → `/speckit-plan` → `/speckit-tasks`
  → `/speckit-implement`, with `/speckit-clarify` and `/speckit-analyze` used to de-risk
  ambiguous features before implementation.
- Delivery follows the README phases: MVP ENC power ranking first, then the winrate
  predictor, then the full system. Complexity is added when a phase requires it, not before.
- Quality gates before merge: `make lint`, `make fmt`, and `make test` all green; new
  data-touching code carries fixtures and tests per Principle III.

## Governance

This constitution supersedes ad-hoc practice. When a decision conflicts with these
principles, the principle wins unless the constitution is formally amended first.

- **Amendments** MUST be made by editing this file with a Sync Impact Report, a version
  bump, and propagation to any affected templates and guidance docs.
- **Versioning** follows semantic rules: MAJOR for principle removals/redefinitions, MINOR
  for added or materially expanded principles/sections, PATCH for clarifications and wording.
- **Compliance:** every plan and review MUST verify alignment with these principles;
  deviations MUST be explicitly justified in the relevant spec or plan, or the work changes.

**Version**: 1.0.0 | **Ratified**: 2026-06-27 | **Last Amended**: 2026-06-27
