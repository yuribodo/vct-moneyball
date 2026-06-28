# vct-moneyball (core)

Python service: scraping, data, features, models, and API for the VCT Moneyball
draft intelligence system. Managed with [uv](https://docs.astral.sh/uv/).

## Layout

```
src/vct_moneyball/
├── scraping/   # VLR.gg collection (Playwright)
├── data/       # DB models & persistence
├── features/   # feature engineering
├── models/     # ML (player score, winrate predictor, embeddings)
└── api/        # FastAPI app
```

## Common tasks

```bash
uv sync                      # install base + dev deps
uv sync --group scraping     # add Playwright
uv sync --group ml           # add pandas/sklearn/xgboost/lightgbm
uv run pytest                # tests
uv run ruff check .          # lint
uv run ruff format .         # format
```
