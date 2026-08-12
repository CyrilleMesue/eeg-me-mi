"""Participant eligibility: E01 primary, E02 movement, strict sensitivity."""

from __future__ import annotations

from typing import Iterable

import pandas as pd

from eeg_me_mi.protocol import MATCHED_RUN_PAIRS, PAIR_FAMILY

MOVEMENTS = ("left_fist", "right_fist", "both_fists", "both_feet")
E02_ANALYSES = (
    "left_fist",
    "right_fist",
    "both_fists",
    "both_feet",
    "unilateral",
    "bilateral",
)

REASON_CODES = {
    "ELIGIBLE": "eligible under primary rule",
    "STRUCTURAL_ANOMALY": "unrecoverable structural anomaly in used data",
    "INSUFFICIENT_ME_EPOCHS": "fewer than required ME epochs after rejection",
    "INSUFFICIENT_MI_EPOCHS": "fewer than required MI epochs after rejection",
    "INSUFFICIENT_MATCHED_PAIRS": "fewer than two usable matched ME/MI pairs",
    "MISSING_UNILATERAL_PAIR": "no usable unilateral matched pair",
    "MISSING_BILATERAL_PAIR": "no usable bilateral matched pair",
    "MOVEMENT_COMPOSITION": "movement composition not represented in both modes",
    "NO_EPOCHS": "no retained epochs after preprocessing",
    "INSUFFICIENT_MOVEMENT_ME": "fewer than required ME epochs for movement analysis",
    "INSUFFICIENT_MOVEMENT_MI": "fewer than required MI epochs for movement analysis",
    "INSUFFICIENT_MOVEMENT_PAIRS": "fewer than required matched pairs for movement analysis",
    "STRICT_NOT_ALL_RUNS_VALID": "not all 12 task runs structurally valid",
    "STRICT_MODE_EPOCHS": "strict cohort requires ≥40 epochs per mode",
    "STRICT_CELL_EPOCHS": "strict cohort requires ≥20 epochs per movement×mode cell",
    "STRICT_CELL_FRACTION": "strict cohort requires ≥80% of expected cell observations",
}


def usable_matched_pairs(sub_meta: pd.DataFrame, audit_by_run: dict[int, bool]) -> list[tuple[int, int]]:
    usable = []
    for me, mi in MATCHED_RUN_PAIRS:
        if (
            audit_by_run.get(me, False)
            and audit_by_run.get(mi, False)
            and int((sub_meta["run"] == me).sum()) >= 1
            and int((sub_meta["run"] == mi).sum()) >= 1
        ):
            usable.append((me, mi))
    return usable


def retained_from_pairs(sub_meta: pd.DataFrame, pairs: list[tuple[int, int]]) -> pd.DataFrame:
    runs = {r for pair in pairs for r in pair}
    return sub_meta.loc[sub_meta["run"].isin(runs)].copy()


def movement_mode_counts(retained: pd.DataFrame) -> dict[str, int]:
    out = {}
    for movement in MOVEMENTS:
        for mode, key in (("execution", "me"), ("imagery", "mi")):
            out[f"n_{movement}_{key}"] = int(
                ((retained["movement"] == movement) & (retained["condition"] == mode)).sum()
            )
    return out


def expected_cell_count(audit_row_by_run: dict[int, pd.Series], movement: str, mode: str) -> float:
    """Expected observations from audit T1/T2 counts for runs that produce ``movement``."""
    # Unilateral: T1=left, T2=right; bilateral: T1=both_fists, T2=both_feet
    if movement in {"left_fist", "right_fist"}:
        family = "unilateral"
        ann = "T1" if movement == "left_fist" else "T2"
    else:
        family = "bilateral"
        ann = "T1" if movement == "both_fists" else "T2"
    total = 0.0
    for me, mi in MATCHED_RUN_PAIRS:
        if PAIR_FAMILY[(me, mi)] != family:
            continue
        run = me if mode == "execution" else mi
        row = audit_row_by_run.get(run)
        if row is None:
            continue
        col = f"{ann}_count"
        if col in row and pd.notna(row[col]):
            total += float(row[col])
    return total


