# Publication figure source map

**Freeze:** `analysis-complete-pre-manuscript` (`6d0ce7a`)  
**Generator:** `figures/scripts/generate_all_figures.py`  
**Rule:** every plotted quantitative value is read from frozen machine-readable outputs under `results/`; figure scripts do not recompute EEG features, CV, or inferential endpoints.

CI definition (unless noted): **participant-bootstrap 95% percentile interval** from the named `bootstrap_summary.csv` (`ci_low`, `ci_high`).

---

## Figure 1 — Study design and analysis framework

| Panel | Scientific question | Source file(s) | Variables | N | Statistic | CI | Inferential? | Frozen analysis | Script |
|---|---|---|---|---|---|---|---|---|---|
| 1A | ME→MI matched run order | Conceptual (`src/eeg_me_mi/protocol` run structure) | Runs 3–14 pairs | — | Schematic | — | Descriptive | Protocol definition | `figure_1_study_design` |
| 1B | Participant-disjoint nested CV | Conceptual (matches E01 CV design docs) | Outer/inner/test participants | — | Schematic | — | Descriptive | E01 design | same |
| 1C | FIR-safe temporal windows | `results/definitive/full/e00/window.json`, `e01/.../window.json` (conceptual display of frozen windows) | Pre-cue / excluded / task intervals | — | Window edges | — | Descriptive | E00/E01 windows | same |
| 1D | 42 ERD features → nested LR | Protocol channel/band definitions | 21 ch × μ/β | — | Feature schematic | — | Descriptive | E01 ERD-LR | same |
| 1E | Control/evidence logic | Conceptual map of E00–E08 suite | Analysis names | — | Flow | — | Descriptive | Full freeze suite | same |

**Missing sources:** none for conceptual panels. Window edges must match frozen window JSON (validated visually against freeze docs).

---

## Figure 2 — Primary cross-participant decoding

| Panel | Scientific question | Source file(s) | Variables | N | Statistic | CI | Inferential? | Frozen analysis | Output |
|---|---|---|---|---|---|---|---|---|---|
| 2A | Primary participant BAcc | `results/definitive/full/e01/erd_lr/participant_metrics.csv`, `.../bootstrap_summary.csv` | `balanced_accuracy`; bootstrap mean/CI | 102 | Participant BAcc + mean | Bootstrap 95% | Descriptive distribution + CI | E01 ERD-LR | `Figure_2A_source.csv` |
| 2B | Model comparators (same CV) | `e01/{dummy,csp_lda,tangent_lr,erd_lr}/bootstrap_summary.csv` | `balanced_accuracy` mean/CI | 102 | Participant-mean BAcc | Bootstrap 95% | Descriptive comparison | E01 | `Figure_2B_source.csv` |
| 2C | Structured permutation null | `results/definitive/full/e07/null_statistics.csv`, `e07_summary.json` | `statistic`; `observed_statistic`; `p_value_plusone` | 1000 nulls | Null BAcc hist + observed | Plus-one p | Inferential (E07) | E07 | `Figure_2C_source.csv` |
| 2D | Secondary metrics | `e01/erd_lr/summary.json` | BAcc, ROC-AUC, Macro-F1, Sens, Spec, MCC | 102 | Point estimates | — | Descriptive (BAcc primary) | E01 | `Figure_2D_source.csv` |

Exact frozen anchors: mean BAcc = **0.6179239767**; E07 observed identical; **0/1000** null ≥ observed; plus-one **p = 0.000999**.

---

## Figure 3 — Pre-cue vs post-cue

| Panel | Question | Source | Variables | N | Statistic | CI / test | Inferential? | Analysis | Output |
|---|---|---|---|---|---|---|---|---|---|
| 3A | Temporal schematic E00 vs E01 | Window definitions (conceptual) | Windows | — | Schematic | — | Descriptive | E00/E01 | — |
| 3B | Paired E00 vs E01 | `results/definitive/full/comparisons/e00_vs_e01_participant.csv`; E00/E01 bootstrap | participant BAccs | 102 | Paired means | Bootstrap on each arm | Descriptive paired | E00 vs E01 | `Figure_3B_source.csv` |
| 3C | ΔBAcc = E01−E00 | same + `e00_vs_e01_bootstrap_summary.csv` + `e00_vs_e01_signflip.json` | `difference_e01_minus_e00` | 102 | Mean Δ | Bootstrap CI; sign-flip p | Inferential (sign-flip) | Comparison | `Figure_3C_source.csv` |
| 3D | Optional secondary | Not plotted separately (covered by 2D / Table 2) | — | — | — | — | — | — | **Not generated** (avoid overcrowding) |

Exact anchors: E00 ≈ **0.539**; E01 ≈ **0.618**; mean Δ ≈ **0.079**; CI ≈ **[0.066, 0.092]**; sign-flip **p ≈ 0.0005**.

---

## Figure 4 — Physiology and spatial evidence

