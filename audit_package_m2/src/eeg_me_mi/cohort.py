"""Full-cohort audit, preprocess, and eligibility (performance-blind)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from eeg_me_mi.audit import audit_subjects, summarize_anomalies
from eeg_me_mi.config import AnalysisConfig, load_config
from eeg_me_mi.cv import assert_participant_disjoint, fold_assignment_table
from eeg_me_mi.download import download_cohort
from eeg_me_mi.eligibility import E02_ANALYSES, evaluate_eligibility, filter_eligible_epochs
from eeg_me_mi.preprocess import build_epoch_dataset
from eeg_me_mi.provenance import write_json, write_run_metadata
from eeg_me_mi.protocol import ANOMALY_WATCHLIST


def run_full_cohort_audit(
    config: AnalysisConfig,
    *,
    project_root: Path | None = None,
    download: bool = True,
    force_preprocess: bool = False,
) -> dict[str, Any]:
    """Audit + preprocess + eligibility for the configured cohort without decoding."""
    project_root = project_root or config.source.parent.parent
    data_root = config.path("data_root", project_root=project_root)
    cache_root = config.path("cache_root", project_root=project_root)
    out = project_root / "results" / "full_cohort_audit"
    out.mkdir(parents=True, exist_ok=True)

    write_run_metadata(
        out,
        config_raw=config.raw,
        project_root=project_root,
        seed=config.seed,
        extra={"stage": "full_cohort_audit"},
    )

    if download:
        manifest = download_cohort(
            config.subjects,
            config.runs,
            data_root,
            manifest_path=out / "download_manifest.csv",
        )
    else:
        from eeg_me_mi.audit import resolve_edf_path

        rows = []
        for s in config.subjects:
            for r in config.runs:
                p = resolve_edf_path(data_root, int(s), int(r))
                rows.append(
                    {
                        "subject": int(s),
                        "run": int(r),
                        "status": "exists" if p else "missing",
                        "path": str(p) if p else "",
                        "nbytes": int(p.stat().st_size) if p else 0,
                        "sha256": "",
                        "attempts": 0,
                        "error": "" if p else "missing",
                    }
                )
        manifest = pd.DataFrame(rows)
        manifest.to_csv(out / "download_manifest.csv", index=False)

    audit = audit_subjects(config.subjects, config.runs, data_root, download=False)
    audit.to_csv(out / "raw_data_audit.csv", index=False)

    # Focused anomaly report including watchlist
    anomaly = summarize_anomalies(audit)
    watch = audit.loc[audit["subject"].isin(ANOMALY_WATCHLIST)].copy()
    anomaly_report = pd.concat([anomaly, watch], ignore_index=True).drop_duplicates()
    anomaly_report.to_csv(out / "anomaly_report.csv", index=False)

    # Primary-threshold preprocess via minimal cache + 200 µV filter
    epochs, rejection_log = build_epoch_dataset(
        config.subjects,
        config.runs,
        data_root,
        cache_root,
        config.preprocessing,
        download=False,
        force=force_preprocess,
        mode="minimal",
        threshold_uv=float(config.preprocessing["reject_peak_to_peak_uv"]),
    )
    rejection_log.to_csv(out / "rejection_qc.csv", index=False)
    if epochs is None or len(epochs) == 0:
        raise RuntimeError("No epochs available after preprocessing")

    metadata = epochs.metadata.copy().reset_index(drop=True)
    elig = evaluate_eligibility(
        metadata,
        audit,
        config.subjects,
        min_epochs_per_mode=int(config.eligibility.get("min_epochs_per_mode", 30)),
        e02_min_epochs=int(config.eligibility.get("e02_min_epochs_per_mode", 15)),
        e02_min_pairs=int(config.eligibility.get("e02_min_matched_pairs", 2)),
    )
    elig.to_csv(out / "participant_eligibility.csv", index=False)

    # Freeze primary outer folds for E01-eligible subjects only
    primary_meta = filter_eligible_epochs(metadata, elig, audit, eligible_col="eligible_primary")
    primary_subjects = sorted(map(int, primary_meta["subject"].unique()))
    n_outer = int(config.cv["outer_folds"])
    if len(primary_subjects) >= n_outer:
        # One row per subject for fold assignment identity
        groups = primary_meta["subject"].to_numpy(dtype=int)
        assignments = fold_assignment_table(groups, n_outer, config.seed)
        assert_participant_disjoint(assignments)
        assignments.to_csv(out / "fold_assignments_e01_primary.csv", index=False)
    else:
        assignments = pd.DataFrame()
        (out / "fold_assignments_e01_primary.csv").write_text(
            "fold,role,subject\n", encoding="utf-8"
        )

    # E02 cohort sizes
    e02_rows = []
    for analysis in E02_ANALYSES:
        col = f"e02_{analysis}_eligible"
        n = int(elig[col].sum()) if col in elig else 0
        e02_rows.append({"analysis": analysis, "n_eligible": n})
    pd.DataFrame(e02_rows).to_csv(out / "e02_cohort_sizes.csv", index=False)

    summary = {
        "n_subjects_requested": len(config.subjects),
        "n_runs_requested": len(config.runs),
        "n_download_ok": int(manifest["status"].isin(["exists", "downloaded"]).sum()),
        "n_download_failed": int((manifest["status"] == "failed").sum()),
        "n_structurally_valid_runs": int(audit["structurally_valid"].sum()),
        "n_e01_eligible": int(elig["eligible_primary"].sum()),
        "n_strict_eligible": int(elig["eligible_strict"].sum()),
        "n_min20": int(elig["eligible_min20"].sum()),
        "n_min40": int(elig["eligible_min40"].sum()),
        "e01_subjects": primary_subjects,
        "e02_cohort_sizes": e02_rows,
        "watchlist_subjects": list(ANOMALY_WATCHLIST),
    }
    write_json(out / "cohort_summary.json", summary)

    # Human-readable QC report
    _write_qc_markdown(project_root / "docs" / "full_cohort_qc_report.md", summary, elig, anomaly_report)
    return {
        "output_dir": out,
        "audit": audit,
        "eligibility": elig,
        "metadata": metadata,
        "epochs": epochs,
        "fold_assignments": assignments,
        "summary": summary,
    }


def _write_qc_markdown(path: Path, summary: dict, elig: pd.DataFrame, anomaly: pd.DataFrame) -> None:
    lines = [
        "# Full cohort QC report",
        "",
        "Generated during Milestone 2. Eligibility is **performance-blind**.",
        "",
        "## Summary",
        "",
        f"- Subjects requested: {summary['n_subjects_requested']}",
        f"- Structurally valid subject/run rows: {summary['n_structurally_valid_runs']}",
        f"- E01 primary eligible: **{summary['n_e01_eligible']}**",
        f"- Strict sensitivity eligible: **{summary['n_strict_eligible']}**",
        f"- ≥20/mode flag: {summary['n_min20']}",
        f"- ≥40/mode flag: {summary['n_min40']}",
        "",
        "## E02 cohort sizes",
        "",
    ]
    for row in summary["e02_cohort_sizes"]:
        lines.append(f"- {row['analysis']}: {row['n_eligible']}")
    lines += ["", "## Anomaly / watchlist notes", ""]
    if anomaly.empty:
        lines.append("No anomaly/watchlist rows flagged in this audit table.")
    else:
        lines.append(f"Rows in anomaly report: {len(anomaly)}")
        lines.append("")
        cols = [c for c in ("subject", "run", "structurally_valid", "invalidity_reason", "sfreq", "n_channels") if c in anomaly.columns]
        lines.append(anomaly[cols].head(50).to_csv(index=False))
    lines += [
        "",
        "## Exclusion reason frequencies (E01 primary)",
        "",
    ]
    if "reason_codes" in elig:
        freq = elig.loc[~elig["eligible_primary"], "reason_codes"].value_counts().head(20)
        lines.append(freq.to_csv())
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run_from_config(path: str | Path, **kwargs) -> dict[str, Any]:
    return run_full_cohort_audit(load_config(path), **kwargs)
