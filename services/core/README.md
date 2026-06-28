# vct-moneyball (core)

Python service for the VCT Moneyball draft intelligence system. The MVP is the
**ENC 2026 power ranking** pipeline, exposed through the `vctm` CLI. Managed with
[uv](https://docs.astral.sh/uv/).

## Pipeline layout

```
src/vct_moneyball/
├── config.py     # versioned scoring params (weights, window, thresholds) + config_hash
├── common/       # logging + CLI error/exit helpers
├── collect/      # VLR.gg collection: cache, rate-limited fetcher, parsers, discovery
├── store/        # SQLAlchemy models, repositories (upserts w/ provenance), queries
├── score/        # per-map player composite scoring + normalization
├── rank/         # team aggregation, artifact builder/validator, pre-build gates
├── evaluate/     # post-tournament comparison vs. baseline (metrics, standings)
└── cli/          # `vctm collect | build-ranking | evaluate`
```

## Setup

```bash
make up                                   # start Postgres (docker compose)
cd services/core && uv sync --group scraping --group ml
uv run playwright install chromium        # one-time, for live collection
uv run alembic upgrade head               # migrate the schema
```

## The `vctm` CLI

Every command prints human output + errors to stderr, supports `--json` (machine output
on stdout), and exits non-zero on any validation failure.

### `vctm collect`

Collect the 16 ENC teams, their rosters, and in-window matches into Postgres (caching
raw HTML). The ENC cohort is **runtime data**, supplied via env (not hardcoded):

```bash
# Option A: explicit team URLs
export VCTM_ENC_TEAMS="https://www.vlr.gg/team/1184/fut-esports,...(16 total)"
# Option B: an event page to discover participants
export VCTM_ENC_EVENT_URL="https://www.vlr.gg/event/.../enc-2026"

uv run vctm collect --window-months 12          # add --no-cache to force live
```

Exits non-zero unless exactly 16 ENC teams (each with an active roster) resolve.

### `vctm build-ranking`

Score players per map, aggregate to teams, and write a dated, immutable artifact
(`artifacts/rankings/enc-2026/<version>/ranking.json` + `ranking.md`) plus append-only
`ranking*` rows.

```bash
uv run vctm build-ranking \
  --version enc-2026.v1 \
  --tournament-start 2026-07-10T18:00:00+00:00
```

Gates (writes nothing if any fail): `published_at` must be ≥24h before
`--tournament-start`; exactly 16 teams; every in-pool map covered; the version/output
directory must not already exist (immutable). A correction uses a new `--version` with
`--supersedes <old-version>`.

### `vctm evaluate`

After the tournament, compare a locked ranking to final standings vs. a baseline:

```bash
uv run vctm evaluate --version enc-2026.v1 --standings final.json --baseline vlr-seed
```

`final.json`: `{ "source": "...", "final": [teams...], "baselines": {"vlr-seed": [...]} }`.
Writes `outcome_comparison` rows (Spearman ρ, Kendall τ, top-4 hit rate); the ranking is
read-only.

## Winrate predictor (feature 002)

A match-outcome model learned from the collected history; predicts calibrated win
probabilities, evaluated only on held-out **future** matches vs. an explicit baseline,
with runs tracked in MLflow (`mlruns/`, git-ignored). See
`specs/002-winrate-predictor/`.

```bash
uv run alembic upgrade head            # adds match outcome columns
uv run vctm backfill-results           # offline: derive winners from cached HTML
uv run vctm eval-winrate --cutoff 2026-04-01 \
  --baseline winrate-elo --baseline coin     # train<cutoff, eval>=cutoff, vs baselines
uv run vctm train-winrate --cutoff 2026-11-08 # train + log an MLflow run
uv run vctm predict-match --team-a "United States of America" --team-b "Brazil" \
  --as-of 2026-11-08                          # calibrated win probabilities
```

Reports land in `artifacts/models/winrate/<run>/` (JSON validated against
`contracts/eval-report.schema.json` + Markdown). Features are **leakage-free** (each
match's signals use only data dated before it; the temporal split is verified) and a
model that does not beat its baseline is reported as such.

## Quality gates (Constitution III)

```bash
make lint     # ruff check
make fmt      # ruff format
make test     # pytest (unit + integration on fixtures; integration skips if no DB)
```
