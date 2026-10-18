"""
FXFlow — Centralised configuration.

Reads settings from environment variables / .env file and exposes
them as typed attributes.  Nothing is hard-coded.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from dotenv import load_dotenv

# ── locate .env ──────────────────────────────────────────────────────
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_PROJECT_ROOT / ".env")


@dataclass(frozen=True)
class DatabaseConfig:
    """PostgreSQL connection parameters."""

    host: str = os.getenv("POSTGRES_HOST", "localhost")
    port: int = int(os.getenv("POSTGRES_PORT", "5432"))
    database: str = os.getenv("POSTGRES_DB", "fxflow")
    user: str = os.getenv("POSTGRES_USER", "fxflow_user")
    password: str = os.getenv("POSTGRES_PASSWORD", "")

    @property
    def url(self) -> str:
        """SQLAlchemy-compatible connection URL."""
        return (
            f"postgresql://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.database}"
        )


@dataclass(frozen=True)
class APIConfig:
    """Frankfurter API settings."""

    base_url: str = os.getenv(
        "FRANKFURTER_BASE_URL", "https://api.frankfurter.dev/v2"
    )
    base_currency: str = os.getenv("DEFAULT_BASE_CURRENCY", "USD")
    tracked_currencies: List[str] = field(default_factory=lambda: [
        c.strip()
        for c in os.getenv(
            "TRACKED_CURRENCIES",
            "EUR,GBP,JPY,CHF,CAD,AUD,CNY,INR,BRL,MXN",
        ).split(",")
    ])


@dataclass(frozen=True)
class PipelineConfig:
    """Pipeline tuning knobs."""

    initial_backfill_days: int = int(
        os.getenv("INITIAL_BACKFILL_DAYS", "365")
    )
    volatility_window: int = int(os.getenv("VOLATILITY_WINDOW", "20"))


@dataclass(frozen=True)
class LogConfig:
    """Logging settings."""

    level: str = os.getenv("LOG_LEVEL", "INFO")
    log_dir: Path = Path(os.getenv("LOG_DIR", str(_PROJECT_ROOT / "logs")))


# ── singletons ───────────────────────────────────────────────────────
db_config = DatabaseConfig()
api_config = APIConfig()
pipeline_config = PipelineConfig()
log_config = LogConfig()
PROJECT_ROOT = _PROJECT_ROOT
