# Post-definitive control completion report

## Provenance

| Field | Value |
|---|---|
| Parent definitive tag | `m2-preexec-fir-windows-candidate` |
| Parent definitive commit | `3b615ed1a8e455918d6e9d90bfb5c4e42ae44adc` |
| Reason for execution | Completion of analyses prespecified before definitive outcome inspection but absent from the definitive output package. |
| Artifact-sensitivity job | TRUBA Orfoz **6240549** (thresholds; exit 1 due to epoch-count guard miscalibration; outputs retained) |
| Spatial-completion job | TRUBA Orfoz **6242944** (`SKIP_THRESHOLDS=1`; exit 0) |
| Immutable definitive tree | `results/definitive/` — **not modified** |
| New outputs root | `results/postdefinitive_e05/` |
| Review extractions root | `results/postdefinitive_review/` |

This work occurs **after** definitive primary E01/E07 acceptance.

## Why this task was performed

Definitive `run_full` wrote E05 cohort metadata and spatial-channel provenance only. Prespecified artifact-sensitivity decoding and spatial-control decoding were implemented in the pilot path but not executed in the definitive package. This task completed those missing prespecified controls and extracted existing E03/E04/E08/sensitivity tables for review.

## E05 audit

See `docs/e05_postdefinitive_audit.md`.

- **Prespecified:** artifact decoding at none / 150 µV / 200 µV; spatial-control ERD-LR decoding on frozen peripheral channels.
- **Definitive executed:** `threshold_cohorts.csv` + `spatial_control_channels.json` only.
- **Missing until this completion:** decoding exports under each threshold and spatial control.

## Artifact-threshold reconciliation

See `docs/e05_threshold_reconciliation.md` and `results/postdefinitive_e05/threshold_reconciliation.csv`.

Corrected counts on the definitive TRUBA minimal cache (`preproc_minimal_9526854ad3f9`):

| threshold | epochs_before | epochs_rejected | epochs_retained | participants_eligible |
|---|---:|---:|---:|---:|
| none (true) | 19440 | 0 | 19440 | 109 |
| 150uv | 19440 | 4150 | 15290 | 94 |
| 200uv | 19440 | 2183 | 17257 | 102 |
| none_as_executed_in_definitive_run_full_BUG | 19440 | 2183 | 17257 | 102 |

Identical definitive package `none` and `200uv` rows (both 17257 / N=102) occurred because `threshold_uv=None` fell back to config **200 µV**. Primary E01 used explicit `threshold_uv=200.0` and is unaffected.

Note: decoding cohort epoch counts are **post-eligibility** (E01 OOF length at 200 µV = **16913**), whereas `threshold_cohorts` / reconciliation `epochs_retained` are **pre-eligibility** PTP-retained totals.

## Artifact sensitivity decoding

Factual results from `results/postdefinitive_e05/artifact_sensitivity/`:

| Condition | Eligible N | Participant-mean BAcc | Bootstrap 95% CI (BAcc) |
|---|---:|---:|---|
| no rejection | **109** | **0.618568** | [0.605923, 0.632710] |
| 150 µV | **94** | **0.616887** | [0.601611, 0.631560] |
| 200 µV (primary) | **102** | **0.617924** | [0.603553, 0.632899] |

Exact stored values:

- none: `0.6185680325505829`
- 150uv: `0.6168866326577104`
- 200uv: `0.6179239767273408`

**200 µV reproduction check:** `match=true`  
(`primary_reproduction_check.json`: frozen E01 BAcc `0.6179239767`, E05 200 µV BAcc `0.6179239767273408`, `n_epochs=16913`, `expected_200uv_epochs=16913`).

200 µV remains primary regardless of other threshold outcomes.

## Spatial control

Frozen channels (21; from `eeg_me_mi.rois.SPATIAL_CONTROL_CHANNELS`, also `spatial_control_channels.json`):

