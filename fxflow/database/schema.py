"""
FXFlow — PostgreSQL schema definitions.

Warehouse schema following dimensional modelling:
  • dim_currency        – currency dimension
  • fact_exchange_rate   – daily exchange rate facts
  • fact_rate_analytics  – derived analytics (pct change, volatility)
  • meta_pipeline_run    – pipeline execution log
  • meta_rejected_record – records that failed validation

The DDL is idempotent: every statement uses IF NOT EXISTS.
"""

from __future__ import annotations

# ─────────────────────────────────────────────────────────────────────
# All DDL statements, executed in order.
# ─────────────────────────────────────────────────────────────────────

SCHEMA_DDL: list[str] = [
    # ── dimension: currency ──────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS dim_currency (
        currency_id   SERIAL PRIMARY KEY,
        iso_code      VARCHAR(3)  NOT NULL UNIQUE,
        name          VARCHAR(80) NOT NULL,
        symbol        VARCHAR(10),
        start_date    DATE,
        end_date      DATE,
        created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
        updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    """,

    # ── fact: daily exchange rates ───────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS fact_exchange_rate (
        rate_id       BIGSERIAL PRIMARY KEY,
        rate_date     DATE        NOT NULL,
        base_currency VARCHAR(3)  NOT NULL,
        quote_currency VARCHAR(3) NOT NULL,
        rate          NUMERIC(18,8) NOT NULL,
        source        VARCHAR(50) NOT NULL DEFAULT 'frankfurter',
        ingested_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
        UNIQUE (rate_date, base_currency, quote_currency)
    );
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_fact_rate_date
        ON fact_exchange_rate (rate_date);
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_fact_rate_pair
        ON fact_exchange_rate (base_currency, quote_currency);
    """,

    # ── fact: analytics (daily pct change, rolling vol) ──────────────
    """
    CREATE TABLE IF NOT EXISTS fact_rate_analytics (
        analytics_id    BIGSERIAL PRIMARY KEY,
        rate_date       DATE        NOT NULL,
        base_currency   VARCHAR(3)  NOT NULL,
        quote_currency  VARCHAR(3)  NOT NULL,
        daily_pct_change NUMERIC(12,6),
        rolling_volatility NUMERIC(12,6),
        volatility_window  INT NOT NULL DEFAULT 20,
        computed_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
        UNIQUE (rate_date, base_currency, quote_currency)
    );
    """,

    # ── meta: pipeline run log ───────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS meta_pipeline_run (
        run_id        BIGSERIAL PRIMARY KEY,
        run_type      VARCHAR(40) NOT NULL,
        status        VARCHAR(20) NOT NULL DEFAULT 'running',
        started_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
        finished_at   TIMESTAMPTZ,
        rows_fetched  INT DEFAULT 0,
        rows_inserted INT DEFAULT 0,
        rows_rejected INT DEFAULT 0,
        error_message TEXT,
        metadata      JSONB
    );
    """,

    # ── meta: rejected records ───────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS meta_rejected_record (
        reject_id     BIGSERIAL PRIMARY KEY,
        run_id        BIGINT REFERENCES meta_pipeline_run(run_id),
        record_data   JSONB NOT NULL,
        reason        TEXT  NOT NULL,
        rejected_at   TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    """,

    # ── raw: store raw API responses for lineage ─────────────────────
    """
    CREATE TABLE IF NOT EXISTS raw_api_response (
        response_id   BIGSERIAL PRIMARY KEY,
        run_id        BIGINT REFERENCES meta_pipeline_run(run_id),
        request_url   TEXT NOT NULL,
        status_code   INT,
        response_body JSONB,
        fetched_at    TIMESTAMPTZ NOT NULL DEFAULT now()
    );
    """,
]
