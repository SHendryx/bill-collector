"""Defines the MeterReading model for utility meter readings."""
from dataclasses import dataclass
from typing import Optional

@dataclass
class MeterReading:
    """Represents a reading from a utility meter."""
    id: Optional[int] = None
    meter_id: int
    reading_value: float
    reading_date: str  # ISO format date string
