# Quickstart & Validation: ENC Prediction API (Phase 4)

Set up, run, and validate the read-only serving layer. Run/validation guide; implementation
lives in `tasks.md` and the code.

## Prerequisites

- Features 001–003 done: data collected, outcomes + sides backfilled, an ENC ranking published
  (`vctm enc-ranking`).
- `cd services/core && uv sync --group api --group ml` (FastAPI/uvicorn/httpx).

## Quality gates (must stay green — Constitution III)

```bash
make lint && make fmt && make test
```

## Run the service

```bash
uv run vctm serve            # or: uv run uvicorn vct_moneyball.api.app:app --reload
# OpenAPI docs at http://127.0.0.1:8000/docs
```

## Scenario 1 — Health

```bash
curl -s localhost:8000/health
```

- **Expected**: `{ "status": "ok", "database": "ok" }` (or `"unavailable"` if the DB is down,
  still a clean 200 — liveness).

## Scenario 2 — Serve the ENC ranking (NON-NEGOTIABLE: byte-faithful, read-only)

```bash
curl -s localhost:8000/enc/ranking | jq '.teams | length, .provenance'
```

- **Expected**: 16 ordered teams + confidence, with `provenance` naming the published artifact
  version. Matches the committed artifact exactly; the request mutates nothing.
- **404** when no ranking is published.

## Scenario 3 — Predict an ENC matchup (CLI parity)

```bash
curl -s "localhost:8000/enc/predict?team_a=United%20States%20of%20America&team_b=Brazil&as_of=2026-11-08"
```

- **Expected**: `p_a`+`p_b` = 1.0, a winner, `low_confidence`, top contributors, and
  `provenance`. **Identical** to `vctm enc-predict` for the same inputs. Unknown team or bad
  date → **400**; DB down → **503**.

## Scenario 4 — Serve the honest evaluation

```bash
curl -s "localhost:8000/enc/evaluation?kind=bridge" | jq '.model, .baselines'
```

- **Expected**: per-metric model-vs-baseline values, `leakage_verified: true`, and `provenance`
  (run id + window). Unchanged from the published report.

## Done = all gates green

- Ranking + evaluation served byte-faithfully with provenance; predictions match the CLI.
- Invalid/unavailable requests return correct 400/404/503 — never a crash or misleading 200.
- No endpoint mutates any data, artifact, or run.
