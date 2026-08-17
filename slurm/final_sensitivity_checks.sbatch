#!/bin/bash
#SBATCH -J eeg-me-mi-finalsens
#SBATCH -o slurm/logs/final_sensitivity_%j.out
#SBATCH -e slurm/logs/final_sensitivity_%j.err
#SBATCH -N 1
#SBATCH -c 56
#SBATCH --mem=32G
#SBATCH -t 12:00:00
#
# Final sampling-rate sensitivity + ME/MI rejection audit.
# Does NOT rewrite results/definitive/ or results/postdefinitive_e05/.

set -euo pipefail

PROJECT_DIR="${SLURM_SUBMIT_DIR:-}"
if [[ -z "${PROJECT_DIR}" || ! -d "${PROJECT_DIR}" ]]; then
  echo "ERROR: SLURM_SUBMIT_DIR missing" >&2
  exit 1
fi
cd "${PROJECT_DIR}"

if [[ -f ".venv/bin/activate" ]]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
else
  echo "ERROR: .venv missing" >&2
  exit 1
fi

mkdir -p slurm/logs results/final_sensitivity_checks

CONFIG="${CONFIG:-configs/full.yaml}"
echo "HOST=$(hostname)"
echo "DATE=$(date -Is)"
echo "GIT=$(git rev-parse HEAD)"
echo "TAG=$(git describe --tags --exact-match 2>/dev/null || true)"
python -c "import mne, sklearn, sys; print(sys.version); print('mne', mne.__version__); print('sklearn', sklearn.__version__)"

FROZEN_FOLDS="${FROZEN_FOLDS:-results/full/e01/erd_lr/fold_assignments.csv}"
if [[ ! -f "${FROZEN_FOLDS}" ]]; then
  FROZEN_FOLDS="results/definitive/full/e01/erd_lr/fold_assignments.csv"
fi
echo "FROZEN_FOLDS=${FROZEN_FOLDS}"

PYTHONPATH=src /usr/bin/time -v python scripts/run_final_sensitivity_checks.py \
  --config "${CONFIG}" \
  --out-root results/final_sensitivity_checks \
  --frozen-folds "${FROZEN_FOLDS}" \
  2> "slurm/logs/final_sensitivity_${SLURM_JOB_ID:-local}_time.txt"

python - <<'PY'
import json, sys
from pathlib import Path
root = Path("results/final_sensitivity_checks")
s = json.loads((root / "sampling_rate/sampling_rate_sensitivity_summary.json").read_text())
r = json.loads((root / "rejection_audit/rejection_audit_summary.json").read_text())
rec = json.loads((root / "reconciliation/reconciliation.json").read_text())
imm = json.loads((root / "primary_immutability_check.json").read_text())
print("sampling", s)
print("rejection_primary", r["primary_cohort"])
print("reconcile_ok", rec["reconcile_ok"])
print("immutable", imm)
if not rec["reconcile_ok"] or not imm.get("unchanged"):
    sys.exit(1)
print("OK")
PY
