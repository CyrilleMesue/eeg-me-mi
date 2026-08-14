# E05 threshold reconciliation (updated after Job 6242944)

**Parent definitive:** `m2-preexec-fir-windows-candidate` / `3b615ed`  
**Primary E01/E07 impact:** **none** (primary uses explicit `threshold_uv=200.0`).

## Definitive package counts (as executed in run_full)

| threshold | n_epochs | n_e01_eligible |
|---|---:|---:|
| none | 17257 | 102 |
| 150uv | 15290 | 94 |
| 200uv | 17257 | 102 |

Identical `none` and `200uv` rows reflect the `threshold_uv=None` → config 200 µV fallback bug — not a scientific claim that no epochs exceed 200 µV.

## Corrected reconciliation (definitive TRUBA cache)

Source: `results/postdefinitive_e05/threshold_reconciliation.csv`

| threshold | epochs_before | epochs_rejected | epochs_retained | participants_eligible |
|---|---:|---:|---:|---:|
| none (true) | 19440 | 0 | 19440 | 109 |
| 150uv | 19440 | 4150 | 15290 | 94 |
| 200uv | 19440 | 2183 | 17257 | 102 |
| none_as_executed_in_definitive_run_full_BUG | 19440 | 2183 | 17257 | 102 |

Pre-eligibility PTP-retained 200 µV count = 17257.  
Post-eligibility E01 / E05-200uv decoding epochs = **16913** (matches definitive E01 `oof_predictions.csv` length).

## Primary analysis

Frozen primary E01/E07 remain valid.
