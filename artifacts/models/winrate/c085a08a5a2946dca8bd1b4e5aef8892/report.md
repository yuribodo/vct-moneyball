# Winrate Model Evaluation

- Run: `c085a08a5a2946dca8bd1b4e5aef8892`  ·  Learner: `logreg`  ·  Calibration: `sigmoid`
- Cutoff: `2026-04-01T00:00:00+00:00`  ·  Train/Eval: 665/461
- Data window: `2025-07-03T17:15:00+00:00` → `2026-06-25T18:00:00+00:00`
- Feature fingerprint: `2fd8bdac36b88f6d`  ·  leakage verified: True

| Predictor | log-loss | accuracy | Brier | calib. err |
|-----------|---------:|---------:|------:|-----------:|
| **model** | 0.6629 | 0.6204 | 0.2351 | 0.0554 |
| winrate-elo | 0.6693 | 0.6052 | 0.2382 | 0.0406 |
| coin | 0.6931 | 0.4751 | 0.2500 | 0.0249 |

On log-loss, the model **beats** its best baseline (`winrate-elo`).
