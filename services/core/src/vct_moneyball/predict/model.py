"""Train + calibrate the winrate model and predict matchup probabilities.

MVP learner: standardized, L2-regularized logistic regression wrapped in probability
calibration (research R1). A gradient-boosted alternative is available behind the same
interface. Predictions below a minimum-history threshold are flagged low-confidence (FR-007).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from vct_moneyball.predict.features import FEATURE_NAMES, FeatureConfig, MatchExample

MIN_HISTORY = 5  # min prior matches per side for a confident prediction


@dataclass
class WinrateModel:
    estimator: Any
    feature_names: tuple[str, ...]
    learner: str

    def predict_proba_a(self, features: dict[str, float]) -> float:
        """P(team_a wins) for a single feature vector."""
        x = [[features[name] for name in self.feature_names]]
        return float(self.estimator.predict_proba(x)[0][1])

    def predict_block(self, examples: list) -> list[float]:
        x = [[ex.features[name] for name in self.feature_names] for ex in examples]
        return [float(p[1]) for p in self.estimator.predict_proba(x)]


def _build_estimator(learner: str):
    from sklearn.calibration import CalibratedClassifierCV
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    if learner == "gbt":
        from sklearn.ensemble import GradientBoostingClassifier

        base = GradientBoostingClassifier(random_state=0)
        return CalibratedClassifierCV(base, method="isotonic", cv=3)
    # default: standardized, regularized logistic regression
    from sklearn.linear_model import LogisticRegression

    pipe = make_pipeline(StandardScaler(), LogisticRegression(C=1.0, max_iter=1000))
    return CalibratedClassifierCV(pipe, method="sigmoid", cv=3)


def train(examples: list[MatchExample], *, learner: str = "logreg") -> WinrateModel:
    """Fit the calibrated model on a list of training examples."""
    if not examples:
        raise ValueError("no training examples")
    x = [[ex.features[name] for name in FEATURE_NAMES] for ex in examples]
    y = [ex.label for ex in examples]
    if len(set(y)) < 2:
        raise ValueError("training data has a single class; cannot fit a classifier")
    estimator = _build_estimator(learner)
    estimator.fit(x, y)
    return WinrateModel(estimator=estimator, feature_names=FEATURE_NAMES, learner=learner)


def is_low_confidence(min_volume: int, threshold: int = MIN_HISTORY) -> bool:
    return min_volume < threshold


# Re-exported so callers can reference the feature config without importing two modules.
__all__ = ["WinrateModel", "train", "is_low_confidence", "MIN_HISTORY", "FeatureConfig"]
