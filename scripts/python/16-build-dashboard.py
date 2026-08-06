#!/usr/bin/env python3
"""Build the reproducible artifacts for DVP Chapter 16."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


REGIONS = ("Central", "Coastal", "Lake", "Northern")
COLORS = {
    "Central": "#0072B2",
    "Coastal": "#E69F00",
    "Lake": "#009E73",
    "Northern": "#CC79A7",
}
TARGET = 0.92


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=1607)
    parser.add_argument("--days", type=int, default=90)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    return parser.parse_args()


def generate_data(seed: int, days: int) -> pd.DataFrame:
    if days < 14:
        raise ValueError("--days must be at least 14")
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2026-04-01", periods=days, freq="D")
    region_effect = {"Central": 0.01, "Coastal": -0.015, "Lake": 0.025, "Northern": -0.005}
    workload = {"Central": 125, "Coastal": 105, "Lake": 82, "Northern": 94}
    records: list[dict[str, object]] = []

    for day_index, date in enumerate(dates):
        weekly = 0.012 * np.sin(2 * np.pi * day_index / 7)
        improvement = 0.025 * day_index / max(days - 1, 1)
        for region in REGIONS:
            requests = int(rng.poisson(workload[region] * (0.88 if date.dayofweek >= 5 else 1.0)))
            probability = np.clip(0.89 + region_effect[region] + weekly + improvement, 0.78, 0.98)
            completed = int(rng.binomial(requests, probability))
            median_hours = max(4.0, 21.0 - 20.0 * (probability - 0.88) + rng.normal(0, 1.8))
            satisfaction = float(np.clip(3.55 + 2.0 * (probability - 0.85) + rng.normal(0, 0.12), 1, 5))
            records.append(
                {
                    "date": date,
                    "region": region,
                    "requests": requests,
                    "completed": completed,
                    "completion_rate": completed / requests if requests else np.nan,
                    "median_resolution_hours": median_hours,
                    "satisfaction_score": satisfaction,
                }
            )
    return pd.DataFrame.from_records(records)


def validate(data: pd.DataFrame, days: int) -> list[str]:
    expected = {
        "date", "region", "requests", "completed", "completion_rate",
        "median_resolution_hours", "satisfaction_score",
    }
    checks = {
        "required columns present": expected.issubset(data.columns),
        "date-region keys unique": not data.duplicated(["date", "region"]).any(),
        "expected row count": len(data) == days * len(REGIONS),
        "all regions present": set(data["region"]) == set(REGIONS),
        "no missing values": not data[list(expected)].isna().any().any(),
        "requests positive": data["requests"].gt(0).all(),
        "completed bounded by requests": data["completed"].between(0, data["requests"]).all(),
        "completion rates bounded": data["completion_rate"].between(0, 1).all(),
        "satisfaction bounded": data["satisfaction_score"].between(1, 5).all(),
    }
    failures = [name for name, passed in checks.items() if not passed]
    if failures:
        raise ValueError("Validation failed: " + ", ".join(failures))
    return [f"PASS | {name}" for name in checks]


def summarize(data: pd.DataFrame) -> pd.DataFrame:
    summary = data.groupby("region", as_index=False).agg(
        requests=("requests", "sum"),
        completed=("completed", "sum"),
        median_resolution_hours=("median_resolution_hours", "median"),
        satisfaction_score=("satisfaction_score", "mean"),
    )
    summary["completion_rate"] = summary["completed"] / summary["requests"]
    return summary[
        ["region", "requests", "completed", "completion_rate", "median_resolution_hours", "satisfaction_score"]
    ]


def plot_static(data: pd.DataFrame, summary: pd.DataFrame, output: Path) -> None:
    plt.style.use("seaborn-v0_8-whitegrid")
    fig = plt.figure(figsize=(14, 9), constrained_layout=True)
    grid = fig.add_gridspec(3, 4, height_ratios=[0.72, 2.2, 2.0])

    total_requests = int(data["requests"].sum())
    completion = data["completed"].sum() / total_requests
    resolution = data["median_resolution_hours"].median()
    satisfaction = np.average(data["satisfaction_score"], weights=data["completed"])
    cards = [
        ("Requests", f"{total_requests:,}", "90-day workload"),
        ("Completion", f"{completion:.1%}", f"Target {TARGET:.0%}"),
        ("Median resolution", f"{resolution:.1f} h", "Guardrail metric"),
        ("Satisfaction", f"{satisfaction:.2f}/5", "Completed cases"),
    ]
    for i, (title, value, note) in enumerate(cards):
        ax = fig.add_subplot(grid[0, i])
        ax.set_facecolor("#F3F6F8")
        ax.text(0.05, 0.75, title, fontsize=11, color="#405261", transform=ax.transAxes)
        ax.text(0.05, 0.36, value, fontsize=22, weight="bold", color="#142B3A", transform=ax.transAxes)
        ax.text(0.05, 0.08, note, fontsize=9, color="#5B6870", transform=ax.transAxes)
        ax.set_xticks([]); ax.set_yticks([])
        for spine in ax.spines.values(): spine.set_visible(False)

    trend_ax = fig.add_subplot(grid[1, :3])
    for region in REGIONS:
        subset = data[data["region"] == region]
        trend_ax.plot(subset["date"], subset["completion_rate"], label=region, color=COLORS[region], lw=1.8)
    trend_ax.axhline(TARGET, color="#222222", linestyle="--", lw=1.2, label="92% target")
    trend_ax.set(title="Daily completion rate", ylabel="Completion rate", xlabel="")
    trend_ax.yaxis.set_major_formatter(lambda x, pos: f"{x:.0%}")
    trend_ax.legend(ncol=3, frameon=False, fontsize=9)

    volume_ax = fig.add_subplot(grid[1, 3])
    volume = data.groupby("region")["requests"].sum().reindex(REGIONS)
    volume_ax.barh(volume.index, volume.values, color=[COLORS[r] for r in volume.index])
    volume_ax.set(title="Requests by region", xlabel="Requests")
    volume_ax.tick_params(axis="y", labelsize=9)

    comp_ax = fig.add_subplot(grid[2, :2])
    ordered = summary.sort_values("completion_rate")
    comp_ax.barh(ordered["region"], ordered["completion_rate"], color=[COLORS[r] for r in ordered["region"]])
    comp_ax.axvline(TARGET, color="#222222", linestyle="--", lw=1.2)
    comp_ax.set(title="Regional completion rate", xlabel="Completion rate")
    comp_ax.xaxis.set_major_formatter(lambda x, pos: f"{x:.0%}")
    comp_ax.set_xlim(0.84, 0.97)

    resolution_ax = fig.add_subplot(grid[2, 2:])
    ordered = summary.sort_values("median_resolution_hours", ascending=False)
    resolution_ax.barh(ordered["region"], ordered["median_resolution_hours"], color=[COLORS[r] for r in ordered["region"]])
    resolution_ax.set(title="Median resolution time", xlabel="Hours")

    fig.suptitle("Service Operations Dashboard", x=0.01, ha="left", fontsize=20, weight="bold", color="#142B3A")
    fig.text(0.01, 0.955, f"{data['date'].min():%d %b %Y}–{data['date'].max():%d %b %Y} | Synthetic instructional data", fontsize=10, color="#5B6870")
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def plot_interactive(data: pd.DataFrame, summary: pd.DataFrame, output: Path) -> None:
    records = data.assign(date=data["date"].dt.strftime("%Y-%m-%d")).to_dict(orient="records")
    payload = json.dumps(records, separators=(",", ":"))
    colors = json.dumps(COLORS)
    html = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Service Operations Linked Dashboard</title>
<style>
:root{font-family:system-ui,sans-serif;color:#142b3a;background:#f5f7f9}body{margin:0;padding:1.25rem;max-width:1200px;margin:auto}
h1{margin:.2rem 0}.sub{color:#56636c}.toolbar{margin:1rem 0}label{font-weight:650}select{margin-left:.5rem;padding:.45rem}
.cards{display:grid;grid-template-columns:repeat(4,1fr);gap:.8rem}.card,.panel{background:white;border:1px solid #dfe5e8;border-radius:8px;padding:1rem}
.value{font-size:1.7rem;font-weight:750}.note{font-size:.85rem;color:#5b6870}.grid{display:grid;grid-template-columns:2fr 1fr;gap:.8rem;margin-top:.8rem}
.wide{grid-column:1/-1}svg{width:100%;height:300px;overflow:visible}.axis{stroke:#60717c;stroke-width:1}.target{stroke:#222;stroke-dasharray:5 4}
.line{fill:none;stroke-width:2}.point{stroke:white;stroke-width:1.5}.tip{position:fixed;background:#142b3a;color:white;padding:.45rem .6rem;border-radius:5px;pointer-events:none;font-size:.82rem;display:none}
@media(max-width:760px){.cards,.grid{grid-template-columns:1fr}.wide{grid-column:auto}}@media(prefers-reduced-motion:reduce){*{scroll-behavior:auto!important}}
</style></head><body>
<h1>Service Operations</h1><p class="sub">Linked region selection · synthetic instructional data</p>
<div class="toolbar"><label for="region">Region</label><select id="region"><option>All regions</option></select></div>
<section class="cards" id="cards" aria-label="Headline metrics"></section>
<section class="grid"><article class="panel wide"><h2>Daily completion rate</h2><svg id="trend" role="img" aria-label="Daily completion rate trend"></svg></article>
<article class="panel"><h2>Daily requests</h2><svg id="volume" role="img" aria-label="Daily request volume"></svg></article>
<article class="panel"><h2>Regional performance</h2><svg id="compare" role="img" aria-label="Completion rate by region"></svg></article></section>
<div class="tip" id="tip" role="status"></div>
<script>
const DATA=__DATA__, COLORS=__COLORS__, REGIONS=Object.keys(COLORS), NS='http://www.w3.org/2000/svg';
const sel=document.querySelector('#region');REGIONS.forEach(r=>sel.add(new Option(r,r)));sel.addEventListener('change',render);
function node(tag,a={}){const n=document.createElementNS(NS,tag);Object.entries(a).forEach(([k,v])=>n.setAttribute(k,v));return n}
function filtered(){return sel.value==='All regions'?DATA:DATA.filter(d=>d.region===sel.value)}
function metrics(d){const req=d.reduce((s,x)=>s+x.requests,0),done=d.reduce((s,x)=>s+x.completed,0),hrs=[...d].sort((a,b)=>a.median_resolution_hours-b.median_resolution_hours),sat=d.reduce((s,x)=>s+x.satisfaction_score*x.completed,0)/done;return [
['Requests',req.toLocaleString(),'Selected workload'],['Completion',(done/req*100).toFixed(1)+'%','Target 92%'],['Median resolution',hrs[Math.floor(hrs.length/2)].median_resolution_hours.toFixed(1)+' h','Guardrail metric'],['Satisfaction',sat.toFixed(2)+'/5','Completed cases']]}
function renderCards(d){document.querySelector('#cards').innerHTML=metrics(d).map(x=>`<div class="card"><div>${x[0]}</div><div class="value">${x[1]}</div><div class="note">${x[2]}</div></div>`).join('')}
function setup(id){const s=document.querySelector(id);s.innerHTML='';s.setAttribute('viewBox','0 0 700 300');s.append(node('line',{x1:50,y1:255,x2:680,y2:255,class:'axis'}));s.append(node('line',{x1:50,y1:20,x2:50,y2:255,class:'axis'}));return s}
function tip(e,text){const t=document.querySelector('#tip');t.textContent=text;t.style.display='block';t.style.left=(e.clientX+12)+'px';t.style.top=(e.clientY+12)+'px'}
function trend(d){const s=setup('#trend'),dates=[...new Set(d.map(x=>x.date))],groups=REGIONS.filter(r=>d.some(x=>x.region===r));const X=x=>50+dates.indexOf(x)/Math.max(1,dates.length-1)*630,Y=y=>255-(y-.78)/.22*235;s.append(node('line',{x1:50,y1:Y(.92),x2:680,y2:Y(.92),class:'target'}));groups.forEach(r=>{const q=d.filter(x=>x.region===r),p=node('polyline',{points:q.map(x=>`${X(x.date)},${Y(x.completion_rate)}`).join(' '),class:'line',stroke:COLORS[r]});s.append(p);q.filter((_,i)=>i%7===0).forEach(x=>{const c=node('circle',{cx:X(x.date),cy:Y(x.completion_rate),r:4,fill:COLORS[r],class:'point',tabindex:0});c.addEventListener('mousemove',e=>tip(e,`${r} · ${x.date} · ${(x.completion_rate*100).toFixed(1)}%`));c.addEventListener('mouseout',()=>document.querySelector('#tip').style.display='none');s.append(c)})})}
function volume(d){const s=setup('#volume'),by={};d.forEach(x=>by[x.date]=(by[x.date]||0)+x.requests);const a=Object.entries(by),max=Math.max(...a.map(x=>x[1])),w=630/a.length;a.forEach(([date,v],i)=>s.append(node('rect',{x:50+i*w,y:255-v/max*220,width:Math.max(1,w-.5),height:v/max*220,fill:'#0072B2'})))}
function compare(d){const s=setup('#compare'),groups=REGIONS.filter(r=>d.some(x=>x.region===r));groups.forEach((r,i)=>{const q=d.filter(x=>x.region===r),rate=q.reduce((z,x)=>z+x.completed,0)/q.reduce((z,x)=>z+x.requests,0),w=(rate-.8)/.2*600,y=45+i*52;s.append(node('rect',{x:50,y,width:w,height:28,fill:COLORS[r]}));const t=node('text',{x:55,y:y+20,fill:'white'});t.textContent=`${r} ${(rate*100).toFixed(1)}%`;s.append(t)})}
function render(){const d=filtered();renderCards(d);trend(d);volume(d);compare(d)}render();
</script></body></html>'''.replace('__DATA__', payload).replace('__COLORS__', colors)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html, encoding="utf-8")


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    paths = {
        "data": root / "data/processed/16-service-operations.csv",
        "summary": root / "results/16-dashboard-summary.csv",
        "validation": root / "results/16-dashboard-validation.txt",
        "preview": root / "results/figures/16-dashboard-preview.png",
        "interactive": root / "results/interactive/16-linked-dashboard.html",
        "manifest": root / "results/16-dashboard-manifest.json",
    }
    for path in paths.values(): path.parent.mkdir(parents=True, exist_ok=True)
    data = generate_data(args.seed, args.days)
    checks = validate(data, args.days)
    summary = summarize(data)
    data.to_csv(paths["data"], index=False, date_format="%Y-%m-%d", float_format="%.4f")
    summary.to_csv(paths["summary"], index=False, float_format="%.4f")
    paths["validation"].write_text("DVP-016 dashboard validation\n" + "\n".join(checks) + "\n", encoding="utf-8")
    plot_static(data, summary, paths["preview"])
    plot_interactive(data, summary, paths["interactive"])
    manifest = {
        "chapter": "DVP-016",
        "seed": args.seed,
        "days": args.days,
        "date_min": data["date"].min().date().isoformat(),
        "date_max": data["date"].max().date().isoformat(),
        "rows": len(data),
        "regions": list(REGIONS),
        "target_completion_rate": TARGET,
        "artifacts": [str(path.relative_to(root)) for path in paths.values() if path != paths["manifest"]],
    }
    paths["manifest"].write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"DVP-016 workflow complete: {len(data)} rows, {len(paths)} artifacts")


if __name__ == "__main__":
    main()
