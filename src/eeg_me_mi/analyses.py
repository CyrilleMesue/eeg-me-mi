"""Physiology (E03), heterogeneity (E04), duration (E06), drift (E08) analyses."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import spearmanr, ttest_1samp, wilcoxon

from eeg_me_mi.features import BANDS, band_powers, extract_e01_erd_features
from eeg_me_mi.protocol import SENSORIMOTOR_CHANNELS
from eeg_me_mi.rois import ROIS


def fdr_bh(pvals: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Benjamini–Hochberg FDR; returns (reject, p_adjusted)."""
    p = np.asarray(pvals, dtype=float)
    n = len(p)
    out_p = np.full(n, np.nan)
    reject = np.zeros(n, dtype=bool)
    mask = np.isfinite(p)
    if not mask.any():
        return reject, out_p
    pv = p[mask]
    order = np.argsort(pv)
    ranked = pv[order]
    adj = ranked * n / (np.arange(1, len(ranked) + 1))
    adj = np.minimum.accumulate(adj[::-1])[::-1]
    adj = np.clip(adj, 0, 1)
    tmp = np.empty_like(adj)
    tmp[order] = adj
    out_p[mask] = tmp
    reject[mask] = out_p[mask] <= 0.05
    return reject, out_p


def _safe_wilcoxon(x: np.ndarray) -> float:
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]
    if len(x) < 3 or np.allclose(x, 0):
        return float("nan")
    try:
        return float(wilcoxon(x).pvalue)
    except ValueError:
        return float(ttest_1samp(x, 0.0).pvalue)


def participant_erd_table(epochs, preproc: dict[str, Any]) -> pd.DataFrame:
    """Epoch-level ERD features with metadata for physiology analyses."""
    X, names = extract_e01_erd_features(epochs, preproc)
    meta = epochs.metadata.reset_index(drop=True).copy()
    feat = pd.DataFrame(X, columns=names)
    return pd.concat([meta, feat], axis=1)


