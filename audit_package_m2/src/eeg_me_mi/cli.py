"""Command-line entry point with Milestone-2 subcommands."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="eeg-me-mi",
        description="Leakage-safe EEGMMIDB ME vs MI analysis",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_dl = sub.add_parser("download", help="Warm EEGMMIDB EDF cache (restartable)")
    p_dl.add_argument("config", type=Path)

    p_audit = sub.add_parser("audit", help="Full-cohort audit + eligibility (no decoding)")
    p_audit.add_argument("config", type=Path)
    p_audit.add_argument("--no-download", action="store_true")
    p_audit.add_argument("--force-preprocess", action="store_true")

    p_pilot = sub.add_parser("pilot", help="Complete-path local pilot (E00–E08)")
    p_pilot.add_argument("config", type=Path)
    p_pilot.add_argument("--no-download", action="store_true")
    p_pilot.add_argument("--force-preprocess", action="store_true")

    p_run = sub.add_parser("run-toy", help="Milestone-1 E00/E01 toy/pilot pipeline")
    p_run.add_argument("config", type=Path)
    p_run.add_argument("--no-download", action="store_true")
    p_run.add_argument("--force-preprocess", action="store_true")

    p_bench = sub.add_parser("benchmark-e07", help="Benchmark N matched-pair permutations")
    p_bench.add_argument("config", type=Path)
    p_bench.add_argument("--n-permutations", type=int, default=20)
    p_bench.add_argument("--no-download", action="store_true")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "download":
        from eeg_me_mi.config import load_config
        from eeg_me_mi.download import download_cohort

        config = load_config(args.config)
        root = config.source.parent.parent
        out = root / "results" / "full_cohort_audit"
        out.mkdir(parents=True, exist_ok=True)
        manifest = download_cohort(
            config.subjects,
            config.runs,
            config.path("data_root", project_root=root),
            manifest_path=out / "download_manifest.csv",
        )
        print(json.dumps({"ok": int(manifest.status.isin(["exists", "downloaded"]).sum()), "failed": int((manifest.status == "failed").sum())}, indent=2))
        return 0

    if args.command == "audit":
        from eeg_me_mi.cohort import run_from_config

        result = run_from_config(
            args.config,
            download=not args.no_download,
            force_preprocess=args.force_preprocess,
        )
        print(json.dumps(result["summary"], indent=2, default=str))
        return 0

    if args.command == "pilot":
        from eeg_me_mi.pilot import run_pilot_from_config

        result = run_pilot_from_config(
            args.config,
            download=not args.no_download,
            force_preprocess=args.force_preprocess,
        )
        print(json.dumps({"output_root": str(result["output_root"]), "benchmark": result["benchmark"]}, indent=2, default=str))
        return 0

    if args.command == "run-toy":
        from eeg_me_mi.pipeline import run_from_config_path

        result = run_from_config_path(
            args.config,
            download=not args.no_download,
            force_preprocess=args.force_preprocess,
        )
        print(
            json.dumps(
                {
                    "output_root": str(result["output_root"]),
                    "eligible_subjects": result["benchmark"]["eligible_subjects"],
                    "e00_balanced_accuracy": result["e00"]["summary"].get("balanced_accuracy"),
                    "e01_balanced_accuracy": result["e01"]["summary"].get("balanced_accuracy"),
                },
                indent=2,
            )
        )
        return 0

    if args.command == "benchmark-e07":
        from eeg_me_mi.benchmark_e07 import run_e07_benchmark

        result = run_e07_benchmark(
            args.config,
            n_permutations=args.n_permutations,
            download=not args.no_download,
        )
        print(json.dumps(result, indent=2, default=str))
        return 0

    parser.error(f"Unknown command {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
