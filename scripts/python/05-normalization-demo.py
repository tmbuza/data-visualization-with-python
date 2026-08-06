"""Demonstrate normalization, constraint enforcement, and reconstruction."""

from __future__ import annotations

import argparse
import csv
import sqlite3
from pathlib import Path

import matplotlib.pyplot as plt


CUSTOMERS = [
    (1, "Amina Said", "amina@example.org"),
    (2, "Baraka Mushi", "baraka@example.org"),
    (3, "Neema John", "neema@example.org"),
]
PRODUCTS = [
    (101, "Field notebook", 8.50),
    (102, "USB drive", 14.00),
    (103, "Desk lamp", 22.00),
    (104, "Cable organizer", 6.50),
]
ORDERS = [
    (1001, "2026-07-01", 1),
    (1002, "2026-07-02", 2),
    (1003, "2026-07-03", 1),
    (1004, "2026-07-05", 3),
]
ORDER_ITEMS = [
    (1001, 101, 2, 8.00),
    (1001, 102, 1, 13.50),
    (1002, 103, 1, 21.00),
    (1002, 104, 3, 6.00),
    (1003, 102, 2, 14.00),
    (1003, 104, 1, 6.50),
    (1004, 101, 4, 8.50),
    (1004, 103, 1, 22.00),
]


def create_database(schema_path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.execute("PRAGMA foreign_keys = ON")
    connection.executescript(schema_path.read_text(encoding="utf-8"))
    connection.executemany("INSERT INTO customers VALUES (?, ?, ?)", CUSTOMERS)
    connection.executemany("INSERT INTO products VALUES (?, ?, ?)", PRODUCTS)
    connection.executemany("INSERT INTO orders VALUES (?, ?, ?)", ORDERS)
    connection.executemany("INSERT INTO order_items VALUES (?, ?, ?, ?)", ORDER_ITEMS)
    connection.commit()
    return connection


def wide_rows(connection: sqlite3.Connection) -> list[tuple]:
    query = """
        SELECT o.order_id, o.order_date, c.customer_id, c.customer_name, c.email,
               p.product_id, p.product_name, oi.quantity, oi.unit_price
        FROM orders AS o
        JOIN customers AS c ON c.customer_id = o.customer_id
        JOIN order_items AS oi ON oi.order_id = o.order_id
        JOIN products AS p ON p.product_id = oi.product_id
        ORDER BY o.order_id, p.product_id
    """
    return connection.execute(query).fetchall()


def repeated_values(rows: list[tuple], indexes: tuple[int, ...]) -> int:
    stored = sum(len({row[index] for index in indexes}) for row in rows)
    unique = sum(len({row[index] for row in rows}) for index in indexes)
    return stored - unique


def constraint_is_enforced(connection: sqlite3.Connection, statement: str, values: tuple) -> bool:
    savepoint = "constraint_check"
    connection.execute(f"SAVEPOINT {savepoint}")
    try:
        connection.execute(statement, values)
    except sqlite3.IntegrityError:
        connection.execute(f"ROLLBACK TO {savepoint}")
        connection.execute(f"RELEASE {savepoint}")
        return True
    connection.execute(f"ROLLBACK TO {savepoint}")
    connection.execute(f"RELEASE {savepoint}")
    return False


def write_summary(path: Path, metrics: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["metric", "wide_design", "normalized_design", "interpretation"])
        writer.writeheader()
        writer.writerows(metrics)


def draw_plot(path: Path, customer_repeats: int, product_repeats: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    labels = ["Customer values", "Product values"]
    wide = [customer_repeats, product_repeats]
    normalized = [0, 0]
    positions = range(len(labels))
    width = 0.34

    fig, axis = plt.subplots(figsize=(8.5, 5.2))
    axis.bar([p - width / 2 for p in positions], wide, width, label="Wide table", color="#d97706")
    axis.bar([p + width / 2 for p in positions], normalized, width, label="Normalized tables", color="#2563eb")
    for position, value in zip(positions, wide):
        axis.text(position - width / 2, value + 0.12, str(value), ha="center", fontweight="bold")
    for position in positions:
        axis.text(position + width / 2, 0.12, "0", ha="center", fontweight="bold", color="#2563eb")
    axis.set_xticks(list(positions), labels)
    axis.set_ylabel("Repeated descriptive values")
    axis.set_title("Normalization gives each descriptive fact one home")
    axis.set_ylim(0, max(wide) + 1.5)
    axis.spines[["top", "right"]].set_visible(False)
    axis.grid(axis="y", alpha=0.2)
    axis.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--schema", type=Path, default=Path("scripts/sql/05-normalized-order-schema.sql"))
    parser.add_argument("--summary", type=Path, default=Path("results/05-normalization-summary.csv"))
    parser.add_argument("--figure", type=Path, default=Path("results/figures/05-normalization-comparison.png"))
    args = parser.parse_args()

    connection = create_database(args.schema)
    rows = wide_rows(connection)
    customer_repeats = repeated_values(rows, (2, 3, 4))
    product_repeats = repeated_values(rows, (5, 6))
    reconstructed_total = sum(row[7] * row[8] for row in rows)
    source_total = sum(quantity * price for _, _, quantity, price in ORDER_ITEMS)

    checks = {
        "orphan_order_item_rejected": constraint_is_enforced(
            connection, "INSERT INTO order_items VALUES (?, ?, ?, ?)", (9999, 101, 1, 8.5)
        ),
        "zero_quantity_rejected": constraint_is_enforced(
            connection, "INSERT INTO order_items VALUES (?, ?, ?, ?)", (1001, 103, 0, 22.0)
        ),
        "duplicate_email_rejected": constraint_is_enforced(
            connection, "INSERT INTO customers VALUES (?, ?, ?)", (4, "Duplicate", "amina@example.org")
        ),
        "negative_price_rejected": constraint_is_enforced(
            connection, "INSERT INTO products VALUES (?, ?, ?)", (105, "Invalid", -1.0)
        ),
    }
    if not all(checks.values()):
        raise RuntimeError(f"Constraint validation failed: {checks}")
    if abs(reconstructed_total - source_total) > 1e-9:
        raise RuntimeError("The normalized join did not reproduce the source total")

    metrics = [
        {"metric": "customer_descriptive_repetitions", "wide_design": customer_repeats, "normalized_design": 0, "interpretation": "Customer facts are stored once per customer"},
        {"metric": "product_descriptive_repetitions", "wide_design": product_repeats, "normalized_design": 0, "interpretation": "Product facts are stored once per product"},
        {"metric": "order_line_rows", "wide_design": len(rows), "normalized_design": len(ORDER_ITEMS), "interpretation": "Normalization preserves order-line facts"},
        {"metric": "reconstructed_order_total", "wide_design": f"{source_total:.2f}", "normalized_design": f"{reconstructed_total:.2f}", "interpretation": "Joins reproduce the same analytical total"},
        {"metric": "integrity_checks_passed", "wide_design": "not_enforced", "normalized_design": sum(checks.values()), "interpretation": "Four invalid writes are rejected"},
    ]
    write_summary(args.summary, metrics)
    draw_plot(args.figure, customer_repeats, product_repeats)
    print(f"Wrote {args.summary}")
    print(f"Wrote {args.figure}")
    print(f"All {len(checks)} integrity checks passed; reconstructed total = {reconstructed_total:.2f}")


if __name__ == "__main__":
    main()

