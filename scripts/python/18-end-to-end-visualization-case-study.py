#!/usr/bin/env python3
"""Generate the reproducible artifacts for DVP Chapter 18."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

SEED = 18018
DISTRICTS = ["North", "Central", "South", "East", "West"]
SERVICES = ["Roads", "Waste", "Water", "Lighting"]
CHANNELS = ["Mobile app", "Web", "Phone", "Walk-in"]
OUTCOME_ORDER = ["On time", "Late", "Open"]


def generate_requests(n: int = 2400) -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    opened = pd.Timestamp("2025-01-01") + pd.to_timedelta(rng.integers(0, 365, n), unit="D")
    district = rng.choice(DISTRICTS, n, p=[.18, .24, .21, .20, .17])
    service = rng.choice(SERVICES, n, p=[.27, .31, .18, .24])
    channel = rng.choice(CHANNELS, n, p=[.34, .29, .27, .10])
    priority = rng.choice(["Routine", "Urgent", "Critical"], n, p=[.70, .24, .06])
    targets = pd.Series(service).map({"Roads": 120, "Waste": 48, "Water": 36, "Lighting": 72}).to_numpy()
    service_factor = pd.Series(service).map({"Roads": 1.18, "Waste": .88, "Water": 1.08, "Lighting": .92}).to_numpy()
    district_factor = pd.Series(district).map({"North": .92, "Central": 1.04, "South": 1.23, "East": .98, "West": 1.13}).to_numpy()
    priority_factor = pd.Series(priority).map({"Routine": 1.0, "Urgent": .72, "Critical": .42}).to_numpy()
    seasonal = 1 + .22 * np.sin((opened.dayofyear.to_numpy() - 35) * 2 * np.pi / 365)
    duration = targets * service_factor * district_factor * priority_factor * seasonal * rng.lognormal(0, .42, n)
    open_probability = np.clip(.045 + .06 * (duration > targets) + .025 * (district == "South"), 0, .22)
    completed = rng.random(n) > open_probability
    resolution = np.where(completed, np.round(duration, 1), np.nan)
    outcome = np.where(~completed, "Open", np.where(resolution <= targets, "On time", "Late"))
    satisfaction_mean = 4.45 - 1.35 * (outcome == "Late") - .25 * (resolution / targets > 1.6)
    satisfaction = np.where(completed, np.clip(np.rint(satisfaction_mean + rng.normal(0, .65, n)), 1, 5), np.nan)
    return pd.DataFrame({
        "request_id": [f"SR-{i:05d}" for i in range(1, n + 1)],
        "opened_date": opened,
        "district": district,
        "service_type": service,
        "channel": channel,
        "priority": priority,
        "target_hours": targets,
        "resolution_hours": resolution,
        "status": np.where(completed, "Completed", "Open"),
        "outcome": outcome,
        "satisfaction": satisfaction,
    }).sort_values(["opened_date", "request_id"]).reset_index(drop=True)


def save_monthly(df: pd.DataFrame, path: Path) -> pd.DataFrame:
    monthly = (df.assign(month=df.opened_date.dt.to_period("M").dt.to_timestamp())
                 .groupby("month", as_index=False)
                 .agg(requests=("request_id", "size"), completed=("status", lambda x: (x == "Completed").sum()),
                      on_time=("outcome", lambda x: (x == "On time").sum())))
    monthly["on_time_rate"] = monthly.on_time / monthly.completed
    monthly.to_csv(path, index=False)
    return monthly


def static_figures(df: pd.DataFrame, monthly: pd.DataFrame, figures: Path) -> list[dict]:
    sns.set_theme(style="whitegrid", context="talk")
    records = []
    fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True, constrained_layout=True)
    axes[0].plot(monthly.month, monthly.requests, marker="o", color="#4477AA", linewidth=2.5)
    axes[0].set(ylabel="Requests", title="Service demand and timely completion move through the year")
    axes[1].plot(monthly.month, monthly.on_time_rate * 100, marker="o", color="#228833", linewidth=2.5)
    axes[1].axhline(80, color="#CC6677", linestyle="--", label="80% target")
    axes[1].set(ylabel="On-time rate (%)", xlabel="Month", ylim=(25, 100))
    axes[1].legend(frameon=False)
    p = figures / "18-monthly-service-performance.png"; fig.savefig(p, dpi=180); plt.close(fig)
    records.append({"figure_id": "fig-dvp18-monthly", "path": str(p), "format": "PNG", "width_px": 2160, "height_px": 1440, "purpose": "Monthly overview"})

    completed = df[df.status == "Completed"]
    heat = completed.pivot_table(index="district", columns="service_type", values="outcome", aggfunc=lambda x: (x == "On time").mean()).reindex(index=DISTRICTS, columns=SERVICES)
    fig, ax = plt.subplots(figsize=(10, 6), constrained_layout=True)
    sns.heatmap(heat * 100, annot=True, fmt=".0f", cmap="YlGnBu", vmin=45, vmax=100, cbar_kws={"label": "On-time rate (%)"}, ax=ax)
    ax.set(title="Timely completion is concentrated by district and service", xlabel="Service type", ylabel="District")
    p = figures / "18-district-service-heatmap.png"; fig.savefig(p, dpi=180); plt.close(fig)
    records.append({"figure_id": "fig-dvp18-heatmap", "path": str(p), "format": "PNG", "width_px": 1800, "height_px": 1080, "purpose": "District-service diagnosis"})

    left = df.groupby(["channel", "service_type"]).size().reset_index(name="count")
    right = df.groupby(["service_type", "outcome"]).size().reset_index(name="count")
    # A dependency-light alluvial-style view: weighted connections and scaled nodes.
    fig, ax = plt.subplots(figsize=(12, 6.5), constrained_layout=True)
    columns = [(0, CHANNELS), (1, SERVICES), (2, OUTCOME_ORDER)]
    positions = {}
    for x, labels in columns:
        ys = np.linspace(.85, .15, len(labels))
        for label, y in zip(labels, ys):
            positions[label] = (x, y)
            ax.scatter(x, y, s=850, color="#EEEEEE", edgecolor="#333333", zorder=3)
            ax.text(x, y, label, ha="center", va="center", fontsize=10, zorder=4)
    for row in left.itertuples():
        x0, y0 = positions[row.channel]; x1, y1 = positions[row.service_type]
        ax.plot([x0, x1], [y0, y1], color="#4477AA", alpha=.28, linewidth=max(1, row.count / 45), solid_capstyle="round")
    outcome_colors = {"On time": "#228833", "Late": "#CC6677", "Open": "#999999"}
    for row in right.itertuples():
        x0, y0 = positions[row.service_type]; x1, y1 = positions[row.outcome]
        ax.plot([x0, x1], [y0, y1], color=outcome_colors[row.outcome], alpha=.38, linewidth=max(1, row.count / 45), solid_capstyle="round")
    ax.set(title="Requests flow from intake channel to service outcome", xlim=(-.25, 2.25), ylim=(.02, .98))
    ax.set_xticks([0, 1, 2], ["Intake channel", "Service type", "Outcome"]); ax.set_yticks([])
    for spine in ax.spines.values(): spine.set_visible(False)
    p = figures / "18-request-flow.png"; fig.savefig(p, dpi=180); plt.close(fig)
    records.append({"figure_id": "fig-dvp18-flow", "path": str(p), "format": "PNG", "width_px": 1800, "height_px": 975, "purpose": "Channel-service-outcome flow"})
    return records


def write_explorer(df: pd.DataFrame, path: Path) -> None:
    completed = df[df.status == "Completed"]
    payload = (completed.groupby(["district", "service_type"], as_index=False)
               .agg(requests=("request_id", "size"), median_hours=("resolution_hours", "median"),
                    p90_hours=("resolution_hours", lambda x: x.quantile(.9)), satisfaction=("satisfaction", "mean")))
    records = json.dumps(payload.round(1).to_dict(orient="records"))
    html = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>DVP 18 Resolution-time explorer</title><style>body{font:16px system-ui;max-width:960px;margin:2rem auto;padding:0 1rem;color:#222}label{font-weight:700}select{font:inherit;margin:.5rem;padding:.35rem}table{border-collapse:collapse;width:100%;margin-top:1rem}th,td{padding:.65rem;border-bottom:1px solid #ccc;text-align:right}th:first-child,td:first-child{text-align:left}caption{text-align:left;font-weight:700;margin-bottom:.5rem}.bar{height:.65rem;background:#4477aa;display:inline-block;margin-right:.5rem}</style>
<h1>Resolution-time explorer</h1><p>Choose a district to compare completed service requests. Values are rounded; p90 is the 90th percentile.</p><label for="district">District</label><select id="district"></select><table><caption id="caption"></caption><thead><tr><th>Service</th><th>Requests</th><th>Median hours</th><th>p90 hours</th><th>Mean satisfaction</th></tr></thead><tbody id="rows"></tbody></table>
<script>const data=DATA;const sel=document.querySelector('#district');[...new Set(data.map(d=>d.district))].forEach(x=>sel.add(new Option(x,x)));function draw(){const a=data.filter(d=>d.district===sel.value);document.querySelector('#caption').textContent=`Completed requests in ${sel.value}`;document.querySelector('#rows').innerHTML=a.map(d=>`<tr><td><span class="bar" style="width:${d.median_hours}px"></span>${d.service_type}</td><td>${d.requests}</td><td>${d.median_hours}</td><td>${d.p90_hours}</td><td>${d.satisfaction}</td></tr>`).join('')}sel.onchange=draw;draw()</script></html>'''.replace("DATA", records)
    path.write_text(html, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, default=Path("."))
    args = parser.parse_args()
    root = args.output_root.resolve()
    data_dir, results, figures, interactive = root / "data/processed", root / "results", root / "results/figures", root / "results/interactive"
    for directory in (data_dir, results, figures, interactive): directory.mkdir(parents=True, exist_ok=True)

    df = generate_requests()
    assert df.request_id.is_unique and df.target_hours.gt(0).all()
    assert df.loc[df.status.eq("Open"), "resolution_hours"].isna().all()
    df.to_csv(data_dir / "18-service-requests.csv", index=False, date_format="%Y-%m-%d")
    monthly = save_monthly(df, results / "18-monthly-performance.csv")
    summary = (df.groupby(["district", "service_type"], as_index=False)
                 .agg(requests=("request_id", "size"), completed=("status", lambda x: (x == "Completed").sum()),
                      on_time=("outcome", lambda x: (x == "On time").sum()), median_resolution_hours=("resolution_hours", "median"), mean_satisfaction=("satisfaction", "mean")))
    summary["on_time_rate"] = summary.on_time / summary.completed
    summary.to_csv(results / "18-service-summary.csv", index=False, float_format="%.3f")
    flow = df.groupby(["channel", "service_type", "outcome"], as_index=False).size().rename(columns={"size": "requests"})
    flow.to_csv(results / "18-flow-summary.csv", index=False)

    audit = pd.DataFrame({"metric": ["rows", "unique_request_ids", "open_requests", "completed_requests", "missing_resolution_hours", "grouped_count_reconciliation"],
                          "value": [len(df), df.request_id.nunique(), (df.status == "Open").sum(), (df.status == "Completed").sum(), df.resolution_hours.isna().sum(), summary.requests.sum()]})
    audit.to_csv(results / "18-data-audit.csv", index=False)
    assert summary.requests.sum() == len(df) and summary.on_time_rate.between(0, 1).all()

    write_explorer(df, interactive / "18-resolution-time-explorer.html")
    records = static_figures(df, monthly, figures)
    records.append({"figure_id": "interactive-dvp18-resolution", "path": str(interactive / "18-resolution-time-explorer.html"), "format": "HTML", "width_px": "responsive", "height_px": "responsive", "purpose": "Interactive distribution explorer"})
    manifest = pd.DataFrame(records)
    manifest["path"] = manifest.path.map(lambda x: str(Path(x).relative_to(root)))
    manifest.to_csv(results / "18-figure-manifest.csv", index=False)
    for artifact in manifest.path: assert (root / artifact).stat().st_size > 0
    print(f"Generated {len(df):,} requests and {len(manifest)} visual artifacts.")


if __name__ == "__main__":
    main()
