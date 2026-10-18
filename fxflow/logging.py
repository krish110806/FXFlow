"""
FXFlow — Structured logging with Loguru.

Provides a pre-configured logger that writes to both the console
and rotating log files.
"""

from __future__ import annotations

import sys

from loguru import logger

from fxflow.config import log_config

# ── remove default handler ───────────────────────────────────────────
logger.remove()

# ── console handler ──────────────────────────────────────────────────
logger.add(
    sys.stderr,
    level=log_config.level,
    format=(
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> — "
        "<level>{message}</level>"
    ),
    colorize=True,
)

# ── file handler (rotating) ─────────────────────────────────────────
log_config.log_dir.mkdir(parents=True, exist_ok=True)

logger.add(
    str(log_config.log_dir / "fxflow_{time:YYYY-MM-DD}.log"),
    level=log_config.level,
    rotation="10 MB",
    retention="30 days",
    compression="zip",
    format=(
        "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | "
        "{name}:{function}:{line} — {message}"
    ),
)

# Re-export so other modules can do:  from fxflow.logging import logger
__all__ = ["logger"]
