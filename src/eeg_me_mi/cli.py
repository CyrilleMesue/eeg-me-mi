"""Command-line entry point."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from eeg_me_mi.pipeline import run_from_config_path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="eeg-me-mi",
        description="Leakage-safe EEGMMIDB ME vs MI analysis (Milestone 1: E00/E01)",
    )
    parser.add_argument(
        "config",
        type=Path,
        help="Path to YAML configuration (e.g. configs/toy.yaml)",
    )
    parser.add_argument(
        "--no-download",
        action="store_true",
        help="Fail if EDFs are missing instead of downloading from PhysioNet",
    )
    parser.add_argument(
        "--force-preprocess",
        action="store_true",
        help="Ignore participant epoch caches and reprocess",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    result = run_from_config_path(
        args.config,
        download=not args.no_download,
        force_preprocess=args.force_preprocess,
    )
    summary = {
        "output_root": str(result["output_root"]),
        "eligible_subjects": result["benchmark"]["eligible_subjects"],
        "e00_balanced_accuracy": result["e00"]["summary"].get("balanced_accuracy"),
        "e01_balanced_accuracy": result["e01"]["summary"].get("balanced_accuracy"),
        "timings_sec": result["benchmark"]["timings_sec"],
        "peak_ram_mb_approx": result["benchmark"]["peak_ram_mb_approx"],
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
