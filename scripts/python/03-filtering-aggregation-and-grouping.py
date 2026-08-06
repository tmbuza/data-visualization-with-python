#!/usr/bin/env python3
"""Create the Chapter 03 SQLite data, summaries, validation, and figure."""

from __future__ import annotations

import csv
import sqlite3
from pathlib import Path

import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[2]
DATABASE = ROOT / "data/processed/03-retail.db"
RESULTS = ROOT / "results"
FIGURES = RESULTS / "figures"

ORDERS = [
    (1001, "2026-01-03", "East", "Electronics", "Online", "Completed", 2, 640.00, 0.10),
    (1002, "2026-01-04", "North", "Furniture", "Retail", "Completed", 1, 420.00, None),
    (1003, "2026-01-06", "West", "Office Supplies", "Partner", "Returned", 4, 18.50, 0.05),
    (1004, "2026-01-08", "South", "Electronics", "Retail", "Completed", 3, 125.00, None),
    (1005, "2026-01-09", "East", "Office Supplies", "Online", "Cancelled", 5, 12.00, 0.10),
    (1006, "2026-01-11", "North", "Electronics", "Partner", "Completed", 1, 890.00, 0.15),
    (1007, "2026-01-13", "West", "Furniture", "Online", "Completed", 2, 275.00, 0.05),
    (1008, "2026-01-15", "South", "Office Supplies", "Retail", "Completed", 6, 9.50, None),
    (1009, "2026-01-17", "East", "Furniture", "Partner", "Returned", 1, 510.00, 0.10),
    (1010, "2026-01-20", "North", "Office Supplies", "Online", "Completed", 10, 7.25, 0.05),
    (1011, "2026-01-23", "West", "Electronics", "Retail", "Cancelled", 2, 330.00, None),
    (1012, "2026-01-26", "South", "Furniture", "Partner", "Completed", 1, 760.00, 0.20),
    (1013, "2026-02-02", "East", "Office Supplies", "Retail", "Completed", 8, 14.00, None),
    (1014, "2026-02-05", "North", "Furniture", "Online", "Returned", 1, 305.00, 0.05),
    (1015, "2026-02-08", "West", "Electronics", "Partner", "Completed", 2, 455.00, 0.10),
    (1016, "2026-02-12", "South", "Office Supplies", "Online", "Cancelled", 3, 22.00, None),
    (1017, "2026-02-16", "East", "Furniture", "Retail", "Completed", 2, 340.00, 0.05),
    (1018, "2026-02-20", "North", "Electronics", "Online", "Completed", 4, 210.00, None),
    (1019, "2026-02-24", "West", "Office Supplies", "Retail", "Returned", 7, 11.00, 0.10),
    (1020, "2026-02-27", "South", "Furniture", "Online", "Completed", 1, 585.00, None),
]

CATEGORY_SQL = """
SELECT category,
       COUNT(*) AS completed_order_lines,
       SUM(quantity) AS units_sold,
       ROUND(SUM(quantity * unit_price * (1 - COALESCE(discount_rate, 0))), 2)
           AS net_revenue
FROM orders
WHERE status = 'Completed'
GROUP BY category
ORDER BY net_revenue DESC;
"""

REGION_SQL = """
SELECT region,
       COUNT(*) AS all_order_lines,
       SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) AS completed_lines,
       SUM(CASE WHEN status = 'Returned' THEN 1 ELSE 0 END) AS returned_lines,
       SUM(CASE WHEN status = 'Cancelled' THEN 1 ELSE 0 END) AS cancelled_lines,
       ROUND(100.0 * SUM(CASE WHEN status = 'Returned' THEN 1 ELSE 0 END)
             / COUNT(*), 1) AS return_rate_percent
FROM orders
GROUP BY region
ORDER BY region;
"""


def write_csv(path: Path, columns: list[str], rows: list[sqlite3.Row]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(columns)
        writer.writerows([tuple(row) for row in rows])


def main() -> None:
    DATABASE.parent.mkdir(parents=True, exist_ok=True)
    FIGURES.mkdir(parents=True, exist_ok=True)
    DATABASE.unlink(missing_ok=True)

    with sqlite3.connect(DATABASE) as connection:
        connection.row_factory = sqlite3.Row
        connection.execute("""
            CREATE TABLE orders (
                order_id INTEGER PRIMARY KEY,
                order_date TEXT NOT NULL,
                region TEXT NOT NULL,
                category TEXT NOT NULL,
                sales_channel TEXT NOT NULL,
                status TEXT NOT NULL,
                quantity INTEGER NOT NULL CHECK (quantity > 0),
                unit_price REAL NOT NULL CHECK (unit_price >= 0),
                discount_rate REAL
            );
        """)
        connection.executemany("INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", ORDERS)
        category_rows = connection.execute(CATEGORY_SQL).fetchall()
        region_rows = connection.execute(REGION_SQL).fetchall()

        total_count, total_revenue = connection.execute("""
            SELECT COUNT(*),
                   SUM(quantity * unit_price * (1 - COALESCE(discount_rate, 0)))
            FROM orders WHERE status = 'Completed';
        """).fetchone()
        grouped_count = sum(row["completed_order_lines"] for row in category_rows)
        grouped_revenue = sum(row["net_revenue"] for row in category_rows)
        partitions_valid = all(
            row["all_order_lines"]
            == row["completed_lines"] + row["returned_lines"] + row["cancelled_lines"]
            for row in region_rows
        )

    assert grouped_count == total_count
    assert abs(grouped_revenue - total_revenue) < 0.01
    assert partitions_valid

    write_csv(RESULTS / "03-category-summary.csv", list(category_rows[0].keys()), category_rows)
    write_csv(RESULTS / "03-region-status-summary.csv", list(region_rows[0].keys()), region_rows)

    validation = (
        "Chapter 03 aggregation validation\n"
        f"completed rows (ungrouped): {total_count}\n"
        f"completed rows (grouped sum): {grouped_count}\n"
        f"completed net revenue (ungrouped): {total_revenue:.2f}\n"
        f"completed net revenue (grouped sum): {grouped_revenue:.2f}\n"
        f"category count reconciliation: PASS\n"
        f"category revenue reconciliation: PASS\n"
        f"regional status partitions: PASS\n"
    )
    (RESULTS / "03-validation-summary.txt").write_text(validation, encoding="utf-8")

    categories = [row["category"] for row in reversed(category_rows)]
    revenues = [row["net_revenue"] for row in reversed(category_rows)]
    fig, ax = plt.subplots(figsize=(9, 5.4))
    bars = ax.barh(categories, revenues, color=["#3A7CA5", "#2F6690", "#16425B"])
    ax.bar_label(bars, labels=[f"${value:,.0f}" for value in revenues], padding=5)
    ax.set_title("Completed net revenue by category")
    ax.set_xlabel("Net revenue (USD)")
    ax.set_ylabel("")
    ax.spines[["top", "right", "left"]].set_visible(False)
    ax.grid(axis="x", alpha=0.25)
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(FIGURES / "03-net-revenue-by-category.png", dpi=200, bbox_inches="tight")
    plt.close(fig)

    print(validation, end="")
    print(f"Created {DATABASE.relative_to(ROOT)} and Chapter 03 result files.")


if __name__ == "__main__":
    main()
