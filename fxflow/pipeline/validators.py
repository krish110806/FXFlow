"""
FXFlow — Data validation and quality checks.

Validates individual rate records before they enter the warehouse.
Rejects are logged with reasons for later inspection.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any, Dict, List, Tuple

from fxflow.logging import logger


@dataclass
class ValidationResult:
    """Outcome of validating a batch of records."""

    valid: List[Dict[str, Any]] = field(default_factory=list)
    rejected: List[Tuple[Dict[str, Any], str]] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.valid) + len(self.rejected)

    @property
    def rejection_rate(self) -> float:
        return len(self.rejected) / self.total if self.total else 0.0


def validate_rate_records(
    records: List[Dict[str, Any]],
) -> ValidationResult:
    """
    Validate a list of rate records from the API.

    Each record is expected to have:
      { "date": "YYYY-MM-DD", "base": "XXX", "quote": "YYY", "rate": float }

    Checks performed:
      1. Required fields present
      2. Rate is a positive finite number
      3. Date is parseable and not in the future
      4. Currency codes are 3-letter uppercase alpha
    """
    result = ValidationResult()
    today = date.today()

    for rec in records:
        reason = _check_record(rec, today)
        if reason:
            result.rejected.append((rec, reason))
            logger.debug(f"Rejected record: {reason}  data={rec}")
        else:
            result.valid.append(rec)

    if result.rejected:
        logger.warning(
            f"Validation: {len(result.rejected)}/{result.total} records "
            f"rejected ({result.rejection_rate:.1%})"
        )
    return result


# ── internal checks ──────────────────────────────────────────────────

_REQUIRED = {"date", "base", "quote", "rate"}


def _check_record(rec: Dict[str, Any], today: date) -> str | None:
    """Return a rejection reason or None if valid."""
    # 1. required fields
    missing = _REQUIRED - set(rec.keys())
    if missing:
        return f"Missing fields: {missing}"

    # 2. rate sanity
    try:
        rate = float(rec["rate"])
    except (TypeError, ValueError):
        return f"Non-numeric rate: {rec['rate']!r}"
    if rate <= 0:
        return f"Non-positive rate: {rate}"
    if not __import__("math").isfinite(rate):
        return f"Non-finite rate: {rate}"

    # 3. date check
    try:
        rec_date = date.fromisoformat(str(rec["date"]))
    except (TypeError, ValueError):
        return f"Invalid date: {rec['date']!r}"
    if rec_date > today:
        return f"Future date: {rec_date}"

    # 4. currency codes
    for key in ("base", "quote"):
        code = str(rec[key])
        if len(code) != 3 or not code.isalpha() or not code.isupper():
            return f"Invalid currency code '{code}' in field '{key}'"

    return None
