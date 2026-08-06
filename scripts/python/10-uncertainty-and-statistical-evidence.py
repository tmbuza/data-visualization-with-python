#!/usr/bin/env python3
"""Generate the data summaries and figures for DVP Chapter 10."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats


SEED = 20260807
ROOT = Path(__file__).resolve().parents[2]
FIGURE_DIR = ROOT / "results" / "figures"
RESULT_DIR = ROOT / "results" / "10-uncertainty-and-statistical-evidence"
COLORS = {"ink": "#203040", "blue": "#2878B5", "gold": "#E6A23C", "band": "#91C4E8"}


def style_axes(ax: plt.Axes) -> None:
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color="#D9E1E8", linewidth=0.8, alpha=0.75)
    ax.set_axisbelow(True)


def make_data(rng: np.random.Generator) -> pd.DataFrame:
    specifications = [
        ("Central", 34, 19.0, 4.8),
        ("Coastal", 90, 16.8, 5.6),
        ("Highlands", 52, 21.3, 6.4),
        ("Lake", 130, 18.1, 5.1),
    ]
    frames = []
    for region, n, mean, sd in specifications:
        values = np.clip(rng.normal(mean, sd, n), 3, None)
        frames.append(pd.DataFrame({"region": region, "completion_days": values}))
    return pd.concat(frames, ignore_index=True)


def summarize_groups(data: pd.DataFrame) -> pd.DataFrame:
    summary = data.groupby("region")["completion_days"].agg(n="size", mean="mean", sd="std").reset_index()
    summary["se"] = summary["sd"] / np.sqrt(summary["n"])
    critical = stats.t.ppf(0.975, summary["n"] - 1)
    summary["ci_low"] = summary["mean"] - critical * summary["se"]
    summary["ci_high"] = summary["mean"] + critical * summary["se"]
    return summary.sort_values("mean")


def plot_group_intervals(summary: pd.DataFrame) -> Path:
    fig, ax = plt.subplots(figsize=(8.4, 4.8))
    y = np.arange(len(summary))
    errors = np.vstack((summary["mean"] - summary["ci_low"], summary["ci_high"] - summary["mean"]))
    ax.errorbar(summary["mean"], y, xerr=errors, fmt="o", color=COLORS["blue"],
                ecolor=COLORS["ink"], elinewidth=2, capsize=4, markersize=7)
    ax.set_yticks(y, [f"{r}  (n={n})" for r, n in zip(summary["region"], summary["n"])])
    ax.set_xlabel("Mean completion time (days)")
    ax.set_title("Estimates need context about precision", loc="left", weight="bold", pad=28)
    ax.text(0, 1.01, "Points are sample means; lines are 95% t confidence intervals",
            transform=ax.transAxes, color="#52616B")
    style_axes(ax)
    ax.grid(axis="x", color="#D9E1E8", linewidth=0.8, alpha=0.75)
    ax.grid(axis="y", visible=False)
    fig.tight_layout()
    path = FIGURE_DIR / "10-group-confidence-intervals.png"
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return path


def plot_bootstrap(data: pd.DataFrame, rng: np.random.Generator) -> tuple[Path, dict[str, float]]:
    values = data.loc[data["region"] == "Central", "completion_days"].to_numpy()
    bootstrap = rng.choice(values, size=(5000, len(values)), replace=True).mean(axis=1)
    low, high = np.percentile(bootstrap, [2.5, 97.5])
    observed = float(values.mean())
    fig, ax = plt.subplots(figsize=(8.4, 4.8))
    ax.hist(bootstrap, bins=38, color=COLORS["band"], edgecolor="white")
    ax.axvspan(low, high, color=COLORS["blue"], alpha=0.14, label="95% percentile interval")
    ax.axvline(observed, color=COLORS["ink"], linewidth=2, label="Observed mean")
    ax.axvline(low, color=COLORS["blue"], linestyle="--")
    ax.axvline(high, color=COLORS["blue"], linestyle="--")
    ax.set_xlabel("Bootstrap mean completion time (days)")
    ax.set_ylabel("Resamples")
    ax.set_title("Bootstrap estimates show the shape of uncertainty", loc="left", weight="bold")
    ax.legend(frameon=False)
    style_axes(ax)
    fig.tight_layout()
    path = FIGURE_DIR / "10-bootstrap-distribution.png"
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    pd.DataFrame({"bootstrap_mean": bootstrap}).to_csv(RESULT_DIR / "10-bootstrap-means.csv", index=False)
    return path, {"observed_mean": observed, "ci_low": float(low), "ci_high": float(high)}


def plot_model_band(rng: np.random.Generator) -> tuple[Path, dict[str, float]]:
    n = 120
    workload = rng.uniform(10, 90, n)
    outcome = 9.5 + 0.17 * workload + rng.normal(0, 3.2, n)
    slope, intercept = np.polyfit(workload, outcome, 1)
    fitted = intercept + slope * workload
    residual_sd = np.sqrt(np.sum((outcome - fitted) ** 2) / (n - 2))
    grid = np.linspace(workload.min(), workload.max(), 200)
    predicted = intercept + slope * grid
    ssx = np.sum((workload - workload.mean()) ** 2)
    mean_se = residual_sd * np.sqrt(1 / n + (grid - workload.mean()) ** 2 / ssx)
    critical = stats.t.ppf(0.975, n - 2)
    low, high = predicted - critical * mean_se, predicted + critical * mean_se

    fig, ax = plt.subplots(figsize=(8.4, 4.8))
    ax.scatter(workload, outcome, s=25, alpha=0.45, color=COLORS["ink"], edgecolors="none")
    ax.fill_between(grid, low, high, color=COLORS["band"], alpha=0.6, label="95% CI for mean response")
    ax.plot(grid, predicted, color=COLORS["blue"], linewidth=2.5, label="Fitted relationship")
    ax.set_xlabel("Weekly workload index")
    ax.set_ylabel("Expected completion time (days)")
    ax.set_title("Model uncertainty changes across the observed range", loc="left", weight="bold")
    ax.legend(frameon=False)
    style_axes(ax)
    fig.tight_layout()
    path = FIGURE_DIR / "10-model-confidence-band.png"
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)
    pd.DataFrame({"workload": workload, "completion_days": outcome}).to_csv(
        RESULT_DIR / "10-model-data.csv", index=False
    )
    return path, {"intercept": float(intercept), "slope": float(slope), "residual_sd": float(residual_sd)}


def main() -> None:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_DIR.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)
    data = make_data(rng)
    summary = summarize_groups(data)
    summary.to_csv(RESULT_DIR / "10-group-summary.csv", index=False)
    data.to_csv(RESULT_DIR / "10-synthetic-service-data.csv", index=False)

    group_figure = plot_group_intervals(summary)
    bootstrap_figure, bootstrap_metrics = plot_bootstrap(data, rng)
    model_figure, model_metrics = plot_model_band(rng)
    manifest = {
        "chapter": "DVP-010",
        "seed": SEED,
        "figures": [str(p.relative_to(ROOT)) for p in (group_figure, bootstrap_figure, model_figure)],
        "group_count": int(summary.shape[0]),
        "record_count": int(data.shape[0]),
        "bootstrap": bootstrap_metrics,
        "model": model_metrics,
    }
    (RESULT_DIR / "10-run-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
