"""E00 vs E01 paired comparison and participant sign-flip test."""

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
    """Paired participant comparison of E01 − E00."""
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
    summary["observed_mean_difference"] = float(merged["difference_e01_minus_e00"].mean())
    return merged, summary


def paired_signflip_test(
    differences: np.ndarray,
    *,
    n_signflips: int = 1000,
    seed: int = 2026,
) -> dict:
    """Participant-level paired sign-flip / randomization test on differences.

    Under the null that the mean paired difference is zero, randomly flip the
    sign of each participant's difference and recompute the mean. Plus-one p.
    """
    d = np.asarray(differences, dtype=float)
    d = d[np.isfinite(d)]
    if len(d) == 0:
        raise ValueError("No finite paired differences")
    observed = float(np.mean(d))
    rng = np.random.default_rng(seed)
    null = np.empty(n_signflips, dtype=float)
    for i in range(n_signflips):
        signs = rng.choice(np.array([-1.0, 1.0]), size=len(d))
        null[i] = float(np.mean(signs * d))
    # Two-sided plus-one p-value
    p = (1 + np.sum(np.abs(null) >= abs(observed))) / (n_signflips + 1)
    return {
        "observed_mean_difference": observed,
        "n_participants": int(len(d)),
        "n_signflips": int(n_signflips),
        "p_value_plusone": float(p),
        "null_mean": float(np.mean(null)),
        "null_std": float(np.std(null)),
    }
