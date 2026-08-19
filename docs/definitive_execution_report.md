# Definitive execution report

Factual record of the frozen definitive run. No scientific interpretation.

## Provenance

| Item | Value |
|---|---|
| Git commit | `3b615ed1a8e455918d6e9d90bfb5c4e42ae44adc` |
| Git tag | `m2-preexec-fir-windows-candidate` |
| Clean tree at run | **yes** (`git_dirty: false`) |
| Config | `configs/full.yaml` |
| Config file SHA-256 | `6c619f6039964085506c22f38d5b35647afacac1143e122868704f37438f795a` |
| Run-metadata config checksum (JSON dump) | `6e9b34c99cae13b4efddbd34bf7aae589f8a27c60b1c0eda4d6ba7d7d1065270` |
| Seed | 2026 |
| Python | 3.13.11 |
| MNE | 1.12.1 |
| scikit-learn | 1.9.0 |
| numpy | 2.5.2 |
| scipy | 1.18.0 |
| pandas | 2.3.3 |
| Host (non-E07) | `orfoz268` (job **6237864**) |
| Host (E07) | `orfoz217` (job **6238254**) |
| Pre-run tests | **64 passed**, 0 failed (clean worktree at tag) |

Windows (frozen):

- E00: `[-2.0, -0.8375]`
- E01 baseline: `[-2.0, -0.8375]`
- E01 task: `[+0.8375, +3.5]`

## Final cohorts

From definitive `participant_eligibility.csv` / completion reconciliation:

| Cohort | N |
|---|---:|
| E01 primary | 102 |
| Strict sensitivity | 51 |
| E02 left_fist | 91 |
| E02 right_fist | 90 |
| E02 both_fists | 92 |
| E02 both_feet | 91 |
| E02 unilateral | 102 |
| E02 bilateral | 102 |

S109 not in primary cohort.

Pre-execution audit (2026-08-12, pre-FIR freeze) had identical E01 primary N=102 (same IDs); strict/E02 movement Ns were larger. Investigation: epoch-count decreases under definitive preprocess/cache rebuild; no subjects added; eligibility rules unchanged. See `results/definitive/remote_meta/cohort_count_investigation.md`.

## E00 numerical results

| Metric | Value |
|---|---:|
| Participant-mean BAcc | 0.539019 |
| Bootstrap 95% CI | [0.528088, 0.549952] (n=2000) |
| ROC-AUC | 0.582363 |
| Macro-F1 | 0.487587 |
| Sensitivity | 0.528940 |
| Specificity | 0.549099 |
| Average precision | 0.581750 |
| MCC | 0.093215 |
| Accuracy | 0.538899 |
| N participants | 102 |

Machine-readable: `results/definitive/full/e00/`.

## E01 primary numerical results

Primary endpoint: participant-mean balanced accuracy (ERD-LR).

| Metric | Value |
|---|---:|
| Participant-mean BAcc | 0.617924 |
| Bootstrap 95% CI | [0.603553, 0.632899] (n=2000) |
| ROC-AUC | 0.670352 |
| Macro-F1 | 0.608638 |
| Sensitivity | 0.614182 |
| Specificity | 0.621666 |
| Average precision | 0.668240 |
| MCC | 0.242461 |
| Accuracy | 0.617296 |
| N participants | 102 |

Machine-readable: `results/definitive/full/e01/erd_lr/` (summary, OOF, bootstrap, fold metrics, inner tuning).

## Comparator numerical results

| Model | Participant-mean BAcc |
|---|---:|
| Dummy | 0.500000 |
| CSP + shrinkage LDA | 0.555715 |
| Riemannian tangent-space + LR | 0.583363 |
| Strict-cohort ERD-LR (N=51) | 0.614025 |

## E00–E01 paired numerical results

| Quantity | Value |
|---|---:|
| Common N | 102 |
| Mean difference (E01−E00) | 0.078905 |
| Bootstrap 95% CI | [0.065574, 0.092283] |
| Two-sided paired sign-flip p (plus-one) | 0.0004997501249375312 |
| Sign-flips | 2000 |

