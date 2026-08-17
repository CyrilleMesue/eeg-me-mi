"""Tests for final sensitivity checks (fold filter + exclusions + immutability)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from eeg_me_mi.cv import (
    assert_participant_disjoint,
    filter_fold_assignments,
    make_group_folds_from_assignments,
)


EXCLUDED = {88, 92, 100}


def _frozen_folds() -> pd.DataFrame:
    path = Path("results/definitive/full/e01/erd_lr/fold_assignments.csv")
    if not path.exists():
        pytest.skip("definitive fold assignments missing")
    return pd.read_csv(path)


def test_exclude_exactly_s088_s092_s100():
    frozen = _frozen_folds()
    filtered = filter_fold_assignments(frozen, exclude_subjects=EXCLUDED)
    remaining = set(filtered["subject"].astype(int))
    assert remaining.isdisjoint(EXCLUDED)
    assert set(frozen["subject"].astype(int)) - remaining == EXCLUDED
    assert remaining == set(frozen["subject"].astype(int)) - EXCLUDED


def test_fold_preservation_after_removal():
    frozen = _frozen_folds()
    filtered = filter_fold_assignments(frozen, exclude_subjects=EXCLUDED)
    assert_participant_disjoint(filtered)
    for fold in sorted(frozen["fold"].unique()):
        before = set(
            frozen.loc[(frozen.fold == fold) & (frozen.role == "test"), "subject"].astype(int)
        )
        after = set(
            filtered.loc[(filtered.fold == fold) & (filtered.role == "test"), "subject"].astype(int)
        )
        assert after == before - EXCLUDED
        # remaining subjects keep identical fold membership
        for role in ("train", "test"):
            b = set(
                frozen.loc[(frozen.fold == fold) & (frozen.role == role), "subject"].astype(int)
            ) - EXCLUDED
            a = set(
                filtered.loc[(filtered.fold == fold) & (filtered.role == role), "subject"].astype(int)
            )
            assert a == b


def test_make_folds_from_assignments_indexes():
    frozen = _frozen_folds()
    filtered = filter_fold_assignments(frozen, exclude_subjects=EXCLUDED)
    subjects = sorted(filtered["subject"].unique())
    # Synthetic groups: one row per subject
    groups = np.asarray(subjects, dtype=int)
    folds = make_group_folds_from_assignments(groups, filtered)
    assert len(folds) == 5
    for fold, train_idx, test_idx, train_g, test_g in folds:
        assert set(train_g).isdisjoint(set(test_g))
        assert set(groups[train_idx]) == set(train_g)
        assert set(groups[test_idx]) == set(test_g)


def test_primary_result_immutability_on_disk():
    summary = Path("results/definitive/full/e01/erd_lr/summary.json")
    if not summary.exists():
        pytest.skip("definitive E01 summary missing")
    import json

    d = json.loads(summary.read_text())
    assert abs(float(d["balanced_accuracy"]) - 0.6179239767) < 1e-9
    assert int(float(d["n_participants"])) == 102


def test_definitive_not_targeted_by_final_outputs():
    # Guardrail: final sensitivity outputs live outside definitive/
    out = Path("results/final_sensitivity_checks")
    if out.exists():
        for p in out.rglob("*"):
            assert "results/definitive" not in str(p.resolve())


def test_rejection_audit_me_mi_totals_if_present():
    path = Path("results/final_sensitivity_checks/rejection_audit/rejection_by_condition.csv")
    if not path.exists():
        pytest.skip("rejection audit outputs missing")
    df = pd.read_csv(path)
    prim = df.loc[df["scope"] == "e01_primary_cohort"].set_index("condition")
    assert int(prim.loc["ME", "epochs_before"]) == 9110
    assert int(prim.loc["MI", "epochs_before"]) == 9079
    assert int(prim.loc["ME", "epochs_rejected"]) == 662
    assert int(prim.loc["MI", "epochs_rejected"]) == 587


def test_sampling_rate_summary_if_present():
    path = Path(
        "results/final_sensitivity_checks/sampling_rate/sampling_rate_sensitivity_summary.json"
    )
    if not path.exists():
        pytest.skip("sampling-rate outputs missing")
    import json

    d = json.loads(path.read_text())
    assert d["sensitivity_n"] == 99
    assert d["excluded_subjects"] == [88, 92, 100]
    assert d["conclusion"] == "STABLE"
    assert d["fold_handling"] == "frozen_outer_folds_minus_excluded_subjects"
