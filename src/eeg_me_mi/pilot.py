"""Milestone-2 complete-path local pilot (engineering validation only)."""

from __future__ import annotations

import json
import time
import tracemalloc
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from eeg_me_mi.analyses import (
    e03_laterality,
    e03_roi_and_channel_effects,
    e04_heterogeneity,
    e06_first60_mask,
    e08_drift_diagnostics,
    participant_erd_table,
)
from eeg_me_mi.audit import audit_subjects
from eeg_me_mi.compare import compare_e00_e01, paired_signflip_test
from eeg_me_mi.config import AnalysisConfig, load_config
from eeg_me_mi.cv import assert_participant_disjoint, fold_assignment_table, run_nested_group_cv
from eeg_me_mi.eligibility import E02_ANALYSES, evaluate_eligibility, filter_e02_epochs, filter_eligible_epochs
from eeg_me_mi.features import (
    extract_e00_log_bandpower_features,
    extract_e01_erd_features,
    task_window_array,
)
from eeg_me_mi.metrics import bootstrap_participant_means
from eeg_me_mi.models import (
    logistic_param_grid,
    make_csp_lda_pipeline,
    make_dummy_pipeline,
    make_erd_lr_pipeline,
    make_riemann_lr_pipeline,
)
from eeg_me_mi.permutation import generate_permutation_labels, matched_pair_label_permutation
from eeg_me_mi.preprocess import build_epoch_dataset
from eeg_me_mi.provenance import write_json, write_run_metadata
from eeg_me_mi.rois import SPATIAL_CONTROL_CHANNELS, spatial_control_rationale


def _export_cv(folder: Path, result: dict, n_boot: int, seed: int) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    result["oof_predictions"].to_csv(folder / "oof_predictions.csv", index=False)
    result["participant_metrics"].to_csv(folder / "participant_metrics.csv", index=False)
    result["fold_metrics"].to_csv(folder / "fold_metrics.csv", index=False)
    result["tuning"].to_csv(folder / "inner_tuning.csv", index=False)
    boot, _ = bootstrap_participant_means(
        result["participant_metrics"], n_bootstrap=n_boot, seed=seed, metrics=("balanced_accuracy",)
    )
    boot.to_csv(folder / "bootstrap_summary.csv", index=False)
    write_json(folder / "summary.json", result["summary"])


