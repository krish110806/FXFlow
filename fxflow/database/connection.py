"""
FXFlow — Database connection manager.

Provides a lightweight wrapper around psycopg2 and SQLAlchemy for
connection pooling, schema bootstrap, and convenience helpers.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Generator, Optional

import psycopg2
import psycopg2.extras
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from fxflow.config import db_config
from fxflow.logging import logger
from fxflow.database.schema import SCHEMA_DDL


def get_engine() -> Engine:
    """Return a SQLAlchemy engine (pooled)."""
    return create_engine(
        db_config.url,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
    )


@contextmanager
def get_connection() -> Generator:
    """Yield a raw psycopg2 connection (auto-committed on success)."""
    conn = psycopg2.connect(
        host=db_config.host,
        port=db_config.port,
        dbname=db_config.database,
        user=db_config.user,
        password=db_config.password,
    )
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


@contextmanager
def get_cursor(conn=None) -> Generator:
    """Yield a DictCursor, optionally reusing an existing connection."""
    if conn is not None:
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        try:
            yield cur
        finally:
            cur.close()
    else:
        with get_connection() as c:
            cur = c.cursor(cursor_factory=psycopg2.extras.DictCursor)
            try:
                yield cur
            finally:
                cur.close()


def bootstrap_schema() -> None:
    """Create all tables if they don't exist."""
    logger.info("Bootstrapping database schema …")
    with get_connection() as conn:
        with conn.cursor() as cur:
            for ddl in SCHEMA_DDL:
                cur.execute(ddl)
    logger.info("Schema bootstrap complete.")


def test_connection() -> bool:
    """Return True if the database is reachable."""
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
                return True
    except Exception as exc:
        logger.warning(f"Database connection test failed: {exc}")
        return False
