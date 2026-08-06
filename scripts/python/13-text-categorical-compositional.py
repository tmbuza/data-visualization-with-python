#!/usr/bin/env python3
"""Generate the reproducible data, summaries, and figures for DVP Chapter 13."""

from __future__ import annotations

import json
import re
from collections import Counter
from itertools import combinations
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

SEED = 1307
ROOT = Path(__file__).resolve().parents[2]
FIGURES = ROOT / "results" / "figures"
RESULTS = ROOT / "results"
DATA = ROOT / "data" / "processed"


def build_tickets(n: int = 600) -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    topics = np.array(["Account", "Billing", "Delivery", "Product", "Returns", "Technical"])
    channels = np.array(["Chat", "Email", "Phone", "Social", "Web"])
    regions = np.array(["Central", "East", "North", "West"])
    priorities = np.array(["Low", "Medium", "High", "Critical"])
    statuses = np.array(["Resolved", "Pending", "Escalated"])
    topic = rng.choice(topics, n, p=[.13, .20, .18, .15, .13, .21])
    channel = rng.choice(channels, n, p=[.25, .27, .19, .10, .19])
    region = rng.choice(regions, n, p=[.24, .28, .23, .25])
    priority = rng.choice(priorities, n, p=[.25, .39, .25, .11])
    period = rng.choice(["Earlier", "Recent"], n)

    base = pd.Series(topic).map({"Account": 4.5, "Billing": 6.7, "Delivery": 5.8,
                                  "Product": 4.9, "Returns": 6.1, "Technical": 8.2}).to_numpy()
    severity = pd.Series(priority).map({"Low": 2.4, "Medium": 1.2, "High": 0.0, "Critical": -1.2}).to_numpy()
    response = np.maximum(.3, base + severity + rng.gamma(2.0, 1.1, n) - 2.0)

    resolved_probability = .74 + (period == "Recent") * .07
    resolved_probability += pd.Series(channel).map({"Chat": .04, "Email": -.02, "Phone": .03,
                                                      "Social": -.08, "Web": 0}).to_numpy()
    resolved_probability -= (priority == "Critical") * .18
    draw = rng.random(n)
    status = np.where(draw < resolved_probability, "Resolved",
                      np.where(draw < resolved_probability + .16, "Pending", "Escalated"))

    topic_words = {
        "Account": ["account", "login", "access", "password"],
        "Billing": ["invoice", "charge", "payment", "refund"],
        "Delivery": ["delivery", "late", "tracking", "address"],
        "Product": ["product", "quality", "feature", "replacement"],
        "Returns": ["return", "refund", "label", "replacement"],
        "Technical": ["error", "update", "device", "connection"],
    }
    status_words = {
        "Resolved": ["thanks", "helpful", "fixed", "quick"],
        "Pending": ["waiting", "update", "still", "response"],
        "Escalated": ["urgent", "repeated", "unresolved", "frustrated"],
    }
    comments = []
    for t, s in zip(topic, status):
        selected = rng.choice(topic_words[t], 2, replace=False).tolist()
        selected += rng.choice(status_words[s], 2, replace=False).tolist()
        comments.append("Please help with " + " ".join(selected) + ".")

    return pd.DataFrame({
        "ticket_id": [f"T{i:04d}" for i in range(1, n + 1)], "period": period,
        "region": region, "priority": priority, "channel": channel, "topic": topic,
        "status": status, "response_hours": response.round(2), "comment": comments,
    })


def save_ranking(df: pd.DataFrame) -> pd.DataFrame:
    summary = (df.groupby("topic", as_index=False).agg(
        tickets=("ticket_id", "size"), median_response_hours=("response_hours", "median"))
        .sort_values("median_response_hours"))
    fig, ax = plt.subplots(figsize=(8, 4.8))
    ax.hlines(summary.topic, 0, summary.median_response_hours, color="#CBD5E1", lw=2)
    ax.scatter(summary.median_response_hours, summary.topic, s=75, color="#1565C0", zorder=3)
    for row in summary.itertuples():
        ax.text(row.median_response_hours + .12, row.topic, f"{row.median_response_hours:.1f} h", va="center")
    ax.set(xlabel="Median first-response time (hours)", ylabel="", title="Technical tickets wait longest for a first response")
    ax.set_xlim(left=0); sns.despine(ax=ax, left=True); fig.tight_layout()
    fig.savefig(FIGURES / "13-category-ranking.png", dpi=180); plt.close(fig)
    return summary


