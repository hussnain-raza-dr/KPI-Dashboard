"""Automated data-quality checks run before each dashboard refresh."""

import pandas as pd
from dataclasses import dataclass, field
from typing import List


@dataclass
class QualityResult:
    passed: bool
    checks: List[dict] = field(default_factory=list)

    def summary(self) -> str:
        total  = len(self.checks)
        failed = sum(1 for c in self.checks if not c["passed"])
        return f"{total - failed}/{total} checks passed" + (f" — {failed} FAILED" if failed else " ✓")


def _check(results: list, name: str, condition: bool, detail: str = ""):
    results.append({"check": name, "passed": condition, "detail": detail})


def run_quality_checks(
    sales_df: pd.DataFrame,
    ops_df: pd.DataFrame,
    finance_df: pd.DataFrame,
) -> QualityResult:
    checks: List[dict] = []

    # ── Null checks ────────────────────────────────────────────────────────
    for df, label, cols in [
        (sales_df,   "sales",   ["revenue", "units_sold", "target"]),
        (ops_df,     "ops",     ["tickets_resolved", "avg_handle_time"]),
        (finance_df, "finance", ["budget", "actual"]),
    ]:
        null_count = df[cols].isnull().sum().sum()
        _check(checks, f"{label}: no nulls in key columns",
               null_count == 0, f"{null_count} nulls found")

    # ── Range / sanity checks ──────────────────────────────────────────────
    _check(checks, "sales: revenue >= 0",
           (sales_df["revenue"] >= 0).all(),
           f"negatives: {(sales_df['revenue'] < 0).sum()}")

    _check(checks, "sales: target >= 0",
           (sales_df["target"] >= 0).all())

    _check(checks, "ops: avg_handle_time > 0",
           (ops_df["avg_handle_time"] > 0).all())

    _check(checks, "ops: sla_breached <= tickets_resolved",
           (ops_df["sla_breached"] <= ops_df["tickets_resolved"]).all())

    _check(checks, "finance: budget > 0",
           (finance_df["budget"] > 0).all())

    # ── Completeness ──────────────────────────────────────────────────────
    _check(checks, "sales: at least 12 month-region rows",
           len(sales_df) >= 12, f"rows={len(sales_df)}")

    _check(checks, "finance: 12 months present",
           finance_df["month"].nunique() == 12,
           f"months={finance_df['month'].nunique()}")

    # ── Duplicate check ───────────────────────────────────────────────────
    dup_sales = sales_df.duplicated(subset=["month", "region"]).sum() if "month" in sales_df else 0
    _check(checks, "sales: no duplicate month+region rows",
           dup_sales == 0, f"dupes={dup_sales}")

    passed = all(c["passed"] for c in checks)
    return QualityResult(passed=passed, checks=checks)
