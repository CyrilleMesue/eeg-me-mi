# Supplementary figures — final review package

**Freeze:** `analysis-complete-pre-manuscript` (`6d0ce7a`)  
**Generator:** `PYTHONPATH=src python figures_v2/scripts/generate_supplementary_final.py`  
**Main figures 1–5:** not modified in this task.

---

## Old → new numbering map

| Final | Previous V2 | Status |
|---|---|---|
| S1 Cohort eligibility | S1 | **Redesigned** |
| S2 Movement decoding | S3 | Unchanged (exact copy) |
| S3 Channel-level ERD | S4 | Unchanged (exact copy) |
| S4 Laterality | S5 | Unchanged (exact copy) |
| S5 Participant heterogeneity | S6 | **Redesigned** |
| S6 Artifact sensitivity | S7 | Unchanged (exact copy) |
| S7 Rejection audit | S8 | **Minor cleanup** (labels + exact %) |
| S8 E08 diagnostics | S9 | Unchanged (exact copy) |
| S9 Comparator distributions | S11 | Unchanged (exact copy) |
| S10 Duration/sampling participant-level | S10 | **Redesigned** (nonredundant) |
| — | S2 Secondary metrics | **Removed as figure → Table 2** |

---

## Per-figure notes

### S1 — Cohort eligibility
- **Purpose:** Informative eligibility/QC flow with frozen ineligibility reasons and sensitivity subset Ns.
- **Sources:** `results/definitive/full/qc/participant_eligibility.csv`; sampling-rate summary.
- **N:** audited 109; primary 102; ineligible 7; strict 51; sampling-rate 99.
- **Unresolved:** Long compound reason strings are dense but faithful to frozen codes.

### S2 — Movement decoding
- Exact copy of approved V2 S3. N per movement from frozen E02.

### S3 — Channel ERD
- Exact copy of approved V2 S4.

### S4 — Laterality
- Exact copy of approved V2 S5. Secondary.

### S5 — Heterogeneity (exploratory)
- Ranked BAcc; mean |ERD| vs BAcc; retained epochs vs BAcc.
- Spearman ρ from frozen E04 exploratory correlations.
- Rejection-rate vs BAcc correlation was NaN in freeze → omitted (stated in caption).
- **Unresolved:** none blocking.

### S6 — Artifact sensitivity
- Exact copy of approved V2 S7.

### S7 — Rejection audit
- Same science as V2 S8; explicit axis wording; exact ME/MI % on panel A.
- Bootstrap CI descriptive; no confirmatory p.

### S8 — E08 diagnostics
- Exact copy of approved V2 S9. Caption states confound non-removal.

### S9 — Comparators
- Exact copy of approved V2 S11.

### S10 — Duration / sampling participant-level
- **Retained.** Paired primary vs first-60-s (N=102) and primary vs sampling-rate (N=99) scatters.
- Complements main Fig 5A; does not repeat the robustness forest.
- Sources: E06 first60 metrics; `final_sensitivity_checks/sampling_rate/paired_participant_differences.csv`.

---

## Table 2
- Path: `docs/tables/table_2_secondary_metrics.csv` (+ `.md` preview)
- Primary ERD-LR secondary metrics from frozen `e01/erd_lr/summary.json`.

---

## Validation
See `figures_v2/previews/supplementary_final_validation.txt`.
