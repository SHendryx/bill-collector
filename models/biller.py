"""Defines the Biller model for energy consumption billing."""
from dataclasses import dataclass
from typing import Optional
from enum import StrEnum

class BillerName(StrEnum):
    """Supported biller names for energy consumption billing."""
    PGE = "PG&E"
    SMUD = "SMUD"
    CHW = "CITRUS HEIGHTS WATER"
    OTHER = "Other"

@dataclass
class Biller:
    """Represents a billing entity or service provider."""
    id: Optional[int] = None
    name: BillerName
