"""Configuration loading and validation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class AnalysisConfig:
    raw: dict[str, Any]
    source: Path

    @property
    def run_name(self) -> str:
        return str(self.raw["run_name"])

    @property
    def seed(self) -> int:
        return int(self.raw["seed"])

    @property
    def subjects(self) -> tuple[int, ...]:
        value = self.raw["subjects"]
        if isinstance(value, list):
            return tuple(map(int, value))
        return tuple(range(int(value["start"]), int(value["stop"]) + 1))

    @property
    def runs(self) -> tuple[int, ...]:
        return tuple(map(int, self.raw["runs"]))

    @property
    def preprocessing(self) -> dict[str, Any]:
        return dict(self.raw["preprocessing"])

    @property
    def cv(self) -> dict[str, Any]:
        return dict(self.raw["cv"])

    @property
    def statistics(self) -> dict[str, Any]:
        return dict(self.raw["statistics"])

    @property
    def models(self) -> tuple[str, ...]:
        return tuple(self.raw["models"])

    @property
    def eligibility(self) -> dict[str, Any]:
        return dict(self.raw.get("eligibility", {}))

    @property
    def logistic_c_grid(self) -> tuple[float, ...]:
        grid = self.raw.get("logistic_c_grid", [0.01, 0.1, 1.0, 10.0])
        return tuple(float(x) for x in grid)

    def path(self, key: str, *, project_root: Path | None = None) -> Path:
        value = Path(self.raw["paths"][key]).expanduser()
        if value.is_absolute():
            return value
        root = project_root or self.source.parent.parent
        return (root / value).resolve()


def load_config(path: str | Path) -> AnalysisConfig:
    source = Path(path).expanduser().resolve()
    with source.open(encoding="utf-8") as stream:
        raw = yaml.safe_load(stream)
    if raw.get("schema_version") != 1:
        raise ValueError("Unsupported or missing config schema_version")
    required = {
        "run_name",
        "seed",
        "subjects",
        "runs",
        "paths",
        "preprocessing",
        "cv",
        "statistics",
        "models",
    }
    missing = required - raw.keys()
    if missing:
        raise ValueError(f"Missing config fields: {sorted(missing)}")
    runs = set(map(int, raw["runs"]))
    if not runs or not runs <= set(range(3, 15)):
        raise ValueError("runs must be a non-empty subset of EEGMMIDB task runs 3-14")
    if not AnalysisConfig(raw, source).subjects:
        raise ValueError("subjects must not be empty")
    return AnalysisConfig(raw=raw, source=source)