def e03_roi_and_channel_effects(erd_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Participant-level ME−MI ERD effects for ROIs and channels."""
    feature_cols = [c for c in erd_df.columns if c.endswith("_mu") or c.endswith("_beta")]
    # Participant × condition means
    rows_roi = []
    rows_ch = []
    for subject, sub in erd_df.groupby("subject"):
        me = sub.loc[sub["condition"] == "execution", feature_cols]
        mi = sub.loc[sub["condition"] == "imagery", feature_cols]
        if me.empty or mi.empty:
            continue
        diff = me.mean(axis=0) - mi.mean(axis=0)
        for band in BANDS:
            for roi_name, chans in ROIS.items():
                cols = [f"{ch}_{band}" for ch in chans]
                rows_roi.append(
                    {
                        "subject": int(subject),
                        "band": band,
                        "roi": roi_name,
                        "me_minus_mi": float(diff[cols].mean()),
                    }
                )
            for ch in SENSORIMOTOR_CHANNELS:
                col = f"{ch}_{band}"
                rows_ch.append(
                    {
                        "subject": int(subject),
                        "band": band,
                        "channel": ch,
                        "me_minus_mi": float(diff[col]),
                    }
                )

    roi_df = pd.DataFrame(rows_roi)
    ch_df = pd.DataFrame(rows_ch)

    def _summarize(
        frame: pd.DataFrame,
        group_cols: list[str],
        *,
        fdr_family: str,
        n_bootstrap: int = 2000,
        seed: int = 2026,
    ) -> pd.DataFrame:
        """Summarize participant effects.

        Percentile columns describe the **distribution of participant effects**,
        not a confidence interval for the mean. Bootstrap CIs are reported
        separately for the mean participant effect.
        """
        out = []
        for keys, g in frame.groupby(group_cols):
            if not isinstance(keys, tuple):
                keys = (keys,)
            vals = g["me_minus_mi"].to_numpy(dtype=float)
            vals = vals[np.isfinite(vals)]
            row = dict(zip(group_cols, keys))
            mean_effect = float(np.nanmean(vals)) if len(vals) else float("nan")
            # Participant-level bootstrap CI for the mean effect.
            if len(vals) >= 2:
                rng = np.random.default_rng(seed + (abs(hash(keys)) % 10_000))
                boots = np.empty(n_bootstrap, dtype=float)
                for i in range(n_bootstrap):
                    idx = rng.integers(0, len(vals), size=len(vals))
                    boots[i] = float(np.mean(vals[idx]))
                boot_low = float(np.percentile(boots, 2.5))
                boot_high = float(np.percentile(boots, 97.5))
            else:
                boot_low = boot_high = float("nan")
            row.update(
                {
                    "n": int(len(vals)),
                    "mean": mean_effect,
                    "std": float(np.nanstd(vals)) if len(vals) else float("nan"),
                    # Distribution of participant effects (NOT a CI for the mean).
                    "participant_effect_p2.5": float(np.nanpercentile(vals, 2.5))
                    if len(vals)
                    else float("nan"),
                    "participant_effect_p97.5": float(np.nanpercentile(vals, 97.5))
                    if len(vals)
                    else float("nan"),
                    # Inferential interval for the mean participant effect.
                    "mean_bootstrap_ci_low": boot_low,
                    "mean_bootstrap_ci_high": boot_high,
                    "p_uncorrected": _safe_wilcoxon(vals),
                    "fdr_family": fdr_family,
                }
            )
            out.append(row)
        summary = pd.DataFrame(out)
        if len(summary) and summary["p_uncorrected"].notna().any():
            mask = summary["p_uncorrected"].notna()
            rejected, p_fdr = fdr_bh(summary.loc[mask, "p_uncorrected"].to_numpy())
            summary.loc[mask, "p_fdr"] = p_fdr
            summary.loc[mask, "reject_fdr"] = rejected
        else:
            summary["p_fdr"] = np.nan
            summary["reject_fdr"] = False
        return summary

    # Multiplicity: ROI-level FDR family and channel-level FDR family are separate.
    roi_summary = (
        _summarize(roi_df, ["band", "roi"], fdr_family="roi_level") if len(roi_df) else pd.DataFrame()
    )
    ch_summary = (
        _summarize(ch_df, ["band", "channel"], fdr_family="channel_level_exploratory")
        if len(ch_df)
        else pd.DataFrame()
    )
    return roi_df, roi_summary, ch_summary


def e03_laterality(erd_df: pd.DataFrame) -> pd.DataFrame:
    """Unilateral laterality: contralateral−ipsilateral ERD (participant means)."""
    rows = []
    for subject, sub in erd_df.groupby("subject"):
        uni = sub.loc[sub["task_family"] == "unilateral"]
        if uni.empty:
            continue
        for band in BANDS:
            for movement, contra, ipsi in (
                ("left_fist", "C4", "C3"),
                ("right_fist", "C3", "C4"),
            ):
                m = uni.loc[uni["movement"] == movement]
                if m.empty:
                    continue
                me = m.loc[m["condition"] == "execution"]
                mi = m.loc[m["condition"] == "imagery"]
                if me.empty or mi.empty:
                    continue
                def lat(frame):
                    return float(frame[f"{contra}_{band}"].mean() - frame[f"{ipsi}_{band}"].mean())

                rows.append(
                    {
                        "subject": int(subject),
                        "band": band,
                        "movement": movement,
                        "laterality_me": lat(me),
                        "laterality_mi": lat(mi),
                        "laterality_me_minus_mi": lat(me) - lat(mi),
                    }
                )
    return pd.DataFrame(rows)


def e04_heterogeneity(
    participant_metrics: pd.DataFrame,
    erd_df: pd.DataFrame,
    rejection_log: pd.DataFrame,
    *,
    metric: str = "balanced_accuracy",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Exploratory participant heterogeneity tables (marked exploratory)."""
    pm = participant_metrics.copy()
    pm["rank"] = pm[metric].rank(ascending=False, method="average")
    # Correlates
    corr_rows = []
    # mean |ERD|
    feat_cols = [c for c in erd_df.columns if c.endswith("_mu") or c.endswith("_beta")]
    mean_abs = (
        erd_df.groupby("subject")[feat_cols]
        .apply(lambda x: float(np.nanmean(np.abs(x.to_numpy()))))
        .rename("mean_abs_erd")
    )
    n_epochs = erd_df.groupby("subject").size().rename("n_epochs_erd")
    rej = rejection_log.groupby("subject")["rejection_rate"].mean().rename("mean_rejection_rate")
    merged = pm.set_index("subject").join([mean_abs, n_epochs, rej], how="left")

    for col in ("mean_abs_erd", "n_epochs_erd", "mean_rejection_rate"):
        if col not in merged or merged[col].notna().sum() < 4:
            continue
        rho, p = spearmanr(merged[metric], merged[col], nan_policy="omit")
        corr_rows.append(
            {
                "analysis": "E04_exploratory",
                "predictor": col,
                "outcome": metric,
                "spearman_rho": float(rho) if np.isfinite(rho) else np.nan,
                "p_uncorrected": float(p) if np.isfinite(p) else np.nan,
            }
        )
    corr = pd.DataFrame(corr_rows)
    if len(corr) and corr["p_uncorrected"].notna().any():
        mask = corr["p_uncorrected"].notna()
        _, p_fdr = fdr_bh(corr.loc[mask, "p_uncorrected"].to_numpy())
        corr.loc[mask, "p_fdr"] = p_fdr
    else:
        corr["p_fdr"] = np.nan
    return merged.reset_index(), corr


def e06_first60_mask(metadata: pd.DataFrame) -> np.ndarray:
    """Boolean mask: cue onset within the first 60 seconds of the run."""
    return metadata["onset_seconds"].to_numpy(dtype=float) < 60.0


def e08_drift_diagnostics(epochs, preproc: dict[str, Any]) -> dict[str, pd.DataFrame]:
    """Fixed-order / drift characterization (does not remove the confound)."""
    meta = epochs.metadata.reset_index(drop=True).copy()
    # Pre-cue power
    cropped = epochs.copy().crop(preproc["baseline_tmin"], preproc["baseline_tmax"])
    powers = band_powers(cropped.get_data(copy=False), float(epochs.info["sfreq"]))
    # Mean across channels
    for band, arr in powers.items():
        meta[f"precue_{band}_mean"] = arr.mean(axis=1)
    if "ptp_uv" not in meta.columns:
        data = epochs.get_data(copy=False)
        meta["ptp_uv"] = np.ptp(data, axis=-1).max(axis=1) * 1e6

    by_run = (
        meta.groupby(["run", "condition", "task_family", "repetition"], as_index=False)
        .agg(
            n_epochs=("subject", "size"),
            precue_mu_mean=("precue_mu_mean", "mean"),
            precue_beta_mean=("precue_beta_mean", "mean"),
            ptp_mean=("ptp_uv", "mean"),
        )
        .sort_values("run")
    )

    pair_rows = []
    for me, mi in ((3, 4), (5, 6), (7, 8), (9, 10), (11, 12), (13, 14)):
        a = meta.loc[meta["run"] == me]
        b = meta.loc[meta["run"] == mi]
        pair_rows.append(
            {
                "pair_id": f"{me:02d}-{mi:02d}",
                "me_run": me,
                "mi_run": mi,
                "n_me": int(len(a)),
                "n_mi": int(len(b)),
                "precue_mu_me": float(a["precue_mu_mean"].mean()) if len(a) else np.nan,
                "precue_mu_mi": float(b["precue_mu_mean"].mean()) if len(b) else np.nan,
                "precue_beta_me": float(a["precue_beta_mean"].mean()) if len(a) else np.nan,
                "precue_beta_mi": float(b["precue_beta_mean"].mean()) if len(b) else np.nan,
                "ptp_me": float(a["ptp_uv"].mean()) if len(a) else np.nan,
                "ptp_mi": float(b["ptp_uv"].mean()) if len(b) else np.nan,
            }
        )
    pairs = pd.DataFrame(pair_rows)

    by_rep = (
        meta.groupby(["condition", "task_family", "repetition"], as_index=False)
        .agg(
            n_epochs=("subject", "size"),
            precue_mu_mean=("precue_mu_mean", "mean"),
            precue_beta_mean=("precue_beta_mean", "mean"),
            ptp_mean=("ptp_uv", "mean"),
        )
        .sort_values(["task_family", "repetition", "condition"])
    )
    return {"by_run": by_run, "matched_pairs": pairs, "by_repetition": by_rep}
