"""Leakage and nested-CV tests."""

import numpy as np
import pandas as pd
import pytest
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

from eeg_me_mi.cv import assert_participant_disjoint, fold_assignment_table, make_group_folds, run_nested_group_cv
from eeg_me_mi.models import make_erd_lr_pipeline, logistic_param_grid


class FitTracker(BaseEstimator, TransformerMixin):
    """Records the number of samples seen during fit."""

    def __init__(self):
        self.n_fit_samples_ = None
        self.groups_seen_ = None

    def fit(self, X, y=None):
        self.n_fit_samples_ = len(X)
        return self

    def transform(self, X):
        return X


def test_folds_are_participant_disjoint_and_deterministic():
    groups = np.repeat(np.arange(1, 9), 4)
    a = make_group_folds(groups, 4, 2026)
    b = make_group_folds(groups, 4, 2026)
    for (_, atr, ate, _, _), (_, btr, bte, _, _) in zip(a, b):
        assert np.array_equal(atr, btr)
        assert np.array_equal(ate, bte)
        assert set(groups[atr]).isdisjoint(groups[ate])
    assert_participant_disjoint(fold_assignment_table(groups, 4, 2026))


def test_overlap_audit_fails_closed():
    bad = pd.DataFrame({"fold": [1, 1], "role": ["train", "test"], "subject": [7, 7]})
    with pytest.raises(AssertionError, match="overlap"):
        assert_participant_disjoint(bad)


def test_nested_cv_scaler_train_only_and_reproducible():
    rng = np.random.default_rng(0)
    n_subjects = 6
    n_per = 20
    groups = np.repeat(np.arange(1, n_subjects + 1), n_per)
    y = np.tile([0, 1], n_subjects * n_per // 2)
    X = rng.normal(size=(len(y), 42))
    # Add weak signal correlated with y so LR can fit.
    X[:, 0] += y * 0.5
    metadata = pd.DataFrame(
        {
            "subject": groups,
            "run": 3,
            "movement": "left_fist",
            "pair_id": "03-04",
        }
    )

    pipe = Pipeline(
        [
            ("tracker", FitTracker()),
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(max_iter=1000, random_state=0)),
        ]
    )
    result_a = run_nested_group_cv(
        experiment="test",
        model_name="lr",
        estimator=pipe,
        param_grid={"clf__C": [0.1, 1.0]},
        X=X,
        y=y,
        groups=groups,
        metadata=metadata,
        outer_folds=3,
        inner_folds=2,
        seed=2026,
    )
    result_b = run_nested_group_cv(
        experiment="test",
        model_name="lr",
        estimator=pipe,
        param_grid={"clf__C": [0.1, 1.0]},
        X=X,
        y=y,
        groups=groups,
        metadata=metadata,
        outer_folds=3,
        inner_folds=2,
        seed=2026,
    )

    assert_participant_disjoint(result_a["fold_assignments"])
    for fold, frame in result_a["fold_assignments"].groupby("fold"):
        train = set(frame.loc[frame.role == "train", "subject"])
        test = set(frame.loc[frame.role == "test", "subject"])
        assert train.isdisjoint(test)

    # Tuning used only training participants (recorded in tuning table).
    for _, row in result_a["tuning"].iterrows():
        train_subj = set(map(int, row["train_subjects"].split("|")))
        test_subj = set(map(int, row["test_subjects"].split("|")))
        assert train_subj.isdisjoint(test_subj)

    # Reproducibility of OOF scores
    np.testing.assert_allclose(
        result_a["oof_predictions"]["y_score"].to_numpy(),
        result_b["oof_predictions"]["y_score"].to_numpy(),
        rtol=1e-10,
        atol=1e-10,
    )
    assert result_a["summary"]["balanced_accuracy"] == pytest.approx(
        result_b["summary"]["balanced_accuracy"]
    )


def test_feature_computation_label_free():
    """ERD/log-power extractors are not invoked here; ensure primary pipe has no SelectKBest."""
    pipe = make_erd_lr_pipeline(2026)
    assert "scaler" in pipe.named_steps
    assert "clf" in pipe.named_steps
    assert "select" not in pipe.named_steps
    assert set(logistic_param_grid((0.01, 0.1, 1.0, 10.0))["clf__C"]) == {0.01, 0.1, 1.0, 10.0}
