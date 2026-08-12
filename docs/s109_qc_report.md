# S109 QC report (remediation — eligibility unchanged)

## Scope

Targeted amplitude/unit diagnostics for PhysioNet EEGMMIDB **S109**.  
**No eligibility change. No bad-channel rule introduced. No model performance consulted.**

## Frozen pipeline notes

- MNE loads EDF in SI volts; PhysioNet EDF `orig_units` report **µV**.
- PTP thresholding uses µV (`ptp * 1e6` compared to `reject_peak_to_peak_uv=200`).
- Stages reported: raw EDF (MNE volts), after average reference, after resample+FIR (80 Hz, 8–30 Hz zero-phase).

## S109 summary (after filter/resample)

| Metric | Value |
|---|---|
| Epochs formed | 180 |
| Epochs ≤ 200 µV | **0** |
| Max-PTP min / median / max (µV) | 639.2 / 809.4 / 1016.6 |
| Channel attaining max on every epoch | **C4 (180/180)** |
| Median proportion of channels > 200 µV | ≈ 0.048 (≈1/21) |

Raw-stage (pre-filter) max-PTP is already extreme (median ≈ 705 µV), so the
elevation is **not** created by filtering alone.

## Neighbor comparison (S105–S108)

| Metric | Value |
|---|---|
| Neighbor median-of-medians max-PTP | ≈ 111 µV |
| Neighbor p95 max-PTP | ≈ 274 µV |

Neighbors under the identical pipeline are typically near/below the 200 µV
screen; S109 is an order of magnitude more extreme on the worst channel.

## Unit / preprocessing bug assessment

| Check | Result |
|---|---|
| EDF physical units | µV (header) |
| MNE representation | SI volts (standard) |
| Threshold scaling | µV via `* 1e6` |
| Neighbor amplitudes under same code | Normal / near-threshold |
| Systematic global unit bug | **Not detected** |

**Conclusion:** S109 exclusion under the frozen 200 µV rule remains
**technically justified** as genuine extreme amplitudes (especially C4). No
systematic unit/preprocessing bug requiring global cohort recomputation was
found.

## Proposed rule (NOT implemented — scientific review required)

A *possible* future sensitivity rule (for review only):

> If a participant fails the primary PTP screen solely because a single named
> channel exceeds threshold on essentially all epochs, while the remaining
> sensorimotor channels would retain epochs under the same threshold, flag for
> optional single-channel rejection sensitivity.

**This rule is not adopted.** Implementing it would change eligibility and
requires explicit scientific approval (STOP condition #6).

## Machine-readable tables

- `results/s109_qc/epoch_ptp_by_stage.csv`
- `results/s109_qc/channel_ptp_summaries.csv`
- `results/s109_qc/unit_metadata.json`
- `results/s109_qc/s109_summary.json`
