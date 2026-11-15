"""Defines the Account model for bill collection."""
from dataclasses import dataclass
from typing import Optional

@dataclass(kw_only=True)
class Account:
    """Represent a bill collection account."""
    id: int | None = None
    number: str
    biller_id: int
