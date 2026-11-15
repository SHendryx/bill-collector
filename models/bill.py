"""Defines the Bill model for energy consumption billing."""
from dataclasses import dataclass
from typing import Optional
from datetime import date

@dataclass
class Bill:
    """Represent a bill associated with an account."""  
    id: Optional[int] = None
    account_id: int
    amount_due: str
    due_date: date  # ISO format date string
    unit_of_measure: str  # e.g., "kWh", "CCF", "Therms"
