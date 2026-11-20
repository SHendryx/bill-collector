"""Defines the MeterReading model for utility meter readings."""
from dataclasses import dataclass
from decimal import Decimal


@dataclass(kw_only=True)
class MeterReading:
    """Represents a reading from a utility meter attached to a bill."""
    id: int | None = None
    meter_id: int
    bill_id: int
    usage: Decimal