def evaluate_e02_subset(
    retained: pd.DataFrame,
    analysis: str,
    *,
    min_epochs: int = 15,
    min_pairs: int = 2,
) -> dict:
    """Eligibility for one E02 analysis on already pair-filtered epochs."""
    if analysis in MOVEMENTS:
        subset = retained.loc[retained["movement"] == analysis]
    elif analysis == "unilateral":
        subset = retained.loc[retained["task_family"] == "unilateral"]
    elif analysis == "bilateral":
        subset = retained.loc[retained["task_family"] == "bilateral"]
    else:
        raise ValueError(f"Unknown E02 analysis: {analysis}")

    n_me = int((subset["condition"] == "execution").sum())
    n_mi = int((subset["condition"] == "imagery").sum())
    # Matched repetitions = unique pair_id with both modes present
    pair_ids = []
    for pid, frame in subset.groupby("pair_id"):
        if set(frame["condition"]) >= {"execution", "imagery"}:
            pair_ids.append(pid)
    n_pairs = len(pair_ids)
    reasons = []
    if n_me < min_epochs:
        reasons.append("INSUFFICIENT_MOVEMENT_ME")
    if n_mi < min_epochs:
        reasons.append("INSUFFICIENT_MOVEMENT_MI")
    if n_pairs < min_pairs:
        reasons.append("INSUFFICIENT_MOVEMENT_PAIRS")
    return {
        f"e02_{analysis}_n_me": n_me,
        f"e02_{analysis}_n_mi": n_mi,
        f"e02_{analysis}_n_pairs": n_pairs,
        f"e02_{analysis}_eligible": len(reasons) == 0,
        f"e02_{analysis}_reasons": "|".join(reasons) if reasons else "ELIGIBLE",
    }


def evaluate_strict(
    sub_meta: pd.DataFrame,
    sub_audit: pd.DataFrame,
    retained: pd.DataFrame,
    *,
    min_mode: int = 40,
    min_cell: int = 20,
    min_frac: float = 0.8,
) -> dict:
    audit_by_run = {int(r["run"]): bool(r["structurally_valid"]) for _, r in sub_audit.iterrows()}
    audit_rows = {int(r["run"]): r for _, r in sub_audit.iterrows()}
    all_valid = all(audit_by_run.get(run, False) for run in range(3, 15))
    n_me = int((retained["condition"] == "execution").sum())
    n_mi = int((retained["condition"] == "imagery").sum())
    counts = movement_mode_counts(retained)
    reasons = []
    if not all_valid:
        reasons.append("STRICT_NOT_ALL_RUNS_VALID")
    if n_me < min_mode or n_mi < min_mode:
        reasons.append("STRICT_MODE_EPOCHS")

    cell_ok = True
    frac_ok = True
    for movement in MOVEMENTS:
        for mode, key in (("execution", "me"), ("imagery", "mi")):
            got = counts[f"n_{movement}_{key}"]
            exp = expected_cell_count(audit_rows, movement, mode)
            if got < min_cell:
                cell_ok = False
            if exp > 0 and (got / exp) < min_frac:
                frac_ok = False
            counts[f"expected_{movement}_{key}"] = exp
            counts[f"frac_{movement}_{key}"] = (got / exp) if exp > 0 else float("nan")
    if not cell_ok:
        reasons.append("STRICT_CELL_EPOCHS")
    if not frac_ok:
        reasons.append("STRICT_CELL_FRACTION")

    return {
        "strict_all_runs_valid": all_valid,
        "eligible_strict": len(reasons) == 0,
        "strict_reasons": "|".join(reasons) if reasons else "ELIGIBLE",
        **{k: v for k, v in counts.items() if k.startswith("expected_") or k.startswith("frac_")},
    }


