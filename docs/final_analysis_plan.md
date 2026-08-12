# Frozen analysis plan

Date frozen: 2026-08-12  
Status: prespecified main-analysis specification  
Scientific review: independent ChatGPT review in `docs/chatgpt_scientific_consultation.md`

## Scope and claim

This study is a participant-disjoint, physiology-linked assessment of how reliably
EEG recorded during motor-execution (ME) and motor-imagery (MI) runs can be
distinguished in unseen EEGMMIDB participants, how the distinction varies across
movements, and how sensitive it is to artifact handling and the database's fixed
task order.

The design estimates reproducible **condition-associated prediction under the
EEGMMIDB protocol**. It does not identify a causal, purely cortical effect of ME
versus MI because every matched ME run precedes its MI run and executed movement
can introduce EMG, electrode-motion, and other physical artifacts.

## Protocol definitions

- Participants attempted: EEGMMIDB subjects 1–109.
- Task runs: 3–14.
- ME runs: 3, 5, 7, 9, 11, 13.
- MI runs: 4, 6, 8, 10, 12, 14.
- Unilateral runs: T1 = left fist; T2 = right fist.
- Bilateral runs: T1 = both fists; T2 = both feet.
- T1/T2 never encode ME versus MI.
- Trial unit: annotation-locked T1/T2 event, not a whole recording.

## Frozen cohort rule

Primary eligibility is independent of classification performance and determined
from file/channel/annotation usability before amplitude-threshold rejection.

A participant is eligible when:

1. required sensorimotor EEG channels and valid T1/T2 task annotations are
   available;
2. at least two of three repetitions are usable for each of ME-unilateral,
   MI-unilateral, ME-bilateral, and MI-bilateral; and
3. after the primary 200 µV rejection step, both ME and MI retain at least one
   trial of every movement required for participant-level primary metrics.

Every failure is logged per run and participant. Eligibility never depends on
model accuracy. Requiring all 12 task runs is a prespecified sensitivity cohort.

## Frozen preprocessing

- EEGBCI-standardized channel names and `standard_1005` montage.
- Average reference calculated from available EEG channels.
- Resample to 80 Hz.
- Band-pass 8–30 Hz.
- Primary sensorimotor set: FC5/3/1/z/2/4/6, C5/3/1/z/2/4/6,
  CP5/3/1/z/2/4/6.
- Epoch: -2.0 to 3.5 s around T1/T2.
- Baseline: -2.0 to -0.5 s.
- Task interval: 0.5 to 3.5 s.
- Primary gross-artifact screen: 200 µV peak-to-peak.
- Mandatory artifact sensitivities: 150 µV and no amplitude rejection.

The threshold is not selected using performance. It does not establish cortical
purity. Rejection and cohort changes are reported by condition, movement, run,
and participant.

## Primary hypothesis and endpoint

### H1

EEG recorded during ME and MI task runs contains reproducible differences that
support above-chance prediction in participants excluded from all training and
tuning under the EEGMMIDB protocol.

- Primary model: channel-wise mu/beta ERD, training-fold-only feature selection,
  imputation and scaling, and class-balanced regularized logistic regression.
- Primary endpoint: mean of participant-level OOF balanced accuracies.
- Evaluation: nested participant-disjoint CV with identical outer folds across
  models and stored train/test participant IDs.
- Uncertainty: 2,000-replicate participant bootstrap 95% CI.
- Inferential support: 1,000 group-aware permutations with plus-one p-value.
- A significant result means reproducible condition-associated information; it
  does not resolve fixed order or movement-artifact confounding.

## Mandatory protocol-confound negative control (E00)

Before interpreting task-period decoding, fit a participant-disjoint classifier
using only pre-cue baseline information from -2.0 to -0.5 s.

- Required representation: channel-wise baseline mu/beta log power with the same
  fold-local ERD-model pipeline and outer folds.
- Optional, if toy profiling is inexpensive: baseline covariance/tangent-space
  classifier.
- Endpoint and bootstrap match E01.
- A small group-aware permutation run validates code locally; full inference is
  run when computationally feasible and otherwise reported descriptively with CI.

Interpretation is prespecified:

- baseline near chance and task above baseline is more compatible with
  event-related differentiation, without eliminating artifact/order confounding;
- baseline above chance demonstrates condition-associated run/session state
  before cue onset;
- similar baseline and task performance substantially weakens event-specific
  physiological interpretation.

## Required models (E01)

1. Prior-probability dummy negative control.
2. Primary ERD + logistic regression.
3. CSP + shrinkage LDA spatial comparator.
4. Ledoit-Wolf covariance, Riemannian tangent space, and regularized linear
   classifier.

No deep learning, FBCSP expansion, MDM, domain adaptation, source localization,
or model zoo is part of the frozen main study.

Secondary metrics are participant-mean ROC-AUC, macro-F1, sensitivity,
specificity, average precision, MCC, and accuracy. AUC uses continuous scores.
Model comparisons are paired participant-level secondary analyses with correction
across the three primary-model contrasts.

## Secondary analyses

### E02 — Movement-specific decoding

Retrain the primary pipeline separately for left fist, right fist, both fists,
both feet, unilateral, and bilateral data. Preserve the deterministic outer
participant assignment. Use an omnibus movement comparison before corrected
movement-specific follow-ups.

### E03 — ERD physiology and lateralization

ERD is secondary, not co-primary. Compute

`10 log10(P_task / P_baseline)`

