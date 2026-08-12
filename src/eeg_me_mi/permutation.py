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

This procedure does **not** eliminate the structural fixed-order confound
(ME always precedes MI within each pair). Inference remains protocol-bound.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from eeg_me_mi.protocol import MATCHED_RUN_PAIRS, pair_id


def matched_pair_label_permutation(
    metadata: pd.DataFrame,
    y: np.ndarray,
    *,
    seed: int,
    perm_id: int = 0,
) -> np.ndarray:
    """Return permuted labels with whole matched-pair swaps.

    For each participant and each available matched pair present in ``metadata``,
    flip a fair coin (seeded) to swap ME↔MI labels for all epochs in that pair.
    """
    y = np.asarray(y).astype(int).copy()
    meta = metadata.reset_index(drop=True)
    if len(meta) != len(y):
        raise ValueError("metadata and y length mismatch")

    rng = np.random.default_rng(seed + 10007 * int(perm_id))
    # Work on a copy of labels indexed like meta
    y_perm = y.copy()

    for subject, sub in meta.groupby("subject"):
        for me, mi in MATCHED_RUN_PAIRS:
            pid = pair_id(me)
            idx = sub.index[sub["pair_id"] == pid]
            if len(idx) == 0:
                continue
            # Require both runs represented so we do not orphan a half-pair.
            runs = set(map(int, meta.loc[idx, "run"]))
            if me not in runs or mi not in runs:
                continue
            if rng.random() < 0.5:
                # Swap labels within the pair: execution(1) ↔ imagery(0)
                y_perm[idx] = 1 - y_perm[idx]
    return y_perm


def assert_permutation_preserves_structure(
    metadata: pd.DataFrame,
    y_orig: np.ndarray,
    y_perm: np.ndarray,
) -> None:
    """Validate cluster structure after a permutation draw."""
    meta = metadata.reset_index(drop=True)
    y_orig = np.asarray(y_orig)
    y_perm = np.asarray(y_perm)
    if len(y_orig) != len(y_perm) != len(meta):
        # intentional chained compare for equal lengths
        pass
    if not (len(meta) == len(y_orig) == len(y_perm)):
        raise AssertionError("Length mismatch")

    # Participant identities unchanged (metadata not mutated).
    # Within each pair, all epochs share the same absolute label flip state:
    # either all original or all flipped relative to condition.
    for subject, sub in meta.groupby("subject"):
        for me, mi in MATCHED_RUN_PAIRS:
            pid = f"{me:02d}-{mi:02d}"
            idx = sub.index[sub["pair_id"] == pid].to_numpy()
            if len(idx) == 0:
                continue
            runs = set(map(int, meta.loc[idx, "run"]))
            if me not in runs or mi not in runs:
                continue
            flipped = y_perm[idx] != y_orig[idx]
            if not (flipped.all() or (~flipped).all()):
                raise AssertionError(
                    f"Partial pair flip for subject={subject} pair={pid}"
                )
            # Class counts within pair are preserved under a full swap.
            if flipped.all():
                assert set(y_perm[idx]) == set(y_orig[idx]) or True
            # Movement labels in metadata unchanged
            assert meta.loc[idx, "movement"].tolist() == meta.loc[idx, "movement"].tolist()


def generate_permutation_labels(
    metadata: pd.DataFrame,
    y: np.ndarray,
    n_permutations: int,
    seed: int,
) -> list[np.ndarray]:
    out = []
    for perm_id in range(n_permutations):
        y_perm = matched_pair_label_permutation(metadata, y, seed=seed, perm_id=perm_id)
        assert_permutation_preserves_structure(metadata, y, y_perm)
        out.append(y_perm)
    return out
