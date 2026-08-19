# GitHub repository cleanup report

Date: 2026-08-19  
Branch: `main`  
Pre-cleanup HEAD: `e630455`  
Scope: documentation and repository hygiene only (no scientific reanalysis).

## ZIP files found

| Filename | Path | Size | Tracked? | Contents | Already elsewhere? | Unique scientific evidence? | Action |
|---|---|---:|---|---|---|---|---|
| `eeg_me_mi_milestone2_audit_package.zip` | repo root (deleted in WT; present in HEAD) | ~571 KiB | Yes (tracked) | Snapshot of src/configs/tests/docs + toy/pilot/audit outputs + packaging notes | Code/docs/configs/tests live in tree; pilot/audit results mostly local/gitignored | Packaging-only uniques: `DATA_DICTIONARY.md`, `OMITTED_FILES.md`, freeze text files | **Remove ZIP**; preserve packaging docs under `docs/archive/milestone2_audit_package/` |
| `eeg_me_mi_postdefinitive_controls_review_package.zip` | repo root (deleted in WT) | ~1.1 MiB | Yes | Post-definitive E05 results + scripts + review markdown | `results/postdefinitive_*` (tracked), `scripts/`, `docs/e05_*`, `docs/postdefinitive_*` | No unique science beyond tracked results/docs | **Remove ZIP** |
| `eeg_me_mi_final_sensitivity_checks_review_package.zip` | repo root (deleted in WT) | ~1.6 MiB archive listing | Yes | Final sensitivity results + scripts + report | `results/final_sensitivity_checks/` (tracked), `scripts/run_final_sensitivity_checks.py`, `docs/final_two_sensitivity_checks_report.md` | No | **Remove ZIP** |
| `eeg_me_mi_publication_figures_v2_review.zip` | repo root | ~3.4 MiB | No (gitignored) | Copy of `figures_v2/` main/supplementary review bundle | `figures_v2/` already versioned | No | **Delete local ZIP** |
| `eeg_me_mi_supplementary_figures_final_review.zip` | repo root | ~2.3 MiB | No (gitignored) | Supplementary final figures + generators | `figures_v2/supplementary_final/` + scripts | No | **Delete local ZIP** |

Related sidecars (checksums): three tracked `*.sha256` files for the GitHub-tracked ZIPs, plus ignored local sha256 files for remediation/definitive packages — all removed from the working tree with the archives.

Untracked directory (not a ZIP; not committed): `eeg_me_mi_definitive_results_review_package/` (~39 MiB) duplicates local `results/definitive/` plus packaging files. Left on disk for local review; gitignored via `eeg_me_mi_*_review_package/`. Unique prose report already present as `docs/definitive_execution_report.md` (now versioned).

## ZIP files removed

From Git (this commit):

- `eeg_me_mi_milestone2_audit_package.zip` + `.sha256`
- `eeg_me_mi_postdefinitive_controls_review_package.zip` + `.sha256`
- `eeg_me_mi_final_sensitivity_checks_review_package.zip` + `.sha256`

Deleted locally only (were never tracked):

- `eeg_me_mi_publication_figures_v2_review.zip`
- `eeg_me_mi_supplementary_figures_final_review.zip`
- orphaned `eeg_me_mi_milestone2_remediation_audit_package.sha256`
- orphaned `eeg_me_mi_definitive_results_review_package.sha256`

## Unique contents preserved

Extracted from the Milestone 2 audit ZIP into:

`docs/archive/milestone2_audit_package/`

- `DATA_DICTIONARY.md`
- `OMITTED_FILES.md`
- `PACKAGE_INFO.txt`
- `REPOSITORY_TREE.txt`
- `pip_freeze.txt`
- `software_versions_runtime.json`

Also versioned in this cleanup:

- `docs/definitive_execution_report.md` (execution provenance / frozen numbers)

## README changes

Created publication-quality root `README.md` covering scientific question, frozen headline findings, biological interpretation, protocol-order limitation, dataset access, analysis families E00–E08, install, validated local commands, full vs E07/TRUBA, figure reproduction, tests, reproducibility, compute notes, citation, license status, and public contact URL.

