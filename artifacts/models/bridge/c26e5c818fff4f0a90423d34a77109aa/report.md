# Roster-Strength Bridge Evaluation

- Run: `c26e5c818fff4f0a90423d34a77109aa`  ·  aggregation: `mean`
- Cutoff: `2026-04-01T00:00:00+00:00`  ·  Train/Eval: 663/456
- Attribution coverage: 99.5%  ·  leakage verified: True

| Predictor | log-loss | accuracy | Brier |
|-----------|---------:|---------:|------:|
| **bridge** | 0.6497 | 0.6162 | 0.2293 |
| winrate-elo | 0.6701 | 0.6118 | 0.2386 |
| coin | 0.6931 | 0.4781 | 0.2500 |

The roster-strength bridge **beats** its best baseline (`winrate-elo`) on log-loss.
