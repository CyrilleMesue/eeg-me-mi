import pytest

from eeg_me_mi.protocol import RUN_INFO, condition_label, movement_name


def test_run_condition_mapping():
    assert {run for run in RUN_INFO if condition_label(run) == 1} == {3, 5, 7, 9, 11, 13}
    assert {run for run in RUN_INFO if condition_label(run) == 0} == {4, 6, 8, 10, 12, 14}


@pytest.mark.parametrize("run,t1,t2", [(3, "left_fist", "right_fist"), (4, "left_fist", "right_fist"), (5, "both_fists", "both_feet"), (6, "both_fists", "both_feet")])
def test_movement_mapping(run, t1, t2):
    assert movement_name(run, "T1") == t1
    assert movement_name(run, "T2") == t2


def test_invalid_annotation_fails():
    with pytest.raises(ValueError):
        movement_name(3, "T0")

