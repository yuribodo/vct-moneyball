# Phase 0 Research: ENC 2026 Power Ranking (MVP)

Decisions that resolve the open technical questions for the MVP. Each entry records
the decision, why it was chosen, and the alternatives rejected.

## R1. Scoring model — transparent composite, not learned

**Decision**: Score each player per map as a **deterministic, weighted composite** of
normalized per-map performance metrics (e.g., VLR rating, ACS, KAST, ADR, KD), where
metrics are normalized within the fixed data window and the weights are explicit,
versioned config. Team score = aggregate of its players' per-map scores; per-map
breakdown = the team's score on each map. No model training in the MVP.

**Rationale**: Satisfies Constitution I (regenerable from inputs), II (a deterministic
function of locked data is itself locked), III (unit-testable on fixtures), and IV
(no train/test split means no leakage; honesty comes from baseline comparison). It is
fully explainable — every position traces to players × per-map metric values × weights.

**Alternatives considered**:
- *Learned player rating (Bayesian / regularized APM)*: more sophisticated but opaque
  and heavier; deferred to Phase 2 (winrate predictor) where ML is the point.
- *Team map-winrate only*: ignores the spec's per-player, per-map requirement (FR-002).

## R2. Data window & event scope

**Decision**: Use a fixed recent window of professional play — default **~12 months**
ending at a recorded cutoff date — covering tier-relevant events the ENC players
competed in. The exact window and event filter are stored in `config.py` and recorded
in the ranking artifact, so the window is part of the locked, reproducible inputs.

**Rationale**: Recent play best reflects current form while keeping enough sample per
player/map. Recording the window in the artifact preserves reproducibility (Const. I).

**Alternatives**: All-time history (stale, over-weights past metas); last 3 months
(too sparse per map). Both rejected for the MVP default but trivially re-configurable.

## R3. Insufficient player history — labeled low-confidence baseline (spec Q1 = A)

**Decision**: A player must meet a **minimum-history threshold** (default: played a
minimum number of maps in the window, per map type) to receive a data-driven score.
Below threshold, the player is represented by a **transparent low-confidence baseline**
(e.g., the cohort/role median for that map) and **flagged low-confidence**; any team
score that depends on such players is flagged accordingly. The threshold and baseline
rule are versioned config.

**Rationale**: Directly implements FR-012 / spec clarification A — never invent a
strength the data does not support, and make confidence visible (Const. IV; SC-007).

**Alternatives**: Exclude under-threshold players (drops real roster slots, distorts
teams with new players); hierarchical regional/role model (more coverage but more
modeling — revisited in a later phase).

## R4. Storage & migrations — SQLAlchemy 2.0 Core + Alembic on Postgres 16

**Decision**: Model the schema with SQLAlchemy 2.0 (Core/typed models) and manage DDL
with Alembic versioned migrations against the existing Postgres 16 container. Postgres
is the system of record; the schema is the single source of truth for structure
(Const. I). Provenance columns (`source_url`, `captured_at`) live on collected rows.

**Rationale**: Versioned migrations give reproducible structure; SQLAlchemy gives typed,
testable repositories; both are mainstream and align with the `postgresql-table-design`
guidance (explicit types, constraints, indexes). See `data-model.md` for the schema.

**Alternatives**: Plain SQL migration files + psycopg only (lighter, but more manual
wiring for tests); an ORM-heavy approach (unnecessary for a batch pipeline). Alembic +
Core is the middle ground.

## R5. VLR.gg collection — rate-limited, caching Playwright fetcher

**Decision**: Collect with Playwright through a single fetch layer that (a) caches every
raw HTML response to disk keyed by URL + capture time, (b) rate-limits and backs off,
and (c) prefers cache on re-runs. Parsing is a pure function from cached HTML to
records, tested against committed fixtures. Targets: the 16 ENC teams, their rosters,
and each roster player's matches within the window.

**Rationale**: Respectful scraping (Const. tech constraints), and a cache + pure parser
makes the pipeline reproducible offline and the parser unit-testable (Const. III). The
`playwright-cli` skill informs the browser-automation details.

**Alternatives**: Hitting VLR on every run (disrespectful, non-reproducible); an
unofficial API (availability/stability risk). Cache-first scraping chosen.

## R6. Locked artifact — committed JSON + Markdown, DVC-tracked, append-only

**Decision**: Publish each ranking as a **dated, versioned artifact**: a machine-readable
JSON (validated by a Pydantic schema — see `contracts/`) plus a human-readable Markdown
rendering, written under `artifacts/rankings/enc-2026/<published-at>/`. Artifacts are
append-only and DVC-tracked; a correction is a **new** dated directory that references
the superseded one. Immutability is enforced by process (never overwrite) and review.

**Rationale**: Implements Const. II and FR-006/008 + SC-003/004 — dated, immutable,
reproducible, and publicly visible in the repo.

**Alternatives**: A single mutable file (violates immutability); DB-only output (not
publicly visible as a committed artifact). Rejected.

## R7. Post-tournament evaluation — ordering agreement vs a stated baseline

**Decision**: After ENC concludes, compare the locked predicted order against final
standings using a stated rank-agreement metric (e.g., Spearman's rho and/or Kendall's
tau, plus top-k hit rate), and report it against at least one **baseline** ordering
(e.g., VLR/seed order at lock time). The original artifact is read-only input.

**Rationale**: Const. IV (baseline-relative, honest) and US3/FR-011/SC-006. A stated,
standard metric makes "who was right" objective.

**Alternatives**: Raw accuracy only (no baseline → not honest); bespoke metric (harder
to interpret). Rejected.

## Open items deferred to implementation (data, not design)

These are **factual data to be collected and validated at runtime**, deliberately not
hardcoded into the plan (knowledge cutoff predates ENC 2026 roster/pool finalization):

- The exact list of 16 ENC 2026 national teams and their final rosters.
- The exact competitive map pool in effect at collection time.
- The exact tournament start date used as the lock deadline.

The collection stage validates these (e.g., exactly 16 teams, full map pool) per the
quickstart acceptance checks; they are recorded in the artifact for provenance.