| Panel | Question | Source | Variables | N | Statistic | CI | Inferential? | Analysis | Output |
|---|---|---|---|---|---|---|---|---|---|
| 4A | Sensorimotor channel map | `src/eeg_me_mi/protocol.py`, `rois.py`; MNE `standard_1005` montage for layout only | Channel names / ROI membership | 21 ch | Layout | — | Descriptive | Prespecified montage | — |
| 4B | ROI ME−MI ERD | `results/definitive/full/e03/roi_summary.csv` | `mean`, bootstrap CI, `reject_fdr` | 102 | Mean dB effect | Bootstrap 95% | FDR-marked descriptive/inferential as frozen | E03 | `Figure_4B_source.csv` |
| 4C | Channel topomaps | `e03/channel_summary_fdr.csv` | `mean` by channel/band | channel set | Channel means | — | Supporting descriptive | E03 | `Figure_4C_source.csv` |
| 4D | Movement-specific decoding | `e02/{movement}/bootstrap_summary.csv`, `summary.json` | BAcc, N | per movement | Participant-mean BAcc | Bootstrap 95% | Descriptive | E02 | `Figure_4D_source.csv` |
| 4E | Spatial control | `results/postdefinitive_e05/spatial_control/{summary,bootstrap_summary,paired_effect_summary,paired_participant_differences}.csv/json` | SM/SC BAcc; paired Δ | Spatial N=78; paired N=77 | Means + paired Δ | Bootstrap for SC & paired Δ | Descriptive paired Δ (**no confirmatory p**) | Postdef E05 | `Figure_4E_source.csv`, `Figure_4E_annotations.json` |

Paired SM mean uses **frozen paired CSV mean** (≈0.6225), not full-cohort 0.6179.

---

## Figure 5 — Robustness and protocol diagnostics

| Panel | Question | Source | Variables | N | Statistic | CI | Inferential? | Analysis | Output |
|---|---|---|---|---|---|---|---|---|---|
| 5A | Artifact thresholds | `results/postdefinitive_e05/artifact_sensitivity/{none,150uv,200uv}/` | BAcc, N | 109 / 94 / 102 | Participant-mean BAcc | Bootstrap | Descriptive sensitivity | Postdef E05 | `Figure_5A_source.csv` |
| 5B | Other sensitivities | `results/postdefinitive_review/sensitivity_summary.csv` + `results/final_sensitivity_checks/sampling_rate/sampling_rate_sensitivity_summary.json` | analysis, N, BAcc, CI | varies | BAcc | Bootstrap where available | Descriptive | Review + final sens | `Figure_5B_source.csv` |
| 5C | Label-specific rejection | `results/final_sensitivity_checks/rejection_audit/rejection_audit_summary.json` | ME/MI rejection; participant_paired | 102 | Proportions; mean Δ pp | Bootstrap CI on participant Δ | Descriptive (no confirmatory p) | Final rejection audit | `Figure_5C_source.json` |
| 5D | Fixed ME→MI order | `results/postdefinitive_review/e08_matched_pairs.csv` | me_run, mi_run | pairs | Schematic | — | Descriptive | E08 | (from CSV) |
| 5E | Pre-cue run-state | same matched pairs (`precue_beta_me/mi`) | Pre-cue β by pair | pairs | Means | — | Diagnostic descriptive | E08 | `Figure_5E_source.csv` |

---

## Supplementary

| Figure | Source root | Notes |
|---|---|---|
| S1 Cohort flow | `results/definitive/full/qc/participant_eligibility.csv` | Count overview |
| S2 Secondary metrics | `e01/*/summary.json` | Table-style; also Table 2 candidate |
| S3 Comparator distributions | `e01/*/participant_metrics.csv` | Histograms |
| S4 Movement distributions | `e02/*/participant_metrics.csv` | Histograms |
| S5 Channel ERD | `e03/channel_summary_fdr.csv` | Full channel bars |
| S6 Laterality | `e03/laterality.csv` | Secondary / heterogeneous |
| S7 Heterogeneity | `e01` + `postdefinitive_review/e04_*` | **EXPLORATORY** |
| S8 Artifact distributions | `postdefinitive_e05/artifact_sensitivity/*/participant_metrics.csv` | Expands 5A |
| S9 Rejection audit detail | `final_sensitivity_checks/rejection_audit/*` | Expands 5C |
| S10 E08 expanded | `postdefinitive_review/e08_by_run.csv` | Diagnostic |
| S11 Sampling-rate | `final_sensitivity_checks/sampling_rate/*` | N=99 STABLE |

---

## Panels / figures not generated

| Item | Reason |
|---|---|
| Figure 3D secondary E00/E01 metrics | Would overcrowding Fig 3; values available in Table 2 / S2 if needed |
| New topography recomputation beyond frozen channel means | Would require new analysis — STOP |
| Confirmatory paired p for spatial control | Explicitly not in freeze; not added |
| Historical plots | Superseded; not used |

---

## Regeneration

```bash
PYTHONPATH=src python figures/scripts/generate_all_figures.py
PYTHONPATH=src python figures/scripts/validate_figures.py
```
