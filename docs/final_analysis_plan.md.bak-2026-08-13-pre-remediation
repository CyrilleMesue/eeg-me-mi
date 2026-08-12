# Frozen analysis plan

Date frozen: 2026-08-12  
Last synchronized: 2026-08-12 (Milestone 2 — post Milestone-1 review)  
Status: prespecified main-analysis specification  
Scientific review: independent ChatGPT review in `docs/chatgpt_scientific_consultation.md`  
Prior version backup: `docs/final_analysis_plan.md.bak-2026-08-12-pre-m2`

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
- Matched pairs: 3↔4, 5↔6, 7↔8, 9↔10, 11↔12, 13↔14.
- Unilateral runs: T1 = left fist; T2 = right fist.
- Bilateral runs: T1 = both fists; T2 = both feet.
- T1/T2 never encode ME versus MI.
- Trial unit: annotation-locked T1/T2 event, not a whole recording.

## Primary eligibility (E01)

Eligibility is determined **after** the frozen primary 200 µV peak-to-peak
artifact procedure and **never** depends on classification performance.

A participant is eligible for primary E01 when all of the following hold:

1. No unrecoverable structural anomaly in the data actually used.
2. Only matched ME/MI run pairs where both members are valid are used.
3. ≥30 usable ME epochs and ≥30 usable MI epochs remain.
4. Retained data come from ≥2 matched run pairs.
5. Those pairs include ≥1 unilateral pair and ≥1 bilateral pair.
6. Within retained matched pairs, movement composition remains represented in
   both modes (the set of movements present in ME equals that in MI).

Unequal ME versus MI counts alone do **not** exclude a participant.

Also computed but not used to change the primary rule:

- eligibility at ≥20 epochs/mode;
- eligibility at ≥40 epochs/mode.

## Movement-specific eligibility (E02)

For each individual movement analysis (left fist, right fist, both fists, both
feet) and for pooled unilateral / bilateral analyses:

- ≥15 usable ME epochs for that analysis subset;
- ≥15 usable MI epochs for that analysis subset;
- observations from ≥2 matched repetitions (distinct matched pairs contributing
  to the subset).

A participant may be E01-eligible but E02-ineligible for a given movement.
The participant set is recorded separately for every E02 analysis.

## Strict sensitivity cohort

A participant enters the strict sensitivity cohort when:

1. all 12 task runs are structurally valid;
2. ≥40 retained epochs per mode (ME and MI);
3. ≥20 retained epochs per movement × mode cell
   (left_fist, right_fist, both_fists, both_feet × ME/MI);
4. ≥80% of expected observations retained in each relevant cell.

**Protocol consistency note.** Under EEGMMIDB, each task run typically yields
about 15 T1/T2 cues (~7–8 per movement). A movement×mode cell therefore has an
expected size of roughly 21–24 cues across three matched repetitions. The ≥20
and ≥80%-of-expected rules are jointly satisfiable for typical event counts
(when expected ≥25, both bind meaningfully; when expected is 21–24, ≥20 is
binding and implies ≥80%). If a recording’s annotation counts make expected
cell size &lt;20, that participant fails the strict rule by construction; this is
not a silent rule change.

## Frozen preprocessing

- EEGBCI-standardized channel names and `standard_1005` montage.
- Average reference calculated from available EEG channels.
- Resample to 80 Hz.
- Band-pass 8–30 Hz.
- Primary sensorimotor set: FC5/3/1/z/2/4/6, C5/3/1/z/2/4/6,
  CP5/3/1/z/2/4/6 (21 channels).
- Epoch: -2.0 to 3.5 s around T1/T2.
- Baseline / E00 window: -2.0 to -0.5 s.
- Task interval: 0.5 to 3.5 s.
- Primary gross-artifact screen: 200 µV peak-to-peak.
- Mandatory artifact sensitivities: 150 µV and no amplitude rejection.
- Participant-level caches; shared minimally processed caches support threshold
  sensitivity without reloading all raw EDFs.

The threshold is not selected using performance. It does not establish cortical
purity.

## Band-boundary rule

Welch bins: mu = `[8, 13)` Hz; beta = `[13, 30]` Hz. The 13 Hz edge belongs to
beta only (no double-counting).

## Primary hypothesis and endpoint

### H1

EEG recorded during ME and MI task runs contains reproducible differences that
support above-chance prediction in participants excluded from all training and
tuning under the EEGMMIDB protocol.

### Primary E01 model

