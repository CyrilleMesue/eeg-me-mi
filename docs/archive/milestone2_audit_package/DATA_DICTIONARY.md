# Data dictionary — Milestone 2 machine-readable outputs

Column definitions for primary CSV/JSON exports included in this package.  
Unless noted, missing values are empty/`NaN`. Labels: **ME**=execution (label 1), **MI**=imagery (label 0).

---

## `results/full_cohort_audit/raw_data_audit.csv`

| Column | Meaning |
|---|---|
| `subject` | EEGMMIDB subject ID (1–109) |
| `run` | Task run number (3–14) |
| `condition` | `execution` or `imagery` from run identity |
| `task_family` | `unilateral` or `bilateral` |
| `repetition` | Matched-pair repetition index 1–3 |
| `in_anomaly_watchlist` | True if subject ∈ {38,88,89,92,100,104} |
| `file_exists` | EDF present locally at audit time |
| `downloaded_or_cached` | File available for reading |
| `source_file` | EDF basename |
| `sfreq` | Sampling rate (Hz) |
| `n_channels` | EEG channel count after standardization pick |
| `channel_names` | `|`-joined channel names |
| `duration_sec` | Recording duration |
| `annotation_count` | Total annotations |
| `T0_count` / `T1_count` / `T2_count` | Annotation tallies |
| `unexpected_annotations` | Non T0/T1/T2 descriptions (`|`-joined) |
| `missing_sensorimotor_channels` | Required FC/C/CP channels absent |
| `structurally_valid` | Passes fatal structural rules (not auto-exclude for 128 Hz alone) |
| `invalidity_reason` | `|`-joined reason codes / notes |

`anomaly_report.csv` uses the same schema (watchlist + invalid rows).

---

## `results/full_cohort_audit/download_manifest.csv`

| Column | Meaning |
|---|---|
| `subject`, `run` | Requested recording |
| `status` | `exists` / `downloaded` / `failed` |
| `path` | Local filesystem path |
| `nbytes` | File size bytes |
| `sha256` | Checksum when computed (may be blank for speed on exists) |
| `attempts` | Download attempts |
| `error` | Failure detail |

---

## `results/full_cohort_audit/participant_eligibility.csv`

Performance-blind eligibility after 200 µV PTP filtering of usable matched pairs.

| Column | Meaning |
|---|---|
| `subject` | Participant ID |
| `structural_ok` | No structural anomaly in used data |
| `n_me_epochs` / `n_mi_epochs` | Retained epochs by mode (usable pairs only) |
| `n_usable_matched_pairs` | Count of ME↔MI pairs with both sides valid & ≥1 epoch |
| `n_unilateral_pairs` / `n_bilateral_pairs` | Family coverage |
| `movements_me` / `movements_mi` | `|`-joined movement sets |
| `eligible_primary` | Primary E01 rule (≥30/mode, ≥2 pairs, uni+bi, composition) |
| `eligible_min20` / `eligible_min40` | Sensitivity flags (do not change primary) |
| `eligible_strict` | Strict sensitivity cohort flag |
| `reason_codes` / `reason_detail` | Exclusion codes / text |
| `n_<movement>_me/mi` | Cell counts for left/right fist, both fists/feet |
| `usable_pair_ids` | `|`-joined pair IDs like `03-04` |
| `e02_<analysis>_*` | Per-analysis epoch counts, pair counts, eligibility, reasons |
| `strict_all_runs_valid` | All 12 task runs structurally valid |
| `strict_reasons` | Strict failure codes |
| `expected_<movement>_<me/mi>` | Expected cell size from audit T1/T2 counts |
| `frac_<movement>_<me/mi>` | Retained / expected fraction |

---

## `results/full_cohort_audit/fold_assignments_e01_primary.csv`

| Column | Meaning |
|---|---|
| `fold` | Outer fold index (1…K) |
| `role` | `train` or `test` |
| `subject` | Participant ID in that role |

Identical participant-disjoint outer folds are intended for E00/E01 when population-compatible.

---

## `results/full_cohort_audit/rejection_qc.csv`

Per subject/run preprocess QC for **minimal** caching (rejection applied later by PTP threshold).

| Column | Meaning |
|---|---|
| `n_events` | T1/T2 events found |
| `n_kept` | Epochs retained in minimal cache (before threshold) |
| `n_rejected` | Dropped during minimal construction (usually 0) |
| `rejection_rate` | Rejected / events in that step |
| `status` | `ok` / `error` / … |
| `error` | Exception text if any |
| `peak_to_peak_max_uv` | Max channel PTP (µV) among minimal epochs |

---

## `results/full_cohort_audit/e02_cohort_sizes.csv`

| Column | Meaning |
|---|---|
| `analysis` | Movement / pooled analysis name |
| `n_eligible` | Count of E02-eligible participants |

---

## `results/full_cohort_audit/cohort_summary.json`

