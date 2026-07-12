# Roster-Strength Bridge Evaluation

- Run: `b8d55f95485a414dbdfd72f15e70f653`  ·  aggregation: `mean`  ·  calibration: `sigmoid`
- Cutoff: `2026-04-01T00:00:00+00:00`  ·  Train/Eval: 663/456
- Attribution coverage: 99.5%  ·  leakage verified: True

| Predictor | log-loss | accuracy | Brier | calib. err |
|-----------|---------:|---------:|------:|-----------:|
| **bridge** | 0.6497 | 0.6162 | 0.2293 | 0.0777 |
| winrate-elo | 0.6701 | 0.6118 | 0.2386 | 0.0462 |
| coin | 0.6931 | 0.4781 | 0.2500 | 0.0219 |

The roster-strength bridge **beats** its best baseline (`winrate-elo`) on log-loss.
