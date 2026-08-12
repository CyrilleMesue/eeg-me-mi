"""Definitive E07 structured permutation inference engine.

Distinct from ``benchmark_e07`` (timing only). Implements:

* observed statistic = definitive E01 participant-mean balanced accuracy;
* structured matched-pair label swaps;
* nested hyperparameter retuning under each permutation;
* plus-one one-sided p-value;
* atomic checkpoint / resume.
"""

from __future__ import annotations

import json
import os
import tempfile
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from eeg_me_mi.cv import PARTICIPANT_MEAN_SCORING, run_nested_group_cv
from eeg_me_mi.models import logistic_param_grid, make_erd_lr_pipeline
from eeg_me_mi.permutation import (
    E07_INTERPRETATION,
    assert_permutation_preserves_structure,
    matched_pair_label_permutation,
    plus_one_pvalue,
)
from eeg_me_mi.provenance import write_json


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, default=str)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp_name, path)
    except Exception:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def _read_checkpoint(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Corrupted E07 checkpoint JSON: {path}") from exc
    required = {"perm_id", "statistic", "seed", "status", "swap_map"}
    if not required <= set(payload):
        raise RuntimeError(f"Incomplete E07 checkpoint record: {path}")
    if payload.get("status") != "complete":
        raise RuntimeError(f"Incomplete E07 checkpoint status in {path}")
    if not np.isfinite(float(payload["statistic"])):
        raise RuntimeError(f"Non-finite statistic in checkpoint {path}")
    return payload


def checkpoint_path(checkpoint_dir: Path, perm_id: int) -> Path:
    return checkpoint_dir / f"perm_{int(perm_id):04d}.json"


def list_completed_permutations(checkpoint_dir: Path) -> dict[int, dict[str, Any]]:
    completed: dict[int, dict[str, Any]] = {}
    if not checkpoint_dir.exists():
        return completed
    for path in sorted(checkpoint_dir.glob("perm_*.json")):
        payload = _read_checkpoint(path)
        if payload is None:
            continue
        pid = int(payload["perm_id"])
        if pid in completed:
            raise RuntimeError(f"Duplicate permutation checkpoint for id={pid}")
        completed[pid] = payload
    return completed


def run_e07_inference(
    *,
    X: np.ndarray,
    y: np.ndarray,
    groups: np.ndarray,
    metadata: pd.DataFrame,
    observed_statistic: float | None = None,
    n_permutations: int,
    seed: int,
    outer_folds: int,
    inner_folds: int,
    c_grid: tuple[float, ...] | list[float],
    output_dir: Path,
    checkpoint_dir: Path | None = None,
    resume: bool = True,
    scoring: str = PARTICIPANT_MEAN_SCORING,
) -> dict[str, Any]:
    """Run definitive E07 with atomic checkpoints.

    If ``observed_statistic`` is None, compute it with the identical ERD-LR
    nested CV pipeline used for each permutation (unpermuted labels).
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_dir = Path(checkpoint_dir) if checkpoint_dir else output_dir / "checkpoints"
    checkpoint_dir.mkdir(parents=True, exist_ok=True)

    meta = metadata.reset_index(drop=True)
    y = np.asarray(y).astype(int)
    groups = np.asarray(groups).astype(int)
    X = np.asarray(X)

    write_json(output_dir / "e07_interpretation.json", E07_INTERPRETATION)

    # Observed statistic
    if observed_statistic is None:
        obs_res = run_nested_group_cv(
            experiment="E07_observed",
            model_name="erd_lr",
            estimator=make_erd_lr_pipeline(seed),
            param_grid=logistic_param_grid(c_grid),
            X=X,
            y=y,
            groups=groups,
            metadata=meta,
            outer_folds=outer_folds,
            inner_folds=inner_folds,
            seed=seed,
            scoring=scoring,
        )
        observed_statistic = float(obs_res["summary"]["balanced_accuracy"])
        write_json(output_dir / "observed_summary.json", obs_res["summary"])
    else:
        observed_statistic = float(observed_statistic)

    completed = list_completed_permutations(checkpoint_dir) if resume else {}
    # Detect duplicates / refuse reuse of unexpected IDs outside requested range
    for pid in completed:
        if pid < 0 or pid >= int(n_permutations):
            raise RuntimeError(
                f"Checkpoint perm_id={pid} outside requested range [0, {n_permutations})"
            )

    null_rows: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    t0 = time.perf_counter()

    for perm_id in range(int(n_permutations)):
        if perm_id in completed:
            row = completed[perm_id]
            null_rows.append(
                {
                    "perm_id": perm_id,
                    "statistic": float(row["statistic"]),
                    "seed": int(row["seed"]),
                    "status": "complete",
                    "resumed": True,
                    "swap_map": row["swap_map"],
                }
            )
            continue

        try:
            y_perm, swap_map = matched_pair_label_permutation(
                meta, y, seed=seed, perm_id=perm_id
            )
            assert_permutation_preserves_structure(meta, y, y_perm)
            # Deterministic seed identity for this draw
            draw_seed = int(seed) + 10007 * int(perm_id)
            res = run_nested_group_cv(
                experiment=f"E07_perm_{perm_id}",
                model_name="erd_lr",
                estimator=make_erd_lr_pipeline(seed),
                param_grid=logistic_param_grid(c_grid),
                X=X,
                y=y_perm,
                groups=groups,
                metadata=meta,
                outer_folds=outer_folds,
                inner_folds=inner_folds,
                seed=seed,
                scoring=scoring,
            )
            statistic = float(res["summary"]["balanced_accuracy"])
            payload = {
                "perm_id": int(perm_id),
                "statistic": statistic,
                "seed": draw_seed,
                "config_seed": int(seed),
                "status": "complete",
                "swap_map": {f"{s}:{p}": bool(v) for (s, p), v in swap_map.items()},
                "n_swapped_pairs": int(sum(1 for v in swap_map.values() if v)),
                "n_pairs_considered": int(len(swap_map)),
            }
            _atomic_write_json(checkpoint_path(checkpoint_dir, perm_id), payload)
            null_rows.append(
                {
                    "perm_id": perm_id,
                    "statistic": statistic,
                    "seed": draw_seed,
                    "status": "complete",
                    "resumed": False,
                    "swap_map": payload["swap_map"],
                }
            )
        except Exception as exc:  # noqa: BLE001
            failures.append({"perm_id": int(perm_id), "error": repr(exc)})
            _atomic_write_json(
                checkpoint_dir / f"perm_{perm_id:04d}.FAILED.json",
                {"perm_id": perm_id, "status": "failed", "error": repr(exc)},
            )

    null_df = pd.DataFrame(null_rows).sort_values("perm_id").reset_index(drop=True)
    null_df.to_csv(output_dir / "null_statistics.csv", index=False)

    n_valid = int((null_df["status"] == "complete").sum()) if len(null_df) else 0
    if n_valid != int(n_permutations) or failures:
        manifest = {
            "complete": False,
            "n_requested": int(n_permutations),
            "n_valid": n_valid,
            "n_failures": len(failures),
            "failures": failures,
            "observed_statistic": observed_statistic,
            "interpretation": E07_INTERPRETATION,
        }
        write_json(output_dir / "completion_manifest.json", manifest)
        raise RuntimeError(
            f"E07 incomplete: {n_valid}/{n_permutations} valid permutations; "
            f"failures={len(failures)}"
        )

    stats = null_df["statistic"].to_numpy(dtype=float)
    pinfo = plus_one_pvalue(observed_statistic, stats, alternative="greater")
    elapsed = time.perf_counter() - t0
    summary = {
        "observed_statistic": observed_statistic,
        "statistic_name": "participant_mean_balanced_accuracy",
        "n_permutations": n_valid,
        "n_null_ge_observed": pinfo["n_null_ge_observed"],
        "p_value_plusone": pinfo["p_value_plusone"],
        "denominator": pinfo["denominator"],
        "alternative": "greater",
        "seed": int(seed),
        "elapsed_sec": float(elapsed),
        "interpretation": E07_INTERPRETATION,
    }
    write_json(output_dir / "e07_summary.json", summary)
    write_json(
        output_dir / "completion_manifest.json",
        {
            "complete": True,
            "n_requested": int(n_permutations),
            "n_valid": n_valid,
            "n_failures": 0,
            "failures": [],
            "observed_statistic": observed_statistic,
            "p_value_plusone": pinfo["p_value_plusone"],
            "interpretation": E07_INTERPRETATION,
        },
    )
    return {
        "summary": summary,
        "null_statistics": null_df,
        "output_dir": output_dir,
        "checkpoint_dir": checkpoint_dir,
    }
