"""Generate the reproducible figures and contrast audit for DVP Chapter 14."""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import to_rgb, to_rgba


ROOT = Path(__file__).resolve().parents[2]
FIGURES = ROOT / "results" / "figures"
RESULTS = ROOT / "results"

BLUE = "#0072B2"
ORANGE = "#D55E00"
GREEN = "#009E73"
GRAY = "#707070"
LIGHT_GRAY = "#D9D9D9"
INK = "#222222"
BACKGROUND = "#FFFFFF"


def style_axis(ax: plt.Axes) -> None:
    """Apply a restrained, accessible base style."""
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(colors="#4A4A4A", labelsize=9)
    ax.title.set_color(INK)


def save(fig: plt.Figure, name: str, width: float | None = None) -> None:
    FIGURES.mkdir(parents=True, exist_ok=True)
    fig.savefig(FIGURES / f"{name}.png", dpi=180, bbox_inches="tight", facecolor="white")
    fig.savefig(FIGURES / f"{name}.svg", bbox_inches="tight", facecolor="white")
    plt.close(fig)


def visual_hierarchy() -> None:
    services = ["Service A", "Service B", "Service C", "Service D"]
    values = [76, 79, 84, 73]
    colors = [LIGHT_GRAY, LIGHT_GRAY, BLUE, LIGHT_GRAY]

    fig, ax = plt.subplots(figsize=(8, 4.6))
    bars = ax.barh(services, values, color=colors, height=0.58)
    ax.axvline(80, color=GRAY, linestyle=(0, (4, 3)), linewidth=1.2)
    ax.text(80.4, 3.35, "Target: 80%", color=GRAY, fontsize=9)
    for bar, value in zip(bars, values):
        ax.text(value + 0.6, bar.get_y() + bar.get_height() / 2, f"{value}%", va="center", color=INK)
    ax.annotate(
        "Focus service is 4 points above target",
        xy=(84, 2), xytext=(66, 2.75), color=INK,
        arrowprops={"arrowstyle": "-", "color": BLUE, "linewidth": 1.4},
    )
    ax.set_xlim(0, 100)
    ax.set_xlabel("Requests completed on time")
    ax.set_title("One emphasis color creates a clear hierarchy", loc="left", weight="bold")
    ax.grid(axis="x", color="#ECECEC", linewidth=0.8)
    ax.set_axisbelow(True)
    style_axis(ax)
    fig.tight_layout()
    save(fig, "14-visual-hierarchy")


def palette_families() -> None:
    palettes = {
        "Sequential — magnitude": plt.get_cmap("Blues")(np.linspace(0.25, 0.9, 6)),
        "Diverging — distance from a midpoint": plt.get_cmap("PuOr")(np.linspace(0.08, 0.92, 7)),
        "Qualitative — distinct categories": [BLUE, ORANGE, GREEN, "#CC79A7", "#E69F00", "#56B4E9"],
    }
    fig, axes = plt.subplots(3, 1, figsize=(9, 4.8))
    for ax, (label, colors) in zip(axes, palettes.items()):
        rgba_colors = np.array([to_rgba(color) for color in colors])
        ax.imshow([rgba_colors], aspect="auto")
        ax.set_title(label, loc="left", fontsize=11, color=INK)
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)
    fig.suptitle("Match the color family to the data structure", x=0.125, ha="left", weight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.92), h_pad=1.2)
    save(fig, "14-palette-families")


def direct_labels() -> None:
    months = np.arange(6)
    labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
    north = np.array([72, 74, 76, 78, 80, 82])
    south = np.array([70, 69, 66, 62, 71, 78])
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5), sharey=True)

    for ax in axes:
        ax.plot(months, north, color=BLUE, marker="o", linewidth=2, label="North")
        ax.plot(months, south, color=ORANGE, marker="s", linestyle="--", linewidth=2, label="South")
        ax.set_xticks(months, labels)
        ax.set_ylim(58, 86)
        ax.grid(axis="y", color="#ECECEC")
        ax.set_axisbelow(True)
        style_axis(ax)

    axes[0].legend(frameon=False, loc="upper left")
    axes[0].set_title("Legend lookup", loc="left", weight="bold")
    axes[0].set_ylabel("Completion rate (%)")
    axes[1].set_title("Direct labels + selective annotation", loc="left", weight="bold")
    axes[1].text(5.08, north[-1], "North 82%", color=BLUE, va="center", weight="bold")
    axes[1].text(5.08, south[-1], "South 78%", color=ORANGE, va="center", weight="bold")
    axes[1].annotate(
        "Recovery begins after April",
        xy=(3, 62), xytext=(1.4, 59.2), color=INK,
        arrowprops={"arrowstyle": "->", "color": ORANGE},
    )
    axes[1].set_xlim(-0.2, 6.25)
    fig.suptitle("Labels reduce search; annotations explain significance", x=0.07, ha="left", weight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.91))
    save(fig, "14-direct-labels-and-annotation")


