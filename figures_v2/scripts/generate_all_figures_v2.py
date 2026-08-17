#!/usr/bin/env python3
"""Publication Figures V2 — journal redesign from frozen outputs only.

Entry: PYTHONPATH=src python figures_v2/scripts/generate_all_figures_v2.py
Does not rerun EEG analyses or alter frozen numerical results.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
from matplotlib.gridspec import GridSpec

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "figures_v2" / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

from paths import CMP, E00, E01, E02, E03, E05, E07, QC, REV, SENS, boot_ci, load_json  # noqa: E402
from style import (  # noqa: E402
    BETA,
    BLACK,
    CHANCE,
    CONTROL,
    FIG_PREV,
    FIG_SRC,
    GRAY,
    LIGHT,
    ME,
    MI,
    MU,
    NEUTRAL,
    NULL,
    PRIMARY,
    apply_style,
    chance_hline,
    chance_vline,
    panel_label,
    save_figure,
)

# Exact unit conversion for Welch power stored in V² (MNE default) → µV²
V2_TO_UV2 = 1e12


def export_csv(name: str, df: pd.DataFrame) -> None:
    FIG_SRC.mkdir(parents=True, exist_ok=True)
    df.to_csv(FIG_SRC / name, index=False)


def export_json(name: str, obj: dict) -> None:
    FIG_SRC.mkdir(parents=True, exist_ok=True)
    (FIG_SRC / name).write_text(json.dumps(obj, indent=2) + "\n")


def _channel_xy(channels: list[str]) -> np.ndarray:
    import mne

    info = mne.create_info(channels, 80.0, ch_types="eeg")
    info.set_montage("standard_1005", on_missing="ignore")
    pos = np.array([info["chs"][i]["loc"][:2] for i in range(len(channels))])
    return pos


# ---------------------------------------------------------------------------
# Figure 1 — Design and safeguards (3 panels)
# ---------------------------------------------------------------------------


def figure_1() -> None:
    fig = plt.figure(figsize=(7.2, 6.4))
    gs = GridSpec(2, 2, figure=fig, height_ratios=[1.0, 1.15], hspace=0.38, wspace=0.28)

    # A — fixed protocol order
    ax = fig.add_subplot(gs[0, 0])
    panel_label(ax, "A")
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5.2)
    ax.axis("off")
    ax.set_title("Fixed protocol order", loc="left", pad=4)
    pairs = [(3, 4, "L/R fist"), (5, 6, "both"), (7, 8, "L/R fist"), (9, 10, "both"), (11, 12, "L/R fist"), (13, 14, "both")]
    for i, (me_r, mi_r, fam) in enumerate(pairs):
        y = 4.3 - (i % 3) * 1.25
        x0 = 0.6 if i < 3 else 5.4
        ax.add_patch(mpatches.FancyBboxPatch((x0, y), 1.35, 0.7, boxstyle="round,pad=0.02", fc=ME, ec=BLACK, lw=0.5))
        ax.text(x0 + 0.675, y + 0.35, f"ME R{me_r}", ha="center", va="center", color="white", fontsize=7, fontweight="bold")
        ax.annotate("", xy=(x0 + 1.85, y + 0.35), xytext=(x0 + 1.4, y + 0.35), arrowprops=dict(arrowstyle="->", color=BLACK, lw=0.9))
        ax.add_patch(mpatches.FancyBboxPatch((x0 + 1.9, y), 1.35, 0.7, boxstyle="round,pad=0.02", fc=MI, ec=BLACK, lw=0.5))
        ax.text(x0 + 2.575, y + 0.35, f"MI R{mi_r}", ha="center", va="center", color="white", fontsize=7, fontweight="bold")
        ax.text(x0 + 1.75, y - 0.28, fam, ha="center", fontsize=6, color=GRAY)
    ax.text(0.3, 0.25, "Fixed ME→MI ordering", fontsize=7.5, style="italic", color=GRAY)

    # B — temporal windows
    ax = fig.add_subplot(gs[0, 1])
    panel_label(ax, "B")
    ax.set_title("Temporal windows", loc="left", pad=4)
    # timeline from -2.2 to 3.7
    ax.set_xlim(-2.3, 3.8)
    ax.set_ylim(0, 3.2)
    # regions
    ax.axvspan(-2.0, -0.8375, ymin=0.35, ymax=0.78, color=CONTROL, alpha=0.45, lw=0)
    ax.axvspan(-0.8375, 0.8375, ymin=0.35, ymax=0.78, color=LIGHT, alpha=0.9, lw=0)
    ax.axvspan(0.8375, 3.5, ymin=0.35, ymax=0.78, color=PRIMARY, alpha=0.35, lw=0)
    ax.axvline(0, color=BLACK, lw=1.1)
    ax.plot([-2.3, 3.8], [1.0, 1.0], color=BLACK, lw=0.7)
    ax.text(0, 2.85, "cue", ha="center", fontsize=7)
    ax.text(-1.42, 2.35, "safe pre-cue", ha="center", fontsize=6.5)
    ax.text(0, 2.35, "excluded", ha="center", fontsize=6.5, color=GRAY)
    ax.text(2.15, 2.35, "post-cue task", ha="center", fontsize=6.5)
    ax.text(-1.42, 0.55, "E00 power\nE01 baseline", ha="center", fontsize=6.5, color=BLACK)
    ax.text(2.15, 0.55, "E01 ERD", ha="center", fontsize=6.5, color=BLACK)
    ax.text(3.7, 0.15, "FIR-safe margins", ha="right", fontsize=6.5, style="italic", color=GRAY)
    ax.set_yticks([])
    ax.set_xlabel("Time relative to cue (s)")
    for spine in ("left", "top", "right"):
        ax.spines[spine].set_visible(False)

    # C — participant-disjoint pipeline
    ax = fig.add_subplot(gs[1, :])
    panel_label(ax, "C", x=-0.03)
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 3.2)
    ax.axis("off")
    ax.set_title("Participant-disjoint analysis", loc="left", pad=4)
    boxes = [
        (0.2, 1.2, 2.0, "21 SM channels\n× μ + β\n= 42 ERD features"),
        (3.0, 1.2, 2.2, "Nested\nparticipant-disjoint\nCV"),
        (5.9, 1.2, 2.0, "Held-out\nparticipants"),
        (8.5, 1.2, 1.7, "Participant-level\nmetrics"),
        (10.5, 1.2, 1.4, "Participant-\nmean BAcc"),
    ]
    for x, y, w, txt in boxes:
        ax.add_patch(mpatches.FancyBboxPatch((x, y), w, 1.4, boxstyle="round,pad=0.03", fc="white", ec=BLACK, lw=0.7))
        ax.text(x + w / 2, y + 0.7, txt, ha="center", va="center", fontsize=7)
    for x in (2.25, 5.25, 7.95, 10.25):
        ax.annotate("", xy=(x + 0.7, 1.9), xytext=(x, 1.9), arrowprops=dict(arrowstyle="->", color=BLACK, lw=0.9))
    ax.text(6, 0.35, "No participant contributes epochs to both training and outer test", ha="center", fontsize=7, style="italic", color=GRAY)

    save_figure(fig, "Figure_1_Design_Safeguards", main=True)


# ---------------------------------------------------------------------------
# Figure 2 — Cross-participant decoding (3 panels)
# ---------------------------------------------------------------------------


def figure_2() -> None:
    pm = pd.read_csv(E01 / "erd_lr/participant_metrics.csv")
    mean, lo, hi = boot_ci(E01 / "erd_lr/bootstrap_summary.csv")
    e07 = load_json(E07 / "e07_summary.json")
    null = pd.read_csv(E07 / "null_statistics.csv")

    models = []
    for key, label, is_primary in [
        ("dummy", "Dummy", False),
        ("csp_lda", "CSP-LDA", False),
        ("tangent_lr", "Riemannian-LR", False),
        ("erd_lr", "ERD-LR", True),
    ]:
        m, clo, chi = boot_ci(E01 / f"{key}/bootstrap_summary.csv")
        models.append({"model": label, "key": key, "primary": is_primary, "bacc": m, "ci_low": clo, "ci_high": chi})
    models_df = pd.DataFrame(models)

    export_csv("Figure_2A_source.csv", pm[["subject", "balanced_accuracy", "n_epochs"]])
    export_csv("Figure_2B_source.csv", models_df)
    export_csv("Figure_2C_source.csv", null[["perm_id", "statistic"]])
    export_json(
        "Figure_2_annotations.json",
        {
            "n": int(pm["subject"].nunique()),
            "mean_bacc": mean,
            "ci": [lo, hi],
            "observed_e07": e07["observed_statistic"],
            "n_null": len(null),
            "n_null_ge": e07["n_null_ge_observed"],
            "p_plusone": e07["p_value_plusone"],
        },
    )

    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.9), gridspec_kw={"width_ratios": [1.05, 1.0, 1.15]})

    # A
    ax = axes[0]
    panel_label(ax, "A")
    vals = pm["balanced_accuracy"].to_numpy()
    rng = np.random.default_rng(2026)
    jitter = 0.04 * rng.standard_normal(len(vals))
    parts = ax.violinplot(vals, positions=[0], showmeans=False, showmedians=False, showextrema=False, widths=0.75)
    for b in parts["bodies"]:
        b.set_facecolor(PRIMARY)
        b.set_alpha(0.22)
        b.set_edgecolor(PRIMARY)
        b.set_linewidth(0.6)
    ax.scatter(jitter, vals, s=9, c=PRIMARY, alpha=0.55, edgecolors="none", zorder=3)
    ax.errorbar(0.42, mean, yerr=[[mean - lo], [hi - mean]], fmt="o", color=BLACK, ms=5, capsize=3, zorder=4, elinewidth=1)
    chance_hline(ax)
    ax.set_xlim(-0.65, 0.75)
    ax.set_ylim(0.35, 0.95)
    ax.set_xticks([])
    ax.set_ylabel("Balanced accuracy")
    ax.set_title("Participant-level performance", loc="left")
    ax.text(0.02, 0.98, f"N={len(vals)}\nmean={mean:.3f}", transform=ax.transAxes, va="top", fontsize=7)

    # B
    ax = axes[1]
    panel_label(ax, "B")
    y = np.arange(len(models_df))
    colors = [NEUTRAL, CONTROL, CONTROL, PRIMARY]
    ax.errorbar(
        models_df["bacc"],
        y,
        xerr=[models_df["bacc"] - models_df["ci_low"], models_df["ci_high"] - models_df["bacc"]],
        fmt="none",
        ecolor=BLACK,
        capsize=2.5,
        elinewidth=1,
        zorder=2,
    )
    ax.scatter(models_df["bacc"], y, s=36, c=colors, edgecolors=BLACK, lw=0.5, zorder=3)
    chance_vline(ax)
    labels = [f"{r.model}" + (" (primary)" if r.primary else "") for r in models_df.itertuples()]
    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.invert_yaxis()
    ax.set_xlabel("Participant-mean BAcc")
    ax.set_xlim(0.45, 0.68)
    ax.set_title("Model comparators", loc="left")

    # C
    ax = axes[2]
    panel_label(ax, "C")
    ax.hist(null["statistic"], bins=35, color=NULL, edgecolor="white", lw=0.3, alpha=0.9)
    ax.axvline(e07["observed_statistic"], color=PRIMARY, lw=1.6)
    ax.set_xlabel("Null participant-mean BAcc")
    ax.set_ylabel("Count")
    ax.set_title("Structured permutation", loc="left")
    ax.text(
        0.98,
        0.97,
        f"obs={e07['observed_statistic']:.3f}\n0/1000 ≥ obs\np={e07['p_value_plusone']:.6f}",
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=6.5,
    )

    fig.tight_layout(w_pad=1.2)
    save_figure(fig, "Figure_2_Primary_Decoding", main=True)


# ---------------------------------------------------------------------------
# Figure 3 — Pre-cue vs post-cue (3 panels)
# ---------------------------------------------------------------------------


def figure_3() -> None:
    paired = pd.read_csv(CMP / "e00_vs_e01_participant.csv")
    boot = pd.read_csv(CMP / "e00_vs_e01_bootstrap_summary.csv").iloc[0]
    sign = load_json(CMP / "e00_vs_e01_signflip.json")
    e00_m, e00_lo, e00_hi = boot_ci(E00 / "bootstrap_summary.csv")
    e01_m, e01_lo, e01_hi = boot_ci(E01 / "erd_lr/bootstrap_summary.csv")

    delta = paired["difference_e01_minus_e00"].to_numpy()
    n_pos = int(np.sum(delta > 0))
    d_mean = float(boot["mean_difference"])
    d_lo = float(boot["difference_ci_low"])
    d_hi = float(boot["difference_ci_high"])
    pval = float(sign["p_value_plusone"])

    export_csv("Figure_3B_source.csv", paired)
    export_csv(
        "Figure_3C_source.csv",
        paired[["subject", "difference_e01_minus_e00"]].rename(columns={"difference_e01_minus_e00": "delta_bacc"}),
    )
    export_json(
        "Figure_3_annotations.json",
        {
            "n": int(len(paired)),
            "e00_mean": e00_m,
            "e00_ci": [e00_lo, e00_hi],
            "e01_mean": e01_m,
            "e01_ci": [e01_lo, e01_hi],
            "mean_delta": d_mean,
            "delta_ci": [d_lo, d_hi],
            "signflip_p": pval,
            "n_delta_gt0": n_pos,
            "pct_delta_gt0": n_pos / len(paired),
        },
    )

    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.85), gridspec_kw={"width_ratios": [0.85, 1.15, 1.15]})

    # A compact schematic
    ax = axes[0]
    panel_label(ax, "A")
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis("off")
    ax.set_title("Analysis windows", loc="left")
    ax.add_patch(mpatches.FancyBboxPatch((0.5, 3.6), 9, 1.5, boxstyle="round,pad=0.02", fc=CONTROL, alpha=0.35, ec=BLACK, lw=0.5))
    ax.text(5, 4.35, "E00 — pre-cue absolute μ/β power", ha="center", va="center", fontsize=7.5)
    ax.add_patch(mpatches.FancyBboxPatch((0.5, 1.2), 4.2, 1.5, boxstyle="round,pad=0.02", fc=LIGHT, ec=BLACK, lw=0.5))
    ax.text(2.6, 1.95, "E01 baseline\n(pre-cue)", ha="center", va="center", fontsize=7)
    ax.add_patch(mpatches.FancyBboxPatch((5.3, 1.2), 4.2, 1.5, boxstyle="round,pad=0.02", fc=PRIMARY, alpha=0.35, ec=BLACK, lw=0.5))
    ax.text(7.4, 1.95, "E01 task\n(post-cue ERD)", ha="center", va="center", fontsize=7)
    ax.text(5, 0.35, "FIR-safe windows", ha="center", fontsize=6.5, style="italic", color=GRAY)

    # B distributions
    ax = axes[1]
    panel_label(ax, "B")
    e00 = paired["e00"].to_numpy()
    e01 = paired["e01"].to_numpy()
    data = [e00, e01]
    parts = ax.violinplot(data, positions=[0, 1], showmeans=False, showextrema=False, widths=0.7)
    for b, col in zip(parts["bodies"], [CONTROL, PRIMARY]):
        b.set_facecolor(col)
        b.set_alpha(0.25)
        b.set_edgecolor(col)
    rng = np.random.default_rng(7)
    for i, (arr, col) in enumerate(zip(data, [CONTROL, PRIMARY])):
        ax.scatter(i + 0.04 * rng.standard_normal(len(arr)), arr, s=7, c=col, alpha=0.45, edgecolors="none", zorder=3)
    ax.errorbar(0, e00_m, yerr=[[e00_m - e00_lo], [e00_hi - e00_m]], fmt="o", color=BLACK, ms=4.5, capsize=2.5, zorder=4)
    ax.errorbar(1, e01_m, yerr=[[e01_m - e01_lo], [e01_hi - e01_m]], fmt="o", color=BLACK, ms=4.5, capsize=2.5, zorder=4)
    chance_hline(ax)
    ax.set_xticks([0, 1])
    ax.set_xticklabels([f"E00\n{e00_m:.3f}", f"E01\n{e01_m:.3f}"])
    ax.set_ylabel("Balanced accuracy")
    ax.set_ylim(0.35, 0.95)
    ax.set_title("E00 vs E01", loc="left")

    # C delta
    ax = axes[2]
    panel_label(ax, "C")
    parts = ax.violinplot(delta, positions=[0], showmeans=False, showextrema=False, widths=0.7)
    for b in parts["bodies"]:
        b.set_facecolor(PRIMARY)
        b.set_alpha(0.22)
        b.set_edgecolor(PRIMARY)
    ax.scatter(0.04 * rng.standard_normal(len(delta)), delta, s=8, c=PRIMARY, alpha=0.5, edgecolors="none", zorder=3)
    ax.errorbar(0.4, d_mean, yerr=[[d_mean - d_lo], [d_hi - d_mean]], fmt="o", color=BLACK, ms=5, capsize=3, zorder=4)
    ax.axhline(0, color=CHANCE, ls="--", lw=0.9)
    ax.set_xticks([])
    ax.set_ylabel("ΔBAcc (E01 − E00)")
    ax.set_title("Participant ΔBAcc", loc="left")
    ax.text(
        0.98,
        0.98,
        f"mean={d_mean:.3f}\n{n_pos}/{len(delta)} Δ>0\np={pval:.4f}",
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=6.5,
    )

    fig.tight_layout(w_pad=1.0)
    save_figure(fig, "Figure_3_PreCue_PostCue", main=True)


# ---------------------------------------------------------------------------
# Figure 4 — Physiology and spatial (former Fig4 A–C)
# Figure 5 — Robustness and protocol state (former Fig4 D)
# ---------------------------------------------------------------------------


def _robustness_table() -> tuple[pd.DataFrame, float]:
    rob_rows = []
    prim_m, prim_lo, prim_hi = boot_ci(E01 / "erd_lr/bootstrap_summary.csv")
    rob_rows.append({"analysis": "Primary", "n": 102, "bacc": prim_m, "ci_low": prim_lo, "ci_high": prim_hi})
    for key, label in [("none", "No rejection"), ("150uv", "150 µV"), ("200uv", "200 µV")]:
        m, lo, hi = boot_ci(E05 / f"artifact_sensitivity/{key}/bootstrap_summary.csv")
        n = int(load_json(E05 / f"artifact_sensitivity/{key}/summary.json")["n_participants"])
        rob_rows.append({"analysis": label, "n": n, "bacc": m, "ci_low": lo, "ci_high": hi})
    sens = pd.read_csv(REV / "sensitivity_summary.csv")
    for analysis, label in [
        ("E01_strict", "Strict cohort"),
        ("E06_first60", "First 60 s"),
        ("E06_all_events", "All events"),
    ]:
        r = sens.loc[sens.analysis == analysis].iloc[0]
        rob_rows.append(
            {
                "analysis": label,
                "n": int(r["n"]),
                "bacc": float(r["bacc"]),
                "ci_low": float(r["ci_low"]),
                "ci_high": float(r["ci_high"]),
            }
        )
    samp = load_json(SENS / "sampling_rate/sampling_rate_sensitivity_summary.json")
    rob_rows.append(
        {
            "analysis": "Sampling-rate",
            "n": samp["sensitivity_n"],
            "bacc": samp["sensitivity_bacc"],
            "ci_low": samp["sensitivity_ci"][0],
            "ci_high": samp["sensitivity_ci"][1],
        }
    )
    return pd.DataFrame(rob_rows), prim_m


def figure_4() -> None:
    """Physiology + spatial (V2 Fig4 panels A–C, preserved style)."""
    from eeg_me_mi.protocol import SENSORIMOTOR_CHANNELS

    roi = pd.read_csv(E03 / "roi_summary.csv")
    ch = pd.read_csv(E03 / "channel_summary_fdr.csv")
    spat = load_json(E05 / "spatial_control/paired_effect_summary.json")
    spat_boot = pd.read_csv(E05 / "spatial_control/bootstrap_summary.csv")
    spat_boot_row = (
        spat_boot.loc[spat_boot["metric"] == "balanced_accuracy"].iloc[0]
        if "metric" in spat_boot.columns
        else spat_boot.iloc[0]
    )
    paired = pd.read_csv(E05 / "spatial_control/paired_participant_differences.csv")

    export_csv("Figure_4A_source.csv", roi)
    export_csv("Figure_4B_source.csv", ch[["band", "channel", "mean", "p_fdr", "reject_fdr"]])
    export_csv("Figure_4C_source.csv", paired)
    export_json(
        "Figure_4_annotations.json",
        {
            "spatial_n": int(spat_boot_row["n_participants"]) if "n_participants" in spat_boot_row else 78,
            "spatial_bacc": float(spat_boot_row["mean"]),
            "spatial_ci": [float(spat_boot_row["ci_low"]), float(spat_boot_row["ci_high"])],
            "paired_n": spat["common_n"],
            "mean_sm_minus_sc": spat["mean_difference_sm_minus_sc"],
            "paired_ci": [spat["bootstrap_ci_low"], spat["bootstrap_ci_high"]],
            "formal_p": False,
        },
    )

    fig = plt.figure(figsize=(7.2, 6.2))
    outer = GridSpec(2, 2, figure=fig, height_ratios=[1.0, 1.15], hspace=0.38, wspace=0.32)

    # A forest ROI
    ax = fig.add_subplot(outer[0, 0])
    panel_label(ax, "A")
    order = [
        ("mu", "left_sensorimotor", "μ left"),
        ("mu", "midline", "μ midline"),
        ("mu", "right_sensorimotor", "μ right"),
        ("beta", "left_sensorimotor", "β left"),
        ("beta", "midline", "β midline"),
        ("beta", "right_sensorimotor", "β right"),
    ]
    ys, means, los, his, colors = [], [], [], [], []
    for i, (band, rname, lab) in enumerate(order):
        row = roi.loc[(roi.band == band) & (roi.roi == rname)].iloc[0]
        ys.append(i)
        means.append(float(row["mean"]))
        los.append(float(row["mean_bootstrap_ci_low"]))
        his.append(float(row["mean_bootstrap_ci_high"]))
        colors.append(MU if band == "mu" else BETA)
    ax.errorbar(
        means,
        ys,
        xerr=[np.array(means) - np.array(los), np.array(his) - np.array(means)],
        fmt="o",
        color=BLACK,
        ecolor=BLACK,
        ms=0,
        capsize=2.5,
        elinewidth=1,
        zorder=2,
    )
    ax.scatter(means, ys, c=colors, s=28, edgecolors=BLACK, lw=0.4, zorder=3)
    ax.axvline(0, color=CHANCE, ls="--", lw=0.9)
    ax.set_yticks(ys)
    ax.set_yticklabels([o[2] for o in order])
    ax.invert_yaxis()
    ax.set_xlabel("ME − MI ERD (dB)")
    ax.set_title("ROI ERD effects", loc="left")
    ax.text(0.98, 0.02, "FDR q<0.05 (all)", transform=ax.transAxes, ha="right", va="bottom", fontsize=6, color=GRAY)

    # B topomaps
    gs_b = outer[0, 1].subgridspec(1, 3, width_ratios=[1, 1, 0.08], wspace=0.15)
    ax_mu = fig.add_subplot(gs_b[0, 0])
    ax_beta = fig.add_subplot(gs_b[0, 1])
    cax = fig.add_subplot(gs_b[0, 2])
    panel_label(ax_mu, "B")
    import mne

    info = mne.create_info(list(SENSORIMOTOR_CHANNELS), 80.0, ch_types="eeg")
    info.set_montage("standard_1005", on_missing="ignore")
    vmax = float(np.nanmax(np.abs(ch["mean"].to_numpy())))
    im = None
    for ax_t, band, title in ((ax_mu, "mu", "μ"), (ax_beta, "beta", "β")):
        sub = ch.loc[ch.band == band].set_index("channel")
        data = np.array([float(sub.loc[c, "mean"]) for c in SENSORIMOTOR_CHANNELS])
        im, _ = mne.viz.plot_topomap(
            data,
            info,
            axes=ax_t,
            show=False,
            cmap="RdBu_r",
            vlim=(-vmax, vmax),
            contours=0,
            sensors=True,
            names=None,
        )
        ax_t.set_title(title, fontsize=8)
    cb = fig.colorbar(im, cax=cax)
    cb.set_label("dB", fontsize=6)
    cb.ax.tick_params(labelsize=5)
    ax_mu.set_xlabel("Scalp ME−MI (sensor-space)", fontsize=6.5)

    # C spatial paired (full width)
    ax = fig.add_subplot(outer[1, :])
    panel_label(ax, "C")
    sm = paired["bacc_sm"].to_numpy()
    sc = paired["bacc_sc"].to_numpy()
    dlt = paired["difference_sm_minus_sc"].to_numpy()
    parts = ax.violinplot([sm, sc], positions=[0, 1], showmeans=False, showextrema=False, widths=0.65)
    for b, col in zip(parts["bodies"], [PRIMARY, NEUTRAL]):
        b.set_facecolor(col)
        b.set_alpha(0.25)
        b.set_edgecolor(col)
    rng = np.random.default_rng(11)
    ax.scatter(0 + 0.04 * rng.standard_normal(len(sm)), sm, s=7, c=PRIMARY, alpha=0.45, edgecolors="none")
    ax.scatter(1 + 0.04 * rng.standard_normal(len(sc)), sc, s=7, c=NEUTRAL, alpha=0.45, edgecolors="none")
    chance_hline(ax)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["Sensorimotor", "Peripheral\ncontrol"])
    ax.set_ylabel("Balanced accuracy")
    ax.set_ylim(0.35, 0.90)
    ax.set_xlim(-0.7, 1.7)
    ax.set_title(f"Spatial control (paired N={spat['common_n']})", loc="left")
    ax.text(
        0.02,
        0.02,
        f"mean Δ={spat['mean_difference_sm_minus_sc']:.3f}\n"
        f"95% CI [{spat['bootstrap_ci_low']:.3f}, {spat['bootstrap_ci_high']:.3f}]",
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=6.5,
    )
    inset = ax.inset_axes([0.72, 0.55, 0.25, 0.40])
    inset.hist(dlt, bins=18, color=PRIMARY, edgecolor="white", lw=0.3, alpha=0.85)
    inset.axvline(0, color=CHANCE, ls="--", lw=0.8)
    inset.axvline(spat["mean_difference_sm_minus_sc"], color=BLACK, lw=1.0)
    inset.set_title("Δ (SM−SC)", fontsize=6, pad=1)
    inset.tick_params(labelsize=5)
    inset.set_yticks([])

    save_figure(fig, "Figure_4_Physiology_Spatial", main=True)


def figure_5() -> None:
    """Robustness + protocol-state (former Fig4 panel D, preserved style)."""
    rob, prim_m = _robustness_table()
    pairs = pd.read_csv(REV / "e08_matched_pairs.csv").copy()
    pairs["precue_beta_me_uv2"] = pairs["precue_beta_me"] * V2_TO_UV2
    pairs["precue_beta_mi_uv2"] = pairs["precue_beta_mi"] * V2_TO_UV2
    pairs["delta_beta_uv2"] = pairs["precue_beta_me_uv2"] - pairs["precue_beta_mi_uv2"]

    export_csv("Figure_5A_robustness_source.csv", rob)
    export_csv("Figure_5B_e08_source.csv", pairs)
    export_json(
        "Figure_5_annotations.json",
        {
            "primary_bacc": prim_m,
            "v2_to_uv2": V2_TO_UV2,
            "unit_note": "Pre-cue β displayed as µV² via exact V²×1e12 conversion",
        },
    )

    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.6), gridspec_kw={"width_ratios": [1.15, 1.0]})

    ax_rob = axes[0]
    panel_label(ax_rob, "A")
    y = np.arange(len(rob))
    ax_rob.errorbar(
        rob["bacc"],
        y,
        xerr=[rob["bacc"] - rob["ci_low"], rob["ci_high"] - rob["bacc"]],
        fmt="o",
        color=PRIMARY,
        ecolor=BLACK,
        ms=4.5,
        capsize=2.5,
        elinewidth=0.9,
    )
    chance_vline(ax_rob)
    ax_rob.axvline(prim_m, color=GRAY, ls=":", lw=0.8)
    ax_rob.set_yticks(y)
    ax_rob.set_yticklabels([f"{r.analysis} (N={r.n})" for r in rob.itertuples()], fontsize=7)
    ax_rob.invert_yaxis()
    ax_rob.set_xlabel("BAcc")
    ax_rob.set_xlim(0.58, 0.65)
    ax_rob.set_title("Sensitivity estimates", loc="left")

    ax_e08 = axes[1]
    panel_label(ax_e08, "B")
    x = np.arange(len(pairs))
    w = 0.35
    ax_e08.bar(x - w / 2, pairs["precue_beta_me_uv2"], width=w, color=ME, edgecolor=BLACK, lw=0.3, label="ME")
    ax_e08.bar(x + w / 2, pairs["precue_beta_mi_uv2"], width=w, color=MI, edgecolor=BLACK, lw=0.3, label="MI")
    ax_e08.set_xticks(x)
    ax_e08.set_xticklabels(pairs["pair_id"], fontsize=7)
    ax_e08.set_ylabel("Pre-cue β (µV²)")
    ax_e08.legend(frameon=False, fontsize=7, loc="upper right", ncol=2)
    ax_e08.set_title("Protocol-state diagnostic", loc="left")

    fig.tight_layout(w_pad=1.4)
    save_figure(fig, "Figure_5_Robustness_Protocol", main=True)


# ---------------------------------------------------------------------------
# Supplementary
# ---------------------------------------------------------------------------


def figure_s1() -> None:
    el = pd.read_csv(QC / "participant_eligibility.csv")
    n_all = len(el)
    n_prim = int(el["eligible_primary"].sum()) if "eligible_primary" in el.columns else int(el.iloc[:, -1].sum())
    export_json("Figure_S1_source.json", {"n_audited": n_all, "n_primary": n_prim})
    fig, ax = plt.subplots(figsize=(3.5, 3.2))
    ax.axis("off")
    for y, lab in ((0.75, f"Audited\nN={n_all}"), (0.45, f"Primary eligible\nN={n_prim}"), (0.15, "Primary E01\nnested CV")):
        ax.add_patch(mpatches.FancyBboxPatch((0.2, y), 0.6, 0.18, transform=ax.transAxes, boxstyle="round,pad=0.02", fc="white", ec=BLACK, lw=0.7))
        ax.text(0.5, y + 0.09, lab, transform=ax.transAxes, ha="center", va="center", fontsize=8)
    ax.annotate("", xy=(0.5, 0.63), xytext=(0.5, 0.75), xycoords=ax.transAxes, arrowprops=dict(arrowstyle="->", color=BLACK))
    ax.annotate("", xy=(0.5, 0.33), xytext=(0.5, 0.45), xycoords=ax.transAxes, arrowprops=dict(arrowstyle="->", color=BLACK))
    ax.set_title("Cohort eligibility", fontsize=9)
    save_figure(fig, "Figure_S1_Cohort_Eligibility", main=False)


def figure_s2_secondary_table() -> None:
    s = load_json(E01 / "erd_lr/summary.json")
    rows = [
        {"metric": "BAcc (primary)", "value": s["balanced_accuracy"], "role": "primary"},
        {"metric": "ROC-AUC", "value": s["roc_auc"], "role": "secondary"},
        {"metric": "Macro-F1", "value": s["macro_f1"], "role": "secondary"},
        {"metric": "Sensitivity", "value": s["sensitivity"], "role": "secondary"},
        {"metric": "Specificity", "value": s["specificity"], "role": "secondary"},
        {"metric": "Average precision", "value": s["average_precision"], "role": "secondary"},
        {"metric": "MCC", "value": s["mcc"], "role": "secondary"},
        {"metric": "Accuracy", "value": s["accuracy"], "role": "secondary"},
    ]
    df = pd.DataFrame(rows)
    export_csv("Figure_S2_source.csv", df)
    # Prefer table recommendation — still export compact visual
    fig, ax = plt.subplots(figsize=(5.5, 2.6))
    ax.axis("off")
    disp = df.copy()
    disp["value"] = disp["value"].map(lambda v: f"{v:.3f}")
    tbl = ax.table(cellText=disp[["metric", "value", "role"]].values, colLabels=["Metric", "Value", "Role"], loc="center", cellLoc="center")
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(8)
    tbl.scale(1.1, 1.35)
    ax.set_title("Secondary metrics (prefer Table 2)", fontsize=9, pad=8)
    save_figure(fig, "Figure_S2_Secondary_Metrics", main=False)


def figure_s3_movement() -> None:
    keys = ["left_fist", "right_fist", "both_fists", "both_feet", "unilateral", "bilateral"]
    titles = ["Left fist", "Right fist", "Both fists", "Both feet", "Unilateral", "Bilateral"]
    rows = []
    fig, axes = plt.subplots(2, 3, figsize=(7.2, 4.6), sharex=True, sharey=True)
    for ax, key, title in zip(axes.ravel(), keys, titles):
        pm = pd.read_csv(E02 / key / "participant_metrics.csv")
        m, lo, hi = boot_ci(E02 / key / "bootstrap_summary.csv")
        n = int(load_json(E02 / key / "summary.json")["n_participants"])
        rows.append({"movement": key, "n": n, "bacc": m, "ci_low": lo, "ci_high": hi})
        export_csv(f"Figure_S3_{key}_source.csv", pm[["subject", "balanced_accuracy"]])
        parts = ax.violinplot(pm["balanced_accuracy"], positions=[0], showextrema=False, widths=0.7)
        for b in parts["bodies"]:
            b.set_facecolor(PRIMARY)
            b.set_alpha(0.25)
        ax.scatter(np.zeros(len(pm)), pm["balanced_accuracy"], s=6, c=PRIMARY, alpha=0.4, edgecolors="none")
        ax.errorbar(0.35, m, yerr=[[m - lo], [hi - m]], fmt="o", color=BLACK, ms=4, capsize=2)
        chance_hline(ax)
        ax.set_xticks([])
        ax.set_title(f"{title} (N={n})", fontsize=8)
        ax.set_ylim(0.35, 0.95)
    for ax in axes[:, 0]:
        ax.set_ylabel("BAcc")
    export_csv("Figure_S3_summary.csv", pd.DataFrame(rows))
    fig.suptitle("Movement-specific decoding", fontsize=9, y=1.01)
    fig.tight_layout()
    save_figure(fig, "Figure_S3_Movement_Decoding", main=False)


def figure_s4_channels() -> None:
    ch = pd.read_csv(E03 / "channel_summary_fdr.csv")
    export_csv("Figure_S4_source.csv", ch)
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 4.2))
    for ax, band, col in zip(axes, ["mu", "beta"], [MU, BETA]):
        sub = ch.loc[ch.band == band].sort_values("mean")
        ax.errorbar(
            sub["mean"],
            np.arange(len(sub)),
            xerr=[
                sub["mean"] - sub["mean_bootstrap_ci_low"],
                sub["mean_bootstrap_ci_high"] - sub["mean"],
            ],
            fmt="o",
            color=col,
            ms=3.5,
            capsize=1.5,
            elinewidth=0.7,
        )
        ax.axvline(0, color=CHANCE, ls="--", lw=0.8)
        ax.set_yticks(np.arange(len(sub)))
        ax.set_yticklabels(sub["channel"], fontsize=6)
        ax.set_xlabel("ME − MI (dB)")
        ax.set_title(band)
    fig.suptitle("Channel-level ERD", fontsize=9, y=1.01)
    fig.tight_layout()
    save_figure(fig, "Figure_S4_Channel_ERD", main=False)


def figure_s5_laterality() -> None:
    lat = pd.read_csv(E03 / "laterality.csv")
    export_csv("Figure_S5_source.csv", lat)
    fig, axes = plt.subplots(1, 2, figsize=(6.5, 3.2), sharey=True)
    for ax, band in zip(axes, ["mu", "beta"]):
        sub = lat.loc[lat.band == band]
        data = [sub.loc[sub.movement == g, "laterality_me_minus_mi"].to_numpy() for g in ["left_fist", "right_fist"]]
        parts = ax.violinplot(data, positions=[0, 1], showmeans=True, showextrema=False, widths=0.7)
        for b in parts["bodies"]:
            b.set_facecolor(NULL)
            b.set_alpha(0.3)
        ax.axhline(0, color=CHANCE, ls="--", lw=0.8)
        ax.set_xticks([0, 1])
        ax.set_xticklabels(["Left fist", "Right fist"])
        ax.set_title(band)
    axes[0].set_ylabel("Laterality (ME − MI)")
    fig.suptitle("Laterality (secondary)", fontsize=9, y=1.02)
    fig.tight_layout()
    save_figure(fig, "Figure_S5_Laterality", main=False)


def figure_s6_heterogeneity() -> None:
    pm = pd.read_csv(E01 / "erd_lr/participant_metrics.csv").sort_values("balanced_accuracy")
    ranks = pd.read_csv(REV / "e04_participant_ranks.csv") if (REV / "e04_participant_ranks.csv").exists() else pm.assign(rank=np.arange(1, len(pm) + 1))
    corr = pd.read_csv(REV / "e04_exploratory_correlations_copy.csv") if (REV / "e04_exploratory_correlations_copy.csv").exists() else None
    export_csv("Figure_S6_ranks.csv", ranks)
    if corr is not None:
        export_csv("Figure_S6_correlations.csv", corr)
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 3.2))
    ax = axes[0]
    ax.plot(np.arange(1, len(pm) + 1), pm["balanced_accuracy"], color=PRIMARY, lw=1.0)
    chance_hline(ax)
    ax.set_xlabel("Rank")
    ax.set_ylabel("BAcc")
    ax.set_title("Participant ranks (exploratory)")
    ax = axes[1]
    ax.axis("off")
    if corr is not None:
        ax.text(0.01, 0.99, "Exploratory correlations (frozen):\n\n" + corr.to_string(index=False), va="top", family="monospace", fontsize=6.5)
    fig.suptitle("Participant heterogeneity — EXPLORATORY", fontsize=9, y=1.02)
    fig.tight_layout()
    save_figure(fig, "Figure_S6_Participant_Heterogeneity", main=False)


def figure_s7_artifact() -> None:
    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.8), sharey=True)
    for ax, key, title in zip(axes, ["none", "150uv", "200uv"], ["No rejection", "150 µV", "200 µV"]):
        pm = pd.read_csv(E05 / f"artifact_sensitivity/{key}/participant_metrics.csv")
        m, lo, hi = boot_ci(E05 / f"artifact_sensitivity/{key}/bootstrap_summary.csv")
        n = int(load_json(E05 / f"artifact_sensitivity/{key}/summary.json")["n_participants"])
        export_csv(f"Figure_S7_{key}_source.csv", pm[["subject", "balanced_accuracy"]])
        parts = ax.violinplot(pm["balanced_accuracy"], positions=[0], showextrema=False, widths=0.7)
        for b in parts["bodies"]:
            b.set_facecolor(PRIMARY)
            b.set_alpha(0.25)
        ax.scatter(np.zeros(len(pm)), pm["balanced_accuracy"], s=6, c=PRIMARY, alpha=0.4, edgecolors="none")
        ax.errorbar(0.35, m, yerr=[[m - lo], [hi - m]], fmt="o", color=BLACK, ms=4, capsize=2)
        chance_hline(ax)
        ax.set_xticks([])
        ax.set_title(f"{title}\nN={n}, {m:.3f}", fontsize=8)
        ax.set_ylim(0.35, 0.95)
    axes[0].set_ylabel("BAcc")
    fig.suptitle("Artifact-threshold sensitivity", fontsize=9, y=1.05)
    fig.tight_layout()
    save_figure(fig, "Figure_S7_Artifact_Sensitivity", main=False)


def figure_s8_rejection() -> None:
    rej = load_json(SENS / "rejection_audit/rejection_audit_summary.json")
    part = pd.read_csv(SENS / "rejection_audit/participant_paired_rejection_differences.csv")
    export_json("Figure_S8_summary.json", rej)
    export_csv("Figure_S8_participant_delta.csv", part)
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 3.0))
    ax = axes[0]
    me = rej["primary_cohort"]["ME"]
    mi = rej["primary_cohort"]["MI"]
    ax.scatter([0, 1], [me["rejection_proportion"] * 100, mi["rejection_proportion"] * 100], s=50, c=[ME, MI], edgecolors=BLACK, zorder=3)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["ME", "MI"])
    ax.set_ylabel("Rejection (%)")
    ax.set_xlim(-0.5, 1.5)
    ax.set_title("Aggregate rejection")
    ax.text(
        0.98,
        0.95,
        f"retained {me['epochs_retained']}/{mi['epochs_retained']}",
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=6.5,
    )
    ax = axes[1]
    # find delta column
    dcol = [c for c in part.columns if "diff" in c.lower() or "minus" in c.lower()][0]
    d = part[dcol].to_numpy() * (100 if part[dcol].abs().max() < 1 else 1)
    parts = ax.violinplot(d, positions=[0], showextrema=False, widths=0.7)
    for b in parts["bodies"]:
        b.set_facecolor(PRIMARY)
        b.set_alpha(0.25)
    ax.scatter(np.zeros(len(d)), d, s=8, c=PRIMARY, alpha=0.45, edgecolors="none")
    pp = rej["participant_paired"]
    ax.errorbar(
        0.35,
        pp["mean_me_minus_mi"] * 100,
        yerr=[
            [pp["mean_me_minus_mi"] * 100 - pp["bootstrap_ci_low"] * 100],
            [pp["bootstrap_ci_high"] * 100 - pp["mean_me_minus_mi"] * 100],
        ],
        fmt="o",
        color=BLACK,
        ms=4,
        capsize=2,
    )
    ax.axhline(0, color=CHANCE, ls="--", lw=0.8)
    ax.set_xticks([])
    ax.set_ylabel("ME − MI rejection (pp)")
    ax.set_title("Participant paired Δ")
    fig.suptitle("Label-specific rejection audit", fontsize=9, y=1.02)
    fig.tight_layout()
    save_figure(fig, "Figure_S8_Rejection_Audit", main=False)


def figure_s9_e08() -> None:
    by_run = pd.read_csv(REV / "e08_by_run.csv").copy()
    by_run["precue_beta_uv2"] = by_run["precue_beta_mean"] * V2_TO_UV2
    by_run["precue_mu_uv2"] = by_run["precue_mu_mean"] * V2_TO_UV2
    export_csv("Figure_S9_source.csv", by_run)
    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.8))
    for ax, col, ylab, title in zip(
        axes,
        ["precue_mu_uv2", "precue_beta_uv2", "ptp_mean"],
        ["µV²", "µV²", "µV"],
        ["Pre-cue μ", "Pre-cue β", "PTP"],
    ):
        for cond, color, lab in [("execution", ME, "ME"), ("imagery", MI, "MI")]:
            sub = by_run.loc[by_run["condition"] == cond]
            ax.plot(sub["run"], sub[col], "o-", color=color, label=lab, ms=3.5, lw=1)
        ax.set_title(title)
        ax.set_xlabel("Run")
        ax.set_ylabel(ylab)
        ax.legend(frameon=False, fontsize=6)
    fig.suptitle("E08 protocol/run-state diagnostics", fontsize=9, y=1.05)
    fig.tight_layout()
    save_figure(fig, "Figure_S9_E08_Diagnostics", main=False)


def figure_s10_sampling_duration() -> None:
    samp = load_json(SENS / "sampling_rate/sampling_rate_sensitivity_summary.json")
    pm = pd.read_csv(SENS / "sampling_rate/participant_metrics.csv")
    sens = pd.read_csv(REV / "sensitivity_summary.csv")
    export_json("Figure_S10_sampling.json", samp)
    export_csv("Figure_S10_sampling_participants.csv", pm[["subject", "balanced_accuracy"]])
    fig, axes = plt.subplots(1, 2, figsize=(6.8, 2.9))
    ax = axes[0]
    rows = []
    for analysis, label in [("E01_primary", "Primary"), ("E06_first60", "First 60 s"), ("E06_all_events", "All events")]:
        r = sens.loc[sens.analysis == analysis].iloc[0]
        rows.append((label, float(r.bacc), float(r.ci_low), float(r.ci_high), int(r.n)))
    rows.append(("Sampling-rate", samp["sensitivity_bacc"], samp["sensitivity_ci"][0], samp["sensitivity_ci"][1], samp["sensitivity_n"]))
    y = np.arange(len(rows))
    ax.errorbar(
        [r[1] for r in rows],
        y,
        xerr=[[r[1] - r[2] for r in rows], [r[3] - r[1] for r in rows]],
        fmt="o",
        color=PRIMARY,
        ecolor=BLACK,
        ms=4,
        capsize=2,
    )
    chance_vline(ax)
    ax.set_yticks(y)
    ax.set_yticklabels([f"{r[0]} (N={r[4]})" for r in rows], fontsize=7)
    ax.set_xlabel("BAcc")
    ax.set_title("Duration / sampling-rate")
    ax = axes[1]
    parts = ax.violinplot(pm["balanced_accuracy"], positions=[0], showextrema=False, widths=0.7)
    for b in parts["bodies"]:
        b.set_facecolor(CONTROL)
        b.set_alpha(0.3)
    ax.scatter(np.zeros(len(pm)), pm["balanced_accuracy"], s=6, c=CONTROL, alpha=0.4, edgecolors="none")
    chance_hline(ax)
    ax.set_xticks([])
    ax.set_ylabel("BAcc")
    ax.set_title(f"Sampling-rate cohort (N={samp['sensitivity_n']})")
    fig.tight_layout()
    save_figure(fig, "Figure_S10_Sampling_Duration", main=False)


def figure_s11_comparators() -> None:
    fig, axes = plt.subplots(1, 4, figsize=(7.2, 2.6), sharey=True)
    for ax, key, title, color in zip(
        axes,
        ["dummy", "csp_lda", "tangent_lr", "erd_lr"],
        ["Dummy", "CSP-LDA", "Riemannian-LR", "ERD-LR"],
        [NEUTRAL, CONTROL, CONTROL, PRIMARY],
    ):
        pm = pd.read_csv(E01 / f"{key}/participant_metrics.csv")
        export_csv(f"Figure_S11_{key}_source.csv", pm[["subject", "balanced_accuracy"]])
        ax.hist(pm["balanced_accuracy"], bins=18, color=color, edgecolor="white", lw=0.3)
        chance_vline(ax) if False else ax.axvline(0.5, color=CHANCE, ls="--", lw=0.8)
        ax.set_title(title, fontsize=8)
        ax.set_xlabel("BAcc")
    axes[0].set_ylabel("Count")
    fig.suptitle("Comparator participant distributions", fontsize=9, y=1.05)
    fig.tight_layout()
    save_figure(fig, "Figure_S11_Comparator_Distributions", main=False)


def make_contact_sheet() -> None:
    from matplotlib.backends.backend_pdf import PdfPages
    from PIL import Image

    pngs = sorted((ROOT / "figures_v2/main").glob("Figure_*.png")) + sorted(
        (ROOT / "figures_v2/supplementary").glob("Figure_*.png")
    )
    FIG_PREV.mkdir(parents=True, exist_ok=True)
    out_pdf = FIG_PREV / "publication_figures_v2_contact_sheet.pdf"
    out_png = FIG_PREV / "publication_figures_v2_contact_sheet.png"
    pages = []
    with PdfPages(out_pdf) as pdf:
        for i in range(0, len(pngs), 4):
            chunk = pngs[i : i + 4]
            fig, axes = plt.subplots(2, 2, figsize=(11, 8.5))
            for ax in axes.ravel():
                ax.axis("off")
            for ax, p in zip(axes.ravel(), chunk):
                ax.imshow(Image.open(p))
                ax.set_title(p.stem, fontsize=8)
                ax.axis("off")
            fig.tight_layout()
            pdf.savefig(fig)
            pages.append(fig)
            # keep last page for png overview of first page only after loop
            if i == 0:
                fig.savefig(out_png, dpi=200, bbox_inches="tight")
            plt.close(fig)


def main() -> int:
    apply_style()
    print("Figure 1...")
    figure_1()
    print("Figure 2...")
    figure_2()
    print("Figure 3...")
    figure_3()
    print("Figure 4...")
    figure_4()
    print("Figure 5...")
    figure_5()
    print("Supplementary...")
    figure_s1()
    figure_s2_secondary_table()
    figure_s3_movement()
    figure_s4_channels()
    figure_s5_laterality()
    figure_s6_heterogeneity()
    figure_s7_artifact()
    figure_s8_rejection()
    figure_s9_e08()
    figure_s10_sampling_duration()
    figure_s11_comparators()
    print("Contact sheet...")
    make_contact_sheet()
    print("DONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
