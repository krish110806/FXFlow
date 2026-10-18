"""
FXFlow — Frankfurter API client.

Thin wrapper around the Frankfurter v2 REST API.
Every response is returned as-is *and* persisted to the raw layer
so we never lose source data.
"""

from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

from fxflow.config import api_config, PROJECT_ROOT
from fxflow.logging import logger

# ── raw data directory ───────────────────────────────────────────────
RAW_DIR = PROJECT_ROOT / "data" / "raw"
RAW_DIR.mkdir(parents=True, exist_ok=True)

# ── request timeout (seconds) ───────────────────────────────────────
_TIMEOUT = 30


class FrankfurterClient:
    """Client for the Frankfurter v2 exchange-rate API."""

    def __init__(
        self,
        base_url: str = api_config.base_url,
        base_currency: str = api_config.base_currency,
    ):
        self.base_url = base_url.rstrip("/")
        self.base_currency = base_currency
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})

    # ── public helpers ───────────────────────────────────────────────

    def get_latest_rates(
        self,
        quotes: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Fetch the most recent rates for all (or selected) quotes."""
        params: Dict[str, str] = {"base": self.base_currency}
        if quotes:
            params["quotes"] = ",".join(quotes)
        return self._get("/rates", params)

    def get_historical_rates(
        self,
        from_date: date,
        to_date: Optional[date] = None,
        quotes: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Fetch a time-series of rates between two dates."""
        params: Dict[str, str] = {
            "base": self.base_currency,
            "from": from_date.isoformat(),
        }
        if to_date:
            params["to"] = to_date.isoformat()
        if quotes:
            params["quotes"] = ",".join(quotes)
        return self._get("/rates", params)

    def get_currencies(self) -> List[Dict[str, Any]]:
        """Return the list of available currencies."""
        return self._get("/currencies")

    # ── internals ────────────────────────────────────────────────────

    def _get(
        self,
        path: str,
        params: Optional[Dict[str, str]] = None,
    ) -> Any:
        """Execute GET, persist raw JSON, and return parsed data."""
        url = f"{self.base_url}{path}"
        logger.debug(f"GET {url}  params={params}")
        try:
            resp = self.session.get(url, params=params, timeout=_TIMEOUT)
            resp.raise_for_status()
        except requests.RequestException as exc:
            logger.error(f"API request failed: {exc}")
            raise

        data = resp.json()
        self._save_raw(url, params, resp.status_code, data)
        return data

    def _save_raw(
        self,
        url: str,
        params: Optional[Dict[str, str]],
        status_code: int,
        body: Any,
    ) -> None:
        """Persist the raw API response to data/raw/ for lineage."""
        ts = date.today().isoformat()
        safe_name = (
            url.replace("https://", "")
            .replace("/", "_")
            .replace("?", "_")[:80]
        )
        path = RAW_DIR / f"{ts}_{safe_name}.json"
        payload = {
            "url": url,
            "params": params,
            "status_code": status_code,
            "body": body,
        }
        try:
            path.write_text(json.dumps(payload, default=str), encoding="utf-8")
            logger.debug(f"Raw response saved → {path.name}")
        except OSError as exc:
            logger.warning(f"Could not persist raw response: {exc}")
