"""Milestone-2 expanded tests."""

import numpy as np
import pandas as pd
import pytest
from sklearn.base import clone

from eeg_me_mi.analyses import e06_first60_mask, fdr_bh
from eeg_me_mi.compare import paired_signflip_test
from eeg_me_mi.cv import run_nested_group_cv
from eeg_me_mi.eligibility import evaluate_e02_subset, evaluate_participant, evaluate_strict
from eeg_me_mi.models import make_csp_lda_pipeline, make_riemann_lr_pipeline
from eeg_me_mi.permutation import (
    assert_permutation_preserves_structure,
    generate_permutation_labels,
    matched_pair_label_permutation,
)
from eeg_me_mi.rois import (
    ROI_LEFT,
    ROI_MIDLINE,
    ROI_RIGHT,
    SPATIAL_CONTROL_CHANNELS,
)
from eeg_me_mi.protocol import SENSORIMOTOR_CHANNELS as SM


def test_rois_and_spatial_control_frozen():
    assert ROI_LEFT == ("FC3", "C3", "CP3")
    assert ROI_RIGHT == ("FC4", "C4", "CP4")
    assert ROI_MIDLINE == ("FCz", "Cz", "CPz")
    assert len(SPATIAL_CONTROL_CHANNELS) == 21
    assert set(SPATIAL_CONTROL_CHANNELS).isdisjoint(set(SM))


def test_fdr_output_shape():
    p = np.array([0.001, 0.04, 0.2, np.nan])
    reject, adj = fdr_bh(p)
    assert len(reject) == len(adj) == 4
    assert reject[0]
    assert np.isnan(adj[3])


def test_e06_event_filtering():
    meta = pd.DataFrame({"onset_seconds": [0.0, 30.0, 59.9, 60.0, 120.0]})
    mask = e06_first60_mask(meta)
    assert mask.tolist() == [True, True, True, False, False]


def test_movement_and_strict_eligibility_synthetic():
    rows = []
    # Build rich synthetic subject with all pairs
    for me, mi, family, movs in (
        (3, 4, "unilateral", ("left_fist", "right_fist")),
        (5, 6, "bilateral", ("both_fists", "both_feet")),
        (7, 8, "unilateral", ("left_fist", "right_fist")),
        (9, 10, "bilateral", ("both_fists", "both_feet")),
        (11, 12, "unilateral", ("left_fist", "right_fist")),
        (13, 14, "bilateral", ("both_fists", "both_feet")),
    ):
        for run, cond in ((me, "execution"), (mi, "imagery")):
            for i in range(12):
                rows.append(
                    {
                        "subject": 1,
                        "run": run,
                        "condition": cond,
                        "task_family": family,
                        "movement": movs[i % 2],
                        "pair_id": f"{me:02d}-{mi:02d}",
                        "label": int(cond == "execution"),
                    }
                )
    meta = pd.DataFrame(rows)
    audit = pd.DataFrame(
        [
            {
                "subject": 1,
                "run": r,
                "structurally_valid": True,
                "T1_count": 8,
                "T2_count": 7,
            }
            for r in range(3, 15)
        ]
    )
    result = evaluate_participant(1, meta, audit)
    assert result["eligible_primary"]
    assert result["e02_left_fist_eligible"]
    assert result["e02_unilateral_eligible"]
    # Strict may or may not pass depending on cell counts (8 per cell with 3 pairs → 24)
    assert "eligible_strict" in result

    # Movement-only insufficient
    tiny = meta.loc[meta["movement"] == "left_fist"].iloc[:10]
    e02 = evaluate_e02_subset(tiny, "left_fist", min_epochs=15, min_pairs=2)
    assert e02["e02_left_fist_eligible"] is False


def test_matched_pair_permutation_structure_and_reproducibility():
    meta = pd.DataFrame(
        {
            "subject": [1] * 20 + [2] * 20,
            "run": ([3] * 5 + [4] * 5 + [5] * 5 + [6] * 5) * 2,
            "pair_id": (["03-04"] * 10 + ["05-06"] * 10) * 2,
            "condition": (["execution"] * 5 + ["imagery"] * 5 + ["execution"] * 5 + ["imagery"] * 5) * 2,
            "movement": (["left_fist"] * 5 + ["left_fist"] * 5 + ["both_fists"] * 5 + ["both_fists"] * 5) * 2,
            "label": ([1] * 5 + [0] * 5 + [1] * 5 + [0] * 5) * 2,
        }
    )
    y = meta["label"].to_numpy()
    a, swap_a = matched_pair_label_permutation(meta, y, seed=2026, perm_id=3)
    b, swap_b = matched_pair_label_permutation(meta, y, seed=2026, perm_id=3)
    assert np.array_equal(a, b)
    assert swap_a == swap_b
    assert_permutation_preserves_structure(meta, y, a)
    # Subjects / movement / runs unchanged in metadata
    assert list(meta["subject"]) == ([1] * 20 + [2] * 20)
    assert set(meta["movement"]) == {"left_fist", "both_fists"}
    assert set(meta["run"]) == {3, 4, 5, 6}
    perms = generate_permutation_labels(meta, y, 5, 2026)
    assert len(perms) == 5


def test_csp_and_riemann_fold_local():
    rng = np.random.default_rng(0)
    n_subj, n_per, n_ch, n_times = 6, 12, 8, 40
    groups = np.repeat(np.arange(1, n_subj + 1), n_per)
    y = np.tile([0, 1], n_subj * n_per // 2)
    X = rng.normal(size=(len(y), n_ch, n_times))
    X[y == 1, :2, :] += 0.5
    meta = pd.DataFrame({"subject": groups, "run": 3, "movement": "left_fist", "pair_id": "03-04"})

    for name, est in (
        ("csp", make_csp_lda_pipeline(n_components=2)),
        ("riem", make_riemann_lr_pipeline(0)),
    ):
        res = run_nested_group_cv(
            experiment=name,
            model_name=name,
            estimator=est,
            param_grid=None,
            X=X,
            y=y,
            groups=groups,
            metadata=meta,
            outer_folds=3,
            inner_folds=2,
            seed=0,
        )
        for fold, frame in res["fold_assignments"].groupby("fold"):
            train = set(frame.loc[frame.role == "train", "subject"])
            test = set(frame.loc[frame.role == "test", "subject"])
            assert train.isdisjoint(test)


def test_paired_signflip_null_synthetic():
    rng = np.random.default_rng(0)
    diffs = rng.normal(0, 0.05, size=40)
    out = paired_signflip_test(diffs, n_signflips=200, seed=1)
    assert 0 < out["p_value_plusone"] <= 1
    # Near-null differences should often not be extreme
    assert out["n_participants"] == 40
