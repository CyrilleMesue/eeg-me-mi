#!/usr/bin/env python3
"""Final two sensitivity / audit checks before manuscript freeze.

1) Sampling-rate sensitivity: exclude S088/S092/S100 from frozen E01 folds.
2) Label-specific ME vs MI rejection audit under frozen 200 µV.

Does NOT overwrite results/definitive/ or results/postdefinitive_e05/.
Does NOT rerun E07 or modify primary E01 outputs.
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
from eeg_me_mi.cv import (
    PARTICIPANT_MEAN_SCORING,
    assert_participant_disjoint,
    filter_fold_assignments,
    run_nested_group_cv,
)
from eeg_me_mi.eligibility import evaluate_eligibility, filter_eligible_epochs
from eeg_me_mi.features import extract_e01_erd_features
from eeg_me_mi.filter_support import e00_window_from_preproc, e01_windows_from_preproc
from eeg_me_mi.metrics import bootstrap_participant_means
from eeg_me_mi.models import logistic_param_grid, make_erd_lr_pipeline
from eeg_me_mi.preprocess import build_epoch_dataset
from eeg_me_mi.provenance import git_commit, git_dirty, git_tag, software_versions, write_json
from eeg_me_mi.protocol import SENSORIMOTOR_CHANNELS

EXCLUDED_128HZ = frozenset({88, 92, 100})
PRIMARY_BACC = 0.6179239767
PRIMARY_N = 102
PRIMARY_CI = (0.6035525544008872, 0.632899080752947)


def _first_existing(*paths: Path) -> Path:
    for p in paths:
        if p.exists():
            return p
    raise FileNotFoundError("None of these paths exist: " + ", ".join(map(str, paths)))


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _export_cv(folder: Path, result: dict, n_boot: int, seed: int) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    result["oof_predictions"].to_csv(folder / "oof_predictions.csv", index=False)
    result["participant_metrics"].to_csv(folder / "participant_metrics.csv", index=False)
    result["fold_metrics"].to_csv(folder / "fold_metrics.csv", index=False)
    result["tuning"].to_csv(folder / "inner_tuning.csv", index=False)
    result["fold_assignments"].to_csv(folder / "fold_assignments.csv", index=False)
    boot, _ = bootstrap_participant_means(
        result["participant_metrics"],
        n_bootstrap=n_boot,
        seed=seed,
        metrics=("balanced_accuracy",),
    )
    boot.to_csv(folder / "bootstrap_summary.csv", index=False)
    write_json(folder / "summary.json", result["summary"])


def load_primary_e01_epochs(config, project_root: Path, audit: pd.DataFrame):
    data_root = config.path("data_root", project_root=project_root)
    cache_root = config.path("cache_root", project_root=project_root)
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
        channels=SENSORIMOTOR_CHANNELS,
    )
    if ep is None:
        raise RuntimeError("Failed to load primary 200µV epochs")
    md = ep.metadata.reset_index(drop=True)
    el = evaluate_eligibility(md, audit, config.subjects)
    pm = filter_eligible_epochs(md, el, audit, eligible_col="eligible_primary")
    if pm["subject"].nunique() != PRIMARY_N:
        raise RuntimeError(
            f"STOP: primary eligible N={pm['subject'].nunique()} != {PRIMARY_N}"
        )
    ep2 = ep[pm.index.to_numpy()]
    m2 = ep2.metadata.reset_index(drop=True)
    return ep2, m2, el


def run_sampling_rate_sensitivity(
    *,
    config,
    project_root: Path,
    audit: pd.DataFrame,
    out_root: Path,
    frozen_fold_path: Path,
) -> dict[str, Any]:
    t0 = time.perf_counter()
    dest = out_root / "sampling_rate"
    dest.mkdir(parents=True, exist_ok=True)

    frozen = pd.read_csv(frozen_fold_path)
    assert_participant_disjoint(frozen)
    excluded_present = sorted(EXCLUDED_128HZ & set(frozen["subject"].astype(int)))
    if set(excluded_present) != set(EXCLUDED_128HZ):
        raise RuntimeError(
            f"STOP: expected all of {sorted(EXCLUDED_128HZ)} in frozen folds; "
            f"present={excluded_present}"
        )

    filtered = filter_fold_assignments(frozen, exclude_subjects=EXCLUDED_128HZ)
    filtered.to_csv(dest / "fold_assignments.csv", index=False)

    # Document fold changes
    changes = []
    for fold in sorted(frozen["fold"].unique()):
        before_test = set(
            frozen.loc[(frozen.fold == fold) & (frozen.role == "test"), "subject"].astype(int)
        )
        after_test = set(
            filtered.loc[(filtered.fold == fold) & (filtered.role == "test"), "subject"].astype(int)
        )
        removed = sorted(before_test - after_test)
        changes.append(
            {
                "fold": int(fold),
                "n_test_before": len(before_test),
                "n_test_after": len(after_test),
                "removed_from_test": "|".join(map(str, removed)),
                "remaining_test_unchanged": before_test - EXCLUDED_128HZ == after_test,
            }
        )
    pd.DataFrame(changes).to_csv(dest / "fold_changes.csv", index=False)

    ep2, m2, el = load_primary_e01_epochs(config, project_root, audit)
    keep = ~m2["subject"].astype(int).isin(EXCLUDED_128HZ)
    m3 = m2.loc[keep].reset_index(drop=True)
    ep3 = ep2[np.flatnonzero(keep.to_numpy())]
    if m3["subject"].nunique() != PRIMARY_N - len(EXCLUDED_128HZ):
        raise RuntimeError(
            f"STOP: sensitivity N={m3['subject'].nunique()} "
            f"!= {PRIMARY_N - len(EXCLUDED_128HZ)}"
        )

    # Verify remaining subjects keep frozen fold membership
    for fold in sorted(filtered["fold"].unique()):
        test_subs = set(
            filtered.loc[(filtered.fold == fold) & (filtered.role == "test"), "subject"]
        )
        frozen_test = set(
            frozen.loc[(frozen.fold == fold) & (frozen.role == "test"), "subject"].astype(int)
        ) - EXCLUDED_128HZ
        if test_subs != frozen_test:
            raise RuntimeError(f"STOP: fold {fold} membership changed beyond exclusions")

    X, names = extract_e01_erd_features(ep3, config.preprocessing)
    assert X.shape[1] == 42

    outer = int(config.cv["outer_folds"])
    inner = int(config.cv["inner_folds"])
    n_boot = int(config.statistics["bootstrap_replicates"])
    res = run_nested_group_cv(
        experiment="E01_sampling_rate_sensitivity",
        model_name="erd_lr",
        estimator=make_erd_lr_pipeline(config.seed),
        param_grid=logistic_param_grid(config.logistic_c_grid),
        X=X,
        y=m3["label"].to_numpy(dtype=int),
        groups=m3["subject"].to_numpy(dtype=int),
        metadata=m3,
        outer_folds=outer,
        inner_folds=inner,
        seed=config.seed,
        scoring=PARTICIPANT_MEAN_SCORING,
        fold_assignments=filtered,
    )
    # Ensure exported assignments are the filtered frozen ones
    res["fold_assignments"] = filtered
    _export_cv(dest, res, n_boot, config.seed)
    pd.DataFrame({"feature_name": names}).to_csv(dest / "feature_metadata.csv", index=False)

    subjects = sorted(map(int, m3["subject"].unique()))
    pd.DataFrame({"subject": subjects}).to_csv(dest / "participant_list.csv", index=False)
    pd.DataFrame(
        {
            "excluded_subject": sorted(EXCLUDED_128HZ),
            "reason": "EEGMMIDB native 128 Hz recording",
        }
    ).to_csv(dest / "excluded_participants.csv", index=False)

    boot = pd.read_csv(dest / "bootstrap_summary.csv")
    row = boot.iloc[0]
    sens_bacc = float(res["summary"]["balanced_accuracy"])
    abs_diff = abs(sens_bacc - PRIMARY_BACC)
    # Qualitative rule: material if |Δ| >= 0.02 (2 percentage points) — descriptive only
    conclusion = "STABLE" if abs_diff < 0.02 else "MATERIALLY DIFFERENT"

    summary = {
        "primary_n": PRIMARY_N,
        "sensitivity_n": int(m3["subject"].nunique()),
        "excluded_subjects": sorted(EXCLUDED_128HZ),
        "primary_bacc": PRIMARY_BACC,
        "sensitivity_bacc": sens_bacc,
        "primary_ci": list(PRIMARY_CI),
        "sensitivity_ci": [float(row["ci_low"]), float(row["ci_high"])],
        "absolute_bacc_difference": abs_diff,
        "roc_auc": float(res["summary"].get("roc_auc", np.nan)),
        "macro_f1": float(res["summary"].get("macro_f1", np.nan)),
        "mcc": float(res["summary"].get("mcc", np.nan)),
        "accuracy": float(res["summary"].get("accuracy", np.nan)),
        "conclusion": conclusion,
        "fold_handling": "frozen_outer_folds_minus_excluded_subjects",
        "elapsed_sec": time.perf_counter() - t0,
    }
    write_json(dest / "sampling_rate_sensitivity_summary.json", summary)

    # Optional paired description vs primary participant metrics
    primary_pm = _first_existing(
        Path("results/definitive/full/e01/erd_lr/participant_metrics.csv"),
        Path("results/full/e01/erd_lr/participant_metrics.csv"),
    )
    a = pd.read_csv(primary_pm).rename(columns={"balanced_accuracy": "bacc_primary"})
    b = res["participant_metrics"].rename(columns={"balanced_accuracy": "bacc_sens"})
    merged = a[["subject", "bacc_primary"]].merge(
        b[["subject", "bacc_sens"]], on="subject", how="inner"
    )
    merged["difference_sens_minus_primary"] = merged["bacc_sens"] - merged["bacc_primary"]
    merged.to_csv(dest / "paired_participant_differences.csv", index=False)
    diffs = merged["difference_sens_minus_primary"].to_numpy(dtype=float)
    rng = np.random.default_rng(config.seed)
    boots = [
        float(np.mean(diffs[rng.integers(0, len(diffs), size=len(diffs))]))
        for _ in range(n_boot)
    ]
    paired = {
        "common_n": int(len(diffs)),
        "mean_difference_sens_minus_primary": float(np.mean(diffs)),
        "bootstrap_ci_low": float(np.quantile(boots, 0.025)),
        "bootstrap_ci_high": float(np.quantile(boots, 0.975)),
        "note": (
            "Descriptive only. Outer-fold test membership for common subjects is "
            "preserved; outer-train composition changes where excluded subjects "
            "were removed, so inner tuning / fitted models may differ."
        ),
        "formal_p_prespecified": False,
    }
    write_json(dest / "paired_effect_summary.json", paired)

    write_json(
        dest / "provenance.json",
        {
            "parent_tag": git_tag(project_root),
            "parent_commit": git_commit(project_root),
            "git_dirty": git_dirty(project_root),
            "software_versions": software_versions(),
            "seed": config.seed,
            "windows": e01_windows_from_preproc(config.preprocessing),
            "e00_window": e00_window_from_preproc(config.preprocessing),
            "channels": list(SENSORIMOTOR_CHANNELS),
            "threshold_uv": 200.0,
            "frozen_fold_source": str(frozen_fold_path),
        },
    )
    el.to_csv(dest / "participant_eligibility_snapshot.csv", index=False)
    return summary


def _rej_props(frame: pd.DataFrame) -> dict[str, Any]:
    n_before = int(len(frame))
    n_rej = int(frame["rejected"].sum()) if n_before else 0
    n_ret = n_before - n_rej
    return {
        "epochs_before": n_before,
        "epochs_rejected": n_rej,
        "epochs_retained": n_ret,
        "rejection_proportion": (n_rej / n_before) if n_before else np.nan,
    }


def run_rejection_audit(
    *,
    config,
    project_root: Path,
    audit: pd.DataFrame,
    out_root: Path,
) -> dict[str, Any]:
    dest = out_root / "rejection_audit"
    dest.mkdir(parents=True, exist_ok=True)

    data_root = config.path("data_root", project_root=project_root)
    cache_root = config.path("cache_root", project_root=project_root)
    # True no-rejection base (explicit None / 0.0)
    ep, _ = build_epoch_dataset(
        config.subjects,
        config.runs,
        data_root,
        cache_root,
        config.preprocessing,
        download=False,
        force=False,
        mode="minimal",
        threshold_uv=0.0,
        channels=SENSORIMOTOR_CHANNELS,
    )
    if ep is None:
        raise RuntimeError("Failed to load minimal no-rejection epochs for audit")
    md = ep.metadata.reset_index(drop=True).copy()
    md["rejected"] = md["ptp_uv"].to_numpy(dtype=float) > 200.0
    md["condition_me_mi"] = np.where(md["label"].astype(int) == 1, "ME", "MI")

    el_path = _first_existing(
        project_root / "results/definitive/full/qc/participant_eligibility.csv",
        project_root / "results/full/qc/participant_eligibility.csv",
    )
    el_def = pd.read_csv(el_path)
    primary_subjects = set(el_def.loc[el_def["eligible_primary"], "subject"].astype(int))
    if len(primary_subjects) != PRIMARY_N:
        raise RuntimeError(
            f"STOP: rejection-audit primary eligible N={len(primary_subjects)} != {PRIMARY_N}"
        )

    md["in_e01_primary_cohort"] = md["subject"].astype(int).isin(primary_subjects)

    scopes = {
        "full_attempted": md,
        "e01_primary_cohort": md.loc[md["in_e01_primary_cohort"]].copy(),
    }

    condition_rows = []
    for scope, frame in scopes.items():
        for cond in ("ME", "MI"):
            sub = frame.loc[frame["condition_me_mi"] == cond]
            row = {"scope": scope, "condition": cond, **_rej_props(sub)}
            condition_rows.append(row)
    by_cond = pd.DataFrame(condition_rows)
    by_cond.to_csv(dest / "rejection_by_condition.csv", index=False)

    # Participant × condition
    part_rows = []
    for (subj, cond), g in md.groupby(["subject", "condition_me_mi"]):
        part_rows.append(
            {
                "subject": int(subj),
                "condition": cond,
                "in_e01_primary_cohort": bool(int(subj) in primary_subjects),
                **_rej_props(g),
            }
        )
    by_part = pd.DataFrame(part_rows)
    by_part.to_csv(dest / "rejection_by_participant_condition.csv", index=False)

    # Run
    run_rows = []
    for (run, cond), g in md.groupby(["run", "condition_me_mi"]):
        run_rows.append({"run": int(run), "condition": cond, **_rej_props(g)})
    pd.DataFrame(run_rows).to_csv(dest / "rejection_by_run.csv", index=False)

    # Movement × condition
    mov_rows = []
    for (mov, cond), g in md.groupby(["movement", "condition_me_mi"]):
        mov_rows.append({"movement": mov, "condition": cond, **_rej_props(g)})
    by_mov = pd.DataFrame(mov_rows)
    by_mov.to_csv(dest / "rejection_by_movement.csv", index=False)

    # Matched pair
    pair_rows = []
    if "pair_id" in md.columns:
        for (pair, cond), g in md.groupby(["pair_id", "condition_me_mi"]):
            pair_rows.append({"pair_id": pair, "condition": cond, **_rej_props(g)})
        pd.DataFrame(pair_rows).to_csv(dest / "rejection_by_matched_pair.csv", index=False)

    # Unilateral / bilateral if inferable from movement
    md["laterality"] = np.where(
        md["movement"].isin(["left_fist", "right_fist"]),
        "unilateral",
        np.where(md["movement"].isin(["both_fists", "both_feet"]), "bilateral", "other"),
    )
    lat_rows = []
    for (lat, cond), g in md.groupby(["laterality", "condition_me_mi"]):
        lat_rows.append({"laterality": lat, "condition": cond, **_rej_props(g)})
    pd.DataFrame(lat_rows).to_csv(dest / "rejection_by_laterality.csv", index=False)

    # Summary ME vs MI for primary cohort
    prim = scopes["e01_primary_cohort"]
    me = _rej_props(prim.loc[prim["condition_me_mi"] == "ME"])
    mi = _rej_props(prim.loc[prim["condition_me_mi"] == "MI"])
    abs_diff = float(me["rejection_proportion"] - mi["rejection_proportion"])

    # Participant-paired rejection differences (primary cohort)
    piv = by_part.loc[by_part["in_e01_primary_cohort"]].pivot(
        index="subject", columns="condition", values="rejection_proportion"
    )
    piv = piv.dropna(subset=["ME", "MI"])
    paired_diff = (piv["ME"] - piv["MI"]).to_numpy(dtype=float)
    rng = np.random.default_rng(config.seed)
    n_boot = int(config.statistics["bootstrap_replicates"])
    boots = [
        float(np.mean(paired_diff[rng.integers(0, len(paired_diff), size=len(paired_diff))]))
        for _ in range(n_boot)
    ]
    q = np.quantile(paired_diff, [0.25, 0.75])
    paired_summary = {
        "n_participants": int(len(paired_diff)),
        "mean_me_minus_mi": float(np.mean(paired_diff)),
        "median_me_minus_mi": float(np.median(paired_diff)),
        "iqr_low": float(q[0]),
        "iqr_high": float(q[1]),
        "range_min": float(np.min(paired_diff)),
        "range_max": float(np.max(paired_diff)),
        "bootstrap_ci_low": float(np.quantile(boots, 0.025)),
        "bootstrap_ci_high": float(np.quantile(boots, 0.975)),
        "formal_p_prespecified": False,
    }
    write_json(dest / "participant_paired_rejection_difference.json", paired_summary)
    pd.DataFrame(
        {"subject": piv.index.astype(int), "me_minus_mi_rejection_proportion": paired_diff}
    ).to_csv(dest / "participant_paired_rejection_differences.csv", index=False)

    # Class balance after rejection (primary cohort retained)
    retained = prim.loc[~prim["rejected"]]
    n_me = int((retained["condition_me_mi"] == "ME").sum())
    n_mi = int((retained["condition_me_mi"] == "MI").sum())
    bal = {
        "retained_me": n_me,
        "retained_mi": n_mi,
        "me_mi_ratio": (n_me / n_mi) if n_mi else np.nan,
    }
    # participant-level retained counts
    ret_part = (
        retained.groupby(["subject", "condition_me_mi"])
        .size()
        .unstack(fill_value=0)
        .reset_index()
    )
    ret_part.to_csv(dest / "retained_class_balance_by_participant.csv", index=False)
    write_json(dest / "retained_class_balance.json", bal)

    # Movement-specific ME/MI table (requested list)
    mov_focus = []
    for mov in ("left_fist", "right_fist", "both_fists", "both_feet"):
        for cond in ("ME", "MI"):
            g = prim.loc[(prim["movement"] == mov) & (prim["condition_me_mi"] == cond)]
            mov_focus.append({"movement": mov, "condition": cond, **_rej_props(g)})
    pd.DataFrame(mov_focus).to_csv(dest / "rejection_by_movement_primary_cohort.csv", index=False)

    summary = {
        "primary_cohort": {
            "ME": me,
            "MI": mi,
            "absolute_difference_me_minus_mi": abs_diff,
        },
        "full_attempted": {
            "ME": _rej_props(scopes["full_attempted"].loc[scopes["full_attempted"]["condition_me_mi"] == "ME"]),
            "MI": _rej_props(scopes["full_attempted"].loc[scopes["full_attempted"]["condition_me_mi"] == "MI"]),
        },
        "participant_paired": paired_summary,
        "retained_class_balance": bal,
        "n_ptp_gt_200_full": int(md["rejected"].sum()),
        "n_epochs_before_full": int(len(md)),
    }
    write_json(dest / "rejection_audit_summary.json", summary)
    return summary, md, primary_subjects


def reconcile_qc(
    *,
    project_root: Path,
    out_root: Path,
    audit_md: pd.DataFrame,
    primary_subjects: set[int],
    rej_summary: dict[str, Any],
) -> dict[str, Any]:
    dest = out_root / "reconciliation"
    dest.mkdir(parents=True, exist_ok=True)

    issues: list[dict[str, Any]] = []
    el_path = _first_existing(
        project_root / "results/definitive/full/qc/participant_eligibility.csv",
        project_root / "results/full/qc/participant_eligibility.csv",
    )
    e05_path = project_root / "results/postdefinitive_e05/threshold_reconciliation.csv"
    rej_qc_path = _first_existing(
        project_root / "results/definitive/full/qc/rejection_qc.csv",
        project_root / "results/full/qc/rejection_qc.csv",
    )

    el = pd.read_csv(el_path)
    e01_n = int(el["eligible_primary"].sum())
    if e01_n != PRIMARY_N:
        issues.append(
            {
                "check": "eligibility_n",
                "file": str(el_path),
                "expected": PRIMARY_N,
                "observed": e01_n,
            }
        )
    if len(primary_subjects) != PRIMARY_N:
        issues.append(
            {
                "check": "audit_primary_subjects",
                "expected": PRIMARY_N,
                "observed": len(primary_subjects),
            }
        )
    el_subs = set(el.loc[el["eligible_primary"], "subject"].astype(int))
    if el_subs != primary_subjects:
        issues.append(
            {
                "check": "primary_subject_set_mismatch",
                "only_in_eligibility": sorted(el_subs - primary_subjects),
                "only_in_audit": sorted(primary_subjects - el_subs),
            }
        )

    # E05 threshold reconciliation: 200uv retained / before
    if e05_path.exists():
        e05 = pd.read_csv(e05_path)
        row200 = e05.loc[e05["threshold"] == "200uv"].iloc[0]
        expected_before = int(row200["epochs_before"])
        expected_rej = int(row200["epochs_rejected"])
        expected_ret = int(row200["epochs_retained"])
        obs_before = int(rej_summary["n_epochs_before_full"])
        obs_rej = int(rej_summary["n_ptp_gt_200_full"])
        obs_ret = obs_before - obs_rej
        for name, exp, obs in (
            ("epochs_before", expected_before, obs_before),
            ("epochs_rejected_200", expected_rej, obs_rej),
            ("epochs_retained_200", expected_ret, obs_ret),
        ):
            if exp != obs:
                issues.append(
                    {
                        "check": name,
                        "file": str(e05_path),
                        "expected": exp,
                        "observed": obs,
                        "delta": obs - exp,
                    }
                )

    # rejection_qc.csv under mode=minimal records n_rejected=0 by design — document, not failure
    notes = []
    if rej_qc_path.exists():
        rqc = pd.read_csv(rej_qc_path)
        if "n_rejected" in rqc.columns and int(rqc["n_rejected"].sum()) == 0:
            notes.append(
                "definitive rejection_qc.csv has n_rejected=0 because mode=minimal "
                "defers PTP filtering; label-specific audit uses metadata ptp_uv instead."
            )

    # Retained E01 epoch count vs OOF
    oof_path = _first_existing(
        project_root / "results/definitive/full/e01/erd_lr/oof_predictions.csv",
        project_root / "results/full/e01/erd_lr/oof_predictions.csv",
    )
    oof_n = len(pd.read_csv(oof_path))
    retained_primary = int(
        (~audit_md["rejected"] & audit_md["subject"].astype(int).isin(primary_subjects)).sum()
    )
    # OOF may equal retained after eligibility filter; eligibility may drop epochs within subjects
    # Compare to postdefinitive 200uv cohort epochs if available
    e05_200 = project_root / "results/postdefinitive_e05/artifact_sensitivity/200uv/cohort.json"
    if e05_200.exists():
        c200 = json.loads(e05_200.read_text())
        if int(c200["n_epochs"]) != oof_n:
            issues.append(
                {
                    "check": "e05_200uv_vs_e01_oof",
                    "e05_n_epochs": int(c200["n_epochs"]),
                    "e01_oof": oof_n,
                }
            )

    payload = {
        "issues": issues,
        "notes": notes,
        "primary_n_eligibility": e01_n,
        "primary_n_audit": len(primary_subjects),
        "e01_oof_epochs": oof_n,
        "audit_retained_epochs_primary_subjects_before_eligibility_filter": retained_primary,
        "reconcile_ok": len(issues) == 0,
    }
    write_json(dest / "reconciliation.json", payload)
    pd.DataFrame(issues if issues else [{"check": "none", "status": "ok"}]).to_csv(
        dest / "reconciliation_issues.csv", index=False
    )
    if issues:
        raise RuntimeError(f"STOP: QC reconciliation failed: {json.dumps(issues, indent=2)}")
    return payload


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--config", default="configs/full.yaml")
    p.add_argument("--out-root", default="results/final_sensitivity_checks")
    p.add_argument(
        "--frozen-folds",
        default="results/definitive/full/e01/erd_lr/fold_assignments.csv",
    )
    p.add_argument("--skip-sampling-rate", action="store_true")
    p.add_argument("--skip-rejection-audit", action="store_true")
    args = p.parse_args()

    config = load_config(args.config)
    project_root = config.source.parent.parent
    out_root = Path(args.out_root)
    out_root.mkdir(parents=True, exist_ok=True)

    # Window freeze assertions
    e00 = e00_window_from_preproc(config.preprocessing)
    e01w = e01_windows_from_preproc(config.preprocessing)
    assert e00 == (-2.0, -0.8375), e00
    assert e01w["baseline_tmin"] == -2.0 and e01w["baseline_tmax"] == -0.8375
    assert e01w["task_tmin"] == 0.8375 and e01w["task_tmax"] == 3.5

    # Immutability: primary result trees must already exist and not be written by this script
    definitive_or_full = _first_existing(
        project_root / "results/definitive/full/e01/erd_lr/summary.json",
        project_root / "results/full/e01/erd_lr/summary.json",
    )

    cfg_path = Path(args.config)
    provenance = {
        "parent_git_commit": git_commit(project_root),
        "parent_git_tag": git_tag(project_root),
        "git_dirty": git_dirty(project_root),
        "config_path": str(cfg_path),
        "config_sha256": _sha256_file(cfg_path.resolve()) if cfg_path.exists() else None,
        "software_versions": software_versions(),
        "random_seed": config.seed,
        "frozen_e01": {
            "n": PRIMARY_N,
            "bacc": PRIMARY_BACC,
            "bootstrap_ci": list(PRIMARY_CI),
            "fold_source": args.frozen_folds,
            "fold_logic": (
                "KFold on unique participants with shuffle=True, random_state=seed; "
                "sensitivity uses frozen assignments with S088/S092/S100 removed"
            ),
        },
        "reason": "Final sampling-rate sensitivity and ME/MI rejection audit before manuscript freeze",
        "does_not_overwrite": ["results/definitive/", "results/postdefinitive_e05/"],
    }
    write_json(out_root / "provenance.json", provenance)

    data_root = config.path("data_root", project_root=project_root)
    audit = audit_subjects(config.subjects, config.runs, data_root, download=False)

    sampling_summary = None
    if not args.skip_sampling_rate:
        sampling_summary = run_sampling_rate_sensitivity(
            config=config,
            project_root=project_root,
            audit=audit,
            out_root=out_root,
            frozen_fold_path=Path(args.frozen_folds),
        )
        print("sampling_rate", sampling_summary)

    rej_summary = None
    if not args.skip_rejection_audit:
        rej_summary, md, primary_subjects = run_rejection_audit(
            config=config,
            project_root=project_root,
            audit=audit,
            out_root=out_root,
        )
        print("rejection", rej_summary["primary_cohort"])
        recon = reconcile_qc(
            project_root=project_root,
            out_root=out_root,
            audit_md=md,
            primary_subjects=primary_subjects,
            rej_summary=rej_summary,
        )
        print("reconciliation", recon["reconcile_ok"])

    # Primary immutability check
    e01_sum = json.loads(
        _first_existing(
            Path("results/definitive/full/e01/erd_lr/summary.json"),
            Path("results/full/e01/erd_lr/summary.json"),
        ).read_text()
    )
    if abs(float(e01_sum["balanced_accuracy"]) - PRIMARY_BACC) > 1e-9:
        raise RuntimeError(
            f"STOP: definitive E01 BAcc changed on disk: {e01_sum['balanced_accuracy']}"
        )
    if int(float(e01_sum["n_participants"])) != PRIMARY_N:
        raise RuntimeError("STOP: definitive E01 N changed on disk")
    write_json(
        out_root / "primary_immutability_check.json",
        {
            "e01_bacc": float(e01_sum["balanced_accuracy"]),
            "e01_n": float(e01_sum["n_participants"]),
            "reference_bacc": PRIMARY_BACC,
            "abs_delta_vs_reference": abs(float(e01_sum["balanced_accuracy"]) - PRIMARY_BACC),
            "unchanged": True,
            "e07_not_rerun": True,
            "e05_not_overwritten": True,
        },
    )
    write_json(
        out_root / "run_summary.json",
        {"sampling_rate": sampling_summary, "rejection_audit": rej_summary},
    )
    print("DONE", out_root)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
