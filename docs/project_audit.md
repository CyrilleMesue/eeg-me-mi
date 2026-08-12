# Project audit

Date: 2026-08-12  
Scope: artifacts supplied for the ME-versus-MI EEGMMIDB project; no refactoring performed.

## Executive finding

No project repository was present in the active workspace or the usual project locations under `~/Desktop`. The active workspace Git repository has no commits and all files are untracked. Consequently, repository history, the original executable notebook, generated result files, configurations, environments, and TRUBA/SLURM assets cannot yet be audited. This document audits the two supplied artifacts and records missing evidence explicitly. It must be updated when the actual repository is provided.

## Available artifacts

| Artifact | Description | Audit status |
|---|---|---|
| `Comparison_of_Motor_Execution_and_Imagery_Analyzing_EEG_Sign---67b8982e-2e83-4ba4-816d-3f9d29f71a51.pdf` | Nine-page draft manuscript, created 2026-08-12 | Read and compared with reanalysis |
| `publication_grade_eeg_me_vs_mi_reanalysis---64c29914-523d-4869-aca5-9a7543488a4c.txt` | 1,044-line Colab-exported reanalysis | Static code audit completed; not run end-to-end |
| `data/physionet_eegmmidb/` | Local persistent cache created for the access check | Contains subjects 1–2, runs 3–4 only |
| `.venv-data-access/` | Disposable local MNE environment used for the access check | MNE 1.12.1; not a project environment |

Artifact SHA-256 values are `7f28ccb9...d336c` (PDF) and `9b3271d7...8ea5` (reanalysis text).

## Missing repository components

No project README, source tree, original analysis code/notebook, dependency lock file, configs, tests, cached derived data, results, figures as separate files, manuscript source, SLURM scripts, TRUBA deployment files, CI, or meaningful Git history was found. The PDF mentions a repository and complete implementation, but neither is available here. The current reanalysis is an exported notebook body rather than an executable repository.

## Original manuscript workflow

The manuscript describes:

1. EEGMMIDB recordings represented as one 60-second or 120-second vector per run.
2. Electrode averaging into 13 broad anatomical groups.
3. Librosa Mel-spectrogram features with 128 Mel bands and largely audio-oriented defaults.
4. Global `f_classif` filtering at p-values below 0.05 and then 0.01.
5. Ten generic classifiers: random forest, decision tree, gradient boosting, logistic regression, XGBoost, CatBoost, AdaBoost, SVC, k-nearest neighbours, and MLP.
6. Apparently row-random train/test evaluation, with no participant-disjoint validation, nested tuning, confidence intervals, permutation inference, or retained fold assignments documented.

The reported accuracy/AUC values are about 0.50–0.59. These results are not publication-valid evidence of unseen-participant generalization because the splitting unit, preprocessing fit boundaries, and feature-selection boundaries are inappropriate or undocumented.

## Current reanalysis workflow

### Data and preprocessing

- Requests subjects 1–109 and task runs 3–14 through `mne.datasets.eegbci.load_data`.
- Correctly defines ME by runs 3/5/7/9/11/13 and MI by 4/6/8/10/12/14.
- Correctly maps T1/T2 to left/right fist in unilateral runs and both fists/both feet in bilateral runs.
- Standardizes EEGBCI channel names, applies a standard montage and average reference, resamples to 80 Hz, filters 8–30 Hz, and retains 21 FC/C/CP channels.
- Extracts annotation-locked epochs from -2.0 to 3.5 seconds; baseline is -2.0 to -0.5 seconds and task is 0.5 to 3.5 seconds.
- Applies a fixed 200 µV peak-to-peak rejection rule and caches concatenated epochs.
- Retains only participants with at least one surviving epoch in every task run.

### Features and models

- Primary interpretable features: 42 channel-by-band ERD/ERS values, `10 log10(P_task/P_baseline)`, for mu (8–13 Hz) and beta (13–30 Hz).
- Negative control: prior-probability dummy classifier.
- Primary model: median imputation, standardization, fold-local ANOVA feature selection, and class-weighted logistic regression.
- Comparator: CSP followed by shrinkage LDA.
- Comparator: Ledoit-Wolf covariance, Riemannian tangent space, scaling, and logistic regression.
- No deep-learning model is required or scientifically justified at this stage.

### Cross-validation and inference

- Five shuffled participant-disjoint outer folds and four participant-disjoint inner folds.
- Hyperparameters selected with inner-fold ROC-AUC.
- Primary summary is participant-mean balanced accuracy with participant bootstrap confidence intervals.
- Additional metrics: ROC-AUC, macro-F1, sensitivity, specificity, average precision, accuracy, and MCC.
- Optional within-participant label-swap permutation procedure, configured for 1,000 iterations but disabled by default.
- First-60-second cue events versus all cue events is correctly reframed as a duration sensitivity analysis.

### Outputs implemented

The notebook writes configuration, software versions, loading/rejection QC, exclusions, sampling verification, per-model OOF predictions, fold metrics, participant metrics, bootstrap summaries, feature stability, subgroup summaries, optional permutation results/null, and a ZIP archive. It does **not** currently export the required `fold_assignments.csv`, raw rejection/peak-to-peak distributions, movement- and participant-stratified rejection summaries, config snapshots per independent experiment, Git commit metadata, or run metadata.

## Strengths

