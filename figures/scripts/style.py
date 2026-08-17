"""Shared publication figure style (colorblind-accessible, print-safe)."""

from __future__ import annotations

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt

# Okabe–Ito palette (colorblind-safe)
BLUE = "#0072B2"
ORANGE = "#E69F00"
GREEN = "#009E73"
SKY = "#56B4E9"
VERM = "#D55E00"
PURPLE = "#CC79A7"
YELLOW = "#F0E442"
BLACK = "#000000"
GRAY = "#666666"
LIGHT = "#DDDDDD"

PRIMARY = BLUE
SECONDARY = ORANGE
CONTROL = GREEN
CHANCE = GRAY
NULL = SKY

ROOT = Path(__file__).resolve().parents[2]
FIG_MAIN = ROOT / "figures" / "main"
FIG_SUPP = ROOT / "figures" / "supplementary"
FIG_SRC = ROOT / "figures" / "source_data"
FIG_PREV = ROOT / "figures" / "previews"


def apply_style() -> None:
    mpl.rcParams.update(
        {
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "savefig.facecolor": "white",
            "font.family": "DejaVu Sans",
            "font.size": 9,
            "axes.titlesize": 10,
            "axes.labelsize": 9,
            "xtick.labelsize": 8,
            "ytick.labelsize": 8,
            "legend.fontsize": 8,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.linewidth": 0.8,
            "lines.linewidth": 1.2,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.fonttype": "none",
        }
    )


def panel_label(ax, letter: str, x: float = -0.08, y: float = 1.05) -> None:
    ax.text(
        x,
        y,
        letter,
        transform=ax.transAxes,
        fontsize=12,
        fontweight="bold",
        va="bottom",
        ha="right",
    )


def save_figure(fig: plt.Figure, stem: str, *, main: bool = True) -> None:
    out_dir = FIG_MAIN if main else FIG_SUPP
    out_dir.mkdir(parents=True, exist_ok=True)
    for ext, dpi in (("pdf", None), ("svg", None), ("png", 300)):
        kwargs = {"bbox_inches": "tight"}
        if dpi is not None:
            kwargs["dpi"] = dpi
        fig.savefig(out_dir / f"{stem}.{ext}", **kwargs)
    plt.close(fig)


def chance_line(ax, y: float = 0.5) -> None:
    ax.axhline(y, color=CHANCE, ls="--", lw=1.0, zorder=0)
