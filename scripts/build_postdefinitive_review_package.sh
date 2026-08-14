#!/usr/bin/env bash
# Build eeg_me_mi_postdefinitive_controls_review_package.zip (no caches/EDFs).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
STAGE="$ROOT/.tmp_postdef_pkg"
rm -rf "$STAGE"
PKG=eeg_me_mi_postdefinitive_controls_review_package
mkdir -p "$STAGE/$PKG"

cp docs/postdefinitive_control_completion_report.md "$STAGE/$PKG/"
cp docs/e05_postdefinitive_audit.md "$STAGE/$PKG/"
cp docs/e05_threshold_reconciliation.md "$STAGE/$PKG/"
cp docs/e03_result_extraction.md "$STAGE/$PKG/"
cp docs/e04_result_extraction.md "$STAGE/$PKG/"
cp docs/e08_result_extraction.md "$STAGE/$PKG/"

mkdir -p "$STAGE/$PKG/results_postdefinitive_e05"
cp -a results/postdefinitive_e05/. "$STAGE/$PKG/results_postdefinitive_e05/"
rm -rf "$STAGE/$PKG/results_postdefinitive_e05/job_logs"

mkdir -p "$STAGE/$PKG/results_postdefinitive_review"
cp -a results/postdefinitive_review/. "$STAGE/$PKG/results_postdefinitive_review/"

mkdir -p "$STAGE/$PKG/configs"
cp configs/full.yaml "$STAGE/$PKG/configs/"
cp configs/truba_full.yaml "$STAGE/$PKG/configs/" 2>/dev/null || true

mkdir -p "$STAGE/$PKG/spatial_definition"
cp results/definitive/full/e05/spatial_control_channels.json "$STAGE/$PKG/spatial_definition/"
cp results/postdefinitive_e05/spatial_control/spatial_control_channels.json \
  "$STAGE/$PKG/spatial_definition/spatial_control_channels_postdefinitive_copy.json"

mkdir -p "$STAGE/$PKG/tests"
cp tests/test_postdefinitive_e05.py "$STAGE/$PKG/tests/"

mkdir -p "$STAGE/$PKG/scripts"
cp scripts/run_postdefinitive_e05_controls.py "$STAGE/$PKG/scripts/"
cp scripts/extract_postdefinitive_review_tables.py "$STAGE/$PKG/scripts/" 2>/dev/null || true
cp slurm/postdefinitive_e05.sbatch "$STAGE/$PKG/scripts/"

mkdir -p "$STAGE/$PKG/provenance"
cp results/postdefinitive_e05/provenance_completion.json "$STAGE/$PKG/provenance/"
cat > "$STAGE/$PKG/provenance/frozen_primary_e01_e07_pointers.md" <<'EOF'
# Frozen primary E01/E07 pointers (immutable)

- Tag: `m2-preexec-fir-windows-candidate`
- Commit: `3b615ed1a8e455918d6e9d90bfb5c4e42ae44adc`
- Local immutable tree: `results/definitive/full/e01/erd_lr/` and `results/definitive/full/e07/`
- Primary E01: N=102, BAcc=0.6179239767, bootstrap 95% CI [0.603553, 0.632899]
- E07: 1000/1000 permutations, observed=0.6179239767, count(null>=observed)=0, plus-one p=0.000999000999
- This package does **not** modify those definitive files.
EOF

cat > "$STAGE/$PKG/README_REVIEW.md" <<'EOF'
# Post-definitive E05 controls — scientific review package

Start with `postdefinitive_control_completion_report.md`.

Primary E01/E07 were not changed. See `provenance/frozen_primary_e01_e07_pointers.md`.
EOF

rm -f "$ROOT/$PKG.zip" "$ROOT/$PKG.sha256"
(cd "$STAGE" && zip -r -q "$ROOT/$PKG.zip" "$PKG")
sha256sum "$ROOT/$PKG.zip" | tee "$ROOT/$PKG.sha256"
rm -rf "$STAGE"
echo ZIP_OK
