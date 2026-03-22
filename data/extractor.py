"""SQL extraction layer – all raw queries live here."""

import sqlite3
import pandas as pd
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "db" / "kpi.db"


def _conn() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH)


# ── Sales ──────────────────────────────────────────────────────────────────

def get_monthly_revenue() -> pd.DataFrame:
    sql = """
    SELECT
        strftime('%Y-%m', date)        AS month,
        region,
        SUM(revenue)                   AS revenue,
        SUM(target)                    AS target,
        SUM(units_sold)                AS units_sold
    FROM sales
    GROUP BY month, region
    ORDER BY month, region
    """
    with _conn() as c:
        return pd.read_sql_query(sql, c)


def get_product_revenue() -> pd.DataFrame:
    sql = """
    SELECT
        product,
        region,
        SUM(revenue)  AS revenue,
        SUM(target)   AS target
    FROM sales
    GROUP BY product, region
    ORDER BY revenue DESC
    """
    with _conn() as c:
        return pd.read_sql_query(sql, c)


def get_daily_revenue_trend() -> pd.DataFrame:
    sql = """
    SELECT
        date,
        SUM(revenue)    AS revenue,
        SUM(target)     AS target
    FROM sales
    GROUP BY date
    ORDER BY date
    """
    with _conn() as c:
        return pd.read_sql_query(sql, c)


# ── Operations ─────────────────────────────────────────────────────────────

def get_monthly_ops() -> pd.DataFrame:
    sql = """
    SELECT
        strftime('%Y-%m', date)            AS month,
        department,
        SUM(tickets_resolved)              AS tickets_resolved,
        AVG(avg_handle_time)               AS avg_handle_time,
        SUM(sla_breached)                  AS sla_breached
    FROM operations
    GROUP BY month, department
    ORDER BY month, department
    """
    with _conn() as c:
        return pd.read_sql_query(sql, c)


def get_sla_summary() -> pd.DataFrame:
    sql = """
    SELECT
        department,
        SUM(tickets_resolved)                              AS total_tickets,
        SUM(sla_breached)                                  AS total_breached,
        ROUND(100.0 * SUM(sla_breached)
              / NULLIF(SUM(tickets_resolved), 0), 2)       AS breach_pct
    FROM operations
    GROUP BY department
    ORDER BY breach_pct DESC
    """
    with _conn() as c:
        return pd.read_sql_query(sql, c)


# ── Finance ────────────────────────────────────────────────────────────────

def get_budget_vs_actual() -> pd.DataFrame:
    sql = """
    SELECT
        month,
        category,
        SUM(budget)                                   AS budget,
        SUM(actual)                                   AS actual,
        ROUND(100.0 * (SUM(actual) - SUM(budget))
              / NULLIF(SUM(budget), 0), 2)            AS variance_pct
    FROM finance
    GROUP BY month, category
    ORDER BY month, category
    """
    with _conn() as c:
        return pd.read_sql_query(sql, c)
