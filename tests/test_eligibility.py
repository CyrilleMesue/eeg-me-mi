"""Eligibility rule tests with synthetic metadata."""

import pandas as pd

from eeg_me_mi.eligibility import evaluate_participant


def _audit_all_valid(subject: int, runs=range(3, 15)) -> pd.DataFrame:
    rows = []
    for run in runs:
        rows.append(
            {
                "subject": subject,
                "run": run,
                "structurally_valid": True,
                "invalidity_reason": "",
            }
        )
    return pd.DataFrame(rows)


def _epochs_from_pairs(subject: int, pairs, n_per_run: int = 8) -> pd.DataFrame:
    rows = []
    for me, mi in pairs:
        family = "unilateral" if me in {3, 7, 11} else "bilateral"
        movements = ("left_fist", "right_fist") if family == "unilateral" else ("both_fists", "both_feet")
        for run, condition in ((me, "execution"), (mi, "imagery")):
            for i in range(n_per_run):
                mov = movements[i % 2]
                rows.append(
                    {
                        "subject": subject,
                        "run": run,
                        "condition": condition,
                        "label": int(condition == "execution"),
                        "task_family": family,
                        "movement": mov,
                        "pair_id": f"{me:02d}-{mi:02d}",
                    }
                )
    return pd.DataFrame(rows)


def test_ineligible_when_me_below_30():
    # 29 ME / 40 MI with otherwise good coverage
    pairs = [(3, 4), (5, 6), (7, 8)]
    meta = _epochs_from_pairs(1, pairs, n_per_run=10)
    # Trim ME to 29
    me_idx = meta.index[meta["condition"] == "execution"][:29]
    mi_idx = meta.index[meta["condition"] == "imagery"][:40]
    meta = meta.loc[list(me_idx) + list(mi_idx)]
    # Ensure pair usability: need both sides of pairs — rebuild carefully
    meta = _epochs_from_pairs(1, pairs, n_per_run=10)
    me = meta[meta["condition"] == "execution"].iloc[:29]
    mi = meta[meta["condition"] == "imagery"].iloc[:40]
    meta = pd.concat([me, mi], ignore_index=True)
    result = evaluate_participant(1, meta, _audit_all_valid(1), min_epochs_per_mode=30)
    assert result["eligible_primary"] is False
    assert "INSUFFICIENT_ME_EPOCHS" in result["reason_codes"]


def test_eligible_30_30_with_pair_coverage():
    # 2 uni + 1 bi pairs, 10 epochs/run → 30 ME / 30 MI
    pairs = [(3, 4), (5, 6), (7, 8)]
    meta = _epochs_from_pairs(2, pairs, n_per_run=10)
    assert (meta["condition"] == "execution").sum() == 30
    assert (meta["condition"] == "imagery").sum() == 30
    result = evaluate_participant(2, meta, _audit_all_valid(2), min_epochs_per_mode=30)
    assert result["eligible_primary"] is True
    assert result["reason_codes"] == "ELIGIBLE"
    assert result["eligible_min20"] is True
    assert result["eligible_min40"] is False


def test_only_unilateral_ineligible():
    pairs = [(3, 4), (7, 8), (11, 12)]
    meta = _epochs_from_pairs(3, pairs, n_per_run=12)
    result = evaluate_participant(3, meta, _audit_all_valid(3), min_epochs_per_mode=30)
    assert result["eligible_primary"] is False
    assert "MISSING_BILATERAL_PAIR" in result["reason_codes"]


def test_only_bilateral_ineligible():
    pairs = [(5, 6), (9, 10), (13, 14)]
    meta = _epochs_from_pairs(4, pairs, n_per_run=12)
    result = evaluate_participant(4, meta, _audit_all_valid(4), min_epochs_per_mode=30)
    assert result["eligible_primary"] is False
    assert "MISSING_UNILATERAL_PAIR" in result["reason_codes"]


def test_one_matched_pair_ineligible():
    pairs = [(3, 4)]
    meta = _epochs_from_pairs(5, pairs, n_per_run=40)
    # Still only one pair and missing bilateral
    result = evaluate_participant(5, meta, _audit_all_valid(5), min_epochs_per_mode=30)
    assert result["eligible_primary"] is False
    assert "INSUFFICIENT_MATCHED_PAIRS" in result["reason_codes"]


def test_structurally_invalid_run_handled():
    pairs = [(3, 4), (5, 6), (7, 8)]
    meta = _epochs_from_pairs(6, pairs, n_per_run=10)
    audit = _audit_all_valid(6)
    audit.loc[audit["run"] == 3, "structurally_valid"] = False
    result = evaluate_participant(6, meta, audit, min_epochs_per_mode=30)
    # Pair 3-4 becomes unusable; still have 7-8 uni and 5-6 bi → 20 ME/MI may fail 30 rule
    assert result["n_usable_matched_pairs"] == 2
    # epochs from invalid run still in metadata but pair dropped; ME count from runs 5,7 = 20
    assert result["eligible_primary"] is False