def responsive_layouts() -> None:
    months = np.arange(6)
    labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
    north = np.array([72, 74, 76, 78, 80, 82])
    south = np.array([70, 69, 66, 62, 71, 78])
    fig = plt.figure(figsize=(11, 4.5))
    grid = fig.add_gridspec(1, 2, width_ratios=[1.65, 0.85], wspace=0.35)
    axes = [fig.add_subplot(grid[0, 0]), fig.add_subplot(grid[0, 1])]

    for index, ax in enumerate(axes):
        ax.plot(months, north, color=BLUE, marker="o", linewidth=2)
        ax.plot(months, south, color=ORANGE, marker="s", linestyle="--", linewidth=2)
        shown = months if index == 0 else months[::2]
        ax.set_xticks(shown, [labels[i] for i in shown])
        ax.set_ylim(58, 86)
        ax.grid(axis="y", color="#ECECEC")
        ax.set_axisbelow(True)
        style_axis(ax)
        ax.text(4.95, 82.2, "North", color=BLUE, ha="right", va="bottom", weight="bold", fontsize=9)
        ax.text(4.95, 77.6, "South", color=ORANGE, ha="right", va="top", weight="bold", fontsize=9)
    axes[0].set_title("Wide report layout", loc="left", weight="bold")
    axes[0].set_ylabel("Completion rate (%)")
    axes[0].annotate("South recovers", xy=(4, 71), xytext=(3.15, 64), arrowprops={"arrowstyle": "->", "color": ORANGE})
    axes[1].set_title("Compact layout", loc="left", weight="bold")
    axes[1].annotate("Recovery", xy=(4, 71), xytext=(2.2, 64), fontsize=8, arrowprops={"arrowstyle": "->", "color": ORANGE})
    fig.suptitle("Responsive design preserves the message, not every element", x=0.07, ha="left", weight="bold")
    fig.subplots_adjust(top=0.78)
    save(fig, "14-responsive-layouts")


def relative_luminance(color: str) -> float:
    channels = []
    for value in to_rgb(color):
        channels.append(value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4)
    red, green, blue = channels
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def contrast_ratio(foreground: str, background: str) -> float:
    lighter, darker = sorted([relative_luminance(foreground), relative_luminance(background)], reverse=True)
    return (lighter + 0.05) / (darker + 0.05)


def contrast_audit() -> None:
    pairs = [
        ("Body text", INK, BACKGROUND, 4.5),
        ("Secondary text", GRAY, BACKGROUND, 4.5),
        ("Blue graphical object", BLUE, BACKGROUND, 3.0),
        ("Orange graphical object", ORANGE, BACKGROUND, 3.0),
        ("Light gray grid", LIGHT_GRAY, BACKGROUND, 3.0),
    ]
    RESULTS.mkdir(parents=True, exist_ok=True)
    with (RESULTS / "14-contrast-audit.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["element", "foreground", "background", "ratio", "threshold", "passes"])
        writer.writeheader()
        for element, foreground, background, threshold in pairs:
            ratio = contrast_ratio(foreground, background)
            writer.writerow({
                "element": element,
                "foreground": foreground,
                "background": background,
                "ratio": f"{ratio:.2f}",
                "threshold": f"{threshold:.1f}",
                "passes": ratio >= threshold,
            })


def main() -> None:
    visual_hierarchy()
    palette_families()
    direct_labels()
    responsive_layouts()
    contrast_audit()
    print(f"Created Chapter 14 outputs under {RESULTS.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
