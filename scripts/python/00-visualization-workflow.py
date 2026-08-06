#!/usr/bin/env python3
"""Generate the DVP preface visualization-workflow figure."""

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch


OUTPUT = Path("results/figures/00-visualization-workflow.png")


def main() -> None:
    """Create and save a compact, accessible workflow diagram."""
    stages = [
        ("1", "Question", "Define the\nvisual task"),
        ("2", "Data", "Inspect and\nprepare"),
        ("3", "Encoding", "Map values to\nvisual properties"),
        ("4", "Implementation", "Build with the\nright library"),
        ("5", "Evaluation", "Check accuracy\nand access"),
        ("6", "Communication", "Explain, export,\nand share"),
    ]

    colors = ["#123B5D", "#176B87", "#168AAD", "#2A9D8F", "#E9A23B", "#D96C4C"]
    fig, ax = plt.subplots(figsize=(15, 4.8), constrained_layout=True)
    fig.patch.set_facecolor("#F7F9FB")
    ax.set_facecolor("#F7F9FB")
    ax.set_xlim(0, 15)
    ax.set_ylim(0, 5)
    ax.axis("off")

    x_positions = [0.35, 2.8, 5.25, 7.7, 10.15, 12.6]
    width, height, y = 2.05, 1.65, 2.15

    for index, ((number, title, detail), color, x) in enumerate(
        zip(stages, colors, x_positions)
    ):
        box = FancyBboxPatch(
            (x, y),
            width,
            height,
            boxstyle="round,pad=0.08,rounding_size=0.16",
            facecolor=color,
            edgecolor="none",
        )
        ax.add_patch(box)
        ax.text(x + 0.18, y + 1.34, number, color="#FFFFFF", fontsize=10, weight="bold")
        ax.text(
            x + width / 2,
            y + 1.03,
            title,
            ha="center",
            va="center",
            color="#FFFFFF",
            fontsize=12,
            weight="bold",
        )
        ax.text(
            x + width / 2,
            y + 0.47,
            detail,
            ha="center",
            va="center",
            color="#FFFFFF",
            fontsize=9.5,
            linespacing=1.25,
        )

        if index < len(stages) - 1:
            arrow = FancyArrowPatch(
                (x + width + 0.08, y + height / 2),
                (x_positions[index + 1] - 0.08, y + height / 2),
                arrowstyle="-|>",
                mutation_scale=13,
                linewidth=1.5,
                color="#52606D",
            )
            ax.add_patch(arrow)

    feedback = FancyArrowPatch(
        (11.18, y - 0.08),
        (1.38, y - 0.08),
        connectionstyle="arc3,rad=-0.24",
        arrowstyle="-|>",
        mutation_scale=14,
        linewidth=1.6,
        linestyle="--",
        color="#52606D",
    )
    ax.add_patch(feedback)
    ax.text(
        6.3,
        0.35,
        "Evaluate, learn, and revise",
        ha="center",
        va="center",
        fontsize=10.5,
        color="#36454F",
        weight="bold",
    )
    ax.text(
        0.35,
        4.45,
        "A reproducible visualization workflow",
        fontsize=18,
        weight="bold",
        color="#123B5D",
    )
    ax.text(
        0.35,
        4.08,
        "Begin with purpose, preserve the evidence, and refine through evaluation.",
        fontsize=10.5,
        color="#52606D",
    )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT, dpi=200, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"Saved {OUTPUT}")


if __name__ == "__main__":
    main()

