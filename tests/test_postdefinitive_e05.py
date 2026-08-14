"""Tests for post-definitive E05 threshold sentinel (None = no rejection)."""

from eeg_me_mi.preprocess import _THRESHOLD_DEFAULT, apply_ptp_threshold
import numpy as np
import pandas as pd
import mne


def test_apply_ptp_none_and_nonpositive_keep_all():
    # Minimal synthetic epochs with metadata ptp_uv
    info = mne.create_info(["C3", "C4"], 80.0, ch_types="eeg")
    data = np.random.randn(5, 2, 80) * 1e-6
    meta = pd.DataFrame({"ptp_uv": [50.0, 100.0, 180.0, 250.0, 300.0]})
    epochs = mne.EpochsArray(data, info, tmin=-1.0, metadata=meta, verbose=False)
    kept = apply_ptp_threshold(epochs, None)
    assert len(kept) == 5
    kept0 = apply_ptp_threshold(epochs, 0.0)
    assert len(kept0) == 5
    kept200 = apply_ptp_threshold(epochs, 200.0)
    assert len(kept200) == 3
    kept150 = apply_ptp_threshold(epochs, 150.0)
    assert len(kept150) == 2


def test_threshold_default_sentinel_distinct_from_none():
    assert _THRESHOLD_DEFAULT is not None
    assert _THRESHOLD_DEFAULT != 200.0
