"""Definitive full-analysis execution path (distinct from pilot).

Do not alias ``run_pilot``. This module implements the frozen E00–E08 matrix
with fail-closed validation and completion manifests.

Definitive execution is refused on a dirty git tree by default.
"""

from __future__ import annotations

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
from eeg_me_mi.cv import (
    PARTICIPANT_MEAN_SCORING,
    assert_participant_disjoint,
    fold_assignment_table,
    run_nested_group_cv,
)
from eeg_me_mi.e07 import run_e07_inference
from eeg_me_mi.eligibility import (
    E02_ANALYSES,
    evaluate_eligibility,
    filter_e02_epochs,
    filter_eligible_epochs,
)
from eeg_me_mi.features import (
    extract_e00_log_bandpower_features,
    extract_e01_erd_features,
    task_window_array,
)
from eeg_me_mi.filter_support import e00_window_from_preproc
from eeg_me_mi.metrics import bootstrap_participant_means
from eeg_me_mi.models import (
    logistic_param_grid,
    make_csp_lda_pipeline,
    make_dummy_pipeline,
    make_erd_lr_pipeline,
    make_riemann_lr_pipeline,
)
from eeg_me_mi.preprocess import build_epoch_dataset
from eeg_me_mi.provenance import (
    assert_clean_tree_for_definitive,
    write_json,
    write_run_metadata,
)
from eeg_me_mi.rois import spatial_control_rationale


REQUIRED_FULL_FIELDS = (
    "schema_version",
    "run_name",
    "seed",
    "subjects",
    "runs",
    "paths",
    "preprocessing",
    "cv",
    "statistics",
    "models",
    "eligibility",
    "logistic_c_grid",
)

MANDATORY_ANALYSES = (
    "e00",
    "e01/dummy",
    "e01/erd_lr",
    "e01/csp_lda",
    "e01/tangent_lr",
    "e01_strict_sensitivity/erd_lr",
    "comparisons/e00_vs_e01_participant.csv",
    "e07/completion_manifest.json",
)


def validate_definitive_config(config: AnalysisConfig) -> None:
    """Reject pilot / incomplete configurations for definitive execution."""
    raw = config.raw
    name = str(config.run_name).lower()
    if "pilot" in name or "toy" in name:
        raise ValueError(f"Rejecting non-definitive run_name={config.run_name!r}")
    missing = [k for k in REQUIRED_FULL_FIELDS if k not in raw]
    if missing:
        raise ValueError(f"Definitive config missing fields: {missing}")
    if config.subjects != tuple(range(1, 110)):
        raise ValueError(
            f"Definitive cohort must be subjects 1–109; got {config.subjects[:3]}... "
            f"(n={len(config.subjects)})"
        )
    if tuple(config.runs) != tuple(range(3, 15)):
        raise ValueError(f"Definitive runs must be 3–14; got {config.runs}")
    scoring = str(config.cv.get("scoring", ""))
    if scoring not in {PARTICIPANT_MEAN_SCORING, "balanced_accuracy"}:
        raise ValueError(
            f"Definitive inner scoring must be participant-mean balanced accuracy; got {scoring!r}"
        )
    if "roc_auc" in scoring:
        raise ValueError("Obsolete roc_auc inner tuning is not permitted in definitive config")
    pre = config.preprocessing
    for key in ("l_freq", "h_freq", "target_sfreq", "epoch_tmin", "epoch_tmax", "reject_peak_to_peak_uv"):
        if key not in pre:
            raise ValueError(f"Missing preprocessing field: {key}")
    # Ensure leakage-safe E00/E01 windows are resolvable and FIR-safe.
    from eeg_me_mi.filter_support import e00_window_from_preproc, e01_windows_from_preproc

    e00_window_from_preproc(pre)
    e01_windows_from_preproc(pre)
    if list(config.logistic_c_grid) != [0.01, 0.1, 1.0, 10.0]:
        raise ValueError(f"Frozen C grid required; got {config.logistic_c_grid}")


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


def _require_paths(output_root: Path, relative: tuple[str, ...]) -> None:
    missing = [r for r in relative if not (output_root / r).exists()]
    if missing:
        raise RuntimeError(f"Mandatory outputs missing: {missing}")


