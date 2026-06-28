# web — ENC 2026 demo (feature 005)

A small Next.js (App Router) site that consumes the read-only prediction API
(feature 004) and presents the project's story: the ENC power ranking, a live
matchup predictor, and the honest "who was right" evaluation.

## Run

```bash
# 1) start the API (from the repo root)
make serve                       # http://127.0.0.1:8000

# 2) start the web demo
cd web
cp .env.example .env.local       # set NEXT_PUBLIC_API_BASE if the API isn't on :8000
npm install
npm run dev                      # http://localhost:3000
```

## Pages

- `/` — the 16-team ENC power ranking (strength + confidence + provenance).
- `/predict` — pick two teams + a date → calibrated win probabilities, winner, top
  contributors, and a low-confidence note when applicable.
- `/honesty` — the model vs. its baseline on held-out matches (leakage verified).

## Gates

```bash
npm run build        # production build must succeed
npm run typecheck    # tsc --noEmit
```

The site adds no business logic — it only reads and renders the API, preserving its
confidence flags and "model vs. baseline" honesty. Visual/interaction QA is a human step
in a browser.
