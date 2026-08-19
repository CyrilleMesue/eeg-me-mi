"""Publication Figures V2 shared style (journal aesthetic)."""

from __future__ import annotations

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt

# Semantic Okabe–Ito palette
ME = "#0072B2"  # blue — motor execution
MI = "#E69F00"  # orange — motor imagery
PRIMARY = "#009E73"  # bluish green — primary ERD-LR
CONTROL = "#56B4E9"  # sky blue — controls / E00
NULL = "#CC79A7"  # reddish purple — null / laterality
MU = "#56B4E9"  # sky — mu band (distinct from ME blue)
BETA = "#D55E00"  # vermillion — beta band (distinct from MI orange)
CHANCE = "#666666"
BLACK = "#000000"
GRAY = "#666666"
LIGHT = "#BBBBBB"
NEUTRAL = "#999999"

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
            "font.size": 8,
            "axes.titlesize": 9,
            "axes.labelsize": 8,
            "xtick.labelsize": 7,
            "ytick.labelsize": 7,
            "legend.fontsize": 7,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.linewidth": 0.7,
            "lines.linewidth": 1.0,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.fonttype": "none",
        }
    )


def panel_label(ax, letter: str, x: float = -0.12, y: float = 1.08) -> None:
    ax.text(
        x,
        y,
        letter,
        transform=ax.transAxes,
        fontsize=11,
        fontweight="bold",
        va="bottom",
        ha="right",
    )


def chance_hline(ax, y: float = 0.5) -> None:
    ax.axhline(y, color=CHANCE, ls="--", lw=0.9, zorder=0)


def chance_vline(ax, x: float = 0.5) -> None:
    ax.axvline(x, color=CHANCE, ls="--", lw=0.9, zorder=0)


def save_figure(fig: plt.Figure, stem: str, *, main: bool = True) -> None:
    out = FIG_MAIN if main else FIG_SUPP
    out.mkdir(parents=True, exist_ok=True)
    for ext, dpi in (("pdf", None), ("svg", None), ("png", 300)):
        kwargs = {"bbox_inches": "tight", "pad_inches": 0.05}
        if dpi is not None:
            kwargs["dpi"] = dpi
        fig.savefig(out / f"{stem}.{ext}", **kwargs)
    plt.close(fig)
