# Final two sensitivity checks / audits (pre-manuscript)

## Provenance

| Field | Value |
|---|---|
| Parent definitive tag | `m2-preexec-fir-windows-candidate` (`3b615ed`) |
| Parent postdefinitive tag | `postdefinitive-e05-controls` (`bc51b62`) |
| Outputs root | `results/final_sensitivity_checks/` |
| Immutable trees | `results/definitive/`, `results/postdefinitive_e05/` **not overwritten** |
| Random seed | 2026 |
| Config | `configs/full.yaml` |
| Execution | TRUBA login-node completion after Orfoz queue stall; scientific code identical to `scripts/run_final_sensitivity_checks.py` |

See also `results/final_sensitivity_checks/provenance.json`.

## Sampling-rate sensitivity

### Rationale
Assess whether inclusion of three EEGMMIDB participants recorded at 128 Hz (S088, S092, S100) materially affects the frozen primary ERD-LR result. **Sensitivity only** — does not replace primary N=102.

### Excluded IDs
S088, S092, S100 (all present in frozen E01 primary cohort).

### Fold handling
Frozen outer fold assignments from `results/.../e01/erd_lr/fold_assignments.csv` were **filtered**, not regenerated:

| Fold | n_test before | n_test after | Removed from test |
|---|---:|---:|---|
| 1 | 21 | 21 | — |
| 2 | 21 | 19 | 88, 100 |
| 3 | 20 | 20 | — |
| 4 | 20 | 20 | — |
| 5 | 20 | 19 | 92 |

Remaining participant membership unchanged (`remaining_test_unchanged=True` for all folds). Inner tuning uses `seed + fold` on the reduced outer-train set.

### Results

| Quantity | Primary | Sensitivity |
|---|---:|---:|
| N | 102 | **99** |
| Participant-mean BAcc | 0.6179239767 | **0.6208994043** |
| Bootstrap 95% CI | [0.603553, 0.632899] | **[0.606834, 0.635513]** |
| ROC-AUC | (primary E01) | 0.673021 |
| Macro-F1 | | 0.612702 |
| MCC | | 0.248350 |
| Accuracy | | 0.620854 |

Absolute BAcc difference vs primary: **0.002975**.

Descriptive paired Δ (sens − primary) on common N=99: mean **0.000523**, bootstrap 95% CI **[−0.00155, 0.00249]** (no p-value; not confirmatory).

### Conclusion
**STABLE**

## Label-specific rejection audit

Frozen 200 µV PTP rule applied to minimal-cache epochs (`ptp_uv > 200`). Audit only — threshold/cohort/model unchanged.

### Primary E01 cohort (N=102 subjects’ epochs)

| Condition | Before | Rejected | Retained | Rejection proportion |
|---|---:|---:|---:|---:|
| ME | 9110 | 662 | 8448 | **0.072667** |
| MI | 9079 | 587 | 8492 | **0.064655** |

Absolute difference (ME − MI): **0.008013**.

### Full attempted dataset

| Condition | Before | Rejected | Retained | Rejection proportion |
|---|---:|---:|---:|---:|
| ME | 9731 | 1145 | 8586 | 0.117665 |
| MI | 9709 | 1038 | 8671 | 0.106911 |

### Participant-paired rejection difference (primary cohort)
- N = 102  
- Mean (ME − MI) = 0.008213  
- Median = 0.0  
- IQR = [0.0, 0.011111]  
- Range = [−0.2398, 0.2667]  
- Bootstrap 95% CI of mean = **[−0.00530, 0.02189]**  
- No confirmatory p-value (not prespecified)

### Movement breakdown (primary cohort)
See `rejection_by_movement_primary_cohort.csv`. Largest descriptive ME−MI gap among listed movements: both_feet (ME 0.0859 vs MI 0.0599). No physiological interpretation.

### Run / matched-pair breakdown
Exported: `rejection_by_run.csv`, `rejection_by_matched_pair.csv`.

### Retained class balance (primary cohort, after 200 µV)
- Retained ME = 8448  
- Retained MI = 8492  
- ME/MI ratio = **0.9948** (no substantial systematic imbalance flagged)

## Reconciliation with existing QC

- Eligibility N=102 matches audit primary subject set.  
- Full-dataset PTP>200 count **2183** / before **19440** matches postdefinitive E05 threshold reconciliation.  
- Note: definitive `rejection_qc.csv` has `n_rejected=0` because `mode=minimal` defers PTP filtering; this audit uses `ptp_uv` metadata (documented, not a discrepancy).  
- `reconcile_ok: true`.

## Impact on frozen primary analysis

**NONE.**

- Primary E01 unchanged: N=102, BAcc=0.6179239767273408  
- E07 not rerun  
- E05 not overwritten  
- Definitive outputs not modified  

## Deviations

1. Orfoz job remained `Priority` despite idle nodes; analyses completed on TRUBA login node with the same script/config/cache.  
2. End-of-run immutability assertion initially used 1e-12 vs rounded reference `0.6179239767` (true stored BAcc differs by ~2.7e-11); tolerance corrected to 1e-9 and immutability JSON written. Scientific outputs were already complete.  
3. Primary-cohort retained epoch sum (16940) exceeds E01 OOF length (16913) by 27 because OOF applies within-subject eligibility filtering; documented in reconciliation.

## Remaining analysis needed before manuscript

**NONE** (for these two prespecified checks).
