"""KPI Dashboard – main Dash application entry point."""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import dash
from dash import dcc, html, Input, Output, dash_table
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd

from data.transformer import (
    revenue_with_attainment,
    product_share,
    daily_trend_with_ma,
    ops_with_efficiency,
    sla_summary,
    budget_variance,
)
from data.quality import run_quality_checks
from data.extractor import get_monthly_revenue, get_monthly_ops, get_budget_vs_actual

# ── Colour palette ─────────────────────────────────────────────────────────
PRIMARY   = "#2563EB"
SUCCESS   = "#16A34A"
WARNING   = "#D97706"
DANGER    = "#DC2626"
BG_CARD   = "#1E293B"
BG_PAGE   = "#0F172A"
TEXT_MAIN = "#F1F5F9"
TEXT_MUTED= "#94A3B8"
BORDER    = "#334155"

REGION_COLOURS = px.colors.qualitative.Plotly

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.SLATE],
    suppress_callback_exceptions=True,
    title="KPI Dashboard",
)

# ══════════════════════════════════════════════════════════════════════════════
# Helper builders
# ══════════════════════════════════════════════════════════════════════════════

def kpi_card(title: str, value: str, delta: str, colour: str, icon: str) -> dbc.Card:
    return dbc.Card(
        dbc.CardBody([
            html.Div([
                html.Span(icon, className="me-2", style={"fontSize": "1.4rem"}),
                html.Span(title, style={"color": TEXT_MUTED, "fontSize": "0.85rem", "fontWeight": "600",
                                        "textTransform": "uppercase", "letterSpacing": "0.05em"}),
            ], className="d-flex align-items-center mb-2"),
            html.H3(value, style={"color": TEXT_MAIN, "fontWeight": "700", "margin": "0"}),
            html.Small(delta, style={"color": colour}),
        ]),
        style={"background": BG_CARD, "border": f"1px solid {BORDER}", "borderTop": f"3px solid {colour}"},
        className="shadow-sm",
    )


def section_title(text: str) -> html.Div:
    return html.Div([
        html.H5(text, style={"color": TEXT_MAIN, "fontWeight": "600", "marginBottom": "0"}),
        html.Hr(style={"borderColor": BORDER, "marginTop": "6px"}),
    ], className="mb-3")


CHART_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color=TEXT_MUTED, size=12),
    margin=dict(l=40, r=20, t=30, b=40),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=TEXT_MUTED)),
    xaxis=dict(gridcolor=BORDER, linecolor=BORDER),
    yaxis=dict(gridcolor=BORDER, linecolor=BORDER),
)


# ══════════════════════════════════════════════════════════════════════════════
# Layout
# ══════════════════════════════════════════════════════════════════════════════