`Fp1, Fpz, Fp2, AF7, AF3, AFz, AF4, AF8, F7, F8, FT7, FT8, T7, T8, TP7, TP8, P7, P8, O1, Oz, O2`

Disjoint from the primary 21 sensorimotor channels by construction.

| Quantity | Value |
|---|---|
| Eligible N | **78** |
| Epochs | 11741 |
| Participant-mean BAcc | **0.583815** |
| Bootstrap 95% CI | **[0.5707, 0.5967]** |

Exact BAcc: `0.583814977287951`; CI from bootstrap summary: `[0.5706812773069228, 0.5967002022178616]`.

## Sensorimotor vs spatial-control paired effect

From `paired_effect_summary.json` (effect + CI only):

| Quantity | Value |
|---|---|
| Common N | **77** |
| Mean Δ (SM − SC) | **0.0382** |
| Bootstrap 95% CI | **[0.0245, 0.0521]** |
| Formal paired confirmatory p-value | **none** (not prespecified) |

Exact mean Δ: `0.03823465807166761`; CI: `[0.024501420254655796, 0.052141517857346616]`.  
`formal_paired_p_prespecified: false`.

## E03 extraction

Existing definitive outputs only — see `docs/e03_result_extraction.md` and `results/postdefinitive_review/e03_review_summary.csv`.  
No new analyses. No biological conclusions.

## E04 extraction

Existing definitive outputs only — labeled **EXPLORATORY**.  
See `docs/e04_result_extraction.md` and `results/postdefinitive_review/e04_review_summary.csv`.

## E08 extraction

Existing definitive outputs only — characterize run-order patterns; do not claim confound removal.  
See `docs/e08_result_extraction.md` and `results/postdefinitive_review/e08_review_summary.csv`.

## Other sensitivities

From existing definitive outputs (`results/postdefinitive_review/sensitivity_summary.csv`):

| Analysis | N | BAcc | CI low | CI high |
|---|---:|---:|---:|---:|
| E01 primary | 102 | 0.6179239767 | 0.603553 | 0.632899 |
| E01 strict | 51 | 0.6140246117 | 0.593935 | 0.634892 |
| E06 first60 | 102 | 0.6174294344 | 0.602189 | 0.633765 |
| E06 all-events | 102 | 0.6179239767 | 0.603553 | 0.632899 |
| Sampling-rate sensitivity | 99 | (planned/cohort only; BAcc not present in definitive exports) |  |  |

## Integrity

- Unit tests: `tests/test_postdefinitive_e05.py` (threshold sentinel / PTP keep-all).
- 200 µV E05 vs frozen E01: identical participant-mean BAcc; OOF length 16913; `primary_reproduction_check.json` **match=true**.
- `results/definitive/` unchanged by this completion.
- Spatial-control channel set unchanged from frozen definition.

## Impact on frozen primary results

**NO.** Primary E01 and E07 were not rerun, retuned, or rewritten.  
Frozen primary remains: N=102, BAcc=`0.6179239767`, E07 plus-one p=`0.000999000999`.

## Deviations

1. Definitive E05 decoding was absent from `run_full`; completed post-definitive under `results/postdefinitive_e05/` rather than rewriting `results/definitive/`.
2. Job **6240549** exited non-zero after completing threshold decoding because the guard compared post-eligibility epochs (16913) to pre-eligibility PTP-retained count (17257). Scientific 200 µV reproduction already matched; guard corrected to 16913; spatial completed in job **6242944** with `--skip-threshold-decoding`.
3. Spatial-control eligible N=78 (not 102): eligibility recomputed on spatial-control epochs under existing rules; paired comparison uses common N=77.
4. True “no rejection” uses `threshold_uv=0.0` / explicit `None` after sentinel fix; definitive package “none” row remains the documented bug path.
5. Local working tree may be dirty relative to the parent tag because control scripts/docs were added after the frozen definitive commit.