for mu (8–13 Hz) and beta (13–30 Hz) at every retained sensorimotor channel.
Analyze participant-level ME-minus-MI effects, movement, hemisphere, and
unilateral laterality. Report effect sizes, CIs, exact n, unthresholded maps, and
FDR-corrected channel-level tests. Negative values denote desynchronization.

## Sensitivity analyses

### E05 — Artifact and spatial-plausibility sensitivity

- Repeat the primary model and key E03 summaries at no rejection, 150 µV, and
  200 µV from shared minimally processed caches.
- Compare rejection, cohort composition, performance differences, effect-map
  correlations, and participant-rank stability.
- Compare a prespecified central sensorimotor set with a prespecified
  non-sensorimotor/peripheral set as a diagnostic. This cannot prove artifact
  removal or cortical origin.

### Eligibility sensitivity

Repeat the primary analysis in the strict all-12-task-run complete-case cohort.

### Fixed-order and drift diagnostics

- E00 pre-cue baseline-only decoding.
- Pre-cue mu/beta power and peak-to-peak trends by absolute run index.
- Repetition trends within each task family.
- Adjacent ME/MI pair summaries for 3/4, 5/6, 7/8, 9/10, 11/12, and 13/14.
- Condition-by-repetition stability.

These diagnostics characterize but cannot remove the structural confound.

### E06 — Duration sensitivity (supplementary)

Compare cue events occurring before 60 s with all cue events using the same
pipeline. Do not describe this as 60-s versus 120-s EEG epochs.

## Exploratory analysis (E04)

Participant heterogeneity is not headline novelty. Mandatory descriptive output:

- participant OOF metric distributions and ranges;
- stability of participant ranks across models, movements, and artifact
  thresholds;
- movement-specific participant variation.

Exploratory associations are restricted to mean ERD magnitude, baseline mu/beta
power, laterality, rejection rate, retained-trial count, and within-participant
variability. Use rank associations with bootstrap CIs and exploratory FDR.
Associations involving ERD-model accuracy and ERD magnitude are partly mechanical
and cannot be interpreted as biological causes.

Representational similarity is optional supplementary work only if final primary
results create a clear scientific need. Any such addition is labelled post-hoc.

## Leakage controls

Outer-test participants cannot influence imputation, scaling, feature selection,
CSP, covariance/tangent reference, hyperparameters, thresholds, or model choice.
Inner CV contains training participants only. Automated tests deliberately audit
every learned transform. Outer folds are generated once, reused wherever the
population permits, and exported with participant IDs.

## Statistical hierarchy

- Inference unit: participant.
- Primary endpoint/test: H1 ERD-LR participant-mean balanced accuracy, bootstrap
  CI, and 1,000-permutation group-aware null.
- Secondary: model contrasts, movement decoding, and E03 physiology.
- Sensitivity: E00, thresholds, eligibility, fixed-order/drift, E06.
- Exploratory: E04 and any later representational-similarity work.

Permutation exchangeability is interpreted under the observed fixed-order
protocol only. All later additions are marked sensitivity, exploratory, or
post-hoc; none becomes retrospectively prespecified.

## Required machine-readable outputs

At minimum: `fold_assignments.csv`, inner-fold provenance,
`oof_predictions_*.csv`, `outer_fold_metrics.csv`, `participant_metrics.csv`,
`participant_bootstrap_summary.csv`, bootstrap draws, `selected_features.csv`,
`loading_and_rejection_qc.csv`, `rejection_summary_by_condition.csv`,
peak-to-peak summaries, `excluded_participants.csv`,
`sampling_rate_verification.csv`, `permutation_test.csv`, the complete null
distribution, config snapshot, software versions, Git commit, cache/input
identity, run metadata, and integrity report.

## Validation and execution gates

The identical scientific code path must complete locally on 4–8 participants,
including all models, bootstrap, small permutation test, statistics, figures,
and exports. Automated tests must cover mappings, group separation, fold-local
transforms, channels, sampling, finite features, deterministic outputs, valid
scores, schemas, and cache integrity. Full TRUBA execution is prohibited until
the local toy and TRUBA pilot both pass and their expected outputs are validated.

## Frozen claim discipline

Permitted when supported:

> EEG recorded during execution and imagery runs contained reproducible
> information that generalized to unseen participants under the EEGMMIDB
> protocol.

Conditional on ERD/topographic/robustness results:

> The discriminative information was associated with sensorimotor mu/beta
> differences.

Never claim that the study isolated neural differences caused by ME versus MI,
proved cortical purity, demonstrated online/calibration-free BCI readiness,
clinical utility, rehabilitation effectiveness, or real-time deployment.

## Frozen experiment matrix

| ID | Status | Analysis |
|---|---|---|
| E00 | Mandatory sensitivity/negative control | Pre-cue baseline-only decoding |
| E01 | Primary | Participant-disjoint ME/MI prediction and model comparison |
| E02 | Secondary | Movement-specific decoding |
| E03 | Secondary | Mu/beta ERD, spatial effects, and lateralization |
| E04 | Exploratory | Participant heterogeneity and stability |
| E05 | Sensitivity | Artifact thresholds and spatial plausibility |
| E06 | Supplementary sensitivity | First-60-s events versus all events |
| E07 | Primary inferential support | 1,000 group-aware permutations |
| E08 | Mandatory sensitivity | Fixed-order, repetition, and drift diagnostics |

This file supersedes the review-stage status in
`docs/proposed_experimental_plan.md`. Primary analyses may not be changed in
response to outcomes.
