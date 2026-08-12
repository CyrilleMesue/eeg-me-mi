"""Participant-level preprocessing and epoch caching.

Supports shared *minimal* caches (no amplitude rejection) with per-epoch
peak-to-peak values so E05 thresholds reuse the same filtered epochs.
"""

from __future__ import annotations

import gc
import hashlib
import json
from pathlib import Path
from typing import Any, Sequence

import mne
import numpy as np
import pandas as pd
from mne.datasets import eegbci
from mne.io import read_raw_edf

from eeg_me_mi.protocol import SENSORIMOTOR_CHANNELS, movement_name, pair_id, run_definition


def _cache_key(preproc: dict[str, Any], channels: Sequence[str], *, mode: str) -> str:
    payload = {
        "mode": mode,
        "l_freq": preproc["l_freq"],
        "h_freq": preproc["h_freq"],
        "target_sfreq": preproc["target_sfreq"],
        "epoch_tmin": preproc["epoch_tmin"],
        "epoch_tmax": preproc["epoch_tmax"],
        "baseline_tmin": preproc.get("baseline_tmin"),
        "baseline_tmax": preproc.get("baseline_tmax"),
        "task_tmin": preproc.get("task_tmin"),
        "task_tmax": preproc.get("task_tmax"),
        "e00_tmin": preproc.get("e00_tmin"),
        "e00_tmax": preproc.get("e00_tmax"),
        "reject_peak_to_peak_uv": preproc.get("reject_peak_to_peak_uv"),
        "reference": "average",
        "montage": "standard_1005",
        "filter_method": "fir",
        "fir_design": "firwin",
        "phase": "zero",
        "channels": list(channels),
        "mne_version": mne.__version__,
        "version": 3,
    }
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
    return digest[:12]


def subject_cache_paths(
    cache_root: Path,
    subject: int,
    preproc: dict[str, Any],
    *,
    channels: Sequence[str] = SENSORIMOTOR_CHANNELS,
    mode: str = "rejected",
) -> tuple[Path, Path, Path]:
    key = _cache_key(preproc, channels, mode=mode)
    folder = cache_root / f"preproc_{mode}_{key}" / f"S{subject:03d}"
    return folder / "epochs-epo.fif", folder / "qc.json", folder / "cache_manifest.json"


def load_and_preprocess_raw(
    path: Path,
    preproc: dict[str, Any],
    *,
    channels: Sequence[str] = SENSORIMOTOR_CHANNELS,
) -> mne.io.BaseRaw:
    raw = read_raw_edf(path, preload=True, verbose=False)
    eegbci.standardize(raw)
    raw.pick(picks="eeg")
    raw.set_montage("standard_1005", on_missing="ignore", verbose=False)
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
    missing = sorted(set(channels) - set(raw.ch_names))
    if missing:
        raise RuntimeError(f"Missing required channels: {missing}")
    raw.pick(list(channels))
    return raw


