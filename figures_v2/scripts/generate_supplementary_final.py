#!/usr/bin/env python3
"""Final supplementary figure cleanup (publication candidate).

- Does not rerun scientific analyses.
- Copies approved V2 supplementary figures exactly where required.
- Redesigns only S1 / heterogeneity / rejection labels / S10.
- Writes to figures_v2/supplementary_final/ with final numbering.

Entry: PYTHONPATH=src python figures_v2/scripts/generate_supplementary_final.py
"""

from __future__ import annotations

import json
import shutil
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

from paths import E01, E05, QC, REV, SENS, load_json  # noqa: E402
from style import (  # noqa: E402
    BLACK,
    CHANCE,
    CONTROL,
    GRAY,
    LIGHT,
    ME,
    MI,
    NEUTRAL,
    PRIMARY,
    apply_style,
    chance_hline,
    panel_label,
)

OUT = ROOT / "figures_v2" / "supplementary_final"
SRC_OLD = ROOT / "figures_v2" / "supplementary"
SRC_DATA = ROOT / "figures_v2" / "source_data" / "supplementary_final"
PREV = ROOT / "figures_v2" / "previews"
V2_TO_UV2 = 1e12

# Old V2 stem → final S number (approved exact copies)
APPROVED_COPY = {
    "Figure_S3_Movement_Decoding": "Figure_S2_Movement_Decoding",
    "Figure_S4_Channel_ERD": "Figure_S3_Channel_ERD",
    "Figure_S5_Laterality": "Figure_S4_Laterality",
    "Figure_S7_Artifact_Sensitivity": "Figure_S6_Artifact_Sensitivity",
    "Figure_S9_E08_Diagnostics": "Figure_S8_E08_Diagnostics",
    "Figure_S11_Comparator_Distributions": "Figure_S9_Comparator_Distributions",
}