## .gitignore changes

- Kept exclusions for `.venv/`, caches, `data/`, raw EEG extensions, `results/*` (with `.gitkeep`), SLURM logs, audit working dirs, `*.zip`, `*.sha256`
- Added explicit ignore of `eeg_me_mi_*_review_package/` and `eeg_me_mi_*_audit_package/`
- Added `.DS_Store` / `Thumbs.db`

Did **not** ignore publication figures, configs, tests, or intentionally force-tracked scientific result trees.

## Files added

- `README.md`
- `CITATION.cff` (minimal; manuscript in preparation; no fabricated DOI/journal/license)
- `docs/github_repository_cleanup_report.md` (this file)
- `docs/definitive_execution_report.md`
- `docs/archive/milestone2_audit_package/*` (preserved packaging artifacts)

## Files deleted (cleanup commit)

- Three tracked review ZIPs + three tracked `.sha256` sidecars (listed above)

## Repository structure audit (summary)

| Category | Location |
|---|---|
| Source code | `src/eeg_me_mi/` |
| Configs | `configs/` |
| Tests | `tests/` |
| SLURM/TRUBA | `slurm/` |
| Results | `results/` (mostly local; selected post-definitive / sensitivity trees tracked) |
| Publication figures | `figures_v2/` (current), `figures/` (v1) |
| Documentation | `docs/` |
| Historical code | `historical/` (retained) |
| Temporary / audit packages | local `audit_package_*`, `eeg_me_mi_*_review_package/` (gitignored) |
| Caches / raw data | `cache/`, `data/` (gitignored) |
| Environment | `.venv/` (gitignored); deps in `pyproject.toml` |

Low-risk cleanup only: no aggressive directory reorganization.

## Repository risks found

1. **No `LICENSE` file** — stated in README; not invented.
2. **Definitive full tabular outputs** (`results/definitive/`, ~39 MiB) remain local/gitignored; headline numbers and provenance are documented. Consider a future curated, force-tracked subset if reviewers need machine-readable primary tables in-repo.
3. **Unrelated dirty working tree** (not part of this commit): modified figure v2 assets / generator, caption/review docs, `slurm/e07_final.sbatch`, and `docs/final_preexecution_validation_report.md`.
4. **Secret scan** (conservative): no credential/key material found outside `.venv` vendor noise. No secrets printed.
5. Largest tracked binaries include `historical/original_manuscript_draft.pdf` (~2 MiB) and several OOF CSV files (~1–1.5 MiB); acceptable but monitor GitHub size.

## Tests run

```text
PYTHONPATH=src .venv/bin/pytest -q
→ 73 passed in ~5.9 s
```

## Commands validated

| Command | Result |
|---|---|
| `pip install -e ".[test]"` (existing `.venv`) | Already installed; used for all checks |
| `PYTHONPATH=src .venv/bin/pytest -q` | 73 passed |
| `eeg-me-mi run-toy --no-download configs/toy.yaml` | Success (~1 m 23 s); wrote `results/toy` |
| `eeg-me-mi run-full --dry-run --skip-e07 --no-download configs/full.yaml` | Success |
| `PYTHONPATH=src python figures_v2/scripts/generate_all_figures_v2.py` | Success (~14 s) |
| `PYTHONPATH=src python figures_v2/scripts/validate_figures_v2.py` | 34/34 passed |
| `PYTHONPATH=src python figures_v2/scripts/validate_supplementary_final.py` | 37/37 passed |

**Not** launched: definitive full analysis; E07 ×1000.

## Remaining recommendations

1. Add an explicit open-source `LICENSE` when you choose one.
2. Decide whether to force-track a curated subset of `results/definitive/` summaries for GitHub reviewers.
3. Commit or discard the remaining unrelated local figure/SLURM/doc edits in a separate change.
4. Optionally delete or archive the local `eeg_me_mi_definitive_results_review_package/` directory after confirming `results/definitive/` is retained locally.
5. Keep review ZIPs out of Git; regenerate on demand from `figures_v2/` / `scripts/` if needed for external review.