## E02 numerical results

| Analysis | N | Participant-mean BAcc |
|---|---:|---:|
| left_fist | 91 | 0.623027 |
| right_fist | 90 | 0.632638 |
| both_fists | 92 | 0.607231 |
| both_feet | 91 | 0.613669 |
| unilateral | 102 | 0.623691 |
| bilateral | 102 | 0.618545 |

Outputs under `results/definitive/full/e02/*/`.

## E03 numerical results

ROI / channel physiology tables written to `results/definitive/full/e03/` (`roi_summary.csv`, `roi_participant_effects.csv`, `laterality.csv`, `channel_summary_fdr.csv`, `multiplicity_families.json`).

## E04 outputs

EXPLORATORY: `results/definitive/full/e04/participant_heterogeneity.csv`, `exploratory_correlations.csv`.

## E05 sensitivity outputs

`results/definitive/full/e05/threshold_cohorts.csv`, `spatial_control_channels.json`.

## E06 outputs

| Analysis | Path |
|---|---|
| first-60-second | `e06/first60/` |
| all-event | `e06/all_events/` |

## E08 diagnostics

`e08/by_run.csv`, `by_repetition.csv`, `matched_pairs.csv`.

## E07

| Item | Value |
|---|---|
| SLURM job | **6238254** |
| State | COMPLETED, ExitCode 0:0 |
| Node | orfoz217 |
| N_PERM | 1000 |
| Valid permutations | **1000 / 1000** |
| Failures | 0 |
| Observed statistic | 0.6179239767273408 (= E01 primary BAcc) |
| count(null ≥ observed) | 0 |
| Plus-one p | (1+0)/1001 = **0.000999000999000999** |
| Seed | 2026 |
| Wall (sacct) | 02:24:19 |
| Wall (`/usr/bin/time`) | 2:24:09 |
| MaxRSS (batch) | 8302296K (~7.9 GiB) |
| MaxRSS (`time`) | 5575176K (~5.3 GiB) |
| TotalCPU | 2-22:03:54 |
| CPUs requested | 56 (Orfoz QOS; CLI override of tagged `-c 2`) |
| Mem requested | 16G |
| ALLOW_DIRTY | **not used** |
| Checkpoints | 1000 |

## Integrity checks

| Check | Status |
|---|---|
| Non-E07 completion_manifest.complete | true |
| Mandatory E00–E06/E08 files present | pass |
| E01 OOF unique / finite | pass |
| Fold IDs = primary eligible IDs (N=102) | pass |
| S109 excluded from primary | pass |
| E00 window frozen bounds | pass |
| E07 complete 1000/1000 | pass |
| E07 observed == E01 primary | pass |
| Plus-one p formula | pass |
| Duplicate perm IDs | none |
| Clean tree throughout | yes |

## Execution warnings

1. Orfoz QOS requires `-c 56` or `-c 112`. Tagged `slurm/e07_final.sbatch` still contains `#SBATCH -c 2`; definitive E07 used `sbatch -c 56 ...` override (operational, not a method change).
2. Pre-execution eligibility audit (2026-08-12) vs definitive cohort Ns differ for strict/E02 movement subsets; primary E01 identical. Documented in cohort investigation note.
3. Local working tree may contain uncommitted pre-exec report / sbatch edits; definitive execution used a clean tagged checkout on TRUBA only.

## Deviations from frozen plan

**NONE** for scientific methods (eligibility rules, windows, models, C grid, folds, E07 null, p-formula).

Operational only: Orfoz `-c 56` sbatch override as above.

## Review package

| Item | Value |
|---|---|
| Path | `eeg_me_mi_definitive_results_review_package.zip` |
| SHA-256 | `aec05d0b6404afa58bc000c62e2741aa1c56315c1e6b449c02748e399b7bd561` |
| Sidecar | `eeg_me_mi_definitive_results_review_package.sha256` |
