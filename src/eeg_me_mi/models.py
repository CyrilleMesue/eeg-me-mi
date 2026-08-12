"""Model constructors for Milestone 1 (Dummy + L2 logistic regression)."""

from __future__ import annotations

from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


def make_dummy_pipeline(strategy: str = "prior") -> Pipeline:
    """Negative comparator using a prespecified DummyClassifier strategy."""
    return Pipeline(
        steps=[
            ("clf", DummyClassifier(strategy=strategy)),
        ]
    )


def make_erd_lr_pipeline(seed: int = 2026) -> Pipeline:
    """Primary E01/E00 model: StandardScaler + L2 logistic regression.

    Scaling is a pipeline step so it is fitted on training folds only.
    No SelectKBest / supervised feature selection in the primary model.
    """
    return Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            (
                "clf",
                LogisticRegression(
                    solver="lbfgs",
                    max_iter=2000,
                    class_weight="balanced",
                    random_state=seed,
                ),
            ),
        ]
    )


def logistic_param_grid(c_grid: tuple[float, ...]) -> dict:
    return {"clf__C": list(c_grid)}
