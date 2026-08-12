"""Participant eligibility under the frozen Milestone-1 rule."""

from __future__ import annotations

from typing import Iterable

import pandas as pd

from eeg_me_mi.protocol import MATCHED_RUN_PAIRS, PAIR_FAMILY


REASON_CODES = {
    "ELIGIBLE": "eligible under primary Milestone-1 rule",
    "STRUCTURAL_ANOMALY": "unrecoverable structural anomaly in used data",
    "INSUFFICIENT_ME_EPOCHS": "fewer than required ME epochs after rejection",
    "INSUFFICIENT_MI_EPOCHS": "fewer than required MI epochs after rejection",
    "INSUFFICIENT_MATCHED_PAIRS": "fewer than two usable matched ME/MI pairs",
    "MISSING_UNILATERAL_PAIR": "no usable unilateral matched pair",
    "MISSING_BILATERAL_PAIR": "no usable bilateral matched pair",
    "MOVEMENT_COMPOSITION": "movement composition not represented in both modes",
    "NO_EPOCHS": "no retained epochs after preprocessing",
}


def evaluate_participant(
    subject: int,
    metadata: pd.DataFrame,
    audit: pd.DataFrame,
    *,
    min_epochs_per_mode: int = 30,
) -> dict:
    """Evaluate one participant against the frozen primary eligibility rule."""
    sub_meta = metadata.loc[metadata["subject"] == subject].copy()
    sub_audit = audit.loc[audit["subject"] == subject].copy()

    result = {
        "subject": subject,
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
        "reason_codes": "",
        "reason_detail": "",
    }

    if sub_meta.empty:
        result["reason_codes"] = "NO_EPOCHS"
        result["reason_detail"] = REASON_CODES["NO_EPOCHS"]
        return result

    # Structural validity for runs that contribute epochs.
    used_runs = sorted(set(map(int, sub_meta["run"])))
    reasons: list[str] = []

    audit_by_run = {
        int(r["run"]): bool(r["structurally_valid"])
        for _, r in sub_audit.iterrows()
    }
    for run in used_runs:
        if not audit_by_run.get(run, False):
            reasons.append("STRUCTURAL_ANOMALY")
            break

    # Usable matched pairs: both members structurally valid AND ≥1 kept epoch each.
    usable_pairs: list[tuple[int, int]] = []
    for me, mi in MATCHED_RUN_PAIRS:
        me_ok = audit_by_run.get(me, False)
        mi_ok = audit_by_run.get(mi, False)
        n_me = int(((sub_meta["run"] == me)).sum())
        n_mi = int(((sub_meta["run"] == mi)).sum())
        if me_ok and mi_ok and n_me >= 1 and n_mi >= 1:
            usable_pairs.append((me, mi))

    # Restrict analysis epochs to usable matched pairs only.
    pair_runs = {r for pair in usable_pairs for r in pair}
    retained = sub_meta.loc[sub_meta["run"].isin(pair_runs)].copy()

    n_me = int((retained["condition"] == "execution").sum())
    n_mi = int((retained["condition"] == "imagery").sum())
    result["n_me_epochs"] = n_me
    result["n_mi_epochs"] = n_mi
    result["n_usable_matched_pairs"] = len(usable_pairs)
    result["n_unilateral_pairs"] = sum(1 for p in usable_pairs if PAIR_FAMILY[p] == "unilateral")
    result["n_bilateral_pairs"] = sum(1 for p in usable_pairs if PAIR_FAMILY[p] == "bilateral")

    mov_me = sorted(set(retained.loc[retained["condition"] == "execution", "movement"]))
    mov_mi = sorted(set(retained.loc[retained["condition"] == "imagery", "movement"]))
    result["movements_me"] = "|".join(mov_me)
    result["movements_mi"] = "|".join(mov_mi)

    if not usable_pairs:
        reasons.append("INSUFFICIENT_MATCHED_PAIRS")
    if len(usable_pairs) < 2:
        reasons.append("INSUFFICIENT_MATCHED_PAIRS")
    if result["n_unilateral_pairs"] < 1:
        reasons.append("MISSING_UNILATERAL_PAIR")
    if result["n_bilateral_pairs"] < 1:
        reasons.append("MISSING_BILATERAL_PAIR")

    # Movement composition: every movement present in either mode must appear in both.
    if mov_me or mov_mi:
        if set(mov_me) != set(mov_mi):
            reasons.append("MOVEMENT_COMPOSITION")

    # Sensitivity flags (do not alter primary).
    result["eligible_min20"] = (
        n_me >= 20
        and n_mi >= 20
        and len(usable_pairs) >= 2
        and result["n_unilateral_pairs"] >= 1
        and result["n_bilateral_pairs"] >= 1
        and set(mov_me) == set(mov_mi)
        and "STRUCTURAL_ANOMALY" not in reasons
    )
    result["eligible_min40"] = (
        n_me >= 40
        and n_mi >= 40
        and len(usable_pairs) >= 2
        and result["n_unilateral_pairs"] >= 1
        and result["n_bilateral_pairs"] >= 1
        and set(mov_me) == set(mov_mi)
        and "STRUCTURAL_ANOMALY" not in reasons
    )

    if n_me < min_epochs_per_mode:
        reasons.append("INSUFFICIENT_ME_EPOCHS")
    if n_mi < min_epochs_per_mode:
        reasons.append("INSUFFICIENT_MI_EPOCHS")

    # Deduplicate reason codes while preserving order.
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
        result["reason_detail"] = "; ".join(REASON_CODES[c] for c in deduped)

    return result


def evaluate_eligibility(
    metadata: pd.DataFrame,
    audit: pd.DataFrame,
    subjects: Iterable[int],
    *,
    min_epochs_per_mode: int = 30,
) -> pd.DataFrame:
    rows = [
        evaluate_participant(int(s), metadata, audit, min_epochs_per_mode=min_epochs_per_mode)
        for s in subjects
    ]
    return pd.DataFrame(rows)


def filter_eligible_epochs(
    metadata: pd.DataFrame,
    eligibility: pd.DataFrame,
    audit: pd.DataFrame,
) -> pd.DataFrame:
    """Return epoch metadata restricted to primary-eligible participants and usable pairs."""
    eligible_subjects = set(
        eligibility.loc[eligibility["eligible_primary"], "subject"].astype(int)
    )
    if not eligible_subjects:
        return metadata.iloc[0:0].copy()

    keep_idx = []
    for subject in eligible_subjects:
        sub_meta = metadata.loc[metadata["subject"] == subject]
        sub_audit = audit.loc[audit["subject"] == subject]
        audit_by_run = {
            int(r["run"]): bool(r["structurally_valid"]) for _, r in sub_audit.iterrows()
        }
        usable_runs: set[int] = set()
        for me, mi in MATCHED_RUN_PAIRS:
            n_me = int((sub_meta["run"] == me).sum())
            n_mi = int((sub_meta["run"] == mi).sum())
            if audit_by_run.get(me, False) and audit_by_run.get(mi, False) and n_me and n_mi:
                usable_runs.update({me, mi})
        keep_idx.extend(sub_meta.loc[sub_meta["run"].isin(usable_runs)].index.tolist())

    return metadata.loc[sorted(keep_idx)].copy()
