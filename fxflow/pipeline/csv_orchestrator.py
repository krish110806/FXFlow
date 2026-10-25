"""
FXFlow — CSV Pipeline Orchestrator.

Ingests World Bank Indicator FP.CPI.TOTL.ZG (Inflation, consumer prices annual %).
Five stages:
  1. CSV Extraction   — download from World Bank API
  2. Data Validation  — schema, type, range checks
  3. Transformation   — normalise, deduplicate
  4. Analytics Prep   — compute yoy change and rolling avg
  5. Warehouse Load   — persist raw + cleaned CSVs and run log

Designed to be idempotent: repeated runs skip existing (country_code, year) records.
"""

from __future__ import annotations

import json
import math
import os
import re
import tempfile
import time
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import requests

from fxflow.config import PROJECT_ROOT
from fxflow.logging import logger

# ── storage paths ─────────────────────────────────────────────────────
_DATA_RAW = PROJECT_ROOT / "data" / "raw"
_DATA_PROC = PROJECT_ROOT / "data" / "processed"
_DATA_RAW.mkdir(parents=True, exist_ok=True)
_DATA_PROC.mkdir(parents=True, exist_ok=True)

RAW_CSV = _DATA_RAW / "wb_inflation_raw.csv"
CLEANED_CSV = _DATA_PROC / "wb_inflation_cleaned.csv"
ANALYTICS_CSV = _DATA_PROC / "wb_inflation_analytics.csv"
RUNS_CSV = _DATA_PROC / "csv_pipeline_runs.csv"
RAW_SNAPSHOT_PATTERN = "wb_inflation_raw_*.csv"

# ── World Bank API constants ──────────────────────────────────────────
WB_INDICATOR = "FP.CPI.TOTL.ZG"
WB_API_BASE = "https://api.worldbank.org/v2"

TARGET_COUNTRIES: List[str] = [
    "IN", "US", "GB", "DE", "JP", "CN", "BR", "ZA", "AU", "FR",
]

COUNTRY_NAMES: Dict[str, str] = {
    "IN": "India", "US": "United States", "GB": "United Kingdom",
    "DE": "Germany", "JP": "Japan", "CN": "China", "BR": "Brazil",
    "ZA": "South Africa", "AU": "Australia", "FR": "France",
}

INFLATION_FLOOR = -50.0
INFLATION_CEIL = 500.0
YEAR_MIN = 1960
YEAR_MAX = date.today().year
WB_REQUIRED_COLUMNS = {
    "country_code",
    "country_code2",
    "country_name",
    "indicator_code",
    "indicator_name",
    "year",
    "value",
}


