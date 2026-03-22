"""Transformation layer – enriches raw extracts with derived KPIs."""

import pandas as pd
import numpy as np
from data.extractor import (
    get_monthly_revenue,
    get_product_revenue,
    get_daily_revenue_trend,
    get_monthly_ops,
    get_sla_summary,
    get_budget_vs_actual,
)


def revenue_with_attainment() -> pd.DataFrame:
    df = get_monthly_revenue()
    df["attainment_pct"] = np.where(
        df["target"] > 0,
        (df["revenue"] / df["target"] * 100).round(1),
        np.nan,
    )
    df["above_target"] = df["attainment_pct"] >= 100
    return df


def product_share() -> pd.DataFrame:
    df = get_product_revenue()
    total = df["revenue"].sum()
    df["share_pct"] = (df["revenue"] / total * 100).round(2)
    return df


def daily_trend_with_ma() -> pd.DataFrame:
    df = get_daily_revenue_trend()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date")
    df["revenue_ma7"]  = df["revenue"].rolling(7,  min_periods=1).mean().round(2)
    df["revenue_ma30"] = df["revenue"].rolling(30, min_periods=1).mean().round(2)
    return df


def ops_with_efficiency() -> pd.DataFrame:
    df = get_monthly_ops()
    # tickets-per-hour proxy
    df["efficiency"] = (df["tickets_resolved"] / df["avg_handle_time"]).round(2)
    return df


def sla_summary() -> pd.DataFrame:
    return get_sla_summary()


def budget_variance() -> pd.DataFrame:
    df = get_budget_vs_actual()
    df["status"] = df["variance_pct"].apply(
        lambda v: "Over Budget" if v > 5 else ("Under Budget" if v < -5 else "On Track")
    )
    return df