def build_layout():
    regions = get_monthly_revenue()["region"].unique().tolist()
    months  = sorted(get_monthly_revenue()["month"].unique().tolist())

    return dbc.Container(fluid=True, style={"background": BG_PAGE, "minHeight": "100vh", "padding": "20px"},
        children=[
            # ── Header ───────────────────────────────────────────────────
            dbc.Row(dbc.Col(html.Div([
                html.H2("KPI Dashboard", style={"color": TEXT_MAIN, "fontWeight": "700", "marginBottom": "0"}),
                html.P("Operational & Financial Performance · FY 2024",
                       style={"color": TEXT_MUTED, "marginBottom": "0"}),
            ]), width=12), className="mb-4"),

            # ── Filters ───────────────────────────────────────────────────
            dbc.Row([
                dbc.Col([
                    html.Label("Region", style={"color": TEXT_MUTED, "fontSize": "0.8rem"}),
                    dcc.Dropdown(
                        id="filter-region",
                        options=[{"label": "All Regions", "value": "ALL"}] +
                                [{"label": r, "value": r} for r in sorted(regions)],
                        value="ALL",
                        clearable=False,
                        style={"background": BG_CARD},
                    ),
                ], md=3),
                dbc.Col([
                    html.Label("Month Range", style={"color": TEXT_MUTED, "fontSize": "0.8rem"}),
                    dcc.RangeSlider(
                        id="filter-month",
                        min=0, max=len(months)-1,
                        value=[0, len(months)-1],
                        marks={i: {"label": m, "style": {"color": TEXT_MUTED, "fontSize": "10px"}}
                               for i, m in enumerate(months) if i % 2 == 0},
                        tooltip={"placement": "bottom"},
                    ),
                ], md=7),
                dbc.Col([
                    html.Br(),
                    dbc.Button("Refresh Data", id="btn-refresh", color="primary", size="sm",
                               className="mt-1"),
                ], md=2),
            ], className="mb-4 p-3",
               style={"background": BG_CARD, "borderRadius": "8px", "border": f"1px solid {BORDER}"}),

            # ── Data Quality Banner ───────────────────────────────────────
            html.Div(id="dq-banner", className="mb-3"),

            # ── KPI Cards ────────────────────────────────────────────────
            dbc.Row(id="kpi-cards", className="mb-4 g-3"),

            # ── Tab sections ─────────────────────────────────────────────
            dbc.Tabs(id="main-tabs", active_tab="tab-sales", className="mb-3", children=[
                dbc.Tab(label="Sales",      tab_id="tab-sales"),
                dbc.Tab(label="Operations", tab_id="tab-ops"),
                dbc.Tab(label="Finance",    tab_id="tab-finance"),
            ]),
            html.Div(id="tab-content"),

            # Hidden store for months list
            dcc.Store(id="months-store", data=months),
            dcc.Store(id="refresh-store", data=0),
        ],
    )


app.layout = build_layout


# ══════════════════════════════════════════════════════════════════════════════
# Callbacks
# ══════════════════════════════════════════════════════════════════════════════

@app.callback(
    Output("refresh-store", "data"),
    Input("btn-refresh", "n_clicks"),
    prevent_initial_call=True,
)
def trigger_refresh(n):
    return n or 0


@app.callback(
    [Output("dq-banner", "children"),
     Output("kpi-cards", "children")],
    [Input("filter-region", "value"),
     Input("filter-month",  "value"),
     Input("months-store",  "data"),
     Input("refresh-store", "data")],
)
def update_top(region, month_range, months, _refresh):
    m_start = months[month_range[0]]
    m_end   = months[month_range[1]]

    sales_df   = revenue_with_attainment()
    ops_df     = ops_with_efficiency()
    finance_df = budget_variance()

    # filter
    s = sales_df[(sales_df["month"] >= m_start) & (sales_df["month"] <= m_end)]
    if region != "ALL":
        s = s[s["region"] == region]

    # ── DQ Banner ─────────────────────────────────────────────────────────
    raw_sales   = get_monthly_revenue()
    raw_ops     = get_monthly_ops()
    raw_finance = get_budget_vs_actual()
    dq = run_quality_checks(raw_sales, raw_ops, raw_finance)
    dq_colour = SUCCESS if dq.passed else DANGER
    dq_icon   = "✓" if dq.passed else "✗"
    banner = dbc.Alert(
        [html.Strong(f"Data Quality  {dq_icon}  "), dq.summary()],
        color="success" if dq.passed else "danger",
        className="py-2 mb-0",
        style={"borderRadius": "6px"},
    )

    # ── KPI Cards ─────────────────────────────────────────────────────────
    total_rev   = s["revenue"].sum()
    total_tgt   = s["target"].sum()
    attainment  = total_rev / total_tgt * 100 if total_tgt else 0
    avg_att     = s["attainment_pct"].mean()

    total_tickets = get_monthly_ops()["tickets_resolved"].sum()
    sla_df        = sla_summary()
    avg_breach    = sla_df["breach_pct"].mean()

    fin_df   = get_budget_vs_actual()
    total_var= (fin_df["actual"].sum() - fin_df["budget"].sum()) / fin_df["budget"].sum() * 100

    cards = [
        dbc.Col(kpi_card("Total Revenue",  f"${total_rev/1e6:,.1f}M",
                         f"Target attainment {attainment:.1f}%",
                         SUCCESS if attainment >= 100 else WARNING, "💰"), md=3),
        dbc.Col(kpi_card("Avg Attainment", f"{avg_att:.1f}%",
                         "vs. sales target",
                         SUCCESS if avg_att >= 100 else WARNING, "🎯"), md=3),
        dbc.Col(kpi_card("Tickets Resolved", f"{total_tickets:,}",
                         f"Avg SLA breach {avg_breach:.1f}%",
                         SUCCESS if avg_breach < 5 else DANGER, "🎫"), md=3),
        dbc.Col(kpi_card("Budget Variance",  f"{total_var:+.1f}%",
                         "Over / under budget",
                         SUCCESS if abs(total_var) <= 5 else DANGER, "📊"), md=3),
    ]
    return banner, cards


