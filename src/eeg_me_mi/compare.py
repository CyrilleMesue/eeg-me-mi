"""E00 versus E01 participant-level comparison."""

from __future__ import annotations

import numpy as np
import pandas as pd

from eeg_me_mi.metrics import bootstrap_participant_means


def compare_e00_e01(
    e00_participant_metrics: pd.DataFrame,
    e01_participant_metrics: pd.DataFrame,
    *,
    metric: str = "balanced_accuracy",
    n_bootstrap: int = 50,
    seed: int = 2026,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Paired participant comparison of E01 − E00.

    Epochs are never treated as independent samples for this contrast.
    """
    a = e00_participant_metrics[["subject", metric]].rename(columns={metric: "e00"})
    b = e01_participant_metrics[["subject", metric]].rename(columns={metric: "e01"})
    merged = a.merge(b, on="subject", how="inner")
    if merged.empty:
        raise ValueError("No overlapping participants for E00/E01 comparison")
    merged["difference_e01_minus_e00"] = merged["e01"] - merged["e00"]
    merged = merged.sort_values("subject").reset_index(drop=True)

    diff_frame = merged[["subject", "difference_e01_minus_e00"]].rename(
        columns={"difference_e01_minus_e00": "balanced_accuracy"}
    )
    summary, _draws = bootstrap_participant_means(
        diff_frame,
        n_bootstrap=n_bootstrap,
        seed=seed,
        metrics=("balanced_accuracy",),
    )
    summary = summary.rename(
        columns={
            "mean": "mean_difference",
            "bootstrap_mean": "bootstrap_mean_difference",
            "ci_low": "difference_ci_low",
            "ci_high": "difference_ci_high",
        }
    )
    summary["metric"] = f"{metric}_e01_minus_e00"
    summary["n_participants"] = int(merged["subject"].nunique())
    # Attach observed mean explicitly for clarity.
    summary["observed_mean_difference"] = float(merged["difference_e01_minus_e00"].mean())
    return merged, summary
