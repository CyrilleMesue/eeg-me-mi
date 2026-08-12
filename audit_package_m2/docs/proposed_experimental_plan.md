# Proposed experimental plan

Date: 2026-08-12  
Status: **for scientific review; no refactor or full computation authorized yet**

## Scientific objective

Determine whether physiologically interpretable ME-versus-MI EEG differences are stable enough to generalize to unseen EEGMMIDB participants, how they vary by movement and participant, and whether they survive prespecified artifact and analytic sensitivities.

## Hypotheses and estimands

### Primary hypothesis H1

ME and MI contain distinguishable event-related EEG signatures that generalize to participants excluded from training and tuning.

- **Primary model:** baseline-referenced channel-wise mu/beta ERD + fold-local selection + logistic regression.
- **Primary endpoint:** mean of participant-level balanced accuracies from OOF predictions under nested participant-disjoint CV.
- **Primary null:** no generalizable ME/MI association under within-participant condition-label exchangeability.
- **Primary inference:** 95% participant bootstrap CI and a 1,000-iteration group-aware permutation p-value.
- **Success interpretation:** evidence requires the prespecified permutation result and uncertainty to support above-chance performance; effect magnitude and clinical usefulness remain separate questions.

### Secondary hypotheses

- **H2:** ME and MI differ in baseline-referenced mu and beta ERD magnitude/spatial distribution over FC/C/CP electrodes, with participant-consistent effects.
- **H3:** ME/MI separability and ERD contrast depend on movement (left fist, right fist, both fists, both feet; planned unilateral/bilateral contrasts).
- **H2a lateralization:** For unilateral fist movement, condition differences in contralateral-versus-ipsilateral sensorimotor ERD/laterality are movement-side dependent. Directional claims will be finalized only after literature review of the exact laterality index.

### Exploratory questions

- **H4:** Are OOF participant decoding outcomes associated with a small prespecified set of baseline power, ERD magnitude, laterality, within-participant variability, rejection rate, and retained-epoch count measures?
- **H5:** How similar are participant-level ME and MI spatial ERD patterns across bands and movements?
- Which participants/movements are most sensitive to amplitude rejection?

H4/H5 will be explicitly labelled exploratory; no causal or biomarker claims will be made.

## Cohort and trial definition

- Attempt subjects 1–109 and runs 3–14.
- ME: 3, 5, 7, 9, 11, 13. MI: 4, 6, 8, 10, 12, 14.
- Unilateral T1/T2: left/right fist. Bilateral T1/T2: both fists/both feet.
- Trial: T1/T2 annotation-locked epoch, not an entire recording.
- Proposed primary epoch: -2.0 to 3.5 s; baseline -2.0 to -0.5 s; task 0.5 to 3.5 s.
- Proposed primary preprocessing: standardized names, standard montage, average reference, 80 Hz, 8–30 Hz, 21 FC/C/CP channels.
- Proposed primary rejection threshold: 200 µV **for continuity with the current plan, not because it performs best**. No threshold and 150 µV are mandatory sensitivities.

### Eligibility decision required before outcomes

The current complete-case rule requires at least one retained epoch in every run. Proposed alternative: include a participant in the primary cohort if both conditions and all four movements remain represented with a prespecified minimum number of trials, while logging missing runs; use strict complete-case as sensitivity. This may reduce selection bias but changes the current notebook. The final rule and minimum count must be approved before full analysis.

## Leakage-safe evaluation

1. Generate one deterministic set of outer participant folds and reuse it for every model and compatible sensitivity.
2. Store outer and inner participant IDs in `fold_assignments.csv`/tuning provenance.
3. Fit imputation, scaling, feature selection, CSP, covariance/tangent reference, hyperparameters, and any learned threshold using training participants only.
4. Inner CV contains training participants only.
5. Never use outer-test participants for preprocessing choice, model choice, or decision threshold.
6. Where movement-specific datasets have missing participants, preserve the fold assignment and report the changed analysis population.
7. Add unit/integration tests that deliberately fail on participant overlap and supervised pre-fit transforms.

## Models