@app.callback(
    Output("tab-content", "children"),
    [Input("main-tabs",    "active_tab"),
     Input("filter-region","value"),
     Input("filter-month", "value"),
     Input("months-store", "data"),
     Input("refresh-store","data")],
)
def render_tab(tab, region, month_range, months, _):
    m_start = months[month_range[0]]
    m_end   = months[month_range[1]]

    if tab == "tab-sales":
        return render_sales(region, m_start, m_end)
    elif tab == "tab-ops":
        return render_ops(m_start, m_end)
    else:
        return render_finance(m_start, m_end)


# ── Sales tab ─────────────────────────────────────────────────────────────

def render_sales(region, m_start, m_end):
    df = revenue_with_attainment()
    df = df[(df["month"] >= m_start) & (df["month"] <= m_end)]
    if region != "ALL":
        df = df[df["region"] == region]

    prod_df = product_share()
    trend   = daily_trend_with_ma()

    # Revenue vs Target bar
    grp = df.groupby("month")[["revenue", "target"]].sum().reset_index()
    fig_bar = go.Figure()
    fig_bar.add_bar(x=grp["month"], y=grp["target"],  name="Target",  marker_color=BORDER)
    fig_bar.add_bar(x=grp["month"], y=grp["revenue"], name="Revenue", marker_color=PRIMARY)
    fig_bar.update_layout(**CHART_LAYOUT, barmode="overlay", title="Monthly Revenue vs Target")

    # Region line
    fig_line = go.Figure()
    for i, rgn in enumerate(df["region"].unique()):
        sub = df[df["region"] == rgn].groupby("month")["revenue"].sum().reset_index()
        fig_line.add_scatter(x=sub["month"], y=sub["revenue"], mode="lines+markers",
                             name=rgn, line=dict(color=REGION_COLOURS[i % len(REGION_COLOURS)], width=2))
    fig_line.update_layout(**CHART_LAYOUT, title="Revenue by Region")

    # Product treemap
    fig_tree = px.treemap(prod_df, path=["product", "region"],
                          values="revenue", color="share_pct",
                          color_continuous_scale="Blues",
                          title="Product Revenue Share")
    fig_tree.update_layout(**CHART_LAYOUT)

    # MA trend
    fig_ma = go.Figure()
    fig_ma.add_scatter(x=trend["date"], y=trend["revenue"], mode="lines",
                       name="Daily", line=dict(color=BORDER, width=1), opacity=0.5)
    fig_ma.add_scatter(x=trend["date"], y=trend["revenue_ma7"], mode="lines",
                       name="7-day MA", line=dict(color=WARNING, width=2))
    fig_ma.add_scatter(x=trend["date"], y=trend["revenue_ma30"], mode="lines",
                       name="30-day MA", line=dict(color=SUCCESS, width=2))
    fig_ma.update_layout(**CHART_LAYOUT, title="Revenue Trend with Moving Averages")

    return html.Div([
        section_title("Sales Performance"),
        dbc.Row([
            dbc.Col(dcc.Graph(figure=fig_bar,  config={"displayModeBar": False}), md=6),
            dbc.Col(dcc.Graph(figure=fig_line, config={"displayModeBar": False}), md=6),
        ], className="mb-3"),
        dbc.Row([
            dbc.Col(dcc.Graph(figure=fig_tree, config={"displayModeBar": False}), md=6),
            dbc.Col(dcc.Graph(figure=fig_ma,   config={"displayModeBar": False}), md=6),
        ]),
    ])


