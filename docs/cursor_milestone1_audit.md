# Milestone 1 repository audit

Date: 2026-08-12  
Auditor: Cursor agent (Milestone 1 takeover)  
Scope: inspect existing project state before implementing E00/E01 foundation

## Repository state

| Item | Finding |
|---|---|
| Git | Present; 2 commits (docs only). Untracked scaffolding: `src/`, `tests/`, `configs/`, `pyproject.toml` |
| Python package | Partial skeleton: `protocol.py`, `config.py`, `cv.py`, `__init__.py` |
| CLI | Declared in `pyproject.toml` (`eeg-me-mi` → `eeg_me_mi.cli:main`) but **not implemented** |
| Notebooks | None in repo |
| Historical reanalysis | Outside repo at Downloads / OpenClaw inbound; now copied to `historical/` unchanged |
| Manuscript draft PDF | Outside repo; copied to `historical/` when available |
| PhysioNet cache | Only subjects 1–2, runs 3–4 under `~/.openclaw/workspace/data/physionet_eegmmidb/` (~4 EDFs) |
| Results | Empty (`results/.gitkeep`) |
| Docs | Scientific plans and prior audits present and will be preserved |

## What can be reused

1. **Protocol mapping** in `src/eeg_me_mi/protocol.py` — correct ME/MI, unilateral/bilateral, T1/T2 movements; needs matched-pair helpers and tests.
2. **Config loader** — YAML schema_version=1 with toy/pilot/full configs; extend for Milestone-1 models and eligibility thresholds.
3. **Participant-disjoint CV helpers** — `make_group_folds`, fold assignment table, overlap assertions; extend to nested CV + export.
4. **Historical reanalysis logic** (preserve, do not execute as primary):
   - EEGBCI load → standardize → montage → average ref → resample 80 Hz → 8–30 Hz → 21 channels
   - Epoch −2.0…+3.5 s; 200 µV PTP rejection
   - Welch mu/beta power; ERD dB; nested group CV; participant-mean BAcc; bootstrap
5. **Scientific docs** — claim discipline, E00 requirement, frozen preprocessing numbers.

## What is missing for Milestone 1

- Raw-data audit with per-run structural validity and anomaly documentation
- Participant-level epoch caching (16 GB–safe)
- Milestone-1 eligibility rule and `participant_eligibility.csv`
- E01 ERD features **without** `SelectKBest`
- E00 pre-cue log-band-power features (not ERD with shared baseline)
- Nested LR tuning with frozen C grid; DummyClassifier comparator
- OOF predictions, participant metrics, bootstrap, E00−E01 comparison exports
- Results tree under `results/toy/{audit,e00,e01,comparisons,qc}/`
- Comprehensive automated tests (mapping, leakage, features, eligibility, metrics, reproducibility)
- End-to-end CLI / pipeline runner
- Resource benchmark record

## Documented contradictions (resolved for Milestone 1)

| Topic | `docs/final_analysis_plan.md` | Milestone 1 specification (this task) | Decision |
|---|---|---|---|
| Eligibility | ≥2/3 repetitions for each of four task types; after rejection ≥1 trial per movement | ≥30 ME and ≥30 MI epochs; ≥2 matched pairs including ≥1 unilateral and ≥1 bilateral; movement composition in both modes; also compute ≥20/≥40 sensitivity flags | **Follow Milestone 1** for implementation; note divergence for later plan sync |
| Primary E01 model | Mentions fold-local feature selection | All 42 features; StandardScaler + L2 LR; **no SelectKBest** | **Follow Milestone 1** |
| Models in M1 | Dummy, ERD-LR, CSP-LDA, Riemann | E00 + E01 (+ Dummy comparator); no CSP/Riemann yet | **E00/E01/Dummy only** |
| Permutations | 1,000 for full analysis | Not in M1 toy | Skip E07 |

No fundamental contradiction that blocks implementation: Milestone 1 is an engineering foundation with an explicit, tighter eligibility rule and a simpler primary model.

## Anomalous participants of interest

Do **not** auto-exclude. Independently audit and document:

S038, S088, S089, S092, S100, S104

(Full-cohort audit deferred beyond toy download scope; toy run will document whatever is observed among attempted IDs.)

## Intended changes (Milestone 1)

1. Git checkpoint of current scaffolding + `historical/` provenance copies.
2. Expand `src/eeg_me_mi/` into a configuration-driven, leakage-safe package:
   - `protocol`, `config`, `audit`, `preprocess`, `eligibility`, `features`, `models`, `cv`, `metrics`, `compare`, `provenance`, `pipeline`, `cli`
3. Update `configs/toy.yaml` to ~6–8 early valid subjects, reduced bootstrap, E00/E01 only.
4. Add tests covering mapping, leakage, features, eligibility, metrics, reproducibility.
5. Run complete toy pipeline locally; write `docs/cursor_milestone1_report.md`.
6. Preserve all existing docs and historical code unchanged (except adding audit/report docs).

## Explicit non-goals

Full E02–E07, TRUBA, full 109-subject analysis, deep learning, domain adaptation, large model zoo.

## Data path plan

Use configurable `paths.data_root` (default `data/physionet_eegmmidb`). For local development, symlink or download into that tree via `mne.datasets.eegbci.load_data`. Existing OpenClaw cache may be linked to avoid re-downloading S001/S002.
