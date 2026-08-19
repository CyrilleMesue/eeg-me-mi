# Publication figures V2 — captions

Freeze: `analysis-complete-pre-manuscript` (`6d0ce7a`). Captions carry detail removed from the graphics. No causal claims.

---

## Figure 1. Design and safeguards

**(A)** Matched EEGMMIDB ME→MI run pairs used in this study (runs 3–14). Matched ME runs precede corresponding MI runs (fixed ME→MI ordering). Movement-family labels indicate L/R fist versus both-fists/feet structure. Condition is structurally coupled to run order (not randomized).  
**(B)** FIR-safe temporal windows relative to cue onset (t = 0): safe pre-cue (−2.0 to −0.8375 s), cue-adjacent excluded region (−0.8375 to +0.8375 s), and post-cue task (+0.8375 to +3.5 s). E00 uses pre-cue absolute μ/β power; E01 uses pre-cue baseline and post-cue ERD.  
**(C)** Primary analysis pipeline: 21 sensorimotor channels × μ + β = 42 ERD features, nested participant-disjoint cross-validation, held-out participants, participant-level metrics, and participant-mean balanced accuracy (BAcc). No participant contributes epochs to both training and outer test within a fold.

---

## Figure 2. Cross-participant decoding

**(A)** Participant-level E01 ERD-LR balanced accuracy (N = 102). Chance = 0.50. Mean participant BAcc = 0.617924 with 95% participant-bootstrap CI [0.603553, 0.632899]. All participants are shown, including those below chance.  
**(B)** Prespecified model comparators under the same nested participant-disjoint CV (Dummy, CSP-LDA, Riemannian-LR, ERD-LR primary). Points show participant-mean BAcc; whiskers are 95% participant-bootstrap CIs. Chance = 0.50. Display is descriptive; no formal superiority test is claimed.  
**(C)** E07 structured-permutation null distribution (1,000 permutations) of participant-mean BAcc. Vertical line: observed statistic = 0.617924 (identical to primary E01). 0/1000 null values ≥ observed; plus-one p = 0.000999.

---

## Figure 3. Pre-cue versus post-cue information

**(A)** Compact reminder of E00 (pre-cue absolute μ/β power) versus E01 (baseline → post-cue ERD) using FIR-safe windows.  
**(B)** Participant-level BAcc distributions for E00 and E01 on the common N = 102 participants (chance = 0.50). Means with 95% participant-bootstrap CIs: E00 = 0.539019 [0.528088, 0.549952]; E01 = 0.617924 [0.603553, 0.632899].  
**(C)** Participant-level ΔBAcc = E01 − E00 with zero reference. Mean Δ = 0.078905; 95% bootstrap CI [0.065574, 0.092283]; two-sided paired sign-flip plus-one p = 0.000500 (exact frozen value 0.00049975…). Count of participants with Δ > 0 is a descriptive tally from the frozen paired table (86/102). Pre-cue ME/MI-associated information is present; post-cue ERD adds substantial additional information under this frozen comparison.

---

## Figure 4. Sensorimotor physiology and spatial specificity

**(A)** Six prespecified ROI ME−MI ERD effects (μ/β × left/midline/right): mean dB effect with 95% bootstrap CI; zero line shown. Negative values indicate stronger ERD during ME than MI. All six effects meet the frozen FDR criterion (q < 0.05).  
**(B)** Channel-level μ and β ME−MI scalp topographies from frozen channel summaries on standard electrode positions (sensor-space maps; not cortical source localization). Shared diverging scale; colorbar in dB.  
**(C)** Spatial representation control among participants available for paired comparison (N = 77). **C1:** participant-level BAcc distributions for sensorimotor versus peripheral/non-sensorimotor features (chance = 0.50). **C2:** participant-level paired differences ΔBAcc = sensorimotor BAcc − peripheral-control BAcc, with zero reference; mean Δ = 0.038235; 95% bootstrap CI [0.024501, 0.052142]. No confirmatory paired p-value. Peripheral channels contain ME/MI-associated information; sensorimotor features show additional discriminative information in the paired subset. Spatial-control cohort BAcc = 0.583815 (95% CI [0.570681, 0.596700], N = 78).

---

## Figure 5. Robustness and protocol-state diagnostics

**(A)** Robustness forest of frozen participant-mean BAcc (±95% bootstrap CI where available) across primary, artifact-threshold, strict, duration, and sampling-rate sensitivity analyses (N annotated). Near-identical estimates indicate stability across these analytical choices.  
**(B)** Fixed-order protocol-state diagnostic: pre-cue beta power (µV²; exact V²→µV² display conversion) for each matched ME→MI run pair (03–04 … 13–14). Bars compare ME versus MI within each pair. This diagnostic characterizes systematic pre-cue/run-state differences associated with the fixed ME→MI ordering but does **not** remove the fixed-order confound.

---

## Supplementary captions (short)

**S1.** Cohort eligibility overview from frozen QC counts.  
**S2.** Primary-model secondary metrics (exact frozen values). Prefer **Table 2** for manuscript presentation.  
**S3.** Movement-specific participant BAcc distributions (E02; N and bootstrap mean/CI per movement).  
**S4.** Channel-level μ/β ME−MI ERD forest plots from frozen FDR channel summary.  
**S5.** Participant-level laterality (ME − MI) by band and movement (secondary; heterogeneous).  
**S6.** Participant heterogeneity ranks and exploratory correlations (EXPLORATORY).  
**S7.** Artifact-threshold participant BAcc distributions (none / 150 µV / 200 µV).  
**S8.** Label-specific rejection audit: aggregate ME/MI rejection and participant-paired rejection-rate differences (primary cohort; retained ME = 8448, MI = 8492).  
**S9.** Expanded E08 run-state diagnostics (pre-cue μ/β in µV²; PTP in µV). Diagnostic only.  
**S10.** Duration and sampling-rate sensitivity summaries (sampling-rate N = 99).  
**S11.** Comparator participant BAcc histograms (Dummy, CSP-LDA, Riemannian-LR, ERD-LR).
