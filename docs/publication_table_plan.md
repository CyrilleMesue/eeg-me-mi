# Publication table plan

Recommend tables that add value beyond Figures 1–5. Do **not** duplicate every plotted value.

Freeze: `analysis-complete-pre-manuscript` (`6d0ce7a`).

---

## Table 1 — Cohort and analysis overview

**Purpose:** One-place definition of who enters which analysis.

| Suggested columns | Source |
|---|---|
| Analysis | name (E00, E01 primary, E02 movements, E05 thresholds, spatial control, sampling-rate, etc.) |
| Eligibility rule | frozen QC / cohort JSON |
| N participants | frozen summaries |
| N epochs retained (if relevant) | frozen summaries / rejection audit |
| Feature definition | window + channels (brief) |
| Primary endpoint | BAcc (participant-mean) where applicable |

**Value beyond figures:** Yes — Fig S1 is schematic only; Table 1 carries exact Ns readers need without hunting panels.

---

## Table 2 — Primary and comparator classification metrics

**Purpose:** Exact numeric companion to Figure 2B/2D and Figure S2.

| Columns | Notes |
|---|---|
| Model | Dummy, CSP-LDA, Riemannian-LR, ERD-LR (primary) |
| N | 102 |
| BAcc (primary) | mean + 95% bootstrap CI |
| ROC-AUC, Macro-F1, Sensitivity, Specificity, MCC | point estimates; label secondary/descriptive |
| E07 plus-one p (ERD-LR row only) | p = 0.000999 |

**Value beyond figures:** High — manuscript text will cite exact decimals; figure panels round for display.

**Relation to S2:** If Table 2 is included, Figure S2 can be omitted (or kept only if journal wants a visual appendix table).

---

## Table 3 — Robustness / sensitivity summary

**Purpose:** Compact numeric companion to Figure 5A–B and S8/S11.

| Columns | Source |
|---|---|
| Analysis | artifact none/150/200; strict; first 60 s; all events; sampling-rate excl. 128 Hz |
| N | frozen |
| BAcc | mean |
| 95% bootstrap CI | where available |
| Δ vs primary | optional, if computed from frozen means only |

**Value beyond figures:** Moderate–high for Methods/Results clarity; Figure 5 already shows the pattern.

---

## Optional tables (prefer over extra figures)

| Table | Content | Prefer over |
|---|---|---|
| Table S1 | Full E03 ROI + laterality numeric summary | Expanding S6 into main |
| Table S2 | Full rejection audit counts (ME/MI × movement) | Extra rejection figure panels |
| Table S3 | E08 matched-pair numeric diagnostics | Cherry-picked extra E08 plots |

---

## Not recommended as tables

- Full 1,000 E07 null values (keep as source CSV only).
- Per-participant BAcc lists in print (provide as source_data / supplement CSV).
- Spatial-control confirmatory p-value (not in freeze; do not invent).
