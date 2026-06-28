# VCT Moneyball — Draft Intelligence System

Quantitative analysis of Valorant pro play: scrape VLR.gg, model players per map,
predict draft win probability, and suggest the optimal 5th player for a roster.
First real application: ranking the 16 ENC 2026 national teams before the
tournament in Riyadh (November). When it's over, the data shows who was right.

> Coaches still build rosters by feel. Billy Beane stopped doing that in 2002.

## Status

Bootstrapping. This repo currently holds the project skeleton and tooling — no
collection or modeling logic yet.

## Stack

- **Collection & storage:** Playwright (VLR.gg), PostgreSQL, DVC (data versioning)
- **ML:** pandas + scikit-learn, XGBoost/LightGBM (winrate predictor), PyTorch
  (player embeddings), MLflow (tracking & registry)
- **Serving:** FastAPI, Docker, Evidently (drift monitoring)
- **Demo:** Next.js (Phase 3)

## Layout

```
vct-moneyball/
├── docker-compose.yml      # Postgres 16
├── Makefile                # make up / setup / lint / fmt / test
├── services/core/          # Python service (uv) — see services/core/README.md
└── web/                    # Next.js demo (Phase 3, placeholder)
```

## Prerequisites

- [uv](https://docs.astral.sh/uv/) (manages Python 3.12 + deps)
- Docker (for Postgres)

## Quickstart

```bash
cp .env.example .env        # adjust if needed
make up                     # start Postgres
make setup                  # install Python deps (base + dev)
make test                   # smoke test
```

Optional dependency groups are declared but not installed by default; pull them
on demand from `services/core/`:

```bash
cd services/core
uv sync --group scraping    # Playwright
uv sync --group ml          # pandas, scikit-learn, xgboost, lightgbm
uv sync --group dl          # torch
uv sync --group api         # fastapi, uvicorn
```

## Phases

1. **MVP — ENC Power Ranking:** scrapper, data pipeline, player score model,
   public ranking of the 16 ENC teams with per-map breakdown. Published before
   the tournament.
2. **Winrate Predictor:** feature engineering, XGBoost/LightGBM training, MLflow
   tracking, evaluation on held-out historical matches.
3. **Full system:** player embeddings, 5th-player suggester, roster optimizer,
   public API, and the interactive Next.js demo with drift monitoring.

## Next steps

- Model the Postgres schema (matches, maps, players, per-map stats).
- Build the VLR.gg scrapper and validate one real match end to end.
- Initialize DVC once real data exists.
