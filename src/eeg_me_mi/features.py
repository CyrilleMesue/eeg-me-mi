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

with FIR-safe windows (80 Hz half-support 0.825 s → ±0.8375 s boundary):

* baseline / reference: ``[baseline_tmin, baseline_tmax] = [-2.0, -0.8375]``
* task: ``[task_tmin, task_tmax] = [+0.8375, +3.5]``

The cue-adjacent interval ``(-0.8375, +0.8375)`` is excluded from confirmatory
spectral summaries because zero-phase FIR can smear information across cue onset.

E00 features
------------
Pre-cue run-state **log band power** (not ERD) on the same safe pre-cue interval:

    logBP = log(P_precue + eps)

with ``[e00_tmin, e00_tmax] = [-2.0, -0.8375]``.

E00 and E01 therefore share the same safe pre-cue spectral interval; E00 uses
absolute/log power while E01 uses that interval only as the ERD reference.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import scipy
from mne.time_frequency import psd_array_welch

from eeg_me_mi.filter_support import (
    assert_crop_outside_cue_support,
    e00_window_from_preproc,
    e01_windows_from_preproc,
    measure_fir_support,
)
from eeg_me_mi.protocol import SENSORIMOTOR_CHANNELS

# Canonical band edges; 13 Hz belongs to beta only.
BANDS: dict[str, tuple[float, float]] = {
    "mu": (8.0, 13.0),
    "beta": (13.0, 30.0),
}

N_FEATURES = len(SENSORIMOTOR_CHANNELS) * len(BANDS)  # 42


def feature_names(prefix: str | None = None, channels=SENSORIMOTOR_CHANNELS) -> list[str]:
    """Deterministic interpretable names: ``C3_mu``, ``C3_beta``, ..."""
    names: list[str] = []
    for band in BANDS:
        for channel in channels:
            base = f"{channel}_{band}"
            names.append(f"{prefix}_{base}" if prefix else base)
    return names


def e01_feature_names(channels=SENSORIMOTOR_CHANNELS) -> list[str]:
    return feature_names(channels=channels)


def e00_feature_names(channels=SENSORIMOTOR_CHANNELS) -> list[str]:
    return feature_names(channels=channels)


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


def extract_e01_erd_features(
    epochs, preproc: dict[str, Any], *, channels=SENSORIMOTOR_CHANNELS
) -> tuple[np.ndarray, list[str]]:
    """Baseline-referenced mu/beta ERD features (default 42-D sensorimotor)."""
    wins = e01_windows_from_preproc(preproc)
    half = float(wins["half_support_sec"])

    baseline_ep = epochs.copy().crop(tmin=wins["baseline_tmin"], tmax=wins["baseline_tmax"])
    task_ep = epochs.copy().crop(tmin=wins["task_tmin"], tmax=wins["task_tmax"])
    assert_crop_outside_cue_support(baseline_ep.times, half_support_sec=half, side="pre")
    assert_crop_outside_cue_support(task_ep.times, half_support_sec=half, side="post")

    baseline = baseline_ep.get_data(copy=False)
    task = task_ep.get_data(copy=False)

    sfreq = float(epochs.info["sfreq"])
    baseline_power = band_powers(baseline, sfreq)
    task_power = band_powers(task, sfreq)

    eps = np.finfo(float).tiny
    blocks = []
    for band in BANDS:
        erd = 10.0 * np.log10((task_power[band] + eps) / (baseline_power[band] + eps))
        blocks.append(erd)
    X = np.concatenate(blocks, axis=1)
    names = e01_feature_names(channels=channels)
    n_feat = len(channels) * len(BANDS)
    if X.shape[1] != n_feat:
        raise ValueError(f"Expected {n_feat} E01 features, got {X.shape[1]}")
    if not np.isfinite(X).all():
        raise ValueError("Non-finite E01 features found")
    ch_names = list(epochs.ch_names)
    if ch_names != list(channels):
        idx = [ch_names.index(ch) for ch in channels]
        X = np.concatenate(
            [X[:, len(channels) * b : len(channels) * (b + 1)][:, idx] for b in range(len(BANDS))],
            axis=1,
        )
    return X.astype(np.float64), names


def extract_e00_log_bandpower_features(
    epochs, preproc: dict[str, Any], *, channels=SENSORIMOTOR_CHANNELS
) -> tuple[np.ndarray, list[str]]:
    """Leakage-safe pre-cue log band-power features (no cue/post-cue support)."""
    tmin, tmax = e00_window_from_preproc(preproc)
    sfreq = float(epochs.info["sfreq"])
    support = measure_fir_support(
        sfreq=sfreq,
        l_freq=float(preproc["l_freq"]),
        h_freq=float(preproc["h_freq"]),
    )
    half = float(support["half_support_sec"])
    # Require crop entirely outside the theoretical support of an impulse at t=0.
    if tmax > -half + 1e-12:
        raise ValueError(
            f"E00 tmax={tmax} overlaps zero-phase FIR half-support {half:.6f}s; "
            "refuse potentially leaky window"
        )
    if tmax >= 0:
        raise ValueError("E00 window must not include post-cue samples")

    data = _crop_data(epochs, tmin, tmax)
    cropped = epochs.copy().crop(tmin=tmin, tmax=tmax)
    assert_crop_outside_cue_support(cropped.times, half_support_sec=half, side="pre")
    if cropped.times.max() >= 0:
        raise AssertionError("E00 features used post-cue samples")

    powers = band_powers(data, sfreq)
    eps = np.finfo(float).tiny
    blocks = []
    for band in BANDS:
        blocks.append(np.log(powers[band] + eps))
    X = np.concatenate(blocks, axis=1)
    names = e00_feature_names(channels=channels)
    n_feat = len(channels) * len(BANDS)
    if X.shape[1] != n_feat:
        raise ValueError(f"Expected {n_feat} E00 features, got {X.shape[1]}")
    if not np.isfinite(X).all():
        raise ValueError("Non-finite E00 features found")
    ch_names = list(epochs.ch_names)
    if ch_names != list(channels):
        idx = [ch_names.index(ch) for ch in channels]
        X = np.concatenate(
            [X[:, len(channels) * b : len(channels) * (b + 1)][:, idx] for b in range(len(BANDS))],
            axis=1,
        )
    return X.astype(np.float64), names


def task_window_array(epochs, preproc: dict[str, Any]) -> np.ndarray:
    """Return (n, ch, time) array for CSP/Riemann on the FIR-safe task window."""
    wins = e01_windows_from_preproc(preproc)
    task_ep = epochs.copy().crop(tmin=wins["task_tmin"], tmax=wins["task_tmax"])
    assert_crop_outside_cue_support(
        task_ep.times, half_support_sec=float(wins["half_support_sec"]), side="post"
    )
    return task_ep.get_data(copy=False).astype(np.float64)
