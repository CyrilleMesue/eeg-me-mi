# Files omitted from this audit ZIP

This package is intentionally incomplete relative to the full local workspace. Omissions fall into three classes: **size/privacy of raw data**, **regenerable caches**, and **non-essential local environment clutter**.

## 1. Raw PhysioNet EEGMMIDB EDFs (`data/`)

- **Omitted:** all `*.edf` under `data/physionet_eegmmidb/` (~3.2 GB; 1,308 task-run files).
- **Why:** User instruction; raw recordings are redistributable via PhysioNet and are not required to audit eligibility logic, code, or tabulated outputs. File identity is recorded in `results/full_cohort_audit/download_manifest.csv` (subject, run, status, nbytes, path).

## 2. Preprocessed / derived binary caches (`cache/`)

- **Omitted:** participant epoch FIF caches and related binary artifacts (~803 MB).
- **Why:** Regenerable from EDFs + code; large; `.gitignore` excludes `*.fif`. Audit of scientific rules does not require binary epoch blobs when QC/eligibility CSVs and code are present.

## 3. Virtual environment (`.venv/`)

- **Omitted:** local Python 3.14 virtualenv (~516 MB).
- **Why:** Environment-specific binaries. Replaced by `pyproject.toml`, `pip_freeze.txt`, and `software_versions_runtime.json`.

## 4. Git object store (`.git/`)

- **Omitted:** full Git database.
- **Why:** Not needed for read-only scientific review; commit hash and status are provided as text. Reviewers who need history can clone the repo separately.

## 5. Build / test / editor caches

- **Omitted:** `__pycache__/`, `.pytest_cache/`, `src/eeg_me_mi.egg-info/`, `*.pyc`.
- **Why:** Generated clutter; source `.py` files are included.

## 6. SLURM runtime logs (`slurm/logs/`)

- **Omitted:** empty/runtime log directory.
- **Why:** No TRUBA job was submitted; only the prepared `e07_1000perm.sbatch` script is relevant.

## 7. Historical manuscript PDF (optional)

- **Status:** `historical/original_manuscript_draft.pdf` may be absent from this ZIP even if present on disk.
- **Why:** Large binary draft; historical Colab reanalysis `.py`/`.txt` are included for code provenance. Scientific decisions are captured in the synchronized plan and Milestone reports.

## 8. Unrelated workspace archives

- **Omitted:** `docs.zip` (if present at repo root).
- **Why:** Duplicate of docs already included individually.

## Included despite being large-ish tabular results

- Full-cohort audit CSVs, pilot_m2 machine-readable outputs, E07×20 benchmark JSON, Milestone 1 toy results — all included for audit continuity.

## How to obtain omitted raw data (if needed)

Use PhysioNet EEGMMIDB 1.0.0 via the project downloader after installing dependencies, or download from https://physionet.org/content/eegmmidb/1.0.0/ — subjects 1–109, runs 3–14.
