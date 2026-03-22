"""Seed script: creates kpi.db with realistic sample data."""

import sqlite3
import random
from datetime import date, timedelta

DB_PATH = "db/kpi.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS sales (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    date        DATE NOT NULL,
    region      TEXT NOT NULL,
    product     TEXT NOT NULL,
    revenue     REAL NOT NULL,
    units_sold  INTEGER NOT NULL,
    target      REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS operations (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    date             DATE NOT NULL,
    department       TEXT NOT NULL,
    tickets_resolved INTEGER NOT NULL,
    avg_handle_time  REAL NOT NULL,
    sla_breached     INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS finance (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    month       TEXT NOT NULL,
    category    TEXT NOT NULL,
    budget      REAL NOT NULL,
    actual      REAL NOT NULL
);
"""

REGIONS   = ["North", "South", "East", "West"]
PRODUCTS  = ["Product A", "Product B", "Product C", "Product D"]
DEPTS     = ["Support", "Engineering", "Sales", "Finance"]
FIN_CATS  = ["Marketing", "R&D", "Operations", "HR", "IT"]


def random_date_range(start: date, days: int):
    return [start + timedelta(d) for d in range(days)]


def seed(conn: sqlite3.Connection):
    cur = conn.cursor()
    cur.executescript(SCHEMA)

    # ── Sales ──────────────────────────────────────────────────────────────
    sales_rows = []
    for d in random_date_range(date(2024, 1, 1), 365):
        for region in REGIONS:
            for product in PRODUCTS:
                revenue    = round(random.uniform(5_000, 50_000), 2)
                units      = random.randint(10, 500)
                target     = round(revenue * random.uniform(0.8, 1.3), 2)
                sales_rows.append((str(d), region, product, revenue, units, target))

    cur.executemany(
        "INSERT INTO sales (date, region, product, revenue, units_sold, target) VALUES (?,?,?,?,?,?)",
        sales_rows,
    )

    # ── Operations ─────────────────────────────────────────────────────────
    ops_rows = []
    for d in random_date_range(date(2024, 1, 1), 365):
        for dept in DEPTS:
            resolved   = random.randint(20, 200)
            handle_t   = round(random.uniform(2.0, 15.0), 2)
            sla        = random.randint(0, max(1, resolved // 10))
            ops_rows.append((str(d), dept, resolved, handle_t, sla))

    cur.executemany(
        "INSERT INTO operations (date, department, tickets_resolved, avg_handle_time, sla_breached) VALUES (?,?,?,?,?)",
        ops_rows,
    )

    # ── Finance ────────────────────────────────────────────────────────────
    fin_rows = []
    for month_num in range(1, 13):
        month_str = date(2024, month_num, 1).strftime("%Y-%m")
        for cat in FIN_CATS:
            budget = round(random.uniform(50_000, 200_000), 2)
            actual = round(budget * random.uniform(0.7, 1.2), 2)
            fin_rows.append((month_str, cat, budget, actual))

    cur.executemany(
        "INSERT INTO finance (month, category, budget, actual) VALUES (?,?,?,?)",
        fin_rows,
    )

    conn.commit()
    print(f"Seeded {len(sales_rows)} sales rows, {len(ops_rows)} ops rows, {len(fin_rows)} finance rows.")


if __name__ == "__main__":
    import os
    os.makedirs("db", exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        seed(conn)
