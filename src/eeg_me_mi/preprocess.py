"""Participant-level preprocessing and epoch caching."""

from __future__ import annotations

import gc
import hashlib
import json
from pathlib import Path
from typing import Any

import mne
import numpy as np
import pandas as pd
from mne.datasets import eegbci
from mne.io import read_raw_edf

from eeg_me_mi.protocol import SENSORIMOTOR_CHANNELS, movement_name, pair_id, run_definition


def _cache_key(preproc: dict[str, Any]) -> str:
    payload = {
        "l_freq": preproc["l_freq"],
        "h_freq": preproc["h_freq"],
        "target_sfreq": preproc["target_sfreq"],
        "epoch_tmin": preproc["epoch_tmin"],
        "epoch_tmax": preproc["epoch_tmax"],
        "reject_peak_to_peak_uv": preproc["reject_peak_to_peak_uv"],
        "channels": list(SENSORIMOTOR_CHANNELS),
        "version": 1,
    }
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
    return digest[:12]


def subject_cache_paths(cache_root: Path, subject: int, preproc: dict[str, Any]) -> tuple[Path, Path]:
    key = _cache_key(preproc)
    folder = cache_root / f"preproc_{key}" / f"S{subject:03d}"
    return folder / "epochs-epo.fif", folder / "qc.json"


def load_and_preprocess_raw(path: Path, preproc: dict[str, Any]) -> mne.io.BaseRaw:
    """Load one EDF and apply the frozen Milestone-1 preprocessing chain.

    Order: standardize names → montage → average reference → resample →
    band-pass → pick 21 sensorimotor channels.
    """
    raw = read_raw_edf(path, preload=True, verbose=False)
    eegbci.standardize(raw)
    raw.pick(picks="eeg")
    raw.set_montage("standard_1005", on_missing="raise", verbose=False)
    raw.set_eeg_reference("average", projection=False, verbose=False)
    raw.resample(float(preproc["target_sfreq"]), npad="auto", verbose=False)
    raw.filter(
        float(preproc["l_freq"]),
        float(preproc["h_freq"]),
        picks="eeg",
        method="fir",
        phase="zero",
        fir_design="firwin",
        skip_by_annotation="edge",
        verbose=False,
    )
    missing = sorted(set(SENSORIMOTOR_CHANNELS) - set(raw.ch_names))
    if missing:
        raise RuntimeError(f"Missing required channels: {missing}")
    raw.pick(list(SENSORIMOTOR_CHANNELS))
    return raw


def epoch_run(
    subject: int,
    run: int,
    data_root: Path,
    preproc: dict[str, Any],
    *,
    download: bool = True,
) -> tuple[mne.Epochs | None, dict[str, Any]]:
    """Create annotation-locked epochs for one run with frozen artifact rejection."""
    from eeg_me_mi.audit import ensure_edf

    info = run_definition(run)
    log: dict[str, Any] = {
        "subject": subject,
        "run": run,
        "condition": info.condition,
        "task_family": info.task_family,
        "repetition": info.repetition,
        "n_events": 0,
        "n_kept": 0,
        "n_rejected": 0,
        "rejection_rate": np.nan,
        "status": "error",
        "error": "",
        "peak_to_peak_max_uv": np.nan,
    }

    try:
        path = ensure_edf(data_root, subject, run, download=download)
        if path is None:
            log["status"] = "missing_file"
            log["error"] = "EDF not found"
            return None, log

        raw = load_and_preprocess_raw(path, preproc)
        events, _ = mne.events_from_annotations(
            raw,
            event_id={"T1": 1, "T2": 2},
            verbose=False,
        )
        if len(events) == 0:
            log["status"] = "no_events"
            log["error"] = "No T1/T2 annotations"
            return None, log

        event_names = np.where(events[:, 2] == 1, "T1", "T2")
        metadata = pd.DataFrame(
            {
                "subject": subject,
                "run": run,
                "condition": info.condition,
                "label": int(info.condition == "execution"),
                "task_family": info.task_family,
                "repetition": info.repetition,
                "pair_id": pair_id(run),
                "event_name": event_names,
                "movement": [movement_name(run, e) for e in event_names],
                "onset_seconds": events[:, 0] / raw.info["sfreq"],
                "source_file": path.name,
            }
        )

        reject_uv = float(preproc["reject_peak_to_peak_uv"])
        epochs = mne.Epochs(
            raw,
            events,
            event_id={"T1": 1, "T2": 2},
            tmin=float(preproc["epoch_tmin"]),
            tmax=float(preproc["epoch_tmax"]),
            baseline=None,
            preload=True,
            reject={"eeg": reject_uv * 1e-6},
            reject_by_annotation=True,
            metadata=metadata,
            event_repeated="drop",
            verbose=False,
        )
        # Peak-to-peak of candidate epochs before drop is not retained by MNE;
        # compute on kept epochs for QC distributions.
        if len(epochs):
            data = epochs.get_data(copy=False)
            ptp = np.ptp(data, axis=-1).max(axis=-1) * 1e6
            log["peak_to_peak_max_uv"] = float(np.nanmax(ptp))

        log["n_events"] = int(len(events))
        log["n_kept"] = int(len(epochs))
        log["n_rejected"] = int(len(events) - len(epochs))
        log["rejection_rate"] = float(1.0 - (len(epochs) / len(events)))
        log["status"] = "ok" if len(epochs) else "all_rejected"
        del raw
        gc.collect()
        return epochs if len(epochs) else None, log
    except Exception as exc:  # noqa: BLE001
        log["status"] = "error"
        log["error"] = f"{type(exc).__name__}:{exc}"
        return None, log


