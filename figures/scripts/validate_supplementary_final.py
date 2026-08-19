#!/usr/bin/env python3
"""Validate final supplementary figures / Table 2 against frozen outputs."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "figures" / "supplementary_final"
SRC = ROOT / "figures" / "source_data" / "supplementary_final"


def main() -> int:
    fails = []
    n_ok = 0

    def ok(msg: str) -> None:
        nonlocal n_ok
        n_ok += 1

    def fail(msg: str) -> None:
        fails.append(msg)

    # required figures
    for stem in [
        "Figure_S1_Cohort_Eligibility",
        "Figure_S2_Movement_Decoding",
        "Figure_S3_Channel_ERD",
        "Figure_S4_Laterality",
        "Figure_S5_Participant_Heterogeneity",
        "Figure_S6_Artifact_Sensitivity",
        "Figure_S7_Rejection_Audit",
        "Figure_S8_E08_Diagnostics",
        "Figure_S9_Comparator_Distributions",
        "Figure_S10_Duration_Sampling_Participant",
    ]:
        for ext in ("pdf", "png", "svg"):
            p = OUT / f"{stem}.{ext}"
            if p.exists():
                ok(f"exists {stem}.{ext}")
            else:
                fail(f"missing {stem}.{ext}")

    # no secondary-metrics figure
    if list(OUT.glob("*Secondary*")):
        fail("Secondary metrics figure should not exist in supplementary_final")
    else:
        ok("no secondary-metrics figure")

    # S1 counts
    s1 = json.loads((SRC / "Figure_S1_summary.json").read_text())
    if s1["n_audited"] == 109 and s1["n_primary"] == 102 and s1["n_ineligible"] == 7:
        ok("S1 Ns")
    else:
        fail(f"S1 Ns {s1}")
    if s1["n_strict"] == 51 and s1["n_sampling_rate"] == 99:
        ok("S1 sensitivity Ns")
    else:
        fail(f"S1 sens Ns {s1}")

    # Table 2
    t2 = pd.read_csv(ROOT / "docs/tables/table_2_secondary_metrics.csv")
    e01 = json.loads((ROOT / "results/definitive/full/e01/erd_lr/summary.json").read_text())
    row = t2.loc[t2.metric.str.contains("Balanced accuracy")].iloc[0]
    if abs(float(row.value) - float(e01["balanced_accuracy"])) < 1e-12:
        ok("Table2 BAcc")
    else:
        fail("Table2 BAcc mismatch")

    # S7 retained
    rej = json.loads((SRC / "Figure_S7_rejection_summary.json").read_text())
    if rej["primary_cohort"]["ME"]["epochs_retained"] == 8448 and rej["primary_cohort"]["MI"]["epochs_retained"] == 8492:
        ok("S7 retained")
    else:
        fail("S7 retained mismatch")

    # S10 Ns
    a10 = json.loads((SRC / "Figure_S10_annotations.json").read_text())
    if a10["first60_n"] == 102 and a10["sampling_paired"]["common_n"] == 99:
        ok("S10 Ns")
    else:
        fail(f"S10 Ns {a10}")

    # approved copy identity (png size equal) for one exemplar
    old = ROOT / "figures/supplementary/Figure_S3_Movement_Decoding.png"
    new = OUT / "Figure_S2_Movement_Decoding.png"
    if old.read_bytes() == new.read_bytes():
        ok("S2 byte-identical to old S3")
    else:
        fail("S2 not byte-identical to approved S3")

    report = ROOT / "figures/previews/supplementary_final_validation.txt"
    lines = [f"PASSED {n_ok}", f"FAILED {len(fails)}"] + [f"  - {f}" for f in fails]
    if not fails:
        lines.append("ALL VALIDATION CHECKS PASSED")
    report.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
