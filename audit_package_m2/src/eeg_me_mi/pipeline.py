"""End-to-end Milestone 1 pipeline for E00 and E01."""

from __future__ import annotations

import json
import time
import tracemalloc
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from eeg_me_mi.audit import audit_subjects, summarize_anomalies
from eeg_me_mi.compare import compare_e00_e01
from eeg_me_mi.config import AnalysisConfig, load_config
from eeg_me_mi.cv import assert_participant_disjoint, fold_assignment_table, run_nested_group_cv
from eeg_me_mi.eligibility import evaluate_eligibility, filter_eligible_epochs
from eeg_me_mi.features import (
    N_FEATURES,
    extract_e00_log_bandpower_features,
    extract_e01_erd_features,
)
from eeg_me_mi.metrics import bootstrap_participant_means
from eeg_me_mi.models import logistic_param_grid, make_dummy_pipeline, make_erd_lr_pipeline
from eeg_me_mi.preprocess import build_epoch_dataset
from eeg_me_mi.provenance import write_json, write_run_metadata


def _ensure_dirs(output_root: Path) -> dict[str, Path]:
    dirs = {
        "root": output_root,
        "audit": output_root / "audit",
        "e00": output_root / "e00",
        "e01": output_root / "e01",
        "comparisons": output_root / "comparisons",
        "qc": output_root / "qc",
    }
    for path in dirs.values():
        path.mkdir(parents=True, exist_ok=True)
    return dirs


def _rss_mb() -> float | None:
    try:
        with open("/proc/self/status", encoding="utf-8") as handle:
            for line in handle:
                if line.startswith("VmRSS:"):
                    return float(line.split()[1]) / 1024.0
    except OSError:
        return None
    return None


