# Publication figure inventory

**Analysis freeze:** `analysis-complete-pre-manuscript` (`6d0ce7a`)  
**Inventory date:** 2026-08-17  
**Scope:** repository search for PNG/PDF/SVG/EPS/TIFF/JPEG and plotting code (excluding `.venv` / `.git`).

## Summary verdict

| Category | Count | Disposition |
|---|---:|---|
| Raster/vector figures in active results trees | **0** | — |
| Historical manuscript PDF | 1 | **DISCARD** for manuscript figures (not frozen-analysis figures) |
| Historical plotting scripts | 1 (+copies) | **SUPERSEDED** — do not reuse for publication figures |

**No existing publication-ready figure set is based on the frozen `analysis-complete-pre-manuscript` outputs.** All manuscript figures must be **REGENERATED** from frozen machine-readable results under `figures/`.

---

## Existing assets

### 1. `historical/original_manuscript_draft.pdf`

| Field | Value |
|---|---|
| Path | `historical/original_manuscript_draft.pdf` |
| Type | PDF |
| Dimensions/resolution | Multi-page document (not a single panel); not measured as a figure asset |
| Analysis represented | Pre-freeze / draft manuscript content |
| Source data | Unknown / pre-dates final freeze hierarchy |
| Scientifically current | **No** |
| Based on frozen analysis | **No** |
| Publication-ready | **No** |
| Reusable | **No** (risk of silent historical numbers) |
| Superseded | **Yes** |
| Disposition | **DISCARD** for figure pipeline (keep in `historical/` only) |

### 2. `historical/publication_grade_eeg_me_vs_mi_reanalysis.py` (+ `.txt` copy)

| Field | Value |
|---|---|
| Path | `historical/publication_grade_eeg_me_vs_mi_reanalysis.py` |
| Type | Python plotting/analysis script |
| Analysis represented | Earlier reanalysis workflow |
| Source data | Not guaranteed aligned to `6d0ce7a` freeze |
| Scientifically current | **No** |
| Based on frozen analysis | **No** |
| Publication-ready | **No** |
| Reusable | Code patterns only if reviewed; **do not** import as authority |
| Superseded | **Yes** by `figures/scripts/` |
| Disposition | **DISCARD** for publication figure generation |

### 3. Active result trees (`results/definitive/`, `results/postdefinitive_*`, `results/final_sensitivity_checks/`)

| Field | Value |
|---|---|
| Figure files found | **None** (CSV/JSON/QC only) |
| Disposition | **KEEP** as scientific sources; figures are generated elsewhere |

### 4. `docs/`

No embedded publication figure images found for the freeze. Markdown reports only.

---

## Plotting code in active `src/`

No dedicated publication figure generator under `src/` for the freeze. Scientific modules produce tables/JSON only.

---

## Recommendation

Generate an entirely new figure set from frozen outputs via `figures/scripts/generate_all_figures.py`. Do not import panels from `historical/`.
