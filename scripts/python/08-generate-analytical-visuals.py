"""Generate the data, summaries, and figures used in DVP Chapter 08."""

import os
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", "/tmp/dvp-matplotlib")

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "processed"
FIGURE_DIR = ROOT / "results" / "figures"
RESULTS_DIR = ROOT / "results"
SEED = 20260806

PALETTE = {"Forest": "#036281", "Grassland": "#D97706"}
REGION_ORDER = ["North", "Central", "South"]


def create_dataset(n_sites: int = 720) -> pd.DataFrame:
    """Create a deterministic synthetic environmental field-study dataset."""
    rng = np.random.default_rng(SEED)
    region = rng.choice(REGION_ORDER, n_sites, p=[0.32, 0.38, 0.30])
    habitat = rng.choice(["Forest", "Grassland"], n_sites, p=[0.55, 0.45])

    region_elevation = pd.Series(region).map(
        {"North": 350, "Central": 820, "South": 540}
    ).to_numpy()
    elevation = np.clip(region_elevation + rng.normal(0, 210, n_sites), 40, 1550)

    region_rain = pd.Series(region).map(
        {"North": 760, "Central": 1080, "South": 1320}
    ).to_numpy()
    rainfall = np.clip(
        region_rain
        + np.where(habitat == "Forest", 150, -70)
        + rng.normal(0, 210, n_sites),
        280,
        2100,
    )
    temperature = (
        29.2
        - 0.0061 * elevation
        + pd.Series(region).map({"North": 0.8, "Central": 0.0, "South": 0.5}).to_numpy()
        + rng.normal(0, 1.25, n_sites)
    )
    survey_effort = np.clip(rng.gamma(shape=3.2, scale=1.8, size=n_sites), 1.0, 15.0)

    habitat_effect = np.where(habitat == "Forest", 7.0, -2.0)
    rainfall_effect = 0.020 * rainfall - 0.0000045 * (rainfall - 1350) ** 2
    temperature_effect = -0.65 * np.abs(temperature - 23.5)
    effort_effect = 2.1 * np.log1p(survey_effort)
    richness = np.clip(
        7 + habitat_effect + rainfall_effect + temperature_effect + effort_effect
        + rng.normal(0, 4.1, n_sites),
        3,
        None,
    ).round().astype(int)

    # A few valid but unusual high-richness sites support outlier discussion.
    unusual = rng.choice(n_sites, 5, replace=False)
    richness[unusual] += rng.integers(10, 17, size=5)

    return pd.DataFrame(
        {
            "site_id": [f"SITE-{i:04d}" for i in range(1, n_sites + 1)],
            "region": pd.Categorical(region, categories=REGION_ORDER, ordered=True),
            "habitat": habitat,
            "elevation_m": elevation.round(1),
            "rainfall_mm": rainfall.round(1),
            "temperature_c": temperature.round(1),
            "species_richness": richness,
            "survey_effort_h": survey_effort.round(1),
        }
    )


