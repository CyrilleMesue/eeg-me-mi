"""Participant-equal model-selection scoring.

Inner hyperparameter selection uses the arithmetic mean of per-participant
balanced accuracies on the inner validation fold. Participants with more epochs
do not receive greater weight.
"""

from __future__ import annotations

import numpy as np
from sklearn.metrics import balanced_accuracy_score


def participant_mean_balanced_accuracy(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    groups: np.ndarray,
) -> float:
    """Equal-weight mean of per-participant balanced accuracy."""
    y_true = np.asarray(y_true).astype(int)
    y_pred = np.asarray(y_pred).astype(int)
    groups = np.asarray(groups)
    if len(y_true) != len(y_pred) or len(y_true) != len(groups):
        raise ValueError("y_true, y_pred, and groups must have equal length")
    scores: list[float] = []
    for g in np.unique(groups):
        mask = groups == g
        scores.append(float(balanced_accuracy_score(y_true[mask], y_pred[mask])))
    if not scores:
        raise ValueError("No participants present for scoring")
    return float(np.mean(scores))
