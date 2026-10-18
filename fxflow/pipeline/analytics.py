"""
FXFlow — Analytics calculations.

Compute daily percentage changes and rolling volatility from
the fact_exchange_rate table (or from a DataFrame in file-only mode).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from fxflow.config import pipeline_config
from fxflow.logging import logger


def compute_analytics(
    df: pd.DataFrame,
    window: int | None = None,
) -> pd.DataFrame:
    """
    Given a DataFrame with columns [rate_date, base_currency,
    quote_currency, rate], return a DataFrame with additional columns:
      • daily_pct_change    — simple daily return  (rate_t / rate_{t-1} - 1)
      • rolling_volatility  — std-dev of daily returns over a rolling window

    Parameters
    ----------
    df : pd.DataFrame
        Must contain rate_date, base_currency, quote_currency, rate.
    window : int, optional
        Rolling window in business days.  Defaults to config value.
    """
    if df.empty:
        logger.warning("compute_analytics called with empty DataFrame")
        return df

    window = window or pipeline_config.volatility_window

    # ensure sorted
    df = df.sort_values(["base_currency", "quote_currency", "rate_date"])

    # group by currency pair
    grouped = df.groupby(["base_currency", "quote_currency"])

    parts: list[pd.DataFrame] = []
    for _pair, group in grouped:
        g = group.copy()
        g["daily_pct_change"] = g["rate"].pct_change() * 100  # in %
        g["rolling_volatility"] = (
            g["daily_pct_change"].rolling(window=window, min_periods=2).std()
        )
        g["volatility_window"] = window
        parts.append(g)

    result = pd.concat(parts, ignore_index=True)
    logger.info(
        f"Analytics computed for {len(result)} rows, "
        f"window={window} days"
    )
    return result
