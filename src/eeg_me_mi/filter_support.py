"""FIR temporal support for the frozen continuous preprocessing filter.

Under MNE ``phase='zero'`` FIR filtering, an impulse at time ``t0`` influences
output samples in ``[t0 - half_support, t0 + half_support]``.

At the frozen target rate (80 Hz) the designed band-pass has:

* 133 taps;
* half-support = 66 samples = 0.825 s;
* safe exclusive boundary offset = 67/80 = **0.8375 s**.

Confirmatory spectral windows therefore exclude the cue-adjacent interval
``(-0.8375, +0.8375)`` because samples there can receive contributions across
cue onset.
"""

from __future__ import annotations

from typing import Any

import mne
from mne.filter import create_filter


# Frozen scientific filter settings matching ``load_and_preprocess_raw``.
FILTER_METHOD = "fir"
FIR_DESIGN = "firwin"
FIR_WINDOW = "hamming"
PHASE = "zero"
FILTER_LENGTH = "auto"
L_TRANS = "auto"
H_TRANS = "auto"

# Frozen at 80 Hz for the actual pipeline (resample-then-filter).
FROZEN_SAFE_BOUNDARY_SEC = 0.8375  # (66 + 1) / 80


def measure_fir_support(
    *,
    sfreq: float,
    l_freq: float = 8.0,
    h_freq: float = 30.0,
) -> dict[str, Any]:
    """Return FIR length / half-support for the frozen band-pass design."""
    h = create_filter(
        data=None,
        sfreq=float(sfreq),
        l_freq=float(l_freq),
        h_freq=float(h_freq),
        method=FILTER_METHOD,
        fir_design=FIR_DESIGN,
        fir_window=FIR_WINDOW,
        phase=PHASE,
        filter_length=FILTER_LENGTH,
        l_trans_bandwidth=L_TRANS,
        h_trans_bandwidth=H_TRANS,
        verbose=False,
    )
    n = int(len(h))
    half_samples = (n - 1) / 2.0
    half_sec = half_samples / float(sfreq)
    safe_boundary = float((half_samples + 1) / float(sfreq))
    return {
        "mne_version": mne.__version__,
        "sfreq": float(sfreq),
        "l_freq": float(l_freq),
        "h_freq": float(h_freq),
        "method": FILTER_METHOD,
        "fir_design": FIR_DESIGN,
        "fir_window": FIR_WINDOW,
        "phase": PHASE,
        "filter_length_setting": FILTER_LENGTH,
        "l_trans_bandwidth": L_TRANS,
        "h_trans_bandwidth": H_TRANS,
        "fir_length_samples": n,
        "fir_duration_sec": float(n / float(sfreq)),
        "half_support_samples": float(half_samples),
        "half_support_sec": float(half_sec),
        "safe_boundary_sec": safe_boundary,
        # Lower transition is the binding auto bandwidth for this design.
        "reported_l_trans_hz": 2.0,
        "reported_h_trans_hz": 7.5,
    }


def leakage_safe_boundary_sec(sfreq: float, half_support_sec: float | None = None) -> float:
    """Positive safe offset excluding the ±half_support boundary sample.

        boundary = (half_samples + 1) / sfreq
    """
    if half_support_sec is None:
        half_support_sec = float(measure_fir_support(sfreq=sfreq)["half_support_sec"])
    half_samples = int(round(half_support_sec * float(sfreq)))
    return float((half_samples + 1) / float(sfreq))


def leakage_safe_e00_tmax(sfreq: float, half_support_sec: float | None = None) -> float:
    """Last inclusive pre-cue crop time free of influence from ``t >= 0``."""
    return float(-leakage_safe_boundary_sec(sfreq, half_support_sec))


def leakage_safe_task_tmin(sfreq: float, half_support_sec: float | None = None) -> float:
    """First inclusive post-cue crop time free of influence from ``t <= 0``."""
    return float(leakage_safe_boundary_sec(sfreq, half_support_sec))


def e00_window_from_preproc(preproc: dict[str, Any]) -> tuple[float, float]:
    """Resolve leakage-safe E00 ``(tmin, tmax)`` from preprocessing config."""
    tmin = float(preproc.get("e00_tmin", preproc.get("baseline_tmin", -2.0)))
    if "e00_tmax" in preproc:
        tmax = float(preproc["e00_tmax"])
    else:
        support = measure_fir_support(
            sfreq=float(preproc["target_sfreq"]),
            l_freq=float(preproc["l_freq"]),
            h_freq=float(preproc["h_freq"]),
        )
        tmax = leakage_safe_e00_tmax(float(preproc["target_sfreq"]), support["half_support_sec"])
    if tmax >= 0:
        raise ValueError("E00 tmax must be strictly pre-cue")
    if tmin >= tmax:
        raise ValueError(f"Invalid E00 window [{tmin}, {tmax}]")
    return tmin, tmax


def e01_windows_from_preproc(preproc: dict[str, Any]) -> dict[str, float]:
    """Return E01 baseline/task bounds and validate FIR-safe exclusions."""
    sfreq = float(preproc["target_sfreq"])
    support = measure_fir_support(
        sfreq=sfreq,
        l_freq=float(preproc["l_freq"]),
        h_freq=float(preproc["h_freq"]),
    )
    half = float(support["half_support_sec"])
    safe = float(support["safe_boundary_sec"])
    b_tmin = float(preproc["baseline_tmin"])
    b_tmax = float(preproc["baseline_tmax"])
    t_tmin = float(preproc["task_tmin"])
    t_tmax = float(preproc["task_tmax"])

    if b_tmax > -half + 1e-12:
        raise ValueError(
            f"E01 baseline_tmax={b_tmax} overlaps FIR half-support {half:.6f}s "
            f"(require baseline_tmax <= {-safe:.6f}); refuse historical -0.5 window"
        )
    if t_tmin < half - 1e-12:
        raise ValueError(
            f"E01 task_tmin={t_tmin} overlaps FIR half-support {half:.6f}s "
            f"(require task_tmin >= {safe:.6f}); refuse historical +0.5 window"
        )
    if b_tmax > t_tmin:
        raise ValueError("E01 baseline must end before task begins")
    if b_tmin >= b_tmax or t_tmin >= t_tmax:
        raise ValueError("Invalid E01 baseline/task window ordering")
    return {
        "baseline_tmin": b_tmin,
        "baseline_tmax": b_tmax,
        "task_tmin": t_tmin,
        "task_tmax": t_tmax,
        "half_support_sec": half,
        "safe_boundary_sec": safe,
    }


def assert_crop_outside_cue_support(
    times,
    *,
    half_support_sec: float,
    side: str,
) -> None:
    """Assert cropped sample times lie outside cue-crossing FIR support."""
    import numpy as np

    times = np.asarray(times, dtype=float)
    if side == "pre":
        if times.max() >= -half_support_sec + 1e-12:
            raise AssertionError(
                f"Pre-cue crop includes FIR-supported samples "
                f"(max_t={times.max()}, half_support={half_support_sec})"
            )
    elif side == "post":
        if times.min() <= half_support_sec - 1e-12:
            raise AssertionError(
                f"Post-cue crop includes FIR-supported samples "
                f"(min_t={times.min()}, half_support={half_support_sec})"
            )
    else:
        raise ValueError(f"Unknown side={side!r}")
