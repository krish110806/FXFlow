"""
FXFlow — Data access layer for the CSV (World Bank Inflation) pipeline.

Provides functions that read from the CSV files produced by csv_orchestrator.
The dashboard imports this module exclusively.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

import pandas as pd

from fxflow.config import PROJECT_ROOT

# ── paths (mirrors csv_orchestrator constants) ────────────────────────
_DATA_RAW  = PROJECT_ROOT / "data" / "raw"
_DATA_PROC = PROJECT_ROOT / "data" / "processed"

RAW_CSV      = _DATA_RAW  / "wb_inflation_raw.csv"
CLEANED_CSV  = _DATA_PROC / "wb_inflation_cleaned.csv"
ANALYTICS_CSV = _DATA_PROC / "wb_inflation_analytics.csv"
RUNS_CSV     = _DATA_PROC / "csv_pipeline_runs.csv"


def parse_stage_details(value: Any) -> List[Dict[str, Any]]:
    """Decode persisted stage records, returning no metrics for invalid history."""
    if isinstance(value, list):
        return [stage for stage in value if isinstance(stage, dict)]
    if not isinstance(value, str) or not value.strip():
        return []
    try:
        stages = json.loads(value)
    except (TypeError, ValueError):
        return []
    return [stage for stage in stages if isinstance(stage, dict)] if isinstance(stages, list) else []


def _stage_count(stages: List[Dict[str, Any]], name: str, field: str) -> Optional[int]:
    stage = next((item for item in stages if item.get("stage") == name), None)
    if stage is None or field not in stage or pd.isna(stage[field]):
        return None
    try:
        return int(stage[field])
    except (TypeError, ValueError, OverflowError):
        return None


def get_csv_raw() -> pd.DataFrame:
    """Return raw downloaded inflation records."""
    if not RAW_CSV.exists():
        return pd.DataFrame()
    return pd.read_csv(RAW_CSV)


def get_csv_cleaned() -> pd.DataFrame:
    """Return cleaned (validated + transformed) inflation records."""
    if not CLEANED_CSV.exists():
        return pd.DataFrame()
    df = pd.read_csv(CLEANED_CSV)
    if "year" in df.columns:
        df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    return df


def get_csv_analytics() -> pd.DataFrame:
    """Return analytics-enriched inflation records."""
    if not ANALYTICS_CSV.exists():
        return pd.DataFrame()
    df = pd.read_csv(ANALYTICS_CSV)
    if "year" in df.columns:
        df["year"] = pd.to_numeric(df["year"], errors="coerce").astype("Int64")
    return df


def get_csv_pipeline_runs() -> pd.DataFrame:
    """Return run history with counts derived from persisted stage results."""
    if not RUNS_CSV.exists():
        return pd.DataFrame()
    df = pd.read_csv(RUNS_CSV, parse_dates=["started_at"])
    if "stage_details" not in df.columns:
        df["stage_details"] = ""
    parsed_stages = df["stage_details"].map(parse_stage_details)
    df["_stage_details"] = parsed_stages
    df["rows_fetched"] = parsed_stages.map(
        lambda stages: _stage_count(stages, "CSV Extraction", "records_out")
    )
    df["rows_valid"] = parsed_stages.map(
        lambda stages: _stage_count(stages, "Data Validation", "records_out")
    )
    df["rows_committed"] = parsed_stages.map(
        lambda stages: _stage_count(stages, "Warehouse / Local Storage", "new_records")
    )
    df["rows_rejected"] = parsed_stages.map(
        lambda stages: _stage_count(stages, "Data Validation", "rejected")
    )
    return df


def get_csv_freshness() -> Dict[str, Any]:
    """Return freshness/summary info for the CSV pipeline dataset."""
    info: Dict[str, Any] = {
        "raw_exists": RAW_CSV.exists(),
        "cleaned_exists": CLEANED_CSV.exists(),
        "analytics_exists": ANALYTICS_CSV.exists(),
        "total_raw_rows": 0,
        "total_cleaned_rows": 0,
        "total_analytics_rows": 0,
        "latest_year": None,
        "oldest_year": None,
        "countries": 0,
        "last_run_status": None,
        "last_run_at": None,
        "last_successful_run": None,
    }

    if CLEANED_CSV.exists():
        df = get_csv_cleaned()
        info["total_cleaned_rows"] = len(df)
        if not df.empty and "year" in df.columns:
            info["latest_year"] = int(df["year"].max()) if not df["year"].isna().all() else None
            info["oldest_year"] = int(df["year"].min()) if not df["year"].isna().all() else None
            info["countries"] = df["country_code"].nunique() if "country_code" in df.columns else 0

    if RAW_CSV.exists():
        raw_df = get_csv_raw()
        info["total_raw_rows"] = len(raw_df)

    if ANALYTICS_CSV.exists():
        adf = get_csv_analytics()
        info["total_analytics_rows"] = len(adf)

    runs = get_csv_pipeline_runs()
    if not runs.empty:
        last = runs.iloc[-1]
        info["last_run_status"] = last.get("status")
        info["last_run_at"] = last.get("started_at")
        success_runs = runs[runs["status"] == "success"]
        if not success_runs.empty:
            info["last_successful_run"] = success_runs.iloc[-1].get("started_at")

    return info
