"""Command-line entry point with Milestone-2 remediation subcommands."""

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

    p_full = sub.add_parser("run-full", help="Definitive full-analysis runner (not pilot)")
    p_full.add_argument("config", type=Path)
    p_full.add_argument("--no-download", action="store_true")
    p_full.add_argument("--force-preprocess", action="store_true")
    p_full.add_argument("--dry-run", action="store_true")
    p_full.add_argument("--allow-dirty", action="store_true")
    p_full.add_argument("--skip-e07", action="store_true")
    p_full.add_argument("--e07-permutations", type=int, default=None)

    p_e07 = sub.add_parser("run-e07", help="Definitive E07 structured permutation engine")
    p_e07.add_argument("config", type=Path)
    p_e07.add_argument("--n-permutations", type=int, required=True)
    p_e07.add_argument("--no-download", action="store_true")
    p_e07.add_argument("--allow-dirty", action="store_true")
    p_e07.add_argument("--force-preprocess", action="store_true")

    p_s109 = sub.add_parser("qc-s109", help="S109 amplitude/unit QC only")
    p_s109.add_argument("config", type=Path)
    p_s109.add_argument("--no-download", action="store_true")

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

    if args.command == "run-full":
        from eeg_me_mi.run_full import run_full_from_config

        result = run_full_from_config(
            args.config,
            download=not args.no_download,
            force_preprocess=args.force_preprocess,
            dry_run=args.dry_run,
            allow_dirty=args.allow_dirty,
            run_e07=not args.skip_e07,
            e07_n_permutations=args.e07_permutations,
        )
        print(json.dumps(result if args.dry_run else {"output_root": str(result["output_root"]), "completion": result["completion"]}, indent=2, default=str))
        return 0

    if args.command == "run-e07":
        from eeg_me_mi.config import load_config
        from eeg_me_mi.cv import PARTICIPANT_MEAN_SCORING
        from eeg_me_mi.e07 import run_e07_inference
        from eeg_me_mi.eligibility import evaluate_eligibility, filter_eligible_epochs
        from eeg_me_mi.features import extract_e01_erd_features
        from eeg_me_mi.models import logistic_param_grid, make_erd_lr_pipeline
        from eeg_me_mi.preprocess import build_epoch_dataset
        from eeg_me_mi.provenance import assert_clean_tree_for_definitive, write_run_metadata
        from eeg_me_mi.audit import audit_subjects
        from eeg_me_mi.cv import run_nested_group_cv

        config = load_config(args.config)
        root = config.source.parent.parent
        assert_clean_tree_for_definitive(root, allow_dirty=args.allow_dirty)
        data_root = config.path("data_root", project_root=root)
        cache_root = config.path("cache_root", project_root=root)
        output_root = config.path("output_root", project_root=root) / "e07"
        output_root.mkdir(parents=True, exist_ok=True)
        write_run_metadata(output_root, config_raw=config.raw, project_root=root, seed=config.seed)

        audit = audit_subjects(config.subjects, config.runs, data_root, download=not args.no_download)
        epochs, _ = build_epoch_dataset(
            config.subjects,
            config.runs,
            data_root,
            cache_root,
            config.preprocessing,
            download=not args.no_download,
            force=args.force_preprocess,
            mode="minimal",
            threshold_uv=float(config.preprocessing["reject_peak_to_peak_uv"]),
        )
        if epochs is None:
            raise SystemExit("No epochs for E07")
        metadata = epochs.metadata.reset_index(drop=True)
        elig = evaluate_eligibility(metadata, audit, config.subjects)
        primary = filter_eligible_epochs(metadata, elig, audit)
        epochs_p = epochs[primary.index.to_numpy()]
        meta = epochs_p.metadata.reset_index(drop=True)
        X, _ = extract_e01_erd_features(epochs_p, config.preprocessing)
        y = meta["label"].to_numpy(dtype=int)
        groups = meta["subject"].to_numpy(dtype=int)

        # Observed via identical E01 pipeline
        obs = run_nested_group_cv(
            experiment="E01",
            model_name="erd_lr",
            estimator=make_erd_lr_pipeline(config.seed),
            param_grid=logistic_param_grid(config.logistic_c_grid),
            X=X,
            y=y,
            groups=groups,
            metadata=meta,
            outer_folds=int(config.cv["outer_folds"]),
            inner_folds=int(config.cv["inner_folds"]),
            seed=config.seed,
            scoring=PARTICIPANT_MEAN_SCORING,
        )
        result = run_e07_inference(
            X=X,
            y=y,
            groups=groups,
            metadata=meta,
            observed_statistic=float(obs["summary"]["balanced_accuracy"]),
            n_permutations=args.n_permutations,
            seed=config.seed,
            outer_folds=int(config.cv["outer_folds"]),
            inner_folds=int(config.cv["inner_folds"]),
            c_grid=config.logistic_c_grid,
            output_dir=output_root,
            resume=True,
        )
        print(json.dumps(result["summary"], indent=2, default=str))
        return 0

    if args.command == "qc-s109":
        from eeg_me_mi.s109_qc import run_s109_qc_from_config

        result = run_s109_qc_from_config(args.config, download=not args.no_download)
        print(json.dumps(result["summary"], indent=2, default=str))
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
