#!/usr/bin/env python3
"""
FXFlow — Command-line interface.

Usage:
  python -m fxflow.cli ingest             Full pipeline run
  python -m fxflow.cli ingest --days 30   Last 30 days only
  python -m fxflow.cli bootstrap          Create DB schema
  python -m fxflow.cli check              Test DB connection
"""

from __future__ import annotations

import argparse
import sys
from datetime import date, timedelta

from fxflow.logging import logger


def cmd_ingest(args: argparse.Namespace) -> None:
    """Run the ingestion pipeline."""
    from fxflow.pipeline.orchestrator import run_full_pipeline

    to_date = date.today()
    from_date = to_date - timedelta(days=args.days)

    summary = run_full_pipeline(from_date=from_date, to_date=to_date)
    status = summary.get("status", "unknown")
    if status == "success":
        logger.info(f"✓ Pipeline completed: {summary}")
    else:
        logger.error(f"✗ Pipeline failed: {summary}")
        sys.exit(1)


def cmd_bootstrap(args: argparse.Namespace) -> None:
    """Bootstrap the database schema."""
    from fxflow.database.connection import bootstrap_schema
    bootstrap_schema()


def cmd_check(args: argparse.Namespace) -> None:
    """Test the database connection."""
    from fxflow.database.connection import test_connection
    if test_connection():
        print("✓ Database connection OK")
    else:
        print("✗ Database connection FAILED")
        sys.exit(1)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="fxflow",
        description="FXFlow — Foreign Exchange Intelligence Platform CLI",
    )
    sub = parser.add_subparsers(dest="command")

    # ── ingest ───────────────────────────────────────────────────────
    p_ingest = sub.add_parser("ingest", help="Run the ingestion pipeline")
    p_ingest.add_argument(
        "--days", type=int, default=365,
        help="Number of days to backfill (default: 365)",
    )
    p_ingest.set_defaults(func=cmd_ingest)

    # ── bootstrap ────────────────────────────────────────────────────
    p_boot = sub.add_parser("bootstrap", help="Create database schema")
    p_boot.set_defaults(func=cmd_bootstrap)

    # ── check ────────────────────────────────────────────────────────
    p_check = sub.add_parser("check", help="Test database connection")
    p_check.set_defaults(func=cmd_check)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)

    args.func(args)


if __name__ == "__main__":
    main()
