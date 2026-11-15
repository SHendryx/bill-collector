"""Defines the MeterReading model for utility meter readings."""
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

@dataclass(kw_only=True)
class MeterReading:
    """Represents a reading from a utility meter."""
    id: int | None = None
    meter_id: int
    bill_id: int
    start_date: date
    end_date: date
    start_value: Decimal
    end_value: Decimal

    @property
    def usage(self) -> Decimal:
        """Calculate the usage based on the start and end values."""
        return self.end_value - self.start_value
