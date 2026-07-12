"""Train + calibrate the winrate model and predict matchup probabilities.

MVP learner: standardized, L2-regularized logistic regression wrapped in probability
calibration (research R1). A gradient-boosted alternative is available behind the same
interface. The calibration method (sigmoid vs isotonic) is chosen by an internal,
leakage-free temporal validation split rather than hardcoded per learner — research R1
calls for it to be "chosen by validation", and a fixed mapping does not honor that
(issue #8: shipped calibration was measurably worse than the Elo baseline's). Predictions
below a minimum-history threshold are flagged low-confidence (FR-007).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from vct_moneyball.predict.evaluate import calibration_error
from vct_moneyball.predict.features import FEATURE_NAMES, FeatureConfig, MatchExample

MIN_HISTORY = 5  # min prior matches per side for a confident prediction

# Below this many training examples, an 80/20 internal validation split is too noisy to
# trust for picking a calibration method — fall back to the default mapping instead.
_MIN_EXAMPLES_FOR_SELECTION = 100

_DEFAULT_METHOD = {"logreg": "sigmoid", "gbt": "isotonic"}


@dataclass
class WinrateModel:
    estimator: Any
    feature_names: tuple[str, ...]
    learner: str
    calibration_method: str

    def predict_proba_a(self, features: dict[str, float]) -> float:
        """P(team_a wins) for a single feature vector."""
        x = [[features[name] for name in self.feature_names]]
        return float(self.estimator.predict_proba(x)[0][1])

    def predict_block(self, examples: list) -> list[float]:
        x = [[ex.features[name] for name in self.feature_names] for ex in examples]
        return [float(p[1]) for p in self.estimator.predict_proba(x)]


def _base_estimator(learner: str):
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    if learner == "gbt":
        from sklearn.ensemble import GradientBoostingClassifier

        return GradientBoostingClassifier(random_state=0)
    return make_pipeline(StandardScaler(), LogisticRegression(C=1.0, max_iter=1000))


def _build_estimator(learner: str, method: str):
    from sklearn.calibration import CalibratedClassifierCV

    return CalibratedClassifierCV(_base_estimator(learner), method=method, cv=3)


def _select_calibration_method(examples: list[MatchExample], learner: str) -> str:
    """Pick sigmoid vs isotonic by fitting both on an early slice, scoring ECE on a
    later, held-out slice — a leakage-free proxy for "chosen by validation" (R1)."""
    if len(examples) < _MIN_EXAMPLES_FOR_SELECTION:
        return _DEFAULT_METHOD[learner]

    ordered = sorted(examples, key=lambda e: e.played_at)
    split = int(len(ordered) * 0.8)
    fit_part, val_part = ordered[:split], ordered[split:]
    x_fit = [[e.features[name] for name in FEATURE_NAMES] for e in fit_part]
    y_fit = [e.label for e in fit_part]
    if len(set(y_fit)) < 2 or not val_part:
        return _DEFAULT_METHOD[learner]
    x_val = [[e.features[name] for name in FEATURE_NAMES] for e in val_part]
    y_val = [e.label for e in val_part]

    best_method, best_ece = _DEFAULT_METHOD[learner], None
    for method in ("sigmoid", "isotonic"):
        estimator = _build_estimator(learner, method)
        estimator.fit(x_fit, y_fit)
        probs = [float(p[1]) for p in estimator.predict_proba(x_val)]
        ece = calibration_error(y_val, probs)
        if best_ece is None or ece < best_ece:
            best_method, best_ece = method, ece
    return best_method


def train(
    examples: list[MatchExample],
    *,
    learner: str = "logreg",
    calibration_method: str | None = None,
) -> WinrateModel:
    """Fit the calibrated model on a list of training examples."""
    if not examples:
        raise ValueError("no training examples")
    x = [[ex.features[name] for name in FEATURE_NAMES] for ex in examples]
    y = [ex.label for ex in examples]
    if len(set(y)) < 2:
        raise ValueError("training data has a single class; cannot fit a classifier")
    method = calibration_method or _select_calibration_method(examples, learner)
    estimator = _build_estimator(learner, method)
    estimator.fit(x, y)
    return WinrateModel(
        estimator=estimator,
        feature_names=FEATURE_NAMES,
        learner=learner,
        calibration_method=method,
    )


def is_low_confidence(min_volume: int, threshold: int = MIN_HISTORY) -> bool:
    return min_volume < threshold


# Re-exported so callers can reference the feature config without importing two modules.
__all__ = ["WinrateModel", "train", "is_low_confidence", "MIN_HISTORY", "FeatureConfig"]