def process_subject(
    subject: int,
    runs: tuple[int, ...],
    data_root: Path,
    cache_root: Path,
    preproc: dict[str, Any],
    *,
    download: bool = True,
    force: bool = False,
) -> tuple[mne.Epochs | None, list[dict[str, Any]]]:
    """Process and cache one participant's task-run epochs."""
    epo_path, qc_path = subject_cache_paths(cache_root, subject, preproc)
    if epo_path.exists() and qc_path.exists() and not force:
        epochs = mne.read_epochs(epo_path, preload=True, verbose=False)
        qc = json.loads(qc_path.read_text(encoding="utf-8"))
        return epochs if len(epochs) else None, qc

    run_epochs: list[mne.Epochs] = []
    logs: list[dict[str, Any]] = []
    for run in runs:
        epochs, log = epoch_run(subject, run, data_root, preproc, download=download)
        logs.append(log)
        if epochs is not None and len(epochs):
            run_epochs.append(epochs)

    epo_path.parent.mkdir(parents=True, exist_ok=True)
    if run_epochs:
        combined = mne.concatenate_epochs(
            run_epochs,
            add_offset=True,
            on_mismatch="raise",
            verbose=False,
        )
        combined.metadata = combined.metadata.reset_index(drop=True)
        combined.save(epo_path, overwrite=True, verbose=False)
        qc_path.write_text(json.dumps(logs, indent=2), encoding="utf-8")
        del run_epochs
        gc.collect()
        return combined, logs

    # Persist empty QC even when no epochs survive.
    qc_path.write_text(json.dumps(logs, indent=2), encoding="utf-8")
    del run_epochs
    gc.collect()
    return None, logs


def build_epoch_dataset(
    subjects: tuple[int, ...],
    runs: tuple[int, ...],
    data_root: Path,
    cache_root: Path,
    preproc: dict[str, Any],
    *,
    download: bool = True,
    force: bool = False,
) -> tuple[mne.Epochs | None, pd.DataFrame]:
    """Process subjects one-by-one; never keep all raw EDFs in memory."""
    retained: list[mne.Epochs] = []
    all_logs: list[dict[str, Any]] = []

    for subject in subjects:
        epochs, logs = process_subject(
            subject,
            runs,
            data_root,
            cache_root,
            preproc,
            download=download,
            force=force,
        )
        all_logs.extend(logs)
        if epochs is not None and len(epochs):
            retained.append(epochs)
        del epochs
        gc.collect()

    rejection_log = pd.DataFrame(all_logs)
    if not retained:
        return None, rejection_log

    combined = mne.concatenate_epochs(
        retained,
        add_offset=True,
        on_mismatch="raise",
        verbose=False,
    )
    combined.metadata = combined.metadata.reset_index(drop=True)
    del retained
    gc.collect()
    return combined, rejection_log
