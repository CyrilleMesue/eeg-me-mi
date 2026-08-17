#!/usr/bin/env python3
"""Validate V2 figure exports against frozen analysis outputs."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "figures_v2" / "scripts"))
from paths import CMP, E00, E01, E05, E07, SENS, boot_ci, load_json  # noqa: E402

PRIMARY = 0.6179239767273408
TOL = 1e-9
SRC = ROOT / "figures_v2" / "source_data"


def main() -> int:
    fails = []
    passes = 0

    def ok(name: str) -> None:
        nonlocal passes
        passes += 1

    def fail(name: str, detail: str) -> None:
        fails.append(f"{name}: {detail}")

    def almost(name: str, a: float, b: float, tol: float = TOL) -> None:
        if abs(float(a) - float(b)) > tol:
            fail(name, f"{a} != {b}")
        else:
            ok(name)

    def eq(name: str, a, b) -> None:
        if a != b:
            fail(name, f"{a} != {b}")
        else:
            ok(name)

    ann2 = load_json(SRC / "Figure_2_annotations.json")
    mean, lo, hi = boot_ci(E01 / "erd_lr/bootstrap_summary.csv")
    almost("primary BAcc", mean, PRIMARY)
    almost("Fig2 mean", ann2["mean_bacc"], PRIMARY)
    eq("Fig2 N", ann2["n"], 102)

    e07 = load_json(E07 / "e07_summary.json")
    null = pd.read_csv(E07 / "null_statistics.csv")
    eq("E07 n", len(null), 1000)
    almost("E07 obs", e07["observed_statistic"], PRIMARY)
    almost("E07 p", e07["p_value_plusone"], 0.000999000999000999)
    eq("E07 ge", e07["n_null_ge_observed"], 0)
    almost("Fig2C obs", ann2["observed_e07"], PRIMARY)

    ann3 = load_json(SRC / "Figure_3_annotations.json")
    paired = pd.read_csv(CMP / "e00_vs_e01_participant.csv")
    eq("paired N", len(paired), 102)
    eq("Fig3 N", ann3["n"], 102)
    e00_m, _, _ = boot_ci(E00 / "bootstrap_summary.csv")
    almost("E00", ann3["e00_mean"], e00_m)
    almost("E01 in Fig3", ann3["e01_mean"], PRIMARY)

    ann4 = load_json(SRC / "Figure_4_annotations.json")
    spat = load_json(E05 / "spatial_control/paired_effect_summary.json")
    spat_boot = pd.read_csv(E05 / "spatial_control/bootstrap_summary.csv").iloc[0]
    eq("spatial N", ann4["spatial_n"], 78)
    eq("paired N", ann4["paired_n"], 77)
    almost("SC BAcc", ann4["spatial_bacc"], float(spat_boot["mean"]))
    almost("paired Δ", ann4["mean_sm_minus_sc"], spat["mean_difference_sm_minus_sc"])
    eq("no formal p", ann4["formal_p"], False)

    thr = {
        "none": 0.618568,
        "150uv": 0.616887,
        "200uv": 0.617924,
    }
    rob = pd.read_csv(SRC / "Figure_5A_robustness_source.csv")
    for key, approx in thr.items():
        label = {"none": "No rejection", "150uv": "150 µV", "200uv": "200 µV"}[key]
        row = rob.loc[rob.analysis == label].iloc[0]
        m, _, _ = boot_ci(E05 / f"artifact_sensitivity/{key}/bootstrap_summary.csv")
        almost(f"artifact {key}", float(row.bacc), m)
        almost(f"artifact ~{approx}", float(row.bacc), approx, tol=5e-7)

    samp = load_json(SENS / "sampling_rate/sampling_rate_sensitivity_summary.json")
    row = rob.loc[rob.analysis == "Sampling-rate"].iloc[0]
    eq("samp N", int(row.n), 99)
    almost("samp BAcc", float(row.bacc), samp["sensitivity_bacc"])

    rej = load_json(SENS / "rejection_audit/rejection_audit_summary.json")
    s8 = load_json(SRC / "Figure_S8_summary.json")
    eq("ME retained", s8["primary_cohort"]["ME"]["epochs_retained"], 8448)
    eq("MI retained", s8["primary_cohort"]["MI"]["epochs_retained"], 8492)
    almost("ME rej", s8["primary_cohort"]["ME"]["rejection_proportion"], rej["primary_cohort"]["ME"]["rejection_proportion"])

    required = [
        "figures_v2/main/Figure_1_Design_Safeguards.pdf",
        "figures_v2/main/Figure_2_Primary_Decoding.pdf",
        "figures_v2/main/Figure_3_PreCue_PostCue.pdf",
        "figures_v2/main/Figure_4_Physiology_Spatial.pdf",
        "figures_v2/main/Figure_5_Robustness_Protocol.pdf",
        "figures_v2/previews/publication_figures_v2_contact_sheet.pdf",
    ]
    for rel in required:
        if (ROOT / rel).exists():
            ok(f"exists {rel}")
        else:
            fail(f"exists {rel}", "missing")

    # write report
    report = ROOT / "figures_v2" / "previews" / "validation_report_v2.txt"
    report.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"PASSED {passes}", f"FAILED {len(fails)}"] + [f"  - {f}" for f in fails]
    if not fails:
        lines.append("ALL VALIDATION CHECKS PASSED")
    report.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