| Role | Model | Rationale |
|---|---|---|
| Negative control | Prior-probability dummy | Verifies metric/export behavior; not the inferential null by itself |
| Primary/interpretable | Mu/beta ERD, fold-local ANOVA selection, regularized balanced logistic regression | Directly links decoding to sensorimotor physiology |
| Spatial comparator | CSP + shrinkage LDA | Established discriminative spatial-filter baseline |
| Covariance comparator | Ledoit-Wolf covariance → Riemannian tangent space → regularized linear classifier | Established covariance-geometric representation |

MDM is optional and should be included only if framed as a parameter-light Riemannian comparator; it is not needed for novelty. No deep learning, domain adaptation, or model zoo is proposed.

Hyperparameter grids will be minimal and prespecified. All models use identical outer folds. Model comparisons are paired at participant level and secondary; “winner” language is discouraged.

## Experiments

### E01 Primary generalization

Full eligible cohort, four required models, nested participant-disjoint CV, OOF predictions, participant bootstrap, paired model contrasts.

### E02 Movement-specific decoding

Retrain and evaluate the primary model separately for left fist, right fist, both fists, both feet, unilateral, and bilateral subsets. Do not substitute subgroup scoring of a pooled-movement model. Use the same outer participant assignment.

### E03 Physiology and lateralization

- Participant-level ME-minus-MI ERD for each channel, band, and movement.
- Primary physiological summaries over prespecified central left/right ROIs; channel-wise maps are multiplicity-controlled.
- Mixed-effects or participant-level repeated-measures analysis for condition, band/hemisphere, and movement, with participant as the repeated unit.
- Effect sizes, bootstrap/compatible CIs, exact n, and FDR-corrected channel-level tests.
- Validate sign conventions: negative ERD/ERS dB denotes desynchronization; more negative means stronger ERD.

### E04 Participant heterogeneity (exploratory)

- Derive participant OOF metrics from E01 only.
- Limit predictors to a prespecified small set or reduce them into theoretically defined composites.
- Report rank correlations/regularized associations with bootstrap CIs and FDR correction.
- Check influence and measurement reliability; avoid interpreting performance correlates as causes.

### E05 Artifact sensitivity

- Recreate epochs at none, 150 µV, and 200 µV from shared minimally processed caches.
- Report peak-to-peak distributions and rejection by condition, movement, run, and participant.
- Repeat E01 primary model and key E03 summaries at each threshold.
- Compare effect-map correlation, participant-rank correlation, cohort changes, and paired performance differences.
- Add diagnostic contrasts using central-only versus peripheral/non-sensorimotor channels if scientifically approved. Such diagnostics cannot prove cortical origin.

### E06 Duration sensitivity

Compare events with cue onset before 60 s against all events using the identical primary pipeline and participant folds. Label this correctly; these are not 60-s versus 120-s EEG epochs.

### E07 Permutation inference

Archive the complete 1,000-iteration null distribution. The permutation scheme will be verified by simulation before TRUBA. A local 5–20 permutation run tests code only.

### Order/drift diagnostic (required sensitivity)

Because run condition is fixed-order, quantify pre-cue baseline power and QC drift by run index/repetition; repeat analyses within matched adjacent run pairs where possible; test condition×repetition stability; and state clearly that these diagnostics cannot deconfound condition from order.

## Statistical plan

- Primary unit of inference: participant.
- Primary interval: 2,000-replicate participant bootstrap, resampling participants with all their OOF trials.
- Primary permutation: 1,000 group-aware condition swaps; plus-one p-value.
- Secondary model contrasts: paired participant differences with bootstrap CIs; multiplicity adjustment across the three primary-model comparator contrasts.
- Movement analysis: planned omnibus condition×movement test before movement-specific follow-ups; correct follow-ups for multiplicity.
- Channel maps: FDR within prespecified band/movement families, accompanied by unthresholded effect maps and CIs.
- Heterogeneity: exploratory FDR and stability/influence reporting.
- Always report effect size, CI, exact participant/epoch counts, and missingness. P-values alone are insufficient.
- Do not infer success from epoch-pooled accuracy or outer-fold means alone.

The exact permutation exchangeability assumption needs one final statistical review: condition labels are tied to fixed run order, so permutation tests association under the observed protocol but do not create an unconfounded causal condition test.

