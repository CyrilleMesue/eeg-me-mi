"""E00 and E01 feature extraction.

Band-boundary rule (frozen)
---------------------------
Welch frequency bins are assigned so the shared 13 Hz edge is not double-counted:

* mu  = bins with ``8 <= f < 13``
* beta = bins with ``13 <= f <= 30``

E01 features
------------
Baseline-referenced ERD/ERS in dB:

    ERD_dB = 10 * log10(P_task / P_baseline)

with task window [task_tmin, task_tmax] and baseline [baseline_tmin, baseline_tmax].

E00 features
------------
Pre-cue run-state log band power on [-2.0, -0.5] s only:

    logBP = log(P_precue + eps)

E00 does **not** use a post-cue interval and does **not** form an ERD ratio
against the same window. Zero-phase FIR filtering is applied to continuous data
before epoching; the -0.5 s upper bound leaves a margin before cue onset at 0 s.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import scipy
from mne.time_frequency import psd_array_welch

from eeg_me_mi.protocol import SENSORIMOTOR_CHANNELS

# Canonical band edges; 13 Hz belongs to beta only.
BANDS: dict[str, tuple[float, float]] = {
    "mu": (8.0, 13.0),
    "beta": (13.0, 30.0),
}

N_FEATURES = len(SENSORIMOTOR_CHANNELS) * len(BANDS)  # 42


def feature_names(prefix: str | None = None) -> list[str]:
    """Deterministic interpretable names: ``C3_mu``, ``C3_beta``, ..."""
    names: list[str] = []
    for band in BANDS:
        for channel in SENSORIMOTOR_CHANNELS:
            base = f"{channel}_{band}"
            names.append(f"{prefix}_{base}" if prefix else base)
    return names


def e01_feature_names() -> list[str]:
    return feature_names()


def e00_feature_names() -> list[str]:
    return feature_names()


def band_mask(freqs: np.ndarray, low: float, high: float, *, include_high: bool) -> np.ndarray:
    if include_high:
        return (freqs >= low) & (freqs <= high)
    return (freqs >= low) & (freqs < high)


def band_powers(data: np.ndarray, sfreq: float, bands: dict[str, tuple[float, float]] = BANDS) -> dict[str, np.ndarray]:
    """Welch band power; ``data`` shape (n_epochs, n_channels, n_times)."""
    n_times = data.shape[-1]
    n_fft = min(256, n_times)
    psd, freqs = psd_array_welch(
        data,
        sfreq=sfreq,
        fmin=min(v[0] for v in bands.values()),
        fmax=max(v[1] for v in bands.values()),
        n_fft=n_fft,
        n_per_seg=n_fft,
        n_overlap=n_fft // 2,
        average="mean",
        verbose=False,
    )
    output: dict[str, np.ndarray] = {}
    for name, (low, high) in bands.items():
        # mu: [8, 13); beta: [13, 30]
        include_high = high >= 30.0
        mask = band_mask(freqs, low, high, include_high=include_high)
        if not np.any(mask):
            raise ValueError(f"No frequency bins for band {name} ({low}-{high})")
        output[name] = scipy.integrate.trapezoid(psd[..., mask], freqs[mask], axis=-1)
    return output


def _crop_data(epochs, tmin: float, tmax: float) -> np.ndarray:
    cropped = epochs.copy().crop(tmin=tmin, tmax=tmax)
    times = cropped.times
    if times[0] < tmin - 1e-9 or times[-1] > tmax + 1e-9:
        raise AssertionError("Cropped window exceeds requested bounds")
    return cropped.get_data(copy=False)


def extract_e01_erd_features(epochs, preproc: dict[str, Any]) -> tuple[np.ndarray, list[str]]:
    """42-D baseline-referenced mu/beta ERD features."""
    baseline = _crop_data(epochs, float(preproc["baseline_tmin"]), float(preproc["baseline_tmax"]))
    task = _crop_data(epochs, float(preproc["task_tmin"]), float(preproc["task_tmax"]))
    # Explicit separation assertion for leakage/window tests.
    assert float(preproc["baseline_tmax"]) <= float(preproc["task_tmin"])

    sfreq = float(epochs.info["sfreq"])
    baseline_power = band_powers(baseline, sfreq)
    task_power = band_powers(task, sfreq)

    eps = np.finfo(float).tiny
    blocks = []
    for band in BANDS:
        erd = 10.0 * np.log10((task_power[band] + eps) / (baseline_power[band] + eps))
        blocks.append(erd)
    X = np.concatenate(blocks, axis=1)
    names = e01_feature_names()
    if X.shape[1] != N_FEATURES:
        raise ValueError(f"Expected {N_FEATURES} E01 features, got {X.shape[1]}")
    if not np.isfinite(X).all():
        raise ValueError("Non-finite E01 features found")
    # Align columns to SENSORIMOTOR_CHANNELS order regardless of epoch channel order.
    ch_names = list(epochs.ch_names)
    if ch_names != list(SENSORIMOTOR_CHANNELS):
        # Rebuild in canonical order.
        idx = [ch_names.index(ch) for ch in SENSORIMOTOR_CHANNELS]
        X = np.concatenate(
            [X[:, len(SENSORIMOTOR_CHANNELS) * b : len(SENSORIMOTOR_CHANNELS) * (b + 1)][:, idx] for b in range(len(BANDS))],
            axis=1,
        )
    return X.astype(np.float64), names


def extract_e00_log_bandpower_features(epochs, preproc: dict[str, Any]) -> tuple[np.ndarray, list[str]]:
    """42-D pre-cue log band-power features (no post-cue samples)."""
    tmin = float(preproc["baseline_tmin"])  # -2.0
    tmax = float(preproc["baseline_tmax"])  # -0.5
    if tmax > 0:
        raise ValueError("E00 window must not include post-cue samples")
    data = _crop_data(epochs, tmin, tmax)
    # Hard guard: cropped times must be strictly pre-cue.
    cropped = epochs.copy().crop(tmin=tmin, tmax=tmax)
    if cropped.times.max() > -0.5 + 1e-9:
        raise AssertionError("E00 features used samples after -0.5 s")
    if cropped.times.max() >= 0:
        raise AssertionError("E00 features used post-cue samples")

    powers = band_powers(data, float(epochs.info["sfreq"]))
    eps = np.finfo(float).tiny
    blocks = []
    for band in BANDS:
        blocks.append(np.log(powers[band] + eps))
    X = np.concatenate(blocks, axis=1)
    names = e00_feature_names()
    if X.shape[1] != N_FEATURES:
        raise ValueError(f"Expected {N_FEATURES} E00 features, got {X.shape[1]}")
    if not np.isfinite(X).all():
        raise ValueError("Non-finite E00 features found")
    ch_names = list(epochs.ch_names)
    if ch_names != list(SENSORIMOTOR_CHANNELS):
        idx = [ch_names.index(ch) for ch in SENSORIMOTOR_CHANNELS]
        X = np.concatenate(
            [X[:, len(SENSORIMOTOR_CHANNELS) * b : len(SENSORIMOTOR_CHANNELS) * (b + 1)][:, idx] for b in range(len(BANDS))],
            axis=1,
        )
    return X.astype(np.float64), names
