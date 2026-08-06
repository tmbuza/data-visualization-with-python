"""Generate the offline, synthetic outputs for DVP chapter 11.

Run from the repository root:
    python scripts/python/11-geospatial-visualization.py
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import Normalize
from matplotlib.patches import Polygon


ROOT = Path(__file__).resolve().parents[2]
FIGURES = ROOT / "results" / "figures"
DATA = ROOT / "data" / "processed"
RESULTS = ROOT / "results" / "11-geospatial-visualization"

REGIONS = [
    {"id": "R01", "name": "Northwest", "population": 410_000, "served": 219_350, "facilities": 18, "xy": [(0, 2), (2, 2), (2, 4), (0, 4)]},
    {"id": "R02", "name": "North Central", "population": 520_000, "served": 390_000, "facilities": 31, "xy": [(2, 2), (4, 2), (4, 4), (2, 4)]},
    {"id": "R03", "name": "Northeast", "population": 315_000, "served": 204_750, "facilities": 16, "xy": [(4, 2), (6, 2), (6, 4), (4, 4)]},
    {"id": "R04", "name": "Southwest", "population": 365_000, "served": 310_250, "facilities": 24, "xy": [(0, 0), (2, 0), (2, 2), (0, 2)]},
    {"id": "R05", "name": "South Central", "population": 610_000, "served": 353_800, "facilities": 27, "xy": [(2, 0), (4, 0), (4, 2), (2, 2)]},
    {"id": "R06", "name": "Southeast", "population": 280_000, "served": 229_600, "facilities": 20, "xy": [(4, 0), (6, 0), (6, 2), (4, 2)]},
]


def enrich() -> None:
    for region in REGIONS:
        region["coverage_pct"] = 100 * region["served"] / region["population"]
        region["facilities_per_100k"] = 100_000 * region["facilities"] / region["population"]


def draw_map(ax, *, symbols: bool, title: str) -> None:
    cmap = plt.colormaps["cividis"]
    norm = Normalize(50, 90)
    for region in REGIONS:
        patch = Polygon(region["xy"], facecolor=cmap(norm(region["coverage_pct"])), edgecolor="white", linewidth=2)
        ax.add_patch(patch)
        x = np.mean([p[0] for p in region["xy"]])
        y = np.mean([p[1] for p in region["xy"]])
        ax.text(x, y + 0.22, region["id"], ha="center", va="center", fontsize=9, weight="bold")
        ax.text(x, y - 0.18, f'{region["coverage_pct"]:.0f}%', ha="center", va="center", fontsize=8)
        if symbols:
            ax.scatter(x, y - 0.62, s=region["facilities"] * 7, color="#b23a48", alpha=0.82, edgecolor="white", linewidth=0.8)
    ax.set(xlim=(-0.05, 6.05), ylim=(-0.05, 4.05), aspect="equal", title=title)
    ax.axis("off")


def save_choropleth() -> Path:
    fig, ax = plt.subplots(figsize=(9.2, 6.2))
    draw_map(ax, symbols=True, title="Service coverage and facility count")
    sm = plt.cm.ScalarMappable(norm=Normalize(50, 90), cmap="cividis")
    cbar = fig.colorbar(sm, ax=ax, orientation="horizontal", fraction=0.05, pad=0.04, shrink=0.72)
    cbar.set_label("Eligible population served (%)")
    fig.text(0.5, 0.015, "Circle area represents facility count • Synthetic demonstration data", ha="center", fontsize=9, color="#4b5563")
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    path = FIGURES / "11-geospatial-choropleth.png"
    fig.savefig(path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path


def save_map_and_ranking() -> Path:
    fig, (ax_map, ax_bar) = plt.subplots(1, 2, figsize=(12, 5.8), gridspec_kw={"width_ratios": [1.2, 1]})
    draw_map(ax_map, symbols=False, title="Where is coverage higher?")
    ordered = sorted(REGIONS, key=lambda x: x["coverage_pct"])
    values = [r["coverage_pct"] for r in ordered]
    colors = [plt.colormaps["cividis"](Normalize(50, 90)(v)) for v in values]
    ax_bar.barh([r["name"] for r in ordered], values, color=colors)
    ax_bar.set(xlim=(0, 100), xlabel="Eligible population served (%)", title="How large are the differences?")
    ax_bar.grid(axis="x", alpha=0.25)
    ax_bar.spines[["top", "right", "left"]].set_visible(False)
    for i, value in enumerate(values):
        ax_bar.text(value + 1, i, f"{value:.0f}%", va="center", fontsize=9)
    fig.suptitle("Spatial pattern and precise comparison", fontsize=15, weight="bold")
    fig.text(0.5, 0.01, "Synthetic demonstration data; boundaries do not represent real administrative units.", ha="center", fontsize=9, color="#4b5563")
    fig.tight_layout(rect=(0, 0.04, 1, 0.94))
    path = FIGURES / "11-geospatial-map-and-ranking.png"
    fig.savefig(path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return path


def write_data() -> tuple[Path, Path]:
    csv_path = DATA / "11-region-indicators.csv"
    fields = ["region_id", "region_name", "population", "served", "facilities", "coverage_pct", "facilities_per_100k"]
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for r in REGIONS:
            writer.writerow({
                "region_id": r["id"], "region_name": r["name"], "population": r["population"],
                "served": r["served"], "facilities": r["facilities"],
                "coverage_pct": f'{r["coverage_pct"]:.1f}',
                "facilities_per_100k": f'{r["facilities_per_100k"]:.2f}',
            })
    geojson_path = DATA / "11-synthetic-regions.geojson"
    features = []
    for r in REGIONS:
        ring = r["xy"] + [r["xy"][0]]
        features.append({"type": "Feature", "properties": {"region_id": r["id"], "region_name": r["name"], "coverage_pct": round(r["coverage_pct"], 1)}, "geometry": {"type": "Polygon", "coordinates": [ring]}})
    geojson_path.write_text(json.dumps({"type": "FeatureCollection", "features": features}, indent=2), encoding="utf-8")
    return csv_path, geojson_path


def main() -> None:
    for directory in (FIGURES, DATA, RESULTS):
        directory.mkdir(parents=True, exist_ok=True)
    enrich()
    outputs = [save_choropleth(), save_map_and_ranking(), *write_data()]
    manifest = RESULTS / "11-output-manifest.json"
    manifest.write_text(json.dumps({"chapter": "DVP-011", "data_note": "synthetic demonstration data", "outputs": [str(p.relative_to(ROOT)) for p in outputs]}, indent=2), encoding="utf-8")
    print(f"Generated {len(outputs) + 1} DVP-011 outputs")


if __name__ == "__main__":
    main()
