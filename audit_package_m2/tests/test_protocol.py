"""Expanded protocol mapping tests."""

import pytest

from eeg_me_mi.protocol import (
    MATCHED_RUN_PAIRS,
    ME_RUNS,
    MI_RUNS,
    RUN_INFO,
    condition_label,
    matched_pair,
    movement_name,
    pair_id,
    repetition,
    task_family,
)


def test_run_condition_mapping():
    assert set(ME_RUNS) == {3, 5, 7, 9, 11, 13}
    assert set(MI_RUNS) == {4, 6, 8, 10, 12, 14}
    assert {run for run in RUN_INFO if condition_label(run) == 1} == set(ME_RUNS)
    assert {run for run in RUN_INFO if condition_label(run) == 0} == set(MI_RUNS)


@pytest.mark.parametrize(
    "run,t1,t2",
    [
        (3, "left_fist", "right_fist"),
        (4, "left_fist", "right_fist"),
        (7, "left_fist", "right_fist"),
        (8, "left_fist", "right_fist"),
        (11, "left_fist", "right_fist"),
        (12, "left_fist", "right_fist"),
        (5, "both_fists", "both_feet"),
        (6, "both_fists", "both_feet"),
        (9, "both_fists", "both_feet"),
        (10, "both_fists", "both_feet"),
        (13, "both_fists", "both_feet"),
        (14, "both_fists", "both_feet"),
    ],
)
def test_movement_mapping_all_task_runs(run, t1, t2):
    assert movement_name(run, "T1") == t1
    assert movement_name(run, "T2") == t2


def test_unilateral_bilateral_mapping():
    unilateral = {3, 4, 7, 8, 11, 12}
    bilateral = {5, 6, 9, 10, 13, 14}
    assert {r for r in RUN_INFO if task_family(r) == "unilateral"} == unilateral
    assert {r for r in RUN_INFO if task_family(r) == "bilateral"} == bilateral


def test_repetition_mapping():
    assert repetition(3) == repetition(4) == 1
    assert repetition(5) == repetition(6) == 1
    assert repetition(11) == repetition(12) == 3
    assert repetition(13) == repetition(14) == 3


def test_matched_run_pairs():
    assert MATCHED_RUN_PAIRS == ((3, 4), (5, 6), (7, 8), (9, 10), (11, 12), (13, 14))
    for me, mi in MATCHED_RUN_PAIRS:
        assert matched_pair(me) == (me, mi)
        assert matched_pair(mi) == (me, mi)
        assert pair_id(me) == pair_id(mi) == f"{me:02d}-{mi:02d}"


def test_invalid_annotation_fails():
    with pytest.raises(ValueError):
        movement_name(3, "T0")


def test_baseline_runs_rejected():
    with pytest.raises(ValueError):
        condition_label(1)
