"""Metric aggregation and bootstrap unit tests."""

import numpy as np
import pandas as pd

from eeg_me_mi.metrics import (
    bootstrap_participant_means,
    compute_metrics,
    participant_mean_metrics,
    participant_metric_table,
)


def test_confusion_matrix_metrics():
    y_true = np.array([0, 0, 1, 1])
    y_pred = np.array([0, 1, 1, 1])
    y_score = np.array([0.1, 0.6, 0.7, 0.9])
    metrics = compute_metrics(y_true, y_pred, y_score)
    assert metrics["sensitivity"] == 1.0
    assert metrics["specificity"] == 0.5
    assert 0.0 <= metrics["roc_auc"] <= 1.0
    hard_auc = compute_metrics(y_true, y_pred, y_pred.astype(float))["roc_auc"]
    # Continuous scores should be usable; hard labels are a different input.
    assert np.isfinite(metrics["roc_auc"])
    assert np.isfinite(hard_auc)


def test_participant_balanced_aggregation():
    oof = pd.DataFrame(
        {
            "subject": [1, 1, 1, 1, 2, 2],
            "y_true": [0, 0, 1, 1, 0, 1],
            "y_pred": [0, 0, 1, 0, 0, 1],
            "y_score": [0.1, 0.2, 0.8, 0.4, 0.3, 0.9],
        }
    )
    table = participant_metric_table(oof)
    summary = participant_mean_metrics(table)
    assert len(table) == 2
    assert summary["balanced_accuracy"] == float(np.mean(table["balanced_accuracy"]))


def test_bootstrap_resamples_participants_not_epochs():
    subject_metrics = pd.DataFrame(
        {
            "subject": [1, 2, 3, 4],
            "balanced_accuracy": [0.5, 0.6, 0.7, 0.8],
            "n_epochs": [100, 10, 10, 10],
        }
    )
    summary, draws = bootstrap_participant_means(
        subject_metrics,
        n_bootstrap=20,
        seed=0,
        metrics=("balanced_accuracy",),
    )
    assert len(draws) == 20
    assert summary.loc[0, "n_participants"] == 4
    assert summary.loc[0, "mean"] == float(np.mean(subject_metrics["balanced_accuracy"]))