def save_final(fig: plt.Figure, stem: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for ext, dpi in (("pdf", None), ("svg", None), ("png", 300)):
        kwargs = {"bbox_inches": "tight", "pad_inches": 0.05}
        if dpi is not None:
            kwargs["dpi"] = dpi
        fig.savefig(OUT / f"{stem}.{ext}", **kwargs)
    plt.close(fig)


def export_csv(name: str, df: pd.DataFrame) -> None:
    SRC_DATA.mkdir(parents=True, exist_ok=True)
    df.to_csv(SRC_DATA / name, index=False)


def export_json(name: str, obj: dict) -> None:
    SRC_DATA.mkdir(parents=True, exist_ok=True)
    (SRC_DATA / name).write_text(json.dumps(obj, indent=2) + "\n")


def copy_approved() -> list[tuple[str, str]]:
    mapping = []
    for old_stem, new_stem in APPROVED_COPY.items():
        for ext in ("pdf", "svg", "png"):
            src = SRC_OLD / f"{old_stem}.{ext}"
            dst = OUT / f"{new_stem}.{ext}"
            if not src.exists():
                raise FileNotFoundError(src)
            shutil.copy2(src, dst)
        mapping.append((old_stem, new_stem))
    return mapping


# ---------------------------------------------------------------------------
# Final S1 — eligibility / QC flow
# ---------------------------------------------------------------------------


def figure_s1_eligibility() -> None:
    el = pd.read_csv(QC / "participant_eligibility.csv")
    n_aud = len(el)
    n_prim = int(el["eligible_primary"].sum())
    n_strict = int(el["eligible_strict"].sum())
    samp = load_json(SENS / "sampling_rate/sampling_rate_sensitivity_summary.json")
    n_samp = int(samp["sensitivity_n"])

    inelig = el.loc[~el["eligible_primary"]].copy()
    # Aggregate frozen reason_codes into reader-facing categories
    reason_map = {
        "NO_EPOCHS": "No retained epochs after preprocessing",
        "INSUFFICIENT_ME_EPOCHS": "Insufficient ME epochs after rejection",
        "INSUFFICIENT_MI_EPOCHS": "Insufficient MI epochs after rejection",
        "INSUFFICIENT_MATCHED_PAIRS": "Insufficient matched ME/MI pairs",
        "MISSING_UNILATERAL_PAIR": "No usable unilateral matched pair",
        "MOVEMENT_COMPOSITION": "Movement composition incomplete across modes",
    }
    # Count primary reason family per subject (first/highest-level code grouping)
    rows = []
    for _, r in inelig.iterrows():
        codes = [c for c in str(r["reason_codes"]).split("|") if c and c != "ELIGIBLE"]
        label = " / ".join(reason_map.get(c, c.replace("_", " ").title()) for c in codes)
        rows.append({"subject": int(r["subject"]), "reason_codes": r["reason_codes"], "reason_label": label, "reason_detail": r["reason_detail"]})
    reason_df = pd.DataFrame(rows)
    # Collapse identical label groups for flow counts
    counts = reason_df.groupby("reason_label", as_index=False).size().rename(columns={"size": "n"})

    export_csv("Figure_S1_ineligible.csv", reason_df)
    export_csv("Figure_S1_reason_counts.csv", counts)
    export_json(
        "Figure_S1_summary.json",
        {
            "n_audited": n_aud,
            "n_primary": n_prim,
            "n_ineligible": int(len(inelig)),
            "n_strict": n_strict,
            "n_sampling_rate": n_samp,
            "excluded_128hz_subjects": samp.get("excluded_subjects"),
        },
    )

    fig = plt.figure(figsize=(7.2, 6.4))
    ax = fig.add_subplot(111)
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 14)
    ax.axis("off")
    ax.set_title("Cohort eligibility and sensitivity subsets", loc="left", fontsize=10)

    def box(x, y, w, h, text, fc="white"):
        ax.add_patch(mpatches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02", fc=fc, ec=BLACK, lw=0.7))
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=7.5)

    box(3.0, 12.4, 4.0, 1.1, f"Audited participants\nN = {n_aud}", fc=LIGHT)
    ax.annotate("", xy=(5, 11.55), xytext=(5, 12.35), arrowprops=dict(arrowstyle="->", color=BLACK, lw=0.9))
    box(2.5, 10.1, 5.0, 1.25, "Primary eligibility\n(matched ME/MI pairs + epoch minima)", fc="white")
    ax.annotate("", xy=(5, 9.2), xytext=(5, 10.05), arrowprops=dict(arrowstyle="->", color=BLACK, lw=0.9))
    box(2.5, 7.7, 5.0, 1.3, f"Primary E01 cohort\nN = {n_prim}", fc="#E8F5E9")

    # Ineligible branch (right)
    ax.annotate("", xy=(8.2, 10.7), xytext=(7.5, 10.7), arrowprops=dict(arrowstyle="->", color=GRAY, lw=0.8))
    box(8.25, 10.0, 1.55, 1.4, f"Ineligible\nN = {len(inelig)}", fc="#FFF3E0")

    # Sensitivity subsets
    ax.annotate("", xy=(2.8, 6.7), xytext=(4.0, 7.65), arrowprops=dict(arrowstyle="->", color=BLACK, lw=0.8))
    ax.annotate("", xy=(7.2, 6.7), xytext=(6.0, 7.65), arrowprops=dict(arrowstyle="->", color=BLACK, lw=0.8))
    box(1.0, 5.1, 3.5, 1.4, f"Strict sensitivity cohort\nN = {n_strict}\n(stricter cell rules)", fc="#E3F2FD")
    box(5.5, 5.1, 3.7, 1.4, f"Sampling-rate sensitivity\nN = {n_samp}\n(excl. S088/S092/S100)", fc="#E3F2FD")

    # Reason breakdown below (no overlap)
    ax.text(0.3, 4.4, "Ineligibility reasons (frozen reason codes):", fontsize=7.5, fontweight="bold")
    y = 4.0
    for _, r in counts.sort_values("n", ascending=False).iterrows():
        label = r["reason_label"]
        if len(label) > 95:
            label = label[:92] + "…"
        ax.text(0.35, y, f"• n={int(r['n'])}: {label}", fontsize=6.3, va="top")
        y -= 0.55
    ax.text(
        5,
        0.35,
        "Counts/reasons from frozen participant_eligibility.csv and sampling-rate summary.",
        ha="center",
        fontsize=6.5,
        style="italic",
        color=GRAY,
    )
    save_final(fig, "Figure_S1_Cohort_Eligibility")


# ---------------------------------------------------------------------------
# Final S5 — participant heterogeneity (redesigned)
# ---------------------------------------------------------------------------


