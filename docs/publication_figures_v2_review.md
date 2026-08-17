# Publication figures V2 review (V1 → V2)

**Freeze (immutable):** `analysis-complete-pre-manuscript` @ `6d0ce7a`  
**Generator:** `PYTHONPATH=src python figures_v2/scripts/generate_all_figures_v2.py`  
**Validate:** `PYTHONPATH=src python figures_v2/scripts/validate_figures_v2.py`  
**Contact sheet:** `figures_v2/previews/publication_figures_v2_contact_sheet.pdf`  
**Do not tag** until researcher/ChatGPT visual approval.

---

## Global V1 → V2 changes

| Issue in V1 | V2 change |
|---|---|
| 5 main figures; overloaded | **4 main figures** with clearer evidence chain |
| Paragraphs / “report” text inside panels | Minimal annotations; detail moved to captions |
| Many bar charts | Prefer violins, forests, permutation hist, topomaps, paired Δ |
| Secondary metrics in main Fig 2D | Moved to S2 / Table 2 recommendation |
| Movement / rejection / heterogeneity in main | Moved to Supplement |
| V1 Fig 4 + 5 disconnected | Synthesized into single Fig 4 |
| Inconsistent density | Shared style module; ~double-column widths |

---

## Figure 1 — Design and safeguards

**What was wrong in V1:** Five-panel presentation-slide schematic; control-list panel; excess confounding prose in-figure.  
**What changed:** Three panels only — fixed ME→MI order, temporal windows, participant-disjoint pipeline.  
**Why clearer:** Readers see design/safeguards before performance without Methods-dump graphics.  
**Sources:** Protocol structure; frozen window definitions; conceptual CV matching E01.  
**Unresolved:** Panel C remains schematic (unavoidable); further typography polish possible.

---

## Figure 2 — Cross-participant decoding

**What was wrong in V1:** Four panels including multi-metric bar chart; large annotation boxes; “not a leaderboard” in-panel.  
**What changed:** Three panels — participant distribution, comparator dots+CI, E07 null. Secondary metrics removed from main.  
**Why clearer:** Primary endpoint + inferential null remain; avoids metric-bar misreading.  
**Sources:** E01 ERD-LR / comparators; E07 null + summary.  
**Unresolved:** Compact in-panel N/mean/p text still present (caption also carries CI); optional further reduction.

---

## Figure 3 — Pre-cue vs post-cue

**What was wrong in V1:** Conceptually strong but still somewhat heavy; risk of spaghetti.  
**What changed:** Cleaned three-panel layout; violin distributions + Δ; no 102-line spaghetti; optional Δ>0 count from frozen paired table.  
**Why clearer:** Direct visual of E00 presence + E01 increment.  
**Sources:** E00/E01 bootstrap; `comparisons/e00_vs_e01_*`.  
**Unresolved:** Panel A still schematic (by design).

---

## Figure 4 — Physiology + spatial + robustness + protocol state

**What was wrong in V1:** Fig 4 (5 panels) + Fig 5 (5 panels) fragmented; bars for spatial control; crowded.  
**What changed:** 2×2 synthesis — ROI forest, topomaps, paired spatial distributions + Δ inset, robustness forest + E08 pre-cue β (µV²).  
**Why clearer:** Interpretation evidence chain in one figure; paired spatial story; robustness near-identity visible as forest.  
**Sources:** E03 ROI/channel; E05 spatial; artifact + sensitivity + sampling-rate; E08 matched pairs.  
**Unresolved:**
1. Panel D is dense (two subcomponents); may need journal-specific splitting if column width requires.
2. Topomap color scale includes unused positive range (symmetric diverging scale by design).
3. Band colors (μ/β) vs condition colors (ME/MI) are now distinct Okabe–Ito hues, but still require caption legend clarity.
4. Spatial inset may crowd small print sizes — verify at 175 mm width.

---

## Supplementary reorganization

| V2 | Content | Former |
|---|---|---|
| S1 | Cohort eligibility | S1 |
| S2 | Secondary metrics (prefer Table 2) | Fig 2D / S2 |
| S3 | Movement-specific decoding | Main 4D / S4 |
| S4 | Channel-level ERD | S5 / Main 4C |
| S5 | Laterality | S6 |
| S6 | Heterogeneity (exploratory) | S7 |
| S7 | Artifact details | S8 / Main 5A |
| S8 | Rejection audit (paired) | S9 / Main 5C |
| S9 | Full E08 diagnostics | S10 / Main 5E |
| S10 | Sampling/duration | S11 / Main 5B |
| S11 | Comparator distributions | S3 |

---

## Validation

Last run: **ALL VALIDATION CHECKS PASSED** (`figures_v2/previews/validation_report_v2.txt`).

---

## Next step

ChatGPT + researcher visual review of `eeg_me_mi_publication_figures_v2_review.zip`. Do not tag `publication-figures-v2` yet.
