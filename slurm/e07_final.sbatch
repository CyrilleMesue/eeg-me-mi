#!/bin/bash
#SBATCH -J eeg-me-mi-e07
#SBATCH -o slurm/logs/e07_%j.out
#SBATCH -e slurm/logs/e07_%j.err
#SBATCH -N 1
#SBATCH -c 2
#SBATCH --mem=16G
#SBATCH -t 24:00:00
#
# FINAL E07 structured permutation job (not the timing benchmark).
# Default: 1000 permutations. For smoke tests, override:
#   sbatch --export=N_PERM=10 slurm/e07_final.sbatch
#
# Implementation is single-worker nested CV (n_jobs=1). Requesting many CPUs
# does not accelerate E07; 2 CPUs is intentional.

set -euo pipefail

PROJECT_DIR="${SLURM_SUBMIT_DIR:-}"
if [[ -z "${PROJECT_DIR}" || ! -d "${PROJECT_DIR}" ]]; then
  echo "ERROR: SLURM_SUBMIT_DIR missing or not a directory" >&2
  exit 1
fi
cd "${PROJECT_DIR}"

if [[ ! -f "configs/full.yaml" ]]; then
  echo "ERROR: configs/full.yaml not found in ${PROJECT_DIR}" >&2
  exit 1
fi

# Environment activation — fail closed (no silent fallback)
if [[ -f ".venv/bin/activate" ]]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
elif [[ -n "${EEG_ME_MI_VENV:-}" && -f "${EEG_ME_MI_VENV}/bin/activate" ]]; then
  # shellcheck disable=SC1091
  source "${EEG_ME_MI_VENV}/bin/activate"
else
  echo "ERROR: Python venv not found (.venv or EEG_ME_MI_VENV)" >&2
  exit 1
fi

command -v python >/dev/null || { echo "ERROR: python not on PATH after activate" >&2; exit 1; }

mkdir -p slurm/logs
mkdir -p results/full/e07/checkpoints

N_PERM="${N_PERM:-1000}"
CONFIG="${CONFIG:-configs/full.yaml}"

echo "HOST=$(hostname)"
echo "DATE=$(date -Is)"
echo "GIT=$(git rev-parse HEAD)"
echo "GIT_TAG=$(git describe --tags --exact-match 2>/dev/null || true)"
echo "DIRTY=$(git status --porcelain | wc -l)"
echo "N_PERM=${N_PERM}"
echo "CONFIG=${CONFIG}"
python -c "import mne, sklearn, sys; print('python', sys.version); print('mne', mne.__version__); print('sklearn', sklearn.__version__)"
pip freeze > "slurm/logs/e07_${SLURM_JOB_ID:-local}_pip_freeze.txt"

# Refuse dirty tree for definitive scientific runs unless ALLOW_DIRTY=1
ALLOW_DIRTY_FLAG=()
if [[ "${ALLOW_DIRTY:-0}" == "1" ]]; then
  ALLOW_DIRTY_FLAG=(--allow-dirty)
fi

/usr/bin/time -v python -m eeg_me_mi.cli run-e07 "${CONFIG}" \
  --n-permutations "${N_PERM}" \
  --no-download \
  "${ALLOW_DIRTY_FLAG[@]}" \
  2> "slurm/logs/e07_${SLURM_JOB_ID:-local}_time.txt"

# Fail closed if completion manifest incomplete
python - <<'PY'
import json, sys
from pathlib import Path
p = Path("results/full/e07/completion_manifest.json")
if not p.exists():
    print("ERROR: missing completion_manifest.json", file=sys.stderr)
    sys.exit(1)
m = json.loads(p.read_text())
if not m.get("complete"):
    print("ERROR: E07 incomplete:", m, file=sys.stderr)
    sys.exit(1)
print("E07 complete:", m.get("n_valid"), "permutations; p=", m.get("p_value_plusone"))
PY
