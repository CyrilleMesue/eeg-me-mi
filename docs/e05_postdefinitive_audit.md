# E05 post-definitive audit

**Parent definitive tag:** `m2-preexec-fir-windows-candidate` (`3b615ed`)  
**Purpose:** Determine what E05 was supposed to contain vs what definitive `run_full` actually produced.  
**This audit does not change primary E01/E07.**

---

## A. What E05 was prespecified to contain

From `docs/final_analysis_plan.md` (frozen before definitive outcomes):

1. **Artifact-threshold sensitivity (mandatory):**
   - no amplitude rejection;
   - 150 µV peak-to-peak;
   - 200 µV (primary).
2. Shared **minimally processed** participant caches so thresholds can be applied without reloading all EDFs.
3. **Spatial-plausibility control:** matched-size (21) non-sensorimotor/peripheral channel set, frozen in `eeg_me_mi.rois` before control decoding results were inspected; decode with the analogous mu/beta ERD representation for diagnostic comparison to the sensorimotor primary representation.

Pilot path (`src/eeg_me_mi/pilot.py`) implemented both **threshold decoding** and **spatial-control decoding** (ERD-LR nested CV exports under `e05/{none,150uv,200uv}` and `e05/spatial_control`).

---

## B. What was implemented in definitive `run_full`

`src/eeg_me_mi/run_full.py` E05 block (lines ~461–487) only:

1. Builds minimal-mode epochs for each of `none` / `150uv` / `200uv`;
2. Writes **cohort counts** to `e05/threshold_cohorts.csv`;
3. Writes **channel provenance** to `e05/spatial_control_channels.json` via `spatial_control_rationale()`.

It does **not** call `run_nested_group_cv`, does **not** extract ERD features per threshold, and does **not** run spatial-control decoding.

---

## C. What was executed in the accepted definitive job

Definitive non-E07 job **6237864** ran `run-full … --skip-e07` on TRUBA at the frozen tag.

Executed for E05:

- threshold cohort enumeration;
- spatial-control channel JSON emission.

Not executed:

- artifact-sensitivity decoding under none / 150 / 200 µV;
- spatial-control ERD-LR decoding;
- sensorimotor−spatial paired participant comparison.

---

## D. What outputs currently exist

Under immutable `results/definitive/full/e05/`:

| File | Present | Content |
|---|---|---|
| `threshold_cohorts.csv` | yes | `none`/`150uv`/`200uv` epoch + E01-eligible N counts only |
| `spatial_control_channels.json` | yes | frozen 21-channel control set + rationale |
| `none/` decoding exports | **no** | |
| `150uv/` decoding exports | **no** | |
| `200uv/` decoding exports | **no** | |
| `spatial_control/` decoding exports | **no** | |

No alternate location in the definitive package contains E05 decoding OOF/summaries (search of review package + `results/definitive`).

Definitive `threshold_cohorts.csv` values:

| threshold | n_epochs | n_e01_eligible |
|---|---:|---:|
| none | 17257 | 102 |
| 150uv | 15290 | 94 |
| 200uv | 17257 | 102 |

---

## E. What remains missing (and a related implementation bug)

### Missing (prespecified, not executed)

1. Artifact-sensitivity ERD-LR decoding for none / 150 µV / 200 µV.
2. Spatial-control ERD-LR decoding on the frozen peripheral 21-channel set at 200 µV.
3. Participant-paired sensorimotor vs spatial-control BAcc differences (effect + CI; no new confirmatory p-framework).

### Bug explaining identical none vs 200 µV cohort counts

In `build_epoch_dataset` (`mode="minimal"`):

```text
thr = threshold_uv if threshold_uv is not None else preproc.get("reject_peak_to_peak_uv")
```

The definitive E05 loop passes `threshold_uv=None` for the **"none"** condition. That `None` is treated as “use config default,” which is **200 µV**, not “no rejection.”

Therefore the definitive `none` row is **not** a true no-rejection condition; it is a duplicate of the 200 µV application. Local reproduction: `threshold_uv=None` and `threshold_uv=200.0` retain identical epoch counts; true no-rejection via `threshold_uv=0.0` retains more epochs and shows `n(ptp>200)>0`.

### Impact on frozen primary E01/E07

**Supplementary E05 only.**

Primary E01 passes an **explicit** `threshold_uv=float(config.preprocessing["reject_peak_to_peak_uv"])` (=200). E07 uses that same E01 cohort/statistic. The `None`→200 fallback does **not** alter the primary path.

**STOP-condition verdict:** proceed with corrected post-definitive E05 completion; do **not** invalidate E01/E07.

---

## Next actions (this task)

1. Reconcile threshold epoch counts with distinct cache/application identities (`results/postdefinitive_e05/`).
2. Fix the minimal-mode threshold sentinel so explicit `None` means no rejection (post-definitive commit; does not rewrite definitive outputs).
3. Execute the missing prespecified decoding under `results/postdefinitive_e05/` against the definitive cache where possible, including 200 µV reproduction of primary E01 BAcc within numerical tolerance.
