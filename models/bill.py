"""Defines the Bill model for energy consumption billing."""
from dataclasses import dataclass
from datetime import date

@dataclass(kw_only=True)
class Bill:
    """Represent a bill associated with an account."""  
    id: int | None = None
    account_id: int
    amount_due: str
    due_date: date  # ISO format date string
    start_date: date  # ISO format date string
    end_date: date  # ISO format date string
