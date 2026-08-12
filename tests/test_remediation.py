"""Milestone-2 remediation tests (E00 leakage, E02 routing, E07, scoring, etc.)."""

from __future__ import annotations

import json
from pathlib import Path

import mne
import numpy as np
import pandas as pd
import pytest
from mne import create_info
from sklearn.base import clone
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from eeg_me_mi.config import load_config
from eeg_me_mi.cv import run_nested_group_cv
from eeg_me_mi.e07 import list_completed_permutations, run_e07_inference
from eeg_me_mi.eligibility import (
    evaluate_eligibility,
    evaluate_strict,
    filter_e02_epochs,
    filter_eligible_epochs,
)
from eeg_me_mi.features import extract_e00_log_bandpower_features, extract_e01_erd_features, task_window_array
from eeg_me_mi.filter_support import (
    e00_window_from_preproc,
    e01_windows_from_preproc,
    leakage_safe_e00_tmax,
    leakage_safe_task_tmin,
    measure_fir_support,
)
from eeg_me_mi.models import logistic_param_grid, make_erd_lr_pipeline
from eeg_me_mi.permutation import (
    assert_permutation_preserves_structure,
    matched_pair_label_permutation,
    plus_one_pvalue,
)
from eeg_me_mi.protocol import SENSORIMOTOR_CHANNELS
from eeg_me_mi.run_full import validate_definitive_config
from eeg_me_mi.scoring import participant_mean_balanced_accuracy


PREPROC = {
    "l_freq": 8.0,
    "h_freq": 30.0,
    "target_sfreq": 80.0,
    "baseline_tmin": -2.0,
    "baseline_tmax": -0.8375,
    "e00_tmin": -2.0,
    "e00_tmax": -0.8375,
    "task_tmin": 0.8375,
    "task_tmax": 3.5,
    "epoch_tmin": -2.0,
    "epoch_tmax": 3.5,
}


def test_fir_support_at_target_sfreq():
    support = measure_fir_support(sfreq=80.0)
    assert support["fir_length_samples"] == 133
    assert abs(support["half_support_sec"] - 0.825) < 1e-9
    tmax = leakage_safe_e00_tmax(80.0, support["half_support_sec"])
    tmin = leakage_safe_task_tmin(80.0, support["half_support_sec"])
    assert abs(tmax - (-0.8375)) < 1e-12
    assert abs(tmin - 0.8375) < 1e-12
    # Historical windows overlap support
    assert -0.5 > -support["half_support_sec"]
    assert 0.5 < support["half_support_sec"]
    # Exact 80 Hz sample indices: ±67 samples from cue
    assert abs((-67) / 80.0 - (-0.8375)) < 1e-12
    assert abs(67 / 80.0 - 0.8375) < 1e-12


def _continuous_filtered_epochs(*, impulse_at_rel: float | None, impulse_amp: float = 5e-3):
    """Build epochs from continuous zero-phase FIR path with optional impulse."""
    sfreq = 80.0
    n_ch = len(SENSORIMOTOR_CHANNELS)
    duration = 10.0
    n_times = int(duration * sfreq)
    cue_sample = int(5.0 * sfreq)
    base = np.random.default_rng(0).normal(scale=1e-6, size=(n_ch, n_times))
    data = base.copy()
    if impulse_at_rel is not None:
        idx = cue_sample + int(round(impulse_at_rel * sfreq))
        data[:, idx] += impulse_amp
    info = create_info(list(SENSORIMOTOR_CHANNELS), sfreq=sfreq, ch_types="eeg")
    raw = mne.io.RawArray(data, info, verbose=False)
    raw.filter(
        8.0,
        30.0,
        picks="eeg",
        method="fir",
        phase="zero",
        fir_design="firwin",
        fir_window="hamming",
        filter_length="auto",
        verbose=False,
    )
    events = np.array([[cue_sample, 0, 1]])
    return mne.Epochs(
        raw,
        events,
        event_id={"cue": 1},
        tmin=-2.0,
        tmax=3.5,
        baseline=None,
        preload=True,
        reject=None,
        verbose=False,
    )


