# E00 filter support analysis (Milestone-2 remediation)

## Purpose

Quantify the temporal support of the frozen continuous zero-phase FIR filter so
that E00 pre-cue features cannot receive cue/post-cue information via acausal
filtering.

## Frozen preprocessing (actual pipeline)

| Parameter | Value |
|---|---|
| MNE version | 1.12.1 |
| Pipeline order | average reference → **resample to 80 Hz** → FIR band-pass |
| `l_freq` / `h_freq` | 8 / 30 Hz |
| Method | FIR (`firwin`), Hamming window |
| Phase | `zero` (one-pass, non-causal, zero-phase) |
| `filter_length` | `auto` |
| Transition (auto) | lower 2.00 Hz; upper 7.50 Hz |

Because filtering occurs **after** resampling, the designed filter is always at
**80 Hz**, including for native 128 Hz and 160 Hz recordings.

## Measured FIR support

### Actual pipeline (`sfreq = 80 Hz`)

| Quantity | Value |
|---|---|
| FIR length | **133 samples** |
| FIR duration | **1.6625 s** |
| Half-support (group delay) | **66 samples = 0.825 s** |
| Empirical half-support (~1e-4 of peak) | 0.825 s |

An impulse at time \(t_0\) influences filtered samples in
\([t_0 - 0.825,\ t_0 + 0.825]\) s.

### If filtering were applied before resampling (counterfactual)

| Native rate | FIR length | Duration | Half-support |
|---|---|---|---|
| 160 Hz | 265 | 1.65625 s | 0.825 s |
| 128 Hz | 213 | 1.6640625 s | 0.828125 s |

Half-support in seconds is essentially unchanged; the binding scientific
quantity for the real pipeline is the **80 Hz** result.

## Implication for historical E00 window `[−2.0, −0.5]`

Contamination from cue onset (\(t \ge 0\)) extends backward to \(t = -0.825\) s.

Overlap with the old E00 interval:

- Contaminated overlap: **`[−0.825, −0.5]`** (0.325 s)
- Therefore the old crop at −0.5 s **does not** prove pre-cue-only features.

**Verdict: the previous E00 window was unsafe under zero-phase filtering.**

## Leakage-safe repair (prespecified)

Keep the shared continuous zero-phase preprocessing (no separate causal E00
filter path required).

Safe inclusive crop excludes the boundary sample at −0.825 s:

\[
t_{\max} = -\frac{\mathrm{half\_samples} + 1}{f_s} = -\frac{67}{80} = -0.8375\ \mathrm{s}
\]

Frozen E00 window:

- **`e00_tmin = −2.0 s`**
- **`e00_tmax = −0.8375 s`**
- Usable length ≈ **1.1625 s** (adequate for Welch mu/beta log-power)

E01 baseline remains `[−2.0, −0.5]` (unchanged). The E00 vs E01 window
difference is a **control-specific necessity** documented here and in
`docs/final_analysis_plan.md`.

## Impulse-test requirement

Synthetic continuous data with a large impulse at/after cue onset, filtered with
the real MNE zero-phase FIR, then epoched and passed through
`extract_e00_log_bandpower_features`, must show negligible E00 feature change
under the safe window. The historical `e00_tmax = −0.5` setting must be rejected
by the extractor. Implemented in `tests/test_remediation.py`.
