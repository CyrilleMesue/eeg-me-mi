import numpy as np
import pandas as pd
import pytest

from eeg_me_mi.cv import assert_participant_disjoint, fold_assignment_table, make_group_folds


def test_folds_are_participant_disjoint_and_deterministic():
    groups = np.repeat(np.arange(1, 9), 4)
    a = make_group_folds(groups, 4, 2026)
    b = make_group_folds(groups, 4, 2026)
    for (_, atr, ate), (_, btr, bte) in zip(a, b):
        assert np.array_equal(atr, btr)
        assert np.array_equal(ate, bte)
        assert set(groups[atr]).isdisjoint(groups[ate])
    assert_participant_disjoint(fold_assignment_table(groups, 4, 2026))


def test_overlap_audit_fails_closed():
    bad = pd.DataFrame({"fold": [1, 1], "role": ["train", "test"], "subject": [7, 7]})
    with pytest.raises(AssertionError, match="overlap"):
        assert_participant_disjoint(bad)
