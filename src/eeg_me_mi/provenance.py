"""Strengthened cache fingerprinting and provenance helpers."""

from __future__ import annotations

import hashlib
import json
import platform
import subprocess
from pathlib import Path
from typing import Any, Sequence

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


def git_tag(project_root: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "describe", "--tags", "--exact-match"],
            cwd=str(project_root),
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip() or None
    except Exception:  # noqa: BLE001
        return None


def git_dirty(project_root: Path) -> bool:
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(project_root),
            check=True,
            capture_output=True,
            text=True,
        )
        return bool(result.stdout.strip())
    except Exception:  # noqa: BLE001
        return True


def config_checksum(config_raw: dict[str, Any]) -> str:
    payload = json.dumps(config_raw, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


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
) -> dict[str, Any]:
    qc = output_root / "qc"
    qc.mkdir(parents=True, exist_ok=True)
    write_config_snapshot(qc / "config_snapshot.yaml", config_raw)
    dirty = git_dirty(project_root)
    payload = {
        "seed": seed,
        "git_commit": git_commit(project_root),
        "git_tag": git_tag(project_root),
        "git_dirty": dirty,
        "config_checksum": config_checksum(config_raw),
        "software_versions": software_versions(),
    }
    if extra:
        payload.update(extra)
    write_json(qc / "run_metadata.json", payload)
    write_json(qc / "software_versions.json", software_versions())
    return payload


def assert_clean_tree_for_definitive(project_root: Path, *, allow_dirty: bool = False) -> None:
    if git_dirty(project_root) and not allow_dirty:
        raise RuntimeError(
            "Definitive execution refused: git working tree is dirty. "
            "Commit/tag a clean tree, or pass allow_dirty=True for non-scientific testing only."
        )


def file_fingerprint(path: Path, *, max_bytes: int = 1024 * 1024) -> dict[str, Any]:
    """Stable file identity: size + partial SHA-256 (full hash if small)."""
    path = Path(path)
    if not path.exists():
        return {"path": str(path), "exists": False}
    size = path.stat().st_size
    h = hashlib.sha256()
    with path.open("rb") as handle:
        if size <= max_bytes:
            h.update(handle.read())
            digest = h.hexdigest()
            mode = "full"
        else:
            # Sample head + tail for large EDFs without hashing entire file.
            head = handle.read(max_bytes // 2)
            handle.seek(max(0, size - max_bytes // 2))
            tail = handle.read(max_bytes // 2)
            h.update(head)
            h.update(tail)
            h.update(str(size).encode())
            digest = h.hexdigest()
            mode = "head_tail"
    return {
        "path": str(path),
        "exists": True,
        "size_bytes": int(size),
        "sha256": digest,
        "hash_mode": mode,
    }


def build_cache_manifest(
    *,
    subject: int,
    runs: Sequence[int],
    preproc: dict[str, Any],
    channels: Sequence[str],
    mode: str,
    edf_fingerprints: list[dict[str, Any]],
    annotation_fingerprint: str | None,
    project_root: Path | None = None,
) -> dict[str, Any]:
    """Rich cache identity for scientifically incompatible reuse prevention."""
    manifest = {
        "version": 4,
        "subject": int(subject),
        "runs": list(map(int, runs)),
        "mode": mode,
        "channels": list(channels),
        "preprocessing": {
            "l_freq": preproc.get("l_freq"),
            "h_freq": preproc.get("h_freq"),
            "target_sfreq": preproc.get("target_sfreq"),
            "epoch_tmin": preproc.get("epoch_tmin"),
            "epoch_tmax": preproc.get("epoch_tmax"),
            "baseline_tmin": preproc.get("baseline_tmin"),
            "baseline_tmax": preproc.get("baseline_tmax"),
            "task_tmin": preproc.get("task_tmin"),
            "task_tmax": preproc.get("task_tmax"),
            "e00_tmin": preproc.get("e00_tmin"),
            "e00_tmax": preproc.get("e00_tmax"),
            "reject_peak_to_peak_uv": preproc.get("reject_peak_to_peak_uv"),
            "reference": "average",
            "montage": "standard_1005",
            "filter_method": "fir",
            "fir_design": "firwin",
            "phase": "zero",
        },
        "edf_fingerprints": edf_fingerprints,
        "annotation_fingerprint": annotation_fingerprint,
        "mne_version": mne.__version__,
        "software_versions": software_versions(),
    }
    if project_root is not None:
        manifest["git_commit"] = git_commit(project_root)
        manifest["git_dirty"] = git_dirty(project_root)
    digest = hashlib.sha256(
        json.dumps(manifest, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()
    manifest["manifest_sha256"] = digest
    return manifest


def validate_cache_manifest(
    stored: dict[str, Any],
    expected: dict[str, Any],
    *,
    require_keys: Sequence[str] | None = None,
) -> None:
    """Fail closed if scientifically meaningful preprocessing fields diverge."""
    keys = list(
        require_keys
        or (
            "version",
            "mode",
            "channels",
            "preprocessing",
            "mne_version",
        )
    )
    for key in keys:
        if key not in stored or key not in expected:
            raise RuntimeError(f"Cache manifest missing key: {key}")
        if stored[key] != expected[key]:
            raise RuntimeError(
                f"Cache manifest mismatch for '{key}': "
                f"stored={stored[key]!r} expected={expected[key]!r}"
            )
