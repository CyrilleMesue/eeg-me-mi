# Milestone 2 completion report

Date: 2026-08-12  
Status: **complete** (stop condition met)  
Git checkpoint before M2: `4d68320` (Milestone 1)  
Plan backup: `docs/final_analysis_plan.md.bak-2026-08-12-pre-m2`

**Not done (by design):** definitive full scientific execution; final 1,000-permutation E07; manuscript writing.

---

## Scientific-plan synchronization

Updated `docs/final_analysis_plan.md` to match the independently reviewed Milestone-1 decisions:

| Topic | Before | After (synchronized) |
|---|---|---|
| Primary eligibility | 2-of-3 repetitions / weak post-reject rule | ≥30 ME & ≥30 MI; ≥2 matched pairs with uni+bi; movement composition |
| Primary E01 model | Mentioned fold-local feature selection | 42 ERD → StandardScaler → L2 LR; C∈{0.01,0.1,1,10}; **no SelectKBest** |
| E00 naming | “baseline-only” | **pre-cue run-state decoding control** (not biologically neutral) |
| E02 | Vague | ≥15/mode, ≥2 matched pairs per movement analysis |
| Strict cohort | All-12 complete-case only | All-12 valid + ≥40/mode + ≥20/cell + ≥80% expected (protocol-consistency note added) |
| Compute policy | Implicit TRUBA | Local default; TRUBA for empirically long jobs |

---

## Full data audit

- Subjects 1–109 × runs 3–14 = **1,308** EDFs downloaded/cached (`eeg-me-mi download configs/full.yaml`; restartable; 26 timeouts recovered on retry).
- Structural validity: **1,308 / 1,308** runs usable under fatal rules.
- Watchlist (independent assessment; **not** auto-excluded):

| Subject | Finding | E01 eligible? |
|---:|---|---|
| 38 | Normal 160 Hz / 64 ch | Yes |
| 88 | **128 Hz** (flagged); still structurally recoverable | Yes |
| 89 | Normal 160 Hz | Yes |
| 92 | **128 Hz** (flagged) | Yes |
| 100 | **128 Hz** (flagged) | Yes |
| 104 | Normal 160 Hz | Yes |

128 Hz recordings are annotated `unexpected_sfreq_128.0|watchlist_sfreq_anomaly` but remain structurally valid because required channels/annotations exist; resampling in preprocess handles the rate.

Outputs: `results/full_cohort_audit/{raw_data_audit,anomaly_report,download_manifest}.csv`.

---

## Primary cohort

- **E01 eligible: 102 / 109**
- Excluded (performance-blind):

| Subject | Reason |
|---:|---|
| 9 | Insufficient matched pairs / unilateral / epoch counts |
| 13 | Insufficient ME epochs |
| 17, 24, 48 | Insufficient ME and/or MI epochs |
| 22 | Movement composition + insufficient ME |
| 109 | NO_EPOCHS after 200 µV (all cues exceed threshold; QC shows PTP maxima ~0.8–1.0 mV) |

Sensitivity flags: ≥20/mode = 103; ≥40/mode = 101.

Frozen outer folds: `results/full_cohort_audit/fold_assignments_e01_primary.csv` (5-fold, seed 2026).

---

## Movement cohorts (E02)

| Analysis | Eligible n |
|---|---:|
| left_fist | 93 |
| right_fist | 94 |
| both_fists | 93 |
| both_feet | 92 |
| unilateral | 102 |
| bilateral | 102 |

---

## Strict sensitivity cohort

**n = 67** (`eligible_strict`).

---

## Artifact / QC

- Primary threshold 200 µV via shared **minimal** caches + PTP filter.
- Rejection QC: `results/full_cohort_audit/rejection_qc.csv`.
- Human-readable: `docs/full_cohort_qc_report.md`.

---

## Implementation status

| Component | Status |
|---|---|
| Plan sync + backup | Done |
| `eeg-me-mi download` | Done (parallel, restartable, manifest) |
| Full audit / eligibility / folds | Done |
| E01 Dummy / ERD-LR / CSP-LDA / Riemann | Done |
| E00 + E00−E01 compare + sign-flip test | Done |
| E02 movement decoding | Done |
| E03 ROI/laterality/FDR maps | Done |
| E04 exploratory heterogeneity | Done |
| E05 thresholds + spatial-control set | Done |
| E06 first-60-s vs all | Done |
| E07 matched-pair permutation engine + tests | Done |
| E07 20-perm full-cohort **benchmark** | Done |
| E08 drift diagnostics | Done |
| TRUBA sbatch stub (not submitted) | `slurm/e07_1000perm.sbatch` |
| Final 1,000 E07 / full scientific run | **Not executed** |

