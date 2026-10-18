"""
FXFlow — Data access layer for the Streamlit dashboard.

Provides functions that read from CSV files (file-only mode)
or PostgreSQL.  The dashboard imports this module exclusively;
it never reads files or queries the DB directly.
"""

from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from fxflow.config import api_config, pipeline_config, PROJECT_ROOT
from fxflow.logging import logger
from fxflow.pipeline.api_client import FrankfurterClient

# ── data paths ───────────────────────────────────────────────────────
_DATA_DIR = PROJECT_ROOT / "data" / "processed"

RATES_CSV = _DATA_DIR / "exchange_rates.csv"
ANALYTICS_CSV = _DATA_DIR / "rate_analytics.csv"
PIPELINE_LOG_CSV = _DATA_DIR / "pipeline_runs.csv"
CURRENCIES_CSV = _DATA_DIR / "currencies.csv"
REJECTED_CSV = _DATA_DIR / "rejected_records.csv"


# =====================================================================
# Currency helpers
# =====================================================================

def get_currencies() -> pd.DataFrame:
    """Return the currencies dimension as a DataFrame."""
    if CURRENCIES_CSV.exists():
        return pd.read_csv(CURRENCIES_CSV)
    # fallback: fetch live
    try:
        client = FrankfurterClient()
        data = client.get_currencies()
        df = pd.DataFrame(data)
        df.to_csv(CURRENCIES_CSV, index=False)
        return df
    except Exception as exc:
        logger.warning(f"Could not fetch currencies: {exc}")
        return pd.DataFrame()


def get_currency_map() -> Dict[str, str]:
    """Return {iso_code: name} mapping."""
    df = get_currencies()
    if df.empty:
        return {}
    return dict(zip(df["iso_code"], df["name"]))


# =====================================================================
# Exchange rate data
# =====================================================================

def get_exchange_rates(
    pair: Optional[Tuple[str, str]] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> pd.DataFrame:
    """
    Return exchange rate history, optionally filtered.

    Parameters
    ----------
    pair : (base, quote) or None for all pairs
    from_date, to_date : date range filter
    """
    if not RATES_CSV.exists():
        return pd.DataFrame()

    df = pd.read_csv(RATES_CSV, parse_dates=["rate_date"])

    if pair:
        base, quote = pair
        df = df[
            (df["base_currency"] == base) & (df["quote_currency"] == quote)
        ]

    if from_date:
        df = df[df["rate_date"] >= pd.Timestamp(from_date)]
    if to_date:
        df = df[df["rate_date"] <= pd.Timestamp(to_date)]

    return df.sort_values("rate_date").reset_index(drop=True)


def get_latest_rates() -> pd.DataFrame:
    """Return the most recent rate for each currency pair."""
    df = get_exchange_rates()
    if df.empty:
        return df
    idx = df.groupby(["base_currency", "quote_currency"])["rate_date"].idxmax()
    return df.loc[idx].reset_index(drop=True)


def get_available_pairs() -> List[Tuple[str, str]]:
    """Return sorted list of (base, quote) pairs in the dataset."""
    df = get_exchange_rates()
    if df.empty:
        return []
    pairs = (
        df[["base_currency", "quote_currency"]]
        .drop_duplicates()
        .sort_values(["base_currency", "quote_currency"])
    )
    return list(pairs.itertuples(index=False, name=None))


# =====================================================================
# Analytics data
# =====================================================================

def get_analytics(
    pair: Optional[Tuple[str, str]] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
) -> pd.DataFrame:
    """Return analytics data, optionally filtered."""
    if not ANALYTICS_CSV.exists():
        return pd.DataFrame()

    df = pd.read_csv(ANALYTICS_CSV, parse_dates=["rate_date"])

    if pair:
        base, quote = pair
        df = df[
            (df["base_currency"] == base) & (df["quote_currency"] == quote)
        ]

    if from_date:
        df = df[df["rate_date"] >= pd.Timestamp(from_date)]
    if to_date:
        df = df[df["rate_date"] <= pd.Timestamp(to_date)]

    return df.sort_values("rate_date").reset_index(drop=True)


# =====================================================================
# Pipeline monitoring
# =====================================================================

def get_pipeline_runs() -> pd.DataFrame:
    """Return the pipeline run history."""
    if not PIPELINE_LOG_CSV.exists():
        return pd.DataFrame()
    return pd.read_csv(PIPELINE_LOG_CSV, parse_dates=["started_at", "finished_at"])


def get_rejected_records() -> pd.DataFrame:
    """Return all rejected records."""
    if not REJECTED_CSV.exists():
        return pd.DataFrame()
    return pd.read_csv(REJECTED_CSV, parse_dates=["rejected_at"])


def get_data_freshness() -> Dict[str, Any]:
    """Return freshness info: last ingestion date, row counts, etc."""
    info: Dict[str, Any] = {
        "rates_exist": RATES_CSV.exists(),
        "analytics_exist": ANALYTICS_CSV.exists(),
        "total_rate_rows": 0,
        "total_analytics_rows": 0,
        "latest_rate_date": None,
        "oldest_rate_date": None,
        "unique_pairs": 0,
        "last_pipeline_run": None,
        "last_pipeline_status": None,
    }

    if RATES_CSV.exists():
        df = pd.read_csv(RATES_CSV, parse_dates=["rate_date"])
        info["total_rate_rows"] = len(df)
        if not df.empty:
            info["latest_rate_date"] = df["rate_date"].max()
            info["oldest_rate_date"] = df["rate_date"].min()
            info["unique_pairs"] = df.groupby(
                ["base_currency", "quote_currency"]
            ).ngroups

    if ANALYTICS_CSV.exists():
        adf = pd.read_csv(ANALYTICS_CSV)
        info["total_analytics_rows"] = len(adf)

    runs = get_pipeline_runs()
    if not runs.empty:
        last = runs.iloc[-1]
        info["last_pipeline_run"] = last.get("started_at")
        info["last_pipeline_status"] = last.get("status")

    return info


# =====================================================================
# Live API data (for when CSV doesn't exist yet)
# =====================================================================

def fetch_live_rates(
    from_date: date,
    to_date: Optional[date] = None,
    quotes: Optional[List[str]] = None,
) -> pd.DataFrame:
    """
    Fetch rates directly from the API and return as a DataFrame.
    Used by the dashboard when no local data exists.
    """
    client = FrankfurterClient()
    quotes = quotes or api_config.tracked_currencies
    to_date = to_date or date.today()

    try:
        data = client.get_historical_rates(from_date, to_date, quotes)
        if not data:
            return pd.DataFrame()
        df = pd.DataFrame(data)
        df = df.rename(columns={
            "date": "rate_date",
            "base": "base_currency",
            "quote": "quote_currency",
        })
        df["rate"] = pd.to_numeric(df["rate"], errors="coerce")
        df["rate_date"] = pd.to_datetime(df["rate_date"])
        return df.sort_values("rate_date").reset_index(drop=True)
    except Exception as exc:
        logger.error(f"Live rate fetch failed: {exc}")
        return pd.DataFrame()