Aggregate counts: downloads, structural validity, E01/strict/min20/min40 ns, E02 sizes, eligible subject list, watchlist IDs.

---

## Decoding outputs (pilot / toy) — common schemas

### `oof_predictions.csv`

| Column | Meaning |
|---|---|
| `experiment` | e.g. `E00`, `E01`, `E02_left_fist` |
| `model` | e.g. `erd_lr`, `csp_lda`, `dummy` |
| `fold` | Outer fold of OOF prediction |
| `subject` | Participant |
| `y_true` | 1=ME, 0=MI |
| `y_pred` | Hard prediction |
| `y_score` | Continuous score/probability for ROC-AUC |
| `run` / `movement` / `pair_id` | Epoch metadata |
| `epoch_index` | Index into analysis matrix |

### `participant_metrics.csv`

Per-participant metrics from OOF predictions (equal weight in primary endpoint):  
`balanced_accuracy`, `roc_auc`, `macro_f1`, `sensitivity`, `specificity`, `average_precision`, `mcc`, `accuracy`, `n_epochs`, plus `experiment`/`model`/`subject`.

### `bootstrap_summary.csv`

| Column | Meaning |
|---|---|
| `metric` | Metric name |
| `mean` | Observed participant-mean |
| `bootstrap_mean` | Mean across participant bootstrap draws |
| `ci_low` / `ci_high` | 2.5 / 97.5 percentiles |
| `n_bootstrap` | Resamples |
| `n_participants` | Cohort size |

### `feature_metadata.csv`

| Column | Meaning |
|---|---|
| `feature_name` | Deterministic name e.g. `C3_mu`, `C4_beta` |

### `inner_tuning.csv` / `fold_metrics.csv`

Inner CV best params / scores and outer-fold pooled metrics (see files).

### `summary.json`

Participant-mean metric dict for the analysis.

---

## `results/pilot_m2/comparisons/`

### `e00_vs_e01_participant.csv`

| Column | Meaning |
|---|---|
| `subject` | Participant |
| `e00` / `e01` | Participant balanced accuracy |
| `difference_e01_minus_e00` | Paired difference |

### `e00_vs_e01_signflip.json`

Participant-level sign-flip test on differences (`observed_mean_difference`, `p_value_plusone`, etc.). Engineering validation on pilot only.

---

## `results/pilot_m2/e03/`

### `roi_summary.csv` / `channel_summary_fdr.csv`

| Column | Meaning |
|---|---|
| `band` | `mu` or `beta` |
| `roi` or `channel` | ROI name or electrode |
| `n` | Participants contributing |
| `mean` / `std` | ME−MI ERD summary |
| `ci_low` / `ci_high` | Empirical participant percentiles |
| `p_uncorrected` | Wilcoxon / fallback test |
| `p_fdr` / `reject_fdr` | BH-FDR across reported tests |

### `laterality.csv`

Unilateral contralateral−ipsilateral ERD summaries by subject/band/movement.

---

## `results/pilot_m2/e04/`

Exploratory only. `participant_heterogeneity.csv` joins ranks/metrics with correlates; `exploratory_correlations.csv` has Spearman ρ + FDR.

---

## `results/pilot_m2/e05/threshold_cohorts.csv`

| Column | Meaning |
|---|---|
| `threshold` | `none` / `150uv` / `200uv` |
| `n_epochs` | Epochs after threshold |
| `n_e01_eligible` | Primary-eligible count at that threshold |

`spatial_control_channels.json` freezes the 21-channel peripheral set and rationale.

---

## `results/pilot_m2/e08/`

Fixed-order diagnostics (characterize confound; do not remove it):

- `by_run.csv` — precue mu/beta and PTP by absolute run
- `by_repetition.csv` — condition × family × repetition
- `matched_pairs.csv` — adjacent ME/MI pair summaries (`03-04` … `13-14`)

---

## `results/benchmarks/e07_20perm_benchmark.json`

| Field | Meaning |
|---|---|
| `n_permutations` | 20 |
| `n_eligible_subjects` / `n_epochs` | Cohort size used |
| `wall_time_sec` | Benchmark wall clock |
| `sec_per_permutation` | Mean cost |
| `extrapolated_1000_sec` / `_hours` | Linear extrapolation |
| `null_balanced_accuracy` | Per-perm participant-mean BAcc under matched-pair swaps |
| `recommendation` | `TRUBA` vs local guidance |

---

## Label / band conventions (global)

- **Condition label:** run-defined; T1/T2 never encode ME/MI.
- **Bands:** mu = `[8,13)` Hz; beta = `[13,30]` Hz (13 Hz in beta only).
- **E01 features:** `10*log10(P_task/P_baseline)`; task 0.5–3.5 s; baseline −2.0–−0.5 s.
- **E00 features:** log band power on −2.0–−0.5 s only (pre-cue run-state control).
