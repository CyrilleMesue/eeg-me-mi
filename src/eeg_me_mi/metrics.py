"""Evaluation metrics, participant aggregation, and bootstrap CIs."""

from __future__ import annotations

from typing import Iterable

import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    matthews_corrcoef,
    roc_auc_score,
)


METRIC_NAMES = (
    "balanced_accuracy",
    "roc_auc",
    "macro_f1",
    "sensitivity",
    "specificity",
    "average_precision",
    "mcc",
    "accuracy",
)


def continuous_score(estimator, X: np.ndarray) -> np.ndarray:
    if hasattr(estimator, "predict_proba"):
        proba = estimator.predict_proba(X)
        if proba.ndim == 2 and proba.shape[1] >= 2:
            return proba[:, 1]
        return proba.ravel()
    if hasattr(estimator, "decision_function"):
        return np.asarray(estimator.decision_function(X), dtype=float)
    # Last resort: hard predictions (should not be used for ROC-AUC primary path).
    return np.asarray(estimator.predict(X), dtype=float)


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray, y_score: np.ndarray) -> dict[str, float]:
    y_true = np.asarray(y_true).astype(int)
    y_pred = np.asarray(y_pred).astype(int)
    y_score = np.asarray(y_score, dtype=float)

    metrics: dict[str, float] = {
        "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        "macro_f1": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "mcc": float(matthews_corrcoef(y_true, y_pred)) if len(np.unique(y_true)) > 1 else float("nan"),
    }

    # Confusion-matrix derived sensitivity / specificity for positive class = 1 (ME).
    if len(np.unique(y_true)) < 2 or len(np.unique(y_pred)) == 0:
        metrics["sensitivity"] = float("nan")
        metrics["specificity"] = float("nan")
    else:
        tn, fp, fn, tp = confusion_matrix(y_true, y_pred, labels=[0, 1]).ravel()
        metrics["sensitivity"] = float(tp / (tp + fn)) if (tp + fn) else float("nan")
        metrics["specificity"] = float(tn / (tn + fp)) if (tn + fp) else float("nan")

    if len(np.unique(y_true)) < 2:
        metrics["roc_auc"] = float("nan")
        metrics["average_precision"] = float("nan")
    else:
        metrics["roc_auc"] = float(roc_auc_score(y_true, y_score))
        metrics["average_precision"] = float(average_precision_score(y_true, y_score))
    return metrics


def participant_metric_table(oof: pd.DataFrame) -> pd.DataFrame:
    """Compute per-participant metrics from epoch-level OOF predictions."""
    required = {"subject", "y_true", "y_pred", "y_score"}
    if not required <= set(oof.columns):
        raise ValueError(f"OOF missing columns: {sorted(required - set(oof.columns))}")

    rows = []
    for subject, frame in oof.groupby("subject"):
        metrics = compute_metrics(
            frame["y_true"].to_numpy(),
            frame["y_pred"].to_numpy(),
            frame["y_score"].to_numpy(),
        )
        metrics["subject"] = int(subject)
        metrics["n_epochs"] = int(len(frame))
        rows.append(metrics)
    return pd.DataFrame(rows).sort_values("subject").reset_index(drop=True)


def participant_mean_metrics(subject_metrics: pd.DataFrame) -> dict[str, float]:
    """Equal-weight average across participants (primary aggregation)."""
    out: dict[str, float] = {}
    for name in METRIC_NAMES:
        if name in subject_metrics:
            out[name] = float(np.nanmean(subject_metrics[name].to_numpy(dtype=float)))
    out["n_participants"] = float(subject_metrics["subject"].nunique())
    return out


def bootstrap_participant_means(
    subject_metrics: pd.DataFrame,
    n_bootstrap: int,
    seed: int,
    metrics: Iterable[str] = ("balanced_accuracy",),
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Participant-level bootstrap of mean metrics.

    The bootstrap unit is the participant row, never the EEG epoch.
    """
    metrics = tuple(metrics)
    values = subject_metrics.loc[:, list(metrics)].to_numpy(dtype=float)
    n = values.shape[0]
    if n == 0:
        raise ValueError("No participants available for bootstrap")

    rng = np.random.default_rng(seed)
    draws = np.empty((n_bootstrap, len(metrics)), dtype=float)
    for i in range(n_bootstrap):
        idx = rng.integers(0, n, size=n)  # resample participants
        draws[i] = np.nanmean(values[idx], axis=0)

    summary_rows = []
    for j, name in enumerate(metrics):
        col = draws[:, j]
        summary_rows.append(
            {
                "metric": name,
                "mean": float(np.nanmean(values[:, j])),
                "bootstrap_mean": float(np.nanmean(col)),
                "ci_low": float(np.nanpercentile(col, 2.5)),
                "ci_high": float(np.nanpercentile(col, 97.5)),
                "n_bootstrap": n_bootstrap,
                "n_participants": n,
            }
        )
    summary = pd.DataFrame(summary_rows)
    draw_df = pd.DataFrame(draws, columns=list(metrics))
    draw_df.insert(0, "bootstrap_id", np.arange(1, n_bootstrap + 1))
    return summary, draw_df
