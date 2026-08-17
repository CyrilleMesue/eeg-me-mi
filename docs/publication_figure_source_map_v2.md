# Publication figures V2 — source map

Freeze: `analysis-complete-pre-manuscript` (`6d0ce7a`)  
Generator: `figures_v2/scripts/generate_all_figures_v2.py`  
All quantitative values read from frozen machine-readable outputs (and exported under `figures_v2/source_data/`). V1 source_data is not overwritten.

CI definition (unless noted): participant-bootstrap 95% percentile interval from named `bootstrap_summary.csv`.

| Figure | Panel | Source | Key variables | N | Statistic | Inferential? |
|---|---|---|---|---|---|---|
| 1 | A–C | Protocol conceptual + window definitions | runs; windows; pipeline | — | Schematic | Descriptive |
| 2 | A | `results/definitive/full/e01/erd_lr/participant_metrics.csv`, `bootstrap_summary.csv` | BAcc | 102 | Distribution + mean/CI | Descriptive + CI |
| 2 | B | `e01/{dummy,csp_lda,tangent_lr,erd_lr}/bootstrap_summary.csv` | mean BAcc, CI | 102 | Dot + CI | Descriptive |
| 2 | C | `e07/null_statistics.csv`, `e07_summary.json` | null statistic; observed; p_plusone | 1000 | Histogram | Inferential |
| 3 | A | Conceptual E00/E01 windows | — | — | Schematic | Descriptive |
| 3 | B–C | `comparisons/e00_vs_e01_participant.csv`, bootstrap + signflip JSON; E00/E01 bootstrap | e00, e01, Δ | 102 | Distributions; mean Δ; sign-flip p | Inferential (sign-flip) |
| 4 | A | `e03/roi_summary.csv` | mean, CI, reject_fdr | 102 | Forest | FDR as frozen |
| 4 | B | `e03/channel_summary_fdr.csv` + MNE `standard_1005` layout | channel mean | — | Topomap | Supporting |
| 4 | C | `postdefinitive_e05/spatial_control/*` | SM/SC BAcc; paired Δ | 78 / 77 | Paired distributions | Descriptive (no confirmatory p) |
| 4 | D | E05 artifact + `postdefinitive_review/sensitivity_summary.csv` + sampling-rate JSON; `e08_matched_pairs.csv` | BAcc; pre-cue β | varies | Forest + paired bars | Diagnostic |
| S1 | — | `qc/participant_eligibility.csv` | eligible counts | — | Flow | Descriptive |
| S2 | — | `e01/erd_lr/summary.json` | secondary metrics | 102 | Table | Descriptive |
| S3 | — | `e02/*/…` | BAcc | per movement | Distributions | Descriptive |
| S4 | — | `e03/channel_summary_fdr.csv` | channel effects | — | Forest | Supporting |
| S5 | — | `e03/laterality.csv` | laterality_me_minus_mi | 102 | Distributions | Secondary |
| S6 | — | E01 + `postdefinitive_review/e04_*` | ranks/corrs | 102 | Exploratory | Exploratory |
| S7 | — | E05 artifact participant metrics | BAcc | 109/94/102 | Distributions | Descriptive |
| S8 | — | `final_sensitivity_checks/rejection_audit/*` | rejection; paired Δ | 102 | Aggregate + paired | Descriptive |
| S9 | — | `e08_by_run.csv` | μ/β/PTP | runs | Lines | Diagnostic |
| S10 | — | sensitivity + sampling-rate | BAcc | varies | Forest + dist | Descriptive |
| S11 | — | `e01/*/participant_metrics.csv` | BAcc | 102 | Histograms | Descriptive |

**Unit note (E08):** Welch band power is stored in V² (MNE default volts). Display uses exact conversion ×10¹² → µV². PTP already stored as µV (`ptp_uv`).

**Not generated / not main:** V1 Fig 2D secondary bars; V1 movement panel in main Fig 4; confirmatory spatial p-value.
