# Quickstart & Validation: ENC 2026 Power Ranking (MVP)

How to set up, run, and validate that the feature works end-to-end. This is a
run/validation guide — implementation detail lives in `tasks.md` and the code.

## Prerequisites

- `uv` and Docker installed (see repo README).
- Postgres running: `make up`.
- Python deps: `cd services/core && uv sync --group scraping --group ml`.
- Playwright browser installed (one-time): `uv run playwright install chromium`.
- Schema migrated: `uv run alembic upgrade head`.

## Quality gates (must stay green — Constitution III)

```bash
make lint     # ruff check
make fmt      # ruff format
make test     # pytest (unit + integration on fixtures, offline)
```

## Validation scenario 1 — Single real match, end-to-end (NON-NEGOTIABLE gate)

Prove the whole chain on one real VLR.gg match before scaling (Const. III).

1. Capture one real match page into the fixture cache (records `source_url` +
   `captured_at`).
2. Parse it offline and assert: each map in the match yields one `player_map_stat`
   row per player, all with provenance populated.
3. **Expected**: parsed counts match what the match page shows; re-running parse on the
   cached HTML gives byte-identical structured output (determinism).

## Validation scenario 2 — Collect the ENC cohort

```bash
uv run vctm collect --window-months 12
```

- **Expected**: summary reports exactly **16 ENC teams**, each with ≥1 active roster
  player, the full in-pool map set present, and non-zero `player_map_stat` rows. Re-run
  with `--use-cache` completes offline and reports the same counts (reproducibility,
  SC-004).
- **Failure** is non-zero exit if teams ≠ 16 or the source is unreachable with no cache.

## Validation scenario 3 — Build the locked ranking

```bash
uv run vctm build-ranking \
  --version enc-2026.v1 \
  --tournament-start <ENC_START_TIMESTAMP>
```

- **Expected**: writes `artifacts/rankings/enc-2026/<published-at>/ranking.json`
  (validates against `contracts/ranking-artifact.schema.json`) + `ranking.md`, and the
  16-team ordered table prints. Checks enforced (SC-001/002/003/005/007):
  - exactly 16 teams in strict positions 1..16;
  - every in-pool map appears in each team's `map_breakdown`;
  - `published_at` is at least 1 full day (24h) before `--tournament-start`;
  - each team lists `contributors` explaining its score;
  - players below the history threshold are flagged `low` / `low_history_baseline`.
- **Immutability**: re-running with the same `--version` or an existing output dir
  **fails without overwriting** (Const. II). A correction uses a new `--version` and
  `--supersedes enc-2026.v1`.

## Validation scenario 4 — Post-tournament evaluation (after ENC)

```bash
uv run vctm evaluate \
  --version enc-2026.v1 \
  --standings <FINAL_STANDINGS> \
  --baseline vlr-seed
```

- **Expected**: prints predicted vs baseline values for each metric (Spearman's rho,
  Kendall's tau, top-4 hit rate) and writes `outcome_comparison` rows. The locked
  ranking is read unchanged (SC-006).

## Done = all gates green

- Scenario 1 (single real match) passes and is reproducible.
- `collect` resolves exactly 16 teams with full provenance and is cache-reproducible.
- `build-ranking` produces a schema-valid, dated, immutable artifact that meets every
  Success Criterion; immutability is enforced.
- `evaluate` produces a baseline-relative accuracy report without mutating the ranking.
