"""Model constructors: Dummy, ERD-LR, CSP-LDA, Riemannian tangent LR."""

from __future__ import annotations

from mne.decoding import CSP
from pyriemann.estimation import Covariances
from pyriemann.tangentspace import TangentSpace
from sklearn.base import BaseEstimator, TransformerMixin, clone
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


class EpochCrop(BaseEstimator, TransformerMixin):
    """Crop 3D epoch arrays (n, ch, time) to a sample index range."""

    def __init__(self, start: int = 0, stop: int | None = None):
        self.start = start
        self.stop = stop

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        return X[:, :, self.start : self.stop]


def make_dummy_pipeline(strategy: str = "prior") -> Pipeline:
    return Pipeline(steps=[("clf", DummyClassifier(strategy=strategy))])


def make_erd_lr_pipeline(seed: int = 2026) -> Pipeline:
    """Primary confirmatory model: StandardScaler + L2 LR (no SelectKBest)."""
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


def make_csp_lda_pipeline(
    *,
    n_components: int = 4,
    reg: float | None = 0.01,
    log: bool = True,
) -> Pipeline:
    """CSP + shrinkage LDA.

    Prespecified small parameterization (no large CSP search).
    CSP is a pipeline step → fitted on training folds only.
    Expects X shaped (n_epochs, n_channels, n_times) on the task window.
    """
    return Pipeline(
        steps=[
            (
                "csp",
                CSP(
                    n_components=n_components,
                    reg=reg,
                    log=log,
                    norm_trace=False,
                ),
            ),
            (
                "lda",
                LinearDiscriminantAnalysis(solver="lsqr", shrinkage="auto"),
            ),
        ]
    )


def make_riemann_lr_pipeline(seed: int = 2026) -> Pipeline:
    """Ledoit-Wolf / scm-style covariance → tangent space → L2 LR.

    Uses pyRiemann:
    - Covariances(estimator='lwf') — Ledoit-Wolf shrinkage covariance
    - TangentSpace(metric='riemann') — reference fitted on training covs only
    - LogisticRegression — regularized linear classifier in tangent space

    Expects X shaped (n_epochs, n_channels, n_times).
    """
    return Pipeline(
        steps=[
            ("cov", Covariances(estimator="lwf")),
            ("ts", TangentSpace(metric="riemann")),
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


def clone_estimator(est):
    return clone(est)
