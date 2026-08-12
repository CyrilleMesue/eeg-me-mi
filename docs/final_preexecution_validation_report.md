# Final pre-execution validation report

**Status:** Temporal-support repair complete and locally validated.  
**GO/NO-GO:** **NO-GO for definitive execution until TRUBA 10-perm smoke succeeds** (see blockers).

This amendment was made **before** inspecting definitive scientific outcomes and is
justified solely from the measured zero-phase FIR impulse support.

---

## Temporal repair

### Measured support (frozen)

| Quantity | Value |
|---|---|
| FIR length @ 80 Hz | 133 taps |
| Half-support | 66 samples = **0.825 s** |
| Safe boundary | ±**(66+1)/80 = ±0.8375 s** |

### Final confirmatory windows

| Window | Interval |
|---|---|
| E00 pre-cue log-power | **[-2.0, -0.8375] s** |
| E01 ERD baseline/reference | **[-2.0, -0.8375] s** |
| E01 / CSP / Riemann task | **[+0.8375, +3.5] s** |
| Excluded cue-adjacent | **(-0.8375, +0.8375) s** |

E00 remains absolute/log mu/beta power (not ERD). Sharing the same safe pre-cue
interval for E00 power and the E01 reference is an advantage of the repaired
design.

Historical `baseline_tmax=-0.5` and `task_tmin=+0.5` are **rejected** by
`e01_windows_from_preproc` / feature extractors.

Cache fingerprint version bumped to **v4** so incompatible feature windows are
not silently reused.

### Tests

- Baseline contamination (post-cue impulse → safe baseline): pass
- Task contamination (pre-cue in-support impulse → safe task ≥ +0.8375): pass
- Boundary sample indices at ±0.8375 (80 Hz): pass
- Old unsafe windows rejected: pass
- Full suite: **64 passed**, 0 failed, 0 skipped (~6.4 s)

Plan backup: `docs/final_analysis_plan.md.bak-2026-08-13-pre-fir-e01-windows`

---

## S109

| Decision | Status |
|---|---|
| Primary exclusion under 200 µV whole-epoch PTP | **Retained** |
| C4 / single-channel rescue rule | **Not implemented** |
| Unit/preprocessing bug | Not detected |
| Extreme amplitude under frozen pipeline | Genuine |

---

## Tests

| Metric | Value |
|---|---|
| Passed | **64** |
| Failed | **0** |
| Skipped | **0** |

Local engineering smoke (not definitive): `run-e07` on
`configs/e07_local_smoke.yaml` with **5** permutations completed using the
repaired E01 windows; observed statistic and nulls share the same feature path.

---

## Provenance

| Item | Value |
|---|---|
| Execution-candidate tag | `m2-preexec-fir-windows-candidate` |
| Clean tree | yes |
| Config checksum (SHA-256) | `6c619f6039964085506c22f38d5b35647afacac1143e122868704f37438f795a` |
| Cache version | **4** (includes baseline/task/e00 window fields) |

---

## TRUBA smoke

| Item | Result |
|---|---|
| Requested | `sbatch --export=N_PERM=10 slurm/e07_final.sbatch` |
| Host | `cnjume` workstation |
| `sbatch` available | **No** |
| Job ID | *not submitted* |
| Outcome | **Blocked** — cannot verify TRUBA environment from this host |

### Local substitute smoke (engineering only; not TRUBA)

| Metric | Value |
|---|---|
| Command | `run-e07 configs/e07_local_smoke.yaml --n-permutations 5` |
| Wall time | ≈ 29.6 s |
| CPU | ≈ 246% of one core |
| Peak RSS | ≈ 612 MB |
| Completion | `complete: true`, 5/5 perms |
| Notes | Subjects 1–8 only; not a substitute for full-cohort TRUBA timing |

---

## Remaining blockers

1. **TRUBA 10-permutation smoke not executed** — `sbatch` unavailable on this
   host. Required before GO for definitive E07×1000 / full analyses.
2. No other scientific blockers identified for the FIR-window amendment itself.

---

## STOP

Do **not** run definitive E00–E06/E08, E07×1000, or interpret full scientific
performance until:

1. this commit/tag is reviewed;
2. TRUBA `N_PERM=10` smoke succeeds with completion manifest / provenance checks.
