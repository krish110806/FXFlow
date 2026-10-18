"""
FXFlow — ETL orchestrator.

Coordinates the full ingestion pipeline:
  1. Fetch exchange rates from the Frankfurter API
  2. Validate records
  3. Persist raw responses
  4. Upsert into fact_exchange_rate (or CSV fallback)
  5. Compute and store analytics
  6. Log pipeline run metadata

Designed so that Apache Airflow can call each step independently.
"""

from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from fxflow.config import api_config, pipeline_config, PROJECT_ROOT
from fxflow.logging import logger
from fxflow.pipeline.api_client import FrankfurterClient
from fxflow.pipeline.validators import validate_rate_records, ValidationResult
from fxflow.pipeline.analytics import compute_analytics

# ── processed data directory ─────────────────────────────────────────
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

RATES_CSV = PROCESSED_DIR / "exchange_rates.csv"
ANALYTICS_CSV = PROCESSED_DIR / "rate_analytics.csv"
PIPELINE_LOG_CSV = PROCESSED_DIR / "pipeline_runs.csv"
CURRENCIES_CSV = PROCESSED_DIR / "currencies.csv"
REJECTED_CSV = PROCESSED_DIR / "rejected_records.csv"


# =====================================================================
# Pipeline steps — each is a standalone function (Airflow-friendly)
# =====================================================================