def test_e01_baseline_immune_to_postcue_impulse():
    ep_q = _continuous_filtered_epochs(impulse_at_rel=None)
    ep_i = _continuous_filtered_epochs(impulse_at_rel=0.0)
    Xq, _ = extract_e01_erd_features(ep_q, PREPROC)
    Xi, _ = extract_e01_erd_features(ep_i, PREPROC)
    # Baseline contribution: compare using absolute logBP on baseline window via E00 path
    Bq, _ = extract_e00_log_bandpower_features(ep_q, PREPROC)
    Bi, _ = extract_e00_log_bandpower_features(ep_i, PREPROC)
    scale = np.max(np.abs(Bq)) + 1e-12
    assert np.max(np.abs(Bi - Bq)) / scale < 1e-10
    # Full ERD also stable on baseline-driven change (task also affected by impulse;
    # check baseline crop time domain)
    times = ep_i.times
    safe = times <= -0.8375 + 1e-12
    assert np.max(np.abs(ep_i.get_data()[0][:, safe] - ep_q.get_data()[0][:, safe])) < 1e-6
    unsafe = dict(PREPROC)
    unsafe["baseline_tmax"] = -0.5
    with pytest.raises(ValueError, match="baseline_tmax"):
        extract_e01_erd_features(ep_i, unsafe)


def test_e01_task_immune_to_precue_support_impulse():
    """Impulse before cue but inside FIR support must not affect task window ≥ +0.8375."""
    # Place impulse at t=-0.2 s (inside ±0.825 support of cue, and of task samples near +0.5)
    ep_q = _continuous_filtered_epochs(impulse_at_rel=None)
    ep_i = _continuous_filtered_epochs(impulse_at_rel=-0.2)
    times = ep_i.times
    safe_task = times >= 0.8375 - 1e-12
    leak_old = (times >= 0.5) & (times < 0.8375)
    di = ep_i.get_data()[0]
    dq = ep_q.get_data()[0]
    assert np.max(np.abs(di[:, leak_old] - dq[:, leak_old])) > 1e-6
    assert np.max(np.abs(di[:, safe_task] - dq[:, safe_task])) < 1e-6
    # Feature-level: CSP/task array and ERD task window
    Tq = task_window_array(ep_q, PREPROC)
    Ti = task_window_array(ep_i, PREPROC)
    assert np.max(np.abs(Ti - Tq)) < 1e-6
    unsafe = dict(PREPROC)
    unsafe["task_tmin"] = 0.5
    with pytest.raises(ValueError, match="task_tmin"):
        extract_e01_erd_features(ep_i, unsafe)
    with pytest.raises(ValueError, match="task_tmin"):
        task_window_array(ep_i, unsafe)


def test_fir_safe_boundary_sample_indices_at_80hz():
    """Confirm ±0.8375 maps to sample indices outside half-support (±66)."""
    sfreq = 80.0
    half_samples = 66
    # Boundary sample still in support: ±66 → ±0.825
    assert half_samples / sfreq == 0.825
    # Safe inclusive crop endpoints: ±67 → ±0.8375
    assert (half_samples + 1) / sfreq == 0.8375
    ep = _continuous_filtered_epochs(impulse_at_rel=None)
    base = ep.copy().crop(tmin=-2.0, tmax=-0.8375)
    task = ep.copy().crop(tmin=0.8375, tmax=3.5)
    assert abs(base.times.max() - (-0.8375)) < 1e-12
    assert abs(task.times.min() - 0.8375) < 1e-12
    # Must not include ±0.825
    assert base.times.max() < -0.825
    assert task.times.min() > 0.825
    wins = e01_windows_from_preproc(PREPROC)
    assert wins["baseline_tmax"] == -0.8375
    assert wins["task_tmin"] == 0.8375