def epoch_run(
    subject: int,
    run: int,
    data_root: Path,
    preproc: dict[str, Any],
    *,
    download: bool = True,
    channels: Sequence[str] = SENSORIMOTOR_CHANNELS,
    apply_reject: bool = True,
) -> tuple[mne.Epochs | None, dict[str, Any]]:
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

        raw = load_and_preprocess_raw(path, preproc, channels=channels)
        events, _ = mne.events_from_annotations(
            raw, event_id={"T1": 1, "T2": 2}, verbose=False
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

        reject = None
        if apply_reject:
            reject_uv = float(preproc["reject_peak_to_peak_uv"])
            reject = {"eeg": reject_uv * 1e-6}

        # First form unrejected epochs to record PTP, then drop if needed.
        epochs_all = mne.Epochs(
            raw,
            events,
            event_id={"T1": 1, "T2": 2},
            tmin=float(preproc["epoch_tmin"]),
            tmax=float(preproc["epoch_tmax"]),
            baseline=None,
            preload=True,
            reject=None,
            reject_by_annotation=True,
            metadata=metadata,
            event_repeated="drop",
            verbose=False,
        )
        if len(epochs_all) == 0:
            log["n_events"] = int(len(events))
            log["status"] = "all_rejected"
            return None, log

        data = epochs_all.get_data(copy=False)
        ptp_uv = np.ptp(data, axis=-1).max(axis=1) * 1e6
        epochs_all.metadata = epochs_all.metadata.copy()
        epochs_all.metadata["ptp_uv"] = ptp_uv

        if apply_reject and reject is not None:
            thr = float(preproc["reject_peak_to_peak_uv"])
            keep = ptp_uv <= thr
            epochs = epochs_all[keep]
        else:
            epochs = epochs_all

        log["n_events"] = int(len(events))
        log["n_kept"] = int(len(epochs))
        log["n_rejected"] = int(len(epochs_all) - len(epochs)) if apply_reject else 0
        log["rejection_rate"] = float(1.0 - (len(epochs) / max(len(epochs_all), 1)))
        log["peak_to_peak_max_uv"] = float(np.nanmax(ptp_uv)) if len(ptp_uv) else np.nan
        log["status"] = "ok" if len(epochs) else "all_rejected"
        del raw
        gc.collect()
        return epochs if len(epochs) else None, log
    except Exception as exc:  # noqa: BLE001
        log["status"] = "error"
        log["error"] = f"{type(exc).__name__}:{exc}"
        return None, log


def apply_ptp_threshold(epochs: mne.Epochs, threshold_uv: float | None) -> mne.Epochs:
    """Filter minimal epochs by peak-to-peak threshold (None / <=0 = keep all)."""
    meta = epochs.metadata
    if "ptp_uv" not in meta.columns:
        data = epochs.get_data(copy=False)
        ptp = np.ptp(data, axis=-1).max(axis=1) * 1e6
        meta = meta.copy()
        meta["ptp_uv"] = ptp
        epochs.metadata = meta
    if threshold_uv is None or float(threshold_uv) <= 0:
        return epochs.copy()
    keep = meta["ptp_uv"].to_numpy(dtype=float) <= float(threshold_uv)
    return epochs[keep]


def process_subject(
    subject: int,
    runs: tuple[int, ...],
    data_root: Path,
    cache_root: Path,
    preproc: dict[str, Any],
    *,
    download: bool = True,
    force: bool = False,
    channels: Sequence[str] = SENSORIMOTOR_CHANNELS,
    mode: str = "rejected",
    project_root: Path | None = None,
) -> tuple[mne.Epochs | None, list[dict[str, Any]]]:
    from eeg_me_mi.audit import ensure_edf
    from eeg_me_mi.provenance import (
        build_cache_manifest,
        file_fingerprint,
        validate_cache_manifest,
    )

    apply_reject = mode != "minimal"
    preproc_for_cache = dict(preproc)
    if mode == "minimal":
        preproc_for_cache = {**preproc, "reject_peak_to_peak_uv": None}

    epo_path, qc_path, manifest_path = subject_cache_paths(
        cache_root, subject, preproc_for_cache, channels=channels, mode=mode
    )

    # Build expected identity (EDF fingerprints) before accepting a cache hit.
    edf_fps = []
    ann_parts = []
    for run in runs:
        path = ensure_edf(data_root, subject, run, download=download)
        if path is None:
            edf_fps.append({"run": run, "exists": False})
            continue
        edf_fps.append({"run": int(run), **file_fingerprint(path)})
        try:
            raw_ann = read_raw_edf(path, preload=False, verbose=False)
            anns = [
                (float(a["onset"]), float(a["duration"]), str(a["description"]))
                for a in raw_ann.annotations
            ]
            ann_parts.append(f"{run}:{anns}")
            del raw_ann
        except Exception:  # noqa: BLE001
            ann_parts.append(f"{run}:unreadable")
    ann_fp = hashlib.sha256("|".join(ann_parts).encode("utf-8")).hexdigest()
    expected_manifest = build_cache_manifest(
        subject=subject,
        runs=runs,
        preproc=preproc_for_cache,
        channels=channels,
        mode=mode,
        edf_fingerprints=edf_fps,
        annotation_fingerprint=ann_fp,
        project_root=project_root,
    )

    if epo_path.exists() and qc_path.exists() and manifest_path.exists() and not force:
        stored = json.loads(manifest_path.read_text(encoding="utf-8"))
        # Compare scientifically meaningful fields; allow git_commit drift on reuse
        # of identical preprocessing, but not preprocessing / EDF identity drift.
        try:
            validate_cache_manifest(
                stored,
                expected_manifest,
                require_keys=("version", "mode", "channels", "preprocessing", "mne_version"),
            )
            if stored.get("annotation_fingerprint") != expected_manifest["annotation_fingerprint"]:
                raise RuntimeError("annotation fingerprint mismatch")
            if stored.get("edf_fingerprints") != expected_manifest["edf_fingerprints"]:
                raise RuntimeError("EDF fingerprint mismatch")
            epochs = mne.read_epochs(epo_path, preload=True, verbose=False)
            qc = json.loads(qc_path.read_text(encoding="utf-8"))
            return epochs if len(epochs) else None, qc
        except RuntimeError:
            # Incompatible cache — fall through to rebuild.
            pass

    run_epochs: list[mne.Epochs] = []
    logs: list[dict[str, Any]] = []
    for run in runs:
        epochs, log = epoch_run(
            subject,
            run,
            data_root,
            preproc,
            download=download,
            channels=channels,
            apply_reject=apply_reject,
        )
        logs.append(log)
        if epochs is not None and len(epochs):
            run_epochs.append(epochs)

    epo_path.parent.mkdir(parents=True, exist_ok=True)
    if run_epochs:
        combined = mne.concatenate_epochs(
            run_epochs, add_offset=True, on_mismatch="raise", verbose=False
        )
        combined.metadata = combined.metadata.reset_index(drop=True)
        combined.save(epo_path, overwrite=True, verbose=False)
        qc_path.write_text(json.dumps(logs, indent=2), encoding="utf-8")
        manifest_path.write_text(
            json.dumps(expected_manifest, indent=2, default=str), encoding="utf-8"
        )
        del run_epochs
        gc.collect()
        return combined, logs

    qc_path.write_text(json.dumps(logs, indent=2), encoding="utf-8")
    manifest_path.write_text(
        json.dumps(expected_manifest, indent=2, default=str), encoding="utf-8"
    )
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
    channels: Sequence[str] = SENSORIMOTOR_CHANNELS,
    mode: str = "rejected",
    threshold_uv: float | None = None,
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
            channels=channels,
            mode=mode,
        )
        all_logs.extend(logs)
        if epochs is not None and len(epochs):
            if mode == "minimal":
                thr = threshold_uv if threshold_uv is not None else preproc.get("reject_peak_to_peak_uv")
                epochs = apply_ptp_threshold(epochs, thr)
            if len(epochs):
                retained.append(epochs)
        del epochs
        gc.collect()

    rejection_log = pd.DataFrame(all_logs)
    if not retained:
        return None, rejection_log

    combined = mne.concatenate_epochs(
        retained, add_offset=True, on_mismatch="raise", verbose=False
    )
    combined.metadata = combined.metadata.reset_index(drop=True)
    del retained
    gc.collect()
    return combined, rejection_log
