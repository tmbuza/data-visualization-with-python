"""Build and query the deterministic retail database for Chapter 06."""

from __future__ import annotations

import csv
import json
import sqlite3
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
CUSTOMERS_PATH = ROOT / "data/raw/06-customers.csv"
ORDERS_PATH = ROOT / "data/raw/06-orders.csv"
DATABASE_PATH = ROOT / "data/processed/06-retail.db"
SCHEMA_PATH = ROOT / "queries/06-create-retail-schema.sql"
QUERY_PATH = ROOT / "queries/06-segment-revenue.sql"
RESULT_PATH = ROOT / "results/06-segment-revenue.csv"
SUMMARY_PATH = ROOT / "results/06-sql-python-summary.json"
FIGURE_PATH = ROOT / "results/figures/06-segment-revenue.png"
START_DATE = "2026-01-01"
END_DATE = "2026-04-01"


def read_csv_records(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as source:
        return list(csv.DictReader(source))


def load_segment_revenue(connection: sqlite3.Connection) -> pd.DataFrame:
    return pd.read_sql_query(
        QUERY_PATH.read_text(encoding="utf-8"), connection,
        params={"start_date": START_DATE, "end_date": END_DATE},
    )


def validate(summary: pd.DataFrame, control_total: float) -> float:
    required = {"segment", "completed_orders", "revenue", "average_order_value"}
    missing = required.difference(summary.columns)
    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")
    if summary.empty:
        raise ValueError("The reporting query returned no rows")
    if summary["segment"].duplicated().any():
        raise ValueError("Each segment must occur once")
    numeric = summary[["completed_orders", "revenue", "average_order_value"]]
    if numeric.lt(0).any().any():
        raise ValueError("Counts and monetary values cannot be negative")
    reported_total = round(float(summary["revenue"].sum()), 2)
    if reported_total != round(float(control_total), 2):
        raise ValueError("Segment totals do not reconcile")
    return reported_total


def create_plot(summary: pd.DataFrame) -> None:
    plot_data = summary.sort_values("revenue")
    colors = {"Consumer": "#2A9D8F", "Corporate": "#264653", "Home Office": "#E9C46A"}
    fig, ax = plt.subplots(figsize=(9, 5.4))
    bars = ax.barh(plot_data["segment"], plot_data["revenue"],
                   color=[colors[value] for value in plot_data["segment"]])
    for bar, (_, row) in zip(bars, plot_data.iterrows()):
        ax.text(bar.get_width() + 22, bar.get_y() + bar.get_height() / 2,
                f"${row['revenue']:,.2f}  |  {int(row['completed_orders'])} orders",
                va="center", fontsize=10)
    ax.set_title("Completed-order revenue by customer segment", loc="left", weight="bold")
    ax.set_xlabel("Revenue (USD)")
    ax.set_ylabel("")
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.grid(axis="x", alpha=0.2)
    ax.set_axisbelow(True)
    ax.set_xlim(0, plot_data["revenue"].max() * 1.35)
    fig.tight_layout()
    fig.savefig(FIGURE_PATH, dpi=180, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
    FIGURE_PATH.parent.mkdir(parents=True, exist_ok=True)
    DATABASE_PATH.unlink(missing_ok=True)
    customers = read_csv_records(CUSTOMERS_PATH)
    orders = read_csv_records(ORDERS_PATH)

    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        with connection:
            connection.executemany(
                "INSERT INTO customers VALUES (:customer_id, :customer_name, :segment)", customers)
            connection.executemany(
                "INSERT INTO orders VALUES (:order_id, :customer_id, :order_date, :status, :order_total)",
                orders)
        summary = load_segment_revenue(connection)
        control_total = connection.execute(
            """SELECT ROUND(SUM(order_total), 2) FROM orders
               WHERE status = 'completed' AND order_date >= ? AND order_date < ?""",
            (START_DATE, END_DATE)).fetchone()[0]
        customer_count = connection.execute("SELECT COUNT(*) FROM customers").fetchone()[0]
        order_count = connection.execute("SELECT COUNT(*) FROM orders").fetchone()[0]

    reported_total = validate(summary, control_total)
    summary.to_csv(RESULT_PATH, index=False)
    create_plot(summary)
    metadata = {
        "chapter": "DVP-06",
        "reporting_window": {"start_inclusive": START_DATE, "end_exclusive": END_DATE},
        "source_rows": {"customers": customer_count, "orders": order_count},
        "result_rows": int(len(summary)),
        "completed_orders": int(summary["completed_orders"].sum()),
        "reported_revenue": reported_total,
        "control_revenue": round(float(control_total), 2),
        "reconciled": True,
    }
    SUMMARY_PATH.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(summary.to_string(index=False))
    print(f"\nReconciled revenue: ${reported_total:,.2f}")


if __name__ == "__main__":
    main()
