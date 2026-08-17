# Publication figure caption drafts

Technical captions only. No Discussion language. Freeze: `analysis-complete-pre-manuscript` (`6d0ce7a`).

---

## Figure 1. Study design and analysis framework

**(A)** Matched PhysioNet EEGMMIDB motor execution (ME) and motor imagery (MI) run pairs used in this study. ME precedes the corresponding MI run in each matched pair; condition is therefore structurally coupled to run order (not randomized or counterbalanced).  
**(B)** Participant-disjoint nested cross-validation schematic: outer training participants, inner participant-disjoint tuning, and completely held-out outer-test participants. No participant contributes epochs to both training and outer test within a fold.  
**(C)** FIR-safe temporal windows relative to cue onset (t = 0): E00 pre-cue power (−2.0 to −0.8375 s); cue-adjacent exclusion (−0.8375 to +0.8375 s); E01 baseline (−2.0 to −0.8375 s) and task (+0.8375 to +3.5 s).  
**(D)** Primary feature representation: 21 sensorimotor electrodes × μ (8–13 Hz) and β (13–30 Hz) ERD features (42 dimensions) entered into nested logistic regression yielding participant-level predictions and participant-mean balanced accuracy (BAcc).  
**(E)** Analysis/control logic connecting primary decoding to pre-cue, physiology, movement-specific, spatial, artifact, duration, sampling-rate, run-order, and structured-permutation interrogations.

---

## Figure 2. Primary cross-participant decoding

**(A)** Participant-level E01 ERD-LR balanced accuracy (N = 102). Chance = 0.50. Mean participant BAcc = 0.618 with 95% participant-bootstrap confidence interval [0.604, 0.633]. All participants are shown, including those below chance.  
**(B)** Participant-mean BAcc for Dummy, CSP-LDA, Riemannian-LR, and primary ERD-LR under the same nested participant-disjoint CV. Error bars are 95% participant-bootstrap CIs. This panel is a same-pipeline comparator display, not a classifier leaderboard.  
**(C)** Distribution of 1,000 E07 structured-permutation null statistics of participant-mean BAcc. Vertical line: observed statistic = 0.617924 (identical to primary E01). 0/1000 null values ≥ observed; plus-one p = 0.000999.  
**(D)** Primary-model secondary metrics from the frozen E01 summary (ROC-AUC, Macro-F1, sensitivity, specificity, MCC). BAcc is the primary endpoint; other metrics are descriptive.

---

## Figure 3. Pre-cue versus post-cue information

**(A)** Schematic contrasting E00 pre-cue absolute μ/β power and E01 post-cue ERD relative to the FIR-safe baseline.  
**(B)** Paired participant performance for E00 and E01 on the common N = 102 participants (chance = 0.50). Summary means: E00 ≈ 0.539; E01 ≈ 0.618 (exact values in source data / annotations).  
**(C)** Participant-level ΔBAcc = E01 − E00 with zero reference. Mean Δ ≈ +0.079; 95% bootstrap CI approximately [0.066, 0.092]; paired sign-flip / randomization p ≈ 0.0005 (exact frozen values in `Figure_3_annotations.json`). Pre-cue ME/MI-associated information is present, and post-cue ERD adds substantial additional information under the frozen comparison.

---

## Figure 4. Physiology and spatial evidence

**(A)** Prespecified 21 sensorimotor electrodes on a standard scalp layout, colored by left, midline, and right ROIs. Layout is sensor-space only and does not imply cortical source localization.  
**(B)** Six prespecified ROI ME−MI ERD effects (μ/β × left/midline/right): mean dB effect with 95% bootstrap CI; zero line shown. Negative values indicate stronger ERD in ME than MI. FDR rejection marked from the frozen ROI summary.  
**(C)** Channel-level supporting μ and β ME−MI maps from frozen channel summaries. These are scalp-channel difference maps, not cortical activation maps.  
**(D)** Movement-specific participant-mean BAcc (left fist, right fist, both fists, both feet, unilateral pooled, bilateral pooled) with 95% bootstrap CIs and cohort N; chance = 0.50.  
**(E)** Spatial representation control comparing sensorimotor features versus the prespecified peripheral/non-sensorimotor control among participants available for paired comparison (paired N = 77). Spatial-control cohort BAcc = 0.584 (95% CI [0.571, 0.597], N = 78). Mean SM − SC Δ = 0.038 (95% CI [0.025, 0.052]). No confirmatory paired p-value is reported. Sensorimotor features showed higher participant-mean BAcc than the peripheral control in the paired subset.

---

## Figure 5. Robustness and protocol-state diagnostics

**(A)** Artifact peak-to-peak threshold sensitivity: no rejection (N = 109), 150 µV (N = 94), and 200 µV primary (N = 102), with participant-mean BAcc and 95% bootstrap CIs. Cohorts are not identical. Exact BAcc: 0.618568 / 0.616887 / 0.617924.  
**(B)** Additional sensitivity analyses from frozen review/final packages (strict cohort, first 60 s, all events, sampling-rate exclusion of S088/S092/S100 with N = 99, BAcc ≈ 0.6209, 95% CI ≈ [0.6068, 0.6355]). Primary reference indicated.  
**(C)** Label-specific 200 µV rejection for the primary cohort: ME ≈ 7.27% rejected (retained 8,448); MI ≈ 6.47% rejected (retained 8,492). Participant-level mean ME−MI rejection difference ≈ 0.82 percentage points with 95% bootstrap CI approximately [−0.53, +2.19] pp (exact frozen values in source JSON).  
**(D)** Fixed matched-pair ME → MI run order (diagnostic context for E08).  
**(E)** Prespecified pre-cue β run-state diagnostic by matched ME/MI pairs from frozen E08 outputs. Labeled diagnostic — does not remove fixed-order confounding.

---

## Supplementary captions (short)

**Figure S1.** Cohort/eligibility overview from frozen eligibility counts (audited → primary eligible → primary analysis).  

**Figure S2.** Full secondary classification metrics for Dummy, CSP-LDA, Riemannian-LR, and ERD-LR from frozen E01 summaries (descriptive; BAcc primary).  

**Figure S3.** Participant-level BAcc distributions for the four E01 models (chance = 0.50).  

**Figure S4.** Participant-level BAcc histograms for E02 movement-specific cohorts (N annotated per panel; chance = 0.50).  

**Figure S5.** Channel-level μ and β ME−MI ERD effects from frozen FDR channel summary.  

**Figure S6.** Participant-level laterality (ME − MI) by band and movement from frozen E03 laterality table. Secondary; effects are heterogeneous.  

**Figure S7.** Participant heterogeneity rank plot and exploratory correlation table from frozen E04 review outputs. Labeled EXPLORATORY.  

**Figure S8.** Participant BAcc distributions across artifact-threshold cohorts (none / 150 µV / 200 µV).  

**Figure S9.** Expanded label-specific rejection audit by condition and by movement × condition (primary cohort).  

**Figure S10.** Expanded E08 run diagnostics (pre-cue μ, pre-cue β, PTP by run and condition). Diagnostic only.  

**Figure S11.** Sampling-rate sensitivity excluding S088/S092/S100 (N = 99) versus primary (N = 102), with participant distribution for the sensitivity cohort.