def _atomic_to_csv(df: pd.DataFrame, path: Path) -> None:
    """Write a CSV beside its destination, then atomically replace it."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", newline="", suffix=".tmp",
            prefix=f".{path.name}.", dir=path.parent, delete=False,
        ) as temp_file:
            temp_path = temp_file.name
        df.to_csv(temp_path, index=False)
        os.replace(temp_path, path)
    except Exception:
        if temp_path:
            try:
                os.unlink(temp_path)
            except FileNotFoundError:
                pass
        raise


def _merge_cleaned_records(new_df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
    """Return the existing dataset merged with new keys and the new-key count."""
    if not CLEANED_CSV.exists():
        return new_df.copy(), len(new_df)

    existing = pd.read_csv(CLEANED_CSV)
    existing["year"] = pd.to_numeric(existing["year"], errors="coerce").astype("Int64")
    merge_keys = ["country_code", "year"]
    merged = new_df.merge(existing[merge_keys], on=merge_keys, how="left", indicator=True)
    truly_new = merged[merged["_merge"] == "left_only"].drop(columns=["_merge"])
    combined = pd.concat([existing, truly_new], ignore_index=True)
    combined = combined.drop_duplicates(subset=merge_keys, keep="last")
    return combined, len(truly_new)


# =====================================================================
# Stage 1 — CSV Extraction
# =====================================================================

def stage_extract(
    country_codes: Optional[List[str]] = None,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Download annual inflation data from World Bank API."""
    stage_info: Dict[str, Any] = {
        "stage": "CSV Extraction", "status": "idle",
        "records_in": 0, "records_out": 0, "error": None,
    }
    codes = country_codes or TARGET_COUNTRIES
    country_str = ";".join(codes)
    url = (
        f"{WB_API_BASE}/country/{country_str}/indicator/{WB_INDICATOR}"
        f"?format=json&per_page=1000&mrv=65"
    )
    logger.info(f"[CSV Pipeline] Stage 1: GET {url}")
    t0 = time.monotonic()
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        payload = resp.json()
    except Exception as exc:
        stage_info.update({"status": "error", "error": str(exc)})
        logger.error(f"[CSV Pipeline] Stage 1 failed: {exc}")
        return pd.DataFrame(), stage_info

    elapsed_ms = int((time.monotonic() - t0) * 1000)

    if not isinstance(payload, list) or len(payload) < 2:
        stage_info.update({"status": "error", "error": "Unexpected API response structure"})
        return pd.DataFrame(), stage_info

    records = payload[1]
    if not records:
        stage_info.update({"status": "error", "error": "No data returned from World Bank API"})
        return pd.DataFrame(), stage_info

    if not isinstance(records, list) or any(not isinstance(item, dict) for item in records):
        stage_info.update({"status": "error", "error": "Invalid World Bank record structure"})
        return pd.DataFrame(), stage_info

    rows = []
    for item in records:
        country = item.get("country")
        indicator = item.get("indicator")
        country = country if isinstance(country, dict) else {}
        indicator = indicator if isinstance(indicator, dict) else {}
        rows.append({
            "country_code":   item.get("countryiso3code", ""),
            "country_code2":  country.get("id", ""),
            "country_name":   country.get("value", ""),
            "indicator_code": indicator.get("id", ""),
            "indicator_name": indicator.get("value", ""),
            "year":           item.get("date", ""),
            "value":          item.get("value"),
        })

    raw_df = pd.DataFrame(rows)
    snapshot_time = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    snapshot_path = RAW_CSV.with_name(
        f"{RAW_CSV.stem}_{snapshot_time}{RAW_CSV.suffix}"
    )
    try:
        _atomic_to_csv(raw_df, snapshot_path)
        _atomic_to_csv(raw_df, RAW_CSV)
    except OSError as exc:
        stage_info.update({"status": "error", "error": f"Could not store raw snapshot: {exc}"})
        logger.error(f"[CSV Pipeline] Stage 1 failed to store raw snapshot: {exc}")
        return pd.DataFrame(), stage_info

    stage_info.update({
        "status": "success", "records_in": len(records),
        "records_out": len(raw_df), "latency_ms": elapsed_ms,
        "snapshot_file": snapshot_path.name,
    })
    logger.info(f"[CSV Pipeline] Stage 1: {len(raw_df)} raw records -> {RAW_CSV.name}")
    return raw_df, stage_info


# =====================================================================
# Stage 2 — Data Validation
# =====================================================================

