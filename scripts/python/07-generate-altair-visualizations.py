#!/usr/bin/env python3
"""Generate the reproducible data and visual artifacts used in DVP Chapter 07."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = ROOT / "data/processed/07-altair-observations.csv"
FIGURE_DIR = ROOT / "results/figures"
MANIFEST_PATH = ROOT / "results/07-altair-chart-manifest.csv"
COLORS = {"North": "#2563EB", "Central": "#F59E0B", "South": "#059669"}


def make_data() -> pd.DataFrame:
    """Create a deterministic teaching dataset with time, groups, and measures."""
    rng = np.random.default_rng(20260806)
    dates = pd.date_range("2025-01-01", periods=24, freq="MS")
    rows: list[dict[str, object]] = []
    for region_index, region in enumerate(COLORS):
        for month_index, date in enumerate(dates):
            reach = 92 + region_index * 17 + month_index * 2.7 + rng.normal(0, 8)
            engagement = 42 + region_index * 5 + month_index * 0.65 + rng.normal(0, 4)
            rows.append(
                {
                    "date": date,
                    "region": region,
                    "reach": round(reach, 1),
                    "engagement": round(engagement, 1),
                    "completion_rate": round(np.clip(0.45 + engagement / 180 + rng.normal(0, .025), .45, .91), 3),
                }
            )
    return pd.DataFrame(rows)


def save_vega_html(spec: dict, path: Path, title: str) -> None:
    """Write a portable Vega-Lite wrapper around a complete specification."""
    html = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>{title}</title><script src="https://cdn.jsdelivr.net/npm/vega@5"></script>
<script src="https://cdn.jsdelivr.net/npm/vega-lite@5"></script>
<script src="https://cdn.jsdelivr.net/npm/vega-embed@6"></script></head>
<body><main id="vis"></main><script>vegaEmbed('#vis', {json.dumps(spec)}, {{actions: true}});</script></body></html>
"""
    path.write_text(html, encoding="utf-8")


def linked_spec(records: list[dict[str, object]]) -> dict:
    point = {"name": "region_pick", "select": {"type": "point", "fields": ["region"], "on": "click", "clear": "dblclick"}}
    base = {"data": {"values": records}, "params": [point]}
    scatter = {
        **base, "width": 420, "height": 280,
        "mark": {"type": "circle", "size": 85, "opacity": .8},
        "encoding": {
            "x": {"field": "reach", "type": "quantitative"}, "y": {"field": "engagement", "type": "quantitative"},
            "color": {"condition": {"param": "region_pick", "field": "region", "type": "nominal", "scale": {"domain": list(COLORS), "range": list(COLORS.values())}}, "value": "#D1D5DB"},
            "tooltip": [{"field": "date", "type": "temporal", "timeUnit": "yearmonth"}, {"field": "region"}, {"field": "reach"}, {"field": "engagement"}]
        }
    }
    trend = {
        "data": {"values": records}, "transform": [{"filter": {"param": "region_pick", "empty": True}}],
        "width": 420, "height": 280, "mark": {"type": "line", "point": True},
        "encoding": {"x": {"field": "date", "type": "temporal"}, "y": {"field": "completion_rate", "type": "quantitative", "scale": {"zero": False}},
                     "color": {"field": "region", "type": "nominal", "scale": {"domain": list(COLORS), "range": list(COLORS.values())}},
                     "tooltip": [{"field": "date", "type": "temporal", "timeUnit": "yearmonth"}, {"field": "region"}, {"field": "completion_rate", "format": ".1%"}]}
    }
    return {"$schema": "https://vega.github.io/schema/vega-lite/v5.json", "title": "Click a region to coordinate both views; double-click to reset", "hconcat": [scatter, trend], "resolve": {"scale": {"color": "shared"}}}


def focus_spec(records: list[dict[str, object]]) -> dict:
    selection = {"name": "brush", "select": {"type": "interval", "encodings": ["x"]}, "bind": "scales"}
    line_encoding = {"x": {"field": "date", "type": "temporal"}, "y": {"field": "engagement", "type": "quantitative", "scale": {"zero": False}}, "color": {"field": "region", "type": "nominal", "scale": {"domain": list(COLORS), "range": list(COLORS.values())}}}
    detail = {"width": 860, "height": 300, "data": {"values": records}, "params": [selection], "mark": {"type": "line", "point": True}, "encoding": line_encoding}
    context = {"width": 860, "height": 90, "data": {"values": records}, "mark": "line", "encoding": {**line_encoding, "x": {**line_encoding["x"], "axis": {"title": "Drag horizontally to inspect a time window"}}}}
    return {"$schema": "https://vega.github.io/schema/vega-lite/v5.json", "title": "Engagement through time: zoom and pan the detailed view", "vconcat": [detail, context]}


def save_previews(data: pd.DataFrame) -> None:
    plt.style.use("seaborn-v0_8-whitegrid")
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))
    for region, group in data.groupby("region"):
        axes[0].scatter(group["reach"], group["engagement"], s=35, alpha=.75, color=COLORS[region], label=region)
        axes[1].plot(group["date"], group["completion_rate"], marker="o", ms=3, lw=1.7, color=COLORS[region], label=region)
    axes[0].set(xlabel="Reach", ylabel="Engagement", title="Relationship view")
    axes[1].set(xlabel="Date", ylabel="Completion rate", title="Time view")
    axes[1].yaxis.set_major_formatter(lambda x, _: f"{x:.0%}")
    axes[0].legend(frameon=False)
    fig.suptitle("Linked-view static preview")
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "07-altair-linked-view.png", dpi=180, bbox_inches="tight")
    plt.close(fig)

    fig, (top, bottom) = plt.subplots(2, 1, figsize=(11, 5.8), height_ratios=[3, 1], sharex=True)
    for region, group in data.groupby("region"):
        top.plot(group["date"], group["engagement"], marker="o", ms=3, color=COLORS[region], label=region)
        bottom.plot(group["date"], group["engagement"], color=COLORS[region], lw=1.2)
    top.set(ylabel="Engagement", title="Focus and context static preview")
    bottom.set(xlabel="Date", ylabel="Context")
    top.legend(frameon=False, ncol=3)
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "07-altair-focus-context.png", dpi=180, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    data = make_data()
    data.to_csv(DATA_PATH, index=False, date_format="%Y-%m-%d")
    records = data.assign(date=data["date"].dt.strftime("%Y-%m-%d")).to_dict(orient="records")
    save_vega_html(linked_spec(records), FIGURE_DIR / "07-altair-linked-view.html", "Altair linked view")
    save_vega_html(focus_spec(records), FIGURE_DIR / "07-altair-focus-context.html", "Altair focus and context")
    save_previews(data)
    pd.DataFrame([
        {"file": "results/figures/07-altair-linked-view.html", "format": "interactive HTML", "purpose": "Coordinated selection across views"},
        {"file": "results/figures/07-altair-linked-view.png", "format": "PNG", "purpose": "Static preview of coordinated views"},
        {"file": "results/figures/07-altair-focus-context.html", "format": "interactive HTML", "purpose": "Zoomable time-series view"},
        {"file": "results/figures/07-altair-focus-context.png", "format": "PNG", "purpose": "Static focus-and-context preview"},
    ]).to_csv(MANIFEST_PATH, index=False)
    print(f"Generated {len(data)} observations and 4 visual artifacts.")


if __name__ == "__main__":
    main()
