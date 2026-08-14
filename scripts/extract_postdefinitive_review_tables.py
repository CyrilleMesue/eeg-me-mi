#!/usr/bin/env python3
"""Extract E03/E04/E08 and sensitivity tables from immutable definitive outputs."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


def extract_e03(full: Path, out: Path) -> None:
    roi = pd.read_csv(full / "e03" / "roi_summary.csv")
    lat = pd.read_csv(full / "e03" / "laterality.csv")
    ch = pd.read_csv(full / "e03" / "channel_summary_fdr.csv")
    mult = json.loads((full / "e03" / "multiplicity_families.json").read_text())
    # Compact review table from ROI summary
    roi.to_csv(out / "e03_review_summary.csv", index=False)
    # Significant channel counts
    if "reject_fdr" in ch.columns:
        ch.groupby([c for c in ("band", "movement", "contrast") if c in ch.columns])["reject_fdr"].sum().to_csv(
            out / "e03_significant_channel_counts.csv"
        )
    elif "p_fdr" in ch.columns:
        sig = ch["p_fdr"] < 0.05
        ch.assign(significant=sig).groupby([c for c in ("band", "movement") if c in ch.columns])[
            "significant"
        ].sum().to_csv(out / "e03_significant_channel_counts.csv")
    (out / "e03_multiplicity_families.json").write_text(json.dumps(mult, indent=2))
    lat.to_csv(out / "e03_laterality_copy.csv", index=False)

    lines = [
        "# E03 result extraction (factual)",
        "",
        f"- Source: `{full / 'e03'}` (immutable definitive).",
        f"- ROI summary rows: {len(roi)}",
        f"- Channel FDR rows: {len(ch)}",
        f"- Laterality rows: {len(lat)}",
        "",
        "## ROI summary columns",
        "",
        ", ".join(map(str, roi.columns)),
        "",
        "## Notes",
        "",
        "- `participant_effect_p2.5` / `p97.5` are participant-effect **distribution percentiles**, not CIs for the mean.",
        "- `mean_bootstrap_ci_low` / `mean_bootstrap_ci_high` are bootstrap CIs for the mean effect.",
        "- No biological conclusions in this extraction.",
        "",
        "## ROI summary (verbatim)",
        "",
        "```",
        roi.to_string(index=False),
        "```",
        "",
    ]
    Path("docs/e03_result_extraction.md").write_text("\n".join(lines) + "\n")


def extract_e04(full: Path, out: Path) -> None:
    het = pd.read_csv(full / "e04" / "participant_heterogeneity.csv")
    corr = pd.read_csv(full / "e04" / "exploratory_correlations.csv")
    # E01 BAcc distribution from definitive participant metrics
    pm = pd.read_csv(full / "e01" / "erd_lr" / "participant_metrics.csv")
    b = pm["balanced_accuracy"].to_numpy(dtype=float)
    dist = {
        "label": "EXPLORATORY",
        "n": int(len(b)),
        "median": float(np.median(b)),
        "iqr_low": float(np.quantile(b, 0.25)),
        "iqr_high": float(np.quantile(b, 0.75)),
        "min": float(np.min(b)),
        "max": float(np.max(b)),
        "proportion_above_0_5": float(np.mean(b > 0.5)),
    }
    pd.DataFrame([dist]).to_csv(out / "e04_review_summary.csv", index=False)
    corr.to_csv(out / "e04_exploratory_correlations_copy.csv", index=False)
    # ranks
    ranks = pm[["subject", "balanced_accuracy"]].sort_values("balanced_accuracy", ascending=False)
    ranks = ranks.assign(rank=np.arange(1, len(ranks) + 1))
    ranks.to_csv(out / "e04_participant_ranks.csv", index=False)

    lines = [
        "# E04 result extraction (EXPLORATORY)",
        "",
        "All E04 outputs are **EXPLORATORY**. No new hypotheses.",
        "",
        f"- N: {dist['n']}",
        f"- Median BAcc: {dist['median']:.6f}",
        f"- IQR: [{dist['iqr_low']:.6f}, {dist['iqr_high']:.6f}]",
        f"- Range: [{dist['min']:.6f}, {dist['max']:.6f}]",
        f"- Proportion > 0.5: {dist['proportion_above_0_5']:.6f}",
        f"- Exploratory correlation rows: {len(corr)} (all retained, not filtered by significance)",
        "",
    ]
    Path("docs/e04_result_extraction.md").write_text("\n".join(lines))


def extract_e08(full: Path, out: Path) -> None:
    by_run = pd.read_csv(full / "e08" / "by_run.csv")
    by_rep = pd.read_csv(full / "e08" / "by_repetition.csv")
    pairs = pd.read_csv(full / "e08" / "matched_pairs.csv")
    # Compact: write copies + a small summary of available columns / N
    by_run.to_csv(out / "e08_by_run.csv", index=False)
    by_rep.to_csv(out / "e08_by_repetition.csv", index=False)
    pairs.to_csv(out / "e08_matched_pairs.csv", index=False)
    summary = pd.DataFrame(
        [
            {"table": "by_run", "n_rows": len(by_run), "columns": "|".join(by_run.columns)},
            {"table": "by_repetition", "n_rows": len(by_rep), "columns": "|".join(by_rep.columns)},
            {"table": "matched_pairs", "n_rows": len(pairs), "columns": "|".join(pairs.columns)},
        ]
    )
    summary.to_csv(out / "e08_review_summary.csv", index=False)
    lines = [
        "# E08 result extraction (protocol-confound diagnostic)",
        "",
        "These tables **characterize** fixed-order / drift patterns. They do **not** remove the run-order confound.",
        "",
        f"- by_run rows: {len(by_run)}; columns: {list(by_run.columns)}",
        f"- by_repetition rows: {len(by_rep)}; columns: {list(by_rep.columns)}",
        f"- matched_pairs rows: {len(pairs)}; columns: {list(pairs.columns)}",
        "",
    ]
    Path("docs/e08_result_extraction.md").write_text("\n".join(lines))


def sensitivity_summary(full: Path, out: Path) -> None:
    e01 = json.loads((full / "e01" / "erd_lr" / "summary.json").read_text())
    boot = pd.read_csv(full / "e01" / "erd_lr" / "bootstrap_summary.csv")
    row_b = boot.loc[boot["metric"] == "balanced_accuracy"].iloc[0] if "metric" in boot.columns else boot.iloc[0]

    def _ci(frame_path: Path):
        b = pd.read_csv(frame_path)
        if "metric" in b.columns:
            r = b.loc[b["metric"] == "balanced_accuracy"]
            r = r.iloc[0] if len(r) else b.iloc[0]
        else:
            r = b.iloc[0]
        low = r.get("ci_low", r.get("lower", r.get("q025")))
        high = r.get("ci_high", r.get("upper", r.get("q975")))
        return low, high

    strict_sum = json.loads((full / "e01_strict_sensitivity" / "erd_lr" / "summary.json").read_text())
    strict_cohort = json.loads((full / "e01_strict_sensitivity" / "cohort.json").read_text())
    e06a = json.loads((full / "e06" / "all_events" / "summary.json").read_text())
    e06f = json.loads((full / "e06" / "first60" / "summary.json").read_text())
    # first60 N from oof
    n_first = pd.read_csv(full / "e06" / "first60" / "oof_predictions.csv")["subject"].nunique()
    n_all = pd.read_csv(full / "e06" / "all_events" / "oof_predictions.csv")["subject"].nunique()
    n_e01 = pd.read_csv(full / "e01" / "erd_lr" / "oof_predictions.csv")["subject"].nunique()

    def ci_for(path: Path):
        try:
            return _ci(path)
        except Exception:
            return (None, None)

    rows = [
        {
            "analysis": "E01_primary",
            "n": n_e01,
            "bacc": e01.get("balanced_accuracy"),
            "ci_low": row_b.get("ci_low", row_b.get("lower")),
            "ci_high": row_b.get("ci_high", row_b.get("upper")),
        },
        {
            "analysis": "E01_strict",
            "n": strict_cohort.get("n_subjects"),
            "bacc": strict_sum.get("balanced_accuracy"),
            "ci_low": ci_for(full / "e01_strict_sensitivity" / "erd_lr" / "bootstrap_summary.csv")[0],
            "ci_high": ci_for(full / "e01_strict_sensitivity" / "erd_lr" / "bootstrap_summary.csv")[1],
        },
        {
            "analysis": "E06_first60",
            "n": int(n_first),
            "bacc": e06f.get("balanced_accuracy"),
            "ci_low": ci_for(full / "e06" / "first60" / "bootstrap_summary.csv")[0],
            "ci_high": ci_for(full / "e06" / "first60" / "bootstrap_summary.csv")[1],
        },
        {
            "analysis": "E06_all_events",
            "n": int(n_all),
            "bacc": e06a.get("balanced_accuracy"),
            "ci_low": ci_for(full / "e06" / "all_events" / "bootstrap_summary.csv")[0],
            "ci_high": ci_for(full / "e06" / "all_events" / "bootstrap_summary.csv")[1],
        },
    ]
    # sampling-rate plan only (not executed by default)
    sr_plan = full / "e01_sampling_rate_sensitivity" / "plan.json"
    if sr_plan.exists():
        plan = json.loads(sr_plan.read_text())
        rows.append(
            {
                "analysis": "E01_sampling_rate_sensitivity",
                "n": plan.get("n_remaining_in_primary_subset"),
                "bacc": None,
                "ci_low": None,
                "ci_high": None,
            }
        )
    pd.DataFrame(rows).to_csv(out / "sensitivity_summary.csv", index=False)


def main() -> None:
    full = Path("results/definitive/full")
    out = Path("results/postdefinitive_review")
    out.mkdir(parents=True, exist_ok=True)
    extract_e03(full, out)
    extract_e04(full, out)
    extract_e08(full, out)
    sensitivity_summary(full, out)
    print("Wrote extractions to", out)


if __name__ == "__main__":
    main()
