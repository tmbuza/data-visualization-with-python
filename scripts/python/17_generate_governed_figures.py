#!/usr/bin/env python3
"""Generate the governed figure release used by DVP chapter 17."""

from __future__ import annotations

import csv
import hashlib
import json
import os
import platform
from datetime import datetime, timezone
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "data/processed/17-publishing-runs.csv"
FIGURE_DIR = ROOT / "results/figures"
SUMMARY = ROOT / "results/17-publishing-summary.csv"
METADATA = ROOT / "results/17-publishing-success-rate.metadata.json"
INDEX = ROOT / "results/17-figure-index.csv"
ALT_TEXT = (
    "Horizontal bars show publishing success rates of 96 percent for Web, "
    "91 percent for PDF, and 88 percent for Slides. Web has the highest rate."
)
ORDER = ["Web", "PDF", "Slides"]
COLORS = ["#1f5a94", "#4b86b4", "#8cb3d9"]
EXPORT = {"width_inches": 8.0, "height_inches": 4.8, "dpi": 160}


def relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def read_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    with SOURCE.open(newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            total = int(row["total_runs"])
            successful = int(row["successful_runs"])
            if total <= 0 or not 0 <= successful <= total:
                raise ValueError(f"Invalid counts for {row['channel']}")
            rows.append({
                "channel": row["channel"], "total_runs": total,
                "successful_runs": successful, "success_rate": successful / total,
            })
    by_channel = {str(row["channel"]): row for row in rows}
    if set(by_channel) != set(ORDER):
        raise ValueError(f"Expected channels: {', '.join(ORDER)}")
    return [by_channel[channel] for channel in ORDER]


def write_summary(rows: list[dict[str, object]]) -> None:
    SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    with SUMMARY.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=["channel", "total_runs", "successful_runs", "success_rate"])
        writer.writeheader()
        for row in rows:
            writer.writerow({**row, "success_rate": f"{float(row['success_rate']):.4f}"})


def render(rows: list[dict[str, object]]) -> list[Path]:
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({
        "font.family": "DejaVu Sans", "axes.titleweight": "bold",
        "axes.edgecolor": "#d7dde5", "axes.labelcolor": "#263238",
        "text.color": "#263238", "xtick.color": "#52606d", "ytick.color": "#263238",
    })
    fig, ax = plt.subplots(figsize=(EXPORT["width_inches"], EXPORT["height_inches"]), facecolor="white")
    rates = [float(row["success_rate"]) for row in rows]
    bars = ax.barh(ORDER, rates, color=COLORS, height=0.58)
    ax.invert_yaxis()
    ax.set_xlim(0, 1.04)
    ax.set_xlabel("Successful publishing runs")
    ax.set_title("Publishing success remains high across delivery channels", loc="left", pad=16)
    ax.text(0, 1.03, "Share of automated runs completed without publication errors", transform=ax.transAxes, color="#52606d")
    ax.xaxis.set_major_formatter(lambda value, _: f"{value:.0%}")
    ax.grid(axis="x", color="#e9edf2", linewidth=0.8)
    ax.set_axisbelow(True)
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.tick_params(axis="y", length=0)
    for bar, rate in zip(bars, rates):
        ax.text(rate - 0.015, bar.get_y() + bar.get_height() / 2, f"{rate:.0%}", ha="right", va="center", color="white", fontweight="bold")
    fig.text(0.125, 0.015, "Source: synthetic publishing-run audit for DVP 17", fontsize=8.5, color="#697784")
    fig.subplots_adjust(left=0.16, right=0.96, top=0.78, bottom=0.20)
    outputs = [FIGURE_DIR / "17-publishing-success-rate.png", FIGURE_DIR / "17-publishing-success-rate.svg"]
    fig.savefig(outputs[0], dpi=EXPORT["dpi"], facecolor="white", metadata={"Title": "Publishing success rate by output channel"})
    fig.savefig(outputs[1], facecolor="white", metadata={"Title": "Publishing success rate by output channel"})
    plt.close(fig)
    return outputs


def write_governance(outputs: list[Path]) -> None:
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    artifacts = [{
        "path": relative(path), "format": path.suffix.lstrip("."),
        "bytes": path.stat().st_size, "sha256": sha256(path),
    } for path in outputs]
    metadata = {
        "figure_id": "DVP-017-F01", "title": "Publishing success rate by output channel",
        "alt_text": ALT_TEXT, "source_data": relative(SOURCE),
        "generator": "scripts/python/17_generate_governed_figures.py",
        "summary_data": relative(SUMMARY), "generated_at_utc": generated_at,
        "canvas_inches": [EXPORT["width_inches"], EXPORT["height_inches"]],
        "png_dpi": EXPORT["dpi"], "python_version": platform.python_version(),
        "matplotlib_version": matplotlib.__version__, "artifacts": artifacts,
        "validation_status": "pending",
    }
    METADATA.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    with INDEX.open("w", newline="", encoding="utf-8") as stream:
        fields = ["figure_id", "title", "format", "path", "bytes", "sha256", "source_data", "generator", "alt_text"]
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for artifact in artifacts:
            writer.writerow({"figure_id": metadata["figure_id"], "title": metadata["title"], **artifact,
                             "source_data": metadata["source_data"], "generator": metadata["generator"], "alt_text": ALT_TEXT})


def main() -> None:
    os.environ.setdefault("SOURCE_DATE_EPOCH", "0")
    rows = read_rows()
    write_summary(rows)
    outputs = render(rows)
    write_governance(outputs)
    print("Generated governed figure release:")
    for path in [*outputs, SUMMARY, METADATA, INDEX]:
        print(f"- {relative(path)}")


if __name__ == "__main__":
    main()
