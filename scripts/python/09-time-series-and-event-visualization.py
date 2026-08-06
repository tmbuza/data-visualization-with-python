#!/usr/bin/env python3
"""Generate DVP 09 time-series data, figures, summaries, and manifest."""

from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "processed"
FIGURE_DIR = ROOT / "results" / "figures"
RESULTS_DIR = ROOT / "results"
SEED = 20260807
REGIONS = ("Central", "Coastal", "Northern")
COLORS = {"Central": "#2563eb", "Coastal": "#0f766e", "Northern": "#9333ea"}
WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def build_daily_data() -> pd.DataFrame:
    """Create deterministic daily service metrics with one deliberate gap."""
    rng = np.random.default_rng(SEED)
    dates = pd.date_range("2026-01-01", "2026-06-30", freq="D")
    frames: list[pd.DataFrame] = []
    offsets = {"Central": 70, "Coastal": 20, "Northern": -25}

    for region in REGIONS:
        t = np.arange(len(dates))
        weekly = 42 * np.sin(2 * np.pi * (dates.dayofweek.to_numpy() + 1) / 7)
        trend = 0.65 * t
        release_lift = np.where(dates >= pd.Timestamp("2026-04-15"), 55, 0)
        noise = rng.normal(0, 24, len(dates))
        requests = 620 + offsets[region] + trend + weekly + release_lift + noise
        lower = requests - (55 + rng.uniform(0, 10, len(dates)))
        upper = requests + (55 + rng.uniform(0, 10, len(dates)))
        frames.append(
            pd.DataFrame(
                {
                    "date": dates,
                    "region": region,
                    "requests": np.rint(requests).astype(int),
                    "expected_lower": np.rint(lower).astype(int),
                    "expected_upper": np.rint(upper).astype(int),
                }
            )
        )

    daily = pd.concat(frames, ignore_index=True)
    gap = (
        daily["region"].eq("Coastal")
        & daily["date"].between("2026-03-08", "2026-03-14")
    )
    daily.loc[gap, ["requests", "expected_lower", "expected_upper"]] = np.nan
    daily["requests_7d"] = daily.groupby("region", sort=False)["requests"].transform(
        lambda values: values.rolling(7, min_periods=4).mean()
    )
    daily["weekday"] = pd.Categorical(
        daily["date"].dt.day_name(), categories=WEEKDAYS, ordered=True
    )
    return daily


def style_axis(ax: plt.Axes) -> None:
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color="#d1d5db", linewidth=0.7, alpha=0.7)
    ax.tick_params(colors="#374151")