## Sensitivity analyses

Prespecified:

- amplitude rejection: none, 150 µV, 200 µV;
- first-60-second cue events versus all events;
- strict complete-case versus approved minimum-data eligibility rule;
- adjacent-pair/repetition and baseline-drift diagnostics;
- model representation (ERD, CSP, tangent space), with ERD remaining primary.

Possible but not yet approved:

- individual-mu-frequency sensitivity estimated without outer-test leakage;
- alternative reference or task window;
- MDM comparator.

These must not be selected based on favorable final accuracy.

## Required validation gates

Before TRUBA pilot, a 4–8-participant local toy run must assert:

- correct ME/MI and unilateral/bilateral mappings;
- no participant overlap in outer or inner folds;
- fold-local learned transforms;
- 80 Hz and exact channel set;
- finite features and valid scores;
- deterministic assignments/outputs;
- complete required schemas;
- no duplicate/missing OOF predictions;
- threshold-specific cache identity;
- correct bootstrap and permutation behavior on synthetic null/signal data.

Full TRUBA execution remains prohibited until toy and pilot gates pass.

## Expected figures

1. Study design, run mapping, and participant-disjoint nested workflow, including fixed-order caveat.
2. Participant-level mu/beta ME-minus-MI topographies with movement panels.
3. Primary participant OOF balanced-accuracy distributions and 95% CIs for four models.
4. Movement-specific participant distributions/effect estimates.
5. Participant heterogeneity and prespecified QC/physiology associations (exploratory).
6. Artifact-threshold robustness: rejection, performance/effect stability, and participant-rank changes.

## Expected tables

1. Dataset, exclusions, retained participants/epochs, movement counts, and rejection QC.
2. Primary model participant-mean metrics, CIs, and paired contrasts.
3. Movement-specific decoding and physiological contrasts.
4. Artifact, duration, eligibility, and order/drift sensitivities.

All figures/tables must be generated from machine-readable outputs.

## Output requirements

At minimum: fold assignments (outer and inner), OOF predictions, fold/participant metrics, bootstrap draws or sufficient summaries, selected features, loading/rejection QC, peak-to-peak summaries, exclusions with reasons, sampling verification, permutation statistic and full null, configs, seeds, software/environment versions, Git commit, input/cache identity, and integrity-check report.

## Computational requirements (planning estimates)

- Dataset: 109 × 12 = 1,308 task EDFs, likely several GB; download once to persistent shared storage.
- Epoch cache: prefer per-subject/run minimally processed artifacts so rejection sensitivities do not duplicate EDFs or force complete re-downloads.
- E01 ERD is modest CPU/RAM; CSP and covariance models require profiling because nested grids over all epochs can be memory-heavy.
- E05 multiplies preprocessing/evaluation by three thresholds, but should reuse minimally processed inputs.
- E07 is dominant: 1,000 complete nested primary-model fits; parallelize restartable permutation batches with deterministic permutation IDs, then combine and integrity-check.
- Exact SLURM CPU/RAM/time requests will be determined only after local toy and TRUBA pilot profiling.

## Decision framework after results

- If primary CI and permutation inference support above-chance generalization and artifact sensitivities are stable: claim modest, protocol-specific unseen-participant separability, not clinical utility or cortical purity.
- If performance is above chance but artifact/order diagnostics are unstable: emphasize confounding and refrain from physiological attribution.
- If inference does not support above-chance generalization: report that reliable unseen-participant decoding was not demonstrated; physiology may still show participant-level condition contrasts.
- Negative movement or heterogeneity results remain valid and will not trigger uncontrolled model searching.

## Review decisions requested

1. Approve the integrated robustness/heterogeneity framing as the intended contribution.
2. Choose and freeze the primary cohort eligibility rule before outcomes.
3. Approve 200 µV as the primary threshold with none/150 µV sensitivities, or choose another primary threshold for non-performance reasons.
4. Confirm whether H2 physiology is co-primary or secondary; this affects multiplicity and manuscript emphasis.
5. Approve the order/drift diagnostic as mandatory while accepting that it cannot remove the fixed-order limitation.