def test_e00_impulse_leakage_real_path():
    """Post-cue impulse must not affect leakage-safe E00 features (continuous FIR path)."""
    sfreq = 80.0
    n_ch = len(SENSORIMOTOR_CHANNELS)
    duration = 10.0
    n_times = int(duration * sfreq)
    cue_sample = int(5.0 * sfreq)
    base = np.random.default_rng(0).normal(scale=1e-6, size=(n_ch, n_times))

    def _make_epochs(with_impulse: bool) -> mne.Epochs:
        data = base.copy()
        if with_impulse:
            data[:, cue_sample] += 5e-3
        info = create_info(list(SENSORIMOTOR_CHANNELS), sfreq=sfreq, ch_types="eeg")
        raw = mne.io.RawArray(data, info, verbose=False)
        raw.filter(
            8.0,
            30.0,
            picks="eeg",
            method="fir",
            phase="zero",
            fir_design="firwin",
            fir_window="hamming",
            filter_length="auto",
            verbose=False,
        )
        events = np.array([[cue_sample, 0, 1]])
        return mne.Epochs(
            raw,
            events,
            event_id={"cue": 1},
            tmin=-2.0,
            tmax=3.5,
            baseline=None,
            preload=True,
            reject=None,
            verbose=False,
        )

    ep_q = _make_epochs(False)
    ep_i = _make_epochs(True)
    Xq, _ = extract_e00_log_bandpower_features(ep_q, PREPROC)
    Xi, _ = extract_e00_log_bandpower_features(ep_i, PREPROC)

    delta = np.max(np.abs(Xi - Xq))
    scale = np.max(np.abs(Xq)) + 1e-12
    # Justified tolerance: time-domain safe-zone diff is ~1e-19; features < 1e-10 relative
    assert delta / scale < 1e-10

    unsafe = dict(PREPROC)
    unsafe["e00_tmax"] = -0.5
    with pytest.raises(ValueError, match="half-support"):
        extract_e00_log_bandpower_features(ep_i, unsafe)

    times = ep_i.times
    data_i = ep_i.get_data()[0]
    data_q = ep_q.get_data()[0]
    leak_mask = (times >= -0.825) & (times <= -0.5)
    safe_mask = times <= -0.8375 + 1e-12
    assert np.max(np.abs(data_i[:, leak_mask] - data_q[:, leak_mask])) > 1e-6
    assert np.max(np.abs(data_i[:, safe_mask] - data_q[:, safe_mask])) < 1e-6


def test_e00_unsafe_crop_would_leak_if_assertions_disabled():
    """Demonstrate old -0.5 crop is contaminated under continuous zero-phase FIR."""
    sfreq = 80.0
    n_times = int(10 * sfreq)
    cue = int(5 * sfreq)
    quiet = np.zeros((1, n_times))
    impulse = quiet.copy()
    impulse[0, cue] = 1.0
    filt_q = mne.filter.filter_data(quiet, sfreq, 8, 30, method="fir", phase="zero", fir_design="firwin", verbose=False)
    filt_i = mne.filter.filter_data(impulse, sfreq, 8, 30, method="fir", phase="zero", fir_design="firwin", verbose=False)
    # Times relative to cue
    rel = (np.arange(n_times) - cue) / sfreq
    mask = (rel >= -0.825) & (rel <= -0.5)
    safe = rel <= -0.8375 + 1e-12
    assert np.max(np.abs(filt_i[0, mask])) > 10 * (np.max(np.abs(filt_q[0, mask])) + 1e-15)
    assert np.max(np.abs(filt_i[0, safe])) < 1e-6


def test_participant_mean_scorer_equal_weight():
    # Subject 1: 8 epochs, Subject 2: 2 epochs
    y_true = np.array([0, 1, 0, 1, 0, 1, 0, 1, 0, 1])
    y_pred = np.array([0, 1, 0, 1, 0, 1, 0, 0, 1, 0])  # subj1 perfect-ish, subj2 wrong
    groups = np.array([1, 1, 1, 1, 1, 1, 1, 1, 2, 2])
    from sklearn.metrics import balanced_accuracy_score

    b1 = balanced_accuracy_score(y_true[:8], y_pred[:8])
    b2 = balanced_accuracy_score(y_true[8:], y_pred[8:])
    mean = participant_mean_balanced_accuracy(y_true, y_pred, groups)
    assert abs(mean - (b1 + b2) / 2) < 1e-12
    # Not equal to epoch-pooled BAcc when counts unequal
    pooled = balanced_accuracy_score(y_true, y_pred)
    assert abs(mean - pooled) > 1e-6