def figure_s5_heterogeneity() -> None:
    het = pd.read_csv(ROOT / "results/definitive/full/e04/participant_heterogeneity.csv")
    corr = pd.read_csv(REV / "e04_exploratory_correlations_copy.csv")
    rho_erd = float(corr.loc[corr.predictor == "mean_abs_erd", "spearman_rho"].iloc[0])
    p_erd = float(corr.loc[corr.predictor == "mean_abs_erd", "p_uncorrected"].iloc[0])
    rho_n = float(corr.loc[corr.predictor == "n_epochs_erd", "spearman_rho"].iloc[0])
    p_n = float(corr.loc[corr.predictor == "n_epochs_erd", "p_uncorrected"].iloc[0])

    export_csv("Figure_S5_heterogeneity_source.csv", het[["subject", "balanced_accuracy", "mean_abs_erd", "n_epochs", "rank"]])
    export_json(
        "Figure_S5_correlations.json",
        {
            "mean_abs_erd_vs_bacc": {"spearman_rho": rho_erd, "p_uncorrected": p_erd},
            "n_epochs_vs_bacc": {"spearman_rho": rho_n, "p_uncorrected": p_n},
            "mean_rejection_rate_vs_bacc": "undefined_in_freeze_omitted",
            "label": "EXPLORATORY",
        },
    )

    pm = het.sort_values("balanced_accuracy")
    mean_b = float(pm["balanced_accuracy"].mean())

    fig, axes = plt.subplots(1, 3, figsize=(7.2, 3.0))
    # A ranks
    ax = axes[0]
    panel_label(ax, "A")
    ax.plot(np.arange(1, len(pm) + 1), pm["balanced_accuracy"].to_numpy(), color=PRIMARY, lw=1.1)
    ax.scatter(np.arange(1, len(pm) + 1), pm["balanced_accuracy"].to_numpy(), s=8, c=PRIMARY, alpha=0.55, edgecolors="none")
    chance_hline(ax)
    ax.axhline(mean_b, color=GRAY, ls=":", lw=0.9)
    ax.set_xlabel("Participant rank")
    ax.set_ylabel("Balanced accuracy")
    ax.set_title("Ranked performance", loc="left")
    ax.text(0.98, 0.05, f"N={len(pm)}\nmean={mean_b:.3f}", transform=ax.transAxes, ha="right", va="bottom", fontsize=6.5)

    # B ERD vs BAcc
    ax = axes[1]
    panel_label(ax, "B")
    ax.scatter(het["mean_abs_erd"], het["balanced_accuracy"], s=14, c=PRIMARY, alpha=0.55, edgecolors="none")
    chance_hline(ax)
    ax.set_xlabel("Mean absolute ERD (dB)")
    ax.set_ylabel("Balanced accuracy")
    ax.set_title("ERD magnitude vs BAcc", loc="left")
    ax.text(0.98, 0.05, f"Spearman ρ={rho_erd:.3f}", transform=ax.transAxes, ha="right", va="bottom", fontsize=6.5)

    # C epochs vs BAcc
    ax = axes[2]
    panel_label(ax, "C")
    ax.scatter(het["n_epochs"], het["balanced_accuracy"], s=14, c=CONTROL, alpha=0.55, edgecolors="none")
    chance_hline(ax)
    ax.set_xlabel("Retained epoch count")
    ax.set_ylabel("Balanced accuracy")
    ax.set_title("Epoch count vs BAcc", loc="left")
    ax.text(0.98, 0.05, f"Spearman ρ={rho_n:.3f}", transform=ax.transAxes, ha="right", va="bottom", fontsize=6.5)

    fig.suptitle("Participant heterogeneity (exploratory)", fontsize=9, y=1.02)
    fig.tight_layout()
    save_final(fig, "Figure_S5_Participant_Heterogeneity")


# ---------------------------------------------------------------------------
# Final S7 — rejection audit (label cleanup only)
# ---------------------------------------------------------------------------


