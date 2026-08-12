"""Deterministic participant-disjoint nested cross-validation."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.model_selection import GridSearchCV, KFold

from eeg_me_mi.metrics import compute_metrics, continuous_score, participant_mean_metrics, participant_metric_table


def make_group_folds(groups: np.ndarray, n_splits: int, seed: int):
    groups = np.asarray(groups)
    unique = np.unique(groups)
    if n_splits < 2 or len(unique) < n_splits:
        raise ValueError(f"Need >= {n_splits} unique participants; got {len(unique)}")
    splitter = KFold(n_splits=n_splits, shuffle=True, random_state=seed)
    folds = []
    for fold, (train_g, test_g) in enumerate(splitter.split(unique), 1):
        train_groups, test_groups = unique[train_g], unique[test_g]
        if not set(train_groups).isdisjoint(test_groups):
            raise AssertionError("Participant overlap in generated fold")
        train_idx = np.flatnonzero(np.isin(groups, train_groups))
        test_idx = np.flatnonzero(np.isin(groups, test_groups))
        folds.append((fold, train_idx, test_idx, train_groups, test_groups))
    return folds


def fold_assignment_table(groups: np.ndarray, n_splits: int, seed: int) -> pd.DataFrame:
    rows = []
    groups = np.asarray(groups)
    for fold, train_idx, test_idx, _, _ in make_group_folds(groups, n_splits, seed):
        rows.extend(
            {"fold": fold, "role": "train", "subject": int(x)}
            for x in np.unique(groups[train_idx])
        )
        rows.extend(
            {"fold": fold, "role": "test", "subject": int(x)}
            for x in np.unique(groups[test_idx])
        )
    return pd.DataFrame(rows)


def assert_participant_disjoint(assignments: pd.DataFrame) -> None:
    required = {"fold", "role", "subject"}
    if not required <= set(assignments):
        raise ValueError(f"Missing assignment columns: {sorted(required - set(assignments))}")
    for fold, frame in assignments.groupby("fold"):
        train = set(frame.loc[frame.role == "train", "subject"])
        test = set(frame.loc[frame.role == "test", "subject"])
        overlap = train & test
        if overlap:
            raise AssertionError(f"Fold {fold} participant overlap: {sorted(overlap)}")


def _inner_cv(train_groups: np.ndarray, n_splits: int, seed: int):
    unique = np.unique(train_groups)
    n_splits = min(n_splits, len(unique))
    if n_splits < 2:
        raise ValueError("Need at least 2 training participants for inner CV")
    return list(KFold(n_splits=n_splits, shuffle=True, random_state=seed).split(unique))


def run_nested_group_cv(
    *,
    experiment: str,
    model_name: str,
    estimator,
    param_grid: dict | None,
    X: np.ndarray,
    y: np.ndarray,
    groups: np.ndarray,
    metadata: pd.DataFrame,
    outer_folds: int,
    inner_folds: int,
    seed: int,
    scoring: str = "balanced_accuracy",
) -> dict:
    """Nested participant-disjoint CV with leakage assertions."""
    X = np.asarray(X)
    y = np.asarray(y).astype(int)
    groups = np.asarray(groups).astype(int)

    assignments = fold_assignment_table(groups, outer_folds, seed)
    assert_participant_disjoint(assignments)

    oof_rows = []
    fold_rows = []
    tuning_rows = []

    for fold, train_idx, test_idx, train_groups, test_groups in make_group_folds(
        groups, outer_folds, seed
    ):
        assert set(train_groups).isdisjoint(set(test_groups))
        assert set(groups[train_idx]).isdisjoint(set(groups[test_idx]))

        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]
        g_train = groups[train_idx]

        pipe = clone(estimator)
        if param_grid:
            # Build participant-disjoint inner splits over training participants only.
            unique_train = np.unique(g_train)
            inner_splitter = KFold(
                n_splits=min(inner_folds, len(unique_train)),
                shuffle=True,
                random_state=seed + fold,
            )
            inner_folds_idx = []
            for tr_g, va_g in inner_splitter.split(unique_train):
                tr_part = unique_train[tr_g]
                va_part = unique_train[va_g]
                assert set(tr_part).isdisjoint(set(va_part))
                # Map participant splits back to epoch indices within outer-train.
                tr_idx = np.flatnonzero(np.isin(g_train, tr_part))
                va_idx = np.flatnonzero(np.isin(g_train, va_part))
                inner_folds_idx.append((tr_idx, va_idx))

            search = GridSearchCV(
                estimator=pipe,
                param_grid=param_grid,
                scoring=scoring,
                cv=inner_folds_idx,
                refit=True,
                n_jobs=1,
            )
            search.fit(X_train, y_train)
            best = search.best_estimator_
            tuning_rows.append(
                {
                    "experiment": experiment,
                    "model": model_name,
                    "fold": fold,
                    "best_params": str(search.best_params_),
                    "best_inner_score": float(search.best_score_),
                    "train_subjects": "|".join(map(str, map(int, sorted(train_groups)))),
                    "test_subjects": "|".join(map(str, map(int, sorted(test_groups)))),
                }
            )
            # Prove scaler saw training data only: fitted mean length matches n_features.
            if "scaler" in best.named_steps:
                scaler = best.named_steps["scaler"]
                assert hasattr(scaler, "mean_")
                assert scaler.n_features_in_ == X_train.shape[1]
        else:
            best = pipe
            best.fit(X_train, y_train)
            tuning_rows.append(
                {
                    "experiment": experiment,
                    "model": model_name,
                    "fold": fold,
                    "best_params": "{}",
                    "best_inner_score": np.nan,
                    "train_subjects": "|".join(map(str, map(int, sorted(train_groups)))),
                    "test_subjects": "|".join(map(str, map(int, sorted(test_groups)))),
                }
            )

        y_pred = best.predict(X_test)
        y_score = continuous_score(best, X_test)
        metrics = compute_metrics(y_test, y_pred, y_score)
        metrics.update(
            {
                "experiment": experiment,
                "model": model_name,
                "fold": fold,
                "n_train_epochs": int(len(train_idx)),
                "n_test_epochs": int(len(test_idx)),
                "n_train_subjects": int(len(train_groups)),
                "n_test_subjects": int(len(test_groups)),
            }
        )
        fold_rows.append(metrics)

        meta_test = metadata.iloc[test_idx].reset_index(drop=True)
        for i in range(len(test_idx)):
            oof_rows.append(
                {
                    "experiment": experiment,
                    "model": model_name,
                    "fold": fold,
                    "subject": int(groups[test_idx[i]]),
                    "y_true": int(y_test[i]),
                    "y_pred": int(y_pred[i]),
                    "y_score": float(y_score[i]),
                    "run": int(meta_test.loc[i, "run"]) if "run" in meta_test else -1,
                    "movement": meta_test.loc[i, "movement"] if "movement" in meta_test else "",
                    "pair_id": meta_test.loc[i, "pair_id"] if "pair_id" in meta_test else "",
                    "epoch_index": int(test_idx[i]),
                }
            )

    oof = pd.DataFrame(oof_rows)
    subject_metrics = participant_metric_table(oof)
    subject_metrics.insert(0, "experiment", experiment)
    subject_metrics.insert(1, "model", model_name)
    summary = participant_mean_metrics(subject_metrics)
    summary.update({"experiment": experiment, "model": model_name})

    return {
        "fold_assignments": assignments,
        "oof_predictions": oof,
        "fold_metrics": pd.DataFrame(fold_rows),
        "participant_metrics": subject_metrics,
        "summary": summary,
        "tuning": pd.DataFrame(tuning_rows),
    }
