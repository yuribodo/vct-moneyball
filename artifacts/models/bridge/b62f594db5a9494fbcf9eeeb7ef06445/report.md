# Roster-Strength Bridge Evaluation

- Run: `b62f594db5a9494fbcf9eeeb7ef06445`  ·  aggregation: `mean`
- Cutoff: `2026-04-01T00:00:00+00:00`  ·  Train/Eval: 663/456
- Attribution coverage: 99.5%  ·  leakage verified: True

| Predictor | log-loss | accuracy | Brier |
|-----------|---------:|---------:|------:|
| **bridge** | 0.6485 | 0.6184 | 0.2287 |
| winrate-elo | 0.6656 | 0.6162 | 0.2364 |
| coin | 0.6931 | 0.4781 | 0.2500 |

The roster-strength bridge **beats** its best baseline (`winrate-elo`) on log-loss.
