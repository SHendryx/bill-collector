"""Defines the Bill model for energy consumption billing."""
from dataclasses import dataclass
from typing import Optional
from datetime import date

@dataclass
class Bill:
    """Represent a bill associated with an account."""  
    id: Optional[int] = None
    biller_id: int
    account_id: int
    amount_due: str
    due_date: date  # ISO format date string
    start_date: date  # ISO format date string
    end_date: date  # ISO format date string
