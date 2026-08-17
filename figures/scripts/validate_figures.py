#!/usr/bin/env python3
"""Validate plotted/exported publication figures against frozen analysis outputs.

Fails (exit 1) if any mapped numeric claim disagrees with frozen sources.
Does not rerun scientific analyses.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "figures" / "scripts"))

from paths import CMP, E00, E01, E02, E03, E05, E07, REV, SENS, boot_ci, load_json  # noqa: E402

PRIMARY_BACC = 0.6179239767273408
TOL = 1e-9


class Check:
    def __init__(self) -> None:
        self.failures: list[str] = []
        self.passes: list[str] = []

    def ok(self, name: str) -> None:
        self.passes.append(name)

    def fail(self, name: str, detail: str) -> None:
        self.failures.append(f"{name}: {detail}")

    def almost(self, name: str, a: float, b: float, tol: float = TOL) -> None:
        if abs(float(a) - float(b)) > tol:
            self.fail(name, f"{a!r} != {b!r} (tol={tol})")
        else:
            self.ok(name)

    def eq(self, name: str, a, b) -> None:
        if a != b:
            self.fail(name, f"{a!r} != {b!r}")
        else:
            self.ok(name)


def main() -> int:
    c = Check()
    src = ROOT / "figures/source_data"

    # --- E01 primary ---
    mean, lo, hi = boot_ci(E01 / "erd_lr/bootstrap_summary.csv")
    c.almost("E01 primary BAcc", mean, PRIMARY_BACC)
    pm = pd.read_csv(E01 / "erd_lr/participant_metrics.csv")
    c.eq("E01 N", int(pm["subject"].nunique()), 102)
    ann2 = load_json(src / "Figure_2_annotations.json")
    c.almost("Fig2A exported mean", ann2["mean_bacc"], PRIMARY_BACC)
    c.eq("Fig2A exported N", ann2["n"], 102)

    # --- E07 ---
    e07 = load_json(E07 / "e07_summary.json")
    null = pd.read_csv(E07 / "null_statistics.csv")
    c.eq("E07 n_null", len(null), 1000)
    c.eq("E07 n_permutations field", e07["n_permutations"], 1000)
    c.almost("E07 observed == E01", e07["observed_statistic"], PRIMARY_BACC)
    c.eq("E07 n_null_ge", e07["n_null_ge_observed"], 0)
    c.almost("E07 plus-one p", e07["p_value_plusone"], 0.000999000999000999)
    c.almost("Fig2C observed export", ann2["observed_e07"], PRIMARY_BACC)
    null_src = pd.read_csv(src / "Figure_2C_source.csv")
    c.eq("Fig2C null count", len(null_src), 1000)

    # --- E00/E01 paired ---
    paired = pd.read_csv(CMP / "e00_vs_e01_participant.csv")
    ann3 = load_json(src / "Figure_3_annotations.json")
    c.eq("E00/E01 paired N", len(paired), 102)
    c.eq("Fig3 paired N export", ann3["n"], 102)
    e00_m, _, _ = boot_ci(E00 / "bootstrap_summary.csv")
    c.almost("Fig3 E00 mean", ann3["e00_mean"], e00_m)
    c.almost("Fig3 E01 mean", ann3["e01_mean"], PRIMARY_BACC)

    # --- E03 ROI ---
    roi = pd.read_csv(E03 / "roi_summary.csv")
    roi_src = pd.read_csv(src / "Figure_4B_source.csv")
    c.eq("E03 ROI rows exported", len(roi_src), len(roi))
    for _, r in roi.iterrows():
        m = roi_src.loc[(roi_src.band == r.band) & (roi_src.roi == r.roi)].iloc[0]
        c.almost(f"ROI {r.band}/{r.roi}", float(m["mean"]), float(r["mean"]), tol=1e-12)

    # --- E02 movement Ns ---
    mov = pd.read_csv(src / "Figure_4D_source.csv")
    for _, r in mov.iterrows():
        n_frozen = int(load_json(E02 / r["key"] / "summary.json")["n_participants"])
        c.eq(f"E02 N {r['key']}", int(r["n"]), n_frozen)

    # --- Spatial control ---
    spat = load_json(E05 / "spatial_control/paired_effect_summary.json")
    spat_boot = pd.read_csv(E05 / "spatial_control/bootstrap_summary.csv").iloc[0]
    ann4e = load_json(src / "Figure_4E_annotations.json")
    c.eq("Spatial N", ann4e["spatial_n"], int(spat_boot["n_participants"]))
    c.eq("Spatial paired N", ann4e["paired_n"], spat["common_n"])
    c.almost("Spatial BAcc", ann4e["spatial_bacc"], float(spat_boot["mean"]))
    c.almost("Spatial paired Δ", ann4e["mean_sm_minus_sc"], spat["mean_difference_sm_minus_sc"])
    c.eq("No confirmatory paired p flag", ann4e["formal_p"], False)
    c.eq("Spatial N expected 78", ann4e["spatial_n"], 78)
    c.eq("Paired N expected 77", ann4e["paired_n"], 77)

    # --- Artifact E05 ---
    thr = pd.read_csv(src / "Figure_5A_source.csv")
    expected = {
        "No rejection": ("none", 0.618568),
        "150 µV": ("150uv", 0.616887),
        "200 µV (primary)": ("200uv", 0.617924),
    }
    for label, (key, approx) in expected.items():
        row = thr.loc[thr.threshold == label].iloc[0]
        m, _, _ = boot_ci(E05 / f"artifact_sensitivity/{key}/bootstrap_summary.csv")
        n = int(load_json(E05 / f"artifact_sensitivity/{key}/summary.json")["n_participants"])
        c.eq(f"Artifact N {key}", int(row["n"]), n)
        c.almost(f"Artifact BAcc {key}", float(row["bacc"]), m)
        c.almost(f"Artifact BAcc ~{approx} {key}", float(row["bacc"]), approx, tol=5e-7)

    # --- Sampling-rate ---
    samp = load_json(SENS / "sampling_rate/sampling_rate_sensitivity_summary.json")
    s11 = load_json(src / "Figure_S11_annotations.json")
    c.eq("Sampling N", s11["sensitivity_n"], 99)
    c.almost("Sampling BAcc", s11["sensitivity_bacc"], samp["sensitivity_bacc"])
    c.almost("Sampling BAcc ~0.6209", s11["sensitivity_bacc"], 0.620899, tol=5e-7)

    # --- Rejection ---
    rej = load_json(SENS / "rejection_audit/rejection_audit_summary.json")
    f5c = load_json(src / "Figure_5C_source.json")
    me = f5c["primary_cohort"]["ME"]
    mi = f5c["primary_cohort"]["MI"]
    c.eq("Retained ME", me["epochs_retained"], 8448)
    c.eq("Retained MI", mi["epochs_retained"], 8492)
    c.almost("ME rejection", me["rejection_proportion"], rej["primary_cohort"]["ME"]["rejection_proportion"])
    c.almost(
        "Participant mean Δ rejection",
        f5c["participant_paired"]["mean_me_minus_mi"],
        rej["participant_paired"]["mean_me_minus_mi"],
    )

    # --- No historical figure paths accidentally referenced ---
    gen = (ROOT / "figures/scripts/generate_all_figures.py").read_text()
    if "historical/" in gen:
        c.fail("historical path", "generate_all_figures.py references historical/")
    else:
        c.ok("no historical/ in generator")

    # --- Required figure files exist ---
    required = [
        "figures/main/Figure_1_Study_Design.pdf",
        "figures/main/Figure_2_Primary_Decoding.pdf",
        "figures/main/Figure_3_PreCue_PostCue.pdf",
        "figures/main/Figure_4_Physiology_Spatial.pdf",
        "figures/main/Figure_5_Robustness_Protocol.pdf",
        "figures/previews/publication_figures_contact_sheet.pdf",
    ]
    for rel in required:
        p = ROOT / rel
        if p.exists():
            c.ok(f"exists {rel}")
        else:
            c.fail(f"exists {rel}", "missing")

    print(f"PASSED {len(c.passes)} checks")
    if c.failures:
        print(f"FAILED {len(c.failures)} checks:")
        for f in c.failures:
            print("  -", f)
        return 1
    print("ALL VALIDATION CHECKS PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
