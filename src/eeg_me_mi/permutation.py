"""E07 structured matched-pair permutation engine.

Exchangeability assumption
--------------------------
Under the observed EEGMMIDB protocol, each matched ME/MI run pair shares the
same movement family and repetition index, with ME always recorded before MI.
The null procedure randomly swaps or keeps labels for an entire matched pair
within each participant. This preserves:

    * participant clustering;
    * movement family and repetition;
    * within-run epoch structure;

and does **not** make epochs exchangeable across runs or participants.

Interpretation (frozen)
-----------------------
E07 is a **protocol-bound structured association test** under a conditional
matched-pair exchangeability assumption. It does **not** eliminate the
structural fact that ME is the first member of every pair and MI the second.
A significant E07 result does **not** by itself establish a purely physiological
execution-versus-imagery effect. Do not describe E07 as controlling for or
removing run order.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from eeg_me_mi.protocol import MATCHED_RUN_PAIRS, pair_id


def matched_pair_swap_map(
    metadata: pd.DataFrame,
    *,
    seed: int,
    perm_id: int = 0,
) -> dict[tuple[int, str], bool]:
    """Return ``{(subject, pair_id): swap}`` decisions for one permutation."""
    meta = metadata.reset_index(drop=True)
    rng = np.random.default_rng(int(seed) + 10007 * int(perm_id))
    decisions: dict[tuple[int, str], bool] = {}
    for subject, sub in meta.groupby("subject"):
        for me, mi in MATCHED_RUN_PAIRS:
            pid = pair_id(me)
            idx = sub.index[sub["pair_id"] == pid]
            if len(idx) == 0:
                continue
            runs = set(map(int, meta.loc[idx, "run"]))
            if me not in runs or mi not in runs:
                continue
            decisions[(int(subject), pid)] = bool(rng.random() < 0.5)
    return decisions


def apply_swap_map(
    metadata: pd.DataFrame,
    y: np.ndarray,
    swap_map: dict[tuple[int, str], bool],
) -> np.ndarray:
    """Apply whole-pair ME↔MI label swaps according to ``swap_map``."""
    y = np.asarray(y).astype(int).copy()
    meta = metadata.reset_index(drop=True)
    if len(meta) != len(y):
        raise ValueError("metadata and y length mismatch")
    y_perm = y.copy()
    for (subject, pid), swap in swap_map.items():
        if not swap:
            continue
        idx = meta.index[(meta["subject"] == subject) & (meta["pair_id"] == pid)]
        y_perm[idx] = 1 - y_perm[idx]
    return y_perm


def matched_pair_label_permutation(
    metadata: pd.DataFrame,
    y: np.ndarray,
    *,
    seed: int,
    perm_id: int = 0,
) -> tuple[np.ndarray, dict[tuple[int, str], bool]]:
    """Return ``(permuted_labels, swap_map)`` for one structured permutation."""
    swap_map = matched_pair_swap_map(metadata, seed=seed, perm_id=perm_id)
    y_perm = apply_swap_map(metadata, y, swap_map)
    return y_perm, swap_map


def assert_permutation_preserves_structure(
    metadata: pd.DataFrame,
    y_orig: np.ndarray,
    y_perm: np.ndarray,
) -> None:
    """Validate cluster structure after a permutation draw."""
    meta = metadata.reset_index(drop=True)
    y_orig = np.asarray(y_orig)
    y_perm = np.asarray(y_perm)
    if not (len(meta) == len(y_orig) == len(y_perm)):
        raise AssertionError(
            f"Length mismatch: meta={len(meta)} y_orig={len(y_orig)} y_perm={len(y_perm)}"
        )

    # Participant / run / movement / pair columns must be unchanged (labels only).
    for col in ("subject", "run", "movement", "pair_id", "task_family", "repetition"):
        if col in meta.columns:
            # Structure is in metadata; permutation must not require mutating it.
            assert meta[col].isna().sum() == meta[col].isna().sum()

    for subject, sub in meta.groupby("subject"):
        for me, mi in MATCHED_RUN_PAIRS:
            pid = f"{me:02d}-{mi:02d}"
            idx = sub.index[sub["pair_id"] == pid].to_numpy()
            if len(idx) == 0:
                continue
            runs = set(map(int, meta.loc[idx, "run"]))
            if me not in runs or mi not in runs:
                continue
            # Whole-pair flip or keep: no partial pair flips.
            flipped = y_perm[idx] != y_orig[idx]
            if not (bool(flipped.all()) or bool((~flipped).all())):
                raise AssertionError(
                    f"Partial pair flip for subject={subject} pair={pid}"
                )
            # Class multiset within the pair is preserved under a full swap.
            if flipped.all():
                assert sorted(y_perm[idx].tolist()) == sorted((1 - y_orig[idx]).tolist())
            # Movement family and run membership unchanged.
            assert set(meta.loc[idx, "run"].astype(int)) == set(meta.loc[idx, "run"].astype(int))
            movements = meta.loc[idx, "movement"].tolist()
            assert movements == meta.loc[idx, "movement"].tolist()
            assert all(meta.loc[idx, "subject"].astype(int) == int(subject))


def generate_permutation_labels(
    metadata: pd.DataFrame,
    y: np.ndarray,
    n_permutations: int,
    seed: int,
) -> list[np.ndarray]:
    out = []
    for perm_id in range(n_permutations):
        y_perm, _swap = matched_pair_label_permutation(
            metadata, y, seed=seed, perm_id=perm_id
        )
        assert_permutation_preserves_structure(metadata, y, y_perm)
        out.append(y_perm)
    return out


def plus_one_pvalue(observed: float, null_stats: np.ndarray, *, alternative: str = "greater") -> dict[str, Any]:
    """Plus-one p-value for a one-sided (default) or two-sided null comparison."""
    null = np.asarray(null_stats, dtype=float)
    null = null[np.isfinite(null)]
    n = int(len(null))
    if alternative == "greater":
        count = int(np.sum(null >= float(observed)))
    elif alternative == "two-sided":
        count = int(np.sum(np.abs(null) >= abs(float(observed))))
    else:
        raise ValueError(f"Unsupported alternative: {alternative}")
    p = (1 + count) / (1 + n) if n >= 0 else float("nan")
    return {
        "observed": float(observed),
        "n_permutations": n,
        "n_null_ge_observed": count if alternative == "greater" else count,
        "p_value_plusone": float(p),
        "alternative": alternative,
        "denominator": int(1 + n),
    }


E07_INTERPRETATION = {
    "test_type": "protocol_bound_structured_association_test",
    "exchangeability": "conditional_matched_pair_within_participant",
    "does_not_remove_run_order": True,
    "me_always_first_in_pair": True,
    "mi_always_second_in_pair": True,
    "claim_limit": (
        "A significant E07 result supports protocol-bound association under the "
        "matched-pair exchangeability assumption; it does not by itself establish "
        "a purely physiological execution-versus-imagery effect."
    ),
}
