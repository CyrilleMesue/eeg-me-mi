"""Feature extraction unit tests with synthetic epochs."""

import numpy as np
import pytest
from mne import create_info
from mne.io.array import RawArray
import mne

from eeg_me_mi.features import (
    BANDS,
    N_FEATURES,
    band_mask,
    e00_feature_names,
    e01_feature_names,
    extract_e00_log_bandpower_features,
    extract_e01_erd_features,
)
from eeg_me_mi.protocol import SENSORIMOTOR_CHANNELS


PREPROC = {
    "baseline_tmin": -2.0,
    "baseline_tmax": -0.5,
    "task_tmin": 0.5,
    "task_tmax": 3.5,
    "epoch_tmin": -2.0,
    "epoch_tmax": 3.5,
}


def _make_epochs(n_epochs: int = 4, sfreq: float = 80.0):
    info = create_info(list(SENSORIMOTOR_CHANNELS), sfreq=sfreq, ch_types="eeg")
    n_times = int(round((PREPROC["epoch_tmax"] - PREPROC["epoch_tmin"]) * sfreq)) + 1
    data = np.random.default_rng(0).normal(scale=1e-5, size=(n_epochs, len(SENSORIMOTOR_CHANNELS), n_times))
    # Inject mu-band oscillation in task window for realism.
    times = PREPROC["epoch_tmin"] + np.arange(n_times) / sfreq
    task = (times >= 0.5) & (times <= 3.5)
    for ch in range(len(SENSORIMOTOR_CHANNELS)):
        data[:, ch, task] += 2e-5 * np.sin(2 * np.pi * 10 * times[task])

    # Build via EpochsArray
    epochs = mne.EpochsArray(
        data,
        info,
        tmin=PREPROC["epoch_tmin"],
        verbose=False,
    )
    return epochs


def test_feature_counts_and_names():
    assert len(e01_feature_names()) == N_FEATURES == 42
    assert len(e00_feature_names()) == 42
    assert e01_feature_names()[0] == "FC5_mu"
    assert "C3_mu" in e01_feature_names()
    assert "C3_beta" in e01_feature_names()
    assert e01_feature_names() == e00_feature_names()


def test_band_boundary_no_double_count():
    freqs = np.array([8.0, 10.0, 12.0, 13.0, 20.0, 30.0])
    mu = band_mask(freqs, 8.0, 13.0, include_high=False)
    beta = band_mask(freqs, 13.0, 30.0, include_high=True)
    assert not np.any(mu & beta)
    assert freqs[mu].tolist() == [8.0, 10.0, 12.0]
    assert freqs[beta].tolist() == [13.0, 20.0, 30.0]


def test_e01_and_e00_shapes_finite():
    epochs = _make_epochs()
    X1, names1 = extract_e01_erd_features(epochs, PREPROC)
    X0, names0 = extract_e00_log_bandpower_features(epochs, PREPROC)
    assert X1.shape == (len(epochs), 42)
    assert X0.shape == (len(epochs), 42)
    assert names1 == e01_feature_names()
    assert names0 == e00_feature_names()
    assert np.isfinite(X1).all()
    assert np.isfinite(X0).all()


def test_e00_rejects_postcue_window(monkeypatch):
    epochs = _make_epochs()
    bad = dict(PREPROC)
    bad["baseline_tmax"] = 0.5  # would include post-cue
    with pytest.raises(ValueError, match="post-cue"):
        extract_e00_log_bandpower_features(epochs, bad)


def test_e01_windows_separated():
    assert PREPROC["baseline_tmax"] <= PREPROC["task_tmin"]
    epochs = _make_epochs()
    extract_e01_erd_features(epochs, PREPROC)
