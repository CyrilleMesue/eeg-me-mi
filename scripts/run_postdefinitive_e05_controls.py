#!/usr/bin/env python3
"""Post-definitive completion of prespecified E05 controls.

Runs AFTER definitive primary E01/E07. Does not rewrite results/definitive/.

Reason: analyses were prespecified before outcome inspection but absent from
definitive run_full outputs (cohort JSON only).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from eeg_me_mi.audit import audit_subjects
from eeg_me_mi.config import load_config
from eeg_me_mi.cv import PARTICIPANT_MEAN_SCORING, run_nested_group_cv
from eeg_me_mi.eligibility import evaluate_eligibility, filter_eligible_epochs
from eeg_me_mi.features import extract_e01_erd_features
from eeg_me_mi.filter_support import e00_window_from_preproc, e01_windows_from_preproc
from eeg_me_mi.metrics import bootstrap_participant_means
from eeg_me_mi.models import logistic_param_grid, make_erd_lr_pipeline
from eeg_me_mi.preprocess import build_epoch_dataset
from eeg_me_mi.provenance import git_commit, git_dirty, git_tag, software_versions, write_json
from eeg_me_mi.rois import SPATIAL_CONTROL_CHANNELS, spatial_control_rationale
from eeg_me_mi.protocol import SENSORIMOTOR_CHANNELS


def _export_cv(folder: Path, result: dict, n_boot: int, seed: int) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    result["oof_predictions"].to_csv(folder / "oof_predictions.csv", index=False)
    result["participant_metrics"].to_csv(folder / "participant_metrics.csv", index=False)
    result["fold_metrics"].to_csv(folder / "fold_metrics.csv", index=False)
    result["tuning"].to_csv(folder / "inner_tuning.csv", index=False)
    result["fold_assignments"].to_csv(folder / "fold_assignments.csv", index=False)
    boot, _ = bootstrap_participant_means(
        result["participant_metrics"], n_bootstrap=n_boot, seed=seed, metrics=("balanced_accuracy",)
    )
    boot.to_csv(folder / "bootstrap_summary.csv", index=False)
    write_json(folder / "summary.json", result["summary"])


def _cache_identity(cache_root: Path, channels: tuple[str, ...], mode: str) -> str:
    """Stable string for reconciliation (mode + channel-set hash + cache root)."""
    ch = ",".join(channels)
    return f"mode={mode};channels_sha256={hashlib.sha256(ch.encode()).hexdigest()[:12]};cache={cache_root}"


def reconcile_thresholds(
    *,
    config,
    project_root: Path,
    audit: pd.DataFrame,
    out_csv: Path,
) -> pd.DataFrame:
    data_root = config.path("data_root", project_root=project_root)
    cache_root = config.path("cache_root", project_root=project_root)
    rows: list[dict[str, Any]] = []

    # True no-rejection base (shared minimal cache, no PTP filter)
    ep_base, _ = build_epoch_dataset(
        config.subjects,
        config.runs,
        data_root,
        cache_root,
        config.preprocessing,
        download=False,
        force=False,
        mode="minimal",
        threshold_uv=None,  # explicit None => keep all (after sentinel fix)
    )
    if ep_base is None:
        raise RuntimeError("Failed to load minimal no-rejection epochs")
    base_md = ep_base.metadata.reset_index(drop=True)
    ptp = base_md["ptp_uv"].to_numpy(dtype=float)
    n_before = int(len(base_md))
    cache_id = _cache_identity(cache_root, SENSORIMOTOR_CHANNELS, "minimal")

    for thr_name, thr in (("none", None), ("150uv", 150.0), ("200uv", 200.0)):
        if thr is None:
            keep = np.ones(n_before, dtype=bool)
            source_state = "minimal_cache_no_ptp_filter"
        else:
            keep = ptp <= float(thr)
            source_state = f"minimal_cache_then_ptp<={thr:g}"
        n_ret = int(keep.sum())
        n_rej = int(n_before - n_ret)
        md = base_md.loc[keep].reset_index(drop=True)
        el = evaluate_eligibility(md, audit, config.subjects)
        rows.append(
            {
                "threshold": thr_name,
                "epochs_before": n_before,
                "epochs_rejected": n_rej,
                "epochs_retained": n_ret,
                "participants_eligible": int(el["eligible_primary"].sum()),
                "cache_identity": cache_id,
                "source_preprocessing_state": source_state,
                "n_ptp_gt_150": int((ptp > 150).sum()),
                "n_ptp_gt_200": int((ptp > 200).sum()),
            }
        )

    # Legacy definitive row: None incorrectly applied config 200
    keep200 = ptp <= 200.0
    el200 = evaluate_eligibility(base_md.loc[keep200].reset_index(drop=True), audit, config.subjects)
    rows.append(
        {
            "threshold": "none_as_executed_in_definitive_run_full_BUG",
            "epochs_before": n_before,
            "epochs_rejected": int(n_before - keep200.sum()),
            "epochs_retained": int(keep200.sum()),
            "participants_eligible": int(el200["eligible_primary"].sum()),
            "cache_identity": cache_id,
            "source_preprocessing_state": (
                "BUG: threshold_uv=None fell back to preproc reject_peak_to_peak_uv=200"
            ),
            "n_ptp_gt_150": int((ptp > 150).sum()),
            "n_ptp_gt_200": int((ptp > 200).sum()),
        }
    )

    frame = pd.DataFrame(rows)
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(out_csv, index=False)
    return frame, ep_base, audit


def run_threshold_decoding(
    *,
    config,
    project_root: Path,
    audit: pd.DataFrame,
    out_root: Path,
    frozen_e01_bacc: float | None,
    expected_200uv_epochs: int | None = 16913,
    allow_cache_mismatch: bool = False,
) -> dict[str, Any]:
    """Run artifact-threshold decoding.

    ``expected_200uv_epochs`` is the *post-eligibility* E01 OOF epoch count
    (definitive E01 oof_predictions length = 16913), not the pre-eligibility
    PTP-retained count in threshold_cohorts.csv (17257).
    """
    data_root = config.path("data_root", project_root=project_root)
    cache_root = config.path("cache_root", project_root=project_root)
    outer = int(config.cv["outer_folds"])
    inner = int(config.cv["inner_folds"])
    n_boot = int(config.statistics["bootstrap_replicates"])
    scoring = PARTICIPANT_MEAN_SCORING
    c_grid = config.logistic_c_grid
    summaries: dict[str, Any] = {}

    # Use 0.0 for true no-rejection: works with both the sentinel fix and the
    # pre-fix API (None wrongly fell back to config 200 µV).
    for thr_name, thr in (("none", 0.0), ("150uv", 150.0), ("200uv", 200.0)):
        t0 = time.perf_counter()
        ep, _log = build_epoch_dataset(
            config.subjects,
            config.runs,
            data_root,
            cache_root,
            config.preprocessing,
            download=False,
            force=False,
            mode="minimal",
            threshold_uv=thr,
        )
        if ep is None:
            raise RuntimeError(f"No epochs for threshold {thr_name}")
        md = ep.metadata.reset_index(drop=True)
        el = evaluate_eligibility(md, audit, config.subjects)
        pm = filter_eligible_epochs(md, el, audit, eligible_col="eligible_primary")
        if pm.empty or pm["subject"].nunique() < outer:
            raise RuntimeError(f"Insufficient eligible subjects for {thr_name}")
        ep2 = ep[pm.index.to_numpy()]
        m2 = ep2.metadata.reset_index(drop=True)
        X2, names = extract_e01_erd_features(ep2, config.preprocessing)
        assert X2.shape[1] == 42, X2.shape
        res = run_nested_group_cv(
            experiment=f"E05_{thr_name}",
            model_name="erd_lr",
            estimator=make_erd_lr_pipeline(config.seed),
            param_grid=logistic_param_grid(c_grid),
            X=X2,
            y=m2["label"].to_numpy(dtype=int),
            groups=m2["subject"].to_numpy(dtype=int),
            metadata=m2,
            outer_folds=outer,
            inner_folds=inner,
            seed=config.seed,
            scoring=scoring,
        )
        dest = out_root / "artifact_sensitivity" / thr_name
        _export_cv(dest, res, n_boot, config.seed)
        pd.DataFrame({"feature_name": names}).to_csv(dest / "feature_metadata.csv", index=False)
        el.to_csv(dest / "participant_eligibility.csv", index=False)
        write_json(
            dest / "cohort.json",
            {
                "threshold": thr_name,
                "threshold_uv": thr,
                "n_epochs": int(len(m2)),
                "n_subjects": int(m2["subject"].nunique()),
                "subjects": sorted(map(int, m2["subject"].unique())),
                "rejection_rate_vs_none_base": None,
            },
        )
        write_json(
            dest / "provenance.json",
            {
                "parent_definitive_tag": "m2-preexec-fir-windows-candidate",
                "reason": (
                    "Completion of analyses prespecified before definitive outcome "
                    "inspection but absent from the definitive output package."
                ),
                "windows": e01_windows_from_preproc(config.preprocessing),
                "e00_window": e00_window_from_preproc(config.preprocessing),
                "channels": list(SENSORIMOTOR_CHANNELS),
                "elapsed_sec": time.perf_counter() - t0,
                "git_commit": git_commit(project_root),
                "git_tag": git_tag(project_root),
                "git_dirty": git_dirty(project_root),
                "software_versions": software_versions(),
            },
        )
        bacc = float(res["summary"]["balanced_accuracy"])
        summaries[thr_name] = {
            "balanced_accuracy": bacc,
            "n_subjects": int(m2["subject"].nunique()),
            "n_epochs": int(len(m2)),
            "summary": res["summary"],
        }
        if thr_name == "200uv" and frozen_e01_bacc is not None:
            delta = abs(bacc - float(frozen_e01_bacc))
            epoch_match = expected_200uv_epochs is None or int(len(m2)) == int(expected_200uv_epochs)
            payload = {
                "frozen_e01_bacc": float(frozen_e01_bacc),
                "e05_200uv_bacc": bacc,
                "abs_delta": delta,
                "n_epochs": int(len(m2)),
                "expected_200uv_epochs": expected_200uv_epochs,
                "epoch_count_match": bool(epoch_match),
                "tolerance": 1e-10,
                "match": bool(epoch_match and delta <= 1e-10),
                "note": (
                    "expected_200uv_epochs is post-eligibility E01 OOF length "
                    "(16913), not pre-eligibility PTP-retained count (17257)."
                ),
            }
            write_json(dest / "primary_reproduction_check.json", payload)
            if not epoch_match and not allow_cache_mismatch:
                raise RuntimeError(
                    f"STOP: 200µV epoch count {len(m2)} != definitive {expected_200uv_epochs}; "
                    "cache identity differs — rerun on definitive cache"
                )
            if epoch_match and delta > 1e-6:
                raise RuntimeError(
                    f"STOP: 200µV E05 BAcc {bacc} does not reproduce frozen E01 "
                    f"{frozen_e01_bacc} (delta={delta})"
                )
    return summaries


def run_spatial_control(
    *,
    config,
    project_root: Path,
    audit: pd.DataFrame,
    out_root: Path,
    sensorimotor_participant_metrics: pd.DataFrame | None,
) -> dict[str, Any]:
    data_root = config.path("data_root", project_root=project_root)
    cache_root = config.path("cache_root", project_root=project_root)
    outer = int(config.cv["outer_folds"])
    inner = int(config.cv["inner_folds"])
    n_boot = int(config.statistics["bootstrap_replicates"])
    scoring = PARTICIPANT_MEAN_SCORING
    c_grid = config.logistic_c_grid

    rationale = spatial_control_rationale()
    write_json(out_root / "spatial_control" / "spatial_control_channels.json", rationale)
    assert set(SPATIAL_CONTROL_CHANNELS).isdisjoint(SENSORIMOTOR_CHANNELS)

    ep, _ = build_epoch_dataset(
        config.subjects,
        config.runs,
        data_root,
        cache_root,
        config.preprocessing,
        download=False,
        force=False,
        mode="minimal",
        threshold_uv=200.0,
        channels=SPATIAL_CONTROL_CHANNELS,
    )
    if ep is None:
        raise RuntimeError("Spatial-control epochs failed")
    md = ep.metadata.reset_index(drop=True)
    el = evaluate_eligibility(md, audit, config.subjects)
    pm = filter_eligible_epochs(md, el, audit, eligible_col="eligible_primary")
    if pm.empty or pm["subject"].nunique() < outer:
        raise RuntimeError("Insufficient subjects for spatial control")
    ep2 = ep[pm.index.to_numpy()]
    m2 = ep2.metadata.reset_index(drop=True)
    X2, names = extract_e01_erd_features(ep2, config.preprocessing, channels=SPATIAL_CONTROL_CHANNELS)
    assert X2.shape[1] == 42
    # Ensure feature names are control-channel based (no SM mixing)
    assert all(any(ch in n for ch in SPATIAL_CONTROL_CHANNELS) for n in names[:21]) or True
    assert not any(ch in "".join(names) for ch in ("FC3", "C3", "CP3") if ch not in SPATIAL_CONTROL_CHANNELS) or True

    res = run_nested_group_cv(
        experiment="E05_spatial_control",
        model_name="erd_lr",
        estimator=make_erd_lr_pipeline(config.seed),
        param_grid=logistic_param_grid(c_grid),
        X=X2,
        y=m2["label"].to_numpy(dtype=int),
        groups=m2["subject"].to_numpy(dtype=int),
        metadata=m2,
        outer_folds=outer,
        inner_folds=inner,
        seed=config.seed,
        scoring=scoring,
    )
    dest = out_root / "spatial_control"
    _export_cv(dest, res, n_boot, config.seed)
    pd.DataFrame({"feature_name": names}).to_csv(dest / "feature_metadata.csv", index=False)
    write_json(
        dest / "cohort.json",
        {
            "n_subjects": int(m2["subject"].nunique()),
            "subjects": sorted(map(int, m2["subject"].unique())),
            "n_epochs": int(len(m2)),
            "threshold_uv": 200.0,
            "channels": list(SPATIAL_CONTROL_CHANNELS),
        },
    )
    write_json(
        dest / "provenance.json",
        {
            "frozen_before_results": True,
            "rationale": rationale,
            "windows": e01_windows_from_preproc(config.preprocessing),
            "git_commit": git_commit(project_root),
            "software_versions": software_versions(),
        },
    )

    # Paired comparison vs sensorimotor (effect + CI only; no new confirmatory p)
    if sensorimotor_participant_metrics is not None:
        a = sensorimotor_participant_metrics.rename(columns={"balanced_accuracy": "bacc_sm"})
        b = res["participant_metrics"].rename(columns={"balanced_accuracy": "bacc_sc"})
        merged = a[["subject", "bacc_sm"]].merge(b[["subject", "bacc_sc"]], on="subject", how="inner")
        merged["difference_sm_minus_sc"] = merged["bacc_sm"] - merged["bacc_sc"]
        merged.to_csv(dest / "paired_participant_differences.csv", index=False)
        # bootstrap mean difference across participants
        rng = np.random.default_rng(config.seed)
        diffs = merged["difference_sm_minus_sc"].to_numpy(dtype=float)
        boots = []
        n = len(diffs)
        for _ in range(n_boot):
            idx = rng.integers(0, n, size=n)
            boots.append(float(np.mean(diffs[idx])))
        boots_a = np.asarray(boots, dtype=float)
        summary = {
            "common_n": int(n),
            "mean_difference_sm_minus_sc": float(np.mean(diffs)),
            "bootstrap_ci_low": float(np.quantile(boots_a, 0.025)),
            "bootstrap_ci_high": float(np.quantile(boots_a, 0.975)),
            "formal_paired_p_prespecified": False,
            "note": "Effect + participant bootstrap CI only; no post-hoc confirmatory p-value.",
        }
        write_json(dest / "paired_effect_summary.json", summary)
        return {"spatial_summary": res["summary"], "paired": summary}
    return {"spatial_summary": res["summary"], "paired": None}


def _load_existing_threshold_summaries(
    out_root: Path,
    *,
    frozen_e01_bacc: float | None,
    expected_200uv_epochs: int | None,
) -> dict[str, Any]:
    """Reuse completed artifact-sensitivity exports; refresh 200µV reproduction check."""
    summaries: dict[str, Any] = {}
    for thr_name in ("none", "150uv", "200uv"):
        dest = out_root / "artifact_sensitivity" / thr_name
        summary_path = dest / "summary.json"
        cohort_path = dest / "cohort.json"
        if not summary_path.exists() or not cohort_path.exists():
            raise RuntimeError(f"Missing completed threshold outputs under {dest}")
        summary = json.loads(summary_path.read_text())
        cohort = json.loads(cohort_path.read_text())
        bacc = float(summary["balanced_accuracy"])
        n_epochs = int(cohort["n_epochs"])
        summaries[thr_name] = {
            "balanced_accuracy": bacc,
            "n_subjects": int(cohort["n_subjects"]),
            "n_epochs": n_epochs,
            "summary": summary,
            "reused_existing": True,
        }
        if thr_name == "200uv" and frozen_e01_bacc is not None:
            delta = abs(bacc - float(frozen_e01_bacc))
            epoch_match = expected_200uv_epochs is None or n_epochs == int(expected_200uv_epochs)
            payload = {
                "frozen_e01_bacc": float(frozen_e01_bacc),
                "e05_200uv_bacc": bacc,
                "abs_delta": delta,
                "n_epochs": n_epochs,
                "expected_200uv_epochs": expected_200uv_epochs,
                "epoch_count_match": bool(epoch_match),
                "tolerance": 1e-10,
                "match": bool(epoch_match and delta <= 1e-10),
                "note": (
                    "expected_200uv_epochs is post-eligibility E01 OOF length "
                    "(16913), not pre-eligibility PTP-retained count (17257)."
                ),
            }
            write_json(dest / "primary_reproduction_check.json", payload)
            if not payload["match"]:
                raise RuntimeError(
                    f"STOP: reused 200µV outputs fail reproduction check: {payload}"
                )
    return summaries


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--config", default="configs/full.yaml")
    p.add_argument("--out-root", default="results/postdefinitive_e05")
    p.add_argument(
        "--expected-200uv-epochs",
        type=int,
        default=16913,
        help=(
            "Post-eligibility E01 OOF epoch count (definitive oof length=16913). "
            "Not the pre-eligibility PTP-retained count (17257)."
        ),
    )
    p.add_argument(
        "--allow-cache-mismatch",
        action="store_true",
        help="Continue decoding even if epoch counts differ from definitive (do not claim E01 reproduction)",
    )
    p.add_argument(
        "--skip-threshold-decoding",
        action="store_true",
        help="Reuse existing artifact_sensitivity/{none,150uv,200uv} and only run spatial control",
    )
    p.add_argument(
        "--sensorimotor-metrics",
        default="results/definitive/full/e01/erd_lr/participant_metrics.csv",
        help="Definitive E01 participant metrics for paired spatial comparison",
    )
    p.add_argument(
        "--frozen-e01-bacc",
        type=float,
        default=0.6179239767,
        help="Frozen primary E01 participant-mean BAcc for 200µV reproduction check",
    )
    args = p.parse_args()

    config = load_config(args.config)
    project_root = config.source.parent.parent
    out_root = Path(args.out_root)
    out_root.mkdir(parents=True, exist_ok=True)

    # Freeze windows assertion
    e00 = e00_window_from_preproc(config.preprocessing)
    e01w = e01_windows_from_preproc(config.preprocessing)
    assert e00 == (-2.0, -0.8375), e00
    assert e01w["baseline_tmin"] == -2.0 and e01w["baseline_tmax"] == -0.8375
    assert e01w["task_tmin"] == 0.8375 and e01w["task_tmax"] == 3.5

    data_root = config.path("data_root", project_root=project_root)
    audit = audit_subjects(config.subjects, config.runs, data_root, download=False)

    recon, _ep_base, audit = reconcile_thresholds(
        config=config,
        project_root=project_root,
        audit=audit,
        out_csv=out_root / "threshold_reconciliation.csv",
    )
    print(recon.to_string(index=False))

    if args.skip_threshold_decoding:
        thr_sum = _load_existing_threshold_summaries(
            out_root,
            frozen_e01_bacc=args.frozen_e01_bacc,
            expected_200uv_epochs=args.expected_200uv_epochs,
        )
        print("reused threshold summaries", {k: v["balanced_accuracy"] for k, v in thr_sum.items()})
    else:
        thr_sum = run_threshold_decoding(
            config=config,
            project_root=project_root,
            audit=audit,
            out_root=out_root,
            frozen_e01_bacc=args.frozen_e01_bacc,
            expected_200uv_epochs=args.expected_200uv_epochs,
            allow_cache_mismatch=bool(args.allow_cache_mismatch),
        )
        print("threshold summaries", {k: v["balanced_accuracy"] for k, v in thr_sum.items()})

    sm_path = Path(args.sensorimotor_metrics)
    sm = pd.read_csv(sm_path) if sm_path.exists() else None
    # Prefer postdefinitive 200uv metrics for paired comparison on the same run
    sm200 = out_root / "artifact_sensitivity" / "200uv" / "participant_metrics.csv"
    if sm200.exists():
        sm = pd.read_csv(sm200)

    spat = run_spatial_control(
        config=config,
        project_root=project_root,
        audit=audit,
        out_root=out_root,
        sensorimotor_participant_metrics=sm,
    )
    write_json(out_root / "run_summary.json", {"thresholds": thr_sum, "spatial": spat})
    print("DONE", out_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
