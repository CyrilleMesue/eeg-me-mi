#!/bin/bash
#SBATCH -J eeg-me-mi-e07
#SBATCH -o slurm/logs/e07_%j.out
#SBATCH -e slurm/logs/e07_%j.err
#SBATCH -N 1
#SBATCH -c 16
#SBATCH --mem=32G
#SBATCH -t 24:00:00
#
# PREPARED in Milestone 2 — DO NOT submit until scientific go-ahead.
# Final E07 is 1,000 matched-pair permutations on the E01 primary cohort.
#
# Estimated from local 20-perm benchmark (~16.3 s/perm → ~4.5 h for 1000 on
# similar CPU). Prefer TRUBA so the workstation is not occupied for hours.
#
# Example (after approval):
#   sbatch slurm/e07_1000perm.sbatch

set -euo pipefail
module load python/3.11 || true
cd "${SLURM_SUBMIT_DIR:-$PWD}"
python -m eeg_me_mi.cli benchmark-e07 configs/full.yaml --n-permutations 1000 --no-download
