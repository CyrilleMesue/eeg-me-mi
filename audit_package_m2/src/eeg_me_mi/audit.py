"""Reusable raw-data audit for EEGMMIDB task runs."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

import mne
import numpy as np
import pandas as pd
from mne.datasets import eegbci
from mne.io import read_raw_edf

from eeg_me_mi.protocol import (
    ANOMALY_WATCHLIST,
    EXPECTED_ANNOTATIONS,
    SENSORIMOTOR_CHANNELS,
    condition_name,
    run_definition,
)


def resolve_edf_path(data_root: Path, subject: int, run: int) -> Path | None:
    """Locate an EDF without downloading."""
    candidates = [
        data_root
        / "MNE-eegbci-data"
        / "files"
        / "eegmmidb"
        / "1.0.0"
        / f"S{subject:03d}"
        / f"S{subject:03d}R{run:02d}.edf",
        data_root / f"S{subject:03d}" / f"S{subject:03d}R{run:02d}.edf",
        data_root / f"S{subject:03d}R{run:02d}.edf",
    ]
    for path in candidates:
        if path.exists():
            return path
    return None


def ensure_edf(data_root: Path, subject: int, run: int, *, download: bool = True) -> Path | None:
    existing = resolve_edf_path(data_root, subject, run)
    if existing is not None:
        return existing
    if not download:
        return None
    data_root.mkdir(parents=True, exist_ok=True)
    files = eegbci.load_data(
        subject,
        runs=[run],
        path=str(data_root),
        update_path=False,
        verbose=False,
    )
    if not files:
        return None
    return Path(files[0])


def _annotation_counts(raw: mne.io.BaseRaw) -> dict[str, int]:
    descriptions = list(raw.annotations.description)
    counts = {name: descriptions.count(name) for name in EXPECTED_ANNOTATIONS}
    unexpected = sorted({d for d in descriptions if d not in EXPECTED_ANNOTATIONS})
    counts["unexpected_annotations"] = "|".join(unexpected) if unexpected else ""
    counts["annotation_count"] = len(descriptions)
    return counts


def audit_run(
    subject: int,
    run: int,
    data_root: Path,
    *,
    download: bool = True,
) -> dict[str, Any]:
    """Audit one participant/run recording."""
    info = run_definition(run)
    row: dict[str, Any] = {
        "subject": subject,
        "run": run,
        "condition": info.condition,
        "task_family": info.task_family,
        "repetition": info.repetition,
        "in_anomaly_watchlist": subject in ANOMALY_WATCHLIST,
        "file_exists": False,
        "downloaded_or_cached": False,
        "source_file": "",
        "sfreq": np.nan,
        "n_channels": np.nan,
        "channel_names": "",
        "duration_sec": np.nan,
        "annotation_count": np.nan,
        "T0_count": np.nan,
        "T1_count": np.nan,
        "T2_count": np.nan,
        "unexpected_annotations": "",
        "missing_sensorimotor_channels": "",
        "structurally_valid": False,
        "invalidity_reason": "",
    }

    try:
        path = ensure_edf(data_root, subject, run, download=download)
        if path is None:
            row["invalidity_reason"] = "missing_file"
            return row

        row["file_exists"] = True
        row["downloaded_or_cached"] = True
        row["source_file"] = path.name

        raw = read_raw_edf(path, preload=False, verbose=False)
        eegbci.standardize(raw)
        raw.pick(picks="eeg")

        row["sfreq"] = float(raw.info["sfreq"])
        row["n_channels"] = int(len(raw.ch_names))
        row["channel_names"] = "|".join(raw.ch_names)
        row["duration_sec"] = float(raw.n_times / raw.info["sfreq"])

        counts = _annotation_counts(raw)
        row["annotation_count"] = counts["annotation_count"]
        row["T0_count"] = counts["T0"]
        row["T1_count"] = counts["T1"]
        row["T2_count"] = counts["T2"]
        row["unexpected_annotations"] = counts["unexpected_annotations"]

        missing = sorted(set(SENSORIMOTOR_CHANNELS) - set(raw.ch_names))
        row["missing_sensorimotor_channels"] = "|".join(missing)

        reasons: list[str] = []
        if row["sfreq"] <= 0:
            reasons.append("invalid_sfreq")
        elif abs(float(row["sfreq"]) - 160.0) > 0.5:
            # Unexpected rate is flagged but not automatically fatal if > 0.
            reasons.append(f"unexpected_sfreq_{row['sfreq']}")
        if row["n_channels"] < 21:
            reasons.append("too_few_channels")
        if missing:
            reasons.append("missing_sensorimotor_channels")
        if row["T1_count"] + row["T2_count"] < 1:
            reasons.append("no_task_annotations")
        if row["duration_sec"] < 5.5:
            reasons.append("duration_too_short")

        # Watchlist notes are informational; not automatic exclusions.
        if subject in ANOMALY_WATCHLIST:
            if float(row["sfreq"]) != 160.0:
                reasons.append("watchlist_sfreq_anomaly")
            if int(row["n_channels"]) != 64:
                reasons.append("watchlist_channel_count_anomaly")

        fatal = {
            "invalid_sfreq",
            "too_few_channels",
            "missing_sensorimotor_channels",
            "no_task_annotations",
            "duration_too_short",
        }
        fatal_hit = [r for r in reasons if r in fatal]
        row["structurally_valid"] = len(fatal_hit) == 0
        row["invalidity_reason"] = "|".join(reasons) if reasons else ""
        raw.close()
        return row
    except Exception as exc:  # noqa: BLE001 - audit must capture all failures
        row["invalidity_reason"] = f"exception:{type(exc).__name__}:{exc}"
        row["structurally_valid"] = False
        return row


def audit_subjects(
    subjects: Iterable[int],
    runs: Iterable[int],
    data_root: Path,
    *,
    download: bool = True,
) -> pd.DataFrame:
    rows = [
        audit_run(int(subject), int(run), data_root, download=download)
        for subject in subjects
        for run in runs
    ]
    return pd.DataFrame(rows)


def summarize_anomalies(audit: pd.DataFrame) -> pd.DataFrame:
    """Return watchlist and invalid rows for reporting."""
    mask = (~audit["structurally_valid"]) | audit["in_anomaly_watchlist"]
    return audit.loc[mask].copy()