def run_full(
    config: AnalysisConfig,
    *,
    project_root: Path | None = None,
    download: bool = False,
    force_preprocess: bool = False,
    allow_dirty: bool = False,
    dry_run: bool = False,
    run_e07: bool = True,
    e07_n_permutations: int | None = None,
) -> dict[str, Any]:
    """Execute the frozen definitive experiment matrix."""
    project_root = project_root or config.source.parent.parent
    validate_definitive_config(config)
    assert_clean_tree_for_definitive(project_root, allow_dirty=allow_dirty or dry_run)

    data_root = config.path("data_root", project_root=project_root)
    cache_root = config.path("cache_root", project_root=project_root)
    output_root = config.path("output_root", project_root=project_root)

    if dry_run:
        payload = {
            "dry_run": True,
            "run_name": config.run_name,
            "n_subjects": len(config.subjects),
            "runs": list(config.runs),
            "e00_window": e00_window_from_preproc(config.preprocessing),
            "scoring": PARTICIPANT_MEAN_SCORING,
            "analyses": list(MANDATORY_ANALYSES),
            "output_root": str(output_root),
        }
        output_root.mkdir(parents=True, exist_ok=True)
        write_json(output_root / "qc" / "dry_run_manifest.json", payload)
        return payload

    for sub in (
        "e00",
        "e01",
        "e01_strict_sensitivity",
        "e01_sampling_rate_sensitivity",
        "e02",
        "e03",
        "e04",
        "e05",
        "e06",
        "e07",
        "e08",
        "comparisons",
        "qc",
    ):
        (output_root / sub).mkdir(parents=True, exist_ok=True)

    meta_run = write_run_metadata(
        output_root,
        config_raw=config.raw,
        project_root=project_root,
        seed=config.seed,
        extra={"execution_mode": "definitive_full"},
    )
    if meta_run.get("git_dirty") and not allow_dirty:
        raise RuntimeError("Dirty tree recorded; refusing definitive run")

    timings: dict[str, float] = {}
    tracemalloc.start()
    t_all = time.perf_counter()

    audit = audit_subjects(config.subjects, config.runs, data_root, download=download)
    audit.to_csv(output_root / "qc" / "raw_data_audit.csv", index=False)
    if audit.empty:
        raise RuntimeError("Audit produced no rows")

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
        raise RuntimeError("No epochs after preprocessing")

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

    # Reconciliation targets from performance-blind eligibility audit (not hard truth).
    recon = {
        "e01_primary": int(elig["eligible_primary"].sum()),
        "strict": int(elig["eligible_strict"].sum()),
        **{f"e02_{a}": int(elig[f"e02_{a}_eligible"].sum()) for a in E02_ANALYSES},
    }
    write_json(output_root / "qc" / "cohort_reconciliation.json", recon)

    primary_meta = filter_eligible_epochs(metadata, elig, audit, eligible_col="eligible_primary")
    if primary_meta.empty:
        raise RuntimeError("No E01-eligible participants")
    idx = primary_meta.index.to_numpy()
    epochs_p = epochs[idx]
    meta = epochs_p.metadata.reset_index(drop=True)

    y = meta["label"].to_numpy(dtype=int)
    groups = meta["subject"].to_numpy(dtype=int)
    outer = int(config.cv["outer_folds"])
    inner = int(config.cv["inner_folds"])
    n_boot = int(config.statistics["bootstrap_replicates"])
    scoring = PARTICIPANT_MEAN_SCORING
    c_grid = config.logistic_c_grid

    assignments = fold_assignment_table(groups, outer, config.seed)
    assert_participant_disjoint(assignments)
    assignments.to_csv(output_root / "qc" / "fold_assignments_e01_primary.csv", index=False)

    X_e01, names_e01 = extract_e01_erd_features(epochs_p, config.preprocessing)
    X_e00, names_e00 = extract_e00_log_bandpower_features(epochs_p, config.preprocessing)
    X_task = task_window_array(epochs_p, config.preprocessing)
    pd.DataFrame({"feature_name": names_e01}).to_csv(output_root / "e01" / "feature_metadata.csv", index=False)
    pd.DataFrame({"feature_name": names_e00}).to_csv(output_root / "e00" / "feature_metadata.csv", index=False)
    write_json(
        output_root / "e00" / "window.json",
        {"tmin_tmax": e00_window_from_preproc(config.preprocessing)},
    )

    # ---- E01 ----
    t0 = time.perf_counter()
    e01_models = {
        "dummy": (make_dummy_pipeline("prior"), None),
        "erd_lr": (make_erd_lr_pipeline(config.seed), logistic_param_grid(c_grid)),
        "csp_lda": (make_csp_lda_pipeline(), None),
        "tangent_lr": (make_riemann_lr_pipeline(config.seed), logistic_param_grid(c_grid)),
    }
    e01_results: dict[str, Any] = {}
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

    # ---- Strict-cohort sensitivity (not a new primary) ----
    strict_meta = filter_eligible_epochs(metadata, elig, audit, eligible_col="eligible_strict")
    write_json(
        output_root / "e01_strict_sensitivity" / "cohort.json",
        {
            "label": "strict-cohort sensitivity analysis",
            "n_subjects": int(strict_meta["subject"].nunique()) if len(strict_meta) else 0,
            "subjects": sorted(map(int, strict_meta["subject"].unique())) if len(strict_meta) else [],
        },
    )
    if not strict_meta.empty and strict_meta["subject"].nunique() >= outer:
        ep_s = epochs[strict_meta.index.to_numpy()]
        m_s = ep_s.metadata.reset_index(drop=True)
        # Participant-disjoint folds specific to strict population.
        X_s, _ = extract_e01_erd_features(ep_s, config.preprocessing)
        res_s = run_nested_group_cv(
            experiment="E01_strict_sensitivity",
            model_name="erd_lr",
            estimator=make_erd_lr_pipeline(config.seed),
            param_grid=logistic_param_grid(c_grid),
            X=X_s,
            y=m_s["label"].to_numpy(dtype=int),
            groups=m_s["subject"].to_numpy(dtype=int),
            metadata=m_s,
            outer_folds=outer,
            inner_folds=inner,
            seed=config.seed,
            scoring=scoring,
        )
        _export_cv(output_root / "e01_strict_sensitivity" / "erd_lr", res_s, n_boot, config.seed)
    else:
        write_json(
            output_root / "e01_strict_sensitivity" / "erd_lr" / "skipped.json",
            {"reason": "insufficient_strict_subjects"},
        )

    # ---- Optional sampling-rate sensitivity prep (S088/S092/S100) ----
    sr_exclude = {88, 92, 100}
    sr_meta = meta.loc[~meta["subject"].isin(sr_exclude)].copy()
    write_json(
        output_root / "e01_sampling_rate_sensitivity" / "plan.json",
        {
            "label": "sampling-rate sensitivity analysis",
            "excluded_subjects": sorted(sr_exclude),
            "reason": "structurally valid 128 Hz recordings; Nyquist sufficient for 8–30 Hz",
            "primary_cohort_unchanged": True,
            "n_remaining_in_primary_subset": int(sr_meta["subject"].nunique()),
            "execute_by_default": False,
        },
    )

    # ---- E00 ----
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
        e00["participant_metrics"],
        e01_results["erd_lr"]["participant_metrics"],
        n_bootstrap=n_boot,
        seed=config.seed,
    )
    comparison.to_csv(output_root / "comparisons" / "e00_vs_e01_participant.csv", index=False)
    comp_sum.to_csv(output_root / "comparisons" / "e00_vs_e01_bootstrap_summary.csv", index=False)
    signflip = paired_signflip_test(
        comparison["difference_e01_minus_e00"].to_numpy(),
        n_signflips=max(50, n_boot),
        seed=config.seed,
    )
    write_json(output_root / "comparisons" / "e00_vs_e01_signflip.json", signflip)

    # ---- E02: independent cohorts from full 200 µV metadata ----
    t0 = time.perf_counter()
    for analysis in E02_ANALYSES:
        e02_meta = filter_e02_epochs(metadata, elig, audit, analysis)
        n_subj = int(e02_meta["subject"].nunique()) if len(e02_meta) else 0
        write_json(
            output_root / "e02" / analysis / "cohort.json",
            {
                "analysis": analysis,
                "n_subjects": n_subj,
                "subjects": sorted(map(int, e02_meta["subject"].unique())) if len(e02_meta) else [],
                "routed_from": "full_200uv_metadata",
                "not_restricted_to_e01_primary": True,
            },
        )
        if e02_meta.empty or n_subj < outer:
            write_json(output_root / "e02" / analysis / "skipped.json", {"reason": "insufficient_subjects"})
            continue
        ep2 = epochs[e02_meta.index.to_numpy()]
        m2 = ep2.metadata.reset_index(drop=True)
        X2, _ = extract_e01_erd_features(ep2, config.preprocessing)
        # Population-specific participant-disjoint folds.
        res = run_nested_group_cv(
            experiment=f"E02_{analysis}",
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
        _export_cv(output_root / "e02" / analysis, res, n_boot, config.seed)
    timings["e02_sec"] = time.perf_counter() - t0

    # ---- E03 ----
    erd_df = participant_erd_table(epochs_p, config.preprocessing)
    roi_part, roi_sum, ch_sum = e03_roi_and_channel_effects(erd_df)
    lat = e03_laterality(erd_df)
    roi_part.to_csv(output_root / "e03" / "roi_participant_effects.csv", index=False)
    roi_sum.to_csv(output_root / "e03" / "roi_summary.csv", index=False)
    ch_sum.to_csv(output_root / "e03" / "channel_summary_fdr.csv", index=False)
    lat.to_csv(output_root / "e03" / "laterality.csv", index=False)
    write_json(
        output_root / "e03" / "multiplicity_families.json",
        {
            "roi_level": "FDR within ROI×band tests",
            "channel_level": "separate FDR within channel×band exploratory tests",
            "percentile_columns": "participant_effect distribution, not CI for the mean",
            "mean_bootstrap_ci": "participant-level bootstrap CI for mean effect",
        },
    )

    # ---- E04 ----
    het, corr = e04_heterogeneity(e01_results["erd_lr"]["participant_metrics"], erd_df, rejection_log)
    het.to_csv(output_root / "e04" / "participant_heterogeneity.csv", index=False)
    corr.to_csv(output_root / "e04" / "exploratory_correlations.csv", index=False)

    # ---- E05 (threshold cohorts + spatial control channel list) ----
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
    pd.DataFrame(e05_rows).to_csv(output_root / "e05" / "threshold_cohorts.csv", index=False)
    write_json(output_root / "e05" / "spatial_control_channels.json", spatial_control_rationale())

    # ---- E06 ----
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

    # ---- E08 ----
    drift = e08_drift_diagnostics(epochs_p, config.preprocessing)
    for name, frame in drift.items():
        frame.to_csv(output_root / "e08" / f"{name}.csv", index=False)

    # ---- E07 definitive engine ----
    if run_e07:
        n_perm = int(e07_n_permutations if e07_n_permutations is not None else config.statistics["permutations"])
        t0 = time.perf_counter()
        e07 = run_e07_inference(
            X=X_e01,
            y=y,
            groups=groups,
            metadata=meta,
            observed_statistic=float(e01_results["erd_lr"]["summary"]["balanced_accuracy"]),
            n_permutations=n_perm,
            seed=config.seed,
            outer_folds=outer,
            inner_folds=inner,
            c_grid=c_grid,
            output_dir=output_root / "e07",
            resume=True,
            scoring=scoring,
        )
        timings["e07_sec"] = time.perf_counter() - t0
        # Equality check: observed matches E01 primary
        if abs(e07["summary"]["observed_statistic"] - e01_results["erd_lr"]["summary"]["balanced_accuracy"]) > 1e-12:
            raise RuntimeError("E07 observed statistic != E01 primary participant-mean BAcc")

    timings["total_sec"] = time.perf_counter() - t_all
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    write_json(
        output_root / "qc" / "inferential_hierarchy.json",
        {
            "primary_effect_estimate": "E01 participant-mean balanced accuracy",
            "primary_uncertainty": "Participant bootstrap 95% CI for E01",
            "primary_empirical_null_support": "E07 structured permutation test",
            "mandatory_protocol_state_control": "E00 pre-cue run-state decoding",
            "e00_vs_e01": "Participant-paired E01−E00 control comparison (not independent H1 proof)",
            "e02": "Secondary movement-specific decoding",
            "e03": "Secondary physiological analysis",
            "e04": "Exploratory only",
            "e05_e06_e08": "Sensitivity/supplementary/diagnostic",
            "no_competing_primary_significance_tests": True,
        },
    )

    completion = {
        "complete": True,
        "run_name": config.run_name,
        "git_commit": meta_run.get("git_commit"),
        "git_tag": meta_run.get("git_tag"),
        "git_dirty": meta_run.get("git_dirty"),
        "config_checksum": meta_run.get("config_checksum"),
        "timings_sec": timings,
        "tracemalloc_peak_mb": peak / (1024 * 1024),
        "cohort_reconciliation": recon,
        "e01_primary_bacc": e01_results["erd_lr"]["summary"].get("balanced_accuracy"),
        "e00_bacc": e00["summary"].get("balanced_accuracy"),
    }
    # Fail closed on mandatory outputs
    _require_paths(
        output_root,
        (
            "e00/summary.json",
            "e01/erd_lr/summary.json",
            "e01/dummy/summary.json",
            "e01/csp_lda/summary.json",
            "e01/tangent_lr/summary.json",
            "comparisons/e00_vs_e01_participant.csv",
            "qc/participant_eligibility.csv",
            "qc/run_metadata.json",
        ),
    )
    if run_e07:
        _require_paths(output_root, ("e07/completion_manifest.json", "e07/e07_summary.json"))
    write_json(output_root / "qc" / "completion_manifest.json", completion)
    return {
        "output_root": output_root,
        "completion": completion,
        "e01": e01_results,
        "e00": e00,
    }


def run_full_from_config(path: str | Path, **kwargs) -> dict[str, Any]:
    return run_full(load_config(path), **kwargs)