def figure_s7_rejection() -> None:
    rej = load_json(SENS / "rejection_audit/rejection_audit_summary.json")
    part = pd.read_csv(SENS / "rejection_audit/participant_paired_rejection_differences.csv")
    export_json("Figure_S7_rejection_summary.json", rej)
    export_csv("Figure_S7_participant_delta.csv", part)

    me = rej["primary_cohort"]["ME"]
    mi = rej["primary_cohort"]["MI"]
    pp = rej["participant_paired"]
    dcol = [c for c in part.columns if "diff" in c.lower() or "minus" in c.lower()][0]
    d = part[dcol].to_numpy() * 100  # to percentage points

    fig, axes = plt.subplots(1, 2, figsize=(7.0, 3.1))
    ax = axes[0]
    panel_label(ax, "A")
    vals = [me["rejection_proportion"] * 100, mi["rejection_proportion"] * 100]
    ax.scatter([0, 1], vals, s=55, c=[ME, MI], edgecolors=BLACK, zorder=3)
    ax.set_xticks([0, 1])
    ax.set_xticklabels(["ME", "MI"])
    ax.set_ylabel("Rejection rate (%)")
    ax.set_xlim(-0.5, 1.5)
    ax.set_ylim(0, max(vals) * 1.45)
    ax.set_title("Aggregate rejection (primary cohort)", loc="left")
    ax.text(
        0.98,
        0.95,
        f"ME = {me['rejection_proportion']*100:.2f}%\n"
        f"MI = {mi['rejection_proportion']*100:.2f}%\n"
        f"retained {me['epochs_retained']:,} / {mi['epochs_retained']:,}",
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=6.5,
    )

    ax = axes[1]
    panel_label(ax, "B")
    parts = ax.violinplot(d, positions=[0], showextrema=False, widths=0.7)
    for b in parts["bodies"]:
        b.set_facecolor(PRIMARY)
        b.set_alpha(0.25)
    ax.scatter(np.zeros(len(d)), d, s=8, c=PRIMARY, alpha=0.45, edgecolors="none")
    mean_pp = pp["mean_me_minus_mi"] * 100
    lo_pp = pp["bootstrap_ci_low"] * 100
    hi_pp = pp["bootstrap_ci_high"] * 100
    ax.errorbar(0.35, mean_pp, yerr=[[mean_pp - lo_pp], [hi_pp - mean_pp]], fmt="o", color=BLACK, ms=4.5, capsize=2.5)
    ax.axhline(0, color=CHANCE, ls="--", lw=0.8)
    ax.set_xticks([])
    ax.set_ylabel("Rejection-rate difference, ME − MI\n(percentage points)")
    ax.set_title(f"Participant paired Δ (N={pp['n_participants']})", loc="left")
    ax.text(
        0.98,
        0.95,
        f"mean = {mean_pp:.2f} pp\n95% bootstrap CI\n[{lo_pp:.2f}, {hi_pp:.2f}] pp",
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=6.5,
    )
    fig.tight_layout()
    save_final(fig, "Figure_S7_Rejection_Audit")


# ---------------------------------------------------------------------------
# Final S10 — nonredundant duration / sampling participant-level
# ---------------------------------------------------------------------------


def figure_s10_sensitivities() -> None:
    prim = pd.read_csv(E01 / "erd_lr/participant_metrics.csv")[["subject", "balanced_accuracy"]].rename(columns={"balanced_accuracy": "bacc_primary"})
    first60 = pd.read_csv(ROOT / "results/definitive/full/e06/first60/participant_metrics.csv")[
        ["subject", "balanced_accuracy"]
    ].rename(columns={"balanced_accuracy": "bacc_first60"})
    paired60 = prim.merge(first60, on="subject", how="inner")
    paired60["delta_first60_minus_primary"] = paired60["bacc_first60"] - paired60["bacc_primary"]

    samp = pd.read_csv(SENS / "sampling_rate/paired_participant_differences.csv")
    samp_sum = load_json(SENS / "sampling_rate/paired_effect_summary.json")

    export_csv("Figure_S10_first60_paired.csv", paired60)
    export_csv("Figure_S10_sampling_paired.csv", samp)
    export_json("Figure_S10_annotations.json", {"first60_n": len(paired60), "sampling_paired": samp_sum})

    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.2))

    # A first60 paired scatter
    ax = axes[0]
    panel_label(ax, "A")
    ax.scatter(paired60["bacc_primary"], paired60["bacc_first60"], s=14, c=PRIMARY, alpha=0.55, edgecolors="none")
    lims = [0.35, 0.95]
    ax.plot(lims, lims, color=GRAY, ls="--", lw=0.8)
    ax.set_xlim(lims)
    ax.set_ylim(lims)
    ax.set_xlabel("Primary BAcc")
    ax.set_ylabel("First 60 s BAcc")
    ax.set_title(f"Duration sensitivity (paired N={len(paired60)})", loc="left")
    ax.set_aspect("equal", adjustable="box")

    # B sampling-rate paired scatter
    ax = axes[1]
    panel_label(ax, "B")
    ax.scatter(samp["bacc_primary"], samp["bacc_sens"], s=14, c=CONTROL, alpha=0.55, edgecolors="none")
    ax.plot(lims, lims, color=GRAY, ls="--", lw=0.8)
    ax.set_xlim(lims)
    ax.set_ylim(lims)
    ax.set_xlabel("Primary BAcc")
    ax.set_ylabel("Sampling-rate sensitivity BAcc")
    ax.set_title(f"Sampling-rate sensitivity (paired N={samp_sum['common_n']})", loc="left")
    ax.set_aspect("equal", adjustable="box")
    ax.text(
        0.98,
        0.05,
        f"mean Δ={samp_sum['mean_difference_sens_minus_primary']:+.4f}",
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=6.5,
    )

    fig.suptitle("Participant-level sensitivity comparisons", fontsize=9, y=1.02)
    fig.tight_layout()
    save_final(fig, "Figure_S10_Duration_Sampling_Participant")