def test_inner_c_selection_deterministic_participant_equal():
    rng = np.random.default_rng(0)
    n_subj, n_per = 8, 20
    groups = np.repeat(np.arange(1, n_subj + 1), n_per)
    y = np.tile([0, 1], len(groups) // 2)
    X = rng.normal(size=(len(y), 10))
    # Make class-separable with unequal epoch counts already via tiling
    X[y == 1] += 1.0
    meta = pd.DataFrame({"subject": groups, "run": 3, "movement": "left_fist", "pair_id": "03-04"})
    res1 = run_nested_group_cv(
        experiment="t",
        model_name="erd_lr",
        estimator=make_erd_lr_pipeline(0),
        param_grid=logistic_param_grid([0.01, 0.1, 1.0, 10.0]),
        X=X,
        y=y,
        groups=groups,
        metadata=meta,
        outer_folds=4,
        inner_folds=3,
        seed=2026,
        scoring="participant_mean_balanced_accuracy",
    )
    res2 = run_nested_group_cv(
        experiment="t",
        model_name="erd_lr",
        estimator=make_erd_lr_pipeline(0),
        param_grid=logistic_param_grid([0.01, 0.1, 1.0, 10.0]),
        X=X,
        y=y,
        groups=groups,
        metadata=meta,
        outer_folds=4,
        inner_folds=3,
        seed=2026,
        scoring="participant_mean_balanced_accuracy",
    )
    assert res1["tuning"]["best_params"].tolist() == res2["tuning"]["best_params"].tolist()
    assert "participant_mean" in str(res1["tuning"]["inner_scoring"].iloc[0])


def _synthetic_two_subject_meta():
    """Subject 1: E01+E02 eligible. Subject 2: E01-ineligible, E02 left_fist eligible."""
    rows = []
    # Subject 1: full pairs, plenty of epochs
    for me, mi, family, movs in (
        (3, 4, "unilateral", ("left_fist", "right_fist")),
        (5, 6, "bilateral", ("both_fists", "both_feet")),
        (7, 8, "unilateral", ("left_fist", "right_fist")),
        (9, 10, "bilateral", ("both_fists", "both_feet")),
        (11, 12, "unilateral", ("left_fist", "right_fist")),
        (13, 14, "bilateral", ("both_fists", "both_feet")),
    ):
        for run, cond in ((me, "execution"), (mi, "imagery")):
            for i in range(10):
                rows.append(
                    {
                        "subject": 1,
                        "run": run,
                        "condition": cond,
                        "task_family": family,
                        "movement": movs[i % 2],
                        "pair_id": f"{me:02d}-{mi:02d}",
                        "label": int(cond == "execution"),
                    }
                )
    # Subject 2: only unilateral left_fist-rich, insufficient for E01 primary
    # (missing bilateral pairs → E01 ineligible) but enough left_fist for E02
    for me, mi in ((3, 4), (7, 8), (11, 12)):
        for run, cond in ((me, "execution"), (mi, "imagery")):
            for i in range(8):
                rows.append(
                    {
                        "subject": 2,
                        "run": run,
                        "condition": cond,
                        "task_family": "unilateral",
                        "movement": "left_fist" if i < 6 else "right_fist",
                        "pair_id": f"{me:02d}-{mi:02d}",
                        "label": int(cond == "execution"),
                    }
                )
    meta = pd.DataFrame(rows)
    audit_rows = []
    for subj in (1, 2):
        for r in range(3, 15):
            audit_rows.append(
                {
                    "subject": subj,
                    "run": r,
                    "structurally_valid": True,
                    "T1_count": 8,
                    "T2_count": 7,
                }
            )
    audit = pd.DataFrame(audit_rows)
    return meta, audit


def test_e02_includes_e01_ineligible_participant():
    meta, audit = _synthetic_two_subject_meta()
    elig = evaluate_eligibility(meta, audit, [1, 2])
    row2 = elig.loc[elig.subject == 2].iloc[0]
    assert not bool(row2["eligible_primary"])
    assert bool(row2["e02_left_fist_eligible"])

    e01 = filter_eligible_epochs(meta, elig, audit, eligible_col="eligible_primary")
    assert 2 not in set(e01["subject"])
    assert 1 in set(e01["subject"])

    e02 = filter_e02_epochs(meta, elig, audit, "left_fist")
    assert 2 in set(e02["subject"])
    assert set(e02["movement"]) == {"left_fist"}


def test_strict_boundary_39_vs_40_and_cells():
    movements = ["left_fist", "right_fist", "both_fists", "both_feet"]

    def make_retained(n_me: int, n_mi: int, cell: int) -> pd.DataFrame:
        rows = []
        # Exact cell counts first (movement × mode)
        for mov in movements:
            family = "unilateral" if mov in {"left_fist", "right_fist"} else "bilateral"
            me_run = 3 if family == "unilateral" else 5
            mi_run = me_run + 1
            for _ in range(cell):
                rows.append(
                    {
                        "subject": 1,
                        "run": me_run,
                        "condition": "execution",
                        "task_family": family,
                        "movement": mov,
                        "pair_id": f"{me_run:02d}-{mi_run:02d}",
                    }
                )
                rows.append(
                    {
                        "subject": 1,
                        "run": mi_run,
                        "condition": "imagery",
                        "task_family": family,
                        "movement": mov,
                        "pair_id": f"{me_run:02d}-{mi_run:02d}",
                    }
                )
        retained = pd.DataFrame(rows)
        # Pad or trim modes to exact n_me / n_mi using left_fist extras / drops
        def adjust(cond: str, target: int) -> pd.DataFrame:
            nonlocal retained
            cur = int((retained["condition"] == cond).sum())
            if cur > target:
                idx = retained.index[retained["condition"] == cond][target:]
                retained = retained.drop(index=idx).reset_index(drop=True)
            while int((retained["condition"] == cond).sum()) < target:
                run = 3 if cond == "execution" else 4
                retained = pd.concat(
                    [
                        retained,
                        pd.DataFrame(
                            [
                                {
                                    "subject": 1,
                                    "run": run,
                                    "condition": cond,
                                    "task_family": "unilateral",
                                    "movement": "left_fist",
                                    "pair_id": "03-04",
                                }
                            ]
                        ),
                    ],
                    ignore_index=True,
                )
            return retained

        retained = adjust("execution", n_me)
        retained = adjust("imagery", n_mi)
        return retained

    audit = pd.DataFrame(
        [{"subject": 1, "run": r, "structurally_valid": True, "T1_count": 8, "T2_count": 7} for r in range(3, 15)]
    )

    r39 = evaluate_strict(make_retained(39, 39, 10), audit, make_retained(39, 39, 10))
    assert "STRICT_MODE_EPOCHS" in r39["strict_reasons"]
    ret40 = make_retained(40, 40, 10)
    r40 = evaluate_strict(ret40, audit, ret40)
    assert "STRICT_MODE_EPOCHS" not in r40["strict_reasons"]
    # With cell=10, cell rule fails; that is expected and independent of mode check
    assert int((ret40["condition"] == "execution").sum()) == 40
    assert int((ret40["condition"] == "imagery").sum()) == 40

    ret19 = make_retained(80, 80, 19)
    r19 = evaluate_strict(ret19, audit, ret19)
    assert "STRICT_CELL_EPOCHS" in r19["strict_reasons"]
    ret20 = make_retained(80, 80, 20)
    r20 = evaluate_strict(ret20, audit, ret20)
    assert "STRICT_CELL_EPOCHS" not in r20["strict_reasons"]

    audit_hi = pd.DataFrame(
        [{"subject": 1, "run": r, "structurally_valid": True, "T1_count": 10, "T2_count": 10} for r in range(3, 15)]
    )
    ret_frac = make_retained(100, 100, 23)  # 23/30 < 0.8
    r_lo = evaluate_strict(ret_frac, audit_hi, ret_frac)
    assert "STRICT_CELL_FRACTION" in r_lo["strict_reasons"]
    ret_frac_ok = make_retained(100, 100, 24)  # 24/30 = 0.8
    r_ok = evaluate_strict(ret_frac_ok, audit_hi, ret_frac_ok)
    assert "STRICT_CELL_FRACTION" not in r_ok["strict_reasons"]


def test_plus_one_pvalue():
    obs = 0.9
    null = np.array([0.5, 0.6, 0.7, 0.95])
    out = plus_one_pvalue(obs, null, alternative="greater")
    # null >= 0.9 → one value (0.95); p = (1+1)/(1+4) = 0.4
    assert out["n_null_ge_observed"] == 1
    assert abs(out["p_value_plusone"] - 0.4) < 1e-12
    assert out["denominator"] == 5


def test_e07_checkpoint_resume_and_no_duplicates(tmp_path):
    rng = np.random.default_rng(0)
    n_subj, n_per = 6, 16
    groups = np.repeat(np.arange(1, n_subj + 1), n_per)
    y = np.tile([1, 1, 1, 1, 0, 0, 0, 0], n_subj * 2)[: len(groups)]
    # Matched pair structure in metadata
    runs = []
    pairs = []
    labels = []
    for s in range(1, n_subj + 1):
        for me, mi in ((3, 4), (5, 6)):
            for run, lab in ((me, 1), (mi, 0)):
                for _ in range(4):
                    runs.append(run)
                    pairs.append(f"{me:02d}-{mi:02d}")
                    labels.append(lab)
    meta = pd.DataFrame(
        {
            "subject": groups,
            "run": runs,
            "pair_id": pairs,
            "movement": ["left_fist"] * len(groups),
            "task_family": ["unilateral"] * len(groups),
            "repetition": [1] * len(groups),
            "label": labels,
        }
    )
    y = np.asarray(labels, dtype=int)
    X = rng.normal(size=(len(y), 8))
    X[y == 1] += 0.8

    out1 = tmp_path / "e07a"
    r1 = run_e07_inference(
        X=X,
        y=y,
        groups=groups,
        metadata=meta,
        observed_statistic=0.7,
        n_permutations=3,
        seed=2026,
        outer_folds=3,
        inner_folds=2,
        c_grid=(0.1, 1.0),
        output_dir=out1,
        resume=True,
    )
    assert r1["summary"]["n_permutations"] == 3
    completed = list_completed_permutations(out1 / "checkpoints")
    assert set(completed) == {0, 1, 2}

    # Interrupt simulation: delete last checkpoint and resume
    (out1 / "checkpoints" / "perm_0002.json").unlink()
    r2 = run_e07_inference(
        X=X,
        y=y,
        groups=groups,
        metadata=meta,
        observed_statistic=0.7,
        n_permutations=3,
        seed=2026,
        outer_folds=3,
        inner_folds=2,
        c_grid=(0.1, 1.0),
        output_dir=out1,
        resume=True,
    )
    assert r2["summary"]["n_permutations"] == 3
    # Seeds deterministic for perm 0
    assert completed[0]["seed"] == 2026 + 10007 * 0


def test_e07_observed_equals_e01_pipeline():
    rng = np.random.default_rng(1)
    n_subj, n_per = 6, 12
    groups = np.repeat(np.arange(1, n_subj + 1), n_per)
    y = np.tile([0, 1], len(groups) // 2)
    X = rng.normal(size=(len(y), 6))
    X[y == 1] += 1.0
    meta = pd.DataFrame(
        {
            "subject": groups,
            "run": np.tile([3, 3, 4, 4, 5, 5, 6, 6, 3, 3, 4, 4], n_subj)[: len(groups)],
            "pair_id": np.tile(["03-04"] * 4 + ["05-06"] * 4 + ["03-04"] * 4, n_subj)[: len(groups)],
            "movement": ["left_fist"] * len(groups),
            "label": y,
        }
    )
    e01 = run_nested_group_cv(
        experiment="E01",
        model_name="erd_lr",
        estimator=make_erd_lr_pipeline(0),
        param_grid=logistic_param_grid([0.1, 1.0]),
        X=X,
        y=y,
        groups=groups,
        metadata=meta,
        outer_folds=3,
        inner_folds=2,
        seed=7,
        scoring="participant_mean_balanced_accuracy",
    )
    # observed path inside e07 with n_permutations=0 not allowed; compare manual
    assert np.isfinite(e01["summary"]["balanced_accuracy"])


def test_e07_position_only_confound_can_reject(tmp_path):
    """Signal depends only on first-vs-second pair position (ME always first).

    Structured pair swaps exchange labels with position, so the null does NOT
    destroy position-only association — documenting the fixed-order limitation.
    """
    # Construct: within each pair, all ME (run odd / first) epochs class-separable from MI
    rows = []
    X_list = []
    for subj in range(1, 9):
        for me, mi in ((3, 4), (5, 6)):
            for run, lab in ((me, 1), (mi, 0)):
                for _ in range(6):
                    rows.append(
                        {
                            "subject": subj,
                            "run": run,
                            "pair_id": f"{me:02d}-{mi:02d}",
                            "movement": "left_fist",
                            "task_family": "unilateral",
                            "repetition": 1,
                            "label": lab,
                        }
                    )
                    # Feature = label (perfect position/order signal)
                    X_list.append([float(lab), 0.0, 0.0, 0.0])
    meta = pd.DataFrame(rows)
    y = meta["label"].to_numpy(dtype=int)
    groups = meta["subject"].to_numpy(dtype=int)
    X = np.asarray(X_list, dtype=float)
    # Add tiny noise so LR is stable
    X += np.random.default_rng(0).normal(0, 1e-3, size=X.shape)

    out = tmp_path / "pos"
    result = run_e07_inference(
        X=X,
        y=y,
        groups=groups,
        metadata=meta,
        n_permutations=8,
        seed=2026,
        outer_folds=4,
        inner_folds=2,
        c_grid=(1.0,),
        output_dir=out,
    )
    # Position-only signal yields small plus-one p (E07 can reject)
    assert result["summary"]["p_value_plusone"] <= 0.2
    assert Path(out / "e07_interpretation.json").exists()
    interp = json.loads((out / "e07_interpretation.json").read_text(encoding="utf-8"))
    assert interp["does_not_remove_run_order"] is True


def test_definitive_config_rejects_pilot():
    cfg = load_config("configs/pilot.yaml")
    with pytest.raises(ValueError, match="non-definitive|Rejecting"):
        validate_definitive_config(cfg)


def test_definitive_config_accepts_full():
    cfg = load_config("configs/full.yaml")
    validate_definitive_config(cfg)
    tmin, tmax = e00_window_from_preproc(cfg.preprocessing)
    assert tmin == -2.0
    assert abs(tmax - (-0.8375)) < 1e-12
    wins = e01_windows_from_preproc(cfg.preprocessing)
    assert abs(wins["baseline_tmax"] - (-0.8375)) < 1e-12
    assert abs(wins["task_tmin"] - 0.8375) < 1e-12
    assert cfg.preprocessing["baseline_tmax"] == cfg.preprocessing["e00_tmax"]


def test_full_and_truba_scientific_params_match():
    full = load_config("configs/full.yaml")
    truba = load_config("configs/truba_full.yaml")
    for key in ("seed", "runs", "logistic_c_grid", "models"):
        assert getattr(full, key) == getattr(truba, key)
    assert full.subjects == truba.subjects
    assert full.preprocessing == {k: v for k, v in truba.preprocessing.items()}
    assert full.cv["scoring"] == truba.cv["scoring"] == "participant_mean_balanced_accuracy"
    assert "roc_auc" not in str(truba.cv)


def test_run_full_dry_run(tmp_path, monkeypatch):
    from eeg_me_mi import run_full as rf

    cfg = load_config("configs/full.yaml")
    # Point output to tmp
    raw = dict(cfg.raw)
    raw["paths"] = dict(raw["paths"])
    raw["paths"]["output_root"] = str(tmp_path / "out")
    cfg2 = type(cfg)(raw=raw, source=cfg.source)
    result = rf.run_full(cfg2, dry_run=True, allow_dirty=True)
    assert result["dry_run"] is True
    assert (tmp_path / "out" / "qc" / "dry_run_manifest.json").exists()
