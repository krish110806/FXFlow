"""Isolated tests for World Bank CSV pipeline validation and persistence."""

from __future__ import annotations

import importlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import pandas as pd
import requests

from fxflow import data_access_csv
from fxflow.pipeline import csv_orchestrator as pipeline


def wb_record(
    country_code: str = "IND",
    country_code2: str = "IN",
    country_name: str = "India",
    indicator_code: str = "FP.CPI.TOTL.ZG",
    year: str = "2020",
    value: float | None = 5.5,
) -> dict:
    return {
        "countryiso3code": country_code,
        "country": {"id": country_code2, "value": country_name},
        "indicator": {"id": indicator_code, "value": "Inflation"},
        "date": year,
        "value": value,
    }


class CsvPipelineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        root = Path(self.temp_dir.name)
        self.raw_csv = root / "raw" / "wb_inflation_raw.csv"
        self.cleaned_csv = root / "processed" / "wb_inflation_cleaned.csv"
        self.analytics_csv = root / "processed" / "wb_inflation_analytics.csv"
        self.runs_csv = root / "processed" / "csv_pipeline_runs.csv"
        self.raw_csv.parent.mkdir(parents=True)
        self.cleaned_csv.parent.mkdir(parents=True)

        paths = (
            (pipeline, "RAW_CSV", self.raw_csv),
            (pipeline, "CLEANED_CSV", self.cleaned_csv),
            (pipeline, "ANALYTICS_CSV", self.analytics_csv),
            (pipeline, "RUNS_CSV", self.runs_csv),
            (data_access_csv, "RAW_CSV", self.raw_csv),
            (data_access_csv, "CLEANED_CSV", self.cleaned_csv),
            (data_access_csv, "ANALYTICS_CSV", self.analytics_csv),
            (data_access_csv, "RUNS_CSV", self.runs_csv),
        )
        for module, name, value in paths:
            patcher = patch.object(module, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    @staticmethod
    def api_response(records: list[dict]) -> Mock:
        response = Mock()
        response.json.return_value = [{"page": 1}, records]
        return response

    def run_with_records(self, records: list[dict]) -> dict:
        with patch.object(
            pipeline.requests,
            "get",
            return_value=self.api_response(records),
        ):
            return pipeline.run_csv_pipeline(country_codes=["IN", "US"])

    def test_successful_ingestion_and_persisted_stage_metrics(self) -> None:
        records = [
            wb_record(year="2020", value=5.5),
            wb_record(year="2020", value=6.0),
            wb_record(
                country_code="USA",
                country_code2="US",
                country_name="United States",
                indicator_code="WRONG.INDICATOR",
            ),
            wb_record(year="2021", value=None),
        ]

        result = self.run_with_records(records)
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["rows_fetched"], 4)
        self.assertEqual(result["rows_valid"], 2)
        self.assertEqual(result["rows_rejected"], 2)
        self.assertEqual(result["rows_committed"], 1)
        self.assertEqual(result["stages"][2]["duplicates_removed"], 1)
        self.assertEqual(len(pd.read_csv(self.cleaned_csv)), 1)

        runs = data_access_csv.get_csv_pipeline_runs()
        latest = runs.iloc[-1]
        self.assertEqual(latest["rows_fetched"], 4)
        self.assertEqual(latest["rows_valid"], 2)
        self.assertEqual(latest["rows_committed"], 1)
        self.assertEqual(latest["rows_rejected"], 2)
        self.assertEqual(len(latest["_stage_details"]), 5)

    def test_invalid_schema_and_row_values_are_rejected(self) -> None:
        missing_column = pd.DataFrame([{
            "country_code": "IND",
            "year": "2020",
            "value": 5.5,
        }])
        _, _, schema_result = pipeline.stage_validate(missing_column)
        self.assertEqual(schema_result["status"], "error")
        self.assertIn("Missing required columns", schema_result["error"])

        cases = [
            (wb_record(indicator_code="WRONG"), "indicator"),
            (wb_record(country_code="IN"), "ISO-3"),
            (wb_record(country_code2="IND"), "ISO-2"),
            (wb_record(year="2020.5"), "year"),
            (wb_record(value=float("inf")), "Non-finite"),
            (wb_record(value="not-a-number"), "Non-numeric"),
        ]
        raw = pd.DataFrame([
            {
                "country_code": r["countryiso3code"],
                "country_code2": r["country"]["id"],
                "country_name": r["country"]["value"],
                "indicator_code": r["indicator"]["id"],
                "indicator_name": r["indicator"]["value"],
                "year": r["date"],
                "value": r["value"],
            }
            for r, _ in cases
        ])
        valid, rejected, info = pipeline.stage_validate(raw)
        self.assertTrue(valid.empty)
        self.assertEqual(len(rejected), len(cases))
        self.assertEqual(info["rejected"], len(cases))
        for reason, (_, expected) in zip(rejected["_rejection_reason"], cases):
            self.assertIn(expected.lower(), reason.lower())

    def test_duplicate_existing_keys_are_not_counted_as_committed(self) -> None:
        first = self.run_with_records([wb_record(year="2020", value=5.5)])
        second = self.run_with_records([wb_record(year="2020", value=5.5)])

        self.assertEqual(first["rows_committed"], 1)
        self.assertEqual(second["rows_committed"], 0)
        self.assertEqual(len(pd.read_csv(self.cleaned_csv)), 1)
        self.assertEqual(
            int(data_access_csv.get_csv_pipeline_runs().iloc[-1]["rows_committed"]),
            0,
        )

    def test_failed_request_preserves_cleaned_data_and_logs_error(self) -> None:
        self.run_with_records([wb_record(year="2020", value=5.5)])
        cleaned_before = self.cleaned_csv.read_bytes()
        analytics_before = self.analytics_csv.read_bytes()
        raw_before = self.raw_csv.read_bytes()
        snapshots_before = set(self.raw_csv.parent.glob(pipeline.RAW_SNAPSHOT_PATTERN))

        with patch.object(
            pipeline.requests,
            "get",
            side_effect=requests.RequestException("offline"),
        ):
            result = pipeline.run_csv_pipeline(country_codes=["IN"])

        self.assertEqual(result["status"], "error")
        self.assertEqual(self.cleaned_csv.read_bytes(), cleaned_before)
        self.assertEqual(self.analytics_csv.read_bytes(), analytics_before)
        self.assertEqual(self.raw_csv.read_bytes(), raw_before)
        self.assertEqual(
            set(self.raw_csv.parent.glob(pipeline.RAW_SNAPSHOT_PATTERN)),
            snapshots_before,
        )
        self.assertEqual(data_access_csv.get_csv_pipeline_runs().iloc[-1]["status"], "error")
        self.assertEqual(data_access_csv.get_csv_pipeline_runs().iloc[-1]["rows_fetched"], 0)

    def test_raw_snapshots_are_archived_and_reload_from_disk(self) -> None:
        self.run_with_records([wb_record(year="2020", value=5.5)])
        self.run_with_records([wb_record(year="2021", value=6.0)])

        snapshots = list(self.raw_csv.parent.glob(pipeline.RAW_SNAPSHOT_PATTERN))
        self.assertEqual(len(snapshots), 2)
        self.assertTrue(self.raw_csv.exists())

        importlib.reload(data_access_csv)
        self.addCleanup(importlib.reload, data_access_csv)
        for name, value in (
            ("RAW_CSV", self.raw_csv),
            ("CLEANED_CSV", self.cleaned_csv),
            ("ANALYTICS_CSV", self.analytics_csv),
            ("RUNS_CSV", self.runs_csv),
        ):
            setattr(data_access_csv, name, value)

        self.assertEqual(len(data_access_csv.get_csv_raw()), 1)
        self.assertEqual(len(data_access_csv.get_csv_cleaned()), 2)
        self.assertEqual(len(data_access_csv.get_csv_analytics()), 2)
        runs = data_access_csv.get_csv_pipeline_runs()
        self.assertEqual(len(runs), 2)
        self.assertEqual(int(runs.iloc[-1]["rows_committed"]), 1)
        self.assertEqual(
            json.loads(runs.iloc[-1]["stage_details"])[-1]["new_records"], 1
        )


if __name__ == "__main__":
    unittest.main()
