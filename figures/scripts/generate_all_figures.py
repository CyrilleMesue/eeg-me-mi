#!/usr/bin/env python3
"""Generate publication figures from frozen analysis outputs only.

Does not rerun EEG preprocessing or modeling.
Entry point: python figures/scripts/generate_all_figures.py
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
sys.path.insert(0, str(ROOT / "figures" / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

from paths import CMP, E00, E01, E02, E03, E05, E07, REV, SENS, boot_ci, load_json  # noqa: E402
from style import (  # noqa: E402
    BLACK,
    BLUE,
    CHANCE,
    CONTROL,
    FIG_SRC,
    GRAY,
    LIGHT,
    NULL,
    ORANGE,
    PRIMARY,
    PURPLE,
    SECONDARY,
    VERM,
    apply_style,
    chance_line,
    panel_label,
    save_figure,
)


def export_source(name: str, df: pd.DataFrame) -> None:
    FIG_SRC.mkdir(parents=True, exist_ok=True)
    df.to_csv(FIG_SRC / name, index=False)


def export_source_json(name: str, obj: dict) -> None:
    FIG_SRC.mkdir(parents=True, exist_ok=True)
    (FIG_SRC / name).write_text(json.dumps(obj, indent=2) + "\n")


# ---------------------------------------------------------------------------
# Figure 1 — Study design (conceptual)
# ---------------------------------------------------------------------------


def figure_1_study_design() -> None:
    fig = plt.figure(figsize=(11.5, 10.5))
    gs = GridSpec(3, 2, figure=fig, height_ratios=[1.0, 1.1, 1.0], hspace=0.45, wspace=0.35)

    # A — protocol
    ax = fig.add_subplot(gs[0, 0])
    panel_label(ax, "A")
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis("off")
    ax.set_title("EEGMMIDB matched ME→MI runs", loc="left", pad=6)
    y = 4.5
    for i, (me, mi, fam) in enumerate(
        [
            (3, 4, "L/R fist"),
            (5, 6, "both fists/feet"),
            (7, 8, "L/R fist"),
            (9, 10, "both fists/feet"),
            (11, 12, "L/R fist"),
            (13, 14, "both fists/feet"),
        ]
    ):
        x = 0.4 + i * 1.55
        ax.add_patch(mpatches.FancyBboxPatch((x, y), 0.65, 0.9, boxstyle="round,pad=0.02", fc=PRIMARY, ec=BLACK, lw=0.6))
        ax.text(x + 0.325, y + 0.45, f"ME\nR{me}", ha="center", va="center", color="white", fontsize=7, fontweight="bold")
        ax.annotate("", xy=(x + 0.85, y + 0.45), xytext=(x + 0.65, y + 0.45), arrowprops=dict(arrowstyle="->", color=GRAY, lw=1))
        ax.add_patch(mpatches.FancyBboxPatch((x + 0.9, y), 0.65, 0.9, boxstyle="round,pad=0.02", fc=SECONDARY, ec=BLACK, lw=0.6))
        ax.text(x + 1.225, y + 0.45, f"MI\nR{mi}", ha="center", va="center", color="white", fontsize=7, fontweight="bold")
        ax.text(x + 0.775, y - 0.35, fam, ha="center", va="top", fontsize=6.5, color=GRAY)
    ax.text(0.2, 2.4, "Repetitions 1–3 across matched pairs", fontsize=8, color=BLACK)
    ax.text(
        0.2,
        1.4,
        "Condition is structurally coupled to run order.\n(ME always precedes matched MI; not randomized.)",
        fontsize=8,
        color=VERM,
        style="italic",
    )

    # B — participant-disjoint CV
    ax = fig.add_subplot(gs[0, 1])
    panel_label(ax, "B")
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis("off")
    ax.set_title("Participant-disjoint nested evaluation", loc="left", pad=6)
    boxes = [
        (2.5, 5.0, "Participants (N=102)"),
        (2.5, 3.7, "Outer-train participants"),
        (2.5, 2.4, "Inner participant-disjoint C tuning"),
        (2.5, 1.1, "Held-out outer-test participants"),
    ]
    for i, (x, y, lab) in enumerate(boxes):
        ax.add_patch(mpatches.FancyBboxPatch((x, y - 0.35), 5, 0.7, boxstyle="round,pad=0.03", fc=LIGHT, ec=BLACK, lw=0.7))
        ax.text(x + 2.5, y, lab, ha="center", va="center", fontsize=8)
        if i < len(boxes) - 1:
            ax.annotate("", xy=(5, boxes[i + 1][1] + 0.35), xytext=(5, y - 0.35), arrowprops=dict(arrowstyle="->", color=BLACK, lw=1))
    ax.text(0.3, 0.25, "No participant contributes epochs to both outer train and outer test.", fontsize=7.5, color=GRAY)

    # C — temporal windows
    ax = fig.add_subplot(gs[1, :])
    panel_label(ax, "C", x=-0.02)
    ax.set_xlim(-2.2, 3.7)
    ax.set_ylim(0, 3)
    ax.set_yticks([])
    ax.set_xlabel("Time relative to cue (s)")
    ax.axvline(0, color=BLACK, lw=1.2)
    ax.text(0.05, 2.7, "cue t=0", fontsize=8)
    # excluded
    ax.axvspan(-0.8375, 0.8375, color=LIGHT, alpha=1.0, zorder=0)
    ax.text(0, 2.2, "excluded\ncue-adjacent", ha="center", fontsize=7, color=GRAY)
    # E00 / baseline
    ax.plot([-2.0, -0.8375], [1.5, 1.5], color=PRIMARY, lw=6, solid_capstyle="butt")
    ax.text(-1.42, 1.75, "E00 / E01 baseline\n[−2.0, −0.8375]", ha="center", fontsize=8, color=PRIMARY)
    # task
    ax.plot([0.8375, 3.5], [1.5, 1.5], color=SECONDARY, lw=6, solid_capstyle="butt")
    ax.text(2.15, 1.75, "E01 task\n[+0.8375, +3.5]", ha="center", fontsize=8, color=SECONDARY)
    ax.text(-2.1, 0.4, "FIR-safe temporal margins", fontsize=8, style="italic", color=BLACK)
    ax.set_title("Temporal feature definition", loc="left")

    # D — ERD pipeline
    ax = fig.add_subplot(gs[2, 0])
    panel_label(ax, "D")
    ax.axis("off")
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5)
    ax.set_title("ERD feature representation", loc="left")
    steps = [
        "21 sensorimotor channels",
        "μ 8–13 Hz + β 13–30 Hz",
        "42 ERD features",
        "Nested L2 logistic regression",
        "Participant-level OOF → mean BAcc",
    ]
    for i, s in enumerate(steps):
        y = 4.2 - i * 0.75
        ax.add_patch(mpatches.FancyBboxPatch((1.2, y - 0.28), 7.5, 0.55, boxstyle="round,pad=0.02", fc="white", ec=PRIMARY, lw=0.9))
        ax.text(5, y, s, ha="center", va="center", fontsize=8)
        if i < len(steps) - 1:
            ax.annotate("", xy=(5, y - 0.28), xytext=(5, y - 0.47), arrowprops=dict(arrowstyle="->", color=GRAY))

    # E — analysis logic
    ax = fig.add_subplot(gs[2, 1])
    panel_label(ax, "E")
    ax.axis("off")
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 5)
    ax.set_title("Analysis / control logic", loc="left")
    flow = [
        "Primary E01 (ERD-LR)",
        "Pre-cue E00 control",
        "Physiology (E03) / movements (E02)",
        "Spatial control (E05)",
        "Artifact / duration / sampling-rate",
        "Run-order diagnostics (E08)",
        "Structured permutation (E07)",
    ]
    for i, s in enumerate(flow):
        y = 4.5 - i * 0.6
        ax.text(1.0, y, "→  " + s if i else s, fontsize=8, va="center", color=BLACK if i == 0 else GRAY)

    save_figure(fig, "Figure_1_Study_Design", main=True)


# ---------------------------------------------------------------------------
# Figure 2 — Primary decoding
# ---------------------------------------------------------------------------


def figure_2_primary() -> None:
    pm = pd.read_csv(E01 / "erd_lr/participant_metrics.csv")
    mean, lo, hi = boot_ci(E01 / "erd_lr/bootstrap_summary.csv")
    e07 = load_json(E07 / "e07_summary.json")
    null = pd.read_csv(E07 / "null_statistics.csv")
    assert len(null) == 1000

    models = []
    for name, label in [
        ("dummy", "Dummy"),
        ("csp_lda", "CSP-LDA"),
        ("tangent_lr", "Riemannian-LR"),
        ("erd_lr", "ERD-LR (primary)"),
    ]:
        m, clo, chi = boot_ci(E01 / f"{name}/bootstrap_summary.csv")
        models.append({"model": label, "key": name, "bacc": m, "ci_low": clo, "ci_high": chi})
    models_df = pd.DataFrame(models)

    summary = load_json(E01 / "erd_lr/summary.json")
    secondary = pd.DataFrame(
        [
            {"metric": "BAcc (primary)", "value": summary["balanced_accuracy"], "role": "primary"},
            {"metric": "ROC-AUC", "value": summary["roc_auc"], "role": "secondary"},
            {"metric": "Macro-F1", "value": summary["macro_f1"], "role": "secondary"},
            {"metric": "Sensitivity", "value": summary["sensitivity"], "role": "secondary"},
            {"metric": "Specificity", "value": summary["specificity"], "role": "secondary"},
            {"metric": "MCC", "value": summary["mcc"], "role": "secondary"},
        ]
    )

    export_source("Figure_2A_source.csv", pm[["subject", "balanced_accuracy", "n_epochs"]])
    export_source("Figure_2B_source.csv", models_df)
    export_source("Figure_2C_source.csv", null[["perm_id", "statistic"]])
    export_source("Figure_2D_source.csv", secondary)
    export_source_json(
        "Figure_2_annotations.json",
        {
            "n": 102,
            "mean_bacc": mean,
            "ci": [lo, hi],
            "observed_e07": e07["observed_statistic"],
            "n_null_ge": e07["n_null_ge_observed"],
            "p_plusone": e07["p_value_plusone"],
        },
    )

    fig, axes = plt.subplots(2, 2, figsize=(10.5, 8.2))
    # A
    ax = axes[0, 0]
    panel_label(ax, "A")
    vals = pm["balanced_accuracy"].to_numpy()
    rng = np.random.default_rng(2026)
    x = 0.02 * rng.standard_normal(len(vals))
    parts = ax.violinplot(vals, positions=[0], showmeans=False, showmedians=False, showextrema=False, widths=0.7)
    for b in parts["bodies"]:
        b.set_facecolor(PRIMARY)
        b.set_alpha(0.25)
        b.set_edgecolor(PRIMARY)
    ax.scatter(x, vals, s=12, c=PRIMARY, alpha=0.55, edgecolors="none", zorder=3)
    ax.errorbar(0.35, mean, yerr=[[mean - lo], [hi - mean]], fmt="o", color=BLACK, ms=6, capsize=4, zorder=4)
    chance_line(ax)
    ax.set_xlim(-0.7, 0.7)
    ax.set_ylim(0.35, 0.95)
    ax.set_xticks([])
    ax.set_ylabel("Participant BAcc")
    ax.set_title("Primary E01 participant-level BAcc")
    ax.text(
        0.02,
        0.98,
        f"N=102\nmean={mean:.3f}\n95% bootstrap CI [{lo:.3f}, {hi:.3f}]",
        transform=ax.transAxes,
        va="top",
        fontsize=8,
        bbox=dict(boxstyle="round,pad=0.25", fc="white", ec=LIGHT),
    )

    # B
    ax = axes[0, 1]
    panel_label(ax, "B")
    ypos = np.arange(len(models_df))
    colors = [GRAY, "#56B4E9", CONTROL, PRIMARY]
    ax.barh(ypos, models_df["bacc"], color=colors, edgecolor=BLACK, lw=0.5, height=0.65)
    ax.errorbar(
        models_df["bacc"],
        ypos,
        xerr=[models_df["bacc"] - models_df["ci_low"], models_df["ci_high"] - models_df["bacc"]],
        fmt="none",
        ecolor=BLACK,
        capsize=3,
    )
    ax.axvline(0.5, color=CHANCE, ls="--", lw=1.0)
    ax.set_yticks(ypos)
    ax.set_yticklabels(models_df["model"])
    ax.set_xlabel("Participant-mean BAcc")
    ax.set_xlim(0.45, 0.70)
    ax.set_title("Model comparators (same nested CV)")
    ax.text(0.98, 0.05, "Not a classifier leaderboard", transform=ax.transAxes, ha="right", fontsize=7, style="italic", color=GRAY)

    # C
    ax = axes[1, 0]
    panel_label(ax, "C")
    ax.hist(null["statistic"], bins=40, color=NULL, edgecolor="white", lw=0.4)
    ax.axvline(e07["observed_statistic"], color=VERM, lw=2.0)
    ax.set_xlabel("Null participant-mean BAcc")
    ax.set_ylabel("Count (of 1000)")
    ax.set_title("E07 structured permutation null")
    ax.text(
        0.98,
        0.95,
        f"observed = {e07['observed_statistic']:.6f}\n"
        f"0/1000 null ≥ observed\n"
        f"plus-one p = {e07['p_value_plusone']:.6f}",
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=8,
        bbox=dict(boxstyle="round,pad=0.25", fc="white", ec=LIGHT),
    )

    # D
    ax = axes[1, 1]
    panel_label(ax, "D")
    y = np.arange(len(secondary))
    cols = [PRIMARY if r == "primary" else GRAY for r in secondary["role"]]
    ax.barh(y, secondary["value"], color=cols, edgecolor=BLACK, lw=0.4, height=0.65)
    ax.set_yticks(y)
    ax.set_yticklabels(secondary["metric"])
    ax.set_xlabel("Value")
    ax.set_title("Primary model secondary metrics")
    ax.text(0.98, 0.05, "BAcc = primary endpoint;\nothers descriptive", transform=ax.transAxes, ha="right", fontsize=7, style="italic", color=GRAY)

    fig.tight_layout()
    save_figure(fig, "Figure_2_Primary_Decoding", main=True)


# ---------------------------------------------------------------------------
# Figure 3 — Pre-cue vs post-cue
# ---------------------------------------------------------------------------


def figure_3_precue_postcue() -> None:
    paired = pd.read_csv(CMP / "e00_vs_e01_participant.csv")
    boot = pd.read_csv(CMP / "e00_vs_e01_bootstrap_summary.csv").iloc[0]
    sign = load_json(CMP / "e00_vs_e01_signflip.json")
    e00_m, e00_lo, e00_hi = boot_ci(E00 / "bootstrap_summary.csv")
    e01_m, e01_lo, e01_hi = boot_ci(E01 / "erd_lr/bootstrap_summary.csv")

    export_source("Figure_3B_source.csv", paired)
    export_source(
        "Figure_3C_source.csv",
        paired[["subject", "difference_e01_minus_e00"]].rename(columns={"difference_e01_minus_e00": "delta_bacc"}),
    )
    export_source_json(
        "Figure_3_annotations.json",
        {
            "e00_mean": e00_m,
            "e00_ci": [e00_lo, e00_hi],
            "e01_mean": e01_m,
            "e01_ci": [e01_lo, e01_hi],
            "mean_delta": float(boot["mean_difference"]),
            "delta_ci": [float(boot["difference_ci_low"]), float(boot["difference_ci_high"])],
            "signflip_p": sign["p_value_plusone"],
            "n": int(sign["n_participants"]),
        },
    )

    fig = plt.figure(figsize=(11, 8.5))
    gs = GridSpec(2, 2, figure=fig, hspace=0.35, wspace=0.3)

    # A timeline
    ax = fig.add_subplot(gs[0, 0])
    panel_label(ax, "A")
    ax.set_xlim(-2.2, 3.7)
    ax.set_ylim(0, 3)
    ax.set_yticks([])
    ax.axvline(0, color=BLACK, lw=1.1)
    ax.axvspan(-0.8375, 0.8375, color=LIGHT)
    ax.plot([-2.0, -0.8375], [1.8, 1.8], color=PRIMARY, lw=7, solid_capstyle="butt")
    ax.text(-1.42, 2.15, "E00: absolute μ/β power\n(FIR-safe pre-cue)", ha="center", fontsize=8, color=PRIMARY)
    ax.plot([0.8375, 3.5], [1.2, 1.2], color=SECONDARY, lw=7, solid_capstyle="butt")
    ax.text(2.15, 1.55, "E01: μ/β ERD vs baseline\n(FIR-safe post-cue)", ha="center", fontsize=8, color=SECONDARY)
    ax.set_xlabel("Time (s)")
    ax.set_title("Pre-cue vs post-cue features")

    # B paired summary (avoid spaghetti): twin distributions + mean bars
    ax = fig.add_subplot(gs[0, 1])
    panel_label(ax, "B")
    data = [paired["e00"], paired["e01"]]
    parts = ax.violinplot(data, positions=[0, 1], showextrema=False, widths=0.7)
    for i, b in enumerate(parts["bodies"]):
        b.set_facecolor([PRIMARY, SECONDARY][i])
        b.set_alpha(0.3)
    rng = np.random.default_rng(7)
    for i, col in enumerate(["e00", "e01"]):
        y = paired[col].to_numpy()
        x = i + 0.04 * rng.standard_normal(len(y))
        ax.scatter(x, y, s=8, c=[PRIMARY, SECONDARY][i], alpha=0.35, edgecolors="none")
    ax.errorbar(0, e00_m, yerr=[[e00_m - e00_lo], [e00_hi - e00_m]], fmt="o", color=BLACK, ms=6, capsize=4)
    ax.errorbar(1, e01_m, yerr=[[e01_m - e01_lo], [e01_hi - e01_m]], fmt="o", color=BLACK, ms=6, capsize=4)
    chance_line(ax)
    ax.set_xticks([0, 1])
    ax.set_xticklabels([f"E00\n{e00_m:.3f}", f"E01\n{e01_m:.3f}"])
    ax.set_ylabel("Participant BAcc")
    ax.set_ylim(0.35, 0.95)
    ax.set_title(f"Paired common N={len(paired)}")

    # C deltas
    ax = fig.add_subplot(gs[1, :])
    panel_label(ax, "C", x=-0.02)
    d = paired["difference_e01_minus_e00"].to_numpy()
    order = np.argsort(d)
    ax.axhline(0, color=CHANCE, ls="--", lw=1)
    ax.scatter(np.arange(len(d)), d[order], s=14, c=np.where(d[order] >= 0, SECONDARY, PRIMARY), alpha=0.75, edgecolors="none")
    mean_d = float(boot["mean_difference"])
    lo = float(boot["difference_ci_low"])
    hi = float(boot["difference_ci_high"])
    ax.axhline(mean_d, color=BLACK, lw=1.2)
    ax.fill_between([-2, len(d) + 2], lo, hi, color=LIGHT, alpha=0.8, zorder=0)
    ax.set_xlim(-1, len(d))
    ax.set_xlabel("Participants (sorted by ΔBAcc)")
    ax.set_ylabel("E01 − E00 BAcc")
    ax.set_title("Participant-level post-cue advantage")
    ax.text(
        0.01,
        0.97,
        f"mean Δ = {mean_d:.3f}; 95% bootstrap CI [{lo:.3f}, {hi:.3f}]\n"
        f"paired sign-flip plus-one p = {sign['p_value_plusone']:.6f}",
        transform=ax.transAxes,
        va="top",
        fontsize=8,
        bbox=dict(boxstyle="round,pad=0.25", fc="white", ec=LIGHT),
    )

    fig.tight_layout()
    save_figure(fig, "Figure_3_PreCue_PostCue", main=True)


# ---------------------------------------------------------------------------
# Figure 4 — Physiology + spatial
# ---------------------------------------------------------------------------


def _channel_xy(channels: list[str]):
    import mne

    mont = mne.channels.make_standard_montage("standard_1005")
    pos = mont.get_positions()["ch_pos"]
    xy = []
    for ch in channels:
        if ch not in pos:
            raise KeyError(ch)
        p = pos[ch]
        xy.append([p[0], p[1]])
    return np.asarray(xy, float)


def figure_4_physiology_spatial() -> None:
    from eeg_me_mi.protocol import SENSORIMOTOR_CHANNELS
    from eeg_me_mi.rois import ROI_LEFT, ROI_MIDLINE, ROI_RIGHT, SPATIAL_CONTROL_CHANNELS

    roi = pd.read_csv(E03 / "roi_summary.csv")
    ch = pd.read_csv(E03 / "channel_summary_fdr.csv")
    spat = load_json(E05 / "spatial_control/paired_effect_summary.json")
    spat_boot = pd.read_csv(E05 / "spatial_control/bootstrap_summary.csv").iloc[0]
    paired = pd.read_csv(E05 / "spatial_control/paired_participant_differences.csv")
    sm_mean = float(paired["bacc_sm"].mean())
    sc_mean = float(paired["bacc_sc"].mean())

    mov_rows = []
    for key, label in [
        ("left_fist", "Left fist"),
        ("right_fist", "Right fist"),
        ("both_fists", "Both fists"),
        ("both_feet", "Both feet"),
        ("unilateral", "Unilateral"),
        ("bilateral", "Bilateral"),
    ]:
        m, lo, hi = boot_ci(E02 / key / "bootstrap_summary.csv")
        n = int(load_json(E02 / key / "summary.json")["n_participants"])
        mov_rows.append({"movement": label, "key": key, "n": n, "bacc": m, "ci_low": lo, "ci_high": hi})
    mov_df = pd.DataFrame(mov_rows)

    export_source("Figure_4B_source.csv", roi)
    export_source("Figure_4C_source.csv", ch[["band", "channel", "mean", "p_fdr", "reject_fdr"]])
    export_source("Figure_4D_source.csv", mov_df)
    export_source("Figure_4E_source.csv", paired)
    export_source_json(
        "Figure_4E_annotations.json",
        {
            "spatial_n": int(spat_boot["n_participants"]),
            "spatial_bacc": float(spat_boot["mean"]),
            "spatial_ci": [float(spat_boot["ci_low"]), float(spat_boot["ci_high"])],
            "paired_n": spat["common_n"],
            "mean_sm_minus_sc": spat["mean_difference_sm_minus_sc"],
            "paired_ci": [spat["bootstrap_ci_low"], spat["bootstrap_ci_high"]],
            "paired_sm_mean": sm_mean,
            "paired_sc_mean": sc_mean,
            "formal_p": False,
        },
    )

    fig = plt.figure(figsize=(12, 10))
    gs = GridSpec(3, 2, figure=fig, height_ratios=[1.05, 1.0, 1.0], hspace=0.4, wspace=0.3)

    # A map
    ax = fig.add_subplot(gs[0, 0])
    panel_label(ax, "A")
    xy = _channel_xy(list(SENSORIMOTOR_CHANNELS))
    colors = []
    for c in SENSORIMOTOR_CHANNELS:
        if c in ROI_LEFT:
            colors.append(PRIMARY)
        elif c in ROI_RIGHT:
            colors.append(SECONDARY)
        elif c in ROI_MIDLINE:
            colors.append(CONTROL)
        else:
            colors.append(GRAY)
    ax.scatter(xy[:, 0], xy[:, 1], c=colors, s=55, edgecolors=BLACK, lw=0.5, zorder=3)
    # head outline
    circle = plt.Circle((0, 0), 0.12, fill=False, color=GRAY, lw=1)
    ax.add_patch(circle)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("21 sensorimotor channels (prespecified ROIs)")
    ax.legend(
        handles=[
            mpatches.Patch(color=PRIMARY, label="Left ROI"),
            mpatches.Patch(color=CONTROL, label="Midline ROI"),
            mpatches.Patch(color=SECONDARY, label="Right ROI"),
        ],
        loc="lower center",
        ncol=3,
        frameon=False,
        fontsize=7,
    )
    ax.text(0.5, -0.05, "Scalp layout; not source localization", transform=ax.transAxes, ha="center", fontsize=7, style="italic", color=GRAY)

    # B ROI effects
    ax = fig.add_subplot(gs[0, 1])
    panel_label(ax, "B")
    order = [
        ("mu", "left_sensorimotor"),
        ("mu", "midline"),
        ("mu", "right_sensorimotor"),
        ("beta", "left_sensorimotor"),
        ("beta", "midline"),
        ("beta", "right_sensorimotor"),
    ]
    ys, means, los, his, labs = [], [], [], [], []
    for i, (band, rname) in enumerate(order):
        row = roi.loc[(roi.band == band) & (roi.roi == rname)].iloc[0]
        ys.append(i)
        means.append(float(row["mean"]))
        los.append(float(row["mean_bootstrap_ci_low"]))
        his.append(float(row["mean_bootstrap_ci_high"]))
        labs.append(f"{band} {rname.replace('_sensorimotor','')}")
        mark = "*" if bool(row["reject_fdr"]) else ""
        ax.text(float(row["mean_bootstrap_ci_high"]) + 0.05, i, mark, va="center", fontsize=10, color=BLACK)
    ax.errorbar(means, ys, xerr=[np.array(means) - np.array(los), np.array(his) - np.array(means)], fmt="o", color=PRIMARY, ms=5, capsize=3)
    ax.axvline(0, color=CHANCE, ls="--", lw=1)
    ax.set_yticks(ys)
    ax.set_yticklabels(labs)
    ax.set_xlabel("ME − MI ERD (dB); negative = stronger ME ERD")
    ax.set_title("Prespecified ROI effects (FDR *)")

    # C topomaps mu/beta
    ax1 = fig.add_subplot(gs[1, 0])
    ax2 = fig.add_subplot(gs[1, 1])
    panel_label(ax1, "C")
    panel_label(ax2, " ")
    import mne

    info = mne.create_info(list(SENSORIMOTOR_CHANNELS), 80.0, ch_types="eeg")
    info.set_montage("standard_1005", on_missing="ignore")
    for ax, band, title in ((ax1, "mu", "μ ME−MI (dB)"), (ax2, "beta", "β ME−MI (dB)")):
        sub = ch.loc[ch.band == band].set_index("channel")
        data = np.array([float(sub.loc[c, "mean"]) for c in SENSORIMOTOR_CHANNELS])
        im, _ = mne.viz.plot_topomap(data, info, axes=ax, show=False, cmap="RdBu_r", contours=0, sensors=True)
        ax.set_title(title)
    fig.colorbar(im, ax=[ax1, ax2], fraction=0.03, pad=0.02, label="ME − MI (dB)")
    ax1.text(0.5, -0.12, "Channel-level supporting maps; not cortical activation maps", transform=ax1.transAxes, ha="center", fontsize=7, style="italic", color=GRAY)

    # D movements
    ax = fig.add_subplot(gs[2, 0])
    panel_label(ax, "D")
    y = np.arange(len(mov_df))
    ax.barh(y, mov_df["bacc"], color=PRIMARY, edgecolor=BLACK, lw=0.4, height=0.65, alpha=0.85)
    ax.errorbar(mov_df["bacc"], y, xerr=[mov_df["bacc"] - mov_df["ci_low"], mov_df["ci_high"] - mov_df["bacc"]], fmt="none", ecolor=BLACK, capsize=3)
    ax.axvline(0.5, color=CHANCE, ls="--", lw=1)
    ax.set_yticks(y)
    ax.set_yticklabels([f"{r.movement} (N={r.n})" for r in mov_df.itertuples()])
    ax.set_xlabel("Participant-mean BAcc")
    ax.set_xlim(0.45, 0.70)
    ax.set_title("Movement-specific decoding")

    # E spatial control — means from frozen paired CSV; SC CI from frozen spatial bootstrap;
    # paired Δ CI from frozen paired_effect_summary (no new inference / no confirmatory p).
    ax = fig.add_subplot(gs[2, 1])
    panel_label(ax, "E")
    labels = ["Sensorimotor\n(paired N=77)", "Peripheral/\nnon-sensorimotor"]
    means = [sm_mean, sc_mean]
    ax.bar([0, 1], means, color=[PRIMARY, SECONDARY], edgecolor=BLACK, lw=0.5, width=0.65)
    # Error bar only for SC cohort mean (frozen). SM paired mean has no separate frozen CI.
    ax.errorbar(
        [1],
        [sc_mean],
        yerr=[[sc_mean - float(spat_boot["ci_low"])], [float(spat_boot["ci_high"]) - sc_mean]],
        fmt="none",
        ecolor=BLACK,
        capsize=4,
    )
    ax.axhline(0.5, color=CHANCE, ls="--", lw=1)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(labels)
    ax.set_ylabel("Participant-mean BAcc")
    ax.set_ylim(0.45, 0.70)
    ax.set_title("Spatial representation control")
    ax.text(
        0.98,
        0.05,
        f"paired N={spat['common_n']}\n"
        f"mean SM−SC Δ={spat['mean_difference_sm_minus_sc']:.3f}\n"
        f"95% CI [{spat['bootstrap_ci_low']:.3f}, {spat['bootstrap_ci_high']:.3f}]\n"
        f"(no confirmatory paired p)",
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=7,
        bbox=dict(boxstyle="round,pad=0.25", fc="white", ec=LIGHT),
    )

    fig.subplots_adjust(hspace=0.45, wspace=0.35)
    save_figure(fig, "Figure_4_Physiology_Spatial", main=True)


# ---------------------------------------------------------------------------
# Figure 5 — Robustness + protocol
# ---------------------------------------------------------------------------


def figure_5_robustness() -> None:
    thr_rows = []
    for key, label in [("none", "No rejection"), ("150uv", "150 µV"), ("200uv", "200 µV (primary)")]:
        s = load_json(E05 / f"artifact_sensitivity/{key}/summary.json")
        m, lo, hi = boot_ci(E05 / f"artifact_sensitivity/{key}/bootstrap_summary.csv")
        thr_rows.append({"threshold": label, "n": int(s["n_participants"]), "bacc": m, "ci_low": lo, "ci_high": hi})
    thr = pd.DataFrame(thr_rows)

    sens = pd.read_csv(REV / "sensitivity_summary.csv")
    samp = load_json(SENS / "sampling_rate/sampling_rate_sensitivity_summary.json")
    # build compact robustness table
    rob = [
        {"analysis": "Primary E01", "n": 102, "bacc": samp["primary_bacc"], "ci_low": samp["primary_ci"][0], "ci_high": samp["primary_ci"][1]},
    ]
    for _, r in sens.iterrows():
        if r["analysis"] == "E01_primary":
            continue
        if r["analysis"] == "E01_sampling_rate_sensitivity":
            continue
        rob.append(
            {
                "analysis": str(r["analysis"]),
                "n": int(r["n"]) if pd.notna(r["n"]) else None,
                "bacc": float(r["bacc"]) if pd.notna(r["bacc"]) else None,
                "ci_low": float(r["ci_low"]) if pd.notna(r["ci_low"]) else None,
                "ci_high": float(r["ci_high"]) if pd.notna(r["ci_high"]) else None,
            }
        )
    rob.append(
        {
            "analysis": "Sampling-rate (excl. S088/092/100)",
            "n": samp["sensitivity_n"],
            "bacc": samp["sensitivity_bacc"],
            "ci_low": samp["sensitivity_ci"][0],
            "ci_high": samp["sensitivity_ci"][1],
        }
    )
    rob_df = pd.DataFrame(rob)

    rej = load_json(SENS / "rejection_audit/rejection_audit_summary.json")
    pairs = pd.read_csv(REV / "e08_matched_pairs.csv")

    export_source("Figure_5A_source.csv", thr)
    export_source("Figure_5B_source.csv", rob_df)
    export_source_json(
        "Figure_5C_source.json",
        {
            "primary_cohort": rej["primary_cohort"],
            "participant_paired": rej["participant_paired"],
        },
    )
    export_source("Figure_5E_source.csv", pairs)

    fig = plt.figure(figsize=(12, 10))
    gs = GridSpec(3, 2, figure=fig, hspace=0.4, wspace=0.3)

    # A thresholds
    ax = fig.add_subplot(gs[0, 0])
    panel_label(ax, "A")
    x = np.arange(len(thr))
    ax.bar(x, thr["bacc"], color=[CONTROL, "#56B4E9", PRIMARY], edgecolor=BLACK, lw=0.5, width=0.65)
    ax.errorbar(x, thr["bacc"], yerr=[thr["bacc"] - thr["ci_low"], thr["ci_high"] - thr["bacc"]], fmt="none", ecolor=BLACK, capsize=4)
    ax.axhline(0.5, color=CHANCE, ls="--", lw=1)
    ax.set_xticks(x)
    ax.set_xticklabels([f"{r.threshold}\nN={r.n}" for r in thr.itertuples()], fontsize=7)
    ax.set_ylim(0.45, 0.70)
    ax.set_ylabel("Participant-mean BAcc")
    ax.set_title("Artifact-threshold sensitivity")

    # B other sensitivities
    ax = fig.add_subplot(gs[0, 1])
    panel_label(ax, "B")
    y = np.arange(len(rob_df))
    ax.barh(y, rob_df["bacc"], color=PRIMARY, edgecolor=BLACK, lw=0.4, height=0.65, alpha=0.85)
    for i, r in rob_df.iterrows():
        if pd.notna(r["ci_low"]):
            ax.plot([r["ci_low"], r["ci_high"]], [i, i], color=BLACK, lw=1)
    ax.axvline(0.5, color=CHANCE, ls="--", lw=1)
    ax.axvline(samp["primary_bacc"], color=VERM, ls=":", lw=1.2)
    ax.set_yticks(y)
    ax.set_yticklabels([f"{r.analysis} (N={r.n})" for r in rob_df.itertuples()], fontsize=7)
    ax.set_xlabel("Participant-mean BAcc")
    ax.set_xlim(0.45, 0.70)
    ax.set_title("Other sensitivity analyses")

    # C rejection
    ax = fig.add_subplot(gs[1, 0])
    panel_label(ax, "C")
    me = rej["primary_cohort"]["ME"]
    mi = rej["primary_cohort"]["MI"]
    ax.bar([0, 1], [me["rejection_proportion"] * 100, mi["rejection_proportion"] * 100], color=[PRIMARY, SECONDARY], edgecolor=BLACK, width=0.6)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["ME", "MI"])
    ax.set_ylabel("Rejection proportion (%)")
    ax.set_title("Label-specific 200 µV rejection (primary cohort)")
    pp = rej["participant_paired"]
    ax.text(
        0.98,
        0.95,
        f"retained ME={me['epochs_retained']:,}\nretained MI={mi['epochs_retained']:,}\n"
        f"epoch ME−MI rej = {rej['primary_cohort']['absolute_difference_me_minus_mi']*100:.2f} pp\n"
        f"participant mean Δ = {pp['mean_me_minus_mi']*100:.2f} pp\n"
        f"95% bootstrap CI [{pp['bootstrap_ci_low']*100:.2f}, {pp['bootstrap_ci_high']*100:.2f}] pp",
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=7,
        bbox=dict(boxstyle="round,pad=0.25", fc="white", ec=LIGHT),
    )

    # D fixed order schematic
    ax = fig.add_subplot(gs[1, 1])
    panel_label(ax, "D")
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis("off")
    ax.set_title("Fixed matched-pair run order")
    for i, row in pairs.iterrows():
        y = 5.2 - i * 0.75
        ax.add_patch(mpatches.FancyBboxPatch((1.5, y - 0.25), 2.2, 0.5, boxstyle="round,pad=0.02", fc=PRIMARY, ec=BLACK, lw=0.5))
        ax.text(2.6, y, f"ME R{int(row.me_run)}", ha="center", va="center", color="white", fontsize=8)
        ax.annotate("", xy=(4.6, y), xytext=(3.8, y), arrowprops=dict(arrowstyle="->", color=BLACK))
        ax.add_patch(mpatches.FancyBboxPatch((4.7, y - 0.25), 2.2, 0.5, boxstyle="round,pad=0.02", fc=SECONDARY, ec=BLACK, lw=0.5))
        ax.text(5.8, y, f"MI R{int(row.mi_run)}", ha="center", va="center", color="white", fontsize=8)
        ax.text(8.2, y, f"pair {row.pair_id}", va="center", fontsize=7, color=GRAY)
    ax.text(0.5, 0.3, "Diagnostic context for E08 — does not remove fixed-order confounding.", fontsize=7, style="italic", color=VERM)

    # E E08 matched pair precue beta
    ax = fig.add_subplot(gs[2, :])
    panel_label(ax, "E", x=-0.02)
    x = np.arange(len(pairs))
    w = 0.35
    ax.bar(x - w / 2, pairs["precue_beta_me"], width=w, color=PRIMARY, edgecolor=BLACK, lw=0.4, label="ME")
    ax.bar(x + w / 2, pairs["precue_beta_mi"], width=w, color=SECONDARY, edgecolor=BLACK, lw=0.4, label="MI")
    ax.set_xticks(x)
    ax.set_xticklabels([f"{p}" for p in pairs["pair_id"]])
    ax.set_ylabel("Pre-cue β power (frozen E08 mean)")
    ax.set_xlabel("Matched ME–MI pair")
    ax.set_title("Pre-cue run-state diagnostic (matched pairs)")
    ax.legend(frameon=False, loc="upper right")
    ax.text(0.01, 0.97, "Diagnostic — does not remove fixed-order confounding.", transform=ax.transAxes, va="top", fontsize=8, style="italic", color=VERM)

    fig.subplots_adjust(hspace=0.45, wspace=0.3)
    save_figure(fig, "Figure_5_Robustness_Protocol", main=True)


# ---------------------------------------------------------------------------
# Supplementary figures (selected)
# ---------------------------------------------------------------------------


def figure_s2_secondary_metrics_tablefig() -> None:
    """Compact secondary-metric table figure (values also suitable for Table 2)."""
    rows = []
    for name, label in [
        ("dummy", "Dummy"),
        ("csp_lda", "CSP-LDA"),
        ("tangent_lr", "Riemannian-LR"),
        ("erd_lr", "ERD-LR (primary)"),
    ]:
        s = load_json(E01 / f"{name}/summary.json")
        rows.append(
            {
                "model": label,
                "BAcc": s["balanced_accuracy"],
                "ROC-AUC": s["roc_auc"],
                "Macro-F1": s["macro_f1"],
                "Sensitivity": s["sensitivity"],
                "Specificity": s["specificity"],
                "MCC": s["mcc"],
                "N": int(s["n_participants"]),
            }
        )
    df = pd.DataFrame(rows)
    export_source("Figure_S2_source.csv", df)
    fig, ax = plt.subplots(figsize=(10, 2.8))
    ax.axis("off")
    disp = df.copy()
    for c in ["BAcc", "ROC-AUC", "Macro-F1", "Sensitivity", "Specificity", "MCC"]:
        disp[c] = disp[c].map(lambda v: f"{v:.3f}")
    table = ax.table(
        cellText=disp.values,
        colLabels=disp.columns,
        loc="center",
        cellLoc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(8)
    table.scale(1.05, 1.4)
    ax.set_title("Figure S2 — Full secondary metrics (descriptive; BAcc primary)", pad=12)
    save_figure(fig, "Figure_S2_Secondary_Metrics", main=False)


def figure_s6_laterality() -> None:
    lat = pd.read_csv(E03 / "laterality.csv")
    export_source("Figure_S6_source.csv", lat)
    fig, axes = plt.subplots(1, 2, figsize=(9.5, 4.0), sharey=True)
    for ax, band in zip(axes, ["mu", "beta"]):
        panel_label(ax, "A" if band == "mu" else "B")
        sub = lat.loc[lat.band == band]
        groups = ["left_fist", "right_fist"]
        data = [sub.loc[sub.movement == g, "laterality_me_minus_mi"].to_numpy() for g in groups]
        parts = ax.violinplot(data, positions=[0, 1], showmeans=True, showextrema=False, widths=0.7)
        for b in parts["bodies"]:
            b.set_facecolor(PURPLE)
            b.set_alpha(0.35)
        ax.axhline(0, color=CHANCE, ls="--", lw=1)
        ax.set_xticks([0, 1])
        ax.set_xticklabels(["Left fist", "Right fist"])
        ax.set_title(f"{band} laterality (ME − MI)")
        ax.set_ylabel("Laterality index difference" if band == "mu" else "")
    fig.suptitle("Figure S6 — Laterality (SECONDARY; heterogeneous)", y=1.02, fontsize=10)
    fig.text(0.5, -0.02, "Participant-level frozen E03 laterality; exploratory/secondary.", ha="center", fontsize=8, style="italic", color=GRAY)
    fig.tight_layout()
    save_figure(fig, "Figure_S6_Laterality", main=False)


def figure_s8_artifact_distributions() -> None:
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.6), sharey=True)
    for ax, key, title in zip(
        axes,
        ["none", "150uv", "200uv"],
        ["No rejection", "150 µV", "200 µV (primary)"],
    ):
        pm = pd.read_csv(E05 / f"artifact_sensitivity/{key}/participant_metrics.csv")
        export_source(f"Figure_S8_{key}_source.csv", pm[["subject", "balanced_accuracy"]])
        ax.hist(pm["balanced_accuracy"], bins=18, color=PRIMARY, edgecolor="white", lw=0.3)
        ax.axvline(0.5, color=CHANCE, ls="--", lw=1)
        n = int(load_json(E05 / f"artifact_sensitivity/{key}/summary.json")["n_participants"])
        ax.set_title(f"{title}\nN={n}")
        ax.set_xlabel("BAcc")
    axes[0].set_ylabel("Participants")
    fig.suptitle("Figure S8 — Artifact-threshold participant distributions", y=1.05, fontsize=10)
    fig.tight_layout()
    save_figure(fig, "Figure_S8_Artifact_Distributions", main=False)


def figure_s_secondary_and_comparators() -> None:
    # S2 secondary already partly in Fig2D; S3 comparator distributions
    fig, axes = plt.subplots(1, 4, figsize=(12, 3.8), sharey=True)
    for ax, key, title, color in zip(
        axes,
        ["dummy", "csp_lda", "tangent_lr", "erd_lr"],
        ["Dummy", "CSP-LDA", "Riemannian-LR", "ERD-LR"],
        [GRAY, "#56B4E9", CONTROL, PRIMARY],
    ):
        pm = pd.read_csv(E01 / f"{key}/participant_metrics.csv")
        export_source(f"Figure_S3_{key}_source.csv", pm[["subject", "balanced_accuracy"]])
        ax.hist(pm["balanced_accuracy"], bins=20, color=color, edgecolor="white", lw=0.3)
        ax.axvline(0.5, color=CHANCE, ls="--", lw=1)
        ax.set_title(title)
        ax.set_xlabel("BAcc")
    axes[0].set_ylabel("Participants")
    fig.suptitle("Figure S3 — Participant-level comparator distributions", y=1.02, fontsize=10)
    fig.tight_layout()
    save_figure(fig, "Figure_S3_Comparator_Distributions", main=False)


def figure_s_movement_distributions() -> None:
    fig, axes = plt.subplots(2, 3, figsize=(11, 6.5), sharex=True, sharey=True)
    keys = ["left_fist", "right_fist", "both_fists", "both_feet", "unilateral", "bilateral"]
    titles = ["Left fist", "Right fist", "Both fists", "Both feet", "Unilateral", "Bilateral"]
    for ax, key, title in zip(axes.ravel(), keys, titles):
        pm = pd.read_csv(E02 / key / "participant_metrics.csv")
        export_source(f"Figure_S4_{key}_source.csv", pm[["subject", "balanced_accuracy"]])
        ax.hist(pm["balanced_accuracy"], bins=18, color=PRIMARY, edgecolor="white", lw=0.3)
        ax.axvline(0.5, color=CHANCE, ls="--", lw=1)
        n = pm["subject"].nunique() if "subject" in pm else len(pm)
        ax.set_title(f"{title} (N={n})")
    for ax in axes[:, 0]:
        ax.set_ylabel("Count")
    for ax in axes[1, :]:
        ax.set_xlabel("BAcc")
    fig.suptitle("Figure S4 — Movement-specific participant BAcc", y=1.01, fontsize=10)
    fig.tight_layout()
    save_figure(fig, "Figure_S4_Movement_Distributions", main=False)


def figure_s_channel_fdr() -> None:
    ch = pd.read_csv(E03 / "channel_summary_fdr.csv")
    export_source("Figure_S5_source.csv", ch)
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.5))
    for ax, band in zip(axes, ["mu", "beta"]):
        sub = ch.loc[ch.band == band].sort_values("mean")
        ax.barh(sub["channel"], sub["mean"], color=PRIMARY, edgecolor=BLACK, lw=0.2, height=0.75)
        ax.axvline(0, color=CHANCE, ls="--", lw=1)
        ax.set_title(f"{band} ME−MI channel effects")
        ax.set_xlabel("Mean ME − MI (dB)")
    fig.suptitle("Figure S5 — Channel-level ERD effects (all FDR-significant in freeze)", y=1.02, fontsize=10)
    fig.tight_layout()
    save_figure(fig, "Figure_S5_Channel_ERD", main=False)


def figure_s_heterogeneity() -> None:
    pm = pd.read_csv(E01 / "erd_lr/participant_metrics.csv").sort_values("balanced_accuracy")
    ranks = pd.read_csv(REV / "e04_participant_ranks.csv") if (REV / "e04_participant_ranks.csv").exists() else pm.assign(rank=np.arange(1, len(pm) + 1))
    corr = pd.read_csv(REV / "e04_exploratory_correlations_copy.csv") if (REV / "e04_exploratory_correlations_copy.csv").exists() else None
    export_source("Figure_S7_source_ranks.csv", ranks)
    if corr is not None:
        export_source("Figure_S7_source_correlations.csv", corr)

    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    ax = axes[0]
    panel_label(ax, "A")
    ax.plot(np.arange(1, len(pm) + 1), pm["balanced_accuracy"].to_numpy(), color=PRIMARY, lw=1.2)
    ax.axhline(0.5, color=CHANCE, ls="--", lw=1)
    ax.set_xlabel("Participant rank")
    ax.set_ylabel("BAcc")
    ax.set_title("Participant heterogeneity (EXPLORATORY)")
    ax = axes[1]
    panel_label(ax, "B")
    if corr is not None and len(corr):
        ax.axis("off")
        txt = corr.to_string(index=False)
        ax.text(0.01, 0.99, "Exploratory correlations (verbatim frozen):\n\n" + txt, va="top", family="monospace", fontsize=7)
    else:
        ax.axis("off")
        ax.text(0.5, 0.5, "No exploratory correlation table found", ha="center")
    fig.suptitle("Figure S7 — Participant heterogeneity (EXPLORATORY)", y=1.02, fontsize=10)
    fig.tight_layout()
    save_figure(fig, "Figure_S7_Participant_Heterogeneity", main=False)


def figure_s_rejection_full() -> None:
    by = pd.read_csv(SENS / "rejection_audit/rejection_by_condition.csv")
    mov = pd.read_csv(SENS / "rejection_audit/rejection_by_movement_primary_cohort.csv")
    export_source("Figure_S9_condition_source.csv", by)
    export_source("Figure_S9_movement_source.csv", mov)
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    ax = axes[0]
    prim = by.loc[by.scope == "e01_primary_cohort"]
    ax.bar(prim["condition"], prim["rejection_proportion"] * 100, color=[PRIMARY, SECONDARY], edgecolor=BLACK)
    ax.set_ylabel("Rejection %")
    ax.set_title("Primary-cohort rejection by label")
    ax = axes[1]
    labels = [f"{r.movement}\n{r.condition}" for r in mov.itertuples()]
    ax.barh(np.arange(len(mov)), mov["rejection_proportion"] * 100, color=PRIMARY, edgecolor=BLACK, lw=0.3)
    ax.set_yticks(np.arange(len(mov)))
    ax.set_yticklabels(labels, fontsize=7)
    ax.set_xlabel("Rejection %")
    ax.set_title("Movement × condition (primary cohort)")
    fig.suptitle("Figure S9 — Label-specific rejection audit", y=1.02, fontsize=10)
    fig.tight_layout()
    save_figure(fig, "Figure_S9_Rejection_Audit", main=False)


def figure_s_e08_expanded() -> None:
    by_run = pd.read_csv(REV / "e08_by_run.csv")
    export_source("Figure_S10_source.csv", by_run)
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.8))
    for ax, col, title in zip(
        axes,
        ["precue_mu_mean", "precue_beta_mean", "ptp_mean"],
        ["Pre-cue μ", "Pre-cue β", "PTP"],
    ):
        for cond, color in [("execution", PRIMARY), ("imagery", SECONDARY)]:
            sub = by_run.loc[by_run["condition"] == cond]
            ax.plot(sub["run"], sub[col], "o-", color=color, label=cond, ms=4)
        ax.set_title(title)
        ax.set_xlabel("Run")
        ax.legend(frameon=False, fontsize=7)
    fig.suptitle("Figure S10 — Expanded E08 run diagnostics (diagnostic only)", y=1.05, fontsize=10)
    fig.tight_layout()
    save_figure(fig, "Figure_S10_E08_Run_Diagnostics", main=False)


def figure_s_sampling_rate() -> None:
    s = load_json(SENS / "sampling_rate/sampling_rate_sensitivity_summary.json")
    pm = pd.read_csv(SENS / "sampling_rate/participant_metrics.csv")
    export_source("Figure_S11_source_summary.csv", pm[["subject", "balanced_accuracy"]])
    export_source_json("Figure_S11_annotations.json", s)
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.8))
    ax = axes[0]
    ax.bar([0, 1], [s["primary_bacc"], s["sensitivity_bacc"]], color=[PRIMARY, CONTROL], edgecolor=BLACK, width=0.6)
    ax.errorbar(
        [0, 1],
        [s["primary_bacc"], s["sensitivity_bacc"]],
        yerr=[
            [s["primary_bacc"] - s["primary_ci"][0], s["sensitivity_bacc"] - s["sensitivity_ci"][0]],
            [s["primary_ci"][1] - s["primary_bacc"], s["sensitivity_ci"][1] - s["sensitivity_bacc"]],
        ],
        fmt="none",
        ecolor=BLACK,
        capsize=4,
    )
    ax.axhline(0.5, color=CHANCE, ls="--", lw=1)
    ax.set_xticks([0, 1])
    ax.set_xticklabels([f"Primary\nN={s['primary_n']}", f"Excl. 128 Hz\nN={s['sensitivity_n']}"])
    ax.set_ylim(0.45, 0.70)
    ax.set_ylabel("BAcc")
    ax.set_title(f"Sampling-rate sensitivity ({s['conclusion']})")
    ax = axes[1]
    ax.hist(pm["balanced_accuracy"], bins=18, color=CONTROL, edgecolor="white")
    ax.axvline(0.5, color=CHANCE, ls="--", lw=1)
    ax.set_xlabel("Participant BAcc")
    ax.set_ylabel("Count")
    ax.set_title("N=99 participant distribution")
    fig.tight_layout()
    save_figure(fig, "Figure_S11_Sampling_Rate", main=False)


def figure_s1_cohort_flow() -> None:
    """Eligibility flow from frozen eligibility file (counts only)."""
    el = pd.read_csv(ROOT / "results/definitive/full/qc/participant_eligibility.csv")
    n_all = len(el)
    n_prim = int(el["eligible_primary"].sum())
    export_source_json("Figure_S1_source.json", {"n_audited": n_all, "n_primary": n_prim})
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.axis("off")
    boxes = [
        (0.2, 0.75, f"Audited subjects\nN={n_all}"),
        (0.2, 0.45, f"Primary eligible\nN={n_prim}"),
        (0.2, 0.15, "Primary E01 nested CV\nparticipant-mean BAcc"),
    ]
    for x, y, lab in boxes:
        ax.add_patch(mpatches.FancyBboxPatch((x, y), 0.6, 0.18, transform=ax.transAxes, boxstyle="round,pad=0.02", fc=LIGHT, ec=BLACK))
        ax.text(x + 0.3, y + 0.09, lab, transform=ax.transAxes, ha="center", va="center", fontsize=9)
    ax.annotate("", xy=(0.5, 0.63), xytext=(0.5, 0.75), xycoords=ax.transAxes, arrowprops=dict(arrowstyle="->", color=BLACK))
    ax.annotate("", xy=(0.5, 0.33), xytext=(0.5, 0.45), xycoords=ax.transAxes, arrowprops=dict(arrowstyle="->", color=BLACK))
    ax.set_title("Figure S1 — Cohort / eligibility overview")
    save_figure(fig, "Figure_S1_Cohort_Eligibility", main=False)


def make_contact_sheet() -> None:
    from matplotlib.backends.backend_pdf import PdfPages
    from PIL import Image

    pngs = sorted((ROOT / "figures/main").glob("Figure_*.png")) + sorted((ROOT / "figures/supplementary").glob("Figure_*.png"))
    if not pngs:
        return
    out = ROOT / "figures/previews/publication_figures_contact_sheet.pdf"
    out.parent.mkdir(parents=True, exist_ok=True)
    with PdfPages(out) as pdf:
        for i in range(0, len(pngs), 4):
            chunk = pngs[i : i + 4]
            fig, axes = plt.subplots(2, 2, figsize=(11, 8.5))
            axes = axes.ravel()
            for ax in axes:
                ax.axis("off")
            for ax, p in zip(axes, chunk):
                im = Image.open(p)
                ax.imshow(im)
                ax.set_title(p.stem, fontsize=8)
                ax.axis("off")
            fig.tight_layout()
            pdf.savefig(fig)
            plt.close(fig)


def main() -> int:
    apply_style()
    print("Generating Figure 1...")
    figure_1_study_design()
    print("Generating Figure 2...")
    figure_2_primary()
    print("Generating Figure 3...")
    figure_3_precue_postcue()
    print("Generating Figure 4...")
    figure_4_physiology_spatial()
    print("Generating Figure 5...")
    figure_5_robustness()
    print("Generating supplementary...")
    figure_s1_cohort_flow()
    figure_s2_secondary_metrics_tablefig()
    figure_s_secondary_and_comparators()
    figure_s_movement_distributions()
    figure_s_channel_fdr()
    figure_s6_laterality()
    figure_s_heterogeneity()
    figure_s8_artifact_distributions()
    figure_s_rejection_full()
    figure_s_e08_expanded()
    figure_s_sampling_rate()
    print("Contact sheet...")
    make_contact_sheet()
    print("DONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
