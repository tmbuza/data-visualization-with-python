#!/usr/bin/env python3
"""Generate the DVP 12 network, flow figures, and analytical summaries."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Rectangle
import networkx as nx
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
RESULTS = ROOT / "results"
FIGURES = RESULTS / "figures"

NODES = [
    ("Farm North", "supplier", "North"),
    ("Farm West", "supplier", "West"),
    ("Co-op Lake", "supplier", "Lake"),
    ("Plant A", "processor", "North"),
    ("Plant B", "processor", "West"),
    ("Hub East", "distributor", "East"),
    ("Hub Central", "distributor", "Central"),
    ("Market Metro", "market", "East"),
    ("Market Coast", "market", "Coast"),
]

EDGES = [
    ("Farm North", "Plant A", 84, 2.0),
    ("Farm West", "Plant A", 38, 3.5),
    ("Farm West", "Plant B", 62, 1.8),
    ("Co-op Lake", "Plant B", 73, 2.6),
    ("Plant A", "Hub East", 68, 2.2),
    ("Plant A", "Hub Central", 49, 1.5),
    ("Plant B", "Hub East", 42, 3.0),
    ("Plant B", "Hub Central", 81, 2.0),
    ("Hub East", "Market Metro", 51, 1.1),
    ("Hub East", "Market Coast", 54, 1.7),
    ("Hub Central", "Market Metro", 67, 1.4),
    ("Hub Central", "Market Coast", 59, 2.1),
]

STAGE_ORDER = ["supplier", "processor", "distributor", "market"]
STAGE_LABELS = {
    "supplier": "Suppliers",
    "processor": "Processors",
    "distributor": "Distributors",
    "market": "Markets",
}


def build_graph() -> nx.DiGraph:
    """Return a validated directed, weighted distribution graph."""
    graph = nx.DiGraph()
    for name, stage, region in NODES:
        graph.add_node(name, stage=stage, region=region)
    for source, target, volume, lead_days in EDGES:
        graph.add_edge(source, target, volume=volume, lead_days=lead_days)

    assert nx.is_directed_acyclic_graph(graph)
    assert nx.number_weakly_connected_components(graph) == 1
    assert not list(nx.selfloop_edges(graph))
    assert all(data["volume"] > 0 for *_, data in graph.edges(data=True))
    return graph


def analyse_nodes(graph: nx.DiGraph) -> pd.DataFrame:
    """Calculate node metrics and weighted modularity communities."""
    undirected = graph.to_undirected()
    groups = nx.community.greedy_modularity_communities(
        undirected, weight="volume"
    )
    community = {
        node: group_id
        for group_id, group in enumerate(groups, start=1)
        for node in group
    }
    betweenness = nx.betweenness_centrality(graph, normalized=True)
    pagerank = nx.pagerank(graph, weight="volume")

    records = []
    for node, attrs in graph.nodes(data=True):
        records.append(
            {
                "node": node,
                "stage": attrs["stage"],
                "region": attrs["region"],
                "community": community[node],
                "in_degree": graph.in_degree(node),
                "out_degree": graph.out_degree(node),
                "in_volume": graph.in_degree(node, weight="volume"),
                "out_volume": graph.out_degree(node, weight="volume"),
                "betweenness": betweenness[node],
                "pagerank": pagerank[node],
            }
        )
    return pd.DataFrame(records).sort_values(
        ["stage", "betweenness", "node"], ascending=[True, False, True]
    )


def draw_network(graph: nx.DiGraph, summary: pd.DataFrame, path: Path) -> None:
    """Draw a layered node-link view with separate visual channels."""
    y_slots = {
        "supplier": [0.78, 0.50, 0.22],
        "processor": [0.66, 0.34],
        "distributor": [0.66, 0.34],
        "market": [0.66, 0.34],
    }
    positions = {}
    for stage_index, stage in enumerate(STAGE_ORDER):
        stage_nodes = sorted(
            node for node, data in graph.nodes(data=True) if data["stage"] == stage
        )
        for node, y in zip(stage_nodes, y_slots[stage], strict=True):
            positions[node] = (stage_index, y)

    metric = summary.set_index("node")
    palette = {1: "#2A6FBB", 2: "#E37A24", 3: "#3A9D75"}
    node_colors = [palette[int(metric.loc[node, "community"])] for node in graph]
    node_sizes = [900 + 9000 * metric.loc[node, "betweenness"] for node in graph]
    widths = [0.6 + graph[u][v]["volume"] / 34 for u, v in graph.edges()]

    fig, ax = plt.subplots(figsize=(13, 7.2))
    nx.draw_networkx_edges(
        graph,
        positions,
        ax=ax,
        width=widths,
        edge_color="#7E8A97",
        alpha=0.58,
        arrows=True,
        arrowsize=15,
        connectionstyle="arc3,rad=0.035",
        min_source_margin=18,
        min_target_margin=18,
    )
    nx.draw_networkx_nodes(
        graph,
        positions,
        ax=ax,
        node_color=node_colors,
        node_size=node_sizes,
        edgecolors="white",
        linewidths=1.8,
    )
    nx.draw_networkx_labels(graph, positions, ax=ax, font_size=9, font_weight="bold")

    for index, stage in enumerate(STAGE_ORDER):
        ax.text(
            index,
            0.96,
            STAGE_LABELS[stage],
            ha="center",
            va="center",
            fontsize=11,
            fontweight="bold",
            color="#243447",
        )
    ax.set_title(
        "Distribution network: structure, communities, and flow",
        loc="left",
        fontsize=16,
        fontweight="bold",
        pad=18,
    )
    ax.text(
        0,
        0.99,
        "Node size = betweenness  •  node color = detected community  •  edge width = volume",
        transform=ax.transAxes,
        fontsize=10,
        color="#52616B",
        va="bottom",
    )
    ax.set_xlim(-0.35, 3.35)
    ax.set_ylim(0.08, 1.02)
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def aggregate_stage_flows(graph: nx.DiGraph) -> pd.DataFrame:
    """Aggregate edge volume between adjacent supply-chain stages."""
    records = []
    for source, target, data in graph.edges(data=True):
        records.append(
            {
                "source_stage": graph.nodes[source]["stage"],
                "target_stage": graph.nodes[target]["stage"],
                "volume": data["volume"],
                "edge_count": 1,
            }
        )
    return (
        pd.DataFrame(records)
        .groupby(["source_stage", "target_stage"], as_index=False)
        .agg(volume=("volume", "sum"), edge_count=("edge_count", "sum"))
    )


def draw_stage_flow(stage_flow: pd.DataFrame, path: Path) -> None:
    """Draw an accessible static alternative to an interactive Sankey."""
    totals = {
        (row.source_stage, row.target_stage): row.volume
        for row in stage_flow.itertuples(index=False)
    }
    max_volume = max(totals.values())
    colors = ["#2A6FBB", "#3A9D75", "#E37A24", "#8B5FBF"]

    fig, ax = plt.subplots(figsize=(12, 5.5))
    node_width, node_height, y = 0.32, 0.46, 0.5
    for index, stage in enumerate(STAGE_ORDER):
        rectangle = Rectangle(
            (index - node_width / 2, y - node_height / 2),
            node_width,
            node_height,
            facecolor=colors[index],
            edgecolor="white",
            linewidth=2,
            zorder=3,
        )
        ax.add_patch(rectangle)
        ax.text(
            index,
            y,
            STAGE_LABELS[stage],
            ha="center",
            va="center",
            color="white",
            fontsize=10,
            fontweight="bold",
            zorder=4,
        )

    for index, (source_stage, target_stage) in enumerate(zip(STAGE_ORDER, STAGE_ORDER[1:])):
        volume = totals[(source_stage, target_stage)]
        arrow = FancyArrowPatch(
            (index + node_width / 2, y),
            (index + 1 - node_width / 2, y),
            arrowstyle="-|>",
            mutation_scale=16,
            linewidth=5 + 18 * volume / max_volume,
            color="#AAB4BE",
            alpha=0.72,
            zorder=1,
        )
        ax.add_patch(arrow)
        ax.text(
            index + 0.5,
            y + 0.23,
            f"{volume:,} units",
            ha="center",
            va="bottom",
            fontsize=11,
            fontweight="bold",
            color="#243447",
        )

    ax.set_title(
        "Aggregated annual flow across supply-chain stages",
        loc="left",
        fontsize=16,
        fontweight="bold",
        pad=18,
    )
    ax.text(
        0,
        1.01,
        "Arrow width is proportional to total observed shipment volume",
        transform=ax.transAxes,
        fontsize=10,
        color="#52616B",
        va="bottom",
    )
    ax.set_xlim(-0.45, 3.45)
    ax.set_ylim(0.02, 1.05)
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def main() -> None:
    """Generate all chapter artifacts deterministically."""
    RESULTS.mkdir(parents=True, exist_ok=True)
    FIGURES.mkdir(parents=True, exist_ok=True)

    graph = build_graph()
    node_summary = analyse_nodes(graph)
    stage_flow = aggregate_stage_flows(graph)

    network_path = FIGURES / "12-network-communities.png"
    flow_path = FIGURES / "12-stage-flow.png"
    draw_network(graph, node_summary, network_path)
    draw_stage_flow(stage_flow, flow_path)

    node_summary.to_csv(RESULTS / "12-network-node-summary.csv", index=False)
    stage_flow.to_csv(RESULTS / "12-stage-flow-summary.csv", index=False)
    pd.DataFrame(
        [
            {
                "figure": str(network_path.relative_to(ROOT)),
                "purpose": "Layered node-link network with communities and centrality",
            },
            {
                "figure": str(flow_path.relative_to(ROOT)),
                "purpose": "Static stage-level flow view",
            },
        ]
    ).to_csv(RESULTS / "12-network-figure-manifest.csv", index=False)

    print(f"Generated {network_path.relative_to(ROOT)}")
    print(f"Generated {flow_path.relative_to(ROOT)}")
    print(f"Nodes: {graph.number_of_nodes()} | Edges: {graph.number_of_edges()}")


if __name__ == "__main__":
    main()
