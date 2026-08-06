"""Build the DVP 15 visual-critique case study and supporting outputs."""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "results"
FIGURES = RESULTS / "figures"


def build_data() -> pd.DataFrame:
    """Return the quarterly completion-rate series used in the chapter."""
    return pd.DataFrame(
        {
            "quarter": ["2024 Q1", "2024 Q2", "2024 Q3", "2024 Q4",
                        "2025 Q1", "2025 Q2", "2025 Q3", "2025 Q4"],
            "completion_rate": [0.82, 0.83, 0.84, 0.845, 0.85, 0.86, 0.87, 0.88],
            "target_rate": 0.90,
        }
    )


def write_claims() -> None:
    """Record the logical layers of the visual story."""
    claims = pd.DataFrame(
        [
            ("evidence", "Completion increased from 82% to 88% across eight quarters.",
             "Directly supported by the plotted values."),
            ("inference", "Operational changes may have contributed to the increase.",
             "Requires process and causal evidence; the trend alone is insufficient."),
            ("recommendation", "Investigate the remaining gap before changing staffing.",
             "Decision informed by the 90% target and the unresolved cause."),
        ],
        columns=["layer", "statement", "support_note"],
    )
    claims.to_csv(RESULTS / "15-story-claims.csv", index=False)


def draw_critique(data: pd.DataFrame) -> None:
    """Compare a misleading display with an ethical redesign."""
    x = range(len(data))
    values = data["completion_rate"] * 100

    fig, axes = plt.subplots(2, 1, figsize=(10, 8), constrained_layout=True)
    fig.patch.set_facecolor("#f7f4ee")

    ax = axes[0]
    ax.set_facecolor("#f7f4ee")
    ax.bar(x, values, color="#d95f59", width=0.72)
    ax.set_ylim(80, 90)
    ax.set_title("Completion rate soars!", loc="left", fontsize=15, weight="bold")
    ax.set_ylabel("Completion rate (%)")
    ax.set_xticks(x, data["quarter"])
    ax.tick_params(axis="x", rotation=25)
    ax.spines[["top", "right"]].set_visible(False)
    ax.text(0.99, 0.94, "Truncated baseline exaggerates bar lengths",
            transform=ax.transAxes, ha="right", va="top", color="#8b2d2b", fontsize=10)

    ax = axes[1]
    ax.set_facecolor("#f7f4ee")
    ax.plot(x, values, color="#176b87", marker="o", linewidth=2.5, markersize=6)
    ax.axhline(90, color="#555555", linestyle="--", linewidth=1.5)
    ax.text(6.55, 92.5, "90% target", va="center", color="#444444", fontsize=10)
    ax.set_ylim(0, 100)
    ax.set_title("Completion improved, but remains below the 90% target",
                 loc="left", fontsize=15, weight="bold")
    ax.set_ylabel("Completion rate (%)")
    ax.set_xticks(x, data["quarter"])
    ax.tick_params(axis="x", rotation=25)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color="#d9d5cc", linewidth=0.8)
    ax.annotate("82%", (0, values.iloc[0]), xytext=(0, 10),
                textcoords="offset points", ha="center", weight="bold")
    ax.annotate("88%", (7, values.iloc[-1]), xytext=(0, 10),
                textcoords="offset points", ha="center", weight="bold")

    fig.suptitle("Same data, different story", fontsize=18, weight="bold", x=0.01, ha="left")
    fig.savefig(FIGURES / "15-storytelling-critique.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    FIGURES.mkdir(parents=True, exist_ok=True)
    data = build_data()
    data.to_csv(RESULTS / "15-quarterly-completion.csv", index=False)
    write_claims()
    draw_critique(data)
    print("Created DVP 15 data, claims, and critique figure.")


if __name__ == "__main__":
    main()