def save_slope(df: pd.DataFrame) -> None:
    rates = (df.assign(resolved=df.status.eq("Resolved")).groupby(["channel", "period"])
             .resolved.mean().mul(100).unstack())
    fig, ax = plt.subplots(figsize=(8, 5))
    colors = sns.color_palette("colorblind", n_colors=len(rates))
    for (channel, row), color in zip(rates.iterrows(), colors):
        y = [row["Earlier"], row["Recent"]]
        ax.plot([0, 1], y, marker="o", lw=2.2, color=color)
        ax.text(-.03, y[0], f"{channel}  {y[0]:.0f}%", ha="right", va="center", color=color)
        ax.text(1.03, y[1], f"{y[1]:.0f}%  {channel}", ha="left", va="center", color=color)
    ax.set(xticks=[0, 1], xticklabels=["Earlier", "Recent"], ylabel="Resolved tickets (%)",
           title="Resolution rates generally improved in the recent period", xlim=(-.35, 1.35), ylim=(45, 100))
    sns.despine(ax=ax); fig.tight_layout(); fig.savefig(FIGURES / "13-channel-slope.png", dpi=180); plt.close(fig)


def save_composition(df: pd.DataFrame) -> None:
    order = ["Resolved", "Pending", "Escalated"]
    comp = pd.crosstab(df.channel, df.status, normalize="index")[order].mul(100)
    comp = comp.loc[comp.Resolved.sort_values().index]
    fig, ax = plt.subplots(figsize=(8.5, 5))
    comp.plot.barh(stacked=True, color=["#2A9D8F", "#E9C46A", "#E76F51"], ax=ax, width=.72)
    ax.set(xlabel="Share within channel (%)", ylabel="", title="Ticket outcomes differ by support channel", xlim=(0, 100))
    ax.legend(title="Status", ncol=3, loc="upper center", bbox_to_anchor=(.5, -.16), frameon=False)
    sns.despine(ax=ax, left=True); fig.tight_layout(); fig.savefig(FIGURES / "13-channel-composition.png", dpi=180); plt.close(fig)


def tokens(text: str) -> set[str]:
    stop = {"a", "and", "for", "is", "of", "please", "the", "to", "with"}
    return {w for w in re.findall(r"[a-z]+", text.lower()) if w not in stop}


def save_text_outputs(df: pd.DataFrame) -> None:
    doc_tokens = [tokens(x) for x in df.comment]
    pair_counts: Counter[tuple[str, str]] = Counter()
    for words in doc_tokens:
        pair_counts.update(combinations(sorted(words), 2))
    pairs = pd.DataFrame([(a, b, count) for (a, b), count in pair_counts.most_common(25)],
                         columns=["term_1", "term_2", "document_cooccurrence"])
    pairs.to_csv(RESULTS / "13-term-cooccurrence.csv", index=False)

    selected = ["urgent", "frustrated", "waiting", "quick", "helpful", "refund", "error"]
    records = []
    for status in ["Resolved", "Escalated"]:
        indices = df.index[df.status.eq(status)]
        for term in selected:
            present = sum(term in doc_tokens[i] for i in indices)
            records.append((status, term, 100 * present / len(indices)))
    prevalence = pd.DataFrame(records, columns=["status", "term", "document_percent"])
    term_order = (prevalence.groupby("term").document_percent.max().sort_values().index)
    prevalence["term"] = pd.Categorical(prevalence["term"], categories=term_order, ordered=True)
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.scatterplot(data=prevalence, x="document_percent", y="term", hue="status",
                    hue_order=["Resolved", "Escalated"], palette=["#2A9D8F", "#E76F51"], s=85, ax=ax)
    ax.set(xlabel="Tickets containing term (%)", ylabel="", title="Escalated comments use distinctly urgent language")
    ax.legend(title="Ticket status", frameon=False); sns.despine(ax=ax); fig.tight_layout()
    fig.savefig(FIGURES / "13-term-comparison.png", dpi=180); plt.close(fig)


def save_heatmap(df: pd.DataFrame) -> None:
    priority_order = ["Low", "Medium", "High", "Critical"]
    matrix = df.pivot_table(index="priority", columns="region", values="response_hours", aggfunc="median").loc[priority_order]
    fig, ax = plt.subplots(figsize=(8, 4.8))
    sns.heatmap(matrix, annot=True, fmt=".1f", cmap="YlGnBu", cbar_kws={"label": "Median hours"}, ax=ax)
    ax.set(xlabel="Region", ylabel="Priority", title="Response time varies across priority and region")
    fig.tight_layout(); fig.savefig(FIGURES / "13-priority-region-heatmap.png", dpi=180); plt.close(fig)


def main() -> None:
    FIGURES.mkdir(parents=True, exist_ok=True); DATA.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid", context="notebook")
    df = build_tickets(); df.to_csv(DATA / "13-support-tickets.csv", index=False)
    category_summary = save_ranking(df); category_summary.to_csv(RESULTS / "13-category-summary.csv", index=False)
    save_slope(df); save_composition(df); save_text_outputs(df); save_heatmap(df)
    manifest = {"chapter": "DVP-013", "seed": SEED, "ticket_count": len(df),
                "figures": sorted(p.name for p in FIGURES.glob("13-*.png")),
                "tables": ["results/13-category-summary.csv", "results/13-term-cooccurrence.csv"]}
    (RESULTS / "13-run-summary.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Generated {len(manifest['figures'])} figures and chapter summaries for {len(df)} tickets.")


if __name__ == "__main__":
    main()
