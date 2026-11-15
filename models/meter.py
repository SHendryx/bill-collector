"""Defines a Meter class that represents a utility meter linked to a billing account."""
from dataclasses import dataclass
from typing import Optional
from enum import StrEnum

class UnitOfMeasure(StrEnum):
    """Supported unit types for energy consumption reporting."""
    KWH = "kWh"
    CCF = "CCF"
    THERMS = "Therms"

@dataclass
class Meter:
    """Represents a utility meter linked to a billing account."""
    id: Optional[int] = None
    number: str
    account_id: int
    unit_of_measure: UnitOfMeasure
