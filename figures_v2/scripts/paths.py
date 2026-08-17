"""Frozen-path helpers for publication figures V2."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]


def load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def boot_ci(path: Path, metric: str = "balanced_accuracy") -> tuple[float, float, float]:
    df = pd.read_csv(path)
    row = df.loc[df["metric"] == metric].iloc[0]
    return float(row["mean"]), float(row["ci_low"]), float(row["ci_high"])


E01 = ROOT / "results/definitive/full/e01"
E00 = ROOT / "results/definitive/full/e00"
E02 = ROOT / "results/definitive/full/e02"
E03 = ROOT / "results/definitive/full/e03"
E07 = ROOT / "results/definitive/full/e07"
CMP = ROOT / "results/definitive/full/comparisons"
E05 = ROOT / "results/postdefinitive_e05"
REV = ROOT / "results/postdefinitive_review"
SENS = ROOT / "results/final_sensitivity_checks"
QC = ROOT / "results/definitive/full/qc"