# ── Operations tab ────────────────────────────────────────────────────────

def render_ops(m_start, m_end):
    df  = ops_with_efficiency()
    df  = df[(df["month"] >= m_start) & (df["month"] <= m_end)]
    sla = sla_summary()

    # Tickets stacked bar
    fig_tick = go.Figure()
    for i, dept in enumerate(df["department"].unique()):
        sub = df[df["department"] == dept]
        fig_tick.add_bar(x=sub["month"], y=sub["tickets_resolved"],
                         name=dept, marker_color=REGION_COLOURS[i % len(REGION_COLOURS)])
    fig_tick.update_layout(**CHART_LAYOUT, barmode="stack", title="Tickets Resolved by Department")

    # SLA breach gauge-like bar
    fig_sla = go.Figure(go.Bar(
        x=sla["department"], y=sla["breach_pct"],
        marker_color=[DANGER if v > 10 else WARNING if v > 5 else SUCCESS for v in sla["breach_pct"]],
        text=sla["breach_pct"].apply(lambda v: f"{v:.1f}%"),
        textposition="outside",
    ))
    fig_sla.update_layout(**CHART_LAYOUT, title="SLA Breach % by Department",
                          yaxis_title="Breach %")

    # Avg handle time heatmap
    pivot = df.pivot_table(index="department", columns="month", values="avg_handle_time", aggfunc="mean")
    fig_heat = go.Figure(go.Heatmap(
        z=pivot.values, x=pivot.columns.tolist(), y=pivot.index.tolist(),
        colorscale="RdYlGn_r", text=pivot.values.round(1),
        texttemplate="%{text}", showscale=True,
    ))
    fig_heat.update_layout(**CHART_LAYOUT, title="Avg Handle Time (mins) Heatmap")

    # Efficiency line
    eff = df.groupby("month")["efficiency"].mean().reset_index()
    fig_eff = go.Figure(go.Scatter(
        x=eff["month"], y=eff["efficiency"], mode="lines+markers",
        line=dict(color=PRIMARY, width=2),
        fill="tozeroy", fillcolor="rgba(37,99,235,0.1)",
    ))
    fig_eff.update_layout(**CHART_LAYOUT, title="Avg Ticket Efficiency (tickets/hr proxy)")

    return html.Div([
        section_title("Operations Performance"),
        dbc.Row([
            dbc.Col(dcc.Graph(figure=fig_tick, config={"displayModeBar": False}), md=6),
            dbc.Col(dcc.Graph(figure=fig_sla,  config={"displayModeBar": False}), md=6),
        ], className="mb-3"),
        dbc.Row([
            dbc.Col(dcc.Graph(figure=fig_heat, config={"displayModeBar": False}), md=6),
            dbc.Col(dcc.Graph(figure=fig_eff,  config={"displayModeBar": False}), md=6),
        ]),
    ])


# ── Finance tab ───────────────────────────────────────────────────────────