def step_fetch_rates(
    from_date: date,
    to_date: Optional[date] = None,
    quotes: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Step 1: Fetch rates from the API."""
    client = FrankfurterClient()
    quotes = quotes or api_config.tracked_currencies
    to_date = to_date or date.today()

    logger.info(
        f"Fetching rates  {from_date} → {to_date}  "
        f"base={client.base_currency}  quotes={quotes}"
    )
    data = client.get_historical_rates(from_date, to_date, quotes)
    logger.info(f"Fetched {len(data)} raw rate records")
    return data


def step_validate(
    raw_records: List[Dict[str, Any]],
) -> ValidationResult:
    """Step 2: Validate fetched records."""
    result = validate_rate_records(raw_records)
    logger.info(
        f"Validation complete: {len(result.valid)} valid, "
        f"{len(result.rejected)} rejected"
    )
    return result


def step_persist_rates(
    valid_records: List[Dict[str, Any]],
) -> pd.DataFrame:
    """
    Step 3: Upsert validated records.

    In file-only mode (no Postgres), appends to a CSV with
    duplicate detection on (rate_date, base_currency, quote_currency).
    """
    new_df = pd.DataFrame(valid_records)
    if new_df.empty:
        logger.warning("No valid records to persist.")
        return new_df

    # normalise column names
    new_df = new_df.rename(columns={
        "date": "rate_date",
        "base": "base_currency",
        "quote": "quote_currency",
    })
    new_df["rate"] = pd.to_numeric(new_df["rate"], errors="coerce")
    new_df["rate_date"] = pd.to_datetime(new_df["rate_date"]).dt.date
    new_df["source"] = "frankfurter"
    new_df["ingested_at"] = pd.Timestamp.now(tz="UTC")

    # ── deduplicate against existing data ────────────────────────────
    if RATES_CSV.exists():
        existing = pd.read_csv(RATES_CSV, parse_dates=["rate_date"])
        existing["rate_date"] = existing["rate_date"].dt.date
        merge_keys = ["rate_date", "base_currency", "quote_currency"]
        merged = new_df.merge(existing[merge_keys], on=merge_keys, how="left", indicator=True)
        truly_new = merged[merged["_merge"] == "left_only"].drop(columns=["_merge"])
        dupes = len(new_df) - len(truly_new)
        if dupes:
            logger.info(f"Skipped {dupes} duplicate records")
        combined = pd.concat([existing, truly_new], ignore_index=True)
    else:
        combined = new_df
        truly_new = new_df

    combined.to_csv(RATES_CSV, index=False)
    logger.info(
        f"Persisted {len(truly_new)} new rate records  "
        f"(total: {len(combined)})"
    )
    return combined


def step_persist_rejected(
    rejected: List[tuple],
    run_id: str | int = "manual",
) -> None:
    """Step 3b: Log rejected records to CSV."""
    if not rejected:
        return
    rows = [
        {
            "run_id": run_id,
            "record_data": json.dumps(rec, default=str),
            "reason": reason,
            "rejected_at": pd.Timestamp.now(tz="UTC"),
        }
        for rec, reason in rejected
    ]
    new_df = pd.DataFrame(rows)
    if REJECTED_CSV.exists():
        existing = pd.read_csv(REJECTED_CSV)
        combined = pd.concat([existing, new_df], ignore_index=True)
    else:
        combined = new_df
    combined.to_csv(REJECTED_CSV, index=False)
    logger.info(f"Logged {len(rows)} rejected records")


def step_compute_analytics(
    rates_df: Optional[pd.DataFrame] = None,
) -> pd.DataFrame:
    """Step 4: Calculate daily % change and rolling volatility."""
    if rates_df is None:
        if not RATES_CSV.exists():
            logger.warning("No rates data to compute analytics from.")
            return pd.DataFrame()
        rates_df = pd.read_csv(RATES_CSV, parse_dates=["rate_date"])

    analytics_df = compute_analytics(rates_df)

    # save to CSV
    analytics_df.to_csv(ANALYTICS_CSV, index=False)
    logger.info(f"Analytics saved → {ANALYTICS_CSV.name}")
    return analytics_df


def step_fetch_currencies() -> pd.DataFrame:
    """Fetch the currency dimension and persist."""
    client = FrankfurterClient()
    data = client.get_currencies()
    df = pd.DataFrame(data)
    df.to_csv(CURRENCIES_CSV, index=False)
    logger.info(f"Saved {len(df)} currencies → {CURRENCIES_CSV.name}")
    return df


def step_log_run(
    run_type: str,
    status: str,
    rows_fetched: int = 0,
    rows_inserted: int = 0,
    rows_rejected: int = 0,
    error_message: str | None = None,
) -> None:
    """Step 5: Append a pipeline-run record."""
    row = {
        "run_type": run_type,
        "status": status,
        "started_at": pd.Timestamp.now(tz="UTC"),
        "finished_at": pd.Timestamp.now(tz="UTC"),
        "rows_fetched": rows_fetched,
        "rows_inserted": rows_inserted,
        "rows_rejected": rows_rejected,
        "error_message": error_message or "",
    }
    new_df = pd.DataFrame([row])
    if PIPELINE_LOG_CSV.exists():
        existing = pd.read_csv(PIPELINE_LOG_CSV)
        combined = pd.concat([existing, new_df], ignore_index=True)
    else:
        combined = new_df
    combined.to_csv(PIPELINE_LOG_CSV, index=False)


# =====================================================================
# Full pipeline — calls all steps in order
# =====================================================================


def run_full_pipeline(
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    quotes: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Execute the complete ingestion pipeline.

    Returns a summary dict with counts and status.
    """
    to_date = to_date or date.today()
    from_date = from_date or (
        to_date - timedelta(days=pipeline_config.initial_backfill_days)
    )
    quotes = quotes or api_config.tracked_currencies

    logger.info("=" * 60)
    logger.info("FXFlow Pipeline — START")
    logger.info("=" * 60)

    summary: Dict[str, Any] = {
        "status": "running",
        "from_date": from_date.isoformat(),
        "to_date": to_date.isoformat(),
    }

    try:
        # 1. Fetch
        raw = step_fetch_rates(from_date, to_date, quotes)
        summary["rows_fetched"] = len(raw)

        # 2. Validate
        vr = step_validate(raw)
        summary["rows_valid"] = len(vr.valid)
        summary["rows_rejected"] = len(vr.rejected)

        # 3. Persist
        rates_df = step_persist_rates(vr.valid)
        summary["rows_persisted"] = len(rates_df)

        # 3b. Log rejects
        step_persist_rejected(vr.rejected)

        # 4. Analytics
        analytics_df = step_compute_analytics(rates_df)
        summary["analytics_rows"] = len(analytics_df)

        # 5. Currencies dimension
        step_fetch_currencies()

        summary["status"] = "success"
        logger.info(f"Pipeline completed successfully: {summary}")

    except Exception as exc:
        summary["status"] = "error"
        summary["error"] = str(exc)
        logger.exception(f"Pipeline failed: {exc}")

    # 6. Log the run
    step_log_run(
        run_type="full_ingestion",
        status=summary["status"],
        rows_fetched=summary.get("rows_fetched", 0),
        rows_inserted=summary.get("rows_persisted", 0),
        rows_rejected=summary.get("rows_rejected", 0),
        error_message=summary.get("error"),
    )

    logger.info("=" * 60)
    logger.info("FXFlow Pipeline — END")
    logger.info("=" * 60)
    return summary
