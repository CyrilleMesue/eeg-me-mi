"""Frozen EEGMMIDB protocol definitions."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RunDefinition:
    condition: str
    task_family: str
    repetition: int


RUN_INFO: dict[int, RunDefinition] = {
    3: RunDefinition("execution", "unilateral", 1),
    4: RunDefinition("imagery", "unilateral", 1),
    5: RunDefinition("execution", "bilateral", 1),
    6: RunDefinition("imagery", "bilateral", 1),
    7: RunDefinition("execution", "unilateral", 2),
    8: RunDefinition("imagery", "unilateral", 2),
    9: RunDefinition("execution", "bilateral", 2),
    10: RunDefinition("imagery", "bilateral", 2),
    11: RunDefinition("execution", "unilateral", 3),
    12: RunDefinition("imagery", "unilateral", 3),
    13: RunDefinition("execution", "bilateral", 3),
    14: RunDefinition("imagery", "bilateral", 3),
}

ME_RUNS = tuple(run for run, info in RUN_INFO.items() if info.condition == "execution")
MI_RUNS = tuple(run for run, info in RUN_INFO.items() if info.condition == "imagery")

# Matched ME ↔ MI pairs (ME always precedes MI in EEGMMIDB).
MATCHED_RUN_PAIRS: tuple[tuple[int, int], ...] = (
    (3, 4),
    (5, 6),
    (7, 8),
    (9, 10),
    (11, 12),
    (13, 14),
)

PAIR_FAMILY: dict[tuple[int, int], str] = {
    (3, 4): "unilateral",
    (5, 6): "bilateral",
    (7, 8): "unilateral",
    (9, 10): "bilateral",
    (11, 12): "unilateral",
    (13, 14): "bilateral",
}

SENSORIMOTOR_CHANNELS: tuple[str, ...] = (
    "FC5", "FC3", "FC1", "FCz", "FC2", "FC4", "FC6",
    "C5", "C3", "C1", "Cz", "C2", "C4", "C6",
    "CP5", "CP3", "CP1", "CPz", "CP2", "CP4", "CP6",
)

EXPECTED_ANNOTATIONS = ("T0", "T1", "T2")
ANOMALY_WATCHLIST = (38, 88, 89, 92, 100, 104)


def run_definition(run: int) -> RunDefinition:
    try:
        return RUN_INFO[run]
    except KeyError as exc:
        raise ValueError(f"Run {run} is not an EEGMMIDB task run (3-14)") from exc


def movement_name(run: int, annotation: str) -> str:
    if annotation not in {"T1", "T2"}:
        raise ValueError(f"Expected T1 or T2, got {annotation!r}")
    family = run_definition(run).task_family
    return {
        ("unilateral", "T1"): "left_fist",
        ("unilateral", "T2"): "right_fist",
        ("bilateral", "T1"): "both_fists",
        ("bilateral", "T2"): "both_feet",
    }[(family, annotation)]


def condition_label(run: int) -> int:
    """Return 1 for execution and 0 for imagery."""
    return int(run_definition(run).condition == "execution")


def condition_name(run: int) -> str:
    return run_definition(run).condition


def task_family(run: int) -> str:
    return run_definition(run).task_family


def repetition(run: int) -> int:
    return run_definition(run).repetition


def matched_pair(run: int) -> tuple[int, int]:
    """Return the (ME, MI) pair containing ``run``."""
    for me, mi in MATCHED_RUN_PAIRS:
        if run in (me, mi):
            return me, mi
    raise ValueError(f"Run {run} is not part of a matched task pair")


def pair_id(run: int) -> str:
    me, mi = matched_pair(run)
    return f"{me:02d}-{mi:02d}"


def is_execution(run: int) -> bool:
    return run_definition(run).condition == "execution"
