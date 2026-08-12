"""FIR temporal support for the frozen continuous preprocessing filter.

Under MNE ``phase='zero'`` FIR filtering, an impulse at time ``t0`` influences
output samples in ``[t0 - half_support, t0 + half_support]``. Therefore
nominally pre-cue samples with ``t > -half_support`` can carry cue/post-cue
information after zero-phase filtering.
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
        # Lower transition is the binding auto bandwidth for this design.
        "reported_l_trans_hz": 2.0,
        "reported_h_trans_hz": 7.5,
    }


def leakage_safe_e00_tmax(sfreq: float, half_support_sec: float | None = None) -> float:
    """Last inclusive crop time guaranteed free of influence from ``t >= 0``.

    Samples at ``t = -half_support`` remain in the theoretical support of an
    impulse at cue onset.  We therefore exclude that boundary sample:

        tmax = -(half_samples + 1) / sfreq
    """
    if half_support_sec is None:
        half_support_sec = float(measure_fir_support(sfreq=sfreq)["half_support_sec"])
    half_samples = int(round(half_support_sec * float(sfreq)))
    return float(-(half_samples + 1) / float(sfreq))


def e00_window_from_preproc(preproc: dict[str, Any]) -> tuple[float, float]:
    """Resolve leakage-safe E00 ``(tmin, tmax)`` from preprocessing config.

    Prefer explicit ``e00_tmin`` / ``e00_tmax`` when present; otherwise derive
    ``tmax`` from the FIR half-support at ``target_sfreq``.
    """
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