def plot_overview(daily: pd.DataFrame, path: Path) -> None:
    fig, axes = plt.subplots(3, 1, figsize=(11, 8.5), sharex=True, sharey=True)
    release_date = pd.Timestamp("2026-04-15")

    for ax, region in zip(axes, REGIONS):
        frame = daily.loc[daily["region"].eq(region)]
        ax.fill_between(
            frame["date"], frame["expected_lower"], frame["expected_upper"],
            color=COLORS[region], alpha=0.10, linewidth=0,
        )
        ax.plot(frame["date"], frame["requests"], color=COLORS[region], alpha=0.38, linewidth=0.9)
        ax.plot(frame["date"], frame["requests_7d"], color=COLORS[region], linewidth=2.2)
        ax.axvline(release_date, color="#be123c", linestyle="--", linewidth=1.1)
        ax.set_title(region, loc="left", fontsize=11, fontweight="bold")
        style_axis(ax)

    axes[0].annotate(
        "Platform release\n15 Apr",
        xy=(release_date, 850), xytext=(release_date + pd.Timedelta(days=8), 900),
        color="#9f1239", fontsize=9,
        arrowprops={"arrowstyle": "-", "color": "#be123c"},
    )
    axes[1].annotate(
        "No observations",
        xy=(pd.Timestamp("2026-03-11"), 700),
        xytext=(pd.Timestamp("2026-02-18"), 800),
        fontsize=9, color="#4b5563",
        arrowprops={"arrowstyle": "->", "color": "#6b7280"},
    )
    axes[-1].xaxis.set_major_locator(mdates.MonthLocator())
    axes[-1].xaxis.set_major_formatter(mdates.DateFormatter("%b"))
    axes[-1].set_xlabel("Date (2026)")
    fig.supylabel("Daily requests")
    fig.suptitle("Service demand rises through the first half of 2026", x=0.08, ha="left", fontsize=16, fontweight="bold")
    fig.text(0.08, 0.93, "Observed values, seven-day trailing mean, and expected interval", color="#4b5563", fontsize=10)
    fig.text(0.08, 0.012, "Synthetic data · Fixed seed 20260807", color="#6b7280", fontsize=8)
    fig.tight_layout(rect=(0.04, 0.04, 1, 0.91))
    fig.savefig(path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def plot_weekday(daily: pd.DataFrame, path: Path) -> None:
    grouped = (
        daily.groupby(["region", "weekday"], observed=True)["requests"]
        .agg(median="median", q1=lambda x: x.quantile(0.25), q3=lambda x: x.quantile(0.75))
        .reset_index()
    )
    x = np.arange(7)
    fig, ax = plt.subplots(figsize=(10, 5.8))
    for region in REGIONS:
        frame = grouped.loc[grouped["region"].eq(region)]
        ax.fill_between(x, frame["q1"].to_numpy(), frame["q3"].to_numpy(), color=COLORS[region], alpha=0.10)
        ax.plot(x, frame["median"].to_numpy(), marker="o", markersize=4, linewidth=2, color=COLORS[region], label=region)
    ax.set_xticks(x, [day[:3] for day in WEEKDAYS])
    ax.set_ylabel("Daily requests")
    ax.set_title(
        "Weekly demand pattern is consistent across regions",
        loc="left", fontsize=15, fontweight="bold", pad=32,
    )
    ax.text(
        0, 1.015, "Median and interquartile range by weekday",
        transform=ax.transAxes, color="#4b5563",
    )
    ax.legend(frameon=False, ncols=3, loc="upper right")
    style_axis(ax)
    fig.text(0.09, 0.01, "Synthetic data · January–June 2026", color="#6b7280", fontsize=8)
    fig.tight_layout(rect=(0, 0.04, 1, 0.98))
    fig.savefig(path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def write_outputs(daily: pd.DataFrame) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    export = daily.copy()
    export["weekday"] = export["weekday"].astype(str)
    export.to_csv(DATA_DIR / "09-daily-service-metrics.csv", index=False, date_format="%Y-%m-%d")
    expected_days = daily["date"].nunique()
    summary = (
        daily.groupby("region", sort=False)
        .agg(observed_days=("requests", "count"), mean_requests=("requests", "mean"), peak_requests=("requests", "max"))
        .reset_index()
    )
    summary["coverage_pct"] = 100 * summary["observed_days"] / expected_days
    summary[["mean_requests", "coverage_pct"]] = summary[["mean_requests", "coverage_pct"]].round(1)
    summary.to_csv(RESULTS_DIR / "09-time-series-summary.csv", index=False)

    overview = FIGURE_DIR / "09-time-series-overview.png"
    seasonality = FIGURE_DIR / "09-weekday-seasonality.png"
    plot_overview(daily, overview)
    plot_weekday(daily, seasonality)
    manifest = pd.DataFrame(
        [
            {"figure_id": "fig-time-series-overview", "path": overview.relative_to(ROOT).as_posix(), "purpose": "Trend, smoothing, expected interval, event, and missing-data gap"},
            {"figure_id": "fig-weekday-seasonality", "path": seasonality.relative_to(ROOT).as_posix(), "purpose": "Weekday median and interquartile seasonal profile"},
        ]
    )
    manifest.to_csv(RESULTS_DIR / "09-time-series-figure-manifest.csv", index=False)


if __name__ == "__main__":
    write_outputs(build_daily_data())
    print("DVP 09 outputs generated successfully.")