def run_pilot(
    config: AnalysisConfig,
    *,
    project_root: Path | None = None,
    download: bool = True,
    force_preprocess: bool = False,
) -> dict[str, Any]:
    """Exercise E00–E08 paths on a reduced cohort."""
    project_root = project_root or config.source.parent.parent
    data_root = config.path("data_root", project_root=project_root)
    cache_root = config.path("cache_root", project_root=project_root)
    output_root = config.path("output_root", project_root=project_root)
    for sub in ("e00", "e01", "e02", "e03", "e04", "e05", "e06", "e07", "e08", "comparisons", "qc"):
        (output_root / sub).mkdir(parents=True, exist_ok=True)

    write_run_metadata(output_root, config_raw=config.raw, project_root=project_root, seed=config.seed)
    timings: dict[str, float] = {}
    tracemalloc.start()
    t_all = time.perf_counter()

    audit = audit_subjects(config.subjects, config.runs, data_root, download=download)
    audit.to_csv(output_root / "qc" / "raw_data_audit.csv", index=False)

    t0 = time.perf_counter()
    epochs, rejection_log = build_epoch_dataset(
        config.subjects,
        config.runs,
        data_root,
        cache_root,
        config.preprocessing,
        download=download,
        force=force_preprocess,
        mode="minimal",
        threshold_uv=float(config.preprocessing["reject_peak_to_peak_uv"]),
    )
    timings["preprocess_sec"] = time.perf_counter() - t0
    rejection_log.to_csv(output_root / "qc" / "rejection_qc.csv", index=False)
    if epochs is None:
        raise RuntimeError("No epochs for pilot")

    metadata = epochs.metadata.reset_index(drop=True)
    elig = evaluate_eligibility(
        metadata,
        audit,
        config.subjects,
        min_epochs_per_mode=int(config.eligibility.get("min_epochs_per_mode", 30)),
        e02_min_epochs=int(config.eligibility.get("e02_min_epochs_per_mode", 15)),
        e02_min_pairs=int(config.eligibility.get("e02_min_matched_pairs", 2)),
    )
    elig.to_csv(output_root / "qc" / "participant_eligibility.csv", index=False)
    primary_meta = filter_eligible_epochs(metadata, elig, audit)
    if primary_meta.empty:
        raise RuntimeError("No E01-eligible participants in pilot")
    idx = primary_meta.index.to_numpy()
    epochs_p = epochs[idx]
    meta = epochs_p.metadata.reset_index(drop=True)

    y = meta["label"].to_numpy(dtype=int)
    groups = meta["subject"].to_numpy(dtype=int)
    outer = int(config.cv["outer_folds"])
    inner = int(config.cv["inner_folds"])
    n_boot = int(config.statistics["bootstrap_replicates"])
    assignments = fold_assignment_table(groups, outer, config.seed)
    assert_participant_disjoint(assignments)
    assignments.to_csv(output_root / "qc" / "fold_assignments.csv", index=False)

    X_e01, names_e01 = extract_e01_erd_features(epochs_p, config.preprocessing)
    X_e00, names_e00 = extract_e00_log_bandpower_features(epochs_p, config.preprocessing)
    X_task = task_window_array(epochs_p, config.preprocessing)
    pd.DataFrame({"feature_name": names_e01}).to_csv(output_root / "e01" / "feature_metadata.csv", index=False)
    pd.DataFrame({"feature_name": names_e00}).to_csv(output_root / "e00" / "feature_metadata.csv", index=False)

    c_grid = config.logistic_c_grid
    scoring = str(config.cv.get("scoring", "balanced_accuracy"))

    # E01 models
    t0 = time.perf_counter()
    e01_models = {
        "dummy": (make_dummy_pipeline("prior"), None),
        "erd_lr": (make_erd_lr_pipeline(config.seed), logistic_param_grid(c_grid)),
        "csp_lda": (make_csp_lda_pipeline(), None),
        "tangent_lr": (make_riemann_lr_pipeline(config.seed), logistic_param_grid(c_grid)),
    }
    e01_results = {}
    for name, (est, grid) in e01_models.items():
        X = X_e01 if name in {"dummy", "erd_lr"} else X_task
        res = run_nested_group_cv(
            experiment="E01",
            model_name=name,
            estimator=est,
            param_grid=grid,
            X=X,
            y=y,
            groups=groups,
            metadata=meta,
            outer_folds=outer,
            inner_folds=inner,
            seed=config.seed,
            scoring=scoring,
        )
        e01_results[name] = res
        _export_cv(output_root / "e01" / name, res, n_boot, config.seed)
    timings["e01_sec"] = time.perf_counter() - t0

    # E00
    t0 = time.perf_counter()
    e00 = run_nested_group_cv(
        experiment="E00",
        model_name="precue_logbp_lr",
        estimator=make_erd_lr_pipeline(config.seed),
        param_grid=logistic_param_grid(c_grid),
        X=X_e00,
        y=y,
        groups=groups,
        metadata=meta,
        outer_folds=outer,
        inner_folds=inner,
        seed=config.seed,
        scoring=scoring,
    )
    _export_cv(output_root / "e00", e00, n_boot, config.seed)
    timings["e00_sec"] = time.perf_counter() - t0

    comparison, comp_sum = compare_e00_e01(
        e00["participant_metrics"], e01_results["erd_lr"]["participant_metrics"], n_bootstrap=n_boot, seed=config.seed
    )
    comparison.to_csv(output_root / "comparisons" / "e00_vs_e01_participant.csv", index=False)
    comp_sum.to_csv(output_root / "comparisons" / "e00_vs_e01_bootstrap_summary.csv", index=False)
    signflip = paired_signflip_test(
        comparison["difference_e01_minus_e00"].to_numpy(),
        n_signflips=max(50, n_boot),
        seed=config.seed,
    )
    write_json(output_root / "comparisons" / "e00_vs_e01_signflip.json", signflip)

    # E02 — independent cohorts from full 200 µV metadata (not E01-primary subset)
    t0 = time.perf_counter()
    for analysis in E02_ANALYSES:
        e02_meta = filter_e02_epochs(metadata, elig, audit, analysis)
        if e02_meta.empty or e02_meta["subject"].nunique() < outer:
            write_json(output_root / "e02" / analysis / "skipped.json", {"reason": "insufficient_subjects"})
            continue
        ep2 = epochs[e02_meta.index.to_numpy()]
        m = ep2.metadata.reset_index(drop=True)
        Xi, _ = extract_e01_erd_features(ep2, config.preprocessing)
        yi = m["label"].to_numpy(dtype=int)
        gi = m["subject"].to_numpy(dtype=int)
        res = run_nested_group_cv(
            experiment=f"E02_{analysis}",
            model_name="erd_lr",
            estimator=make_erd_lr_pipeline(config.seed),
            param_grid=logistic_param_grid(c_grid),
            X=Xi,
            y=yi,
            groups=gi,
            metadata=m,
            outer_folds=outer,
            inner_folds=inner,
            seed=config.seed,
            scoring=scoring,
        )
        _export_cv(output_root / "e02" / analysis, res, n_boot, config.seed)
    timings["e02_sec"] = time.perf_counter() - t0

    # E03
    erd_df = participant_erd_table(epochs_p, config.preprocessing)
    roi_part, roi_sum, ch_sum = e03_roi_and_channel_effects(erd_df)
    lat = e03_laterality(erd_df)
    roi_part.to_csv(output_root / "e03" / "roi_participant_effects.csv", index=False)
    roi_sum.to_csv(output_root / "e03" / "roi_summary.csv", index=False)
    ch_sum.to_csv(output_root / "e03" / "channel_summary_fdr.csv", index=False)
    lat.to_csv(output_root / "e03" / "laterality.csv", index=False)

    # E04
    het, corr = e04_heterogeneity(e01_results["erd_lr"]["participant_metrics"], erd_df, rejection_log)
    het.to_csv(output_root / "e04" / "participant_heterogeneity.csv", index=False)
    corr.to_csv(output_root / "e04" / "exploratory_correlations.csv", index=False)

    # E05 thresholds + spatial control
    t0 = time.perf_counter()
    e05_rows = []
    for thr_name, thr in (("none", None), ("150uv", 150.0), ("200uv", 200.0)):
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
            continue
        md = ep.metadata.reset_index(drop=True)
        el = evaluate_eligibility(md, audit, config.subjects)
        e05_rows.append(
            {
                "threshold": thr_name,
                "n_epochs": len(md),
                "n_e01_eligible": int(el["eligible_primary"].sum()),
            }
        )
        # Small decoding only for primary-eligible at this threshold (erd_lr)
        pm = filter_eligible_epochs(md, el, audit)
        if pm.empty or pm["subject"].nunique() < outer:
            continue
        ep2 = ep[pm.index.to_numpy()]
        m2 = ep2.metadata.reset_index(drop=True)
        X2, _ = extract_e01_erd_features(ep2, config.preprocessing)
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
        _export_cv(output_root / "e05" / thr_name, res, n_boot, config.seed)
    pd.DataFrame(e05_rows).to_csv(output_root / "e05" / "threshold_cohorts.csv", index=False)
    write_json(output_root / "e05" / "spatial_control_channels.json", spatial_control_rationale())

    # Spatial-control decode (may skip if channels missing on some subjects)
    try:
        ep_sc, _ = build_epoch_dataset(
            config.subjects,
            config.runs,
            data_root,
            cache_root,
            config.preprocessing,
            download=False,
            mode="minimal",
            threshold_uv=200.0,
            channels=SPATIAL_CONTROL_CHANNELS,
        )
        if ep_sc is not None:
            md = ep_sc.metadata.reset_index(drop=True)
            el = evaluate_eligibility(md, audit, config.subjects)
            pm = filter_eligible_epochs(md, el, audit)
            if not pm.empty and pm["subject"].nunique() >= outer:
                ep2 = ep_sc[pm.index.to_numpy()]
                m2 = ep2.metadata.reset_index(drop=True)
                X2, _ = extract_e01_erd_features(ep2, config.preprocessing, channels=SPATIAL_CONTROL_CHANNELS)
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
                _export_cv(output_root / "e05" / "spatial_control", res, n_boot, config.seed)
    except Exception as exc:  # noqa: BLE001
        write_json(output_root / "e05" / "spatial_control_error.json", {"error": repr(exc)})
    timings["e05_sec"] = time.perf_counter() - t0

    # E06
    mask60 = e06_first60_mask(meta)
    if meta.loc[mask60, "subject"].nunique() >= outer:
        res = run_nested_group_cv(
            experiment="E06_first60",
            model_name="erd_lr",
            estimator=make_erd_lr_pipeline(config.seed),
            param_grid=logistic_param_grid(c_grid),
            X=X_e01[mask60],
            y=y[mask60],
            groups=groups[mask60],
            metadata=meta.loc[mask60].reset_index(drop=True),
            outer_folds=outer,
            inner_folds=inner,
            seed=config.seed,
            scoring=scoring,
        )
        _export_cv(output_root / "e06" / "first60", res, n_boot, config.seed)
    _export_cv(output_root / "e06" / "all_events", e01_results["erd_lr"], n_boot, config.seed)

    # E08
    drift = e08_drift_diagnostics(epochs_p, config.preprocessing)
    for name, frame in drift.items():
        frame.to_csv(output_root / "e08" / f"{name}.csv", index=False)

    # E07 small permutation smoke
    t0 = time.perf_counter()
    n_perm = int(config.statistics.get("permutations", 5))
    perms = generate_permutation_labels(meta, y, n_perm, config.seed)
    null_scores = []
    for i, y_perm in enumerate(perms):
        res = run_nested_group_cv(
            experiment=f"E07_perm_{i}",
            model_name="erd_lr",
            estimator=make_erd_lr_pipeline(config.seed),
            param_grid=logistic_param_grid(c_grid),
            X=X_e01,
            y=y_perm,
            groups=groups,
            metadata=meta,
            outer_folds=outer,
            inner_folds=inner,
            seed=config.seed,
            scoring=scoring,
        )
        null_scores.append(res["summary"]["balanced_accuracy"])
    write_json(
        output_root / "e07" / "small_permutation_smoke.json",
        {"n_permutations": n_perm, "null_balanced_accuracy": null_scores},
    )
    timings["e07_smoke_sec"] = time.perf_counter() - t0

    timings["total_sec"] = time.perf_counter() - t_all
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    bench = {"timings_sec": timings, "tracemalloc_peak_mb": peak / (1024 * 1024)}
    write_json(output_root / "qc" / "resource_benchmark.json", bench)
    write_json(
        output_root / "qc" / "pilot_summary.json",
        {
            "eligible_subjects": sorted(map(int, meta["subject"].unique())),
            "e00_bacc": e00["summary"].get("balanced_accuracy"),
            "e01_erd_bacc": e01_results["erd_lr"]["summary"].get("balanced_accuracy"),
            "e01_csp_bacc": e01_results["csp_lda"]["summary"].get("balanced_accuracy"),
            "e01_riemann_bacc": e01_results["tangent_lr"]["summary"].get("balanced_accuracy"),
            "timings_sec": timings,
        },
    )
    return {"output_root": output_root, "benchmark": bench, "e01": e01_results, "e00": e00}


def run_pilot_from_config(path: str | Path, **kwargs) -> dict[str, Any]:
    return run_pilot(load_config(path), **kwargs)