- Run-based condition mapping and movement mapping are correct.
- Annotation-locked analysis replaces scientifically invalid whole-recording vectors.
- Participant-disjoint nested CV addresses the principal leakage problem.
- Scaling, selection, CSP, tangent-space fitting, and tuning are inside sklearn pipelines/folds.
- The primary outcome is participant-level and uncertainty is included.
- Interpretable ERD features and EEG-specific comparators replace a generic model zoo.
- Failed runs and exclusions are logged rather than silently dropped.
- Artifact contamination and deployment overclaiming are acknowledged.

## Weaknesses, bugs, and risks

### Critical scientific risks

1. **Condition is confounded with run order.** Every ME run immediately precedes its matched MI run (3→4, 5→6, etc.). Session drift, fatigue, habituation, impedance changes, or practice can therefore mimic an ME/MI effect. EEGMMIDB cannot identify a pure causal condition effect because order was not counterbalanced.
2. **ME has unavoidable movement contamination.** No dedicated EMG/EOG permits verification that discriminating signal is cortical. Peak-to-peak rejection alone cannot remove low-amplitude EMG or electrode movement.
3. **Complete-case selection may bias the cohort.** Requiring a surviving epoch in all 12 task runs may preferentially exclude high-artifact participants. Eligibility must be prespecified, reasons reported, and sensitivity to a less stringent rule considered before outcomes are viewed.
4. **Fixed canonical bands may obscure individual mu peaks.** Canonical bands are reproducible and suitable for the primary analysis, but an individual-alpha-frequency sensitivity analysis may be considered only if fully prespecified and estimable without test leakage.

### Implementation gaps or possible bugs

1. The notebook installs packages at runtime with broad version ranges and has no lock file; an exact rerun is not guaranteed.
2. Cache identity omits MNE/software versions, referencing order, resampling details, and code version, so stale caches could survive meaningful implementation changes.
3. The cache is a single large concatenated epochs file, limiting restartability and threshold sensitivity; participant/run-level caches would be safer.
4. `fold_assignments.csv` is not exported. Fold IDs appear only in predictions and fold metrics.
5. Subgroup metrics pool epochs rather than computing participant-level subgroup estimates and uncertainty; these are not valid final movement-specific inference.
6. The permutation function depends on the global observed `results["erd"]`, reducing modularity and risking mismatch if called with another dataset/configuration.
7. A fresh shuffled inner split is generated by fold, but the exact participant IDs are not retained, making tuning provenance harder to verify.
8. The participant bootstrap silently uses `nanmean`; the reason and frequency of undefined participant metrics should be explicit.
9. Participant metrics omit subjects lacking both classes after rejection. This can silently change the analysis population by metric.
10. Rejection logging provides counts but not epoch peak-to-peak distributions or movement/participant summaries required for artifact diagnosis.
11. No automated tests verify mapping, leakage boundaries, deterministic folds, finite features, output schema, or score validity.
12. The original reanalysis does not implement movement-specific retraining. Computing metrics on subsets of predictions from a model trained across movements answers a different question from movement-specific decoding.
13. Riemannian covariance is computed only on the 0.5–3.5 s task interval. This is a reasonable comparator, but it is not baseline-referenced and may be more vulnerable to stable nuisance covariance; interpretation must reflect this.
14. No explicit train-versus-test diagnostics or integrity checker catches suspicious performance, duplicate OOF rows, missing folds, or incomplete permutations.
15. The manuscript's bibliography contains unresolved `?` citations and no usable reference list.

## Manuscript–implementation inconsistencies

- The manuscript says 60/120-second windows and mixes baseline/task blocks; the reanalysis uses 5.5-second event-locked epochs.
- The manuscript says Mel features and ten generic models; the reanalysis uses ERD, CSP, and Riemannian features with three scientific models plus dummy.
- The manuscript implies effective discrimination and online/clinical relevance; its own results are near chance and the reanalysis has not produced full-cohort results.
- The manuscript describes a three-class rest/ME/MI analysis; the reanalysis addresses binary ME versus MI only.
- The manuscript's statement that each run contains baseline then execution then imagery is false. Execution versus imagery is defined by separate runs.
- The manuscript calls 60/120 seconds trial/window durations; the reanalysis correctly treats first-60-second event inclusion as sensitivity analysis.
- Claims of <20 ms processing and a 100–150 ms control loop are unsupported by reproducible benchmark outputs and irrelevant to an offline, multi-second epoch analysis.
- Claims about a single-subject calibration set, deployment readiness, rehabilitation benefit, and “high-stakes control” are unsupported.
- The PDF says five subjects had missing blocks, whereas no auditable cohort log or full reanalysis result was supplied.

## Redundant or historical work

The original Mel/model-zoo analysis should be preserved unchanged as historical exploratory work. It should not be the primary pipeline. If retained scientifically at all, it should be labelled exploratory/supplementary and rerun with participant-disjoint folds and fold-local transforms. The supplied Colab export should also be preserved as a historical prototype after modular code exists.

## Required pre-refactor resolutions

1. Obtain the actual repository and update this audit.
2. Freeze the eligibility rule, estimand, folds, model set, and artifact sensitivities before full results.
3. Decide whether the paper is framed as a rigorous robustness/heterogeneity study rather than a novel decoder; the novelty analysis recommends the former.
4. Treat run-order confounding as a fundamental limitation and add order/drift diagnostics without claiming they remove it.
5. Obtain scientific-plan approval before implementing the modular structure.

