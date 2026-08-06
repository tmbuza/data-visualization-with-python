"""Create the reproducible chart-choice figure for DVP Chapter 01.

The script uses a fixed random seed and synthetic data, so it requires no
external downloads. Run it from the repository root:

    python scripts/python/01-chart-choice-workbench.py
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


SEED = 20260806
OUTPUT_PATH = Path("results/figures/01-chart-choice-workbench.png")


def build_example_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Return small datasets representing comparison, trend, and relationship."""
    rng = np.random.default_rng(SEED)

    comparison = pd.DataFrame(
        {
            "channel": ["Referral", "Search", "Email", "Social"],
            "conversion_rate": [0.184, 0.151, 0.126, 0.091],
        }
    ).sort_values("conversion_rate")

    dates = pd.date_range("2026-01-01", periods=12, freq="MS")
    trend = pd.DataFrame(
        {
            "month": dates,
            "active_users": 920
            + np.arange(12) * 47
            + 90 * np.sin(np.linspace(0, 2.5 * np.pi, 12))
            + rng.normal(0, 22, 12),
        }
    )

    sample_size = 90
    response_time = rng.gamma(shape=4.2, scale=13.0, size=sample_size) + 15
    satisfaction = 96 - 0.43 * response_time + rng.normal(0, 7, sample_size)
    relationship = pd.DataFrame(
        {
            "response_time": response_time,
            "satisfaction": np.clip(satisfaction, 35, 100),
        }
    )
    return comparison, trend, relationship


def create_figure() -> None:
    """Render three questions with chart forms suited to their analytical task."""
    comparison, trend, relationship = build_example_data()
    sns.set_theme(style="whitegrid", context="notebook")

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.8), constrained_layout=True)
    accent = "#2878B5"
    highlight = "#E76F51"

    colors = [accent] * (len(comparison) - 1) + [highlight]
    axes[0].barh(
        comparison["channel"], comparison["conversion_rate"] * 100, color=colors
    )
    axes[0].set(
        title="Compare categories",
        xlabel="Conversion rate (%)",
        ylabel="",
        xlim=(0, 21),
    )
    for index, value in enumerate(comparison["conversion_rate"] * 100):
        axes[0].text(value + 0.35, index, f"{value:.1f}%", va="center", fontsize=9)

    axes[1].plot(
        trend["month"], trend["active_users"], color=accent, marker="o", linewidth=2.2
    )
    axes[1].fill_between(
        trend["month"], trend["active_users"], trend["active_users"].min() - 80,
        color=accent, alpha=0.10
    )
    axes[1].set(title="Follow change over time", xlabel="Month", ylabel="Active users")
    axes[1].tick_params(axis="x", rotation=45)

    sns.regplot(
        data=relationship,
        x="response_time",
        y="satisfaction",
        ax=axes[2],
        scatter_kws={"alpha": 0.60, "s": 32, "color": accent},
        line_kws={"color": highlight, "linewidth": 2},
        ci=None,
    )
    axes[2].set(
        title="Inspect a relationship",
        xlabel="Response time (minutes)",
        ylabel="Satisfaction score",
    )

    for ax in axes:
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="both", alpha=0.22)

    fig.suptitle(
        "Match the chart to the analytical question",
        fontsize=16,
        fontweight="bold",
    )
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT_PATH, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Saved {OUTPUT_PATH}")


if __name__ == "__main__":
    create_figure()
