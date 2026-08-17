# Publication figure review

**Status:** Candidate figures generated for researcher + ChatGPT review.  
**Scientific freeze (immutable):** `analysis-complete-pre-manuscript` @ `6d0ce7a`  
**Suggested future tag (do not apply yet):** `publication-figures-v1`  
**Regenerate:** `PYTHONPATH=src python figures/scripts/generate_all_figures.py`  
**Validate:** `PYTHONPATH=src python figures/scripts/validate_figures.py` → **58/58 passed** (last run).  
**Contact sheet:** `figures/previews/publication_figures_contact_sheet.pdf`

---

## Existing-figure inventory verdict

No publication-ready figures existed under frozen result trees. Historical PDF/scripts are **DISCARD** for manuscript use. Full inventory: `docs/publication_figure_inventory.md`.

---

## Main figures

### Figure 1 — Study design (`figures/main/Figure_1_Study_Design.*`)

| Field | Content |
|---|---|
| Purpose | Orient readers before performance |
| Panels | A protocol; B participant-disjoint CV; C temporal windows; D ERD features; E control logic |
| Frozen data | Conceptual + protocol/window definitions |
| Design decisions | Emphasize ME→MI order coupling; no randomization implication |
| Caveats | Conceptual; window edges should be double-checked against frozen window JSON in layout polish |
| Publication-ready? | **Near** — review visual density / typography |
| Open questions | Prefer 1-page vs slightly taller multi-row layout? |

### Figure 2 — Primary decoding (`Figure_2_Primary_Decoding.*`)

| Field | Content |
|---|---|
| Purpose | Primary phenomenon + E07 inferential support |
| Panels | A participant BAcc; B comparators; C null; D secondary metrics |
| Frozen data | E01 + E07 |
| Design decisions | Explicit “not a leaderboard”; BAcc highlighted as primary |
| Caveats | Panel D could move to Table 2 if main figure feels crowded |
| Publication-ready? | **Yes** pending visual polish |
| Open questions | Keep 2D in main figure or demote to table/S2? |

### Figure 3 — Pre-cue vs post-cue (`Figure_3_PreCue_PostCue.*`)

| Field | Content |
|---|---|
| Purpose | Conceptual centerpiece: pre-cue exists; post-cue adds more |
| Panels | A timeline; B paired; C ΔBAcc |
| Frozen data | E00, E01, comparisons |
| Design decisions | Avoided 102-line spaghetti; used paired summary + Δ distribution |
| Caveats | Exact paired visualization style may need researcher preference |
| Publication-ready? | **Near** |
| Open questions | Preferred paired viz: slope chart subsample, raincloud of Δ only, or Bland–Altman-style? |

### Figure 4 — Physiology / spatial (`Figure_4_Physiology_Spatial.*`)

| Field | Content |
|---|---|
| Purpose | Sensorimotor physiology + non-exclusive spatial information |
| Panels | A map; B ROI; C topomaps; D movements; E spatial control |
| Frozen data | E03, E02, postdefinitive E05 spatial |
| Design decisions | Paired SM mean from frozen paired CSV (≠ full-cohort 0.618); no confirmatory paired p; peripheral label not “non-brain”; RdBu_r diverging map (not jet) |
| Caveats | Topomap interpolation is MNE default over frozen channel means — interpret as channel-supporting only; FDR “*” marks are conservative markers from frozen `reject_fdr` |
| Publication-ready? | **Near** — check colorbar / panel C crowding |
| Open questions | Keep topomaps in main Fig 4 or move to S5 only? |

### Figure 5 — Robustness / protocol (`Figure_5_Robustness_Protocol.*`)

| Field | Content |
|---|---|
| Purpose | Robustness + fixed-order limitation |
| Panels | A artifact; B other sens; C rejection; D order schematic; E E08 pre-cue β |
| Frozen data | Postdef E05, review sensitivity, final sensitivity, E08 |
| Design decisions | Pre-cue β chosen as clear prespecified run-state diagnostic (not max-p cherry-pick); diagnostic labels explicit |
| Caveats | 5B analysis name labels are long; may need abbreviation key |
| Publication-ready? | **Near** |
| Open questions | Prefer Δ-vs-primary bars instead of absolute BAcc in 5B? |

---

## Supplementary figures

| Figure | Purpose | Ready? | Notes |
|---|---|---|---|
| S1 | Eligibility flow | Draft | Counts only; Table 1 may supersede detail |
| S2 | Secondary metrics table-fig | Yes | Omit if Table 2 adopted |
| S3 | Comparator distributions | Yes | |
| S4 | Movement distributions | Yes | |
| S5 | Channel ERD bars | Yes | Complements 4C |
| S6 | Laterality | Yes | Secondary / heterogeneous |
| S7 | Heterogeneity | Yes | EXPLORATORY |
| S8 | Artifact distributions | Yes | Expands 5A |
| S9 | Rejection detail | Yes | Expands 5C |
| S10 | E08 expanded | Yes | Diagnostic |
| S11 | Sampling-rate | Yes | STABLE N=99 |

---

## Not generated / deferred

| Item | Why |
|---|---|
| Figure 3D | Overcrowd risk; covered by Table 2 / S2 |
| Any new scientific endpoint | Freeze rule |
| `publication-figures-v1` tag | Await approval |

---

## Design / style notes

- Okabe–Ito colorblind-safe palette; white backgrounds; chance = 0.50 marked on BAcc panels.
- Vector PDF + SVG + 300 dpi PNG + `figures/source_data/` for quantitative panels.
- Validation enforces primary BAcc, E07 null count, Ns, spatial paired values, artifact/sampling/rejection anchors.

---

## Discrepancies requiring researcher review

1. **None blocking** for mapped primary numbers (validator passed).  
2. **Figure 4E SM error bar:** only SC cohort CI is drawn from frozen bootstrap; SM bar is paired-subset mean without a separate frozen CI (paired Δ CI is annotated). Confirm this display choice.  
3. **Figure 4B FDR asterisks:** present from frozen `reject_fdr`; confirm acceptable vs caption-only FDR statement.  
4. **Figure 5E variable choice:** pre-cue β by matched pair — confirm as the preferred prespecified diagnostic face of E08 for the main figure (full set in S10).  
5. **S1 eligibility flow:** currently coarse counts; expand only if a richer frozen eligibility flowchart table exists (do not invent attrition steps).

---

## Next step

Researcher + ChatGPT visual/scientific figure review → polish → then tag `publication-figures-v1` if approved. Do **not** alter `analysis-complete-pre-manuscript`.