def run_pipeline(
    config: AnalysisConfig,
    *,
    project_root: Path | None = None,
    download: bool = True,
    force_preprocess: bool = False,
) -> dict[str, Any]:
    """Execute the complete E00/E01 toy/pilot pipeline."""
    project_root = project_root or config.source.parent.parent
    data_root = config.path("data_root", project_root=project_root)
    cache_root = config.path("cache_root", project_root=project_root)
    output_root = config.path("output_root", project_root=project_root)
    dirs = _ensure_dirs(output_root)

    timings: dict[str, float] = {}
    peak_ram_mb = 0.0
    tracemalloc.start()
    t0_all = time.perf_counter()

    write_run_metadata(
        output_root,
        config_raw=config.raw,
        project_root=project_root,
        seed=config.seed,
    )

    # ------------------------------------------------------------------ audit
    t0 = time.perf_counter()
    audit = audit_subjects(config.subjects, config.runs, data_root, download=download)
    audit.to_csv(dirs["audit"] / "raw_data_audit.csv", index=False)
    summarize_anomalies(audit).to_csv(dirs["audit"] / "anomaly_watchlist_rows.csv", index=False)
    timings["audit_sec"] = time.perf_counter() - t0
    peak_ram_mb = max(peak_ram_mb, _rss_mb() or 0.0)

    # ------------------------------------------------------------ preprocess
    t0 = time.perf_counter()
    epochs, rejection_log = build_epoch_dataset(
        config.subjects,
        config.runs,
        data_root,
        cache_root,
        config.preprocessing,
        download=download,
        force=force_preprocess,
    )
    timings["preprocess_sec"] = time.perf_counter() - t0
    peak_ram_mb = max(peak_ram_mb, _rss_mb() or 0.0)
    rejection_log.to_csv(dirs["qc"] / "rejection_qc.csv", index=False)

    if epochs is None or len(epochs) == 0:
        raise RuntimeError("No epochs survived preprocessing for the configured subjects")

    metadata = epochs.metadata.copy().reset_index(drop=True)

    # ----------------------------------------------------------- eligibility
    min_epochs = int(config.eligibility.get("min_epochs_per_mode", 30))
    eligibility = evaluate_eligibility(
        metadata,
        audit,
        config.subjects,
        min_epochs_per_mode=min_epochs,
    )
    eligibility.to_csv(dirs["audit"] / "participant_eligibility.csv", index=False)

    eligible_meta = filter_eligible_epochs(metadata, eligibility, audit)
    if eligible_meta.empty:
        raise RuntimeError(
            "No participants met primary eligibility. "
            "Inspect participant_eligibility.csv and consider expanding the toy subject list."
        )

    keep_index = eligible_meta.index.to_numpy()
    epochs_eligible = epochs[keep_index]
    meta = epochs_eligible.metadata.copy().reset_index(drop=True)

    # Save QC summary
    qc_summary = {
        "n_subjects_requested": len(config.subjects),
        "n_subjects_with_epochs": int(metadata["subject"].nunique()),
        "n_subjects_eligible": int(eligibility["eligible_primary"].sum()),
        "n_epochs_total": int(len(metadata)),
        "n_epochs_eligible": int(len(meta)),
        "eligible_subjects": sorted(map(int, meta["subject"].unique())),
        "reject_peak_to_peak_uv": float(config.preprocessing["reject_peak_to_peak_uv"]),
    }
    write_json(dirs["qc"] / "rejection_summary.json", qc_summary)
    rejection_by_condition = (
        rejection_log.groupby("condition", dropna=False)
        .agg(
            events=("n_events", "sum"),
            kept=("n_kept", "sum"),
            mean_rejection=("rejection_rate", "mean"),
        )
        .reset_index()
    )
    rejection_by_condition.to_csv(dirs["qc"] / "rejection_summary_by_condition.csv", index=False)

    # -------------------------------------------------------------- features
    t0 = time.perf_counter()
    X_e01, e01_names = extract_e01_erd_features(epochs_eligible, config.preprocessing)
    X_e00, e00_names = extract_e00_log_bandpower_features(epochs_eligible, config.preprocessing)
    timings["feature_extraction_sec"] = time.perf_counter() - t0
    peak_ram_mb = max(peak_ram_mb, _rss_mb() or 0.0)

    assert X_e01.shape[1] == N_FEATURES == len(e01_names)
    assert X_e00.shape[1] == N_FEATURES == len(e00_names)

    pd.DataFrame({"feature_index": np.arange(len(e01_names)), "feature_name": e01_names}).to_csv(
        dirs["e01"] / "feature_metadata.csv", index=False
    )
    pd.DataFrame({"feature_index": np.arange(len(e00_names)), "feature_name": e00_names}).to_csv(
        dirs["e00"] / "feature_metadata.csv", index=False
    )

    y = meta["label"].to_numpy(dtype=int)
    groups = meta["subject"].to_numpy(dtype=int)

    outer_folds = int(config.cv["outer_folds"])
    inner_folds = int(config.cv["inner_folds"])
    if meta["subject"].nunique() < outer_folds:
        raise RuntimeError(
            f"Only {meta['subject'].nunique()} eligible subjects; need >= {outer_folds} outer folds"
        )

    # Shared outer fold assignments for E00 and E01.
    assignments = fold_assignment_table(groups, outer_folds, config.seed)
    assert_participant_disjoint(assignments)
    assignments.to_csv(dirs["qc"] / "fold_assignments.csv", index=False)

    scoring = str(config.cv.get("scoring", "balanced_accuracy"))
    c_grid = config.logistic_c_grid
    n_boot = int(config.statistics["bootstrap_replicates"])

    # -------------------------------------------------------------------- E01
    t0 = time.perf_counter()
    e01_lr = run_nested_group_cv(
        experiment="E01",
        model_name="erd_lr",
        estimator=make_erd_lr_pipeline(config.seed),
        param_grid=logistic_param_grid(c_grid),
        X=X_e01,
        y=y,
        groups=groups,
        metadata=meta,
        outer_folds=outer_folds,
        inner_folds=inner_folds,
        seed=config.seed,
        scoring=scoring,
    )
    e01_dummy = run_nested_group_cv(
        experiment="E01",
        model_name="dummy",
        estimator=make_dummy_pipeline("prior"),
        param_grid=None,
        X=X_e01,
        y=y,
        groups=groups,
        metadata=meta,
        outer_folds=outer_folds,
        inner_folds=inner_folds,
        seed=config.seed,
        scoring=scoring,
    )
    timings["e01_nested_cv_sec"] = time.perf_counter() - t0
    peak_ram_mb = max(peak_ram_mb, _rss_mb() or 0.0)

    # -------------------------------------------------------------------- E00
    t0 = time.perf_counter()
    e00_lr = run_nested_group_cv(
        experiment="E00",
        model_name="precue_logbp_lr",
        estimator=make_erd_lr_pipeline(config.seed),
        param_grid=logistic_param_grid(c_grid),
        X=X_e00,
        y=y,
        groups=groups,
        metadata=meta,
        outer_folds=outer_folds,
        inner_folds=inner_folds,
        seed=config.seed,
        scoring=scoring,
    )
    e00_dummy = run_nested_group_cv(
        experiment="E00",
        model_name="dummy",
        estimator=make_dummy_pipeline("prior"),
        param_grid=None,
        X=X_e00,
        y=y,
        groups=groups,
        metadata=meta,
        outer_folds=outer_folds,
        inner_folds=inner_folds,
        seed=config.seed,
        scoring=scoring,
    )
    timings["e00_nested_cv_sec"] = time.perf_counter() - t0
    peak_ram_mb = max(peak_ram_mb, _rss_mb() or 0.0)

    # Confirm identical outer fold participant assignments.
    pd.testing.assert_frame_equal(
        e00_lr["fold_assignments"].sort_values(["fold", "role", "subject"]).reset_index(drop=True),
        e01_lr["fold_assignments"].sort_values(["fold", "role", "subject"]).reset_index(drop=True),
    )

    def _export_experiment(folder: Path, primary: dict, dummy: dict) -> dict[str, Any]:
        primary["oof_predictions"].to_csv(folder / "oof_predictions.csv", index=False)
        dummy["oof_predictions"].to_csv(folder / "oof_predictions_dummy.csv", index=False)
        primary["participant_metrics"].to_csv(folder / "participant_metrics.csv", index=False)
        dummy["participant_metrics"].to_csv(folder / "participant_metrics_dummy.csv", index=False)
        primary["fold_metrics"].to_csv(folder / "fold_metrics.csv", index=False)
        primary["tuning"].to_csv(folder / "inner_tuning.csv", index=False)

        t_boot = time.perf_counter()
        boot_summary, boot_draws = bootstrap_participant_means(
            primary["participant_metrics"],
            n_bootstrap=n_boot,
            seed=config.seed,
            metrics=(
                "balanced_accuracy",
                "roc_auc",
                "macro_f1",
                "accuracy",
            ),
        )
        boot_sec = time.perf_counter() - t_boot
        boot_summary.to_csv(folder / "bootstrap_summary.csv", index=False)
        boot_draws.to_csv(folder / "bootstrap_draws.csv", index=False)
        write_json(folder / "summary.json", primary["summary"])
        return {"bootstrap_summary": boot_summary, "bootstrap_sec": boot_sec}

    e01_extra = _export_experiment(dirs["e01"], e01_lr, e01_dummy)
    e00_extra = _export_experiment(dirs["e00"], e00_lr, e00_dummy)
    timings["bootstrap_sec"] = e01_extra["bootstrap_sec"] + e00_extra["bootstrap_sec"]

    comparison, comparison_summary = compare_e00_e01(
        e00_lr["participant_metrics"],
        e01_lr["participant_metrics"],
        metric="balanced_accuracy",
        n_bootstrap=n_boot,
        seed=config.seed,
    )
    comparison.to_csv(dirs["comparisons"] / "e00_vs_e01_participant.csv", index=False)
    comparison_summary.to_csv(dirs["comparisons"] / "e00_vs_e01_bootstrap_summary.csv", index=False)

    timings["total_sec"] = time.perf_counter() - t0_all
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    peak_ram_mb = max(peak_ram_mb, peak / (1024 * 1024), _rss_mb() or 0.0)

    benchmark = {
        "peak_ram_mb_approx": peak_ram_mb,
        "tracemalloc_peak_mb": peak / (1024 * 1024),
        "timings_sec": timings,
        "n_eligible_subjects": int(meta["subject"].nunique()),
        "n_eligible_epochs": int(len(meta)),
        "eligible_subjects": sorted(map(int, meta["subject"].unique())),
    }
    write_json(dirs["qc"] / "resource_benchmark.json", benchmark)

    return {
        "audit": audit,
        "eligibility": eligibility,
        "metadata": meta,
        "e00": e00_lr,
        "e01": e01_lr,
        "comparison": comparison,
        "benchmark": benchmark,
        "output_root": output_root,
    }


def run_from_config_path(
    config_path: str | Path,
    *,
    download: bool = True,
    force_preprocess: bool = False,
) -> dict[str, Any]:
    config = load_config(config_path)
    return run_pipeline(config, download=download, force_preprocess=force_preprocess)
