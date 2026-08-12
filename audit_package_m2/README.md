# Milestone 2 Independent Audit Package

**Purpose:** Self-contained, read-only scientific and technical audit of Milestone 2.  
**Generated for:** External reviewer (no write access to project environment required).  
**Scope:** Specs, code, configs, tests, SLURM stub, full-cohort audit outputs, local pilot outputs, E07×20 benchmark, provenance metadata.

## Important constraints honored by the packager

- Cached PhysioNet **EDF** files are **not** included.
- Preprocessed epoch **FIF**/numpy caches are **not** included.
- No new analysis was run to build this package.
- No code was modified for packaging.
- E07 1,000-permutation job was **not** submitted.
- No manuscript drafting was begun.

## How to navigate

| Path | Contents |
|---|---|
| `docs/final_analysis_plan.md` | Synchronized frozen scientific plan (Milestone 2) |
| `docs/final_analysis_plan.md.bak-2026-08-12-pre-m2` | Pre-sync backup |
| `docs/cursor_milestone1_report.md` | Milestone 1 completion report |
| `docs/cursor_milestone1_audit.md` | Milestone 1 pre-implementation audit |
| `docs/cursor_milestone2_report.md` | Milestone 2 completion report |
| `docs/full_cohort_qc_report.md` | Human-readable full-cohort QC |
| `configs/` | `toy`, `pilot`, `pilot_m2`, `full`, `truba_full` |
| `src/eeg_me_mi/` | Package implementing E00–E08 foundation |
| `tests/` | Automated tests (45 passed at M2 stop) |
| `slurm/e07_1000perm.sbatch` | Prepared TRUBA stub (**not submitted**) |
| `results/full_cohort_audit/` | 109-subject audit, eligibility, folds, manifest |
| `results/pilot_m2/` | Complete-path local pilot outputs |
| `results/benchmarks/` | E07 20-permutation full-cohort benchmark |
| `results/toy/` | Milestone 1 toy outputs (continuity) |
| `DATA_DICTIONARY.md` | Column definitions for machine-readable outputs |
| `OMITTED_FILES.md` | What was left out of the ZIP and why |
| `REPOSITORY_TREE.txt` | Project tree snapshot (heavy dirs pruned) |
| `GIT_COMMIT.txt` / `GIT_STATUS.txt` | Commit hash and dirty-tree status |
| `pyproject.toml` / `pip_freeze.txt` / `software_versions_runtime.json` | Dependencies |

## Git provenance note

Committed HEAD at packaging time was **Milestone 1** (`4d68320…`). Milestone 2 sources, docs, and results exist in the working tree and are included here even when still uncommitted (`GIT_STATUS.txt`).

## Reviewer checklist (suggested)

1. Confirm plan sync vs Milestone 1 decisions (eligibility, no SelectKBest, E00 terminology).
2. Inspect `participant_eligibility.csv` — performance-blind cohort construction.
3. Inspect watchlist rows in `anomaly_report.csv` / audit (S038, S088, S089, S092, S100, S104).
4. Trace E00–E08 code paths under `src/eeg_me_mi/` against tests.
5. Read E07×20 benchmark JSON and TRUBA recommendation; confirm final 1,000 not run.
6. Treat `results/pilot_m2/` metrics as engineering smoke only.

## Reproduce commands (reference only; not required for audit)

```bash
PYTHONPATH=src pytest -q
PYTHONPATH=src python -m eeg_me_mi.cli download configs/full.yaml
PYTHONPATH=src python -m eeg_me_mi.cli audit configs/full.yaml --no-download
PYTHONPATH=src python -m eeg_me_mi.cli pilot configs/pilot_m2.yaml --no-download
PYTHONPATH=src python -m eeg_me_mi.cli benchmark-e07 configs/full.yaml --n-permutations 20 --no-download
```
