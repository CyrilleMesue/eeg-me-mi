# Milestone 1 completion report

Date: 2026-08-12  
Status: **complete** — tests pass; E00/E01 toy pipeline succeeded; required outputs written.  
Stop condition met: no full-cohort analysis and no TRUBA work were started.

## Repository changes

Refactored the Colab-style historical reanalysis into a configuration-driven package under `src/eeg_me_mi/`, while preserving provenance:

| Module | Role |
|---|---|
| `protocol.py` | Frozen EEGMMIDB run/condition/movement/pair mappings |
| `config.py` | YAML schema loading |
| `audit.py` | Per-run raw-data audit → `raw_data_audit.csv` |
| `preprocess.py` | Participant-level preprocess + epoch cache (16 GB–safe) |
| `eligibility.py` | Milestone-1 eligibility rule + ≥20/≥40 sensitivity flags |
| `features.py` | E01 ERD (42) and E00 pre-cue log band power (42) |
| `models.py` | Dummy + StandardScaler + L2 LR (no `SelectKBest`) |
| `cv.py` | Nested participant-disjoint CV with leakage assertions |
| `metrics.py` | Participant-mean metrics + participant bootstrap |
| `compare.py` | E01 − E00 participant comparison |
| `provenance.py` | Config snapshot, versions, git hash |
| `pipeline.py` / `cli.py` | End-to-end runner |

Historical artifacts remain untouched in `historical/`. Prior scientific docs remain in `docs/`.

**Eligibility note:** Milestone 1 implements the task specification (≥30 epochs/mode, ≥2 matched pairs with uni+bi, movement composition), which differs from the older complete-case / 2-of-3-repetition wording in `docs/final_analysis_plan.md`. Sync that plan in Milestone 2.

## Data audit

- Attempted: subjects **1–8**, runs **3–14** (96 recordings).
- All 96 were downloaded into `data/physionet_eegmmidb/` and marked **structurally valid**.
- Watchlist IDs (S038, S088, S089, S092, S100, S104) were not in the toy cohort; no auto-exclusion logic was applied.
- Rejection (200 µV PTP): execution 701/720 kept; imagery 709/720 kept.

## Toy cohort

Subjects **1, 2, 3, 4, 5, 6, 7, 8**.

Chosen as the earliest consecutive IDs after audit (engineering validation), not by expected classification performance. All eight met primary eligibility.

## Eligibility

| Subject | ME epochs | MI epochs | Usable pairs | Primary |
|---:|---:|---:|---:|---|
| 1 | 90 | 90 | 6 | ELIGIBLE |
| 2 | 80 | 87 | 6 | ELIGIBLE |
| 3 | 88 | 86 | 6 | ELIGIBLE |
| 4 | 90 | 90 | 6 | ELIGIBLE |
| 5 | 90 | 89 | 6 | ELIGIBLE |
| 6 | 84 | 89 | 6 | ELIGIBLE |
| 7 | 89 | 88 | 6 | ELIGIBLE |
| 8 | 90 | 90 | 6 | ELIGIBLE |

Eligible epoch total used in CV: **1410**.

## Automated tests

```bash
PYTHONPATH=src .venv/bin/pytest -q
# 38 passed
```

Coverage includes protocol mapping, leakage/disjoint folds, scaler/tuning boundaries, E00/E01 feature constraints, synthetic eligibility cases, metric aggregation, participant bootstrap, config loading, and reproducibility of nested-CV scores.

## E00 engineering result

Pre-cue run-state decoding (log mu/beta power, −2.0…−0.5 s), same folds/model class as E01.

- Participant-mean balanced accuracy: **0.518**
- Bootstrap 95% CI (50 resamples): **[0.501, 0.537]**

Do **not** interpret scientifically from this toy cohort.

## E01 engineering result

Task-period ERD (42 features), StandardScaler + L2 LR, C ∈ {0.01, 0.1, 1, 10}, no `SelectKBest`.

- Participant-mean balanced accuracy: **0.609**
- Bootstrap 95% CI (50 resamples): **[0.587, 0.639]**

Do **not** interpret scientifically from this toy cohort.

## E00 vs E01 (engineering check only)

Mean participant difference (E01 − E00) balanced accuracy: **0.091**  
Bootstrap 95% CI: **[0.063, 0.123]** (n=50). Pipeline only; not a scientific claim.

## Resource benchmark

| Quantity | Value |
|---|---|
| Peak RAM (approx.) | ~498 MB |
| Audit wall time | ~1514 s (dominated by PhysioNet download) |
| Preprocess | ~30 s (after cache/download) |
| Feature extraction | ~36 s |
| E01 nested CV | ~1.3 s |
| E00 nested CV | ~1.7 s |
| Bootstrap | ~0.02 s |
| Total toy runtime | ~1583 s (~26 min, first download) |

Comfortable on 16 GB RAM. Subsequent runs should skip download time via local EDF + participant epoch caches under `cache/`.

## Generated files

```
results/toy/
  audit/raw_data_audit.csv
  audit/participant_eligibility.csv
  audit/anomaly_watchlist_rows.csv
  e00/feature_metadata.csv
  e00/oof_predictions.csv
  e00/participant_metrics.csv
  e00/bootstrap_summary.csv
  e00/summary.json
  e01/feature_metadata.csv
  e01/oof_predictions.csv
  e01/participant_metrics.csv
  e01/bootstrap_summary.csv
  e01/summary.json
  comparisons/e00_vs_e01_participant.csv
  comparisons/e00_vs_e01_bootstrap_summary.csv
  qc/fold_assignments.csv
  qc/rejection_qc.csv
  qc/rejection_summary.json
  qc/config_snapshot.yaml
  qc/software_versions.json
  qc/run_metadata.json
  qc/resource_benchmark.json
```

Also: dummy-model OOF/metrics, inner-tuning tables, bootstrap draws, rejection-by-condition CSV.

## Known issues

1. First-run audit downloads are sequential and slow via PhysioNet/pooch; separate bulk-download helper would help.
2. `mne.concatenate_epochs` warns that annotations are dropped; metadata columns are preserved and used instead.
3. sklearn 1.9 deprecates explicit `penalty='l2'` (fixed to default L2 in `models.py` after the toy run).
4. Milestone-1 eligibility vs `docs/final_analysis_plan.md` wording still needs formal plan sync.
5. Watchlist anomaly reproduction deferred to a broader audit (not in subjects 1–8).
6. Package was run via `PYTHONPATH=src` rather than editable install in this environment (sandbox pip constraints).

## Recommendations for Milestone 2

1. Sync `docs/final_analysis_plan.md` eligibility to the implemented Milestone-1 rule (or explicitly version both).
2. Add a dedicated download/cache-warmup CLI; keep audit read-only when files exist.
3. Expand raw audit to all 109 subjects and document watchlist anomalies independently.
4. Add pilot config run (still local) before TRUBA; keep identical outer folds for E00/E01.
5. Implement E05 threshold caches from shared minimally processed epochs (150 µV / no-reject).
6. Only then schedule TRUBA full-matrix jobs; keep E02–E07 behind the validated foundation.

## Reproduce the toy run

```bash
cd /home/cnjume/Desktop/eeg-me-mi
python3 -m venv .venv
.venv/bin/pip install -e '.[test]'
PYTHONPATH=src .venv/bin/pytest -q
PYTHONPATH=src .venv/bin/python -m eeg_me_mi.cli configs/toy.yaml
# or, after editable install:
# eeg-me-mi configs/toy.yaml
```

Outputs land in `results/toy/`. Re-runs reuse `data/physionet_eegmmidb/` and `cache/` unless `--force-preprocess` is passed.
