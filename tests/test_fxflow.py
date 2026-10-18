"""
FXFlow — Unit test suite using python's built-in unittest module.
"""

from __future__ import annotations

import unittest
from datetime import date, timedelta
import pandas as pd
import numpy as np

from fxflow.pipeline.validators import validate_rate_records, ValidationResult
from fxflow.pipeline.analytics import compute_analytics
from fxflow.data_access import (
    get_exchange_rates,
    get_currency_map,
    get_data_freshness,
    get_available_pairs,
)


class TestValidators(unittest.TestCase):
    def test_valid_record(self):
        records = [
            {"date": "2026-01-10", "base": "USD", "quote": "EUR", "rate": 0.92},
            {"date": "2026-01-11", "base": "USD", "quote": "GBP", "rate": 0.79},
        ]
        result = validate_rate_records(records)
        self.assertEqual(len(result.valid), 2)
        self.assertEqual(len(result.rejected), 0)

    def test_missing_fields_rejected(self):
        records = [
            {"base": "USD", "quote": "EUR", "rate": 0.92},  # missing date
            {"date": "2026-01-10", "quote": "EUR", "rate": 0.92},  # missing base
        ]
        result = validate_rate_records(records)
        self.assertEqual(len(result.valid), 0)
        self.assertEqual(len(result.rejected), 2)

    def test_invalid_rates_rejected(self):
        records = [
            {"date": "2026-01-10", "base": "USD", "quote": "EUR", "rate": 0},
            {"date": "2026-01-10", "base": "USD", "quote": "EUR", "rate": -1.5},
            {"date": "2026-01-10", "base": "USD", "quote": "EUR", "rate": "abc"},
            {"date": "2026-01-10", "base": "USD", "quote": "EUR", "rate": float("inf")},
        ]
        result = validate_rate_records(records)
        self.assertEqual(len(result.valid), 0)
        self.assertEqual(len(result.rejected), 4)

    def test_invalid_currency_codes_rejected(self):
        records = [
            {"date": "2026-01-10", "base": "usd", "quote": "EUR", "rate": 0.92},  # lowercase
            {"date": "2026-01-10", "base": "US", "quote": "EUR", "rate": 0.92},   # 2 chars
            {"date": "2026-01-10", "base": "USD", "quote": "E1R", "rate": 0.92},  # non-alpha
        ]
        result = validate_rate_records(records)
        self.assertEqual(len(result.valid), 0)
        self.assertEqual(len(result.rejected), 3)


class TestAnalytics(unittest.TestCase):
    def test_compute_analytics(self):
        data = {
            "rate_date": pd.date_range("2026-01-01", periods=10, freq="D"),
            "base_currency": ["USD"] * 10,
            "quote_currency": ["EUR"] * 10,
            "rate": [1.0, 1.02, 1.01, 1.03, 1.05, 1.04, 1.06, 1.07, 1.05, 1.08],
        }
        df = pd.DataFrame(data)
        res = compute_analytics(df, window=5)
        
        self.assertIn("daily_pct_change", res.columns)
        self.assertIn("rolling_volatility", res.columns)
        self.assertEqual(len(res), 10)
        
        # first row percentage change should be NaN
        self.assertTrue(np.isnan(res["daily_pct_change"].iloc[0]))
        # second row percentage change = ((1.02 - 1.0) / 1.0) * 100 = 2.0%
        self.assertAlmostEqual(res["daily_pct_change"].iloc[1], 2.0, places=4)


class TestDataAccess(unittest.TestCase):
    def test_freshness_and_rates(self):
        freshness = get_data_freshness()
        self.assertTrue(freshness.get("rates_exist"))
        self.assertGreater(freshness.get("total_rate_rows", 0), 0)

        df = get_exchange_rates()
        self.assertFalse(df.empty)
        self.assertIn("rate", df.columns)
        self.assertIn("rate_date", df.columns)

        pairs = get_available_pairs()
        self.assertTrue(len(pairs) > 0)


if __name__ == "__main__":
    unittest.main()
