#!/usr/bin/env python3
"""Create and validate the Chapter 04 relational-join example."""

from __future__ import annotations

import csv
import sqlite3
from pathlib import Path

import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[2]
TABLE_DIR = ROOT / "results" / "tables"
FIGURE_DIR = ROOT / "results" / "figures"


def write_csv(path: Path, rows: list[sqlite3.Row]) -> None:
    """Write SQLite rows to CSV while preserving query column order."""
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(rows[0].keys())
        writer.writerows(tuple(row) for row in rows)


def main() -> None:
    TABLE_DIR.mkdir(parents=True, exist_ok=True)
    FIGURE_DIR.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.executescript(
        """
        PRAGMA foreign_keys = OFF;
        CREATE TABLE customers (
            customer_id INTEGER PRIMARY KEY,
            customer_name TEXT NOT NULL,
            region TEXT NOT NULL
        );
        CREATE TABLE orders (
            order_id INTEGER PRIMARY KEY,
            customer_id INTEGER,
            order_date TEXT NOT NULL,
            status TEXT NOT NULL
        );
        CREATE TABLE products (
            product_id INTEGER PRIMARY KEY,
            product_name TEXT NOT NULL
        );
        CREATE TABLE order_items (
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            PRIMARY KEY (order_id, product_id)
        );

        INSERT INTO customers VALUES
            (1, 'Asha', 'East'), (2, 'Baraka', 'North'),
            (3, 'Chausiku', 'South'), (4, 'Daudi', 'West'),
            (5, 'Elina', 'East');
        INSERT INTO orders VALUES
            (101, 1, '2026-07-01', 'completed'),
            (102, 1, '2026-07-04', 'cancelled'),
            (103, 2, '2026-07-07', 'completed'),
            (104, 3, '2026-07-09', 'completed'),
            (105, 3, '2026-07-12', 'completed'),
            (106, 4, '2026-07-15', 'completed'),
            (107, 999, '2026-07-18', 'completed');
        INSERT INTO products VALUES
            (10, 'Notebook'), (20, 'Pen'), (30, 'Backpack'), (40, 'Bottle');
        INSERT INTO order_items VALUES
            (101, 10, 2, 4.50), (101, 20, 3, 1.50),
            (102, 30, 1, 28.00), (103, 30, 1, 28.00),
            (103, 40, 2, 8.00), (104, 10, 4, 4.50),
            (105, 20, 10, 1.50), (106, 40, 1, 8.00),
            (107, 10, 1, 4.50);
        """
    )

    customer_summary = connection.execute(
        """
        WITH order_totals AS (
            SELECT o.order_id, o.customer_id,
                   SUM(oi.quantity * oi.unit_price) AS order_revenue
            FROM orders AS o
            JOIN order_items AS oi ON o.order_id = oi.order_id
            WHERE o.status = 'completed'
            GROUP BY o.order_id, o.customer_id
        )
        SELECT c.customer_id, c.customer_name, c.region,
               COUNT(ot.order_id) AS completed_orders,
               ROUND(COALESCE(SUM(ot.order_revenue), 0), 2) AS revenue
        FROM customers AS c
        LEFT JOIN order_totals AS ot ON c.customer_id = ot.customer_id
        GROUP BY c.customer_id, c.customer_name, c.region
        ORDER BY revenue DESC, c.customer_id
        """
    ).fetchall()
    unmatched_orders = connection.execute(
        """
        SELECT o.order_id, o.customer_id, o.order_date, o.status
        FROM orders AS o
        WHERE NOT EXISTS (
            SELECT 1 FROM customers AS c
            WHERE c.customer_id = o.customer_id
        )
        ORDER BY o.order_id
        """
    ).fetchall()
    write_csv(TABLE_DIR / "04-customer-join-summary.csv", customer_summary)
    write_csv(TABLE_DIR / "04-unmatched-orders.csv", unmatched_orders)

    counts = {
        "Customers": connection.execute("SELECT COUNT(*) FROM customers").fetchone()[0],
        "Orders": connection.execute("SELECT COUNT(*) FROM orders").fetchone()[0],
        "Inner join": connection.execute(
            "SELECT COUNT(*) FROM customers c JOIN orders o ON c.customer_id=o.customer_id"
        ).fetchone()[0],
        "Left join": connection.execute(
            "SELECT COUNT(*) FROM customers c LEFT JOIN orders o ON c.customer_id=o.customer_id"
        ).fetchone()[0],
    }
    assert counts == {"Customers": 5, "Orders": 7, "Inner join": 6, "Left join": 7}
    assert len(unmatched_orders) == 1
    assert sum(row["revenue"] for row in customer_summary) == 98.5

    fig, ax = plt.subplots(figsize=(8.2, 4.8))
    colors = ["#4C78A8", "#F58518", "#54A24B", "#B279A2"]
    bars = ax.bar(counts.keys(), counts.values(), color=colors, width=0.68)
    ax.bar_label(bars, padding=3, fontsize=10)
    ax.set(title="Join counts depend on preservation rules", ylabel="Rows")
    ax.set_ylim(0, max(counts.values()) + 1.6)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", alpha=0.2)
    ax.text(
        0.99, 0.96,
        "1 orphan order excluded by both joins\n1 customer without an order retained by LEFT JOIN",
        transform=ax.transAxes, ha="right", va="top", fontsize=9,
        bbox={"boxstyle": "round,pad=0.4", "facecolor": "white", "edgecolor": "#cccccc"},
    )
    fig.tight_layout()
    fig.savefig(FIGURE_DIR / "04-join-cardinality-diagnostics.png", dpi=180)
    plt.close(fig)

    print("Chapter 04 join analysis completed.")
    print(f"Counts: {counts}")
    print(f"Completed revenue for known customers: {98.5:.2f}")


if __name__ == "__main__":
    main()
