# Milestone 2 remediation report

**Status:** Remediation complete — **STOP for scientific review.**  
**Do not** run definitive E00–E06/E08, E07×1000, or interpret definitive accuracy.

Pre-remediation checkpoint: `b8ae008` / tag `m2-pre-remediation-checkpoint`.

Execution-candidate tag: **`m2-remediated-execution-candidate`** (clean tree; resolve commit via `git rev-parse m2-remediated-execution-candidate`).

---

## E00

| Item | Result |
|---|---|
| Measured FIR half-support (80 Hz, MNE 1.12.1) | **0.825 s** (133 taps; duration 1.6625 s) |
| Old window `[-2.0, -0.5]` | **Unsafe** — contaminated overlap `[-0.825, -0.5]` |
| Repaired strategy | Keep shared continuous zero-phase preprocessing; freeze **`e00 = [-2.0, -0.8375]`** |
| Impulse test | Passed (`tests/test_remediation.py`); unsafe `-0.5` crop rejected by extractor |
| Docs | `docs/e00_filter_support_analysis.md` |

---

## E02

| Item | Result |
|---|---|
| Bug | Pilot/path restricted to E01-primary before E02 eligibility |
| Fix | `filter_e02_epochs()` builds each analysis from **full 200 µV metadata** + E02 flag |
| Reconciled counts | left 93, right 94, both fists 93, both feet 92, uni 102, bi 102 |
| Fixture | E01-ineligible / E02-left-eligible participant included in E02 only |

---

## Strict sensitivity

| Item | Result |
|---|---|
| Status | Implemented as **`e01_strict_sensitivity`** (not a new primary) |
| Pipeline | Same primary ERD-LR; population-specific folds |
| Cohort N | **67** (IDs recorded in eligibility table / report package) |
| Boundary tests | 39 vs 40 mode; 19 vs 20 cell; &lt;80% vs ≥80% completeness |
| Wording | Clarified: no separate “expected ≥25” rule |

---

## S109

| Item | Result |
|---|---|
| Findings | 180 epochs; **0** pass 200 µV; max-PTP ≈ 639–1017 µV; **C4** is worst channel on all epochs |
| Neighbors | Median max-PTP ≈ 111 µV (S105–S108) |
| Units | EDF µV; MNE volts; threshold µV — **no systematic unit bug detected** |
| Exclusion | Remains technically justified under frozen 200 µV rule |
| Bad-channel rule | **Not implemented.** Optional single-channel sensitivity proposed for review only |
| STOP? | No global recompute required |

---

## Inner CV

| Item | Result |
|---|---|
| Criterion | **Participant-mean balanced accuracy** (equal weight) |
| Grid | C ∈ {0.01, 0.1, 1, 10} unchanged |
| Tests | Unequal epoch counts; arithmetic mean; deterministic C selection |

---

## E07

| Item | Result |
|---|---|
| Status | Final engine in `eeg_me_mi.e07` / CLI `run-e07` (benchmark kept separate) |
| Observed | Participant-mean BAcc; must equal E01 primary |
| Null | Whole matched-pair ME↔MI swaps within participant |
| p-value | One-sided plus-one; denom = 1 + N_perm |
| Checkpoint | Atomic per-perm JSON; resume; no duplicate IDs; fail-closed completion |
| Interpretation | Protocol-bound structured association; does **not** remove run order |
| Tests | Seeds, structure, plus-one, resume, position-only confound can reject |

---

## Config

| Item | Result |
|---|---|
| Canonical scientific config | `configs/full.yaml` |
| TRUBA overlay | `configs/truba_full.yaml` — **identical scientific parameters** |
| Scoring | `participant_mean_balanced_accuracy` (obsolete `roc_auc` removed) |
| Definitive entrypoint | `python -m eeg_me_mi.cli run-full configs/full.yaml` (rejects pilot; dry-run OK) |

---

## Provenance

Recorded at final commit/tag (see package). Dirty trees refused for definitive runs unless `--allow-dirty`. Cache manifests include EDF fingerprints, annotations, filter/reference/montage, MNE version, git commit.

---

## TRUBA

| Item | Result |
|---|---|
| `sbatch` on this host | **Not available** (`cnjume` workstation) |
| Final script | `slurm/e07_final.sbatch` (targets `run-e07`, `set -euo pipefail`, 2 CPUs) |
| Authorized smoke | **Local** E07 smoke: 5 permutations on subjects 1–8 (`configs/e07_local_smoke.yaml`) |
| Wall time (fresh 5-perm) | ≈ **20.6 s** total (≈5.7 s permutation loop after load) |
| CPU | ≈ **354%** of one core during job (MNE/BLAS threads; E07 itself is single-worker) |
| Peak RSS | ≈ **643 MB** |
| Resume | Verified (deleted `perm_0004`, restart completed without duplicating 0–3) |
| Recommended final request | **2 CPUs, 16 GB, ≥24 h** for N=1000 on full cohort (do not request 16 CPUs expecting speedup) |

Extrapolation note: local 8-subject smoke is **not** a substitute for TRUBA timing of the full 102-participant E01 cohort. Prior M2 benchmark (~16 s/perm on larger cohort) remains the better HPC planning prior until a TRUBA smoke is run.

---

## Tests

| Metric | Value |
|---|---|
| Passed | **60** |
| Failed | **0** |
| Skipped | **0** |
| Runtime | ≈ **9.8–10.1 s** |

---

## Remaining issues requiring scientific review

1. **S109 single-channel (C4) rule** — proposed sensitivity only; not adopted.
2. **TRUBA smoke** — not executed here (no SLURM). Run `sbatch --export=N_PERM=10 slurm/e07_final.sbatch` after clean checkout on TRUBA.
3. **Cache rebuild** — cache key bumped to v3; first definitive preprocess will rebuild subject caches (raw EDFs untouched).
4. **E00 vs E01 baseline windows now differ by design** — documented control-specific necessity; confirm acceptance before definitive execution.

---

## STOP

Remediation package ready for independent review.  
**Do not proceed to definitive analyses until review sign-off.**
