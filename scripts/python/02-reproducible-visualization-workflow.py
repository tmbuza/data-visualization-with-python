#!/usr/bin/env python3
"""Build and validate the reproducible visualization workflow for DVP-002."""

from __future__ import annotations

import hashlib
import json
import platform
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
INPUT_PATH = PROJECT_ROOT / "data" / "raw" / "02-service-indicators.csv"
RESULT_DIR = PROJECT_ROOT / "results" / "02-reproducible-workflow"
FIGURE_DIR = PROJECT_ROOT / "results" / "figures"

EXPECTED_COLUMNS = {
    "month",
    "region",
    "service",
    "requests",
    "completed",
    "median_wait_minutes",
}
EXPECTED_REGIONS = {"Central", "Coastal", "Lake", "Northern"}
EXPECTED_SERVICES = {"Digital", "In-person"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(65_536), b""):
            digest.update(block)
    return digest.hexdigest()


def load_and_validate(path: Path) -> pd.DataFrame:
    data = pd.read_csv(
        path,
        parse_dates=["month"],
        dtype={"region": "string", "service": "string"},
    )

    missing_columns = EXPECTED_COLUMNS.difference(data.columns)
    if missing_columns:
        raise ValueError(f"Missing required columns: {sorted(missing_columns)}")
    if data[list(EXPECTED_COLUMNS)].isna().any().any():
        raise ValueError("Required columns contain missing values.")
    if data.duplicated(["month", "region", "service"]).any():
        raise ValueError("Duplicate region-month-service rows detected.")
    if set(data["region"]) != EXPECTED_REGIONS:
        raise ValueError("Observed regions do not match the declared domain.")
    if set(data["service"]) != EXPECTED_SERVICES:
        raise ValueError("Observed services do not match the declared domain.")
    if not (data["month"].dt.year == 2026).all():
        raise ValueError("All reporting months must be in 2026.")
    if not (data["requests"] > 0).all():
        raise ValueError("Requests must be positive.")
    if not data["completed"].between(0, data["requests"]).all():
        raise ValueError("Completed counts must be between zero and requests.")
    if not (data["median_wait_minutes"] >= 0).all():
        raise ValueError("Median wait time cannot be negative.")

    expected_rows_per_month = len(EXPECTED_REGIONS) * len(EXPECTED_SERVICES)
    rows_per_month = data.groupby("month", observed=True).size()
    if not (rows_per_month == expected_rows_per_month).all():
        raise ValueError("Every month must contain all region-service combinations.")
    return data


def build_plot_data(data: pd.DataFrame) -> pd.DataFrame:
    return (
        data.groupby(["month", "service"], as_index=False, observed=True)
        .agg(requests=("requests", "sum"), completed=("completed", "sum"))
        .assign(completion_rate=lambda x: 100 * x["completed"] / x["requests"])
        .sort_values(["service", "month"])
        .reset_index(drop=True)
    )


def build_profile(data: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "column": data.columns,
            "dtype": [str(data[column].dtype) for column in data.columns],
            "non_missing": [int(data[column].notna().sum()) for column in data.columns],
            "missing": [int(data[column].isna().sum()) for column in data.columns],
            "unique": [int(data[column].nunique(dropna=True)) for column in data.columns],
        }
    )


def draw_figure(plot_data: pd.DataFrame, output_path: Path) -> None:
    colors = {"Digital": "#0072B2", "In-person": "#D55E00"}
    fig, ax = plt.subplots(figsize=(9, 5.4), constrained_layout=True)

    for service in ["Digital", "In-person"]:
        group = plot_data.loc[plot_data["service"] == service]
        ax.plot(
            group["month"],
            group["completion_rate"],
            color=colors[service],
            marker="o",
            markersize=6,
            linewidth=2.2,
            label=service,
        )

    ax.set_title(
        "Monthly completion rates remained above 80%",
        loc="left",
        fontsize=15,
        fontweight="bold",
        pad=14,
    )
    ax.text(
        0,
        1.01,
        "Aggregated across four service regions, January–June 2026",
        transform=ax.transAxes,
        fontsize=10,
        color="#555555",
    )
    ax.set_xlabel("Month")
    ax.set_ylabel("Completed requests (%)")
    ax.set_ylim(78, 94)
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b"))
    ax.grid(axis="y", color="#D9D9D9", linewidth=0.8)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(title="Service channel", frameon=False, ncol=2, loc="lower right")
    ax.text(
        0,
        -0.18,
        "Source: deterministic DVP-002 teaching dataset",
        transform=ax.transAxes,
        fontsize=8.5,
        color="#666666",
    )
    fig.savefig(output_path, dpi=160, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def main() -> None:
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)

    data = load_and_validate(INPUT_PATH)
    plot_data = build_plot_data(data)
    profile = build_profile(data)

    plot_data_path = RESULT_DIR / "02-monthly-completion-rate.csv"
    profile_path = RESULT_DIR / "02-data-profile.csv"
    figure_path = FIGURE_DIR / "02-monthly-completion-rate.png"
    manifest_path = RESULT_DIR / "02-run-manifest.json"

    plot_data.to_csv(plot_data_path, index=False, date_format="%Y-%m-%d")
    profile.to_csv(profile_path, index=False)
    draw_figure(plot_data, figure_path)

    manifest = {
        "chapter_id": "DVP-002",
        "script": str(Path(__file__).relative_to(PROJECT_ROOT)),
        "input": str(INPUT_PATH.relative_to(PROJECT_ROOT)),
        "input_sha256": sha256(INPUT_PATH),
        "source_rows": len(data),
        "plot_rows": len(plot_data),
        "reporting_period": {
            "start": data["month"].min().date().isoformat(),
            "end": data["month"].max().date().isoformat(),
        },
        "environment": {
            "python": platform.python_version(),
            "pandas": pd.__version__,
            "matplotlib": matplotlib.__version__,
        },
        "outputs": [
            str(plot_data_path.relative_to(PROJECT_ROOT)),
            str(profile_path.relative_to(PROJECT_ROOT)),
            str(figure_path.relative_to(PROJECT_ROOT)),
        ],
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print(f"Validated {len(data)} rows at grain: region-month-service.")
    print(f"Saved plotting data: {plot_data_path.relative_to(PROJECT_ROOT)}")
    print(f"Saved data profile: {profile_path.relative_to(PROJECT_ROOT)}")
    print(f"Saved figure: {figure_path.relative_to(PROJECT_ROOT)}")
    print(f"Saved manifest: {manifest_path.relative_to(PROJECT_ROOT)}")
    print("All validation checks passed.")


if __name__ == "__main__":
    main()