42 channel×band ERD features
→ training-fold-only `StandardScaler`
→ L2 logistic regression
→ inner participant-disjoint tuning of `C ∈ {0.01, 0.1, 1, 10}`.

**No `SelectKBest` (or other supervised feature selection) in the primary
confirmatory pipeline.**

- Primary endpoint: mean of participant-level OOF balanced accuracies.
- Evaluation: nested participant-disjoint CV with identical outer folds across
  E00/E01 models where population-compatible; stored train/test participant IDs.
- Uncertainty: 2,000-replicate participant bootstrap 95% CI.
- Inferential support: 1,000 structured matched-pair permutations (E07) with
  plus-one p-value (final execution after Milestone 2 benchmarks).

A significant result means reproducible condition-associated information; it
does not resolve fixed order or movement-artifact confounding.

## E00 — pre-cue run-state decoding control

Mandatory negative/control analysis. Terminology: **pre-cue run-state decoding
control**. Do **not** describe E00 as a biologically neutral baseline.

- Window: −2.0 to −0.5 s (no post-cue samples in features).
- Features: 42 pre-cue log band-power features (mu/beta × 21 channels).
- Same eligible epochs/participants/outer folds/inner structure/scaler/LR/C
  grid/metrics/participant aggregation as E01 wherever scientifically applicable.

Interpretation (prespecified):

- E00 near chance and E01 above E00 is more compatible with event-related
  differentiation, without eliminating artifact/order confounding;
- E00 above chance demonstrates condition-associated run/session state before
  cue onset;
- similar E00 and E01 performance substantially weakens event-specific
  physiological interpretation.

## Required E01 models

1. Prior-probability DummyClassifier negative control.
2. Primary ERD + L2 logistic regression (above).
3. CSP + shrinkage LDA spatial comparator (fold-local CSP; small fixed
   parameterization; no large CSP search).
4. Covariance (shrinkage/Ledoit–Wolf as implemented) → Riemannian tangent space
   → regularized linear classifier (fold-local; e.g. pyRiemann).

No deep learning, FBCSP expansion, MDM zoo, domain adaptation, or source
localization is part of the frozen main study.

Secondary metrics: participant-mean ROC-AUC, macro-F1, sensitivity, specificity,
average precision, MCC, and accuracy. AUC uses continuous scores.

## Experiment matrix

| ID | Status | Analysis |
|---|---|---|
| E00 | Mandatory control | Pre-cue run-state decoding |
| E01 | Primary | ME/MI prediction + Dummy/ERD-LR/CSP-LDA/Riemann |
| E02 | Secondary | Movement-specific decoding |
| E03 | Secondary | Mu/beta ERD physiology, ROI summaries, lateralization |
| E04 | Exploratory | Participant heterogeneity and stability |
| E05 | Sensitivity | Artifact thresholds + spatial-plausibility control |
| E06 | Supplementary | First-60-s cue events vs all cue events |
| E07 | Inferential support | Structured matched-pair permutations (1,000 final) |
| E08 | Mandatory diagnostics | Fixed-order / drift characterization |

### E03 ROI summaries (prespecified)

- Left sensorimotor: FC3, C3, CP3
- Right sensorimotor: FC4, C4, CP4
- Midline: FCz, Cz, CPz

Plus 21-channel maps with FDR-corrected channel-level exploratory tests.
Scalp topography does not prove cortical purity.

### E05 spatial-plausibility control

A frozen non-sensorimotor/peripheral channel set of matched size (21), chosen
before inspecting control decoding results (see code `eeg_me_mi.rois`). Stronger
central than peripheral decoding supports sensorimotor plausibility; similar
performance raises concern for global state/artifact information; neither proves
cortical origin.

### E07 permutation structure

For each participant and each available matched run pair, randomly swap or keep
ME/MI labels for the **entire** pair. Do not independently permute epochs.
Preserves participant clustering, movement family, repetition, and within-run
epochs. **Does not** eliminate the fixed ME-before-MI order confound.
Exchangeability is under the observed fixed-order protocol only.

## Compute policy

- **Local machine is the default environment.**
- **TRUBA is reserved** for empirically long-running jobs (especially final E07
  1,000 permutations or other jobs whose benchmark warrants HPC), even when a
  long local run is technically feasible.

## Leakage controls

Outer-test participants cannot influence scaling, CSP, covariance/tangent
reference, hyperparameters, thresholds, or model choice. Inner CV contains
training participants only. Automated tests audit learned transforms. Outer
folds are generated once for the primary cohort and reused wherever
population-compatible.

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

Primary analyses may not be changed in response to outcomes.