def evaluate_participant(
    subject: int,
    metadata: pd.DataFrame,
    audit: pd.DataFrame,
    *,
    min_epochs_per_mode: int = 30,
    e02_min_epochs: int = 15,
    e02_min_pairs: int = 2,
) -> dict:
    """Full eligibility record for one participant (performance-blind)."""
    sub_meta = metadata.loc[metadata["subject"] == subject].copy()
    sub_audit = audit.loc[audit["subject"] == subject].copy()

    result: dict = {
        "subject": subject,
        "structural_ok": False,
        "n_me_epochs": 0,
        "n_mi_epochs": 0,
        "n_usable_matched_pairs": 0,
        "n_unilateral_pairs": 0,
        "n_bilateral_pairs": 0,
        "movements_me": "",
        "movements_mi": "",
        "eligible_primary": False,
        "eligible_min20": False,
        "eligible_min40": False,
        "eligible_strict": False,
        "reason_codes": "",
        "reason_detail": "",
    }
    for movement in MOVEMENTS:
        result[f"n_{movement}_me"] = 0
        result[f"n_{movement}_mi"] = 0

    if sub_meta.empty:
        result["reason_codes"] = "NO_EPOCHS"
        result["reason_detail"] = REASON_CODES["NO_EPOCHS"]
        for analysis in E02_ANALYSES:
            result[f"e02_{analysis}_eligible"] = False
            result[f"e02_{analysis}_n_me"] = 0
            result[f"e02_{analysis}_n_mi"] = 0
            result[f"e02_{analysis}_n_pairs"] = 0
            result[f"e02_{analysis}_reasons"] = "NO_EPOCHS"
        result["strict_reasons"] = "NO_EPOCHS"
        return result

    reasons: list[str] = []
    audit_by_run = {int(r["run"]): bool(r["structurally_valid"]) for _, r in sub_audit.iterrows()}
    used_runs = sorted(set(map(int, sub_meta["run"])))
    for run in used_runs:
        if not audit_by_run.get(run, False):
            reasons.append("STRUCTURAL_ANOMALY")
            break

    pairs = usable_matched_pairs(sub_meta, audit_by_run)
    retained = retained_from_pairs(sub_meta, pairs)
    result["structural_ok"] = "STRUCTURAL_ANOMALY" not in reasons

    n_me = int((retained["condition"] == "execution").sum())
    n_mi = int((retained["condition"] == "imagery").sum())
    result["n_me_epochs"] = n_me
    result["n_mi_epochs"] = n_mi
    result["n_usable_matched_pairs"] = len(pairs)
    result["n_unilateral_pairs"] = sum(1 for p in pairs if PAIR_FAMILY[p] == "unilateral")
    result["n_bilateral_pairs"] = sum(1 for p in pairs if PAIR_FAMILY[p] == "bilateral")
    result["usable_pair_ids"] = "|".join(f"{a:02d}-{b:02d}" for a, b in pairs)

    mov_me = sorted(set(retained.loc[retained["condition"] == "execution", "movement"]))
    mov_mi = sorted(set(retained.loc[retained["condition"] == "imagery", "movement"]))
    result["movements_me"] = "|".join(mov_me)
    result["movements_mi"] = "|".join(mov_mi)
    result.update(movement_mode_counts(retained))

    if len(pairs) < 2:
        reasons.append("INSUFFICIENT_MATCHED_PAIRS")
    if result["n_unilateral_pairs"] < 1:
        reasons.append("MISSING_UNILATERAL_PAIR")
    if result["n_bilateral_pairs"] < 1:
        reasons.append("MISSING_BILATERAL_PAIR")
    if (mov_me or mov_mi) and set(mov_me) != set(mov_mi):
        reasons.append("MOVEMENT_COMPOSITION")

    base_ok = (
        "STRUCTURAL_ANOMALY" not in reasons
        and len(pairs) >= 2
        and result["n_unilateral_pairs"] >= 1
        and result["n_bilateral_pairs"] >= 1
        and set(mov_me) == set(mov_mi)
    )
    result["eligible_min20"] = base_ok and n_me >= 20 and n_mi >= 20
    result["eligible_min40"] = base_ok and n_me >= 40 and n_mi >= 40

    if n_me < min_epochs_per_mode:
        reasons.append("INSUFFICIENT_ME_EPOCHS")
    if n_mi < min_epochs_per_mode:
        reasons.append("INSUFFICIENT_MI_EPOCHS")

    for analysis in E02_ANALYSES:
        result.update(
            evaluate_e02_subset(
                retained,
                analysis,
                min_epochs=e02_min_epochs,
                min_pairs=e02_min_pairs,
            )
        )

    strict = evaluate_strict(sub_meta, sub_audit, retained)
    result.update(strict)

    deduped: list[str] = []
    for code in reasons:
        if code not in deduped:
            deduped.append(code)
    if not deduped:
        result["eligible_primary"] = True
        result["reason_codes"] = "ELIGIBLE"
        result["reason_detail"] = REASON_CODES["ELIGIBLE"]
    else:
        result["eligible_primary"] = False
        result["reason_codes"] = "|".join(deduped)
        result["reason_detail"] = "; ".join(REASON_CODES.get(c, c) for c in deduped)
    return result