def _validate_wb_row(row: "pd.Series") -> Optional[str]:
    """Return rejection reason or None if row is valid."""
    missing_columns = WB_REQUIRED_COLUMNS.difference(row.index)
    if missing_columns:
        return f"Missing required fields: {', '.join(sorted(missing_columns))}"

    if pd.isna(row["indicator_code"]) or str(row["indicator_code"]).strip() != WB_INDICATOR:
        return f"Unexpected indicator: {row['indicator_code']!r}"

    country_code = str(row["country_code"]).strip().upper()
    country_code2 = str(row["country_code2"]).strip().upper()
    if not re.fullmatch(r"[A-Z]{3}", country_code):
        return f"Invalid ISO-3 country code: {row['country_code']!r}"
    if not re.fullmatch(r"[A-Z]{2}", country_code2):
        return f"Invalid ISO-2 country code: {row['country_code2']!r}"
    if pd.isna(row["country_name"]) or not str(row["country_name"]).strip():
        return "Missing country name"
    if pd.isna(row["indicator_name"]) or not str(row["indicator_name"]).strip():
        return "Missing indicator name"

    if pd.isna(row.get("value")) or not str(row.get("value")).strip():
        return "Missing inflation value (null)"
    try:
        val = float(row["value"])
    except (TypeError, ValueError):
        return f"Non-numeric value: {row.get('value')!r}"
    if not math.isfinite(val):
        return f"Non-finite inflation value: {row.get('value')!r}"
    if val < INFLATION_FLOOR or val > INFLATION_CEIL:
        return f"Value {val:.2f}% out of plausible range [{INFLATION_FLOOR}, {INFLATION_CEIL}]"
    try:
        year_value = float(row["year"])
    except (TypeError, ValueError):
        return f"Invalid year: {row.get('year')!r}"
    if not math.isfinite(year_value) or not year_value.is_integer():
        return f"Invalid year: {row.get('year')!r}"
    yr = int(year_value)
    if yr < YEAR_MIN or yr > YEAR_MAX:
        return f"Year {yr} out of valid range [{YEAR_MIN}, {YEAR_MAX}]"
    return None


