"""Deterministic participant-disjoint cross-validation."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.model_selection import KFold


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
        folds.append((fold, train_idx, test_idx))
    return folds


def fold_assignment_table(groups: np.ndarray, n_splits: int, seed: int) -> pd.DataFrame:
    rows = []
    groups = np.asarray(groups)
    for fold, train_idx, test_idx in make_group_folds(groups, n_splits, seed):
        rows.extend({"fold": fold, "role": "train", "subject": int(x)} for x in np.unique(groups[train_idx]))
        rows.extend({"fold": fold, "role": "test", "subject": int(x)} for x in np.unique(groups[test_idx]))
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