def apply_style() -> None:
    sns.set_theme(style="whitegrid", context="notebook")
    plt.rcParams.update(
        {
            "figure.dpi": 140,
            "savefig.dpi": 180,
            "axes.titleweight": "bold",
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )


def save_grouped_distributions(sites: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.violinplot(
        data=sites,
        x="region",
        y="species_richness",
        hue="habitat",
        order=REGION_ORDER,
        palette=PALETTE,
        inner="quart",
        cut=0,
        gap=0.08,
        ax=ax,
    )
    sample = sites.groupby(["region", "habitat"], observed=True, group_keys=False).sample(
        n=30, random_state=SEED
    )
    sns.stripplot(
        data=sample,
        x="region",
        y="species_richness",
        hue="habitat",
        order=REGION_ORDER,
        dodge=True,
        palette=PALETTE,
        alpha=0.45,
        size=3,
        legend=False,
        ax=ax,
    )
    ax.set(title="Richness distributions vary across region and habitat", xlabel="Region", ylabel="Species richness")
    ax.legend(title="Habitat", frameon=False)
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "08-grouped-distributions.png", bbox_inches="tight")
    plt.close(fig)


def save_bivariate_relationship(sites: pd.DataFrame) -> None:
    grid = sns.lmplot(
        data=sites,
        x="rainfall_mm",
        y="species_richness",
        hue="habitat",
        palette=PALETTE,
        height=6,
        aspect=1.45,
        scatter_kws={"alpha": 0.48, "s": 28, "edgecolor": "none"},
        line_kws={"linewidth": 2.4},
        order=2,
        ci=None,
    )
    grid.set_axis_labels("Annual rainfall (mm)", "Species richness")
    grid.fig.suptitle("Rainfall–richness relationships differ by habitat", y=1.02, fontweight="bold")
    grid.savefig(FIGURE_DIR / "08-bivariate-relationship.png", bbox_inches="tight", dpi=180)
    plt.close(grid.fig)


def save_hexbin(sites: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(9.5, 6))
    hb = ax.hexbin(
        sites["rainfall_mm"],
        sites["species_richness"],
        gridsize=25,
        mincnt=1,
        cmap="Blues",
        linewidths=0.25,
    )
    colorbar = fig.colorbar(hb, ax=ax, pad=0.02)
    colorbar.set_label("Number of sites")
    ax.set(
        title="Hexagonal bins reveal concentration hidden by overlapping points",
        xlabel="Annual rainfall (mm)",
        ylabel="Species richness",
    )
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "08-overplotting-hexbin.png", bbox_inches="tight")
    plt.close(fig)


def save_multivariate_facets(sites: pd.DataFrame) -> None:
    grid = sns.relplot(
        data=sites,
        x="rainfall_mm",
        y="species_richness",
        hue="temperature_c",
        row="habitat",
        col="region",
        col_order=REGION_ORDER,
        palette="viridis_r",
        hue_norm=(sites["temperature_c"].min(), sites["temperature_c"].max()),
        height=3.2,
        aspect=1.05,
        alpha=0.72,
        s=28,
        edgecolor="none",
    )
    grid.set_axis_labels("Rainfall (mm)", "Species richness")
    grid.set_titles(row_template="{row_name}", col_template="{col_name}")
    grid.fig.subplots_adjust(top=0.88)
    grid.fig.suptitle("Conditional views expose regional and habitat structure", fontweight="bold")
    grid.savefig(FIGURE_DIR / "08-multivariate-facets.png", bbox_inches="tight", dpi=180)
    plt.close(grid.fig)


def write_summary(sites: pd.DataFrame) -> None:
    summary = (
        sites.groupby(["region", "habitat"], observed=True)
        .agg(
            n_sites=("site_id", "size"),
            rainfall_mean_mm=("rainfall_mm", "mean"),
            rainfall_sd_mm=("rainfall_mm", "std"),
            richness_median=("species_richness", "median"),
            richness_iqr=("species_richness", lambda x: x.quantile(0.75) - x.quantile(0.25)),
            temperature_mean_c=("temperature_c", "mean"),
        )
        .round(2)
        .reset_index()
    )
    summary.to_csv(RESULTS_DIR / "08-group-summary.csv", index=False)


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    apply_style()

    sites = create_dataset()
    sites.to_csv(DATA_DIR / "08-environmental-sites.csv", index=False)
    write_summary(sites)
    save_grouped_distributions(sites)
    save_bivariate_relationship(sites)
    save_hexbin(sites)
    save_multivariate_facets(sites)

    print(f"Generated {len(sites)} synthetic sampling-site records.")
    print(f"Data: {DATA_DIR / '08-environmental-sites.csv'}")
    print(f"Summary: {RESULTS_DIR / '08-group-summary.csv'}")
    print(f"Figures: {FIGURE_DIR}")


if __name__ == "__main__":
    main()