def evaluate_eligibility(
    metadata: pd.DataFrame,
    audit: pd.DataFrame,
    subjects: Iterable[int],
    *,
    min_epochs_per_mode: int = 30,
    e02_min_epochs: int = 15,
    e02_min_pairs: int = 2,
) -> pd.DataFrame:
    rows = [
        evaluate_participant(
            int(s),
            metadata,
            audit,
            min_epochs_per_mode=min_epochs_per_mode,
            e02_min_epochs=e02_min_epochs,
            e02_min_pairs=e02_min_pairs,
        )
        for s in subjects
    ]
    return pd.DataFrame(rows)


def filter_eligible_epochs(
    metadata: pd.DataFrame,
    eligibility: pd.DataFrame,
    audit: pd.DataFrame,
    *,
    eligible_col: str = "eligible_primary",
) -> pd.DataFrame:
    eligible_subjects = set(eligibility.loc[eligibility[eligible_col].astype(bool), "subject"].astype(int))
    if not eligible_subjects:
        return metadata.iloc[0:0].copy()
    keep_idx = []
    for subject in eligible_subjects:
        sub_meta = metadata.loc[metadata["subject"] == subject]
        sub_audit = audit.loc[audit["subject"] == subject]
        audit_by_run = {int(r["run"]): bool(r["structurally_valid"]) for _, r in sub_audit.iterrows()}
        pairs = usable_matched_pairs(sub_meta, audit_by_run)
        runs = {r for pair in pairs for r in pair}
        keep_idx.extend(sub_meta.loc[sub_meta["run"].isin(runs)].index.tolist())
    return metadata.loc[sorted(keep_idx)].copy()


def filter_e02_epochs(
    metadata: pd.DataFrame,
    eligibility: pd.DataFrame,
    audit: pd.DataFrame,
    analysis: str,
) -> pd.DataFrame:
    """Build an E02 analysis cohort from the full 200 µV metadata.

    Does **not** first restrict to the E01-primary cohort. Each E02 analysis
    uses its own independently frozen eligibility flag.
    """
    if analysis not in E02_ANALYSES:
        raise ValueError(f"Unknown E02 analysis: {analysis}")
    col = f"e02_{analysis}_eligible"
    base = filter_eligible_epochs(metadata, eligibility, audit, eligible_col=col)
    if base.empty:
        return base
    if analysis in MOVEMENTS:
        return base.loc[base["movement"] == analysis].copy()
    if analysis == "unilateral":
        return base.loc[base["task_family"] == "unilateral"].copy()
    return base.loc[base["task_family"] == "bilateral"].copy()
