"""E07 permutation runtime benchmark on the eligible cohort."""

from __future__ import annotations

import time
import tracemalloc
from pathlib import Path

import numpy as np

from eeg_me_mi.audit import audit_subjects
from eeg_me_mi.config import load_config
from eeg_me_mi.cv import run_nested_group_cv
from eeg_me_mi.eligibility import evaluate_eligibility, filter_eligible_epochs
from eeg_me_mi.features import extract_e01_erd_features
from eeg_me_mi.models import logistic_param_grid, make_erd_lr_pipeline
from eeg_me_mi.permutation import matched_pair_label_permutation
from eeg_me_mi.preprocess import build_epoch_dataset
from eeg_me_mi.provenance import write_json


def run_e07_benchmark(
    config_path: str | Path,
    *,
    n_permutations: int = 20,
    download: bool = True,
) -> dict:
    config = load_config(config_path)
    root = config.source.parent.parent
    data_root = config.path("data_root", project_root=root)
    cache_root = config.path("cache_root", project_root=root)
    out = root / "results" / "benchmarks"
    out.mkdir(parents=True, exist_ok=True)

    audit = audit_subjects(config.subjects, config.runs, data_root, download=download)
    epochs, _ = build_epoch_dataset(
        config.subjects,
        config.runs,
        data_root,
        cache_root,
        config.preprocessing,
        download=download,
        mode="minimal",
        threshold_uv=float(config.preprocessing["reject_peak_to_peak_uv"]),
    )
    if epochs is None:
        raise RuntimeError("No epochs for E07 benchmark")
    metadata = epochs.metadata.reset_index(drop=True)
    elig = evaluate_eligibility(metadata, audit, config.subjects)
    primary = filter_eligible_epochs(metadata, elig, audit)
    if primary["subject"].nunique() < int(config.cv["outer_folds"]):
        raise RuntimeError("Insufficient eligible subjects for benchmark")

    epochs_p = epochs[primary.index.to_numpy()]
    meta = epochs_p.metadata.reset_index(drop=True)
    X, _ = extract_e01_erd_features(epochs_p, config.preprocessing)
    y = meta["label"].to_numpy(dtype=int)
    groups = meta["subject"].to_numpy(dtype=int)

    outer = int(config.cv["outer_folds"])
    inner = int(config.cv["inner_folds"])
    # For full-cohort benchmark with many subjects, keep nested CV but scoring only.
    # Use config folds; if subjects from full config, this is the real cost.

    tracemalloc.start()
    t0 = time.perf_counter()
    null = []
    for i in range(n_permutations):
        y_perm = matched_pair_label_permutation(meta, y, seed=config.seed, perm_id=i)
        res = run_nested_group_cv(
            experiment=f"E07_bench_{i}",
            model_name="erd_lr",
            estimator=make_erd_lr_pipeline(config.seed),
            param_grid=logistic_param_grid(config.logistic_c_grid),
            X=X,
            y=y_perm,
            groups=groups,
            metadata=meta,
            outer_folds=min(outer, int(meta["subject"].nunique())),
            inner_folds=min(inner, max(2, int(meta["subject"].nunique()) - 1)),
            seed=config.seed,
            scoring=str(config.cv.get("scoring", "balanced_accuracy")),
        )
        null.append(float(res["summary"]["balanced_accuracy"]))
        print(f"[e07-bench] perm {i+1}/{n_permutations} bacc={null[-1]:.4f}", flush=True)
    elapsed = time.perf_counter() - t0
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    per_perm = elapsed / max(n_permutations, 1)
    payload = {
        "n_permutations": n_permutations,
        "n_eligible_subjects": int(meta["subject"].nunique()),
        "n_epochs": int(len(meta)),
        "wall_time_sec": elapsed,
        "sec_per_permutation": per_perm,
        "extrapolated_1000_sec": per_perm * 1000,
        "extrapolated_1000_hours": (per_perm * 1000) / 3600,
        "tracemalloc_peak_mb": peak / (1024 * 1024),
        "null_balanced_accuracy_mean": float(np.mean(null)),
        "null_balanced_accuracy": null,
        "recommendation": (
            "TRUBA"
            if (per_perm * 1000) > 4 * 3600
            else "LOCAL_OR_TRUBA"
        ),
        "recommendation_reason": (
            "Prefer TRUBA when extrapolated 1000-permutation wall time exceeds ~4 hours "
            "or would materially occupy the local workstation; local remains default otherwise."
        ),
    }
    write_json(out / "e07_20perm_benchmark.json", payload)
    return payload