---

## Automated tests

```text
45 passed
```

Expanded coverage: CSP/Riemann fold-local CV, movement/strict eligibility, FDR helper, ROI/spatial-control freeze, E06 mask, matched-pair permutation structure/reproducibility, sign-flip test.

---

## Local pilot (engineering only)

Config: `configs/pilot_m2.yaml` (subjects 1–8).  
Output: `results/pilot_m2/`.

Engineering smoke metrics (do **not** interpret scientifically):

| Model | Participant-mean BAcc |
|---|---:|
| E00 precue log-BP LR | 0.518 |
| E01 Dummy | 0.500 |
| E01 ERD-LR | 0.609 |
| E01 CSP-LDA | 0.516 |
| E01 Riemann LR | 0.536 |

All of E02–E08 paths produced outputs; E07 smoke (5 perms) null BAcc ≈ 0.46–0.51.  
Wall ~7.3 min; tracemalloc peak ~664 MB.

---

## Resource benchmarks

### E07 20-permutation full eligible cohort

File: `results/benchmarks/e07_20perm_benchmark.json`

| Quantity | Value |
|---|---|
| Eligible subjects | 102 |
| Epochs | 17,121 |
| Wall time (20 perms) | **325.3 s** |
| s / permutation | **16.3** |
| Extrapolated 1,000 | **~4.52 hours** |
| Null mean BAcc | 0.500 |

---

## Compute recommendation

| Job | Where | Why |
|---|---|---|
| Download / audit / eligibility | **Local** | Done; restartable |
| Full E00/E01/E02–E06/E08 scientific run | **Local first**, optional TRUBA if parallelized later | Single nested CV passes are minutes-scale |
| Final E07 **1,000** permutations | **TRUBA** | ~4.5 h extrapolated; would materially occupy the workstation; stub prepared at `slurm/e07_1000perm.sbatch` (**do not submit yet**) |

---

## Generated outputs

```
docs/final_analysis_plan.md
docs/final_analysis_plan.md.bak-2026-08-12-pre-m2
docs/full_cohort_qc_report.md
docs/cursor_milestone2_report.md
results/full_cohort_audit/
  raw_data_audit.csv
  anomaly_report.csv
  download_manifest.csv
  participant_eligibility.csv
  fold_assignments_e01_primary.csv
  e02_cohort_sizes.csv
  rejection_qc.csv
  cohort_summary.json
results/pilot_m2/{e00,e01,e02,e03,e04,e05,e06,e07,e08,comparisons,qc}/
results/benchmarks/e07_20perm_benchmark.json
slurm/e07_1000perm.sbatch
configs/{full,pilot_m2}.yaml
```

---

## Known issues

1. S109: all task epochs exceed 200 µV PTP → excluded as NO_EPOCHS (rule-correct; unusual amplitude).
2. S088/S092/S100: native 128 Hz; kept under current structural rule; document in paper methods.
3. Annotation edge warnings from MNE on some EDFs (limited expanding annotations).
4. `concatenate_epochs` drops Annotations; metadata columns are the analysis record.
5. E07 benchmark tracemalloc underestimates RSS (features already materialized); wall-time is the planning metric.
6. Editable install may still need `PYTHONPATH=src` in this environment.

---

## Exact commands

```bash
cd /home/cnjume/Desktop/eeg-me-mi
PYTHONPATH=src .venv/bin/pytest -q
PYTHONPATH=src .venv/bin/python -m eeg_me_mi.cli download configs/full.yaml
PYTHONPATH=src .venv/bin/python -m eeg_me_mi.cli audit configs/full.yaml --no-download
PYTHONPATH=src .venv/bin/python -m eeg_me_mi.cli pilot configs/pilot_m2.yaml --no-download
PYTHONPATH=src .venv/bin/python -m eeg_me_mi.cli benchmark-e07 configs/full.yaml --n-permutations 20 --no-download
# Final 1000 — NOT yet:
# sbatch slurm/e07_1000perm.sbatch
```

---

## Stop

Milestone 2 is complete. Awaiting scientific review before any definitive full analysis or 1,000-permutation TRUBA submission.