def stage_validate(
    raw_df: pd.DataFrame,
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    """Validate raw records for schema, type, and value constraints."""
    stage_info: Dict[str, Any] = {
        "stage": "Data Validation", "status": "idle",
        "records_in": len(raw_df), "records_out": 0,
        "rejected": 0, "missing_values": 0,
        "invalid_year": 0, "out_of_range": 0, "error": None,
    }
    if raw_df.empty:
        stage_info.update({"status": "error", "error": "No input data to validate"})
        return pd.DataFrame(), pd.DataFrame(), stage_info

    missing_columns = WB_REQUIRED_COLUMNS.difference(raw_df.columns)
    if missing_columns:
        rejected_df = raw_df.copy()
        rejected_df["_rejection_reason"] = (
            f"Missing required columns: {', '.join(sorted(missing_columns))}"
        )
        stage_info.update({
            "status": "error",
            "rejected": len(raw_df),
            "error": rejected_df["_rejection_reason"].iloc[0],
        })
        return pd.DataFrame(), rejected_df, stage_info

    valid_rows, rejected_rows = [], []
    for _, row in raw_df.iterrows():
        reason = _validate_wb_row(row)
        if reason:
            rejected_rows.append({**row.to_dict(), "_rejection_reason": reason})
        else:
            valid_rows.append(row.to_dict())

    valid_df = pd.DataFrame(valid_rows)
    rejected_df = pd.DataFrame(rejected_rows)
    missing = int(
        (raw_df["value"].isna() | raw_df["value"].astype(str).str.strip().eq("")).sum()
    )

    stage_info.update({
        "missing_values": missing,
        "records_out": len(valid_df),
        "rejected": len(rejected_df),
        "status": "success" if len(valid_df) > 0 else "error",
    })
    if not rejected_df.empty:
        oor = rejected_df["_rejection_reason"].str.contains("range", case=False, na=False)
        yr_ = rejected_df["_rejection_reason"].str.contains("year", case=False, na=False)
        stage_info["out_of_range"] = int(oor.sum())
        stage_info["invalid_year"] = int(yr_.sum())

    logger.info(
        f"[CSV Pipeline] Stage 2: {len(valid_df)} valid, {len(rejected_df)} rejected "
        f"({missing} missing values)"
    )
    return valid_df, rejected_df, stage_info


# =====================================================================
# Stage 3 — Transformation
# =====================================================================

def stage_transform(valid_df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Normalise, type-cast, deduplicate and sort validated records."""
    stage_info: Dict[str, Any] = {
        "stage": "Transformation", "status": "idle",
        "records_in": len(valid_df), "records_out": 0,
        "duplicates_removed": 0, "error": None,
    }
    if valid_df.empty:
        stage_info.update({"status": "error", "error": "No valid data to transform"})
        return pd.DataFrame(), stage_info

    df = valid_df.copy()
    df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    df["inflation_pct"] = pd.to_numeric(df["value"], errors="coerce")
    df["country_code"] = df["country_code"].str.strip().str.upper()
    df["country_name"] = df["country_name"].str.strip()
    df["indicator_code"] = df["indicator_code"].str.strip()
    df["source"] = "worldbank"
    df["ingested_at"] = pd.Timestamp.now(tz="UTC")

    before_drop = len(df)
    df = df.dropna(subset=["year", "inflation_pct"])
    stage_info["duplicates_removed"] += before_drop - len(df)

    before_dedup = len(df)
    df = df.drop_duplicates(subset=["country_code", "year"], keep="last")
    stage_info["duplicates_removed"] += before_dedup - len(df)

    keep_cols = [
        "country_code", "country_code2", "country_name",
        "indicator_code", "year", "inflation_pct", "source", "ingested_at",
    ]
    existing_cols = [c for c in keep_cols if c in df.columns]
    df = df[existing_cols].sort_values(["country_code", "year"]).reset_index(drop=True)

    stage_info.update({"status": "success", "records_out": len(df)})
    logger.info(
        f"[CSV Pipeline] Stage 3: {len(df)} cleaned records "
        f"({stage_info['duplicates_removed']} duplicates removed)"
    )
    return df, stage_info


# =====================================================================
# Stage 4 — Analytics Preparation
# =====================================================================

def stage_analytics(cleaned_df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Compute year-on-year change and 5-year rolling average per country."""
    stage_info: Dict[str, Any] = {
        "stage": "Analytics Preparation", "status": "idle",
        "records_in": len(cleaned_df), "records_out": 0, "error": None,
    }
    if cleaned_df.empty:
        stage_info.update({"status": "error", "error": "No cleaned data for analytics"})
        return pd.DataFrame(), stage_info

    frames = []
    for _, grp in cleaned_df.groupby("country_code"):
        g = grp.sort_values("year").copy()
        g["yoy_change_pct"] = g["inflation_pct"].diff()
        g["rolling_5y_avg"] = g["inflation_pct"].rolling(window=5, min_periods=1).mean()
        frames.append(g)

    analytics_df = pd.concat(frames, ignore_index=True)
    stage_info.update({"status": "success", "records_out": len(analytics_df)})
    logger.info(f"[CSV Pipeline] Stage 4: {len(analytics_df)} analytics rows prepared")
    return analytics_df, stage_info


# =====================================================================
# Stage 5 — Warehouse / Local Storage
# =====================================================================

def stage_warehouse(
    cleaned_df: pd.DataFrame,
    stage_infos: List[Dict[str, Any]],
    new_records: Optional[int] = None,
) -> Dict[str, Any]:
    """Atomically persist the merged cleaned dataset (dedup by country+year)."""
    stage_info: Dict[str, Any] = {
        "stage": "Warehouse / Local Storage", "status": "idle",
        "records_in": len(cleaned_df), "records_out": 0,
        "new_records": 0, "error": None,
    }
    if cleaned_df.empty:
        stage_info.update({"status": "error", "error": "No data to persist"})
        return stage_info

    combined = cleaned_df.copy()
    stage_info["new_records"] = (
        new_records if new_records is not None else len(combined)
    )
    try:
        _atomic_to_csv(combined, CLEANED_CSV)
    except OSError as exc:
        stage_info.update({
            "status": "error",
            "new_records": 0,
            "error": f"Could not persist cleaned data: {exc}",
        })
        return stage_info
    stage_info.update({"status": "success", "records_out": len(combined)})
    logger.info(
        f"[CSV Pipeline] Stage 5: {stage_info['new_records']} new records "
        f"(total: {len(combined)})"
    )
    return stage_info


# =====================================================================
# Run logger
# =====================================================================

def log_csv_run(
    run_type: str,
    status: str,
    rows_fetched: int = 0,
    rows_valid: int = 0,
    rows_committed: int = 0,
    rows_rejected: int = 0,
    error_message: Optional[str] = None,
    stage_details: Optional[str] = None,
) -> None:
    """Append one run record to the CSV pipeline run log."""
    row = {
        "run_type": run_type,
        "status": status,
        "started_at": pd.Timestamp.now(tz="UTC"),
        "rows_fetched": rows_fetched,
        "rows_valid": rows_valid,
        "rows_committed": rows_committed,
        "rows_rejected": rows_rejected,
        "error_message": error_message or "",
        "stage_details": stage_details or "",
    }
    new_df = pd.DataFrame([row])
    if RUNS_CSV.exists():
        existing = pd.read_csv(RUNS_CSV)
        combined = pd.concat([existing, new_df], ignore_index=True)
    else:
        combined = new_df
    _atomic_to_csv(combined, RUNS_CSV)


# =====================================================================
# Full pipeline entry point
# =====================================================================

def run_csv_pipeline(
    country_codes: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Execute the complete CSV ingestion pipeline.

    Returns a summary dict with per-stage info and overall status.
    On failure, existing persisted data is NOT deleted (safe fallback).
    """
    logger.info("=" * 60)
    logger.info("FXFlow CSV Pipeline — START")
    logger.info("=" * 60)

    summary: Dict[str, Any] = {
        "status": "running", "stages": [],
        "rows_fetched": 0, "rows_valid": 0,
        "rows_committed": 0, "rows_rejected": 0, "error": None,
    }

    try:
        raw_df, s1 = stage_extract(country_codes)
        summary["stages"].append(s1)
        summary["rows_fetched"] = s1.get("records_out", 0)
        if s1["status"] == "error":
            raise RuntimeError(f"Stage 1 failed: {s1['error']}")

        valid_df, rejected_df, s2 = stage_validate(raw_df)
        summary["stages"].append(s2)
        summary["rows_valid"] = s2.get("records_out", 0)
        summary["rows_rejected"] = s2.get("rejected", 0)
        if s2["status"] == "error":
            raise RuntimeError(f"Stage 2 failed: {s2['error']}")

        cleaned_df, s3 = stage_transform(valid_df)
        summary["stages"].append(s3)
        if s3["status"] == "error":
            raise RuntimeError(f"Stage 3 failed: {s3['error']}")

        combined_df, new_records = _merge_cleaned_records(cleaned_df)
        analytics_df, s4 = stage_analytics(combined_df)
        summary["stages"].append(s4)
        if s4["status"] == "error":
            raise RuntimeError(f"Stage 4 failed: {s4['error']}")

        try:
            _atomic_to_csv(analytics_df, ANALYTICS_CSV)
        except OSError as exc:
            s4.update({"status": "error", "error": f"Could not persist analytics data: {exc}"})
            raise RuntimeError(s4["error"]) from exc
        s5 = stage_warehouse(combined_df, summary["stages"], new_records)
        summary["stages"].append(s5)
        if s5["status"] == "error":
            raise RuntimeError(f"Stage 5 failed: {s5['error']}")
        summary["rows_committed"] = s5.get("new_records", 0)

        summary["status"] = "success"
        logger.info(f"[CSV Pipeline] Completed: {summary}")

    except Exception as exc:
        summary["status"] = "error"
        summary["error"] = str(exc)
        logger.exception(f"[CSV Pipeline] Failed: {exc}")

    stage_detail_str = json.dumps(
        [{k: v for k, v in s.items()} for s in summary.get("stages", [])],
        default=str,
    )
    log_csv_run(
        run_type="csv_worldbank",
        status=summary["status"],
        rows_fetched=summary.get("rows_fetched", 0),
        rows_valid=summary.get("rows_valid", 0),
        rows_committed=summary.get("rows_committed", 0),
        rows_rejected=summary.get("rows_rejected", 0),
        error_message=summary.get("error"),
        stage_details=stage_detail_str,
    )

    logger.info("=" * 60)
    logger.info("FXFlow CSV Pipeline — END")
    logger.info("=" * 60)
    return summary