# ---------------------------------------------------------------------------
# Table 2
# ---------------------------------------------------------------------------


def write_table_2() -> None:
    s = load_json(E01 / "erd_lr/summary.json")
    rows = [
        ("Balanced accuracy (primary endpoint)", s["balanced_accuracy"]),
        ("ROC-AUC", s["roc_auc"]),
        ("Macro-F1", s["macro_f1"]),
        ("Sensitivity", s["sensitivity"]),
        ("Specificity", s["specificity"]),
        ("Average precision", s["average_precision"]),
        ("MCC", s["mcc"]),
        ("Accuracy", s["accuracy"]),
    ]
    df = pd.DataFrame(rows, columns=["metric", "value"])
    df["n_participants"] = int(s["n_participants"])
    df["model"] = "ERD-LR"
    out_dir = ROOT / "docs" / "tables"
    out_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_dir / "table_2_secondary_metrics.csv", index=False)
    md = [
        "# Table 2. Secondary performance metrics for the primary ERD-LR model",
        "",
        f"Frozen source: `results/definitive/full/e01/erd_lr/summary.json` (N = {int(s['n_participants'])}).",
        "Values are participant-mean point estimates from the primary nested CV. No new inference.",
        "",
        "| Metric | Value |",
        "|---|---:|",
    ]
    for metric, value in rows:
        md.append(f"| {metric} | {value:.6f} |")
    (out_dir / "table_2_secondary_metrics.md").write_text("\n".join(md) + "\n")


def make_contact_sheet() -> None:
    from matplotlib.backends.backend_pdf import PdfPages
    from PIL import Image

    pngs = sorted(OUT.glob("Figure_S*.png"))
    PREV.mkdir(parents=True, exist_ok=True)
    out_pdf = PREV / "supplementary_final_contact_sheet.pdf"
    out_png = PREV / "supplementary_final_contact_sheet.png"
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
            if i == 0:
                fig.savefig(out_png, dpi=200, bbox_inches="tight")
            plt.close(fig)


def main() -> int:
    apply_style()
    OUT.mkdir(parents=True, exist_ok=True)
    # clear prior final set
    for p in OUT.glob("Figure_S*"):
        p.unlink()

    print("Copying approved figures with renumbering...")
    mapping = copy_approved()
    print("S1 eligibility...")
    figure_s1_eligibility()
    print("S5 heterogeneity...")
    figure_s5_heterogeneity()
    print("S7 rejection cleanup...")
    figure_s7_rejection()
    print("S10 participant sensitivities...")
    figure_s10_sensitivities()
    print("Table 2...")
    write_table_2()
    print("Contact sheet...")
    make_contact_sheet()

    export_json(
        "numbering_map.json",
        {
            "approved_exact_copies": {k: v for k, v in APPROVED_COPY.items()},
            "redesigned": {
                "Figure_S1_Cohort_Eligibility": "redesigned from old S1",
                "Figure_S5_Participant_Heterogeneity": "redesigned from old S6",
                "Figure_S7_Rejection_Audit": "label cleanup from old S8",
                "Figure_S10_Duration_Sampling_Participant": "redesigned from old S10 (nonredundant)",
            },
            "removed_as_figure": {"Figure_S2_Secondary_Metrics": "Table 2"},
            "mapping_notes": mapping,
        },
    )
    print("DONE →", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
