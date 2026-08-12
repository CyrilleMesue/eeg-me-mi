"""Targeted S109 QC — amplitude / unit diagnostics only.

Does NOT change eligibility, remove bad channels, or invent new rules.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import mne
import numpy as np
import pandas as pd
from mne.datasets import eegbci
from mne.io import read_raw_edf

from eeg_me_mi.audit import ensure_edf
from eeg_me_mi.config import AnalysisConfig, load_config
from eeg_me_mi.preprocess import load_and_preprocess_raw
from eeg_me_mi.protocol import SENSORIMOTOR_CHANNELS, movement_name, pair_id, run_definition
from eeg_me_mi.provenance import write_json


def _ptp_uv(data: np.ndarray) -> np.ndarray:
    """Peak-to-peak in µV for array shaped (n_epochs, n_ch, n_times) or (n_ch, n_times)."""
    if data.ndim == 2:
        return np.ptp(data, axis=-1) * 1e6
    return np.ptp(data, axis=-1) * 1e6


def _channel_summary(ptp_by_ch: np.ndarray, ch_names: list[str]) -> pd.DataFrame:
    """ptp_by_ch: (n_epochs, n_channels) in µV."""
    rows = []
    for i, ch in enumerate(ch_names):
        vals = ptp_by_ch[:, i]
        rows.append(
            {
                "channel": ch,
                "median_ptp_uv": float(np.median(vals)),
                "iqr_ptp_uv": float(np.subtract(*np.percentile(vals, [75, 25]))),
                "p90_ptp_uv": float(np.percentile(vals, 90)),
                "p95_ptp_uv": float(np.percentile(vals, 95)),
                "p99_ptp_uv": float(np.percentile(vals, 99)),
                "max_ptp_uv": float(np.max(vals)),
                "n_epochs": int(len(vals)),
            }
        )
    return pd.DataFrame(rows)


def _edf_unit_metadata(path: Path) -> dict[str, Any]:
    raw = read_raw_edf(path, preload=False, verbose=False)
    info = {
        "path": str(path),
        "n_channels": int(len(raw.ch_names)),
        "sfreq": float(raw.info["sfreq"]),
        "mne_unit_note": "MNE scales EDF to SI volts on load",
        "threshold_unit": "µV (reject compares ptp * 1e6 to reject_peak_to_peak_uv)",
    }
    # Physical dimension / digital scaling if present in info
    try:
        units = [raw._orig_units.get(ch, "") for ch in raw.ch_names[:5]]
        info["orig_units_sample"] = units
    except Exception:  # noqa: BLE001
        info["orig_units_sample"] = []
    try:
        # EDF header fields via mne
        info["highpass"] = raw.info.get("highpass")
        info["lowpass"] = raw.info.get("lowpass")
    except Exception:  # noqa: BLE001
        pass
    del raw
    return info


def qc_subject_epochs(
    subject: int,
    runs: tuple[int, ...],
    data_root: Path,
    preproc: dict[str, Any],
    *,
    threshold_uv: float = 200.0,
    channels: list[str] | None = None,
    download: bool = False,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """Per-epoch and per-channel PTP QC for one subject across pipeline stages."""
    channels = list(channels or SENSORIMOTOR_CHANNELS)
    epoch_rows: list[dict[str, Any]] = []
    stage_channel_frames: list[pd.DataFrame] = []
    unit_meta: dict[str, Any] = {"subject": subject, "runs": {}}

    for run in runs:
        path = ensure_edf(data_root, subject, run, download=download)
        if path is None:
            continue
        unit_meta["runs"][str(run)] = _edf_unit_metadata(path)
        info = run_definition(run)

        # --- Stage: raw EDF (volts as loaded by MNE) ---
        raw0 = read_raw_edf(path, preload=True, verbose=False)
        eegbci.standardize(raw0)
        raw0.pick(picks="eeg")
        sfreq0 = float(raw0.info["sfreq"])
        events0, _ = mne.events_from_annotations(
            raw0, event_id={"T1": 1, "T2": 2}, verbose=False
        )
        if len(events0) == 0:
            del raw0
            continue

        def _epoch_ptp(raw_obj, stage: str, sfreq: float) -> np.ndarray | None:
            ev, _ = mne.events_from_annotations(
                raw_obj, event_id={"T1": 1, "T2": 2}, verbose=False
            )
            if len(ev) == 0:
                return None
            missing = sorted(set(channels) - set(raw_obj.ch_names))
            if missing:
                return None
            raw_ch = raw_obj.copy().pick(channels)
            ep = mne.Epochs(
                raw_ch,
                ev,
                event_id={"T1": 1, "T2": 2},
                tmin=float(preproc["epoch_tmin"]),
                tmax=float(preproc["epoch_tmax"]),
                baseline=None,
                preload=True,
                reject=None,
                reject_by_annotation=False,
                event_repeated="drop",
                verbose=False,
            )
            if len(ep) == 0:
                return None
            data = ep.get_data(copy=False)
            ptp = _ptp_uv(data)  # (n_ep, n_ch)
            ch_sum = _channel_summary(ptp, channels)
            ch_sum.insert(0, "stage", stage)
            ch_sum.insert(1, "subject", subject)
            ch_sum.insert(2, "run", run)
            stage_channel_frames.append(ch_sum)

            event_names = np.where(ev[: len(ep), 2] == 1, "T1", "T2")
            # Align event names to retained epochs via metadata construction
            for i in range(len(ep)):
                ptp_ep = ptp[i]
                max_ch_i = int(np.argmax(ptp_ep))
                n_over = int(np.sum(ptp_ep > threshold_uv))
                epoch_rows.append(
                    {
                        "subject": subject,
                        "run": run,
                        "epoch_index": i,
                        "stage": stage,
                        "pair_id": pair_id(run),
                        "movement": movement_name(run, str(event_names[i])),
                        "mode": info.condition,
                        "event_name": str(event_names[i]),
                        "max_ptp_uv": float(np.max(ptp_ep)),
                        "channel_max_ptp": channels[max_ch_i],
                        "n_channels_over_threshold": n_over,
                        "prop_channels_over_threshold": float(n_over / len(channels)),
                        "threshold_uv": float(threshold_uv),
                        "sfreq": float(sfreq),
                    }
                )
            return ptp

        _epoch_ptp(raw0, "raw_edf_mne_volts", sfreq0)

        # After average reference (still original sfreq)
        raw_ref = raw0.copy()
        raw_ref.set_montage("standard_1005", on_missing="ignore", verbose=False)
        raw_ref.set_eeg_reference("average", projection=False, verbose=False)
        _epoch_ptp(raw_ref, "after_average_reference", sfreq0)

        # Full frozen pipeline (resample + filter)
        del raw0, raw_ref
        raw = load_and_preprocess_raw(path, preproc, channels=channels)
        _epoch_ptp(raw, "after_filter_resample", float(raw.info["sfreq"]))
        del raw

    epoch_df = pd.DataFrame(epoch_rows)
    channel_df = pd.concat(stage_channel_frames, ignore_index=True) if stage_channel_frames else pd.DataFrame()
    return epoch_df, channel_df, unit_meta


def run_s109_qc(
    config: AnalysisConfig,
    *,
    project_root: Path | None = None,
    neighbors: tuple[int, ...] = (107, 108, 106, 105),
    download: bool = False,
) -> dict[str, Any]:
    """QC S109 and compare descriptively to neighboring structurally normal subjects."""
    project_root = project_root or config.source.parent.parent
    data_root = config.path("data_root", project_root=project_root)
    out = project_root / "results" / "s109_qc"
    out.mkdir(parents=True, exist_ok=True)

    preproc = config.preprocessing
    thr = float(preproc["reject_peak_to_peak_uv"])
    subjects = (109,) + tuple(neighbors)

    all_epochs = []
    all_channels = []
    unit_all: dict[str, Any] = {}
    for subj in subjects:
        ep, ch, unit = qc_subject_epochs(
            subj,
            config.runs,
            data_root,
            preproc,
            threshold_uv=thr,
            download=download,
        )
        all_epochs.append(ep)
        all_channels.append(ch)
        unit_all[str(subj)] = unit

    epoch_df = pd.concat(all_epochs, ignore_index=True) if all_epochs else pd.DataFrame()
    channel_df = pd.concat(all_channels, ignore_index=True) if all_channels else pd.DataFrame()
    epoch_df.to_csv(out / "epoch_ptp_by_stage.csv", index=False)
    channel_df.to_csv(out / "channel_ptp_summaries.csv", index=False)
    write_json(out / "unit_metadata.json", unit_all)

    # Focused S109 after-filter summary
    s109 = epoch_df.loc[
        (epoch_df["subject"] == 109) & (epoch_df["stage"] == "after_filter_resample")
    ]
    summary = {
        "subject": 109,
        "threshold_uv": thr,
        "n_epochs_after_filter": int(len(s109)),
        "n_epochs_pass_threshold": int((s109["max_ptp_uv"] <= thr).sum()) if len(s109) else 0,
        "max_ptp_uv_min": float(s109["max_ptp_uv"].min()) if len(s109) else None,
        "max_ptp_uv_median": float(s109["max_ptp_uv"].median()) if len(s109) else None,
        "max_ptp_uv_max": float(s109["max_ptp_uv"].max()) if len(s109) else None,
        "eligibility_unchanged": True,
        "bad_channel_rule_introduced": False,
    }
    # Neighbor comparison at same stage
    neigh = epoch_df.loc[
        (epoch_df["subject"] != 109) & (epoch_df["stage"] == "after_filter_resample")
    ]
    if len(neigh):
        summary["neighbor_max_ptp_median"] = float(neigh.groupby("subject")["max_ptp_uv"].median().median())
        summary["neighbor_max_ptp_p95"] = float(np.percentile(neigh["max_ptp_uv"], 95))
    write_json(out / "s109_summary.json", summary)

    # Markdown report
    report = out / ".." / ".." / "docs" / "s109_qc_report.md"
    # written by caller path preference — also dump here
    md_path = project_root / "docs" / "s109_qc_report.md"
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md = [
        "# S109 QC report (remediation — eligibility unchanged)",
        "",
        "## Scope",
        "",
        "Targeted amplitude/unit diagnostics for S109. **No eligibility change.**",
        "**No bad-channel rule introduced.** No model performance consulted.",
        "",
        "## Frozen pipeline notes",
        "",
        "- MNE loads EDF in SI volts; PTP thresholding uses µV (`ptp * 1e6`).",
        f"- Primary reject threshold: **{thr:g} µV**.",
        "- Stages reported: raw EDF (MNE volts), after average reference, after resample+FIR.",
        "",
        "## S109 summary (after filter/resample)",
        "",
        f"- Epochs formed: {summary['n_epochs_after_filter']}",
        f"- Epochs ≤ {thr:g} µV: {summary['n_epochs_pass_threshold']}",
        f"- Max-PTP range (µV): {summary['max_ptp_uv_min']} … {summary['max_ptp_uv_max']}",
        f"- Median max-PTP (µV): {summary['max_ptp_uv_median']}",
        "",
        "## Neighbor comparison",
        "",
        f"- Neighbors: {list(neighbors)}",
        f"- Neighbor median-of-medians max-PTP: {summary.get('neighbor_max_ptp_median')}",
        f"- Neighbor p95 max-PTP: {summary.get('neighbor_max_ptp_p95')}",
        "",
        "## Machine-readable tables",
        "",
        f"- `{out / 'epoch_ptp_by_stage.csv'}`",
        f"- `{out / 'channel_ptp_summaries.csv'}`",
        f"- `{out / 'unit_metadata.json'}`",
        f"- `{out / 's109_summary.json'}`",
        "",
        "## Conclusion placeholders",
        "",
        "Filled after QC execution in remediation report.",
        "",
    ]
    md_path.write_text("\n".join(md), encoding="utf-8")
    return {"output_dir": out, "summary": summary, "report": md_path}


def run_s109_qc_from_config(path: str | Path, **kwargs) -> dict[str, Any]:
    return run_s109_qc(load_config(path), **kwargs)
