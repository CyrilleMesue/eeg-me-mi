"""Frozen EEGMMIDB protocol definitions."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RunDefinition:
    condition: str
    task_family: str
    repetition: int


RUN_INFO = {
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

SENSORIMOTOR_CHANNELS = (
    "FC5", "FC3", "FC1", "FCz", "FC2", "FC4", "FC6",
    "C5", "C3", "C1", "Cz", "C2", "C4", "C6",
    "CP5", "CP3", "CP1", "CPz", "CP2", "CP4", "CP6",
)


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

