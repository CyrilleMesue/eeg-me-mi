"""Restartable EEGMMIDB download / cache warmup with manifest."""

from __future__ import annotations

import hashlib
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Iterable

import pandas as pd

from eeg_me_mi.audit import resolve_edf_path

PHYSIONET_BASE = "https://physionet.org/files/eegmmidb/1.0.0"


def _file_sha256(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            block = handle.read(chunk)
            if not block:
                break
            h.update(block)
    return h.hexdigest()


def _target_path(data_root: Path, subject: int, run: int) -> Path:
    return (
        Path(data_root)
        / "MNE-eegbci-data"
        / "files"
        / "eegmmidb"
        / "1.0.0"
        / f"S{subject:03d}"
        / f"S{subject:03d}R{run:02d}.edf"
    )


def download_subject_run(
    data_root: Path,
    subject: int,
    run: int,
    *,
    max_retries: int = 3,
    retry_sleep_sec: float = 1.0,
    compute_hash: bool = False,
) -> dict:
    """Download one EDF if missing; skip valid existing files."""
    data_root = Path(data_root)
    existing = resolve_edf_path(data_root, subject, run)
    row = {
        "subject": subject,
        "run": run,
        "status": "",
        "path": "",
        "nbytes": 0,
        "sha256": "",
        "attempts": 0,
        "error": "",
    }
    if existing is not None and existing.exists() and existing.stat().st_size > 1000:
        row["status"] = "exists"
        row["path"] = str(existing)
        row["nbytes"] = int(existing.stat().st_size)
        if compute_hash:
            row["sha256"] = _file_sha256(existing)
        return row

    dest = _target_path(data_root, subject, run)
    dest.parent.mkdir(parents=True, exist_ok=True)
    url = f"{PHYSIONET_BASE}/S{subject:03d}/S{subject:03d}R{run:02d}.edf"
    last_err = ""
    for attempt in range(1, max_retries + 1):
        row["attempts"] = attempt
        tmp = dest.with_suffix(f".part{attempt}")
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "eeg-me-mi-download/0.1"})
            with urllib.request.urlopen(req, timeout=120) as resp, tmp.open("wb") as out:
                while True:
                    chunk = resp.read(1 << 20)
                    if not chunk:
                        break
                    out.write(chunk)
            if tmp.stat().st_size <= 1000:
                raise RuntimeError(f"Downloaded file too small: {tmp.stat().st_size}")
            tmp.replace(dest)
            row["status"] = "downloaded"
            row["path"] = str(dest)
            row["nbytes"] = int(dest.stat().st_size)
            if compute_hash:
                row["sha256"] = _file_sha256(dest)
            row["error"] = ""
            return row
        except Exception as exc:  # noqa: BLE001
            last_err = f"{type(exc).__name__}:{exc}"
            if tmp.exists():
                tmp.unlink(missing_ok=True)
            time.sleep(retry_sleep_sec * attempt)
    row["status"] = "failed"
    row["error"] = last_err
    return row


def download_cohort(
    subjects: Iterable[int],
    runs: Iterable[int],
    data_root: Path,
    *,
    manifest_path: Path | None = None,
    max_retries: int = 3,
    max_workers: int = 16,
    compute_hash: bool = False,
) -> pd.DataFrame:
    """Download all subject/run pairs in parallel; safely restartable."""
    data_root = Path(data_root)
    data_root.mkdir(parents=True, exist_ok=True)
    jobs = [(int(s), int(r)) for s in subjects for r in runs]
    rows: list[dict] = []
    done = 0
    total = len(jobs)

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = {
            pool.submit(
                download_subject_run,
                data_root,
                s,
                r,
                max_retries=max_retries,
                compute_hash=compute_hash,
            ): (s, r)
            for s, r in jobs
        }
        for fut in as_completed(futures):
            row = fut.result()
            rows.append(row)
            done += 1
            if done % 25 == 0 or row["status"] == "failed":
                print(
                    f"[download] {done}/{total} "
                    f"S{row['subject']:03d}R{row['run']:02d} -> {row['status']}",
                    flush=True,
                )

    manifest = pd.DataFrame(rows).sort_values(["subject", "run"]).reset_index(drop=True)
    if manifest_path is not None:
        manifest_path = Path(manifest_path)
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest.to_csv(manifest_path, index=False)
    n_fail = int((manifest["status"] == "failed").sum())
    n_ok = int(manifest["status"].isin(["exists", "downloaded"]).sum())
    print(f"[download] complete: ok={n_ok} failed={n_fail} total={len(manifest)}", flush=True)
    return manifest
