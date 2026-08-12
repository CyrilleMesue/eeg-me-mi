# Scientific novelty analysis

Date: 2026-08-12  
Status: literature-guided planning document; claims must be revisited immediately before submission.

## Bottom line

The publishable contribution should **not** be “ME and MI differ,” “mu/beta ERD occurs,” “CSP/Riemannian methods classify EEG,” or “a classifier reaches the highest accuracy.” Those are established. The strongest defensible contribution is a transparent full-cohort study of **which ME-versus-MI signatures remain detectable in unseen EEGMMIDB participants, how those signatures depend on movement and participant, and how robust they are to artifact handling and protocol choices**.

Even that contribution is incremental-methodological rather than a new physiological discovery. Its value comes from combining participant-disjoint inference, interpretable physiology, movement-resolved heterogeneity, complete OOF outputs, and unusually explicit confound sensitivity on a large public cohort.

## Literature basis

- The [official EEGMMIDB record](https://physionet.org/content/eegmmidb/1.0.0/) establishes the 109-participant, 64-channel, 160 Hz protocol and the correct run/T1/T2 semantics.
- Foundational ERD/ERS physiology is established by [Pfurtscheller & Lopes da Silva (1999)](https://doi.org/10.1016/S1388-2457(99)00141-8), and MI sensorimotor activation by [Pfurtscheller & Neuper (1997)](https://doi.org/10.1016/S0304-3940(97)00889-6).
- Direct comparisons already report that ME and MI share motor-related ERD but can differ in strength, duration, and distribution; for example, [Lee et al. (2017)](https://pubmed.ncbi.nlm.nih.gov/27636359/) found strongest/longest alpha suppression for execution, with MI only partially resembling ME.
- A recent [2025 ME/MI EEG review](https://pubmed.ncbi.nlm.nih.gov/41141194/) emphasizes shared mu/beta signatures, substantial methodological heterogeneity, inter-participant non-response, and sparse EMG verification.
- [Kaya et al. (2024)](https://pmc.ncbi.nlm.nih.gov/articles/PMC10998040/) curated EEGMMIDB specifically for intra-/inter-subject decoding, transfer learning, MI/ME tasks, and movement contrasts. Thus dataset curation or cross-subject use alone is not novel.
- CSP/FBCSP is established (e.g. [Ang et al., 2012](https://doi.org/10.3389/fnins.2012.00039)); Riemannian covariance methods are established (e.g. [Barachant et al., 2012](https://doi.org/10.1109/TBME.2011.2172210)); and EEG classifier comparisons are extensively reviewed by [Lotte et al. (2018)](https://doi.org/10.1088/1741-2552/aab2f2).
- Cross-subject EEGMMIDB decoding and deep architectures already exist, including [EEGNet Fusion](https://doi.org/10.3390/computers9030072). These usually decode movement classes separately within ME or MI, which is not identical to ME-versus-MI classification, but they eliminate any claim that subject-independent EEGMMIDB decoding itself is new.
- EEG segment leakage and non-independent validation are recognized hazards; [Brookshire et al. (2024)](https://doi.org/10.3389/fnins.2024.1373515) specifically emphasizes leakage created by segment-based splitting in translational EEG.
- Chance thresholds and uncertainty depend on sample structure; see [Combrisson & Jerbi (2015)](https://doi.org/10.1016/j.jneumeth.2015.01.010) and [Varoquaux (2018)](https://doi.org/10.1016/j.neuroimage.2017.06.061).

## Established, incremental, potentially novel, speculative

### Already established

- ME and MI recruit overlapping sensorimotor networks.
- Both can elicit mu and beta ERD; ME often produces stronger or more sustained changes.
- CSP, filter-bank CSP, Riemannian covariance/tangent space, and linear classifiers are appropriate EEG baselines.
- Cross-participant EEG decoding is difficult because of inter-individual variability and domain shift.
- Random epoch splitting and global supervised feature selection can inflate EEG performance.
- Physical movement creates EMG/electrode-motion confounding in ME-versus-MI EEG.

### Incremental but valuable

- Leakage-safe ME-versus-MI benchmarking across the full eligible EEGMMIDB cohort.
- Paired comparison of interpretable ERD, CSP-LDA, and tangent-space linear models using identical outer participants.
- Participant-level uncertainty, group-aware permutation inference, and complete OOF publication artifacts.
- Correcting the widely repeated 60/120-second interpretation and run/T1/T2 mapping.

### Potentially novel as an integrated contribution

- Joint characterization of unseen-participant separability, movement-specific physiology, participant heterogeneity, and artifact-threshold robustness for ME versus MI on EEGMMIDB.
- Asking whether spatial ME/MI similarity across movements predicts which signatures generalize across unseen participants, if prespecified and kept interpretable.
- Quantifying how stable participant rankings and spatial effects are across rejection thresholds, rather than reporting only mean accuracy.

### Unsupported or speculative

- Purely cortical attribution of ME/MI differences.
- Clinical or rehabilitation effectiveness.
- Online, real-time, or calibration-free BCI readiness.
- A universal physiological biomarker of imagery ability; EEGMMIDB lacks imagery-vividness and behavioral compliance measures.
- Causal attribution to ME versus MI independent of fatigue/order, because execution always precedes imagery in matched run pairs.

## Contribution-by-contribution assessment

### C1. Cross-participant ME-versus-MI generalization

- **Question:** Can event-related EEG distinguish ME from MI in participants excluded from all training and tuning?
- **Prior knowledge:** ME/MI differences and cross-subject decoding are established; validation quality varies.
- **Gap:** A transparent full-cohort EEGMMIDB analysis centered on participant-level ME-versus-MI inference, rather than movement-class accuracy, is not clearly established by the reviewed literature.
- **Dataset suitability:** Large cohort and repeated ME/MI movements are strengths.
- **Required experiment:** Nested participant-disjoint CV; identical outer folds; dummy, ERD-LR, CSP-LDA, tangent-space LR; participant bootstrap and 1,000 group-aware permutations.
- **Contribution:** Reproducible estimate of generalizable signal, including negative evidence if near chance.
- **Confounders:** Run order, physical artifacts, cohort selection, shared cue structure, temporal drift.
- **Risk:** Moderate. Result may be modest; novelty is methodological/integrative.
- **Role:** **Primary.**

### C2. Sensorimotor mu/beta physiology

- **Question:** How do baseline-referenced mu/beta magnitude, topography, and lateralization differ between ME and MI?
- **Prior knowledge:** Shared ERD and often stronger ME ERD are established.
- **Gap:** Movement-resolved, participant-level effect maps and consistency across the full EEGMMIDB cohort may add scale and reproducibility.
- **Dataset suitability:** Repeated unilateral/bilateral trials and dense sensorimotor montage.
- **Required experiment:** Participant-level condition contrasts by band/channel/movement, effect sizes and CIs, FDR correction, topographies, and laterality indices.
- **Contribution:** Large-cohort replication and boundary conditions, not discovery of ERD.
- **Confounders:** EMG, reference choice, canonical bands, volume conduction, fixed order.
- **Risk:** Low-to-moderate scientifically; novelty alone is low.
- **Role:** **Co-primary physiological analysis or strong secondary**, tied to C1.

### C3. Movement-specific ME/MI differences

- **Question:** Does generalizable ME/MI separability vary across left fist, right fist, both fists, and both feet?
- **Prior knowledge:** Somatotopy and movement-dependent ERD are established; recent work shows trial count and movement can alter ME/MI contrasts.
- **Gap:** Paired movement-specific generalization plus physiology on full EEGMMIDB appears less saturated.
- **Dataset suitability:** The protocol provides each movement in both conditions across three repetitions.
- **Required experiment:** Separately trained/evaluated movement-specific models with shared participant folds; multilevel participant-level condition×movement inference; unilateral/bilateral planned contrasts.
- **Contribution:** Identifies which body movements carry stable cross-participant ME/MI differences.
- **Confounders:** Lower trials, different motor artifact profiles, feet versus fists, run position.
- **Risk:** Multiple comparisons and lower precision.
- **Role:** **Secondary.**

### C4. Participant heterogeneity

- **Question:** For whom does cross-participant ME/MI decoding work, and which prespecified EEG/QC measures correlate with success?
- **Prior knowledge:** BCI non-response and inter-participant variability are well established.
- **Gap:** Linking strictly OOF ME/MI performance to a small prespecified set of physiology/QC features may be useful.
- **Dataset suitability:** N≈109 is relatively large for EEG but modest for multivariable association.
- **Required experiment:** OOF participant metrics; at most a small prespecified predictor set; robust/Spearman or regularized multivariable analysis; bootstrap CIs; multiplicity control; leave-one-participant influence diagnostics.
- **Contribution:** Characterizes heterogeneity without claiming causal predictors or imagery aptitude.
- **Confounders:** Metric noise, retained epoch counts, collider bias from exclusion, artifact-driven performance.
- **Risk:** High false-discovery and overinterpretation risk.
- **Role:** **Exploratory.**

### C5. Representational similarity

- **Question:** How similar are ME and MI channel-wise ERD patterns, and does similarity depend on movement?
- **Prior knowledge:** Partial overlap of ME/MI cortical patterns is established.
- **Gap:** Cross-validated or participant-level movement-resolved similarity on EEGMMIDB could complement decoding.
- **Dataset suitability:** Common channels, movements, and repeated conditions.
- **Required experiment:** Participant-level ME/MI ERD vectors by band/movement; correlation and cosine similarity with uncertainty; reliability/noise-ceiling estimates; avoid using the same epochs to select and test channels.
- **Contribution:** Interpretability beyond classifier weights.
- **Confounders:** Common reference, spatial smoothing, unequal reliability, artifacts.
- **Risk:** Similarity is scale-insensitive and may obscure meaningful magnitude differences.
- **Role:** **Exploratory/supplementary unless reliability is adequate.**

### C6. Artifact robustness

- **Question:** Are conclusions stable under no threshold, 150 µV, and 200 µV, and are retained signals spatially/spectrally plausible?
- **Prior knowledge:** Movement artifact confounding is known; dedicated EMG is preferred but absent.
- **Gap:** Many public-dataset studies under-report differential rejection and robustness.
- **Dataset suitability:** Raw EEG permits threshold and distribution diagnostics, but not definitive artifact removal.
- **Required experiment:** PTP distributions and rejection rates by condition/movement/participant; full primary reruns at prespecified thresholds; participant-ranking/effect-map stability; optional peripheral-versus-central channel negative-control diagnostics.
- **Contribution:** Determines whether the main conclusion is fragile to plausible cleaning choices.
- **Confounders:** Thresholding cannot remove all EMG and may induce selection bias.
- **Risk:** Cannot establish cortical purity.
- **Role:** **Required sensitivity analysis and central limitation.**

### Rejected additions at this stage

- Model zoo, EEGNet, FBCSP variants, domain adaptation, and transfer learning: reject unless a later, literature-backed scientific question requires them. They broaden optimization without strengthening the current estimand.
- Source localization: reject for the primary paper because EEGMMIDB electrode geometry and absence of individual anatomy make strong localization claims difficult.
- Automated ICA “artifact removal”: reject as a guaranteed solution because no EOG/EMG references exist and component decisions introduce flexibility. It could be a separately prespecified sensitivity study only.

## Recommended paper contribution

**Provisional contribution statement:** A full-cohort, participant-disjoint and physiology-linked assessment of which EEG signatures distinguish execution from imagery in unseen individuals, with movement-resolved heterogeneity and explicit artifact/protocol sensitivity.

The paper should be presented as a rigorous benchmark plus physiological robustness study. If generalization is weak, the contribution becomes a well-powered boundary result showing that within-protocol ME/MI differences do not necessarily form stable unseen-participant features.

## Fundamental identification limitation

EEGMMIDB uses the fixed sequence ME-unilateral, MI-unilateral, ME-bilateral, MI-bilateral, repeated three times. Thus ME/MI is perfectly aligned with odd/even task-run position and ME always precedes matched MI. No statistical adjustment can fully separate condition from short-timescale order, fatigue, learning, habituation, or drift. Analyses can test trend sensitivity (repetition, elapsed time, adjacent-pair contrasts, baseline drift), but the manuscript must not call the resulting contrast an unconfounded causal ME effect.