def render_finance(m_start, m_end):
    df = budget_variance()
    df = df[(df["month"] >= m_start) & (df["month"] <= m_end)]

    # Budget vs Actual grouped bar
    grp = df.groupby("month")[["budget", "actual"]].sum().reset_index()
    fig_bva = go.Figure()
    fig_bva.add_bar(x=grp["month"], y=grp["budget"], name="Budget",  marker_color=BORDER)
    fig_bva.add_bar(x=grp["month"], y=grp["actual"], name="Actual",  marker_color=PRIMARY)
    fig_bva.update_layout(**CHART_LAYOUT, barmode="group", title="Monthly Budget vs Actual Spend")

    # Variance waterfall per category
    cat_grp = df.groupby("category")[["budget", "actual"]].sum().reset_index()
    cat_grp["variance"] = cat_grp["actual"] - cat_grp["budget"]
    fig_wf = go.Figure(go.Waterfall(
        name="Variance",
        orientation="v",
        x=cat_grp["category"],
        y=cat_grp["variance"],
        connector={"line": {"color": BORDER}},
        increasing={"marker": {"color": DANGER}},
        decreasing={"marker": {"color": SUCCESS}},
        totals={"marker": {"color": PRIMARY}},
    ))
    fig_wf.update_layout(**CHART_LAYOUT, title="Budget Variance by Category ($)")

    # Status donut
    status_counts = df.groupby("status").size().reset_index(name="count")
    color_map = {"On Track": SUCCESS, "Over Budget": DANGER, "Under Budget": WARNING}
    fig_donut = go.Figure(go.Pie(
        labels=status_counts["status"],
        values=status_counts["count"],
        hole=0.55,
        marker_colors=[color_map.get(s, PRIMARY) for s in status_counts["status"]],
    ))
    fig_donut.update_layout(**CHART_LAYOUT, title="Budget Status Distribution",
                            showlegend=True)

    # Variance % heatmap
    piv = df.pivot_table(index="category", columns="month", values="variance_pct")
    fig_heat = go.Figure(go.Heatmap(
        z=piv.values, x=piv.columns.tolist(), y=piv.index.tolist(),
        colorscale="RdYlGn", zmid=0,
        text=piv.values.round(1), texttemplate="%{text}%",
    ))
    fig_heat.update_layout(**CHART_LAYOUT, title="Variance % Heatmap (green=under, red=over)")

    # Table
    tbl = df[["month", "category", "budget", "actual", "variance_pct", "status"]].copy()
    tbl["budget"]  = tbl["budget"].apply(lambda v: f"${v:,.0f}")
    tbl["actual"]  = tbl["actual"].apply(lambda v: f"${v:,.0f}")
    tbl["variance_pct"] = tbl["variance_pct"].apply(lambda v: f"{v:+.1f}%")

    table = dash_table.DataTable(
        data=tbl.to_dict("records"),
        columns=[{"name": c.replace("_", " ").title(), "id": c} for c in tbl.columns],
        page_size=12,
        style_table={"overflowX": "auto"},
        style_header={"backgroundColor": BG_CARD, "color": TEXT_MAIN, "fontWeight": "600",
                      "border": f"1px solid {BORDER}"},
        style_cell={"backgroundColor": BG_PAGE, "color": TEXT_MUTED,
                    "border": f"1px solid {BORDER}", "fontSize": "13px"},
        style_data_conditional=[
            {"if": {"filter_query": "{status} = 'Over Budget'",  "column_id": "status"},
             "color": DANGER, "fontWeight": "600"},
            {"if": {"filter_query": "{status} = 'Under Budget'", "column_id": "status"},
             "color": WARNING},
            {"if": {"filter_query": "{status} = 'On Track'",     "column_id": "status"},
             "color": SUCCESS},
        ],
        sort_action="native",
        filter_action="native",
    )

    return html.Div([
        section_title("Financial Performance"),
        dbc.Row([
            dbc.Col(dcc.Graph(figure=fig_bva,   config={"displayModeBar": False}), md=6),
            dbc.Col(dcc.Graph(figure=fig_wf,    config={"displayModeBar": False}), md=6),
        ], className="mb-3"),
        dbc.Row([
            dbc.Col(dcc.Graph(figure=fig_donut, config={"displayModeBar": False}), md=4),
            dbc.Col(dcc.Graph(figure=fig_heat,  config={"displayModeBar": False}), md=8),
        ], className="mb-3"),
        section_title("Finance Detail Table"),
        table,
    ])


# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8050)
