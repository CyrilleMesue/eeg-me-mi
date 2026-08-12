"""Run provenance and software-version snapshots."""

from __future__ import annotations

import json
import platform
import subprocess
from pathlib import Path
from typing import Any

import mne
import numpy as np
import pandas as pd
import scipy
import sklearn
import yaml


def git_commit(project_root: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(project_root),
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()
    except Exception:  # noqa: BLE001
        return "unknown"


def software_versions() -> dict[str, str]:
    return {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "mne": mne.__version__,
        "numpy": np.__version__,
        "pandas": pd.__version__,
        "scipy": scipy.__version__,
        "scikit_learn": sklearn.__version__,
    }


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")


def write_config_snapshot(path: Path, config_raw: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(config_raw, sort_keys=False), encoding="utf-8")


def write_run_metadata(
    output_root: Path,
    *,
    config_raw: dict[str, Any],
    project_root: Path,
    seed: int,
    extra: dict[str, Any] | None = None,
) -> None:
    qc = output_root / "qc"
    qc.mkdir(parents=True, exist_ok=True)
    write_config_snapshot(qc / "config_snapshot.yaml", config_raw)
    payload = {
        "seed": seed,
        "git_commit": git_commit(project_root),
        "software_versions": software_versions(),
    }
    if extra:
        payload.update(extra)
    write_json(qc / "run_metadata.json", payload)
    write_json(qc / "software_versions.json", software_versions())
