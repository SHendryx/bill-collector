"""Defines the Account model for bill collection."""
from dataclasses import dataclass
from typing import Optional

@dataclass
class Account:
    """Represent a bill collection account."""
    id: Optional[int] = None
    number: str
    biller_id: int
