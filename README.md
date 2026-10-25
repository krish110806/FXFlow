# FXFlow — Foreign Exchange Intelligence Platform

A professional **Data Engineering** project that ingests, warehouses, validates, and
visualises foreign exchange rates.

---

## ✨ Features

| Layer | Capabilities |
|-------|-------------|
| **Ingestion** | Fetch historical rates from the [Frankfurter API](https://frankfurter.app/) and annual inflation from World Bank indicator `FP.CPI.TOTL.ZG` |
| **Validation** | Type checks, range guards, duplicate detection, rejected-record logging |
| **Storage** | Raw JSON lineage files, timestamped World Bank CSV snapshots, and processed CSV (PostgreSQL optional) |
| **Analytics** | Daily % returns, rolling volatility, normalised performance, correlations |
| **Design System** | Editorial-finance terminal aesthetic (Warm ivory #F4F0E7, soft ivory cards #FFFCF5, midnight navy #142B3B, deep teal #287D6B, champagne gold #C6A568) |
| **Dashboard** | 5-page Streamlit app with institutional Plotly interactive charts |
| **Monitoring** | Pipeline run log, data freshness, data quality metrics |
| **Extensibility** | Modular step functions ready for Apache Airflow DAGs |

---

## 🗂️ Project Structure

```
FXFlow/
├── app.py                          # Streamlit entry point
├── requirements.txt
├── .env.example                    # Environment variable template
├── .streamlit/config.toml          # Streamlit theme
├── fxflow/
│   ├── __init__.py
│   ├── config.py                   # Centralised configuration
│   ├── logging.py                  # Loguru structured logging
│   ├── cli.py                      # Command-line interface
│   ├── data_access.py              # Data access layer (dashboard reads this)
│   ├── data_access_csv.py          # World Bank CSV pipeline data access
│   ├── database/
│   │   ├── __init__.py
│   │   ├── schema.py               # PostgreSQL DDL (dim/fact/meta tables)
│   │   └── connection.py           # Connection manager + schema bootstrap
│   ├── pipeline/
│   │   ├── __init__.py
│   │   ├── api_client.py           # Frankfurter API client
│   │   ├── validators.py           # Record-level data validation
│   │   ├── analytics.py            # % change & rolling volatility
│   │   ├── orchestrator.py         # Full ETL pipeline (Airflow-ready)
│   │   └── csv_orchestrator.py     # World Bank inflation ETL and run history
│   └── dashboard/
│       ├── __init__.py
│       ├── theme.py                # Colours, Plotly template, CSS
│       ├── page_overview.py        # Overview — KPIs & trends
│       ├── page_explorer.py        # Currency Explorer — pair deep-dive
│       ├── page_volatility.py      # Volatility Lab — returns & vol
│       ├── page_economics.py       # Economic Insights — comparisons
│       ├── page_pipeline.py        # Frankfurter Pipeline Monitor
│       └── page_pipeline_csv.py    # World Bank CSV pipeline dashboard
├── data/
│   ├── raw/                        # Raw API JSON + World Bank CSV snapshots
│   └── processed/                  # Cleaned CSVs
└── logs/                           # Rotating log files
```

---

## 🚀 Quick Start

### 1. Clone & create virtual environment

```bash
cd FXFlow
python -m venv venv
venv\Scripts\activate       # Windows
# source venv/bin/activate  # macOS/Linux
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment

```bash
copy .env.example .env
# Edit .env if you want to change defaults
# PostgreSQL is OPTIONAL — the project works with CSV files out of the box
```

### 4. Run the ingestion pipeline

```bash
# Ingest the last 90 days of exchange rate data
python -m fxflow.cli ingest --days 90

# Or backfill a full year
python -m fxflow.cli ingest --days 365
```

### 5. Launch the dashboard

```bash
streamlit run app.py
```

The dashboard opens at **http://localhost:8502**.

> **Note:** You can launch the dashboard *without* running the pipeline first.
> It will fetch live data directly from the Frankfurter API. Running the
> pipeline gives you persistent local data, analytics, and pipeline monitoring.

---

## 🗄️ PostgreSQL (Optional)

The project works entirely with CSV files by default. To enable the PostgreSQL
warehouse:

1. Create the database and user:

```sql
CREATE DATABASE fxflow;
CREATE USER fxflow_user WITH PASSWORD 'your_strong_password';
GRANT ALL PRIVILEGES ON DATABASE fxflow TO fxflow_user;
```

2. Update `.env` with your connection details.

3. Bootstrap the schema:

```bash
python -m fxflow.cli bootstrap
```

4. Test the connection:

```bash
python -m fxflow.cli check
```

---

## 📊 Dashboard Pages

| Page | Description |
|------|-------------|
| **Overview** | KPI cards for key pairs, day-over-day deltas, historical trend chart with period & currency selectors |
| **Currency Explorer** | Pick any pair + date range, see rate chart with 20-day MA overlay, summary stats, raw data table |
| **Volatility Lab** | Daily returns bar chart + rolling volatility line, adjustable window, volatility ranking table |
| **Economic Insights** | Normalised performance comparison, return correlation heatmap, period change ranking |
| **Pipeline Monitor** | Data freshness badges, ingestion volume chart, run history table, quality metrics, rejected records |
| **Data Pipeline → CSV** | Separate World Bank inflation pipeline with per-run stage metrics, validation, local storage lineage, throughput, and execution history |

The CSV pipeline stores its latest raw response at
`data/raw/wb_inflation_raw.csv` and retains timestamped raw snapshots alongside it.
Cleaned data, analytics, and CSV-specific execution history are stored under
`data/processed/`; the CSV pipeline does not require PostgreSQL. Its dashboard
counts are derived from each persisted run's stage details, while total stored
record counts describe the current cleaned dataset.

---

## 🔄 Airflow Integration

Each pipeline step in `fxflow/pipeline/orchestrator.py` is a standalone function:

```python
from fxflow.pipeline.orchestrator import (
    step_fetch_rates,
    step_validate,
    step_persist_rates,
    step_compute_analytics,
    step_fetch_currencies,
    step_log_run,
)
```

These can be wrapped in Airflow `PythonOperator` tasks to build a scheduled DAG
with proper dependency management, retries, and alerting.

---

## ⚙️ Configuration

All settings are controlled via environment variables (see `.env.example`):

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_HOST` | `localhost` | Database host |
| `POSTGRES_PORT` | `5432` | Database port |
| `POSTGRES_DB` | `fxflow` | Database name |
| `POSTGRES_USER` | `fxflow_user` | Database user |
| `POSTGRES_PASSWORD` | — | Database password (**never committed**) |
| `FRANKFURTER_BASE_URL` | `https://api.frankfurter.dev/v2` | API base URL |
| `DEFAULT_BASE_CURRENCY` | `USD` | Base currency for ingestion |
| `TRACKED_CURRENCIES` | `EUR,GBP,...` | Comma-separated quote currencies |
| `INITIAL_BACKFILL_DAYS` | `365` | Days to backfill on first run |
| `VOLATILITY_WINDOW` | `20` | Rolling volatility window |
| `LOG_LEVEL` | `INFO` | Logging verbosity |

---

## 🛡️ Data Quality

The validation pipeline checks every record for:

- ✅ Required fields present (`date`, `base`, `quote`, `rate`)
- ✅ Rate is a positive finite number
- ✅ Date is valid ISO format and not in the future
- ✅ Currency codes are 3-letter uppercase alpha
- ✅ Duplicate detection on `(date, base, quote)` during upsert

Rejected records are logged with reasons for inspection on the Pipeline Monitor page.

---

## 📜 License

MIT
