# KPI Dashboard & Reporting Prototype

A data-driven KPI dashboard built with **Python, SQL, Plotly Dash** and **SQLite**.

---

## Features

| Area | What's inside |
|------|--------------|
| **Data Layer** | SQL extraction via `data/extractor.py`, pandas transformations in `data/transformer.py` |
| **Data Quality** | Automated null, range, completeness & duplicate checks (`data/quality.py`) |
| **Sales** | Revenue vs Target bar, Region lines, Product treemap, 7/30-day MA trend |
| **Operations** | Tickets stacked bar, SLA breach %, Handle-time heatmap, Efficiency trend |
| **Finance** | Budget vs Actual, Variance waterfall, Status donut, Variance heatmap + filterable table |
| **Filters** | Region dropdown + Month range slider (all charts update live) |
| **Refresh** | Manual "Refresh Data" button re-runs all queries and DQ checks |

---

## Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Seed the database (one-time)
```bash
python db/seed_data.py
```
This creates `db/kpi.db` with a full year (2024) of synthetic sales, operations, and finance data.

### 3. Run the dashboard
```bash
python app.py
```

### 4. Open in browser
```
http://localhost:8050
```

---

## Project Structure

```
KPI-Dashboard/
├── app.py                  ← Dash app (layout + callbacks)
├── requirements.txt
├── db/
│   ├── seed_data.py        ← Creates kpi.db with sample data
│   └── kpi.db              ← SQLite DB (generated)
├── data/
│   ├── extractor.py        ← SQL queries → DataFrames
│   ├── transformer.py      ← Derived KPIs (attainment %, MA, etc.)
│   └── quality.py          ← Automated data-quality checks
└── README.md
```

---

## Tech Stack

- **Python 3.10+**
- **SQLite** – embedded DB, zero config
- **SQLAlchemy / sqlite3** – data extraction
- **Pandas / NumPy** – transformation & KPI derivation
- **Plotly Dash** – interactive charts & layout
- **Dash Bootstrap Components** – responsive grid
