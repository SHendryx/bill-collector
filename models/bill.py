"""Defines the Bill dataclass representing a utility billing statement."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(kw_only=True)
class Bill:
    """Represents a utility billing statement linked to an account."""

    id: int | None = None
    account_id: int
    amount_due: Decimal
    due_date: date
    start_date: date
    end_date: date
    file_hash: str | None = None
