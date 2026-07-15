# Winrate Model Evaluation

- Run: `554b0d772e6d4e32852bc3694cfd6a7b`  ·  Learner: `logreg`  ·  Calibration: `sigmoid`
- Cutoff: `2026-07-01T00:00:00+00:00`  ·  Train/Eval: 1226/70
- Data window: `2025-07-06T17:00:00+00:00` → `2026-07-12T16:00:00+00:00`
- Feature fingerprint: `2fd8bdac36b88f6d`  ·  leakage verified: True

| Predictor | log-loss | accuracy | Brier | calib. err |
|-----------|---------:|---------:|------:|-----------:|
| **model** | 0.6442 | 0.6429 | 0.2259 | 0.0973 |
| winrate-elo | 0.6680 | 0.6000 | 0.2371 | 0.1031 |
| recent-form | 0.6923 | 0.5714 | 0.2492 | 0.1342 |
| coin | 0.6931 | 0.4000 | 0.2500 | 0.1000 |

On log-loss, the model **beats** its best baseline (`winrate-elo`).
