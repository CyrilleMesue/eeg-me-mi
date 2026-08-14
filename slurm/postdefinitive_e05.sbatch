#!/bin/bash
#SBATCH -J eeg-me-mi-e05pd
#SBATCH -o slurm/logs/postdefinitive_e05_%j.out
#SBATCH -e slurm/logs/postdefinitive_e05_%j.err
#SBATCH -N 1
#SBATCH -c 56
#SBATCH --mem=32G
#SBATCH -t 24:00:00
#
# Post-definitive E05 controls (artifact sensitivity + spatial control).
# Does NOT rewrite results/definitive/. Does NOT rerun E07.
# Orfoz QOS requires -c 56 or 112.
#
# Resume spatial-only after completed thresholds:
#   sbatch --export=SKIP_THRESHOLDS=1 slurm/postdefinitive_e05.sbatch

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

mkdir -p slurm/logs results/postdefinitive_e05

CONFIG="${CONFIG:-configs/full.yaml}"
# Post-eligibility E01 OOF length (not pre-eligibility PTP-retained 17257)
EXPECTED_EPOCHS="${EXPECTED_200UV_EPOCHS:-16913}"
FROZEN_BACC="${FROZEN_E01_BACC:-0.6179239767}"
SKIP_THRESHOLDS="${SKIP_THRESHOLDS:-0}"

echo "HOST=$(hostname)"
echo "DATE=$(date -Is)"
echo "GIT=$(git rev-parse HEAD)"
echo "GIT_TAG=$(git describe --tags --exact-match 2>/dev/null || true)"
echo "DIRTY=$(git status --porcelain | wc -l)"
echo "CONFIG=${CONFIG}"
echo "EXPECTED_200UV_EPOCHS=${EXPECTED_EPOCHS}"
echo "FROZEN_E01_BACC=${FROZEN_BACC}"
echo "SKIP_THRESHOLDS=${SKIP_THRESHOLDS}"
python -c "import mne, sklearn, sys; print('python', sys.version); print('mne', mne.__version__); print('sklearn', sklearn.__version__)"
pip freeze > "slurm/logs/postdefinitive_e05_${SLURM_JOB_ID:-local}_pip_freeze.txt"

SENSORIMOTOR_METRICS="${SENSORIMOTOR_METRICS:-results/full/e01/erd_lr/participant_metrics.csv}"
if [[ ! -f "${SENSORIMOTOR_METRICS}" ]]; then
  SENSORIMOTOR_METRICS="results/definitive/full/e01/erd_lr/participant_metrics.csv"
fi

EXTRA_ARGS=()
if [[ "${SKIP_THRESHOLDS}" == "1" ]]; then
  EXTRA_ARGS+=(--skip-threshold-decoding)
fi

PYTHONPATH=src /usr/bin/time -v python scripts/run_postdefinitive_e05_controls.py \
  --config "${CONFIG}" \
  --out-root results/postdefinitive_e05 \
  --expected-200uv-epochs "${EXPECTED_EPOCHS}" \
  --frozen-e01-bacc "${FROZEN_BACC}" \
  --sensorimotor-metrics "${SENSORIMOTOR_METRICS}" \
  "${EXTRA_ARGS[@]}" \
  2> "slurm/logs/postdefinitive_e05_${SLURM_JOB_ID:-local}_time.txt"

# Fail closed if primary reproduction check missing or failed
python - <<'PY'
import json, sys
from pathlib import Path
p = Path("results/postdefinitive_e05/artifact_sensitivity/200uv/primary_reproduction_check.json")
if not p.exists():
    print("ERROR: missing primary_reproduction_check.json", file=sys.stderr)
    sys.exit(1)
d = json.loads(p.read_text())
print("reproduction_check", d)
if not d.get("match"):
    print("ERROR: 200µV E05 did not reproduce frozen E01", file=sys.stderr)
    sys.exit(1)
spat = Path("results/postdefinitive_e05/spatial_control/summary.json")
if not spat.exists():
    print("ERROR: missing spatial_control/summary.json", file=sys.stderr)
    sys.exit(1)
print("OK: postdefinitive E05 controls complete")
PY
